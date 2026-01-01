#!/usr/bin/env python3
"""
持仓盈利极值跟踪守护进程
记录每个持仓的最高盈利率和最大亏损率
"""

import time
import sqlite3
import json
import os
import sys
import traceback
from datetime import datetime
import pytz
import requests

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

def get_okx_config():
    """读取OKX配置（主账号）"""
    try:
        # 读取配置文件
        config_file = '/home/user/webapp/sub_account_config.json'
        if not os.path.exists(config_file):
            print(f"⚠️  配置文件不存在: {config_file}")
            return None
            
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        # 获取主账号配置
        if 'main_account' in data:
            return data['main_account']
        elif 'sub_accounts' in data and len(data['sub_accounts']) > 0:
            return data['sub_accounts'][0]
        
        print("⚠️  配置文件中没有找到账号信息")
        return None
        
    except Exception as e:
        print(f"❌ 读取配置失败: {e}")
        traceback.print_exc()
        return None

def get_current_positions():
    """从Flask API获取当前所有持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('positions', [])
        return []
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return []

def get_position_open_time(inst_id, pos_side):
    """从数据库获取持仓开仓时间"""
    try:
        conn = sqlite3.connect('/home/user/webapp/trading_decision.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT created_at, updated_at 
            FROM position_opens 
            WHERE inst_id = ? AND pos_side = ? AND open_size != 0
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (inst_id, pos_side))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # 优先使用 created_at，如果没有则使用 updated_at
            return row['created_at'] or row['updated_at']
        return None
    except Exception as e:
        print(f"❌ 获取开仓时间失败 {inst_id} {pos_side}: {e}")
        return None

def update_profit_extremes(inst_id, pos_side, open_time, current_profit_rate):
    """更新盈利极值记录"""
    try:
        conn = sqlite3.connect('/home/user/webapp/trading_decision.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = get_beijing_time()
        
        # 查询现有记录
        cursor.execute('''
            SELECT max_profit_rate, max_loss_rate 
            FROM position_profit_extremes 
            WHERE inst_id = ? AND pos_side = ? AND open_time = ?
        ''', (inst_id, pos_side, open_time))
        
        row = cursor.fetchone()
        
        if row:
            # 更新现有记录
            max_profit_rate = row['max_profit_rate']
            max_loss_rate = row['max_loss_rate']
            
            # 检查是否需要更新最高盈利率
            if current_profit_rate > max_profit_rate:
                cursor.execute('''
                    UPDATE position_profit_extremes 
                    SET max_profit_rate = ?,
                        max_profit_time = ?,
                        current_profit_rate = ?,
                        updated_at = ?
                    WHERE inst_id = ? AND pos_side = ? AND open_time = ?
                ''', (current_profit_rate, now, current_profit_rate, now, 
                      inst_id, pos_side, open_time))
                print(f"📈 {inst_id} {pos_side} 新高盈利: {current_profit_rate:.2f}% (之前: {max_profit_rate:.2f}%)")
            
            # 检查是否需要更新最大亏损率
            elif current_profit_rate < max_loss_rate:
                cursor.execute('''
                    UPDATE position_profit_extremes 
                    SET max_loss_rate = ?,
                        max_loss_time = ?,
                        current_profit_rate = ?,
                        updated_at = ?
                    WHERE inst_id = ? AND pos_side = ? AND open_time = ?
                ''', (current_profit_rate, now, current_profit_rate, now,
                      inst_id, pos_side, open_time))
                print(f"📉 {inst_id} {pos_side} 新低亏损: {current_profit_rate:.2f}% (之前: {max_loss_rate:.2f}%)")
            
            else:
                # 只更新当前盈亏率
                cursor.execute('''
                    UPDATE position_profit_extremes 
                    SET current_profit_rate = ?,
                        updated_at = ?
                    WHERE inst_id = ? AND pos_side = ? AND open_time = ?
                ''', (current_profit_rate, now, inst_id, pos_side, open_time))
        
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO position_profit_extremes 
                (inst_id, pos_side, open_time, max_profit_rate, max_profit_time, 
                 max_loss_rate, max_loss_time, current_profit_rate, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (inst_id, pos_side, open_time, 
                  current_profit_rate if current_profit_rate > 0 else 0,
                  now if current_profit_rate > 0 else None,
                  current_profit_rate if current_profit_rate < 0 else 0,
                  now if current_profit_rate < 0 else None,
                  current_profit_rate, now))
            print(f"✨ {inst_id} {pos_side} 创建极值记录: {current_profit_rate:.2f}%")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 更新极值失败 {inst_id} {pos_side}: {e}")
        traceback.print_exc()
        return False

def track_all_positions():
    """跟踪所有持仓的盈利极值"""
    print(f"\n{'='*60}")
    print(f"🔍 开始扫描持仓盈利极值 - {get_beijing_time()}")
    print(f"{'='*60}")
    
    # 获取当前持仓（从Flask API）
    positions = get_current_positions()
    
    if not positions or len(positions) == 0:
        print("ℹ️  当前没有持仓")
        return
    
    print(f"📊 发现 {len(positions)} 个持仓")
    
    tracked_count = 0
    
    for pos in positions:
        # Flask API返回的格式
        inst_id = pos.get('inst_id')
        pos_side = pos.get('pos_side')
        pos_size = float(pos.get('pos_size', 0))
        
        # 跳过空仓
        if pos_size == 0:
            continue
        
        # 获取当前盈亏率（Flask API已经计算好了）
        current_profit_rate = float(pos.get('profit_rate', 0))
        
        # 获取开仓时间
        open_time = get_position_open_time(inst_id, pos_side)
        if not open_time:
            print(f"⚠️  {inst_id} {pos_side} 无法获取开仓时间，跳过")
            continue
        
        # 更新极值
        if update_profit_extremes(inst_id, pos_side, open_time, current_profit_rate):
            tracked_count += 1
    
    print(f"\n✅ 成功跟踪 {tracked_count} 个持仓的盈利极值")

def main():
    """主循环"""
    print("="*60)
    print("🚀 持仓盈利极值跟踪守护进程启动")
    print("="*60)
    print(f"📍 工作目录: {os.getcwd()}")
    print(f"🕐 扫描间隔: 60秒")
    print(f"📊 功能: 跟踪每个持仓的最高盈利率和最大亏损率")
    print("="*60)
    
    while True:
        try:
            track_all_positions()
            
            # 等待60秒
            print(f"\n⏰ 等待60秒后进行下一次扫描...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  收到退出信号，正在停止...")
            break
        except Exception as e:
            print(f"\n❌ 主循环错误: {e}")
            traceback.print_exc()
            print("⏰ 等待60秒后重试...")
            time.sleep(60)
    
    print("\n👋 守护进程已停止")

if __name__ == '__main__':
    main()
