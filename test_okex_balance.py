import json
import requests
import hmac
import base64
from datetime import datetime

# 读取配置
with open('sub_account_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 获取第一个启用的子账户
sub_account = None
for acc in config['sub_accounts']:
    if acc.get('enabled'):
        sub_account = acc
        break

if not sub_account:
    print("没有启用的子账户")
    exit(1)

account_name = sub_account['account_name']
api_key = sub_account['api_key']
secret_key = sub_account['secret_key']
passphrase = sub_account['passphrase']

print(f"\n测试账户: {account_name}")
print("=" * 80)

# 构建请求 - 查询账户余额
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
method = 'GET'
request_path = '/api/v5/account/balance'
params = ''
full_path = request_path

# 签名
message = timestamp + method + full_path
mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
signature = base64.b64encode(mac.digest()).decode()

# 发送请求
headers = {
    'OK-ACCESS-KEY': api_key,
    'OK-ACCESS-SIGN': signature,
    'OK-ACCESS-TIMESTAMP': timestamp,
    'OK-ACCESS-PASSPHRASE': passphrase,
    'Content-Type': 'application/json'
}

url = f'https://www.okx.com{full_path}'
response = requests.get(url, headers=headers, timeout=10)
result = response.json()

print("\n账户余额API响应:")
print(json.dumps(result, indent=2, ensure_ascii=False))

if result.get('code') == '0' and result.get('data'):
    print("\n\n账户余额详情:")
    print("=" * 80)
    for account in result['data']:
        total_eq = float(account.get('totalEq', 0))
        iso_eq = float(account.get('isoEq', 0))
        adj_eq = float(account.get('adjEq', 0))
        
        print(f"总权益(totalEq): {total_eq} USDT")
        print(f"逐仓保证金权益(isoEq): {iso_eq} USDT")
        print(f"有效保证金(adjEq): {adj_eq} USDT")
        print(f"账户层级(uTime): {account.get('uTime')}")
        
        if 'details' in account:
            print("\n币种详情:")
            for detail in account['details']:
                if float(detail.get('eq', 0)) > 0 or float(detail.get('availEq', 0)) > 0:
                    ccy = detail.get('ccy')
                    eq = float(detail.get('eq', 0))
                    avail_eq = float(detail.get('availEq', 0))
                    frozen_bal = float(detail.get('frozenBal', 0))
                    
                    print(f"\n  币种: {ccy}")
                    print(f"  权益(eq): {eq}")
                    print(f"  可用权益(availEq): {avail_eq}")
                    print(f"  冻结金额(frozenBal): {frozen_bal}")
