#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复crypto_data.db缺失crypto_snapshots表的问题
"""

import sqlite3
import os

DB_PATH = '/home/user/webapp/databases/crypto_data.db'

def create_crypto_snapshots_table():
    """创建crypto_snapshots表"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建crypto_snapshots表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS crypto_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            snapshot_time TEXT NOT NULL,
            inst_id TEXT NOT NULL,
            last_price REAL,
            high_24h REAL,
            low_24h REAL,
            vol_24h REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_date ON crypto_snapshots(snapshot_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_time ON crypto_snapshots(snapshot_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inst_id ON crypto_snapshots(inst_id)')
        
        conn.commit()
        
        # 验证表已创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crypto_snapshots'")
        result = cursor.fetchone()
        
        if result:
            print("✅ crypto_snapshots 表已成功创建")
            
            # 显示表结构
            cursor.execute("PRAGMA table_info(crypto_snapshots)")
            columns = cursor.fetchall()
            print("\n表结构:")
            for col in columns:
                print(f"  {col[1]} {col[2]}")
            
            conn.close()
            return True
        else:
            print("❌ 表创建失败")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 修复 crypto_data.db 缺失表问题")
    print("=" * 60)
    
    success = create_crypto_snapshots_table()
    
    if success:
        print("\n✅ 修复完成！")
    else:
        print("\n❌ 修复失败！")
