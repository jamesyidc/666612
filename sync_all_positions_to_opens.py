#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将所有当前持仓同步到position_opens表
用于修复历史极值记录缺失的问题
"""

import sqlite3
import requests
from datetime import datetime
import pytz
import traceback

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DB_PATH = '/home/user/webapp/trading_decision.db'
FLASK_API = 'http://localhost:5000/api/anchor-system/current-positions?trade_mode=real'

def get_beijing_time():
    """获取北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

def get_current_positions():
    """从Flask API获取当前实盘持仓"""
    try:
        response = requests.get(FLASK_API, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('positions', [])
        
        print(f"⚠️  Flask API返回错误: {response.text[:200]}")
        return []
        
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return []

def sync_position_to_opens(conn, cursor, pos):
    """同步单个持仓到position_opens表"""
    inst_id = pos.get('inst_id')
    pos_side = pos.get('pos_side')
    pos_size = float(pos.get('pos_size', 0))
    avg_price = float(pos.get('avg_price', 0))
    mark_price = float(pos.get('mark_price', 0))
    lever = int(pos.get('lever', 10))
    margin = float(pos.get('margin', 0))
    upl = float(pos.get('upl', 0))
    profit_rate = float(pos.get('profit_rate', 0))
    
    # 跳过空仓
    if pos_size == 0:
        return False, "空仓"
    
    # 检查是否已存在
    cursor.execute("""
        SELECT id, created_at, open_size, open_price FROM position_opens 
        WHERE inst_id = ? AND pos_side = ? AND open_size != 0
    """, (inst_id, pos_side))
    
    existing = cursor.fetchone()
    
    if existing:
        # 如果已存在且仓位大小相同，跳过
        existing_size = float(existing[2])
        if abs(existing_size - pos_size) < 0.001:
            print(f"  ⏭️  {inst_id} {pos_side} 已存在且仓位相同，跳过")
            return False, "已存在"
        
        # 如果仓位大小不同，更新记录
        cursor.execute("""
            UPDATE position_opens
            SET open_size = ?,
                mark_price = ?,
                profit_rate = ?,
                upl = ?,
                lever = ?,
                margin = ?,
                updated_time = ?
            WHERE inst_id = ? AND pos_side = ?
        """, (pos_size, mark_price, profit_rate, upl, lever, margin, 
              get_beijing_time(), inst_id, pos_side))
        
        print(f"  ✅ {inst_id} {pos_side} 更新: {existing_size} → {pos_size} 张")
        return True, "更新"
    
    # 插入新记录
    timestamp = get_beijing_time()
    
    try:
        cursor.execute("""
            INSERT INTO position_opens (
                inst_id, pos_side, open_price, open_size, open_percent,
                granularity, total_positions, is_anchor, 
                timestamp, created_at, mark_price, profit_rate,
                upl, lever, margin, updated_time, trade_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inst_id, 
            pos_side, 
            avg_price,      # 使用当前均价作为开仓价
            pos_size,
            100.0,          # open_percent
            0.0,            # granularity
            0,              # total_positions
            1,              # is_anchor = 1 (标记为锚点单)
            timestamp,
            timestamp,
            mark_price,
            profit_rate,
            upl,
            lever,
            margin,
            timestamp,
            'real'          # trade_mode
        ))
        
        inserted_id = cursor.lastrowid
        print(f"  ✅ {inst_id} {pos_side} 新增: {pos_size} 张 @ {avg_price:.4f}")
        return True, "新增"
        
    except Exception as e:
        print(f"  ❌ {inst_id} {pos_side} 插入失败: {e}")
        traceback.print_exc()
        return False, f"错误: {e}"

def sync_all_positions():
    """同步所有当前持仓到position_opens表"""
    print("="*70)
    print("🔄 开始同步所有持仓到 position_opens 表")
    print("="*70)
    print(f"数据库路径: {DB_PATH}")
    print(f"Flask API: {FLASK_API}")
    print(f"当前时间: {get_beijing_time()}")
    print("")
    
    # 获取当前持仓
    positions = get_current_positions()
    
    if not positions:
        print("⚠️  没有获取到持仓数据")
        return
    
    print(f"📊 发现 {len(positions)} 个持仓\n")
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for pos in positions:
        inst_id = pos.get('inst_id')
        pos_side = pos.get('pos_side')
        pos_size = pos.get('pos_size', 0)
        
        print(f"处理: {inst_id} {pos_side} ({pos_size} 张)")
        
        success, reason = sync_position_to_opens(conn, cursor, pos)
        
        if success:
            if reason == "新增":
                success_count += 1
            elif reason == "更新":
                success_count += 1
        elif reason == "已存在":
            skip_count += 1
        else:
            error_count += 1
    
    # 提交更改
    conn.commit()
    
    # 统计结果
    cursor.execute("SELECT COUNT(*) FROM position_opens WHERE open_size != 0")
    total_count = cursor.fetchone()[0]
    
    print("\n" + "="*70)
    print("📋 同步结果统计：")
    print(f"  ✅ 成功处理: {success_count} 个")
    print(f"  ⏭️  已存在跳过: {skip_count} 个")
    print(f"  ❌ 失败: {error_count} 个")
    print(f"  📊 position_opens表总记录数: {total_count}")
    print("="*70)
    
    # 显示所有做空仓位
    print("\n📉 所有做空仓位：")
    cursor.execute("""
        SELECT inst_id, pos_side, open_size, open_price, created_at
        FROM position_opens 
        WHERE pos_side = 'short' AND open_size != 0
        ORDER BY created_at DESC
    """)
    
    shorts = cursor.fetchall()
    if shorts:
        for row in shorts:
            print(f"  {row[0]} {row[1]} {row[2]} 张 @ {row[3]:.4f} ({row[4]})")
    else:
        print("  (无)")
    
    conn.close()
    print("\n✅ 同步完成！")

if __name__ == '__main__':
    try:
        sync_all_positions()
        print("\n💡 提示：")
        print("  - 极值追踪服务将在下次扫描时发现这些新记录")
        print("  - 扫描间隔为60秒")
        print("  - 可以查看日志：pm2 logs profit-extremes-tracker --lines 50")
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        traceback.print_exc()
