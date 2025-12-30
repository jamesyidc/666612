#!/usr/bin/env python3
"""
自动检查并修正所有持仓的杠杆倍数为10倍
"""
import requests
import hmac
import base64
import hashlib
import json
from datetime import datetime, timezone
from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE, OKEX_REST_URL

def generate_signature(timestamp, method, request_path, body=''):
    if body:
        body = json.dumps(body)
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(OKEX_SECRET_KEY, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod=hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()

def get_headers(method, request_path, body=''):
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    sign = generate_signature(timestamp, method, request_path, body)
    return {
        'OK-ACCESS-KEY': OKEX_API_KEY,
        'OK-ACCESS-SIGN': sign,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKEX_PASSPHRASE,
        'Content-Type': 'application/json'
    }

def fix_all_leverage():
    """检查并修正所有持仓的杠杆为10倍"""
    print("=" * 80)
    print("🔍 开始检查所有持仓的杠杆倍数...")
    print("=" * 80)
    
    # 1. 查询所有持仓
    positions_path = '/api/v5/account/positions?instType=SWAP'
    headers = get_headers('GET', positions_path)
    response = requests.get(OKEX_REST_URL + positions_path, headers=headers, timeout=10)
    result = response.json()
    
    if result.get('code') != '0':
        print(f"❌ 查询持仓失败: {result.get('msg')}")
        return
    
    fixed_count = 0
    total_positions = 0
    
    for pos in result['data']:
        pos_value = float(pos.get('pos', 0))
        if pos_value == 0:
            continue
        
        total_positions += 1
        inst_id = pos['instId']
        pos_side = pos['posSide']
        lever = int(pos.get('lever', 10))
        
        if lever != 10:
            print(f"\n⚠️  发现非10倍杠杆: {inst_id} ({pos_side}), 当前杠杆: {lever}x")
            print(f"   正在修改为10倍...")
            
            # 修改杠杆
            leverage_path = '/api/v5/account/set-leverage'
            leverage_body = {
                'instId': inst_id,
                'lever': '10',
                'mgnMode': 'cross',
                'posSide': pos_side
            }
            
            headers = get_headers('POST', leverage_path, leverage_body)
            fix_response = requests.post(
                OKEX_REST_URL + leverage_path,
                headers=headers,
                json=leverage_body,
                timeout=10
            )
            fix_result = fix_response.json()
            
            if fix_result.get('code') == '0':
                print(f"   ✅ 修改成功: {inst_id} 杠杆已设为10倍")
                fixed_count += 1
            else:
                print(f"   ❌ 修改失败: {fix_result.get('msg')}")
    
    print("\n" + "=" * 80)
    print(f"✅ 检查完成！")
    print(f"   总持仓数: {total_positions}")
    print(f"   修正数量: {fixed_count}")
    print(f"   所有持仓都是10倍杠杆: {'是' if fixed_count == 0 else '否'}")
    print("=" * 80)

if __name__ == '__main__':
    fix_all_leverage()
