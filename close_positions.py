#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""平仓指定持仓，保留CRO 10U"""

import requests
import hmac
import base64
import hashlib
import json
from datetime import datetime

# OKX API配置
OKEX_REST_URL = "https://www.okx.com"

def get_okex_signature(timestamp, method, request_path, body, secret_key):
    """生成OKEx签名"""
    if body is None:
        body = ''
    elif isinstance(body, dict):
        body = json.dumps(body)
    
    message = timestamp + method + request_path + body
    mac = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode('utf-8')

def get_okex_headers(api_key, secret_key, passphrase, method, request_path, body=None):
    """生成OKEx请求头"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    signature = get_okex_signature(timestamp, method, request_path, body, secret_key)
    
    return {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }

def close_position(api_key, secret_key, passphrase, inst_id, pos_side, size):
    """平仓指定持仓"""
    request_path = '/api/v5/trade/order'
    
    # 平仓订单：long平仓用sell，short平仓用buy
    side = 'sell' if pos_side == 'long' else 'buy'
    
    order_data = {
        'instId': inst_id,
        'tdMode': 'cross',
        'side': side,
        'posSide': pos_side,
        'ordType': 'market',
        'sz': str(int(size))
    }
    
    print(f"\n📤 准备平仓: {inst_id} {pos_side} {size}张")
    print(f"   订单详情: {json.dumps(order_data, indent=2)}")
    
    headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', request_path, order_data)
    url = f"{OKEX_REST_URL}{request_path}"
    
    try:
        response = requests.post(url, headers=headers, json=order_data, timeout=10)
        print(f"   HTTP状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   API响应: {json.dumps(result, indent=2)}")
            
            if result.get('code') == '0':
                order_id = result['data'][0]['ordId']
                print(f"✅ 平仓成功! 订单ID: {order_id}")
                return True
            else:
                print(f"❌ 平仓失败: {result.get('msg')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 平仓异常: {e}")
        return False

def reduce_cro_position(api_key, secret_key, passphrase, current_size, target_size):
    """减少CRO持仓到目标数量"""
    reduce_size = current_size - target_size
    if reduce_size <= 0:
        print(f"✅ CRO持仓已经是 {current_size}张，无需减仓")
        return True
    
    print(f"\n📉 准备减少CRO持仓: 当前 {current_size}张 → 目标 {target_size}张，需要平掉 {reduce_size}张")
    
    return close_position(api_key, secret_key, passphrase, 'CRO-USDT-SWAP', 'long', reduce_size)

def main():
    # 加载子账户配置
    with open('sub_account_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    sub_account = config['sub_accounts'][0]  # Wu666666
    api_key = sub_account['api_key']
    secret_key = sub_account['secret_key']
    passphrase = sub_account['passphrase']
    
    print("=" * 60)
    print("🎯 子账户持仓调整计划")
    print("=" * 60)
    
    # 1. 获取当前持仓
    print("\n📊 正在获取当前持仓...")
    request_path = '/api/v5/account/positions'
    query_string = 'instType=SWAP'
    headers = get_okex_headers(api_key, secret_key, passphrase, 'GET', request_path + '?' + query_string)
    
    url = f"{OKEX_REST_URL}{request_path}"
    response = requests.get(url, headers=headers, params={'instType': 'SWAP'}, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ 获取持仓失败: HTTP {response.status_code}")
        return
    
    data = response.json()
    if data.get('code') != '0':
        print(f"❌ 获取持仓失败: {data.get('msg')}")
        return
    
    positions = [pos for pos in data.get('data', []) if float(pos.get('pos', 0)) != 0]
    
    print(f"\n当前持仓 ({len(positions)}个):")
    for pos in positions:
        inst_id = pos['instId']
        pos_side = pos['posSide']
        pos_size = float(pos['pos'])
        avg_px = float(pos.get('avgPx', 0))
        mark_px = float(pos.get('markPx', 0))
        upl = float(pos.get('upl', 0))
        
        print(f"  • {inst_id} {pos_side} {abs(pos_size)}张, 开仓价:{avg_px}, 当前价:{mark_px}, 盈亏:{upl:.4f} USDT")
    
    # 2. 执行平仓操作
    print("\n" + "=" * 60)
    print("🔨 开始执行平仓操作")
    print("=" * 60)
    
    cro_size = 0
    for pos in positions:
        inst_id = pos['instId']
        pos_side = pos['posSide']
        pos_size = abs(float(pos['pos']))
        
        if inst_id == 'CRO-USDT-SWAP' and pos_side == 'long':
            cro_size = pos_size
            continue  # 先跳过CRO，最后处理
        
        # 平掉其他所有持仓
        print(f"\n🎯 目标: 平仓 {inst_id} {pos_side}")
        success = close_position(api_key, secret_key, passphrase, inst_id, pos_side, pos_size)
        
        if success:
            print(f"✅ {inst_id} 已平仓")
        else:
            print(f"⚠️ {inst_id} 平仓失败，请手动检查")
    
    # 3. 调整CRO到10U
    if cro_size > 0:
        # 当前CRO价格约0.0925，10U ≈ 108张
        target_size = 108
        print(f"\n🎯 目标: CRO持仓调整为 10U (约{target_size}张)")
        
        if cro_size > target_size:
            success = reduce_cro_position(api_key, secret_key, passphrase, int(cro_size), target_size)
            if success:
                print(f"✅ CRO持仓已调整为 {target_size}张 (约10U)")
            else:
                print(f"⚠️ CRO减仓失败，请手动检查")
        else:
            print(f"✅ CRO当前持仓 {int(cro_size)}张 已经小于目标，保持不变")
    
    print("\n" + "=" * 60)
    print("✅ 操作完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
