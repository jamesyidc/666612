#!/usr/bin/env python3
"""
持仓盈利极值跟踪守护进程
只监控你的持仓盈亏率，记录最高盈利率和最大亏损率
不从OKX获取市场极值
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
import hmac
import base64

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

def get_current_positions():
    """从Flask API获取当前实盘持仓"""
    try:
        # 使用Flask API获取持仓
        flask_api_url = 'http://localhost:5000/api/anchor-system/current-positions?trade_mode=real'
        response = requests.get(flask_api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                positions = data.get('positions', [])
                return positions
        
        print(f"⚠️  Flask API返回错误: {response.text[:200]}")
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
            SELECT created_at, updated_time, timestamp
            FROM position_opens 
            WHERE inst_id = ? AND pos_side = ? AND open_size != 0
            ORDER BY created_at DESC
            LIMIT 1
        ''', (inst_id, pos_side))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # 优先使用 created_at，如果没有则使用 updated_time或timestamp
            return row['created_at'] or row['updated_time'] or row['timestamp']
        return None
    except Exception as e:
        print(f"❌ 获取开仓时间失败 {inst_id} {pos_side}: {e}")
        return None

def insert_to_history_records(inst_id, pos_side, record_type, profit_rate, pos_size, avg_price, mark_price):
    """插入历史极值记录到anchor_system.db"""
    try:
        conn = sqlite3.connect('/home/user/webapp/anchor_system.db')
        cursor = conn.cursor()
        
        now = get_beijing_time()
        
        # 先删除旧记录
        cursor.execute('''
            DELETE FROM anchor_real_profit_records 
            WHERE inst_id = ? AND pos_side = ? AND record_type = ?
        ''', (inst_id, pos_side, record_type))
        
        # 插入新记录
        cursor.execute('''
            INSERT INTO anchor_real_profit_records 
            (inst_id, pos_side, record_type, profit_rate, timestamp, pos_size, avg_price, mark_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (inst_id, pos_side, record_type, profit_rate, now, pos_size, avg_price, mark_price))
        
        conn.commit()
        conn.close()
        print(f"📝 历史记录已更新: {inst_id} {pos_side} {record_type} {profit_rate:.2f}%")
        return True
    except Exception as e:
        print(f"❌ 插入历史记录失败 {inst_id} {pos_side}: {e}")
        traceback.print_exc()
        return False

def update_profit_extremes(inst_id, pos_side, open_time, current_profit_rate, pos_info=None):
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
            
            updated = False
            
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
                
                # 插入历史极值记录
                if pos_info:
                    insert_to_history_records(
                        inst_id, pos_side, 'max_profit', current_profit_rate,
                        pos_info.get('pos_size', 0),
                        pos_info.get('avg_price', 0),
                        pos_info.get('mark_price', 0)
                    )
                
                updated = True
            
            # 检查是否需要更新最大亏损率
            if current_profit_rate < max_loss_rate:
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
                
                # 插入历史极值记录
                if pos_info:
                    insert_to_history_records(
                        inst_id, pos_side, 'max_loss', current_profit_rate,
                        pos_info.get('pos_size', 0),
                        pos_info.get('avg_price', 0),
                        pos_info.get('mark_price', 0)
                    )
                
                updated = True
            
            # 如果没有更新极值，只更新当前盈亏率
            if not updated:
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
            print(f"✨ {inst_id} {pos_side} 创建极值记录: 当前盈亏率 {current_profit_rate:.2f}%")
        
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
    
    # 获取当前持仓
    positions = get_current_positions()
    
    if not positions or len(positions) == 0:
        print("ℹ️  当前没有持仓")
        return
    
    print(f"📊 发现 {len(positions)} 个持仓")
    
    tracked_count = 0
    
    for pos in positions:
        inst_id = pos.get('inst_id')  # Flask API返回的是inst_id
        pos_side = pos.get('pos_side')  # Flask API返回的是pos_side
        pos_size = float(pos.get('pos_size', 0))
        
        # 跳过空仓
        if pos_size == 0:
            continue
        
        # 获取当前盈亏率（Flask API已经计算好了）
        try:
            current_profit_rate = float(pos.get('profit_rate', 0))
        except:
            print(f"⚠️  {inst_id} {pos_side} 无法获取盈亏率")
            continue
        
        # 获取开仓时间
        open_time = get_position_open_time(inst_id, pos_side)
        if not open_time:
            print(f"⚠️  {inst_id} {pos_side} 无法获取开仓时间，使用当前时间")
            open_time = get_beijing_time()
        
        # 更新极值
        if update_profit_extremes(inst_id, pos_side, open_time, current_profit_rate, pos):
            tracked_count += 1
            print(f"   ✓ {inst_id} {pos_side}: 当前 {current_profit_rate:+.2f}%")
    
    print(f"\n✅ 成功跟踪 {tracked_count} 个持仓的盈利极值")

def main():
    """主循环"""
    print("="*60)
    print("🚀 持仓盈利极值跟踪守护进程启动")
    print("="*60)
    print(f"📍 工作目录: {os.getcwd()}")
    print(f"🕐 扫描间隔: 60秒")
    print(f"📊 功能: 监控每个持仓的盈亏率")
    print(f"📈 记录: 最高盈利率（正值）")
    print(f"📉 记录: 最大亏损率（负值）")
    print(f"❌ 不获取: OKX市场极值")
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
