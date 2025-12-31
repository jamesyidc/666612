#!/usr/bin/env python3
"""
子账户自动开仓守护进程
功能：监控主账户持仓，如果出现亏损且子账户没有该币种，自动开10U仓位
"""

import json
import time
import requests
import hmac
import base64
from datetime import datetime
import traceback

# 配置
CHECK_INTERVAL = 30  # 30秒检查一次
OPEN_AMOUNT_USDT = 10  # 开仓金额10U
LEVERAGE = 10  # 杠杆10倍

def get_china_time():
    """获取北京时间"""
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=8)))

def log(msg):
    """打印日志"""
    print(f"[{get_china_time().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_sub_account_config():
    """加载子账户配置"""
    try:
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取第一个启用的子账户
        for acc in config['sub_accounts']:
            if acc.get('enabled'):
                return acc
        return None
    except Exception as e:
        log(f"❌ 加载子账户配置失败: {e}")
        return None

def get_main_account_positions():
    """获取主账户持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            # 过滤出亏损的持仓
            losing_positions = [
                pos for pos in data['positions']
                if pos.get('profit_rate', 0) < 0
            ]
            return losing_positions
        return []
    except Exception as e:
        log(f"❌ 获取主账户持仓失败: {e}")
        return []

def get_sub_account_positions(account_name):
    """获取子账户持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            # 返回该子账户的所有持仓币种
            return [pos['inst_id'] for pos in data['positions'] if pos['account_name'] == account_name]
        return []
    except Exception as e:
        log(f"❌ 获取子账户持仓失败: {e}")
        return []

def get_mark_price(api_key, secret_key, passphrase, inst_id):
    """获取标记价格"""
    try:
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        method = 'GET'
        request_path = '/api/v5/public/mark-price'
        params = f'instType=SWAP&instId={inst_id}'
        full_path = f'{request_path}?{params}'
        
        message = timestamp + method + full_path
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
        signature = base64.b64encode(mac.digest()).decode()
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        url = f'https://www.okx.com{full_path}'
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') == '0' and result.get('data'):
            return float(result['data'][0]['markPx'])
        return None
    except Exception as e:
        log(f"❌ 获取标记价格失败: {e}")
        return None

def open_position(account_config, inst_id, pos_side):
    """开仓10U"""
    try:
        api_key = account_config['api_key']
        secret_key = account_config['secret_key']
        passphrase = account_config['passphrase']
        account_name = account_config['account_name']
        
        # 获取标记价格
        mark_price = get_mark_price(api_key, secret_key, passphrase, inst_id)
        if not mark_price:
            log(f"❌ 无法获取{inst_id}的标记价格")
            return False
        
        # 计算开仓数量（10U * 杠杆 / 价格）
        order_size = int((OPEN_AMOUNT_USDT * LEVERAGE) / mark_price)
        if order_size < 1:
            order_size = 1
        
        log(f"📊 准备开仓: {inst_id} {pos_side}, 价格 {mark_price}, 数量 {order_size} 张")
        
        # 调用后端API开仓
        response = requests.post('http://localhost:5000/api/anchor/maintain-sub-account', 
                                json={
                                    'account_name': account_name,
                                    'inst_id': inst_id,
                                    'pos_side': pos_side,
                                    'pos_size': order_size,
                                    'amount': OPEN_AMOUNT_USDT
                                },
                                timeout=60)
        
        result = response.json()
        
        if result.get('success'):
            log(f"✅ 开仓成功: {inst_id} {pos_side} {order_size}张")
            return True
        else:
            log(f"❌ 开仓失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        log(f"❌ 开仓异常: {e}")
        log(traceback.format_exc())
        return False

def main_loop():
    """主循环"""
    log("🚀 子账户自动开仓守护进程启动")
    log(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    log(f"💰 开仓金额: {OPEN_AMOUNT_USDT}U")
    log(f"📊 杠杆倍数: {LEVERAGE}x")
    
    while True:
        try:
            # 加载子账户配置
            sub_account = load_sub_account_config()
            if not sub_account:
                log("❌ 没有启用的子账户，等待30秒后重试")
                time.sleep(CHECK_INTERVAL)
                continue
            
            account_name = sub_account['account_name']
            log(f"\n{'='*60}")
            log(f"🔍 检查账户: {account_name}")
            
            # 获取主账户亏损持仓
            main_losing = get_main_account_positions()
            log(f"📉 主账户亏损持仓数: {len(main_losing)}")
            
            if not main_losing:
                log("✅ 主账户无亏损持仓")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 获取子账户已有持仓
            sub_positions = get_sub_account_positions(account_name)
            log(f"📊 子账户已有持仓: {sub_positions}")
            
            # 检查需要开仓的币种
            for pos in main_losing:
                inst_id = pos['inst_id']
                pos_side = pos['pos_side']
                profit_rate = pos.get('profit_rate', 0)
                
                log(f"  检查 {inst_id} {pos_side}: 主账户收益率 {profit_rate:.2f}%")
                
                if inst_id not in sub_positions:
                    log(f"  ⚠️ 子账户没有 {inst_id}，准备开仓...")
                    
                    # 开仓
                    success = open_position(sub_account, inst_id, pos_side)
                    
                    if success:
                        log(f"  ✅ {inst_id} 开仓成功")
                        # 开仓成功后等待一段时间再检查下一个
                        time.sleep(5)
                    else:
                        log(f"  ❌ {inst_id} 开仓失败")
                else:
                    log(f"  ✓ 子账户已有 {inst_id}")
            
            log(f"{'='*60}\n")
            
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())
        
        # 等待下一次检查
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main_loop()
