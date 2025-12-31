import requests
import hmac
import hashlib
import base64
from datetime import datetime
import json

# Wu666666账户API配置
API_KEY = "8650e46c-059b-431d-93cf-55f8c79babdb"
SECRET_KEY = "4C2BD2AC6A08615EA7F36A6251857FCE"
PASSPHRASE = "Wu666666."

OKEX_REST_URL = "https://www.okx.com"

def get_headers(method, request_path, body=''):
    """生成OKEx API请求头"""
    timestamp = datetime.utcnow().isoformat("T", "milliseconds") + "Z"
    if body:
        body_str = json.dumps(body) if isinstance(body, dict) else body
    else:
        body_str = ''
    
    prehash_string = timestamp + method + request_path + body_str
    signature = base64.b64encode(
        hmac.new(
            SECRET_KEY.encode('utf-8'),
            prehash_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }
    return headers

# 查询账单明细（STX相关）
path = '/api/v5/account/bills'
params = '?instId=STX-USDT-SWAP&limit=100'
url = OKEX_REST_URL + path + params

headers = get_headers('GET', path + params)
response = requests.get(url, headers=headers, timeout=10)
result = response.json()

print("="*100)
print("STX账单明细（最近100条）")
print("="*100)

if result['code'] == '0' and result['data']:
    print(f"\n找到 {len(result['data'])} 条STX相关账单：\n")
    
    # 按时间排序
    bills = sorted(result['data'], key=lambda x: int(x['ts']), reverse=True)
    
    for i, bill in enumerate(bills[:30], 1):  # 显示最近30条
        bill_time = datetime.fromtimestamp(int(bill['ts'])/1000)
        print(f"{i}. 时间: {bill_time}")
        print(f"   类型: {bill['type']}")
        print(f"   金额: {bill['bal']} USDT")
        print(f"   变动: {bill['balChg']} USDT")
        print(f"   备注: {bill.get('notes', 'N/A')}")
        print()
else:
    print(f"查询失败: {result}")

