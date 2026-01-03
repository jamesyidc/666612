#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逃顶信号数统计记录脚本
每分钟执行一次，统计24小时和2小时内的逃顶信号数，同时获取市场强度等级
"""

import sqlite3
import time
from datetime import datetime, timedelta
import pytz
import requests

def get_china_time():
    """获取北京时间"""
    return datetime.now(pytz.timezone('Asia/Shanghai'))

def get_market_strength():
    """从API获取市场强度等级"""
    try:
        # 获取下跌强度等级
        response = requests.get('http://localhost:5000/api/anchor/decline-strength', timeout=5)
        if response.status_code == 200:
            data = response.json()
            decline_level = data.get('level', 0) if data.get('success') else 0
        else:
            decline_level = 0
        
        # 获取上涨强度等级（基于多单盈利）
        response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                positions = data.get('positions', [])
                long_positions = [p for p in positions if p.get('pos_side') == 'long']
                
                # 计算上涨强度等级
                profit_100_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 100)
                profit_90_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 90)
                profit_80_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 80)
                profit_70_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 70)
                profit_60_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 60)
                profit_40_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 40)
                
                if profit_100_plus >= 1 and profit_40_plus > 10:
                    rise_level = 5
                elif profit_100_plus == 0 and profit_90_plus >= 1 and profit_80_plus >= 1 and profit_40_plus > 10:
                    rise_level = 4
                elif profit_100_plus == 0 and profit_90_plus == 0 and profit_80_plus == 0 and profit_70_plus >= 1 and profit_60_plus >= 2 and profit_40_plus > 8:
                    rise_level = 3
                elif profit_100_plus == 0 and profit_90_plus == 0 and profit_80_plus == 0 and profit_70_plus == 0 and profit_60_plus >= 2 and profit_40_plus > 5:
                    rise_level = 2
                elif profit_100_plus == 0 and profit_90_plus == 0 and profit_80_plus == 0 and profit_70_plus == 0 and profit_60_plus == 0 and profit_40_plus >= 3:
                    rise_level = 1
                else:
                    rise_level = 0
            else:
                rise_level = 0
        else:
            rise_level = 0
        
        return decline_level, rise_level
        
    except:
        return 0, 0

def record_escape_signal_stats():
    """记录逃顶信号数统计"""
    try:
        # 连接数据库
        sr_conn = sqlite3.connect('/home/user/webapp/support_resistance.db', timeout=10.0)
        sr_cursor = sr_conn.cursor()
        
        crypto_conn = sqlite3.connect('/home/user/webapp/databases/crypto_data.db', timeout=10.0)
        crypto_cursor = crypto_conn.cursor()
        
        # 获取当前北京时间
        now = get_china_time()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 计算24小时前和2小时前的时间
        time_24h_ago = now - timedelta(hours=24)
        time_2h_ago = now - timedelta(hours=2)
        
        time_24h_ago_str = time_24h_ago.strftime('%Y-%m-%d %H:%M:%S')
        time_2h_ago_str = time_2h_ago.strftime('%Y-%m-%d %H:%M:%S')
        
        # 统计24小时内的逃顶信号数（scenario_3 + scenario_4的总和）
        sr_cursor.execute('''
            SELECT COALESCE(SUM(scenario_3_count + scenario_4_count), 0)
            FROM support_resistance_snapshots
            WHERE snapshot_time >= ?
        ''', (time_24h_ago_str,))
        
        signal_24h = sr_cursor.fetchone()[0]
        
        # 统计2小时内的逃顶信号数（scenario_3 + scenario_4的总和）
        sr_cursor.execute('''
            SELECT COALESCE(SUM(scenario_3_count + scenario_4_count), 0)
            FROM support_resistance_snapshots
            WHERE snapshot_time >= ?
        ''', (time_2h_ago_str,))
        
        signal_2h = sr_cursor.fetchone()[0]
        
        # 获取历史最大值
        crypto_cursor.execute('''
            SELECT 
                COALESCE(MAX(max_signal_24h), 0) as max_24h,
                COALESCE(MAX(max_signal_2h), 0) as max_2h
            FROM escape_signal_stats
        ''')
        
        max_row = crypto_cursor.fetchone()
        current_max_24h = max_row[0] if max_row else 0
        current_max_2h = max_row[1] if max_row else 0
        
        # 更新最大值
        new_max_24h = max(current_max_24h, signal_24h)
        new_max_2h = max(current_max_2h, signal_2h)
        
        # 获取市场强度等级
        decline_level, rise_level = get_market_strength()
        
        # 插入新记录（包含市场强度等级）
        crypto_cursor.execute('''
            INSERT INTO escape_signal_stats 
            (stat_time, signal_24h_count, signal_2h_count, max_signal_24h, max_signal_2h,
             decline_strength_level, rise_strength_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (now_str, signal_24h, signal_2h, new_max_24h, new_max_2h, decline_level, rise_level))
        
        crypto_conn.commit()
        
        print(f"✅ [{now_str}] 记录完成 | 24H信号: {signal_24h} (最大: {new_max_24h}) | "
              f"2H信号: {signal_2h} (最大: {new_max_2h}) | 下跌强度: {decline_level} | 上涨强度: {rise_level}")
        
        sr_conn.close()
        crypto_conn.close()
        
    except Exception as e:
        print(f"❌ 记录失败: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主循环"""
    print(f"🚀 逃顶信号数统计记录脚本启动")
    print(f"⏰ 采集频率: 每60秒一次")
    print(f"📊 统计内容: 24小时和2小时内的逃顶信号数（scenario_3 + scenario_4）")
    print("-" * 80)
    
    while True:
        try:
            record_escape_signal_stats()
            time.sleep(60)  # 每60秒执行一次
        except KeyboardInterrupt:
            print("\n⏹️  脚本已停止")
            break
        except Exception as e:
            print(f"❌ 主循环错误: {str(e)}")
            time.sleep(60)

if __name__ == '__main__':
    main()
