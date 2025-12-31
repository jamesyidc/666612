import requests
import hmac
import hashlib
import base64
from datetime import datetime
import json
import time

# Wu666666账户API配置
API_KEY = "7a2e0baf-88e1-4a25-8f0d-8b962ccf821b"
SECRET_KEY = "F4BB1B6AF50FA5A47BFD00D4BB62AC6F"
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

def get_stx_positions():
    """查询STX持仓"""
    path = '/api/v5/account/positions'
    params = '?instType=SWAP&instId=STX-USDT-SWAP'
    url = OKEX_REST_URL + path + params
    
    headers = get_headers('GET', path + params)
    response = requests.get(url, headers=headers, timeout=10)
    result = response.json()
    
    print(f"查询持仓响应: {json.dumps(result, indent=2)}")
    
    if result['code'] == '0' and result['data']:
        for pos in result['data']:
            if pos.get('pos') and float(pos['pos']) != 0:
                return {
                    'pos_size': abs(float(pos['pos'])),
                    'pos_side': pos['posSide'],
                    'margin': float(pos.get('margin', 0)),
                    'upl': float(pos.get('upl', 0)),
                    'uplRatio': float(pos.get('uplRatio', 0))
                }
    return None

def close_stx_position(pos_size, pos_side):
    """平仓STX - 使用平仓接口"""
    print(f"\n开始平仓 {pos_size} 张 STX ({pos_side})")
    
    # 使用平仓专用接口
    path = '/api/v5/trade/close-position'
    
    close_body = {
        "instId": "STX-USDT-SWAP",
        "mgnMode": "cross",  # 全仓模式
        "posSide": pos_side,
        "ccy": "USDT"
    }
    
    print(f"平仓请求体: {json.dumps(close_body, indent=2)}")
    
    headers = get_headers('POST', path, close_body)
    url = OKEX_REST_URL + path
    
    try:
        response = requests.post(url, headers=headers, json=close_body, timeout=10)
        result = response.json()
        
        print(f"平仓响应: {json.dumps(result, indent=2)}")
        
        if result['code'] == '0':
            print(f"✅ 平仓成功！")
            if result.get('data') and len(result['data']) > 0:
                order_id = result['data'][0].get('ordId', 'N/A')
                print(f"平仓订单ID: {order_id}")
            return True
        else:
            print(f"❌ 平仓失败: {result.get('msg', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 平仓异常: {str(e)}")
        return False

# 主流程
print("=" * 60)
print("开始完全平仓STX")
print("=" * 60)

# 1. 查询当前持仓
pos = get_stx_positions()
if not pos:
    print("✅ STX已无持仓")
    exit(0)

print(f"\n当前STX持仓:")
print(f"  数量: {pos['pos_size']} 张")
print(f"  方向: {pos['pos_side']}")
print(f"  保证金: {pos['margin']} USDT")
print(f"  收益率: {pos['uplRatio'] * 100:.2f}%")

# 2. 执行平仓
success = close_stx_position(pos['pos_size'], pos['pos_side'])

# 3. 等待2秒后再次查询
time.sleep(2)
print("\n" + "=" * 60)
print("验证平仓结果")
print("=" * 60)
pos_after = get_stx_positions()

if not pos_after:
    print("✅ STX已完全平仓")
else:
    print(f"❌ STX仍有持仓: {pos_after['pos_size']} 张")

