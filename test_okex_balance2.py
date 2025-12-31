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

account_name = sub_account['account_name']
api_key = sub_account['api_key']
secret_key = sub_account['secret_key']
passphrase = sub_account['passphrase']

# 构建请求 - 查询账户余额
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
method = 'GET'
request_path = '/api/v5/account/balance'
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

if result.get('code') == '0' and result.get('data'):
    account = result['data'][0]
    details = account['details'][0]
    
    print("\n" + "="*80)
    print(f"账户: {account_name}")
    print("="*80)
    
    # 账户总览
    print(f"\n【账户总览】")
    total_eq = float(account.get('totalEq', 0)) if account.get('totalEq') else 0
    iso_eq = float(account.get('isoEq', 0)) if account.get('isoEq') else 0
    print(f"  总权益(totalEq): {total_eq:.4f} USDT")
    print(f"  逐仓保证金权益(isoEq): {iso_eq:.4f} USDT")
    
    # USDT详情
    print(f"\n【USDT详情】")
    eq = float(details.get('eq', 0)) if details.get('eq') else 0
    avail_bal = float(details.get('availBal', 0)) if details.get('availBal') else 0
    avail_eq = float(details.get('availEq', 0)) if details.get('availEq') else 0
    frozen_bal = float(details.get('frozenBal', 0)) if details.get('frozenBal') else 0
    iso_eq_detail = float(details.get('isoEq', 0)) if details.get('isoEq') else 0
    iso_upl = float(details.get('isoUpl', 0)) if details.get('isoUpl') else 0
    upl = float(details.get('upl', 0)) if details.get('upl') else 0
    
    print(f"  权益(eq): {eq:.4f} USDT")
    print(f"  可用余额(availBal): {avail_bal:.4f} USDT")
    print(f"  可用权益(availEq): {avail_eq:.4f} USDT")
    print(f"  冻结金额(frozenBal): {frozen_bal:.4f} USDT")
    print(f"  逐仓保证金(isoEq): {iso_eq_detail:.4f} USDT")
    print(f"  逐仓未实现盈亏(isoUpl): {iso_upl:.4f} USDT")
    print(f"  未实现盈亏(upl): {upl:.4f} USDT")
    
    print("\n【分析】")
    print(f"  可用余额 = {avail_bal:.4f} USDT （可以用来开新仓）")
    print(f"  逐仓占用保证金 = {frozen_bal:.4f} USDT （当前持仓占用）")
    print(f"  账户总权益 = {eq:.4f} USDT （可用 + 冻结）")
    print("="*80)
