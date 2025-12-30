#!/usr/bin/env python3
"""调整逐仓持仓到10U保证金"""
import json
import requests
import hmac
import base64
import hashlib
from datetime import datetime
import time

# 加载配置
with open('sub_account_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

sub_account = config['sub_accounts'][0]
api_key = sub_account['api_key']
secret_key = sub_account['secret_key']
passphrase = sub_account['passphrase']

OKEX_REST_URL = 'https://www.okx.com'

def get_okex_headers(api_key, secret_key, passphrase, method, request_path, body=None):
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    if body:
        body_str = json.dumps(body) if isinstance(body, dict) else body
    else:
        body_str = ''
    
    message = timestamp + method + request_path + body_str
    mac = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    signature = base64.b64encode(mac.digest()).decode('utf-8')
    
    return {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }

print("=" * 60)
print("🔧 调整持仓到10U保证金（逐仓模式）")
print("=" * 60)

# 获取当前持仓
print("\n1️⃣ 获取当前持仓...")
request_path = '/api/v5/account/positions'
query_string = 'instType=SWAP'
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
message = timestamp + 'GET' + request_path + '?' + query_string
mac = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
signature = base64.b64encode(mac.digest()).decode('utf-8')

headers = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature,
    'OK-ACCESS-TIMESTAMP': timestamp,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

url = f"{OKEX_REST_URL}{request_path}"
response = requests.get(url, headers=headers, params={'instType': 'SWAP'}, timeout=10)
data = response.json()

positions = [p for p in data.get('data', []) if float(p.get('pos', 0)) != 0]
pos = positions[0]
inst_id = pos['instId']
pos_side = pos['posSide']
current_size = abs(float(pos['pos']))
# 安全处理保证金字段
imr = pos.get('imr', '')
margin = pos.get('margin', '')
current_margin = float(imr or margin or 0)

print(f"✅ 当前持仓: {current_size}张，保证金: {current_margin:.2f} USDT")

# 获取当前价格
ticker_response = requests.get(f"{OKEX_REST_URL}/api/v5/market/ticker", params={'instId': inst_id}, timeout=10)
ticker_data = ticker_response.json()
current_price = float(ticker_data['data'][0]['last'])
print(f"   当前价格: ${current_price:.4f}")

# 计算目标持仓：10U保证金
target_margin = 10  # 10U保证金
target_size = max(1, round(target_margin / current_price))
print(f"   目标持仓: {target_size}张 (约{target_size * current_price:.2f} USDT保证金)")

# 需要减仓
reduce_size = int(current_size - target_size)
if reduce_size <= 0:
    print("✅ 持仓已经符合要求")
    exit(0)

print(f"\n2️⃣ 减仓 {reduce_size}张...")
close_path = '/api/v5/trade/order'
close_data = {
    'instId': inst_id,
    'tdMode': 'isolated',
    'side': 'sell' if pos_side == 'long' else 'buy',
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(reduce_size)
}
close_headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', close_path, close_data)
close_response = requests.post(f"{OKEX_REST_URL}{close_path}", headers=close_headers, json=close_data, timeout=10)

if close_response.status_code == 200:
    close_result = close_response.json()
    if close_result.get('code') == '0':
        close_order_id = close_result['data'][0]['ordId']
        print(f"✅ 减仓成功: 订单ID {close_order_id}")
    else:
        print(f"❌ 减仓失败: {close_result.get('msg')}")
        exit(1)

# 验证
print("\n3️⃣ 验证结果...")
time.sleep(3)

response = requests.get(url, headers=headers, params={'instType': 'SWAP'}, timeout=10)
data = response.json()
positions = [p for p in data.get('data', []) if float(p.get('pos', 0)) != 0]
if positions:
    pos = positions[0]
    final_size = abs(float(pos['pos']))
    imr = pos.get('imr', '')
    margin = pos.get('margin', '')
    final_margin = float(imr or margin or 0)
    print(f"✅ 最终持仓: {final_size}张")
    print(f"   保证金: {final_margin:.2f} USDT")
    print(f"   名义价值: {final_size * current_price:.2f} USDT")
    print(f"   保证金模式: {pos['mgnMode']} ({'全仓' if pos['mgnMode'] == 'cross' else '逐仓'})")

print("=" * 60)
