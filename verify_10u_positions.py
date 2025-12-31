#!/usr/bin/env python3
import requests
import json
import hmac
import hashlib
import base64
from datetime import datetime

# 读取配置
with open('sub_account_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

sub_account = config['sub_accounts'][0]
api_key = sub_account['api_key']
secret_key = sub_account['secret_key']
passphrase = sub_account['passphrase']

def sign_request(timestamp, method, request_path, body=''):
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(secret_key, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod=hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()

def get_positions():
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    method = 'GET'
    request_path = '/api/v5/account/positions?instType=SWAP'
    
    signature = sign_request(timestamp, method, request_path)
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    url = f'https://www.okx.com{request_path}'
    response = requests.get(url, headers=headers, timeout=10)
    return response.json()

# 查询持仓
result = get_positions()

print(f"\n{'='*100}")
print(f"子账户 Wu666666 持仓验证 - 目标：所有持仓保证金 ≈ 10U")
print(f"{'='*100}\n")

if result.get('code') == '0':
    positions = [p for p in result.get('data', []) if float(p.get('pos', 0)) != 0]
    
    total_margin = 0
    positions_detail = []
    
    for pos in positions:
        inst_id = pos.get('instId', '')
        pos_size = float(pos.get('pos', 0))
        mgn_mode = pos.get('mgnMode', '')
        pos_side = pos.get('posSide', '')
        
        # 获取保证金
        margin_str = pos.get('margin', '0')
        if margin_str == '':
            margin = 0.0
        else:
            margin = float(margin_str)
        
        # 计算收益率
        upl = float(pos.get('upl', 0))
        if margin > 0:
            profit_rate = (upl / margin) * 100
        else:
            profit_rate = 0
        
        # 判断状态
        if 9.5 <= margin <= 10.5:
            status = "✅ 正常"
        elif margin < 9.5:
            status = "⚠️ 偏低"
        elif margin > 10.5:
            status = f"❌ 偏高"
        else:
            status = "❓ 未知"
        
        positions_detail.append({
            'symbol': inst_id.replace('-USDT-SWAP', ''),
            'inst_id': inst_id,
            'margin': margin,
            'size': abs(pos_size),
            'profit_rate': profit_rate,
            'mode': mgn_mode,
            'side': pos_side,
            'status': status
        })
        
        total_margin += margin
    
    # 按保证金排序
    positions_detail.sort(key=lambda x: x['margin'], reverse=True)
    
    # 打印详情
    for i, pos in enumerate(positions_detail, 1):
        print(f"{i:2d}. {pos['symbol']:8s} | 保证金: {pos['margin']:7.2f} USDT | "
              f"数量: {pos['size']:8.1f}张 | 收益率: {pos['profit_rate']:7.2f}% | "
              f"模式: {pos['mode']:8s} | 方向: {pos['side']:5s} | {pos['status']}")
    
    print(f"\n{'='*100}")
    print(f"总计持仓数: {len(positions_detail)} 个")
    print(f"总保证金: {total_margin:.2f} USDT")
    if positions_detail:
        print(f"平均保证金: {total_margin/len(positions_detail):.2f} USDT")
    
    # 检查异常
    abnormal = [p for p in positions_detail if not (9.5 <= p['margin'] <= 10.5)]
    if abnormal:
        print(f"\n⚠️ 发现 {len(abnormal)} 个保证金异常的持仓:")
        for pos in abnormal:
            print(f"   - {pos['symbol']:8s}: {pos['margin']:7.2f} USDT ({pos['mode']}) {pos['status']}")
        print(f"\n需要调整的持仓:")
        for pos in abnormal:
            if pos['margin'] > 10.5:
                print(f"   - {pos['inst_id']}: 需要减少保证金 {pos['margin'] - 10:.2f} USDT")
    else:
        print(f"\n✅ 所有持仓保证金均在正常范围 (9.5-10.5 USDT)")
    
    print(f"{'='*100}\n")
else:
    print(f"❌ 查询失败: {result}")
