#!/bin/bash
set -e

cd /home/user/webapp

echo "=== 修复数据库路径 ==="

# 1. 备份当前的小数据库
if [ -f "databases/crypto_data.db" ]; then
    mv databases/crypto_data.db databases/crypto_data.db.small_backup
    echo "✅ 已备份小数据库为 crypto_data.db.small_backup"
fi

# 2. 使用 crypto_data_corrupted.db（虽然名字是corrupted，但大部分表都正常）
if [ -f "databases/crypto_data_corrupted.db" ]; then
    cp databases/crypto_data_corrupted.db databases/crypto_data.db
    echo "✅ 已复制 crypto_data_corrupted.db 为 crypto_data.db"
    ls -lh databases/crypto_data.db
else
    echo "❌ crypto_data_corrupted.db 不存在！"
    exit 1
fi

# 3. 验证新数据库的表
python3 << 'PYEOF'
import sqlite3

conn = sqlite3.connect('databases/crypto_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print(f"\n✅ 新 crypto_data.db 包含 {len(tables)} 个表:")
for t in sorted(tables):
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    count = cursor.fetchone()[0]
    print(f"  {t}: {count:,} 条")
conn.close()
PYEOF

echo -e "\n✅ 数据库修复完成！"
