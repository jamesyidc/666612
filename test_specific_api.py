import json
import requests
import hmac
import base64
from datetime import datetime

# 你提供的API凭证
api_key = "8650e46c-059b-431d-93cf-55f8c79babdb"
secret_key = "4C2BD2AC6A08615EA7F36A6251857FCE"
passphrase = "Wu666666"

print(f"\n测试API凭证:")
print(f"  API Key: {api_key}")
print(f"  账户名: Wu666666 (POIT)")
print("=" * 80)

# 1. 查询持仓
print("\n【1. 查询持仓信息】")
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
method = 'GET'
request_path = '/api/v5/account/positions'
params = 'instType=SWAP'
full_path = f'{request_path}?{params}'

message = timestamp + method + full_path
mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
signature = base64.b64encode(mac.digest()).decode()

headers = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature,
    'OK-ACCESS-TIMESTAMP': timestamp,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

url = f'https://www.okx.com{full_path}'
response = requests.get(url, headers=headers, timeout=10)
positions_result = response.json()

if positions_result.get('code') == '0' and positions_result.get('data'):
    for pos in positions_result['data']:
        print(f"\n  币种: {pos.get('instId')}")
        print(f"  持仓方向: {pos.get('posSide')}")
        print(f"  持仓数量: {pos.get('pos')}")
        print(f"  保证金(margin): {pos.get('margin')} USDT")
        print(f"  初始保证金(imr): {pos.get('imr')} USDT")
        print(f"  维持保证金(mmr): {pos.get('mmr')} USDT")
        print(f"  未实现盈亏(upl): {pos.get('upl')} USDT")
        print(f"  名义价值(notionalUsd): {pos.get('notionalUsd')} USDT")
else:
    print(f"  错误: {positions_result}")

# 2. 查询账户余额
print("\n" + "=" * 80)
print("【2. 查询账户余额】")
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
request_path = '/api/v5/account/balance'
full_path = request_path

message = timestamp + method + full_path
mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
signature = base64.b64encode(mac.digest()).decode()

headers = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature,
    'OK-ACCESS-TIMESTAMP': timestamp,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

url = f'https://www.okx.com{full_path}'
response = requests.get(url, headers=headers, timeout=10)
balance_result = response.json()

if balance_result.get('code') == '0' and balance_result.get('data'):
    account = balance_result['data'][0]
    details = account['details'][0]
    
    total_eq = float(account.get('totalEq', 0)) if account.get('totalEq') else 0
    iso_eq = float(account.get('isoEq', 0)) if account.get('isoEq') else 0
    eq = float(details.get('eq', 0)) if details.get('eq') else 0
    avail_bal = float(details.get('availBal', 0)) if details.get('availBal') else 0
    frozen_bal = float(details.get('frozenBal', 0)) if details.get('frozenBal') else 0
    iso_upl = float(details.get('isoUpl', 0)) if details.get('isoUpl') else 0
    
    print(f"\n  账户总权益: {total_eq:.4f} USDT")
    print(f"  可用余额: {avail_bal:.4f} USDT")
    print(f"  冻结保证金: {frozen_bal:.4f} USDT")
    print(f"  逐仓保证金权益: {iso_eq:.4f} USDT")
    print(f"  逐仓未实现盈亏: {iso_upl:.4f} USDT")
else:
    print(f"  错误: {balance_result}")

print("\n" + "=" * 80)
