#!/usr/bin/env python3
import sqlite3
import os

db_path = 'databases/crypto_data.db'
os.makedirs('databases', exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建crypto_snapshots表
cursor.execute('''
CREATE TABLE IF NOT EXISTS crypto_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_id TEXT,
    file_name TEXT,
    folder_id TEXT,
    data_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id)
)
''')

# 创建索引
cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_time ON crypto_snapshots(snapshot_time)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_id ON crypto_snapshots(file_id)')

conn.commit()
conn.close()

print(f"✅ 数据库表已重建: {db_path}")
print("   - crypto_snapshots (快照表)")
print("   - 索引已创建")
