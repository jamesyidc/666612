#!/usr/bin/env python3
"""将全仓持仓改为逐仓：先平仓再重新开仓"""
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
print("🔄 将全仓持仓转换为逐仓模式")
print("=" * 60)

# 1. 获取当前持仓
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

if data.get('code') != '0':
    print(f"❌ 获取持仓失败: {data.get('msg')}")
    exit(1)

positions = [p for p in data.get('data', []) if float(p.get('pos', 0)) != 0]
if not positions:
    print("❌ 没有持仓")
    exit(1)

pos = positions[0]
inst_id = pos['instId']
pos_side = pos['posSide']
pos_size = abs(float(pos['pos']))
avg_price = float(pos['avgPx'])
mgn_mode = pos['mgnMode']

print(f"✅ 当前持仓:")
print(f"   币种: {inst_id}")
print(f"   方向: {pos_side}")
print(f"   数量: {pos_size}张")
print(f"   开仓均价: ${avg_price:.4f}")
print(f"   保证金模式: {mgn_mode} ({'全仓' if mgn_mode == 'cross' else '逐仓'})")

if mgn_mode == 'isolated':
    print("✅ 已经是逐仓模式，无需转换")
    exit(0)

# 2. 先设置逐仓模式和杠杆
print("\n2️⃣ 设置逐仓模式和10倍杠杆...")
leverage_path = '/api/v5/account/set-leverage'
leverage_data = {
    'instId': inst_id,
    'lever': '10',
    'mgnMode': 'isolated',
    'posSide': pos_side
}
leverage_headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', leverage_path, leverage_data)
leverage_response = requests.post(f"{OKEX_REST_URL}{leverage_path}", headers=leverage_headers, json=leverage_data, timeout=10)

if leverage_response.status_code == 200:
    result = leverage_response.json()
    if result.get('code') == '0':
        print(f"✅ 杠杆设置成功: 逐仓10x")
    else:
        print(f"⚠️ 杠杆设置: {result.get('msg')}")

# 3. 平仓
print("\n3️⃣ 平仓...")
close_path = '/api/v5/trade/order'
close_data = {
    'instId': inst_id,
    'tdMode': 'cross',  # 当前是全仓，所以平仓也用全仓
    'side': 'sell' if pos_side == 'long' else 'buy',
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(int(pos_size))
}
close_headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', close_path, close_data)
close_response = requests.post(f"{OKEX_REST_URL}{close_path}", headers=close_headers, json=close_data, timeout=10)

if close_response.status_code != 200:
    print(f"❌ 平仓失败: {close_response.status_code}")
    exit(1)

close_result = close_response.json()
if close_result.get('code') != '0':
    print(f"❌ 平仓失败: {close_result.get('msg')}")
    exit(1)

close_order_id = close_result['data'][0]['ordId']
print(f"✅ 平仓成功: 订单ID {close_order_id}")

# 等待平仓完成
print("⏳ 等待3秒...")
time.sleep(3)

# 4. 以逐仓模式重新开仓
print("\n4️⃣ 以逐仓模式重新开仓 (10U保证金，10倍杠杆)...")

# 获取当前价格
ticker_response = requests.get(f"{OKEX_REST_URL}/api/v5/market/ticker", params={'instId': inst_id}, timeout=10)
ticker_data = ticker_response.json()
if ticker_data.get('code') != '0':
    print(f"❌ 获取价格失败: {ticker_data.get('msg')}")
    exit(1)

current_price = float(ticker_data['data'][0]['last'])
print(f"   当前价格: ${current_price:.4f}")

# 计算开仓数量：10U保证金，10倍杠杆 = 100U名义价值
size_usdt = 10 * 10  # 10U保证金 × 10倍杠杆 = 100U
size = max(1, round(size_usdt / current_price))

print(f"   开仓数量: {size}张")
print(f"   预计名义价值: ${size * current_price:.2f}")
print(f"   预计保证金: ${size * current_price / 10:.2f}")

open_path = '/api/v5/trade/order'
open_data = {
    'instId': inst_id,
    'tdMode': 'isolated',  # 逐仓模式
    'side': 'buy' if pos_side == 'long' else 'sell',
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(size)
}
open_headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', open_path, open_data)
open_response = requests.post(f"{OKEX_REST_URL}{open_path}", headers=open_headers, json=open_data, timeout=10)

if open_response.status_code != 200:
    print(f"❌ 开仓失败: {open_response.status_code}")
    exit(1)

open_result = open_response.json()
if open_result.get('code') != '0':
    print(f"❌ 开仓失败: {open_result.get('msg')}")
    exit(1)

open_order_id = open_result['data'][0]['ordId']
print(f"✅ 开仓成功: 订单ID {open_order_id}")

# 5. 验证结果
print("\n5️⃣ 验证转换结果...")
time.sleep(2)

response = requests.get(url, headers=headers, params={'instType': 'SWAP'}, timeout=10)
data = response.json()

if data.get('code') == '0':
    positions = [p for p in data.get('data', []) if float(p.get('pos', 0)) != 0]
    if positions:
        pos = positions[0]
        print(f"✅ 新持仓:")
        print(f"   币种: {pos['instId']}")
        print(f"   方向: {pos['posSide']}")
        print(f"   数量: {abs(float(pos['pos']))}张")
        print(f"   保证金模式: {pos['mgnMode']} ({'全仓' if pos['mgnMode'] == 'cross' else '逐仓'})")
        print(f"   杠杆: {pos['lever']}x")
        print(f"   保证金: {pos.get('imr', pos.get('margin', 'N/A'))}")
        
        if pos['mgnMode'] == 'isolated':
            print("\n🎉 转换成功！已改为逐仓模式")
        else:
            print("\n⚠️ 仍然是全仓模式")

print("=" * 60)
