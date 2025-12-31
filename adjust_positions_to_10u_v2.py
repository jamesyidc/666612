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

def get_positions(inst_id):
    """查询持仓"""
    path = '/api/v5/account/positions'
    params = f'?instType=SWAP&instId={inst_id}'
    url = OKEX_REST_URL + path + params
    
    headers = get_headers('GET', path + params)
    response = requests.get(url, headers=headers, timeout=10)
    result = response.json()
    
    positions = []
    if result['code'] == '0' and result['data']:
        for pos in result['data']:
            if pos.get('pos') and float(pos['pos']) != 0:
                margin_val = pos.get('margin', '0')
                margin = float(margin_val) if margin_val else 0
                
                positions.append({
                    'pos': float(pos['pos']),
                    'posSide': pos['posSide'],
                    'mgnMode': pos['mgnMode'],
                    'margin': margin,
                    'markPx': float(pos['markPx']),
                    'lever': pos['lever']
                })
    return positions

def close_position(inst_id, pos_side, mgn_mode, size):
    """平仓"""
    path = '/api/v5/trade/order'
    
    order_body = {
        'instId': inst_id,
        'tdMode': mgn_mode,
        'side': 'sell' if pos_side == 'long' else 'buy',
        'posSide': pos_side,
        'ordType': 'market',
        'sz': str(int(size))
    }
    
    headers = get_headers('POST', path, order_body)
    url = OKEX_REST_URL + path
    
    response = requests.post(url, headers=headers, json=order_body, timeout=10)
    result = response.json()
    
    return result

print("="*80)
print("调整持仓到10U")
print("="*80)

# 1. 处理CFX全仓持仓（平掉1296张）
print("\n【1】处理CFX全仓持仓")
print("-"*80)
cfx_positions = get_positions('CFX-USDT-SWAP')

for pos in cfx_positions:
    print(f"CFX {pos['mgnMode']}: {pos['pos']}张, 保证金: {pos['margin']:.2f} USDT")
    
    if pos['mgnMode'] == 'cross':
        print(f"开始平仓全仓CFX {pos['pos']}张...")
        
        result = close_position('CFX-USDT-SWAP', pos['posSide'], 'cross', pos['pos'])
        
        if result['code'] == '0':
            print(f"✅ CFX全仓平仓成功！")
        else:
            print(f"❌ CFX全仓平仓失败: {result.get('msg')}")
            print(f"详细信息: {result}")
        
        time.sleep(2)

# 2. 处理BCH持仓（保留10U）
print("\n【2】处理BCH持仓")
print("-"*80)
bch_positions = get_positions('BCH-USDT-SWAP')

for pos in bch_positions:
    print(f"当前BCH持仓: {pos['pos']}张, 保证金: {pos['margin']:.2f} USDT")
    
    # 计算需要平掉的数量
    target_margin = 10
    lever = float(pos['lever'])
    keep_size = round((target_margin * lever) / pos['markPx'])
    close_size = int(pos['pos']) - keep_size
    
    print(f"目标保证金: {target_margin}U")
    print(f"标记价格: {pos['markPx']}")
    print(f"需要保留: {keep_size}张")
    print(f"需要平掉: {close_size}张")
    
    if close_size > 0:
        print(f"开始平仓 {close_size} 张...")
        
        result = close_position('BCH-USDT-SWAP', pos['posSide'], pos['mgnMode'], close_size)
        
        if result['code'] == '0':
            print(f"✅ BCH部分平仓成功！")
        else:
            print(f"❌ BCH平仓失败: {result.get('msg')}")
            print(f"详细信息: {result}")
    else:
        print("✅ 无需平仓，已经符合要求")

print("\n" + "="*80)
print("操作完成！验证结果...")
print("="*80)

# 等待3秒后验证
time.sleep(3)

# 验证结果
print("\n【验证】CFX持仓:")
cfx_positions = get_positions('CFX-USDT-SWAP')
for pos in cfx_positions:
    print(f"  {pos['mgnMode']}: {pos['pos']}张, 保证金: {pos['margin']:.2f} USDT")

print("\n【验证】BCH持仓:")
bch_positions = get_positions('BCH-USDT-SWAP')
for pos in bch_positions:
    print(f"  {pos['mgnMode']}: {pos['pos']}张, 保证金: {pos['margin']:.2f} USDT")

print("\n" + "="*80)
print("✅ 所有持仓已调整完成！")
print("="*80)

