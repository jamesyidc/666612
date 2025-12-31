#!/usr/bin/env python3
"""
子账户止盈守护进程
功能：
1. 规则1：交易对盈利超过30%时止盈50%仓位
2. 规则2：主账户反向交易对亏损时，止盈子账户对应交易对
"""

import json
import time
import requests
from datetime import datetime, timezone, timedelta
import traceback

# 配置
CHECK_INTERVAL = 10  # 10秒检查一次（从30秒改为10秒）
PROFIT_THRESHOLD = 30  # 盈利30%触发止盈
TAKE_PROFIT_RATIO = 0.5  # 止盈50%仓位
MAIN_ACCOUNT_LOSS_THRESHOLD = 0  # 主账户反向交易对亏损即触发

# 止盈记录文件
TAKE_PROFIT_RECORDS_FILE = 'sub_account_take_profit_records.json'

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def get_china_today():
    """获取北京时间的今天日期"""
    return get_china_time().strftime('%Y-%m-%d')

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

def get_sub_account_positions(account_name):
    """获取子账户持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            return [pos for pos in data['positions'] if pos['account_name'] == account_name]
        return []
    except Exception as e:
        log(f"❌ 获取子账户持仓失败: {e}")
        return []

def get_main_account_positions():
    """获取主账户持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            return data['positions']
        return []
    except Exception as e:
        log(f"❌ 获取主账户持仓失败: {e}")
        return []

