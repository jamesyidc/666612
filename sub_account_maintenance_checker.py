#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子账号自动维护检查器
针对子账号持仓执行3次超级维护策略：
- 第1次：-10% → 买入100U → 平仓剩余10U
- 第2次：-10% → 买入100U → 平仓剩余10U
- 第3次：-10% → 买入100U → 平仓剩余10U
- 第3次后：-20%止损（全部平仓）
"""

import json
import time
import requests
import hmac
import base64
import hashlib
from datetime import datetime
from collections import defaultdict

# 配置
CONFIG_FILE = '/home/user/webapp/sub_account_config.json'
MAINTENANCE_COUNT_FILE = '/home/user/webapp/sub_account_maintenance_count.json'
OKEX_REST_URL = 'https://www.okx.com'
CHECK_INTERVAL = 10  # 每10秒检查一次

def load_config():
    """加载配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_maintenance_count():
    """加载维护次数记录"""
    try:
        with open(MAINTENANCE_COUNT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_maintenance_count(counts):
    """保存维护次数记录"""
    with open(MAINTENANCE_COUNT_FILE, 'w', encoding='utf-8') as f:
        json.dump(counts, f, indent=2, ensure_ascii=False)

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
            return []
        
        data = response.json()
        if data.get('code') != '0':
            return []
        
        # 过滤有持仓的并计算盈亏率
        positions = []
        for pos in data.get('data', []):
            pos_size = float(pos.get('pos', 0))
            if pos_size != 0:
                avg_px = float(pos.get('avgPx', 0))
                mark_px = float(pos.get('markPx', 0))
                upl = float(pos.get('upl', 0))
                notional_usd = float(pos.get('notionalUsd', 0))
                
                # 计算盈亏率
                if notional_usd != 0:
                    profit_rate = (upl / abs(notional_usd)) * 100
                else:
                    profit_rate = 0
                
                positions.append({
                    'inst_id': pos['instId'],
                    'pos_side': pos['posSide'],
                    'pos_size': pos_size,
                    'avg_price': avg_px,
                    'mark_price': mark_px,
                    'upl': upl,
                    'notional_usd': notional_usd,
                    'profit_rate': profit_rate,
                    'margin': float(pos.get('margin', 0))
                })
        
        return positions
    except Exception as e:
        print(f"❌ 获取子账号持仓异常: {e}")
        return []

def execute_super_maintenance(sub_account, position, maintenance_count):
    """执行超级维护"""
    try:
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        current_size = abs(position['pos_size'])
        mark_price = position['mark_price']
        
        # 配置
        buy_amount = sub_account['maintenance_config']['buy_amount_usdt']
        keep_margin = sub_account['maintenance_config']['keep_margin_usdt']
        
        print(f"\n🔧 开始超级维护 #{maintenance_count}")
        print(f"   币种: {inst_id} {pos_side}")
        print(f"   当前持仓: {current_size} 盈亏率: {position['profit_rate']:.2f}%")
        
        # 步骤1: 买入100U
        buy_size = round(buy_amount / mark_price)
        if buy_size < 1:
            buy_size = 1
        
        print(f"   📈 买入 {buy_amount}U (约{buy_size}张)...")
        
        request_path = '/api/v5/trade/order'
        buy_order = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': 'buy' if pos_side == 'long' else 'sell',
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(buy_size)
        }
        
        headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', request_path, buy_order)
        response = requests.post(f"{OKEX_REST_URL}{request_path}", headers=headers, json=buy_order, timeout=10)
        
        if response.status_code != 200 or response.json().get('code') != '0':
            print(f"   ❌ 买入失败")
            return False
        
        buy_order_id = response.json()['data'][0]['ordId']
        print(f"   ✅ 买入成功 订单ID:{buy_order_id}")
        
        # 等待订单成交
        time.sleep(2)
        
        # 步骤2: 平仓到剩余10U保证金
        # 重新获取持仓
        positions = get_sub_account_positions(sub_account)
        current_pos = next((p for p in positions if p['inst_id'] == inst_id and p['pos_side'] == pos_side), None)
        
        if not current_pos:
            print(f"   ❌ 无法获取最新持仓")
            return False
        
        new_size = abs(current_pos['pos_size'])
        new_margin = current_pos['margin']
        
        print(f"   📊 买入后持仓: {new_size}张 保证金:{new_margin:.2f}U")
        
        # 计算需要平仓的数量（保留10U保证金）
        # 保证金 = 持仓价值 / 杠杆
        # 假设杠杆为10倍，保留10U需要保留100U持仓价值 = 100/mark_price 张
        keep_size = round(keep_margin * 10 / mark_price)  # 10倍杠杆
        close_size = new_size - keep_size
        
        if close_size < 1:
            print(f"   ⚠️ 无需平仓")
            return True
        
        print(f"   📉 平仓 {close_size}张 (保留{keep_size}张)...")
        
        close_order = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': 'sell' if pos_side == 'long' else 'buy',
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(close_size)
        }
        
        headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', request_path, close_order)
        response = requests.post(f"{OKEX_REST_URL}{request_path}", headers=headers, json=close_order, timeout=10)
        
        if response.status_code != 200 or response.json().get('code') != '0':
            print(f"   ❌ 平仓失败")
            return False
        
        close_order_id = response.json()['data'][0]['ordId']
        print(f"   ✅ 平仓成功 订单ID:{close_order_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 超级维护异常: {e}")
        return False

