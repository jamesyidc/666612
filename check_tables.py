import sqlite3
import os

# 需要的表
required_tables = [
    'price_breakthrough_events',
    'crypto_coin_data',
    'crypto_snapshots',
    'okex_technical_indicators',
    'position_system'
]

# 检查所有数据库
databases = []
for f in os.listdir('databases'):
    if f.endswith('.db'):
        databases.append(f'databases/{f}')

print("=== 查找所需的表 ===\n")
for table in required_tables:
    found = False
    for db_path in databases:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: 在 {db_path} ({count:,} 条)")
                found = True
            conn.close()
        except:
            pass
    if not found:
        print(f"❌ {table}: 未找到")
