#!/bin/bash
# 系统恢复脚本
# 使用方法: ./restore.sh

set -e

echo "======================================"
echo "加密货币交易系统 - 完整恢复"
echo "======================================"
echo ""

# 检查分片文件
echo "🔍 检查分片文件..."
PARTS=(webapp_full_*.tar.gz.part*)
if [ ${#PARTS[@]} -eq 0 ]; then
    echo "❌ 错误：未找到分片文件！"
    echo "请确保所有 .part* 文件都在当前目录"
    exit 1
fi
echo "✅ 找到 ${#PARTS[@]} 个分片文件"
echo ""

# 验证MD5
if [ -f "checksums.md5" ]; then
    echo "🔐 验证文件完整性..."
    if md5sum -c checksums.md5 2>/dev/null; then
        echo "✅ 所有文件校验通过"
    else
        echo "⚠️  警告：部分文件校验失败，但继续恢复..."
    fi
    echo ""
fi

# 合并分片
echo "🔗 合并分片文件..."
ARCHIVE_NAME=$(ls webapp_full_*.tar.gz.part01 | sed 's/.part01$//')
cat ${ARCHIVE_NAME}.part* > ${ARCHIVE_NAME}
echo "✅ 合并完成: ${ARCHIVE_NAME}"
echo ""

# 解压
echo "📦 解压文件..."
tar xzf ${ARCHIVE_NAME} -C /tmp/
echo "✅ 解压完成"
echo ""

# 恢复到目标位置
echo "📋 恢复系统文件..."
RESTORE_SOURCE="/tmp/webapp"
RESTORE_TARGET="/home/user/webapp"

if [ -d "${RESTORE_TARGET}" ]; then
    echo "⚠️  目标目录已存在，创建备份..."
    BACKUP_TS=$(date +%Y%m%d_%H%M%S)
    mv "${RESTORE_TARGET}" "${RESTORE_TARGET}.backup_${BACKUP_TS}"
    echo "  原目录备份为: ${RESTORE_TARGET}.backup_${BACKUP_TS}"
fi

echo "复制文件到目标位置..."
cp -r "${RESTORE_SOURCE}" "${RESTORE_TARGET}"
echo "✅ 文件恢复完成"
echo ""

# 设置权限
echo "🔧 设置文件权限..."
cd "${RESTORE_TARGET}"
chmod +x *.py 2>/dev/null || true
chmod +x source_code/*.py 2>/dev/null || true
echo "✅ 权限设置完成"
echo ""

# 启动服务
echo "🚀 启动系统服务..."
cd "${RESTORE_TARGET}"

# 安装依赖（如需要）
if [ -f "requirements.txt" ]; then
    echo "安装Python依赖..."
    pip3 install -r requirements.txt > /dev/null 2>&1
fi

# 启动PM2服务
echo "启动PM2服务..."
pm2 delete all 2>/dev/null || true
pm2 start app_new.py --name flask-app --interpreter python3
pm2 start support_resistance_collector.py --name support-resistance-collector --interpreter python3
pm2 start sar_slope_collector.py --name sar-slope-collector --interpreter python3
pm2 save

echo "✅ 服务启动完成"
echo ""

# 验证
echo "✅ 系统恢复完成！"
echo ""
echo "验证步骤："
echo "1. 检查服务状态: pm2 list"
echo "2. 检查API: curl http://localhost:5000/api/latest"
echo "3. 访问页面: http://localhost:5000/"
echo ""
echo "数据库位置: ${RESTORE_TARGET}/databases/"
echo "日志位置: ${RESTORE_TARGET}/logs/"
echo ""