def execute_stop_loss(sub_account, position):
    """执行止损（全部平仓）"""
    try:
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        close_size = abs(position['pos_size'])
        
        print(f"\n🛑 执行止损")
        print(f"   币种: {inst_id} {pos_side}")
        print(f"   平仓数量: {close_size}张")
        print(f"   盈亏率: {position['profit_rate']:.2f}%")
        
        request_path = '/api/v5/trade/order'
        close_order = {
            'instId': inst_id,
            'tdMode': 'cross',
            'side': 'sell' if pos_side == 'long' else 'buy',
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(int(close_size))
        }
        
        headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', request_path, close_order)
        response = requests.post(f"{OKEX_REST_URL}{request_path}", headers=headers, json=close_order, timeout=10)
        
        if response.status_code != 200 or response.json().get('code') != '0':
            print(f"   ❌ 止损失败: {response.json().get('msg')}")
            return False
        
        order_id = response.json()['data'][0]['ordId']
        print(f"   ✅ 止损成功 订单ID:{order_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 止损异常: {e}")
        return False

def check_and_maintain():
    """检查并维护子账号"""
    try:
        # 加载配置
        config = load_config()
        maintenance_counts = load_maintenance_count()
        
        # 今天日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 遍历子账号
        for sub_account in config['sub_accounts']:
            if not sub_account['enabled']:
                continue
            
            account_name = sub_account['account_name']
            print(f"\n🔍 检查子账号: {account_name}")
            
            # 获取持仓
            positions = get_sub_account_positions(sub_account)
            
            if not positions:
                print(f"   ✅ 无持仓")
                continue
            
            print(f"   📊 持仓数量: {len(positions)}个")
            
            # 检查每个持仓
            for pos in positions:
                inst_id = pos['inst_id']
                pos_side = pos['pos_side']
                profit_rate = pos['profit_rate']
                
                key = f"{account_name}:{inst_id}:{pos_side}:{today}"
                current_count = maintenance_counts.get(key, 0)
                
                loss_threshold = sub_account['maintenance_config']['loss_threshold']
                stop_loss_threshold = sub_account['maintenance_config']['stop_loss_threshold']
                max_count = sub_account['maintenance_config']['max_maintenance_count']
                
                # 检查超级维护开关
                super_maintain_enabled = False
                if pos_side == 'long':
                    super_maintain_enabled = sub_account.get('super_maintain_long_enabled', False)
                else:  # short
                    super_maintain_enabled = sub_account.get('super_maintain_short_enabled', False)
                
                if not super_maintain_enabled:
                    print(f"   ⏸️ {inst_id} {pos_side} 超级维护未启用")
                    continue
                
                print(f"   📈 {inst_id} {pos_side} 盈亏:{profit_rate:.2f}% 维护次数:{current_count}/{max_count}")
                
                # 检查止损条件（第3次维护后）
                if current_count >= max_count and profit_rate <= stop_loss_threshold:
                    print(f"   ⚠️ 触发止损条件: {profit_rate:.2f}% <= {stop_loss_threshold}%")
                    success = execute_stop_loss(sub_account, pos)
                    
                    if success:
                        # 清除维护次数
                        if key in maintenance_counts:
                            del maintenance_counts[key]
                        save_maintenance_count(maintenance_counts)
                        print(f"   ✅ 止损完成")
                    continue
                
                # 检查维护条件
                if current_count < max_count and profit_rate <= loss_threshold:
                    print(f"   ⚠️ 触发维护条件: {profit_rate:.2f}% <= {loss_threshold}%")
                    success = execute_super_maintenance(sub_account, pos, current_count + 1)
                    
                    if success:
                        # 增加维护次数
                        maintenance_counts[key] = current_count + 1
                        save_maintenance_count(maintenance_counts)
                        print(f"   ✅ 维护完成 当前次数:{maintenance_counts[key]}/{max_count}")
                    
                    # 等待一下再检查下一个
                    time.sleep(5)
    
    except Exception as e:
        print(f"❌ 检查异常: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 子账号自动维护检查器已启动")
    print(f"📊 配置文件: {CONFIG_FILE}")
    print(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    while True:
        try:
            print(f"\n⏰ 开始检查... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            check_and_maintain()
            print(f"⏳ 等待{CHECK_INTERVAL}秒后继续...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 检查器已停止")
            break
        except Exception as e:
            print(f"❌ 主循环异常: {e}")
            print(f"⏳ 等待{CHECK_INTERVAL}秒后重试...")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
