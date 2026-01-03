#!/bin/bash

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
AIDRIVE="/mnt/aidrive"

echo "=========================================="
echo "分批备份到AI Drive"
echo "=========================================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 备份核心数据库（单独打包，避免AI Drive慢速）
echo "1️⃣  备份核心数据库..."
tar -czf /tmp/databases_${BACKUP_DATE}.tar.gz \
    databases/crypto_data.db \
    databases/support_resistance.db \
    databases/sar_slope_data.db \
    databases/anchor_system.db \
    databases/trading_decision.db \
    databases/fund_monitor.db \
    databases/v1v2_data.db \
    2>/dev/null

echo "   数据库打包完成: $(du -sh /tmp/databases_${BACKUP_DATE}.tar.gz | awk '{print $1}')"
echo "   上传到AI Drive..."
cp /tmp/databases_${BACKUP_DATE}.tar.gz "${AIDRIVE}/" && echo "   ✅ 数据库已上传"

# 2. 备份Git仓库
echo ""
echo "2️⃣  备份Git仓库..."
tar -czf /tmp/git_${BACKUP_DATE}.tar.gz .git 2>/dev/null
echo "   Git打包完成: $(du -sh /tmp/git_${BACKUP_DATE}.tar.gz | awk '{print $1}')"
echo "   上传到AI Drive..."
cp /tmp/git_${BACKUP_DATE}.tar.gz "${AIDRIVE}/" && echo "   ✅ Git已上传"

# 3. 备份日志（可选，按需）
echo ""
echo "3️⃣  备份日志文件..."
tar -czf /tmp/logs_${BACKUP_DATE}.tar.gz logs/ 2>/dev/null
echo "   日志打包完成: $(du -sh /tmp/logs_${BACKUP_DATE}.tar.gz | awk '{print $1}')"
echo "   上传到AI Drive..."
cp /tmp/logs_${BACKUP_DATE}.tar.gz "${AIDRIVE}/" && echo "   ✅ 日志已上传"

# 4. 备份代码和配置
echo ""
echo "4️⃣  备份代码和配置..."
tar -czf /tmp/code_config_${BACKUP_DATE}.tar.gz \
    templates/ \
    *.py \
    *.json \
    *.txt \
    *.sh \
    2>/dev/null

echo "   代码打包完成: $(du -sh /tmp/code_config_${BACKUP_DATE}.tar.gz | awk '{print $1}')"
echo "   上传到AI Drive..."
cp /tmp/code_config_${BACKUP_DATE}.tar.gz "${AIDRIVE}/" && echo "   ✅ 代码已上传"

# 5. 创建备份清单
echo ""
echo "5️⃣  生成备份清单..."
cat > /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt << EOFMANIFEST
========================================
完整系统备份清单
========================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份位置: ${AIDRIVE}

========================================
备份文件
========================================
1. databases_${BACKUP_DATE}.tar.gz
   - crypto_data.db
   - support_resistance.db  
   - sar_slope_data.db
   - anchor_system.db
   - trading_decision.db
   - fund_monitor.db
   - v1v2_data.db

2. git_${BACKUP_DATE}.tar.gz
   - 完整Git仓库

3. logs_${BACKUP_DATE}.tar.gz
   - 所有日志文件

4. code_config_${BACKUP_DATE}.tar.gz
   - HTML模板
   - Python脚本
   - 配置文件

========================================
恢复步骤
========================================
1. 创建恢复目录
   mkdir -p /home/user/webapp_restore

2. 解压所有文件
   cd /home/user/webapp_restore
   tar -xzf ${AIDRIVE}/databases_${BACKUP_DATE}.tar.gz
   tar -xzf ${AIDRIVE}/git_${BACKUP_DATE}.tar.gz
   tar -xzf ${AIDRIVE}/logs_${BACKUP_DATE}.tar.gz
   tar -xzf ${AIDRIVE}/code_config_${BACKUP_DATE}.tar.gz

3. 安装依赖
   pip3 install -r requirements.txt

4. 启动服务
   pm2 start ecosystem.config.js
   
========================================
文件大小
========================================
EOFMANIFEST

ls -lh "${AIDRIVE}/*${BACKUP_DATE}*" 2>/dev/null >> /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt

cp /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt "${AIDRIVE}/" && echo "   ✅ 清单已上传"

# 6. 显示AI Drive内容
echo ""
echo "=========================================="
echo "✅ 备份完成！"
echo "=========================================="
echo ""
echo "📦 AI Drive备份文件:"
ls -lh "${AIDRIVE}"/*${BACKUP_DATE}* 2>/dev/null | awk '{print "   " $9 " - " $5}'

echo ""
echo "📋 备份清单: ${AIDRIVE}/BACKUP_MANIFEST_${BACKUP_DATE}.txt"
echo ""
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 清理临时文件
rm -f /tmp/*${BACKUP_DATE}*
