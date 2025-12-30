#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点系统快照收集器
每1分钟保存一次持仓和统计数据快照
"""
import requests
import sqlite3
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
DB_PATH = "/home/user/webapp/anchor_snapshots.db"

def log(message):
    """打印日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def save_position_snapshot():
    """保存持仓快照"""
    try:
        # 获取当前持仓
        response = requests.get(
            f"{BASE_URL}/api/anchor-system/current-positions",
            params={"trade_mode": "real"},
            timeout=10
        )
        
        if response.status_code != 200:
            log(f"❌ 获取持仓失败: HTTP {response.status_code}")
            return False
        
        data = response.json()
        positions = data.get('positions', [])
        
        if not positions:
            log("⚠️  当前无持仓")
            return True
        
        # 保存到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        snapshot_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        saved_count = 0
        
        for pos in positions:
            cursor.execute('''
            INSERT INTO position_snapshots (
                snapshot_time, inst_id, pos_side, pos_size,
                avg_price, mark_price, leverage, margin,
                profit_rate, upl, maintenance_count,
                is_anchor, status, trade_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_time,
                pos.get('inst_id'),
                pos.get('pos_side'),
                float(pos.get('pos_size', 0)),
                float(pos.get('avg_price', 0)),
                float(pos.get('mark_price', 0)),
                int(pos.get('leverage', 10)),
                float(pos.get('margin', 0)),
                float(pos.get('profit_rate', 0)),
                float(pos.get('upl', 0)),
                int(pos.get('maintenance_count_today', 0)),
                int(pos.get('is_anchor', 0)),
                pos.get('status', ''),
                'real'
            ))
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        log(f"✅ 持仓快照已保存: {saved_count}条 @ {snapshot_time}")
        return True
        
    except Exception as e:
        log(f"❌ 保存持仓快照失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_statistics_snapshot():
    """保存统计快照"""
    try:
        # 获取今日统计
        response = requests.get(
            f"{BASE_URL}/api/anchor-system/today-statistics",
            params={"trade_mode": "real"},
            timeout=10
        )
        
        if response.status_code != 200:
            log(f"❌ 获取统计失败: HTTP {response.status_code}")
            return False
        
        data = response.json()
        stats = data.get('statistics', {})
        
        # 保存到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        snapshot_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存各项统计
        stat_items = [
            ('auto_maintain_long', stats.get('auto_maintain_long', 0), '自动维护多单-10%'),
            ('auto_maintain_short', stats.get('auto_maintain_short', 0), '自动维护空单-10%'),
            ('super_maintain_long', stats.get('super_maintain_long', 0), '超级维护多单'),
            ('super_maintain_short', stats.get('super_maintain_short', 0), '超级维护空单'),
            ('total_positions', stats.get('total_positions', 0), '持仓数量'),
            ('anchor_positions', stats.get('anchor_positions', 0), '锚点单数量'),
            ('warning_positions', stats.get('warning_positions', 0), '预警单数量'),
        ]
        
        for stat_type, stat_value, stat_label in stat_items:
            cursor.execute('''
            INSERT INTO statistics_snapshots (
                snapshot_time, stat_type, stat_value, stat_label, trade_mode
            ) VALUES (?, ?, ?, ?, ?)
            ''', (snapshot_time, stat_type, stat_value, stat_label, 'real'))
        
        conn.commit()
        conn.close()
        
        log(f"✅ 统计快照已保存: {len(stat_items)}项 @ {snapshot_time}")
        return True
        
    except Exception as e:
        log(f"❌ 保存统计快照失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def collect_snapshot():
    """收集一次快照"""
    log("📸 开始收集快照...")
    
    pos_ok = save_position_snapshot()
    stat_ok = save_statistics_snapshot()
    
    if pos_ok and stat_ok:
        log("✅ 快照收集完成")
    else:
        log("⚠️  快照收集部分失败")

def main():
    """主循环：每1分钟收集一次快照"""
    log("🚀 快照收集器启动")
    log(f"📁 数据库: {DB_PATH}")
    log(f"⏰ 收集频率: 每1分钟")
    log(f"🔗 API地址: {BASE_URL}")
    
    while True:
        try:
            collect_snapshot()
            log("⏳ 等待60秒...")
            time.sleep(60)  # 每1分钟
            
        except KeyboardInterrupt:
            log("👋 收到退出信号，停止收集器")
            break
        except Exception as e:
            log(f"❌ 循环异常: {e}")
            import traceback
            traceback.print_exc()
            log("⏳ 30秒后重试...")
            time.sleep(30)

if __name__ == '__main__':
    main()
