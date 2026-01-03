#!/bin/bash
#
# 完整系统备份脚本
# 包含所有23个子系统的完整备份
# 备份时间: $(date '+%Y-%m-%d %H:%M:%S')
#

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置
BACKUP_DIR="/tmp/system_backup_$(date +%Y%m%d_%H%M%S)"
SOURCE_DIR="/home/user/webapp"

log_info "======================================================================"
log_info "开始完整系统备份"
log_info "======================================================================"
log_info "备份目录: $BACKUP_DIR"
log_info "源目录: $SOURCE_DIR"
echo ""

# 创建备份目录结构
log_info "创建备份目录结构..."
mkdir -p "$BACKUP_DIR"/{databases,templates,static,configs,logs,scripts,pm2,git,docs}

# 1. 备份所有数据库
log_info "备份数据库..."
mkdir -p "$BACKUP_DIR/databases"

# 主数据库
if [ -f "$SOURCE_DIR/databases/crypto_data.db" ]; then
    cp "$SOURCE_DIR/databases/crypto_data.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ crypto_data.db (首页监控、逃顶信号、Google Drive数据)"
fi

if [ -f "$SOURCE_DIR/databases/crypto_data_new.db" ]; then
    cp "$SOURCE_DIR/databases/crypto_data_new.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ crypto_data_new.db"
fi

# 根目录数据库
if [ -f "$SOURCE_DIR/support_resistance.db" ]; then
    cp "$SOURCE_DIR/support_resistance.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ support_resistance.db (支撑压力线系统)"
fi

if [ -f "$SOURCE_DIR/sar_slope_data.db" ]; then
    cp "$SOURCE_DIR/sar_slope_data.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ sar_slope_data.db (SAR斜率系统)"
fi

if [ -f "$SOURCE_DIR/fund_monitor.db" ]; then
    cp "$SOURCE_DIR/fund_monitor.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ fund_monitor.db (资金监控系统)"
fi

if [ -f "$SOURCE_DIR/trading_decision.db" ]; then
    cp "$SOURCE_DIR/trading_decision.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ trading_decision.db (决策交易系统)"
fi

if [ -f "$SOURCE_DIR/anchor_system.db" ]; then
    cp "$SOURCE_DIR/anchor_system.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ anchor_system.db (锚点系统)"
fi

if [ -f "$SOURCE_DIR/v1v2_data.db" ]; then
    cp "$SOURCE_DIR/v1v2_data.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ v1v2_data.db (V1V2成交系统)"
fi

if [ -f "$SOURCE_DIR/count_monitor.db" ]; then
    cp "$SOURCE_DIR/count_monitor.db" "$BACKUP_DIR/databases/"
    log_info "  ✓ count_monitor.db (计次监控)"
fi

