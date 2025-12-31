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

# 查询STX订单历史（最近7天）
path = '/api/v5/trade/orders-history'
params = '?instType=SWAP&instId=STX-USDT-SWAP&limit=100'
url = OKEX_REST_URL + path + params

headers = get_headers('GET', path + params)
response = requests.get(url, headers=headers, timeout=10)
result = response.json()

print("="*80)
print("STX订单历史（最近100条）")
print("="*80)

if result['code'] == '0' and result['data']:
    buy_orders = []
    for order in result['data']:
        if order['side'] == 'buy' and order['posSide'] == 'long':
            order_time = datetime.fromtimestamp(int(order['cTime'])/1000)
            buy_orders.append({
                'time': order_time,
                'ordId': order['ordId'],
                'sz': order['sz'],
                'avgPx': order['avgPx'],
                'state': order['state']
            })
    
    print(f"\n找到 {len(buy_orders)} 个STX买入订单：\n")
    for i, order in enumerate(buy_orders[:20], 1):  # 只显示最近20个
        print(f"{i}. 时间: {order['time']}")
        print(f"   订单ID: {order['ordId']}")
        print(f"   数量: {order['sz']} 张")
        print(f"   成交均价: {order['avgPx']}")
        print(f"   状态: {order['state']}")
        print()
else:
    print(f"查询失败: {result}")

