#!/usr/bin/env python3
"""
检查主账户的平仓订单历史
查找CFX、CRO、FIL、TON的多单被平记录
"""
import requests
import json
import hmac
import hashlib
import base64
from datetime import datetime, timezone

# 从okex_api_config导入配置
from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE, OKEX_REST_URL

def generate_signature(timestamp, method, request_path, body=''):
    """生成OKEx API签名"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(OKEX_SECRET_KEY, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    d = mac.digest()
    return base64.b64encode(d).decode()

def get_headers(method, request_path, body=''):
    """生成API请求头"""
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    signature = generate_signature(timestamp, method, request_path, body)
    
    return {
        'OK-ACCESS-KEY': OKEX_API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKEX_PASSPHRASE,
        'Content-Type': 'application/json'
    }

def check_closed_orders(inst_id):
    """查询指定币种的已完成订单历史"""
    print(f"\n{'='*80}")
    print(f"正在查询 {inst_id} 的订单历史...")
    print(f"{'='*80}")
    
    # 查询最近的已完成订单（最多100条）
    request_path = f'/api/v5/trade/orders-history?instType=SWAP&instId={inst_id}&limit=100'
    headers = get_headers('GET', request_path)
    
    try:
        response = requests.get(
            OKEX_REST_URL + request_path,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"响应: {response.text}")
            return
        
        data = response.json()
        
        if data.get('code') != '0':
            print(f"❌ API返回错误: {data.get('msg')}")
            return
        
        orders = data.get('data', [])
        print(f"📊 找到 {len(orders)} 条历史订单")
        
        # 过滤平多单的订单
        # 平多单: side=sell + posSide=long
        # 平空单: side=buy + posSide=short
        close_long_orders = []
        
        for order in orders:
            # 只关注平多单
            if order.get('side') == 'sell' and order.get('posSide') == 'long':
                close_long_orders.append(order)
        
        if not close_long_orders:
            print(f"✅ 没有找到平多单的记录")
            return
        
        print(f"\n⚠️  发现 {len(close_long_orders)} 条平多单记录：")
        print(f"{'='*80}")
        
        for order in close_long_orders:
            order_time = datetime.fromtimestamp(int(order['uTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
            fill_time = datetime.fromtimestamp(int(order['fillTime'])/1000).strftime('%Y-%m-%d %H:%M:%S') if order.get('fillTime') else 'N/A'
            
            print(f"\n订单ID: {order['ordId']}")
            print(f"下单时间: {order_time}")
            print(f"成交时间: {fill_time}")
            print(f"平仓数量: {order['sz']}")
            print(f"平仓价格: {order.get('avgPx', order.get('px', 'N/A'))}")
            print(f"订单状态: {order['state']}")
            print(f"订单类型: {order.get('ordType', 'N/A')}")
            print(f"客户端订单ID: {order.get('clOrdId', 'N/A')}")
            
            # 检查是否是API订单（通常API订单会有特殊标识）
            if order.get('clOrdId'):
                print(f"⚠️  这是一个API订单（可能是程序自动平仓）")
            else:
                print(f"ℹ️  这可能是手动订单")
            
            print(f"-" * 80)
    
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n" + "="*80)
    print(" 主账户平仓订单历史查询")
    print("="*80)
    print(f"账户: JAMESYI")
    print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 查询缺少多单的币种
    missing_long_symbols = [
        'CRO-USDT-SWAP',  # 有空单4，缺多单
        'FIL-USDT-SWAP',  # 有空单39，缺多单
        'TON-USDT-SWAP',  # 有空单4，缺多单
    ]
    
    # 查询缺少空单的币种（CFX有多单13，缺空单）
    missing_short_symbols = [
        'CFX-USDT-SWAP',  # 有多单13，缺空单
    ]
    
    print("\n📌 查询缺少多单的币种（这些应该有多单但现在只有空单）:")
    for symbol in missing_long_symbols:
        check_closed_orders(symbol)
    
    print("\n📌 查询缺少空单的币种（这些应该有空单但现在只有多单）:")
    for symbol in missing_short_symbols:
        # 对于CFX，我们要查询平空单的记录
        print(f"\n{'='*80}")
        print(f"正在查询 {symbol} 的订单历史（查找平空单记录）...")
        print(f"{'='*80}")
        
        request_path = f'/api/v5/trade/orders-history?instType=SWAP&instId={symbol}&limit=100'
        headers = get_headers('GET', request_path)
        
        try:
            response = requests.get(
                OKEX_REST_URL + request_path,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ API请求失败: {response.status_code}")
                continue
            
            data = response.json()
            
            if data.get('code') != '0':
                print(f"❌ API返回错误: {data.get('msg')}")
                continue
            
            orders = data.get('data', [])
            print(f"📊 找到 {len(orders)} 条历史订单")
            
            # 过滤平空单的订单
            # 平空单: side=buy + posSide=short
            close_short_orders = []
            
            for order in orders:
                if order.get('side') == 'buy' and order.get('posSide') == 'short':
                    close_short_orders.append(order)
            
            if not close_short_orders:
                print(f"✅ 没有找到平空单的记录")
                continue
            
            print(f"\n⚠️  发现 {len(close_short_orders)} 条平空单记录：")
            print(f"{'='*80}")
            
            for order in close_short_orders:
                order_time = datetime.fromtimestamp(int(order['uTime'])/1000).strftime('%Y-%m-%d %H:%M:%S')
                fill_time = datetime.fromtimestamp(int(order['fillTime'])/1000).strftime('%Y-%m-%d %H:%M:%S') if order.get('fillTime') else 'N/A'
                
                print(f"\n订单ID: {order['ordId']}")
                print(f"下单时间: {order_time}")
                print(f"成交时间: {fill_time}")
                print(f"平仓数量: {order['sz']}")
                print(f"平仓价格: {order.get('avgPx', order.get('px', 'N/A'))}")
                print(f"订单状态: {order['state']}")
                print(f"订单类型: {order.get('ordType', 'N/A')}")
                print(f"客户端订单ID: {order.get('clOrdId', 'N/A')}")
                
                if order.get('clOrdId'):
                    print(f"⚠️  这是一个API订单（可能是程序自动平仓）")
                else:
                    print(f"ℹ️  这可能是手动订单")
                
                print(f"-" * 80)
        
        except Exception as e:
            print(f"❌ 查询失败: {e}")
    
    print("\n" + "="*80)
    print(" 查询完成")
    print("="*80)

if __name__ == '__main__':
    main()
