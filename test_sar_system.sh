#!/bin/bash
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          SAR斜率系统 - 完整测试报告                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "=== 1. 数据目录结构测试 ==="
ls -la data/sar_slope/ | head -15
echo ""

echo "=== 2. 数据文件示例 ==="
echo "BTC 今日数据:"
wc -l data/sar_slope/BTC/$(date +%Y-%m-%d).jsonl
echo ""

echo "=== 3. API端点测试 ===" 
echo "测试 /api/sar-slope/latest..."
curl -s http://localhost:5000/api/sar-slope/latest | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"✅ 成功: {d['success']}, 数据数量: {len(d['data'])}, 多头: {d['stats']['bullish_count']}, 空头: {d['stats']['bearish_count']}\")"
echo ""

echo "测试 /api/sar-slope/history/BTC..."
curl -s "http://localhost:5000/api/sar-slope/history/BTC?limit=10" | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"✅ 成功: {d['success']}, BTC历史数据: {d['count']} 条\")"
echo ""

echo "测试 /api/sar-slope/collector-status..."
curl -s http://localhost:5000/api/sar-slope/collector-status | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"✅ 状态: {d['status']}, 存储类型: {d['storage_type']}, 数据目录: {d['data_dir']}\")"
echo ""

echo "=== 4. 页面访问测试 ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/sar-slope)
echo "SAR斜率页面状态: $STATUS"
if [ "$STATUS" = "200" ]; then
    echo "✅ 页面访问正常"
else
    echo "❌ 页面访问失败"
fi
echo ""

echo "=== 5. 数据完整性验证 ==="
SYMBOLS=("BTC" "ETH" "SOL" "BNB" "XRP")
for symbol in "${SYMBOLS[@]}"; do
    TODAY=$(date +%Y-%m-%d)
    FILE="data/sar_slope/$symbol/$TODAY.jsonl"
    if [ -f "$FILE" ]; then
        COUNT=$(wc -l < "$FILE")
        echo "✅ $symbol: $COUNT 条记录"
    else
        echo "❌ $symbol: 数据文件不存在"
    fi
done
echo ""

echo "=== 6. 存储空间使用 ==="
du -sh data/sar_slope/
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "✅ 测试完成！"
echo "═══════════════════════════════════════════════════════════"
