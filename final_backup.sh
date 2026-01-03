#!/bin/bash

BACKUP_DATE=$(date +%Y-%m-%d_%H%M%S)

echo "=========================================="
echo "最终完整备份"
echo "=========================================="
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 核心数据库
echo "1️⃣  打包核心数据库..."
tar -czf /tmp/databases_${BACKUP_DATE}.tar.gz \
    databases/crypto_data.db \
    databases/support_resistance.db \
    databases/sar_slope_data.db \
    databases/anchor_system.db \
    databases/trading_decision.db \
    databases/fund_monitor.db \
    databases/v1v2_data.db \
    2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/databases_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 2. Git仓库
echo ""
echo "2️⃣  打包Git仓库..."
tar -czf /tmp/git_${BACKUP_DATE}.tar.gz .git 2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/git_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 3. 日志
echo ""
echo "3️⃣  打包日志..."
tar -czf /tmp/logs_${BACKUP_DATE}.tar.gz logs/ 2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/logs_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 4. 代码和配置
echo ""
echo "4️⃣  打包代码和配置..."
tar -czf /tmp/code_config_${BACKUP_DATE}.tar.gz \
    templates/ \
    *.py \
    *.json \
    *.txt \
    *.sh \
    2>/dev/null
echo "   ✅ 完成: $(du -sh /tmp/code_config_${BACKUP_DATE}.tar.gz | awk '{print $1}')"

# 5. 创建备份清单
echo ""
echo "5️⃣  生成备份清单..."
cat > /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt << EOFMANIFEST
==========================================
完整系统备份清单
==========================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份位置: /tmp

==========================================
备份文件列表
==========================================
EOFMANIFEST

ls -lh /tmp/*${BACKUP_DATE}* 2>/dev/null | awk '{print $9 " - " $5}' >> /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt

cat >> /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt << EOFMANIFEST2

==========================================
备份内容详情
==========================================

📦 1. databases_${BACKUP_DATE}.tar.gz
   包含7个核心数据库:
   - crypto_data.db (历史数据)
   - support_resistance.db (支撑压力线)
   - sar_slope_data.db (SAR斜率)
   - anchor_system.db (锚点系统)
   - trading_decision.db (交易决策)
   - fund_monitor.db (资金监控)
   - v1v2_data.db (V1V2成交)

📦 2. git_${BACKUP_DATE}.tar.gz
   完整Git仓库 (.git目录)
   - 所有提交历史
   - 所有分支
   - 所有标签

📦 3. logs_${BACKUP_DATE}.tar.gz
   所有日志文件 (logs目录)

📦 4. code_config_${BACKUP_DATE}.tar.gz
   - HTML模板 (templates/)
   - Python脚本 (*.py)
   - 配置文件 (*.json, *.txt, *.sh)

==========================================
恢复步骤
==========================================

1. 创建恢复目录
   mkdir -p /home/user/webapp_restore
   cd /home/user/webapp_restore

2. 解压所有文件
   tar -xzf /tmp/databases_${BACKUP_DATE}.tar.gz
   tar -xzf /tmp/git_${BACKUP_DATE}.tar.gz
   tar -xzf /tmp/logs_${BACKUP_DATE}.tar.gz
   tar -xzf /tmp/code_config_${BACKUP_DATE}.tar.gz

3. 安装依赖
   pip3 install -r requirements.txt

4. 启动服务
   pm2 resurrect
   pm2 list

==========================================
23个子系统对应关系
==========================================

数据库映射:
1. 历史数据查询系统 -> crypto_data.db
2. 交易信号监控系统 -> crypto_data.db
3. 恐慌清洗指数系统 -> crypto_data.db
4. 比价系统 -> crypto_data.db
5. 星星系统 -> crypto_data.db
6. 币种池系统 -> crypto_data.db
7. 实时市场原始数据 -> crypto_data.db
8. 数据采集监控 -> count_monitor.db
9. 深度图得分 -> crypto_data.db
10. 深度图可视化 -> crypto_data.db
11. 平均分页面 -> crypto_data.db
12. OKEx加密指数 -> crypto_data.db
13. 位置系统 -> crypto_data.db
14. 支撑压力线系统 -> support_resistance.db
15. 决策交易信号系统 -> trading_decision.db
16. 决策-K线指标系统 -> trading_decision.db
17. V1V2成交系统 -> v1v2_data.db
18. 1分钟涨跌幅系统 -> crypto_data.db
19. Google Drive监控系统 -> crypto_data.db (crypto_snapshots表)
20. Telegram消息推送系统 -> 配置文件
21. 资金监控系统 -> fund_monitor.db
22. 锚点系统 -> anchor_system.db
23. 自动交易系统 -> trading_decision.db

页面文件映射:
1. 历史数据查询 -> templates/chart_new.html
2. 交易信号监控 -> templates/monitor.html
3. 恐慌清洗指数 -> templates/panic.html
4. 比价系统 -> templates/price_comparison.html
5. 星星系统 -> templates/crypto_index.html
6. 币种池 -> templates/coin_pool.html
7. 实时市场数据 -> templates/index.html
8. 数据采集监控 -> templates/control_center.html
9. 深度图得分 -> templates/depth_score.html
10. 深度图可视化 -> templates/depth_chart.html
11. 平均分 -> templates/coin_selection.html
12. OKEx指数 -> templates/crypto_index.html
13. 位置系统 -> templates/position_system.html
14. 支撑压力线 -> templates/support_resistance.html
15. 决策交易信号 -> templates/trading_manager.html
16. K线指标 -> templates/kline_indicators.html
17. V1V2成交 -> templates/v1v2_monitor.html
18. 1分钟涨跌幅 -> templates/price_speed_monitor.html
19. Google Drive监控 -> templates/gdrive_detector.html
20. Telegram推送 -> templates/telegram_dashboard.html
21. 资金监控 -> templates/fund_monitor.html
22. 锚点系统 -> templates/anchor_system_real.html
23. 自动交易 -> templates/trading_manager.html

==========================================
EOFMANIFEST2

echo "   ✅ 清单已生成"

echo ""
echo "=========================================="
echo "✅ 备份完成！"
echo "=========================================="
echo ""
echo "📦 备份文件:"
ls -lh /tmp/*${BACKUP_DATE}* 2>/dev/null | awk '{print "   " $9 " - " $5}'

echo ""
TOTAL=$(du -ch /tmp/*${BACKUP_DATE}* 2>/dev/null | grep total | awk '{print $1}')
echo "📊 总计: ${TOTAL}"

echo ""
echo "📋 备份清单: /tmp/BACKUP_MANIFEST_${BACKUP_DATE}.txt"
echo ""
echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
