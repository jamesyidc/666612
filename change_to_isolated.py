#!/usr/bin/env python3
"""将现有持仓从全仓改为逐仓模式"""
import json
import requests
import hmac
import base64
import hashlib
from datetime import datetime

# 加载配置
with open('sub_account_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

sub_account = config['sub_accounts'][0]
api_key = sub_account['api_key']
secret_key = sub_account['secret_key']
passphrase = sub_account['passphrase']

OKEX_REST_URL = 'https://www.okx.com'

def get_okex_signature(timestamp, method, request_path, body, secret_key):
    if body:
        body_str = json.dumps(body) if isinstance(body, dict) else body
    else:
        body_str = ''
    
    message = timestamp + method + request_path + body_str
    mac = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode('utf-8')

def get_okex_headers(api_key, secret_key, passphrase, method, request_path, body=None):
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    signature = get_okex_signature(timestamp, method, request_path, body, secret_key)
    
    return {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }

# 1. 查看当前持仓和保证金模式
print("=" * 60)
print("1️⃣ 查看当前持仓...")
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

if data.get('code') == '0':
    positions = [p for p in data.get('data', []) if float(p.get('pos', 0)) != 0]
    print(f"✅ 当前持仓: {len(positions)}个")
    for pos in positions:
        print(f"   {pos['instId']} {pos['posSide']} {pos['pos']}张")
        print(f"   保证金模式: {pos['mgnMode']} ({'全仓' if pos['mgnMode'] == 'cross' else '逐仓'})")
        print(f"   杠杆: {pos['lever']}x")
        print()

# 2. 将持仓改为逐仓模式
print("2️⃣ 设置为逐仓模式...")
inst_id = 'CRO-USDT-SWAP'
pos_side = 'long'

leverage_path = '/api/v5/account/set-leverage'
leverage_data = {
    'instId': inst_id,
    'lever': '10',
    'mgnMode': 'isolated',  # 逐仓模式
    'posSide': pos_side
}
leverage_headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', leverage_path, leverage_data)
leverage_url = f"{OKEX_REST_URL}{leverage_path}"
leverage_response = requests.post(leverage_url, headers=leverage_headers, json=leverage_data, timeout=10)

if leverage_response.status_code == 200:
    result = leverage_response.json()
    print(f"API响应: {result}")
    if result.get('code') == '0':
        print(f"✅ 已设置为逐仓模式，杠杆10x")
    else:
        print(f"⚠️ 设置失败: {result.get('msg')}")
else:
    print(f"❌ 请求失败: {leverage_response.status_code}")

# 3. 再次查看确认
print("\n3️⃣ 确认修改结果...")
response = requests.get(url, headers=headers, params={'instType': 'SWAP'}, timeout=10)
data = response.json()

if data.get('code') == '0':
    positions = [p for p in data.get('data', []) if float(p.get('pos', 0)) != 0]
    for pos in positions:
        print(f"   {pos['instId']} {pos['posSide']}")
        print(f"   保证金模式: {pos['mgnMode']} ({'全仓' if pos['mgnMode'] == 'cross' else '逐仓'})")
        print(f"   杠杆: {pos['lever']}x")
        print(f"   保证金: {pos.get('imr', pos.get('margin', 'N/A'))}")

print("=" * 60)
