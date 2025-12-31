import requests
import hmac
import hashlib
import base64
from datetime import datetime
import json
import time

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

def close_stx_isolated():
    """平仓STX - 逐仓模式"""
    print(f"开始平仓STX（逐仓模式）")
    
    # 使用平仓专用接口
    path = '/api/v5/trade/close-position'
    
    close_body = {
        "instId": "STX-USDT-SWAP",
        "mgnMode": "isolated",  # 逐仓模式
        "posSide": "long",
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

# 执行平仓
print("=" * 60)
print("STX逐仓平仓")
print("=" * 60)
close_stx_isolated()

