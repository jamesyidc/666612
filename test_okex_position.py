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

# 构建请求
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
method = 'GET'
request_path = '/api/v5/account/positions'
params = 'instType=SWAP'
full_path = f'{request_path}?{params}'

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

print("\n完整API响应:")
print(json.dumps(result, indent=2, ensure_ascii=False))

if result.get('code') == '0' and result.get('data'):
    print("\n\n持仓详细字段:")
    print("=" * 80)
    for pos in result['data']:
        print(f"\n币种: {pos.get('instId')}")
        print(f"持仓方向: {pos.get('posSide')}")
        print(f"持仓数量(pos): {pos.get('pos')}")
        print(f"保证金余额(margin): {pos.get('margin')}")
        print(f"初始保证金(imr): {pos.get('imr')}")
        print(f"维持保证金(mmr): {pos.get('mmr')}")
        print(f"保证金率(mgnRatio): {pos.get('mgnRatio')}")
        print(f"杠杆倍数(lever): {pos.get('lever')}")
        print(f"未实现盈亏(upl): {pos.get('upl')}")
        print(f"已实现盈亏(realizedPnl): {pos.get('realizedPnl')}")
        print(f"名义价值(notionalUsd): {pos.get('notionalUsd')}")
        print(f"开仓均价(avgPx): {pos.get('avgPx')}")
        print(f"标记价格(markPx): {pos.get('markPx')}")
        print(f"最新成交价(last): {pos.get('last')}")
        print("-" * 80)
