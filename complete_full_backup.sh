#!/bin/bash

# 完整系统备份脚本 v2 - 包含所有数据
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/full_system_backup_${BACKUP_DATE}"
BACKUP_FILE="/tmp/full_system_backup_${BACKUP_DATE}.tar.gz"

echo "=========================================="
echo "完整系统备份 v2"
echo "=========================================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "备份目录: ${BACKUP_DIR}"
echo ""

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 1. 备份所有数据库（包括备份文件）
echo "1️⃣  备份数据库..."
mkdir -p "${BACKUP_DIR}/databases"
cp -v databases/*.db "${BACKUP_DIR}/databases/" 2>/dev/null || true
du -sh "${BACKUP_DIR}/databases"

# 2. 备份完整Git仓库
echo ""
echo "2️⃣  备份Git仓库..."
mkdir -p "${BACKUP_DIR}/git"
cp -r .git "${BACKUP_DIR}/git/" 2>/dev/null || true
du -sh "${BACKUP_DIR}/git"

# 3. 备份所有日志
echo ""
echo "3️⃣  备份日志文件..."
mkdir -p "${BACKUP_DIR}/logs"
cp -r logs/* "${BACKUP_DIR}/logs/" 2>/dev/null || true
du -sh "${BACKUP_DIR}/logs"

# 4. 备份所有模板
echo ""
echo "4️⃣  备份HTML模板..."
mkdir -p "${BACKUP_DIR}/templates"
cp -r templates/* "${BACKUP_DIR}/templates/" 2>/dev/null || true

# 5. 备份所有Python脚本
echo ""
echo "5️⃣  备份Python脚本..."
mkdir -p "${BACKUP_DIR}/scripts"
find . -maxdepth 1 -name "*.py" -exec cp {} "${BACKUP_DIR}/scripts/" \;

# 6. 备份配置文件
echo ""
echo "6️⃣  备份配置文件..."
mkdir -p "${BACKUP_DIR}/configs"
cp *.json "${BACKUP_DIR}/configs/" 2>/dev/null || true
cp *.txt "${BACKUP_DIR}/configs/" 2>/dev/null || true
cp *.sh "${BACKUP_DIR}/configs/" 2>/dev/null || true

# 7. 备份PM2配置
echo ""
echo "7️⃣  备份PM2配置..."
mkdir -p "${BACKUP_DIR}/pm2"
cp -r ~/.pm2 "${BACKUP_DIR}/pm2/" 2>/dev/null || true

# 8. 备份静态文件
echo ""
echo "8️⃣  备份静态文件..."
if [ -d "static" ]; then
    mkdir -p "${BACKUP_DIR}/static"
    cp -r static/* "${BACKUP_DIR}/static/" 2>/dev/null || true
fi

# 9. 创建备份清单
echo ""
echo "9️⃣  生成备份清单..."
cat > "${BACKUP_DIR}/BACKUP_INFO.txt" << EOFINFO
========================================
完整系统备份信息
========================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份版本: v2 (完整备份)
主机名: $(hostname)
工作目录: $(pwd)

========================================
备份内容
========================================
EOFINFO

# 统计各部分大小
echo "" >> "${BACKUP_DIR}/BACKUP_INFO.txt"
echo "📊 各部分大小:" >> "${BACKUP_DIR}/BACKUP_INFO.txt"
du -sh "${BACKUP_DIR}/databases" 2>/dev/null | awk '{print "   数据库: " $1}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
du -sh "${BACKUP_DIR}/git" 2>/dev/null | awk '{print "   Git仓库: " $1}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
du -sh "${BACKUP_DIR}/logs" 2>/dev/null | awk '{print "   日志文件: " $1}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
du -sh "${BACKUP_DIR}/templates" 2>/dev/null | awk '{print "   模板文件: " $1}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
du -sh "${BACKUP_DIR}/scripts" 2>/dev/null | awk '{print "   Python脚本: " $1}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
du -sh "${BACKUP_DIR}/configs" 2>/dev/null | awk '{print "   配置文件: " $1}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"

# 统计文件数量
echo "" >> "${BACKUP_DIR}/BACKUP_INFO.txt"
echo "📁 文件数量统计:" >> "${BACKUP_DIR}/BACKUP_INFO.txt"
find "${BACKUP_DIR}/databases" -name "*.db" 2>/dev/null | wc -l | awk '{print "   数据库: " $1 " 个"}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
find "${BACKUP_DIR}/templates" -name "*.html" 2>/dev/null | wc -l | awk '{print "   HTML模板: " $1 " 个"}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"
find "${BACKUP_DIR}/scripts" -name "*.py" 2>/dev/null | wc -l | awk '{print "   Python脚本: " $1 " 个"}' >> "${BACKUP_DIR}/BACKUP_INFO.txt"

# 10. 打包压缩
echo ""
echo "🔟  压缩备份..."
tar -czf "${BACKUP_FILE}" -C /tmp "$(basename ${BACKUP_DIR})"

echo ""
echo "=========================================="
echo "✅ 备份完成！"
echo "=========================================="
echo "备份文件: ${BACKUP_FILE}"
echo "文件大小: $(du -sh ${BACKUP_FILE} | awk '{print $1}')"
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "📋 备份清单: ${BACKUP_DIR}/BACKUP_INFO.txt"
echo ""
