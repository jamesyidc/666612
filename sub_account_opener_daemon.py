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
OPENED_POSITIONS_FILE = '/home/user/webapp/sub_account_opened_positions.json'  # 已开仓记录
MAIN_API_URL = 'http://localhost:5000'
OKEX_REST_URL = 'https://www.okx.com'
CHECK_INTERVAL = 60  # 每60秒检查一次

def load_config():
    """加载配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_opened_positions():
    """加载已开仓记录"""
    try:
        with open(OPENED_POSITIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_opened_positions(positions):
    """保存已开仓记录"""
    with open(OPENED_POSITIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(positions, f, indent=2, ensure_ascii=False)

def mark_position_opened(account_name, inst_id, pos_side):
    """标记已开仓"""
    positions = load_opened_positions()
    key = f"{account_name}:{inst_id}:{pos_side}"
    positions[key] = {
        'account_name': account_name,
        'inst_id': inst_id,
        'pos_side': pos_side,
        'opened_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    save_opened_positions(positions)

def is_position_opened(account_name, inst_id, pos_side):
    """检查是否已开仓"""
    positions = load_opened_positions()
    key = f"{account_name}:{inst_id}:{pos_side}"
    return key in positions


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

def get_market_strength():
    """获取市场强度等级（上涨和下跌）"""
    try:
        # 获取下跌强度
        decline_url = f"{MAIN_API_URL}/api/anchor/decline-strength"
        decline_response = requests.get(decline_url, timeout=10)
        decline_level = 0
        
        if decline_response.status_code == 200:
            decline_data = decline_response.json()
            if decline_data.get('success'):
                decline_level = decline_data.get('data', {}).get('strength_level', 0)
        
        # 计算上涨强度（基于多单盈利情况）
        positions_url = f"{MAIN_API_URL}/api/anchor-system/current-positions"
        positions_response = requests.get(positions_url, params={'trade_mode': 'real'}, timeout=10)
        rise_level = 0
        
        if positions_response.status_code == 200:
            pos_data = positions_response.json()
            if pos_data.get('success'):
                positions = pos_data.get('positions', [])
                
                # 统计多单盈利情况
                long_profits = [p['profit_rate'] for p in positions if p.get('pos_side') == 'long']
                
                if long_profits:
                    count_100 = len([p for p in long_profits if p >= 100])
                    count_90 = len([p for p in long_profits if p >= 90])
                    count_80 = len([p for p in long_profits if p >= 80])
                    count_70 = len([p for p in long_profits if p >= 70])
                    count_60 = len([p for p in long_profits if p >= 60])
                    count_50 = len([p for p in long_profits if p >= 50])
                    count_40 = len([p for p in long_profits if p >= 40])
                    
                    # 判断上涨等级（与下跌等级规则一致）
                    if count_100 >= 1:
                        rise_level = 5
                    elif count_100 == 0 and count_90 >= 1 and count_80 >= 1:
                        rise_level = 4
                    elif count_100 == 0 and count_90 == 0 and count_80 == 0 and count_70 >= 1 and count_60 >= 2:
                        rise_level = 3
                    elif count_100 == 0 and count_90 == 0 and count_80 == 0 and count_70 == 0 and count_60 >= 2:
                        rise_level = 2
                    elif count_100 == 0 and count_90 == 0 and count_80 == 0 and count_70 == 0 and count_60 == 0 and count_50 == 0 and count_40 >= 3:
                        rise_level = 1
        
        return {
            'decline_level': decline_level,
            'rise_level': rise_level
        }
    except Exception as e:
        print(f"❌ 获取市场强度异常: {e}")
        return {'decline_level': 0, 'rise_level': 0}

def get_sub_account_positions(sub_account):
    """获取子账号持仓"""
    try:
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        request_path = '/api/v5/account/positions'
        query_string = 'instType=SWAP'
        
        # GET请求需要在签名中包含查询参数
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        message = timestamp + 'GET' + request_path + '?' + query_string
        mac = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        signature = base64.b64encode(mac.digest()).decode('utf-8')
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
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
        
        # 先设置杠杆为10倍（逐仓模式）
        print(f"🔧 设置杠杆为10倍（逐仓模式）...")
        leverage_path = '/api/v5/account/set-leverage'
        leverage_data = {
            'instId': inst_id,
            'lever': '10',
            'mgnMode': 'isolated',  # 逐仓模式
            'posSide': pos_side
        }
        leverage_headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', leverage_path, leverage_data)
        leverage_url = f"{OKEX_REST_URL}{leverage_path}"
        leverage_response = requests.post(leverage_url, headers=leverage_headers, json=leverage_data, timeout=10)
        
        if leverage_response.status_code == 200:
            leverage_result = leverage_response.json()
            if leverage_result.get('code') == '0':
                print(f"✅ 杠杆设置成功: 10x")
            else:
                print(f"⚠️ 杠杆设置失败: {leverage_result.get('msg')} (继续开仓)")
        
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
        # 保证金 = (持仓价值 / 杠杆)
        # 持仓价值 = 张数 × 价格 × 合约面值(1)
        # 所以：张数 = (保证金 × 杠杆) / 价格
        lever = 10  # 固定10倍杠杆
        size = round((size_usdt * lever) / last_price)
        
        if size < 1:
            size = 1  # 至少1张
        
        print(f"📊 准备开仓: {inst_id} {pos_side} 数量:{size}张 价格:${last_price:.4f} 杠杆:{lever}x 目标保证金:{size_usdt}U")
        
        # 下单（逐仓模式）
        request_path = '/api/v5/trade/order'
        order_data = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式
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
            
            account_name = sub_account['account_name']
            
            # 获取子账号持仓
            sub_positions = get_sub_account_positions(sub_account)
            sub_inst_ids = set(p['inst_id'] for p in sub_positions)
            
            # 如果API获取失败（401错误），使用本地记录
            if not sub_positions:
                print(f"   ⚠️ 无法从API获取持仓，使用本地记录")
                opened_positions = load_opened_positions()
                for key, pos in opened_positions.items():
                    if pos['account_name'] == account_name:
                        sub_inst_ids.add(pos['inst_id'])
            
            print(f"   子账号已有持仓: {len(sub_inst_ids)}个 ({', '.join(sub_inst_ids) if sub_inst_ids else '无'})")
            
            # 找出需要开仓的币种
            for main_pos in loss_positions:
                inst_id = main_pos['inst_id']
                pos_side = main_pos['pos_side']
                profit_rate = main_pos.get('profit_rate', 0)
                
                # 检查跟单开关
                if pos_side == 'short':
                    if not config.get('follow_short_loss_enabled', False):
                        print(f"   ⚠️ 跟空单亏损开单未启用，跳过 {inst_id} {pos_side}")
                        continue
                elif pos_side == 'long':
                    if not config.get('follow_long_loss_enabled', False):
                        print(f"   ⚠️ 跟多单亏损开单未启用，跳过 {inst_id} {pos_side}")
                        continue
                
                # 🔥 新增：检查市场强度等级（需要达到5级才允许开单）
                market_strength = get_market_strength()
                
                if pos_side == 'short':
                    # 空单亏损需要下跌强度>=5
                    if market_strength['decline_level'] < 5:
                        print(f"   ⚠️ 下跌强度等级{market_strength['decline_level']}不足（需要>=5），跳过 {inst_id} {pos_side}")
                        continue
                    else:
                        print(f"   ✅ 下跌强度等级{market_strength['decline_level']}满足条件（>=5）")
                elif pos_side == 'long':
                    # 多单亏损需要上涨强度>=5
                    if market_strength['rise_level'] < 5:
                        print(f"   ⚠️ 上涨强度等级{market_strength['rise_level']}不足（需要>=5），跳过 {inst_id} {pos_side}")
                        continue
                    else:
                        print(f"   ✅ 上涨强度等级{market_strength['rise_level']}满足条件（>=5）")
                
                # 如果子账号没有该仓位
                if inst_id not in sub_inst_ids:
                    # 检查本地记录，避免重复开仓
                    if is_position_opened(account_name, inst_id, pos_side):
                        print(f"   ✓ {inst_id} {pos_side} 已记录开仓，跳过")
                        continue
                    
                    print(f"   ⚠️ 发现主账号亏损但子账号未持仓: {inst_id} {pos_side} 亏损:{profit_rate:.2f}%")
                    
                    # 开10U仓位
                    initial_size = sub_account['maintenance_config']['initial_position_usdt']
                    print(f"   🚀 准备开仓 {initial_size}U...")
                    
                    success = open_position_on_sub_account(sub_account, inst_id, pos_side, initial_size)
                    
                    if success:
                        print(f"   ✅ 开仓成功: {inst_id} {pos_side} {initial_size}U")
                        # 记录已开仓
                        mark_position_opened(account_name, inst_id, pos_side)
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
