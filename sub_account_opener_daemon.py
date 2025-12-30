#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子账号自动开仓守护进程
监控主账号亏损仓位，在子账号中自动开10U仓位
"""

import json
import time
import requests
import hmac
import base64
import hashlib
from datetime import datetime

# 配置
CONFIG_FILE = '/home/user/webapp/sub_account_config.json'
MAIN_API_URL = 'http://localhost:5000'
OKEX_REST_URL = 'https://www.okx.com'
CHECK_INTERVAL = 60  # 每60秒检查一次

def load_config():
    """加载配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_okex_signature(timestamp, method, request_path, body, secret_key):
    """生成OKEx签名"""
    if body:
        body_str = json.dumps(body) if isinstance(body, dict) else body
    else:
        body_str = ''
    
    message = timestamp + method + request_path + body_str
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

def get_main_account_positions():
    """获取主账号持仓"""
    try:
        url = f"{MAIN_API_URL}/api/anchor-system/current-positions"
        params = {'trade_mode': 'real'}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 获取主账号持仓失败: {response.status_code}")
            return []
        
        data = response.json()
        if not data.get('success'):
            print(f"❌ 主账号API返回失败: {data.get('message')}")
            return []
        
        return data.get('positions', [])
    except Exception as e:
        print(f"❌ 获取主账号持仓异常: {e}")
        return []

def get_sub_account_positions(sub_account):
    """获取子账号持仓"""
    try:
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        request_path = '/api/v5/account/positions'
        headers = get_okex_headers(api_key, secret_key, passphrase, 'GET', request_path)
        
        url = f"{OKEX_REST_URL}{request_path}"
        params = {'instType': 'SWAP'}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 获取子账号持仓失败: {response.status_code}")
            return []
        
        data = response.json()
        if data.get('code') != '0':
            print(f"❌ 子账号API返回失败: {data.get('msg')}")
            return []
        
        # 过滤有持仓的
        positions = []
        for pos in data.get('data', []):
            if float(pos.get('pos', 0)) != 0:
                positions.append({
                    'inst_id': pos['instId'],
                    'pos_side': pos['posSide'],
                    'pos_size': float(pos['pos']),
                    'avg_price': float(pos['avgPx']),
                    'upl': float(pos['upl'])
                })
        
        return positions
    except Exception as e:
        print(f"❌ 获取子账号持仓异常: {e}")
        return []

def open_position_on_sub_account(sub_account, inst_id, pos_side, size_usdt):
    """在子账号开仓"""
    try:
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        # 获取当前价格
        ticker_url = f"{OKEX_REST_URL}/api/v5/market/ticker"
        ticker_response = requests.get(ticker_url, params={'instId': inst_id}, timeout=10)
        
        if ticker_response.status_code != 200:
            print(f"❌ 获取价格失败: {ticker_response.status_code}")
            return False
        
        ticker_data = ticker_response.json()
        if ticker_data.get('code') != '0':
            print(f"❌ 获取价格失败: {ticker_data.get('msg')}")
            return False
        
        last_price = float(ticker_data['data'][0]['last'])
        
        # 计算开仓数量（张数）
        # size_usdt / last_price = 持仓价值（币）
        # 假设每张合约面值为1个币（大多数永续合约）
        size = round(size_usdt / last_price)
        
        if size < 1:
            size = 1  # 至少1张
        
        print(f"📊 准备开仓: {inst_id} {pos_side} 数量:{size}张 价格:${last_price:.4f}")
        
        # 下单
        request_path = '/api/v5/trade/order'
        order_data = {
            'instId': inst_id,
            'tdMode': 'cross',  # 全仓模式
            'side': 'buy' if pos_side == 'long' else 'sell',
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(size)
        }
        
        headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', request_path, order_data)
        
        url = f"{OKEX_REST_URL}{request_path}"
        response = requests.post(url, headers=headers, json=order_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 下单失败: {response.status_code}")
            return False
        
        result = response.json()
        if result.get('code') != '0':
            print(f"❌ 下单失败: {result.get('msg')}")
            return False
        
        order_id = result['data'][0]['ordId']
        print(f"✅ 开仓成功: {inst_id} {pos_side} 订单ID:{order_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 开仓异常: {e}")
        return False

def check_and_open_positions():
    """检查并在子账号开仓"""
    try:
        # 加载配置
        config = load_config()
        
        if not config['main_account']['enabled']:
            print("⚠️ 主账号未启用")
            return
        
        # 获取主账号持仓
        main_positions = get_main_account_positions()
        
        # 筛选亏损仓位
        loss_positions = [p for p in main_positions if p.get('profit_rate', 0) < 0]
        
        if not loss_positions:
            print("✅ 主账号无亏损仓位")
            return
        
        print(f"📊 主账号亏损仓位: {len(loss_positions)}个")
        
        # 遍历子账号
        for sub_account in config['sub_accounts']:
            if not sub_account['enabled']:
                print(f"⚠️ 子账号 {sub_account['account_name']} 未启用")
                continue
            
            print(f"\n🔍 检查子账号: {sub_account['account_name']}")
            
            # 获取子账号持仓
            sub_positions = get_sub_account_positions(sub_account)
            sub_inst_ids = set(p['inst_id'] for p in sub_positions)
            
            print(f"   子账号已有持仓: {len(sub_positions)}个 ({', '.join(sub_inst_ids)})")
            
            # 找出需要开仓的币种
            for main_pos in loss_positions:
                inst_id = main_pos['inst_id']
                pos_side = main_pos['pos_side']
                profit_rate = main_pos.get('profit_rate', 0)
                
                # 如果子账号没有该仓位
                if inst_id not in sub_inst_ids:
                    print(f"   ⚠️ 发现主账号亏损但子账号未持仓: {inst_id} {pos_side} 亏损:{profit_rate:.2f}%")
                    
                    # 开10U仓位
                    initial_size = sub_account['maintenance_config']['initial_position_usdt']
                    print(f"   🚀 准备开仓 {initial_size}U...")
                    
                    success = open_position_on_sub_account(sub_account, inst_id, pos_side, initial_size)
                    
                    if success:
                        print(f"   ✅ 开仓成功: {inst_id} {pos_side} {initial_size}U")
                    else:
                        print(f"   ❌ 开仓失败: {inst_id} {pos_side}")
                    
                    # 等待一下再开下一个
                    time.sleep(2)
                else:
                    print(f"   ✓ {inst_id} 已有持仓，跳过")
    
    except Exception as e:
        print(f"❌ 检查异常: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 子账号自动开仓守护进程已启动")
    print(f"📊 配置文件: {CONFIG_FILE}")
    print(f"🌐 主账号API: {MAIN_API_URL}")
    print(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    while True:
        try:
            print(f"\n⏰ 开始检查... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            check_and_open_positions()
            print(f"⏳ 等待{CHECK_INTERVAL}秒后继续...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 守护进程已停止")
            break
        except Exception as e:
            print(f"❌ 主循环异常: {e}")
            print(f"⏳ 等待{CHECK_INTERVAL}秒后重试...")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
