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

for inst_id in ['CFX-USDT-SWAP', 'BCH-USDT-SWAP']:
    print("="*80)
    print(f"{inst_id} 持仓详情")
    print("="*80)
    
    path = '/api/v5/account/positions'
    params = f'?instType=SWAP&instId={inst_id}'
    url = OKEX_REST_URL + path + params
    
    headers = get_headers('GET', path + params)
    response = requests.get(url, headers=headers, timeout=10)
    result = response.json()
    
    if result['code'] == '0' and result['data']:
        for pos in result['data']:
            if pos.get('pos') and float(pos['pos']) != 0:
                print(f"持仓数量: {pos['pos']} 张")
                print(f"开仓均价: {pos['avgPx']}")
                print(f"标记价格: {pos['markPx']}")
                print(f"保证金: {pos['margin']} USDT")
                print(f"保证金模式: {pos['mgnMode']}")
                print(f"杠杆: {pos['lever']}x")
                print(f"收益率: {float(pos['uplRatio']) * 100:.2f}%")
                
                ctime_dt = datetime.fromtimestamp(int(pos['cTime'])/1000)
                print(f"创建时间: {ctime_dt}")
                print()

