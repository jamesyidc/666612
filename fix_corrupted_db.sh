#!/bin/bash

CORRUPTED_DB="databases/crypto_data_corrupted.db"
FIXED_DB="databases/crypto_data_fixed.db"
TEMP_SQL="/tmp/dump_temp.sql"

echo "=========================================="
echo "使用 sqlite3 命令修复数据库"
echo "=========================================="

# 1. 使用 .dump 导出数据
echo ""
echo "1️⃣ 导出数据..."
sqlite3 "$CORRUPTED_DB" ".dump" > "$TEMP_SQL" 2>&1

if [ $? -eq 0 ]; then
    echo "   ✓ 导出成功"
    DUMP_SIZE=$(du -sh "$TEMP_SQL" | awk '{print $1}')
    echo "   SQL文件大小: $DUMP_SIZE"
else
    echo "   ✗ 导出失败"
    exit 1
fi

# 2. 导入到新数据库
echo ""
echo "2️⃣ 导入到新数据库..."
rm -f "$FIXED_DB"
sqlite3 "$FIXED_DB" < "$TEMP_SQL"

if [ $? -eq 0 ]; then
    echo "   ✓ 导入成功"
else
    echo "   ✗ 导入失败"
    exit 1
fi

# 3. 验证新数据库
echo ""
echo "3️⃣ 验证新数据库..."
TABLE_COUNT=$(sqlite3 "$FIXED_DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
echo "   表数量: $TABLE_COUNT"

# 4. VACUUM优化
echo ""
echo "4️⃣ 优化数据库..."
sqlite3 "$FIXED_DB" "VACUUM;"
echo "   ✓ 优化完成"

# 5. 显示文件大小对比
echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "文件大小对比:"
ls -lh "$CORRUPTED_DB" "$FIXED_DB" | awk '{print "   " $9 ": " $5}'

# 清理临时文件
rm -f "$TEMP_SQL"

echo ""
echo "请手动执行以下命令替换原文件:"
echo "   mv $CORRUPTED_DB ${CORRUPTED_DB}.bak"
echo "   mv $FIXED_DB $CORRUPTED_DB"
echo ""

