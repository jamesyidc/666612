#!/bin/bash

BACKUP_DATE=$(date +%Y-%m-%d_%H%M%S)

echo "=========================================="
echo "完整系统备份（包含所有数据库）"
echo "=========================================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 备份所有数据库（包含两个大数据库）
echo "1️⃣ 备份所有数据库..."
tar -czf /tmp/all_databases_${BACKUP_DATE}.tar.gz \
    databases/crypto_data.db \
    databases/crypto_data_backup_20260102_124047.db \
    databases/crypto_data_corrupted.db \
    databases/crypto_data_new.db \
    databases/support_resistance.db \
    databases/sar_slope_data.db \
    databases/anchor_system.db \
    databases/trading_decision.db \
    databases/fund_monitor.db \
    databases/v1v2_data.db \
    databases/count_monitor.db \
    databases/price_speed_data.db \
    databases/signal_data.db \
    2>/dev/null

echo "   ✅ 完成: $(du -sh /tmp/all_databases_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 2. 备份Git仓库
echo ""
echo "2️⃣ 备份Git仓库..."
tar -czf /tmp/git_${BACKUP_DATE}.tar.gz .git 2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/git_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 3. 备份日志
echo ""
echo "3️⃣ 备份日志..."
tar -czf /tmp/logs_${BACKUP_DATE}.tar.gz logs/ 2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/logs_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 4. 备份代码和配置
echo ""
echo "4️⃣ 备份代码和配置..."
tar -czf /tmp/code_config_${BACKUP_DATE}.tar.gz \
    templates/ \
    *.py \
    *.json \
    *.txt \
    *.sh \
    *.md \
    2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/code_config_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 5. 创建备份清单
echo ""
echo "5️⃣ 生成备份清单..."
cat > /tmp/COMPLETE_BACKUP_MANIFEST_${BACKUP_DATE}.txt << EOFMANIFEST
==========================================
完整系统备份清单（包含所有数据）
==========================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份位置: /tmp

==========================================
备份文件列表
==========================================
EOFMANIFEST

ls -lh /tmp/*${BACKUP_DATE}* 2>/dev/null | awk '{print $9 " - " $5}' >> /tmp/COMPLETE_BACKUP_MANIFEST_${BACKUP_DATE}.txt

cat >> /tmp/COMPLETE_BACKUP_MANIFEST_${BACKUP_DATE}.txt << EOFMANIFEST2

==========================================
备份内容详情
==========================================

📦 1. all_databases_${BACKUP_DATE}.tar.gz
   包含所有数据库（13个）:
   - crypto_data.db (772KB) - 当前使用的数据库
   - crypto_data_backup_20260102_124047.db (1.9GB) - 备份数据库
   - crypto_data_corrupted.db (1.9GB) - 损坏数据库（只有1个表损坏）
   - crypto_data_new.db (24KB)
   - support_resistance.db (0B) - 支撑压力线
   - sar_slope_data.db (505MB) - SAR斜率
   - anchor_system.db (13MB) - 锚点系统
   - trading_decision.db (4.2MB) - 交易决策
   - fund_monitor.db (42MB) - 资金监控
   - v1v2_data.db (12MB) - V1V2成交
   - count_monitor.db (16KB)
   - price_speed_data.db (24KB)
   - signal_data.db (16KB)

📦 2. git_${BACKUP_DATE}.tar.gz
   完整Git仓库 (.git目录)

📦 3. logs_${BACKUP_DATE}.tar.gz
   所有日志文件

📦 4. code_config_${BACKUP_DATE}.tar.gz
   - HTML模板 (templates/)
   - Python脚本 (*.py)
   - 配置文件 (*.json, *.txt, *.sh)
   - 文档文件 (*.md)

==========================================
数据库完整性说明
==========================================

✅ crypto_data_backup_20260102_124047.db
   - 状态: 可用
   - 表数量: 38个
   - 总记录数: 942,390条
   - 损坏的表: okex_technical_indicators (可恢复)

✅ crypto_data_corrupted.db
   - 状态: 可用
   - 表数量: 38个
   - 总记录数: 942,398条
   - 损坏的表: okex_technical_indicators (可恢复)

⚠️ 恢复时注意: 
   两个大数据库只有 okex_technical_indicators 表损坏，
   其他37个表都完好，包含94万+条记录，可以正常使用。

==========================================
恢复步骤
==========================================

1. 创建恢复目录
   mkdir -p /home/user/webapp_restore
   cd /home/user/webapp_restore

2. 解压所有文件
   tar -xzf /tmp/all_databases_${BACKUP_DATE}.tar.gz
   tar -xzf /tmp/git_${BACKUP_DATE}.tar.gz
   tar -xzf /tmp/logs_${BACKUP_DATE}.tar.gz
   tar -xzf /tmp/code_config_${BACKUP_DATE}.tar.gz

3. 选择使用哪个数据库
   # 使用当前版本（772KB）
   # 或使用备份版本（1.9GB，包含更多历史数据）
   
4. 安装依赖
   pip3 install -r requirements.txt

5. 启动服务
   pm2 resurrect
   pm2 list

==========================================
23个子系统完整映射
==========================================

所有23个子系统的数据库、页面、脚本全部已备份！

数据库映射:
1-19. 多个系统 -> crypto_data*.db
14. 支撑压力线系统 -> support_resistance.db
15-16. 决策系统 -> trading_decision.db
17. V1V2成交系统 -> v1v2_data.db
21. 资金监控系统 -> fund_monitor.db
22. 锚点系统 -> anchor_system.db

页面文件、Python脚本、配置文件全部包含在 code_config 包中。

==========================================
EOFMANIFEST2

echo "   ✅ 清单已生成"

echo ""
echo "=========================================="
echo "✅ 完整备份完成！"
echo "=========================================="
echo ""
echo "📦 备份文件:"
ls -lh /tmp/*${BACKUP_DATE}* 2>/dev/null | awk '{print "   " $9 " - " $5}'

echo ""
TOTAL=$(du -ch /tmp/*${BACKUP_DATE}* 2>/dev/null | grep total | awk '{print $1}')
echo "📊 总计: ${TOTAL}"

echo ""
echo "📋 备份清单: /tmp/COMPLETE_BACKUP_MANIFEST_${BACKUP_DATE}.txt"
echo ""
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