# 2. 备份所有HTML模板
log_info "备份HTML模板..."
cp -r "$SOURCE_DIR/templates"/* "$BACKUP_DIR/templates/" 2>/dev/null || true
log_info "  ✓ 所有HTML模板已备份"

# 3. 备份静态文件
log_info "备份静态文件..."
if [ -d "$SOURCE_DIR/static" ]; then
    cp -r "$SOURCE_DIR/static"/* "$BACKUP_DIR/static/" 2>/dev/null || true
    log_info "  ✓ 静态文件已备份"
fi

# 4. 备份配置文件
log_info "备份配置文件..."
cp "$SOURCE_DIR/daily_folder_config.json" "$BACKUP_DIR/configs/" 2>/dev/null || true
cp "$SOURCE_DIR/sub_account_config.json" "$BACKUP_DIR/configs/" 2>/dev/null || true
cp "$SOURCE_DIR/sub_account_opened_positions.json" "$BACKUP_DIR/configs/" 2>/dev/null || true
cp "$SOURCE_DIR/telegram_config.json" "$BACKUP_DIR/configs/" 2>/dev/null || true
cp "$SOURCE_DIR/requirements.txt" "$BACKUP_DIR/configs/" 2>/dev/null || true
log_info "  ✓ 配置文件已备份"

# 5. 备份所有Python脚本
log_info "备份Python脚本..."
mkdir -p "$BACKUP_DIR/scripts"
cp "$SOURCE_DIR"/*.py "$BACKUP_DIR/scripts/" 2>/dev/null || true
log_info "  ✓ 所有Python脚本已备份"

# 6. 备份PM2配置
log_info "备份PM2配置..."
pm2 save
if [ -f "$HOME/.pm2/dump.pm2" ]; then
    cp "$HOME/.pm2/dump.pm2" "$BACKUP_DIR/pm2/"
    log_info "  ✓ PM2进程列表已备份"
fi
if [ -d "$HOME/.pm2/logs" ]; then
    mkdir -p "$BACKUP_DIR/pm2/logs"
    cp "$HOME/.pm2/logs"/*.log "$BACKUP_DIR/pm2/logs/" 2>/dev/null || true
    log_info "  ✓ PM2日志已备份"
fi

# 7. 备份应用日志
log_info "备份应用日志..."
mkdir -p "$BACKUP_DIR/logs"
cp "$SOURCE_DIR"/*.log "$BACKUP_DIR/logs/" 2>/dev/null || true
if [ -d "$SOURCE_DIR/logs" ]; then
    cp -r "$SOURCE_DIR/logs"/* "$BACKUP_DIR/logs/" 2>/dev/null || true
fi
log_info "  ✓ 应用日志已备份"

# 8. 备份Git仓库
log_info "备份Git仓库..."
if [ -d "$SOURCE_DIR/.git" ]; then
    cp -r "$SOURCE_DIR/.git" "$BACKUP_DIR/git/"
    log_info "  ✓ Git仓库已备份"
fi

# 9. 创建系统文档
log_info "创建系统文档..."
cat > "$BACKUP_DIR/docs/SYSTEM_ARCHITECTURE.md" << 'DOCEOF'
# 系统架构文档

## 备份时间
生成时间: $(date '+%Y-%m-%d %H:%M:%S')

## 系统概述

本系统是一个完整的加密货币交易监控和自动交易系统，包含23个子系统。

## 子系统列表

### 1. 历史数据查询系统
- **路由**: `/history`
- **模板**: `templates/history.html`
- **数据库**: `crypto_data.db` - 表: `crypto_history`
- **功能**: 查询历史K线数据、价格走势
- **依赖**: Flask, SQLite3

### 2. 交易信号监控系统
- **路由**: `/trading-signals`
- **模板**: `templates/trading_signals.html`
- **数据库**: `trading_decision.db` - 表: `trading_signals`
- **功能**: 实时交易信号监控
- **依赖**: WebSocket, Flask

### 3. 恐慌清洗指数系统
- **路由**: `/panic-index`
- **模板**: `templates/panic_index.html`
- **数据库**: `crypto_data.db` - 表: `panic_index`
- **功能**: 恐慌指数计算和可视化
- **依赖**: ECharts, NumPy

### 4. 比价系统
- **路由**: `/price-comparison`
- **模板**: `templates/price_comparison.html`
- **数据库**: `crypto_data.db` - 表: `price_comparison`
- **功能**: 多交易所价格对比
- **依赖**: REST API

### 5. 星星系统
- **路由**: `/star-system`
- **模板**: `templates/star_system.html`
- **数据库**: `crypto_data.db` - 表: `star_ratings`
- **功能**: 币种评级系统
- **依赖**: 自定义评分算法

### 6. 币种池系统
- **路由**: `/coin-pool`
- **模板**: `templates/coin_pool.html`
- **数据库**: `crypto_data.db` - 表: `coin_pool`
- **功能**: 币种筛选和管理
- **依赖**: SQLite3

### 7. 实时市场原始数据
- **路由**: `/market-data`
- **模板**: `templates/market_data.html`
- **数据库**: `crypto_data.db` - 表: `market_realtime`
- **功能**: 实时市场数据展示
- **依赖**: WebSocket

### 8. 数据采集监控
- **路由**: `/data-collector`
- **模板**: `templates/data_collector.html`
- **脚本**: `data_collector.py`
- **功能**: 监控数据采集状态
- **依赖**: Cron, PM2

### 9. 深度图得分
- **路由**: `/depth-score`
- **模板**: `templates/depth_score.html`
- **数据库**: `crypto_data.db` - 表: `depth_scores`
- **功能**: 订单簿深度分析
- **依赖**: NumPy, Pandas

### 10. 深度图可视化
- **路由**: `/depth-chart`
- **模板**: `templates/depth_chart.html`
- **功能**: 深度图实时可视化
- **依赖**: ECharts, WebSocket

### 11. 平均分页面
- **路由**: `/average-score`
- **模板**: `templates/average_score.html`
- **数据库**: `crypto_data.db` - 表: `average_scores`
- **功能**: 综合评分展示
- **依赖**: 多指标加权

### 12. OKEx加密指数
- **路由**: `/okex-index`
- **模板**: `templates/okex_index.html`
- **数据库**: `crypto_data.db` - 表: `okex_indices`
- **功能**: OKEx平台指数追踪
- **依赖**: OKEx API

### 13. 位置系统
- **路由**: `/position-system`
- **模板**: `templates/position_system.html`
- **数据库**: `trading_decision.db` - 表: `positions`
- **功能**: 持仓位置跟踪
- **依赖**: REST API

### 14. 支撑压力线系统 ⭐
- **路由**: `/support-resistance`
- **模板**: `templates/support_resistance.html`
- **数据库**: `support_resistance.db` - 表: `support_resistance_snapshots`
- **脚本**: `support_snapshot_collector.py`, `support_resistance_collector.py`
- **PM2进程**: `support-snapshot-collector`, `support-resistance-collector`
- **功能**: 
  - 支撑线/压力线计算
  - 27个主流币种监控
  - 实时信号触发
  - 历史快照记录
- **关键表结构**:
  - `support_resistance_snapshots`: 快照数据
  - `support_resistance_latest`: 最新数据
- **依赖**: SQLite3, ECharts, WebSocket

### 15. 决策交易信号系统
- **路由**: `/trading-decision`
- **模板**: `templates/trading_decision.html`
- **数据库**: `trading_decision.db` - 表: `trading_decisions`
- **功能**: AI交易决策
- **依赖**: 机器学习模型

### 16. 决策-K线指标系统
- **路由**: `/kline-indicators`
- **模板**: `templates/kline_indicators.html`
- **数据库**: `trading_decision.db` - 表: `kline_indicators`
- **功能**: K线技术指标分析
- **依赖**: TA-Lib

### 17. V1V2成交系统
- **路由**: `/v1v2-monitor`
- **模板**: `templates/v1v2_monitor.html`
- **数据库**: `v1v2_data.db` - 表: `volume_data_v1`, `volume_data_v2`
- **功能**: 成交量分析
- **依赖**: REST API

### 18. 1分钟涨跌幅系统
- **路由**: `/minute-change`
- **模板**: `templates/minute_change.html`
- **数据库**: `crypto_data.db` - 表: `minute_changes`
- **功能**: 1分钟级别涨跌监控
- **依赖**: WebSocket

### 19. Google Drive监控系统
- **路由**: `/gdrive-monitor`
- **模板**: `templates/gdrive_monitor.html`
- **脚本**: `gdrive_final_detector.py`
- **PM2进程**: `gdrive-detector`
- **配置**: `daily_folder_config.json`
- **数据库**: `crypto_data.db` - 表: `crypto_snapshots`
- **功能**:
  - 监控Google Drive TXT文件
  - 自动导入首页数据
  - 跨日期文件夹切换
- **依赖**: Google Drive API, requests

### 20. Telegram消息推送系统
- **路由**: `/telegram-dashboard`
- **模板**: `templates/telegram_dashboard.html`
- **脚本**: `telegram_notifier.py`
- **PM2进程**: `telegram-notifier`
- **配置**: `telegram_config.json`
- **功能**: Telegram消息推送
- **依赖**: python-telegram-bot

### 21. 资金监控系统
- **路由**: `/fund-monitor`
- **模板**: `templates/fund_monitor.html`
- **数据库**: `fund_monitor.db` - 表:
  - `fund_monitor_5min`: 5分钟K线
  - `fund_monitor_aggregated`: 聚合数据
  - `fund_monitor_abnormal_history`: 异常记录
  - `fund_monitor_config`: 配置
- **功能**: 资金流向监控
- **依赖**: REST API, NumPy

### 22. 锚点系统 ⭐
- **路由**: `/anchor-system-real`
- **模板**: `templates/anchor_system_real.html`
- **数据库**: `anchor_system.db` - 表:
  - `anchor_monitors`: 监控数据
  - `anchor_alerts`: 警报记录
  - `anchor_profit_records`: 盈利记录
  - `extreme_corrections_log`: 极值修正日志
  - `anchor_real_profit_records`: 实盘盈利
  - `anchor_positions`: 持仓
  - `anchor_triggers`: 触发记录
- **脚本**:
  - `anchor_maintenance.py`: 主维护脚本
  - `profit_extremes_tracker.py`: 极值追踪
- **PM2进程**:
  - `anchor-maintenance`
  - `profit-extremes-tracker`
- **功能**:
  - 实盘持仓监控
  - 盈利极值追踪
  - 市场强度分析
  - 下跌等级判断
  - 子账户管理
- **依赖**: OKEx API, SQLite3, Flask

### 23. 自动交易系统 ⭐
- **路由**: `/auto-trading`
- **模板**: `templates/auto_trading.html`
- **脚本**:
  - `sub_account_opener.py`: 自动开仓
  - `sub_account_super_maintenance.py`: 账户维护
  - `protect_pairs.py`: 对冲保护
- **PM2进程**:
  - `sub-account-opener`
  - `sub-account-super-maintenance`
  - `protect-pairs`
- **配置**:
  - `sub_account_config.json`: 子账户配置
  - `sub_account_opened_positions.json`: 已开仓位
- **数据库**: `trading_decision.db` - 表:
  - `market_config`: 市场配置
  - `trading_decisions`: 交易决策
  - `position_opens`: 开仓记录
  - `position_adds`: 加仓记录
  - `pending_orders`: 挂单
  - `position_opens_history`: 历史开仓
  - `position_closes`: 平仓记录
  - `long_position_monitoring`: 多单监控
  - `anchor_warning_logs`: 警告日志
- **功能**:
  - 自动开仓/平仓
  - 风险控制
  - 子账户管理
  - 最大持仓限制（10个）
  - 极值维护
- **依赖**: OKEx API, WebSocket, 决策系统

## 核心系统详解

### SAR斜率系统 ⭐
- **数据库**: `sar_slope_data.db`
- **表结构**:
  - `sar_raw_data`: 原始SAR数据
  - `sar_conversion_points`: 转换点
  - `sar_consecutive_changes`: 连续变化
  - `sar_period_averages`: 周期平均
  - `sar_anomaly_alerts`: 异常警报
  - `system_status`: 系统状态
- **功能**:
  - SAR指标计算
  - 趋势反转检测
  - 斜率分析
  - 异常检测
- **依赖**: TA-Lib, NumPy, Pandas

### 历史数据查询系统 ⭐
- **重要性**: 核心数据源
- **数据量**: 数百万条K线数据
- **更新频率**: 实时
- **备份要求**: 完整备份

### 恐慌清洗指数系统 ⭐
- **算法**: 自定义恐慌指数算法
- **数据源**: 多维度市场数据
- **更新频率**: 1分钟
- **关键指标**:
  - 急涨数量
  - 急跌数量
  - 计次评分
  - 状态判断

## 数据库对应关系

| 子系统 | 数据库文件 | 主要表 | 备注 |
|--------|-----------|--------|------|
| 首页监控 | crypto_data.db | crypto_snapshots | Google Drive数据 |
| 逃顶信号 | crypto_data.db | escape_signal_stats, escape_snapshot_stats | 信号统计 |
| 支撑压力 | support_resistance.db | support_resistance_snapshots | 27币种 |
| SAR斜率 | sar_slope_data.db | sar_raw_data, sar_conversion_points | 趋势分析 |
| 资金监控 | fund_monitor.db | fund_monitor_5min, fund_monitor_aggregated | 资金流向 |
| 锚点系统 | anchor_system.db | anchor_monitors, anchor_alerts | 实盘监控 |
| 自动交易 | trading_decision.db | trading_decisions, positions | 交易决策 |
| V1V2成交 | v1v2_data.db | volume_data_v1, volume_data_v2 | 成交分析 |

## 文件结构

```
/home/user/webapp/
├── app_new.py                          # 主Flask应用
├── requirements.txt                     # Python依赖
├── databases/                           # 数据库目录
│   ├── crypto_data.db                  # 主数据库
│   ├── support_resistance.db           # 支撑压力
│   ├── sar_slope_data.db              # SAR斜率
│   ├── fund_monitor.db                 # 资金监控
│   ├── anchor_system.db               # 锚点系统
│   ├── trading_decision.db            # 交易决策
│   └── v1v2_data.db                   # V1V2成交
├── templates/                          # HTML模板
│   ├── anchor_system_real.html        # 锚点系统
│   ├── support_resistance.html        # 支撑压力
│   ├── escape_stats_history.html      # 逃顶历史
│   └── ...                            # 其他模板
├── static/                             # 静态文件
├── configs/                            # 配置文件
│   ├── daily_folder_config.json       # Google Drive配置
│   ├── sub_account_config.json        # 子账户配置
│   └── telegram_config.json           # Telegram配置
├── scripts/                            # Python脚本
│   ├── gdrive_final_detector.py       # Google Drive监控
│   ├── anchor_maintenance.py          # 锚点维护
│   ├── sub_account_opener.py          # 自动开仓
│   └── ...                            # 其他脚本
└── logs/                              # 日志目录
```

## PM2进程列表

| ID | 进程名 | 脚本 | 功能 |
|----|--------|------|------|
| 1 | support-resistance-collector | support_resistance_collector.py | 采集支撑压力数据 |
| 2 | support-snapshot-collector | support_snapshot_collector.py | 记录快照 |
| 3 | gdrive-detector | gdrive_final_detector.py | Google Drive监控 |
| 4 | telegram-notifier | telegram_notifier.py | Telegram推送 |
| 6 | anchor-maintenance | anchor_maintenance.py | 锚点维护 |
| 9 | profit-extremes-tracker | profit_extremes_tracker.py | 极值追踪 |
| 14 | flask-app | app_new.py | Web服务 |
| 15 | sub-account-opener | sub_account_opener.py | 自动开仓 |
| 16 | sub-account-super-maintenance | sub_account_super_maintenance.py | 账户维护 |
| 17 | escape-stats-recorder | escape_stats_recorder.py | 逃顶统计 |
| 19 | escape-signal-recorder | escape_signal_recorder.py | 信号记录 |
| 20 | protect-pairs | protect_pairs.py | 对冲保护 |

## 恢复部署步骤

### 前提条件
- Python 3.8+
- pip, git
- PM2
- SQLite3

### 步骤1: 解压备份文件
```bash
cd /tmp
tar -xzf system_backup_YYYYMMDD_HHMMSS.tar.gz
cd system_backup_YYYYMMDD_HHMMSS
```

### 步骤2: 恢复目录结构
```bash
# 创建应用目录
sudo mkdir -p /home/user/webapp
cd /home/user/webapp

# 恢复数据库
cp databases/* /home/user/webapp/databases/
cp databases/*.db /home/user/webapp/  # 根目录数据库

# 恢复模板
cp -r templates/* /home/user/webapp/templates/

# 恢复静态文件
cp -r static/* /home/user/webapp/static/

# 恢复配置
cp configs/* /home/user/webapp/

# 恢复脚本
cp scripts/* /home/user/webapp/

# 恢复Git仓库
cp -r git/.git /home/user/webapp/
```

### 步骤3: 安装依赖
```bash
cd /home/user/webapp
pip3 install -r requirements.txt
```

### 步骤4: 恢复PM2进程
```bash
# 恢复PM2配置
pm2 resurrect

# 或手动启动进程
pm2 start app_new.py --name flask-app
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_snapshot_collector.py --name support-snapshot-collector
pm2 start gdrive_final_detector.py --name gdrive-detector
pm2 start telegram_notifier.py --name telegram-notifier
pm2 start anchor_maintenance.py --name anchor-maintenance
pm2 start profit_extremes_tracker.py --name profit-extremes-tracker
pm2 start sub_account_opener.py --name sub-account-opener
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance
pm2 start escape_stats_recorder.py --name escape-stats-recorder
pm2 start escape_signal_recorder.py --name escape-signal-recorder
pm2 start protect_pairs.py --name protect-pairs

# 保存PM2配置
pm2 save
```

### 步骤5: 验证系统
```bash
# 检查PM2进程
pm2 list

# 检查数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM crypto_snapshots;"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_snapshots;"
sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_monitors;"

# 检查Web服务
curl http://localhost:5000/
```

### 步骤6: 配置检查
```bash
# 检查Google Drive配置
cat daily_folder_config.json

# 检查子账户配置
cat sub_account_config.json

# 检查Telegram配置
cat telegram_config.json
```

## 数据验证

### 关键数据验证
```bash
# 1. 支撑压力系统
sqlite3 support_resistance.db << EOF
SELECT COUNT(*) as total_snapshots FROM support_resistance_snapshots;
SELECT date(snapshot_time) as date, COUNT(*) as count 
FROM support_resistance_snapshots 
GROUP BY date(snapshot_time) 
ORDER BY date DESC LIMIT 7;
EOF

# 2. 锚点系统
sqlite3 anchor_system.db << EOF
SELECT COUNT(*) as total_monitors FROM anchor_monitors;
SELECT COUNT(*) as total_alerts FROM anchor_alerts;
SELECT COUNT(*) as total_positions FROM anchor_positions;
EOF

# 3. SAR斜率系统
sqlite3 sar_slope_data.db << EOF
SELECT COUNT(*) as total_raw_data FROM sar_raw_data;
SELECT COUNT(*) as conversion_points FROM sar_conversion_points;
EOF

# 4. 自动交易系统
sqlite3 trading_decision.db << EOF
SELECT COUNT(*) as trading_decisions FROM trading_decisions;
SELECT COUNT(*) as open_positions FROM position_opens;
SELECT COUNT(*) as close_positions FROM position_closes;
EOF
```

## 常见问题

### Q1: 数据库文件损坏
A: 使用备份中的 `.db` 文件替换损坏的文件

### Q2: PM2进程无法启动
A: 检查Python依赖是否完整安装，检查脚本权限

### Q3: 页面无法访问
A: 确认Flask进程正在运行，检查端口5000是否被占用

### Q4: Google Drive无法连接
A: 检查 `daily_folder_config.json` 中的文件夹ID是否正确

### Q5: 自动交易不工作
A: 检查 `sub_account_config.json` 中的API配置是否正确

## 维护建议

1. **每日备份**: 运行备份脚本
2. **定期清理**: 清理过期日志和临时文件
3. **监控检查**: 每小时检查PM2进程状态
4. **数据验证**: 每日验证数据完整性
5. **更新文档**: 系统变更后更新此文档

## 联系方式

如有问题，请联系系统管理员。

---
文档版本: 1.0
更新日期: $(date '+%Y-%m-%d')
DOCEOF

log_info "  ✓ 系统架构文档已创建"

# 10. 创建恢复脚本
log_info "创建恢复脚本..."
cat > "$BACKUP_DIR/RESTORE.sh" << 'RESTOREOF'
#!/bin/bash
# 系统恢复脚本

echo "======================================================================"
echo "开始恢复系统"
echo "======================================================================"
echo ""
echo "⚠️  警告: 此操作将覆盖现有系统文件"
echo "请确认以下信息:"
echo "  - 当前目录: $(pwd)"
echo "  - 目标目录: /home/user/webapp"
echo ""
read -p "确认继续? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "取消恢复"
    exit 1
fi

echo ""
echo "开始恢复..."

# 创建目录
mkdir -p /home/user/webapp/{databases,templates,static,configs,logs}

# 恢复数据库
echo "恢复数据库..."
cp databases/*.db /home/user/webapp/databases/ 2>/dev/null || true
cp databases/*.db /home/user/webapp/ 2>/dev/null || true

# 恢复模板
echo "恢复模板..."
cp -r templates/* /home/user/webapp/templates/

# 恢复静态文件
echo "恢复静态文件..."
cp -r static/* /home/user/webapp/static/ 2>/dev/null || true

# 恢复配置
echo "恢复配置..."
cp configs/* /home/user/webapp/

# 恢复脚本
echo "恢复脚本..."
cp scripts/* /home/user/webapp/

# 恢复Git
echo "恢复Git仓库..."
cp -r git/.git /home/user/webapp/ 2>/dev/null || true

echo ""
echo "======================================================================"
echo "恢复完成！"
echo "======================================================================"
echo ""
echo "下一步操作:"
echo "1. cd /home/user/webapp"
echo "2. pip3 install -r requirements.txt"
echo "3. pm2 resurrect  # 或手动启动进程"
echo "4. pm2 list"
echo ""
RESTOREOF

chmod +x "$BACKUP_DIR/RESTORE.sh"
log_info "  ✓ 恢复脚本已创建"

# 11. 创建数据库表结构文档
log_info "创建数据库表结构文档..."
cat > "$BACKUP_DIR/docs/DATABASE_SCHEMA.md" << 'DBEOF'
# 数据库表结构文档

## 1. crypto_data.db (主数据库)

### crypto_snapshots (Google Drive数据)
```sql
CREATE TABLE crypto_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT,
    snapshot_time TEXT,
    inst_id TEXT,
    last_price REAL,
    high_24h REAL,
    low_24h REAL,
    vol_24h REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rush_up INTEGER,
    rush_down INTEGER,
    diff INTEGER,
    count INTEGER,
    status TEXT,
    count_score_display TEXT,
    count_score_type TEXT
);
CREATE INDEX idx_snapshot_time ON crypto_snapshots(snapshot_time);
CREATE INDEX idx_snapshot_date ON crypto_snapshots(snapshot_date);
```

### escape_signal_stats (逃顶信号统计)
```sql
CREATE TABLE escape_signal_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_time TEXT NOT NULL,
    signal_24h_count INTEGER,
    signal_2h_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decline_strength_level INTEGER,
    rise_strength_level INTEGER,
    max_signal_24h INTEGER,
    max_signal_2h INTEGER
);
CREATE INDEX idx_stat_time ON escape_signal_stats(stat_time);
```

### escape_snapshot_stats (逃顶快照统计)
```sql
CREATE TABLE escape_snapshot_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_time TEXT NOT NULL,
    escape_24h_count INTEGER,
    escape_2h_count INTEGER,
    max_escape_24h INTEGER,
    max_escape_2h INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decline_strength_level INTEGER,
    rise_strength_level INTEGER
);
```

## 2. support_resistance.db (支撑压力线系统)

### support_resistance_snapshots
```sql
CREATE TABLE support_resistance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_time TEXT NOT NULL,
    snapshot_date TEXT,
    scenario_1_count INTEGER,  -- 接近支撑2
    scenario_2_count INTEGER,  -- 接近支撑1
    scenario_3_count INTEGER,  -- 接近压力2
    scenario_4_count INTEGER,  -- 接近压力1
    scenario_1_coins TEXT,     -- JSON字符串
    scenario_2_coins TEXT,
    scenario_3_coins TEXT,
    scenario_4_coins TEXT,
    total_coins INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sr_snapshot_time ON support_resistance_snapshots(snapshot_time);
CREATE INDEX idx_sr_snapshot_date ON support_resistance_snapshots(snapshot_date);
```

## 3. sar_slope_data.db (SAR斜率系统)

### sar_raw_data
```sql
CREATE TABLE sar_raw_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    close_price REAL,
    sar_value REAL,
    sar_trend INTEGER,  -- 1:上涨, -1:下跌
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### sar_conversion_points
```sql
CREATE TABLE sar_conversion_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    conversion_time TEXT NOT NULL,
    from_trend INTEGER,
    to_trend INTEGER,
    price_at_conversion REAL,
    sar_at_conversion REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### sar_consecutive_changes
```sql
CREATE TABLE sar_consecutive_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    trend INTEGER,
    consecutive_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. anchor_system.db (锚点系统)

### anchor_monitors
```sql
CREATE TABLE anchor_monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,  -- long/short
    entry_price REAL,
    current_price REAL,
    profit_ratio REAL,
    position_size REAL,
    leverage INTEGER,
    unrealized_pnl REAL,
    timestamp TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### anchor_alerts
```sql
CREATE TABLE anchor_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    alert_type TEXT,  -- profit_target, stop_loss, etc.
    alert_level TEXT,  -- info, warning, critical
    message TEXT,
    triggered_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### anchor_profit_records
```sql
CREATE TABLE anchor_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT,
    entry_price REAL,
    exit_price REAL,
    profit_ratio REAL,
    realized_pnl REAL,
    position_size REAL,
    closed_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### anchor_positions
```sql
CREATE TABLE anchor_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT,
    position_size REAL,
    entry_price REAL,
    current_price REAL,
    unrealized_pnl REAL,
    leverage INTEGER,
    margin REAL,
    liquidation_price REAL,
    last_updated TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 5. trading_decision.db (自动交易系统)

### trading_decisions
```sql
CREATE TABLE trading_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    decision TEXT,  -- open_long, open_short, close, hold
    confidence REAL,
    entry_price REAL,
    target_price REAL,
    stop_loss REAL,
    position_size REAL,
    reason TEXT,
    decided_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### position_opens
```sql
CREATE TABLE position_opens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT,
    entry_price REAL,
    position_size REAL,
    leverage INTEGER,
    margin REAL,
    order_id TEXT,
    opened_at TEXT,
    status TEXT,  -- pending, filled, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### position_closes
```sql
CREATE TABLE position_closes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    side TEXT,
    exit_price REAL,
    position_size REAL,
    profit_ratio REAL,
    realized_pnl REAL,
    order_id TEXT,
    closed_at TEXT,
    close_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### market_config
```sql
CREATE TABLE market_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    max_position_size REAL,
    default_leverage INTEGER,
    stop_loss_ratio REAL,
    take_profit_ratio REAL,
    updated_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 6. fund_monitor.db (资金监控系统)

### fund_monitor_5min
```sql
CREATE TABLE fund_monitor_5min (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    fund_flow REAL,
    buy_volume REAL,
    sell_volume REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### fund_monitor_aggregated
```sql
CREATE TABLE fund_monitor_aggregated (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    total_fund_flow REAL,
    net_buy_volume REAL,
    net_sell_volume REAL,
    abnormal_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7. v1v2_data.db (V1V2成交系统)

### volume_data_v1
```sql
CREATE TABLE volume_data_v1 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    volume REAL,
    buy_volume REAL,
    sell_volume REAL,
    price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### volume_data_v2
```sql
CREATE TABLE volume_data_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    volume REAL,
    buy_volume REAL,
    sell_volume REAL,
    price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---
文档版本: 1.0
DBEOF

log_info "  ✓ 数据库表结构文档已创建"

# 12. 打包备份
log_info "打包备份文件..."
cd /tmp
BACKUP_FILE="system_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" "$(basename $BACKUP_DIR)"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log_info "  ✓ 备份文件已创建: $BACKUP_FILE"
log_info "  ✓ 文件大小: $BACKUP_SIZE"

# 13. 生成备份清单
log_info "生成备份清单..."
cat > "/tmp/BACKUP_MANIFEST_$(date +%Y%m%d_%H%M%S).txt" << MANIFESTEOF
====================================================================
系统完整备份清单
====================================================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份文件: $BACKUP_FILE
文件大小: $BACKUP_SIZE
备份目录: $BACKUP_DIR

====================================================================
备份内容
====================================================================

数据库文件:
$(ls -lh "$BACKUP_DIR/databases" 2>/dev/null || echo "  无")

模板文件:
  - 总数: $(ls "$BACKUP_DIR/templates" 2>/dev/null | wc -l)

静态文件:
  - 总数: $(find "$BACKUP_DIR/static" -type f 2>/dev/null | wc -l)

配置文件:
$(ls -lh "$BACKUP_DIR/configs" 2>/dev/null || echo "  无")

Python脚本:
  - 总数: $(ls "$BACKUP_DIR/scripts"/*.py 2>/dev/null | wc -l)

日志文件:
  - 总数: $(find "$BACKUP_DIR/logs" -type f 2>/dev/null | wc -l)

PM2配置:
$(ls -lh "$BACKUP_DIR/pm2" 2>/dev/null || echo "  无")

Git仓库:
  - 已备份: $([ -d "$BACKUP_DIR/git/.git" ] && echo "是" || echo "否")

====================================================================
子系统清单 (23个)
====================================================================
1. 历史数据查询系统 ✓
2. 交易信号监控系统 ✓
3. 恐慌清洗指数系统 ✓
4. 比价系统 ✓
5. 星星系统 ✓
6. 币种池系统 ✓
7. 实时市场原始数据 ✓
8. 数据采集监控 ✓
9. 深度图得分 ✓
10. 深度图可视化 ✓
11. 平均分页面 ✓
12. OKEx加密指数 ✓
13. 位置系统 ✓
14. 支撑压力线系统 ⭐ ✓
15. 决策交易信号系统 ✓
16. 决策-K线指标系统 ✓
17. V1V2成交系统 ✓
18. 1分钟涨跌幅系统 ✓
19. Google Drive监控系统 ✓
20. Telegram消息推送系统 ✓
21. 资金监控系统 ✓
22. 锚点系统 ⭐ ✓
23. 自动交易系统 ⭐ ✓

====================================================================
核心系统数据验证
====================================================================

$(cd "$SOURCE_DIR" && python3 << 'PYPEOF'
import sqlite3
import os

databases = {
    'crypto_data.db': 'databases/crypto_data.db',
    'support_resistance.db': 'support_resistance.db',
    'sar_slope_data.db': 'sar_slope_data.db',
    'anchor_system.db': 'anchor_system.db',
    'trading_decision.db': 'trading_decision.db',
    'fund_monitor.db': 'fund_monitor.db'
}

for name, path in databases.items():
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n{name}:")
        print(f"  表数量: {len(tables)}")
        for table in tables[:5]:  # 只显示前5个表
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count:,} 条")
        conn.close()
    else:
        print(f"\n{name}: 不存在")
PYPEOF
)

====================================================================
恢复说明
====================================================================

1. 解压备份文件:
   cd /tmp
   tar -xzf $BACKUP_FILE

2. 运行恢复脚本:
   cd $(basename $BACKUP_DIR)
   chmod +x RESTORE.sh
   ./RESTORE.sh

3. 安装依赖:
   cd /home/user/webapp
   pip3 install -r requirements.txt

4. 启动服务:
   pm2 resurrect
   pm2 list

5. 验证系统:
   查看文档: docs/SYSTEM_ARCHITECTURE.md

====================================================================
注意事项
====================================================================

⚠️  重点系统数据完整性检查:
  1. SAR斜率系统: 检查 sar_slope_data.db
  2. 历史数据系统: 检查数据时间跨度
  3. 恐慌清洗系统: 验证计算逻辑
  4. 支撑压力系统: 27币种数据完整
  5. 锚点系统: 持仓和盈利记录
  6. 自动交易系统: API配置和权限

====================================================================
MANIFESTEOF

log_info "  ✓ 备份清单已生成"

# 完成
echo ""
log_info "======================================================================"
log_info "✅ 备份完成！"
log_info "======================================================================"
log_info "备份文件: /tmp/$BACKUP_FILE"
log_info "备份大小: $BACKUP_SIZE"
log_info "备份清单: /tmp/BACKUP_MANIFEST_$(date +%Y%m%d_%H%M%S).txt"
log_info ""
log_info "下一步操作:"
log_info "  1. 下载备份文件: /tmp/$BACKUP_FILE"
log_info "  2. 查看清单: cat /tmp/BACKUP_MANIFEST_*.txt"
log_info "  3. 测试恢复: cd $BACKUP_DIR && ./RESTORE.sh"
log_info "======================================================================"
