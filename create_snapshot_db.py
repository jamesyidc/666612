#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建历史快照数据库
"""
import sqlite3
from datetime import datetime

def create_snapshot_database():
    """创建历史快照数据库和表"""
    conn = sqlite3.connect('anchor_snapshots.db')
    cursor = conn.cursor()
    
    # 创建持仓快照表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS position_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        inst_id TEXT NOT NULL,
        pos_side TEXT NOT NULL,
        pos_size REAL,
        avg_price REAL,
        mark_price REAL,
        leverage INTEGER,
        margin REAL,
        profit_rate REAL,
        upl REAL,
        maintenance_count INTEGER DEFAULT 0,
        is_anchor INTEGER DEFAULT 0,
        status TEXT,
        trade_mode TEXT DEFAULT 'real'
    )
    ''')
    
    # 创建统计快照表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS statistics_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        stat_type TEXT NOT NULL,
        stat_value INTEGER DEFAULT 0,
        stat_label TEXT,
        trade_mode TEXT DEFAULT 'real'
    )
    ''')
    
    # 创建索引
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_position_time 
    ON position_snapshots(snapshot_time)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_position_inst 
    ON position_snapshots(inst_id, pos_side, snapshot_time)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_stat_time 
    ON statistics_snapshots(snapshot_time)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_stat_type 
    ON statistics_snapshots(stat_type, snapshot_time)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ 历史快照数据库创建成功！")
    print(f"📁 数据库文件: anchor_snapshots.db")
    print(f"📊 表: position_snapshots (持仓快照)")
    print(f"📊 表: statistics_snapshots (统计快照)")

if __name__ == '__main__':
    create_snapshot_database()
