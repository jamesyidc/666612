#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复crypto_snapshots表的inst_id字段约束
将inst_id改为可空，因为从Google Drive导入的数据不包含inst_id
"""

import sqlite3

DB_PATH = 'databases/crypto_data.db'

def fix_inst_id_constraint():
    """修复inst_id的NOT NULL约束"""
    try:
        print(f"📊 连接数据库: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 由于SQLite不支持直接修改列约束，需要重建表
        print("📝 开始重建表...")
        
        # 1. 创建新表（inst_id改为可空）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crypto_snapshots_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                snapshot_time TEXT NOT NULL,
                inst_id TEXT,
                last_price REAL,
                high_24h REAL,
                low_24h REAL,
                vol_24h REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rush_up INTEGER DEFAULT 0,
                rush_down INTEGER DEFAULT 0,
                diff INTEGER DEFAULT 0,
                count INTEGER DEFAULT 0,
                status TEXT DEFAULT '',
                count_score_display TEXT DEFAULT '',
                count_score_type TEXT DEFAULT ''
            )
        """)
        print("✅ 创建新表成功")
        
        # 2. 复制旧数据到新表
        cursor.execute("""
            INSERT INTO crypto_snapshots_new 
            SELECT * FROM crypto_snapshots
        """)
        print("✅ 数据迁移成功")
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE crypto_snapshots")
        print("✅ 删除旧表成功")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE crypto_snapshots_new RENAME TO crypto_snapshots")
        print("✅ 重命名新表成功")
        
        # 5. 重建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_date ON crypto_snapshots(snapshot_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_time ON crypto_snapshots(snapshot_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inst_id ON crypto_snapshots(inst_id)")
        print("✅ 重建索引成功")
        
        conn.commit()
        
        # 确认表结构
        cursor.execute("PRAGMA table_info(crypto_snapshots)")
        columns = cursor.fetchall()
        print(f"\n✅ 修复后的表结构:")
        for col in columns:
            print(f"   - {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
        conn.close()
        print(f"\n✅ inst_id约束修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fix_inst_id_constraint()
