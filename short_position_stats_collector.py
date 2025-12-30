#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
空单盈利分级统计收集器
每3分钟收集一次空单持仓的盈利分级统计，存入历史快照数据库
统计项目：
- 空单盈利≥70%
- 空单盈利≥60%
- 空单盈利≥50%
- 空单盈利≤20%
- 空单盈利≤10%
- 空单亏损（<0%）
"""

import sqlite3
import requests
import time
import json
from datetime import datetime

# 配置
DB_PATH = '/home/user/webapp/anchor_snapshots.db'
API_BASE_URL = 'http://localhost:5000'
COLLECTION_INTERVAL = 180  # 3分钟 = 180秒

def get_short_position_stats():
    """
    获取空单持仓的盈利分级统计
    """
    try:
        # 获取当前持仓
        url = f"{API_BASE_URL}/api/anchor-system/current-positions"
        params = {'trade_mode': 'real'}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"❌ API请求失败: {response.status_code}")
            return None
        
        data = response.json()
        if not data.get('success'):
            print(f"❌ API返回失败: {data.get('message', 'Unknown error')}")
            return None
        
        positions = data.get('positions', [])
        
        # 筛选空单持仓
        short_positions = [p for p in positions if p.get('pos_side') == 'short']
        
        # 统计各级别数量
        stats = {
            'profit_gte_70': 0,  # ≥70%
            'profit_gte_60': 0,  # ≥60%
            'profit_gte_50': 0,  # ≥50%
            'profit_lte_20': 0,  # ≤20%
            'profit_lte_10': 0,  # ≤10%
            'loss': 0,           # <0%
            'total_short': len(short_positions)
        }
        
        for pos in short_positions:
            profit_rate = pos.get('profit_rate', 0)
            
            if profit_rate < 0:
                stats['loss'] += 1
            
            if profit_rate <= 10:
                stats['profit_lte_10'] += 1
            
            if profit_rate <= 20:
                stats['profit_lte_20'] += 1
            
            if profit_rate >= 50:
                stats['profit_gte_50'] += 1
            
            if profit_rate >= 60:
                stats['profit_gte_60'] += 1
            
            if profit_rate >= 70:
                stats['profit_gte_70'] += 1
        
        return stats
    
    except Exception as e:
        print(f"❌ 获取空单统计失败: {e}")
        return None

def save_stats_to_db(stats):
    """
    保存统计数据到数据库
    """
    if not stats:
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        snapshot_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存各项统计
        stats_items = [
            ('short_profit_gte_70', stats['profit_gte_70'], '空单盈利≥70%'),
            ('short_profit_gte_60', stats['profit_gte_60'], '空单盈利≥60%'),
            ('short_profit_gte_50', stats['profit_gte_50'], '空单盈利≥50%'),
            ('short_profit_lte_20', stats['profit_lte_20'], '空单盈利≤20%'),
            ('short_profit_lte_10', stats['profit_lte_10'], '空单盈利≤10%'),
            ('short_loss', stats['loss'], '空单亏损'),
            ('total_short_positions', stats['total_short'], '空单总数'),
        ]
        
        for stat_type, stat_value, stat_label in stats_items:
            cursor.execute('''
                INSERT INTO statistics_snapshots 
                (snapshot_time, stat_type, stat_value, stat_label)
                VALUES (?, ?, ?, ?)
            ''', (snapshot_time, stat_type, stat_value, stat_label))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 空单统计已保存: {stats}")
        return True
    
    except Exception as e:
        print(f"❌ 保存统计数据失败: {e}")
        return False

def main():
    """
    主函数：每3分钟收集一次空单盈利分级统计
    """
    print("=" * 60)
    print("🚀 空单盈利分级统计收集器已启动")
    print(f"📊 数据库路径: {DB_PATH}")
    print(f"🌐 API地址: {API_BASE_URL}")
    print(f"⏰ 收集间隔: {COLLECTION_INTERVAL}秒（3分钟）")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    while True:
        try:
            print(f"\n⏰ 开始收集... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            
            # 获取统计数据
            stats = get_short_position_stats()
            
            if stats:
                # 保存到数据库
                save_stats_to_db(stats)
                print(f"📊 统计概览:")
                print(f"   空单总数: {stats['total_short']}")
                print(f"   盈利≥70%: {stats['profit_gte_70']}")
                print(f"   盈利≥60%: {stats['profit_gte_60']}")
                print(f"   盈利≥50%: {stats['profit_gte_50']}")
                print(f"   盈利≤20%: {stats['profit_lte_20']}")
                print(f"   盈利≤10%: {stats['profit_lte_10']}")
                print(f"   亏损(<0%): {stats['loss']}")
            else:
                print("⚠️ 本次收集失败，等待下次重试...")
            
            print(f"⏳ 等待{COLLECTION_INTERVAL}秒后继续...")
            time.sleep(COLLECTION_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n👋 收集器已停止")
            break
        except Exception as e:
            print(f"❌ 收集过程异常: {e}")
            print(f"⏳ 等待{COLLECTION_INTERVAL}秒后重试...")
            time.sleep(COLLECTION_INTERVAL)

if __name__ == '__main__':
    main()