def save_take_profit_record(account_name, inst_id, pos_side, profit_rate, close_size, reason):
    """保存止盈记录"""
    try:
        try:
            with open(TAKE_PROFIT_RECORDS_FILE, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except FileNotFoundError:
            records = []
        
        record = {
            'account_name': account_name,
            'inst_id': inst_id,
            'pos_side': pos_side,
            'profit_rate': profit_rate,
            'close_size': close_size,
            'reason': reason,
            'timestamp': get_china_time().strftime('%Y-%m-%d %H:%M:%S'),
            'date': get_china_today()
        }
        
        records.append(record)
        
        with open(TAKE_PROFIT_RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        log(f"❌ 保存止盈记录失败: {e}")
        return False

def execute_take_profit(account_config, inst_id, pos_side, pos_size, profit_rate, reason):
    """执行止盈操作"""
    try:
        account_name = account_config['account_name']
        
        # 计算止盈数量（50%仓位）
        close_size = int(pos_size * TAKE_PROFIT_RATIO)
        
        if close_size <= 0:
            log(f"⚠️  持仓量太小，无法止盈: {pos_size}")
            return False
        
        log(f"🎯 执行止盈: {inst_id} {pos_side}")
        log(f"   当前收益率: {profit_rate:.2f}%")
        log(f"   止盈原因: {reason}")
        log(f"   持仓数量: {pos_size}")
        log(f"   止盈数量: {close_size} (50%)")
        
        # 调用后端API执行止盈（部分平仓）
        response = requests.post('http://localhost:5000/api/anchor/close-sub-account-position', 
                                json={
                                    'account_name': account_name,
                                    'inst_id': inst_id,
                                    'pos_side': pos_side,
                                    'close_size': close_size,
                                    'reason': reason
                                },
                                timeout=30)
        
        result = response.json()
        
        if result.get('success'):
            # 保存止盈记录
            save_take_profit_record(account_name, inst_id, pos_side, profit_rate, close_size, reason)
            
            log(f"✅ 止盈成功!")
            log(f"   平仓订单ID: {result.get('order_id', 'N/A')}")
            log(f"   平仓数量: {close_size}")
            log(f"   剩余持仓: {pos_size - close_size}")
            
            return True
        else:
            log(f"❌ 止盈失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        log(f"❌ 止盈异常: {e}")
        log(traceback.format_exc())
        return False

def check_rule1_profit_threshold(sub_account, positions):
    """规则1：检查盈利超过30%的持仓"""
    log(f"  🔍 规则1：检查盈利>{PROFIT_THRESHOLD}%的持仓")
    
    for pos in positions:
        inst_id = pos['inst_id']
        pos_side = pos['pos_side']
        profit_rate = pos.get('profit_rate', 0)
        pos_size = pos.get('pos_size', 0)
        
        # 检查是否满足规则1
        if profit_rate > PROFIT_THRESHOLD:
            log(f"    ⚠️  {inst_id} {pos_side} 盈利{profit_rate:.2f}% > {PROFIT_THRESHOLD}%，触发规则1")
            
            # 执行止盈
            success = execute_take_profit(
                sub_account, 
                inst_id, 
                pos_side, 
                pos_size, 
                profit_rate, 
                f"规则1：盈利超过{PROFIT_THRESHOLD}%"
            )
            
            if success:
                log(f"    ✅ 规则1止盈完成")
                time.sleep(5)  # 等待5秒
            else:
                log(f"    ❌ 规则1止盈失败")
        else:
            log(f"    ✓ {inst_id} {pos_side} 盈利{profit_rate:.2f}%，未达到阈值")

def check_rule2_reverse_loss(sub_account, sub_positions, main_positions):
    """规则2：检查主账户反向交易对亏损"""
    log(f"  🔍 规则2：检查主账户反向交易对亏损")
    
    # 构建主账户持仓字典：{inst_id: {pos_side: profit_rate}}
    main_pos_dict = {}
    for pos in main_positions:
        inst_id = pos['inst_id']
        pos_side = pos['pos_side']
        profit_rate = pos.get('profit_rate', 0)
        
        if inst_id not in main_pos_dict:
            main_pos_dict[inst_id] = {}
        main_pos_dict[inst_id][pos_side] = profit_rate
    
    # 检查子账户每个持仓
    for sub_pos in sub_positions:
        inst_id = sub_pos['inst_id']
        pos_side = sub_pos['pos_side']
        sub_profit_rate = sub_pos.get('profit_rate', 0)
        pos_size = sub_pos.get('pos_size', 0)
        
        # 确定反向方向
        reverse_side = 'short' if pos_side == 'long' else 'long'
        
        # 检查主账户是否有反向持仓且亏损
        if inst_id in main_pos_dict and reverse_side in main_pos_dict[inst_id]:
            main_reverse_profit = main_pos_dict[inst_id][reverse_side]
            
            # 主账户反向交易对亏损（收益率<0）
            if main_reverse_profit < MAIN_ACCOUNT_LOSS_THRESHOLD:
                log(f"    ⚠️  {inst_id} 主账户{reverse_side}亏损{main_reverse_profit:.2f}%，触发规则2")
                log(f"        子账户{pos_side}盈利{sub_profit_rate:.2f}%")
                
                # 执行止盈
                success = execute_take_profit(
                    sub_account,
                    inst_id,
                    pos_side,
                    pos_size,
                    sub_profit_rate,
                    f"规则2：主账户{reverse_side}亏损{main_reverse_profit:.2f}%"
                )
                
                if success:
                    log(f"    ✅ 规则2止盈完成")
                    time.sleep(5)
                else:
                    log(f"    ❌ 规则2止盈失败")
            else:
                log(f"    ✓ {inst_id} 主账户{reverse_side}盈利{main_reverse_profit:.2f}%，未触发")
        else:
            log(f"    ✓ {inst_id} 主账户无反向持仓")

def main_loop():
    """主循环"""
    log("🚀 子账户止盈守护进程启动")
    log(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    log(f"📈 规则1：盈利>{PROFIT_THRESHOLD}%时止盈{int(TAKE_PROFIT_RATIO*100)}%仓位")
    log(f"📉 规则2：主账户反向交易对亏损时止盈子账户对应交易对")
    
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
            
            # 获取子账户持仓
            sub_positions = get_sub_account_positions(account_name)
            log(f"📊 子账户持仓数量: {len(sub_positions)}")
            
            if not sub_positions:
                log("✅ 无子账户持仓")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 获取主账户持仓（用于规则2）
            main_positions = get_main_account_positions()
            log(f"📊 主账户持仓数量: {len(main_positions)}")
            
            # 规则1：检查盈利超过30%的持仓
            check_rule1_profit_threshold(sub_account, sub_positions)
            
            # 规则2：检查主账户反向交易对亏损
            check_rule2_reverse_loss(sub_account, sub_positions, main_positions)
            
            log(f"{'='*60}\n")
            
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())
        
        # 等待下一次检查
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main_loop()
