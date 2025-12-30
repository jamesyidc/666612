# 完整系统恢复部署指南

**版本**: 2025-12-30  
**备份时间**: $(date '+%Y-%m-%d %H:%M:%S')  
**目标**: 实现1:1完整还原，部署后直接可用

---

## 📋 目录

1. [系统总览](#系统总览)
2. [23个子系统详细说明](#23个子系统详细说明)
3. [数据库对应关系](#数据库对应关系)
4. [恢复部署步骤](#恢复部署步骤)
5. [重点系统专项说明](#重点系统专项说明)
6. [验证测试](#验证测试)
7. [故障排除](#故障排除)

---

## 系统总览

### 备份内容清单

```
system_backup_YYYYMMDD_HHMMSS/
├── databases/              # 10个数据库文件 + SQL转储 + 表结构
├── source_code/           # 完整源代码（Python + JavaScript + HTML）
├── configs/               # 所有配置文件（JSON + ENV）
├── logs/                  # 应用日志 + PM2日志 + 系统日志
├── pm2/                   # PM2进程配置
├── git/                   # Git完整仓库
├── dependencies/          # Python + Node.js依赖清单
├── cache/                 # 缓存数据
├── docs/                  # 本文档
├── SYSTEM_INFO.txt        # 系统信息
├── BACKUP_METADATA.json   # 备份元数据
└── FILE_MANIFEST.txt      # 文件清单
```

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flask Web应用 (端口5000)                  │
│  前端: HTML/CSS/JavaScript + ECharts + WebSocket                │
│  后端: Python Flask + SQLite + OKEx API                        │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   23个子系统 (PM2守护进程)                       │
├─────────────────┬───────────────────┬───────────────────────────┤
│  数据采集层     │   数据处理层      │   业务应用层              │
│  (11个采集器)   │   (6个处理器)     │   (6个应用系统)           │
└─────────────────┴───────────────────┴───────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    10个SQLite数据库                              │
│  crypto_data.db | sar_slope_data.db | support_resistance.db    │
│  signal_data.db | trading_decision.db | anchor_system.db       │
│  v1v2_data.db | fund_monitor.db | count_monitor.db 等          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 23个子系统详细说明

### 【分类1: 数据采集层】- 11个采集器

#### 1. 【历史数据查询系统】
- **PM2进程名**: `crypto-index-collector`
- **源代码文件**: `crypto_index_collector.py`
- **数据库**: `crypto_data.db`
- **表名**: `crypto_index_data`
- **端口**: 无（后台采集）
- **功能**: 采集加密货币历史K线数据
- **依赖**: OKEx API
- **配置文件**: `okex_config.json`
- **日志文件**: `crypto_index_collector.log`
- **启动命令**: `pm2 start crypto_index_collector.py --name crypto-index-collector`
- **采集频率**: 每1分钟
- **数据保留**: 30天

#### 2. 【交易信号监控系统】
- **PM2进程名**: `collector-monitor`
- **源代码文件**: `collector_monitor.py`
- **数据库**: `signal_data.db`
- **表名**: `trading_signals`, `signal_analysis`
- **端口**: 无
- **功能**: 监控采集器状态，发送异常告警
- **页面路由**: `/collector-monitor`
- **日志文件**: `collector_monitor.log`
- **启动命令**: `pm2 start collector_monitor.py --name collector-monitor`
- **检查频率**: 每30秒

#### 3. 【恐慌清洗指数系统】⭐ 重点
- **PM2进程名**: `panic-wash-collector`
- **源代码文件**: `panic_wash_collector.py`
- **数据库**: `crypto_data.db`
- **表名**: `panic_wash_index`
- **端口**: 无
- **功能**: 计算市场恐慌清洗指数
- **页面路由**: `/panic-wash`
- **配置文件**: 无特殊配置
- **日志文件**: `panic_wash_collector.log`
- **启动命令**: `pm2 start panic_wash_collector.py --name panic-wash-collector`
- **计算频率**: 每5分钟
- **指标**: 成交量变化率、价格波动率、持仓变化

#### 4. 【比价系统】
- **PM2进程名**: `price-comparison-collector`
- **源代码文件**: `price_comparison_collector.py`
- **数据库**: `crypto_data.db`
- **表名**: `price_comparison`
- **端口**: 无
- **功能**: 对比不同交易所价格差异
- **页面路由**: `/price-comparison`
- **日志文件**: `price_comparison_collector.log`
- **启动命令**: `pm2 start price_comparison_collector.py --name price-comparison-collector`

#### 5. 【星星系统】（SAR斜率系统）⭐ 重点
- **PM2进程名**: `sar-slope-collector`
- **源代码文件**: `sar_slope_collector.py`
- **数据库**: `sar_slope_data.db`
- **表名**: 
  - `sar_slope_cycles` - SAR周期数据
  - `sar_slope_analysis` - 斜率分析
  - `sar_bias_trend` - 偏离趋势
- **端口**: 无
- **功能**: 抛物线SAR指标斜率分析
- **页面路由**: 
  - `/sar-slope` - 主页面
  - `/sar-bias-trend` - 偏离趋势页面
- **API端点**:
  - `GET /api/sar-slope/current-cycle/<symbol>`
  - `GET /api/sar-slope/bias-trend`
- **配置参数**: SAR初始加速因子0.02，最大0.2
- **日志文件**: `sar_slope_collector.log`
- **启动命令**: `pm2 start sar_slope_collector.py --name sar-slope-collector`
- **采集频率**: 每1分钟
- **币种列表**: 30+主流币种

#### 6. 【币种池系统】
- **PM2进程名**: 无独立进程（集成在Flask中）
- **源代码文件**: `app_new.py` (路由部分)
- **数据库**: `crypto_data.db`
- **表名**: `coin_pool`
- **功能**: 管理交易币种池
- **页面路由**: `/coin-pool`

#### 7. 【实时市场原始数据】
- **PM2进程名**: `websocket-collector`
- **源代码文件**: `websocket_collector.py`
- **数据库**: `crypto_data.db`
- **表名**: `realtime_market_data`
- **端口**: WebSocket连接
- **功能**: WebSocket实时行情推送
- **状态**: errored（需检查）
- **日志文件**: `logs/websocket-collector-*.log`

#### 8. 【数据采集监控】
- **PM2进程名**: `collector-monitor`
- **源代码文件**: `collector_monitor.py`
- **功能**: 监控所有采集器健康状态
- **页面路由**: `/collector-status`

#### 9. 【深度图得分】
- **数据来源**: OKEx Depth API
- **计算逻辑**: 集成在Flask应用中
- **页面路由**: `/depth-score`

#### 10. 【深度图可视化】
- **前端文件**: `templates/depth_chart.html`
- **页面路由**: `/depth-chart`
- **使用ECharts**: 实时深度图展示

#### 11. 【平均分页面】
- **页面路由**: `/average-score`
- **数据源**: 综合各系统得分

### 【分类2: 数据处理层】- 6个处理器

#### 12. 【OKEx加密指数】
- **PM2进程名**: `crypto-index-collector`
- **功能**: 处理加密货币指数
- **集成在**: 历史数据查询系统

#### 13. 【位置系统】
- **PM2进程名**: `position-system-collector`
- **源代码文件**: `position_system_collector.py`
- **数据库**: `crypto_data.db`
- **表名**: `position_data`, `position_history`
- **功能**: 持仓数据采集与分析
- **页面路由**: `/position-system`
- **日志文件**: `position_system.log`
- **启动命令**: `pm2 start position_system_collector.py --name position-system-collector`

#### 14. 【支撑压力线系统】⭐ 重点
- **PM2进程名**: 
  - `support-resistance-collector` - 主采集器
  - `support-resistance-snapshot-collector` - 快照采集器
- **源代码文件**: 
  - `support_resistance_collector.py`
  - `support_resistance_snapshot_collector.py`
- **数据库**: `support_resistance.db`
- **表名**:
  - `support_resistance_lines` - 支撑压力线数据
  - `support_resistance_snapshots` - 历史快照
  - `escape_top_stats` - 逃顶统计
  - `bargain_hunting_stats` - 抄底统计
- **功能**: 
  - 计算支撑压力线
  - 统计逃顶/抄底信号
  - 24小时/2小时统计
- **页面路由**: `/support-resistance`
- **API端点**:
  - `GET /api/support-resistance/lines`
  - `GET /api/support-resistance/stats`
- **日志文件**: `support_resistance.log`, `support_resistance_snapshot.log`
- **启动命令**: 
  ```bash
  pm2 start support_resistance_collector.py --name support-resistance-collector
  pm2 start support_resistance_snapshot_collector.py --name support-resistance-snapshot-collector
  ```
- **采集频率**: 主采集每5分钟，快照每1分钟
- **币种数量**: 30+

#### 15. 【决策交易信号系统】
- **源代码文件**: `trading_decision_system.py`
- **数据库**: `trading_decision.db`
- **表名**: 
  - `decision_signals`
  - `signal_performance`
- **功能**: 综合多指标生成交易决策
- **页面路由**: `/trading-decision`

#### 16. 【决策-K线指标系统】
- **集成在**: Flask应用 `app_new.py`
- **功能**: K线技术指标分析
- **页面路由**: `/kline-indicators`

#### 17. 【V1V2成交系统】
- **PM2进程名**: `v1v2-collector`
- **源代码文件**: `v1v2_collector.py`
- **数据库**: `v1v2_data.db`
- **表名**: `v1v2_trades`
- **功能**: V1/V2成交量分析
- **页面路由**: `/v1v2-system`
- **日志文件**: `v1v2_collector.log`
- **启动命令**: `pm2 start v1v2_collector.py --name v1v2-collector`

#### 18. 【1分钟涨跌幅系统】
- **源代码文件**: `price_speed_collector.py`
- **数据库**: `price_speed_data.db`
- **表名**: `price_changes`
- **功能**: 实时价格变化率监控
- **页面路由**: `/price-speed`

### 【分类3: 业务应用层】- 6个应用系统

#### 19. 【Google Drive监控系统】
- **PM2进程名**: 
  - `gdrive-monitor` - 主监控
  - `gdrive-detector` - 检测器
  - `gdrive-auto-trigger` - 自动触发器
- **源代码文件**: 
  - `gdrive_monitor.py`
  - `gdrive_detector.py`
  - `gdrive_auto_trigger.py`
- **数据库**: 使用Google Drive API
- **功能**: 监控Google Drive文件变化
- **日志文件**: `gdrive_monitor.log`
- **启动命令**: 
  ```bash
  pm2 start gdrive_monitor.py --name gdrive-monitor
  pm2 start gdrive_detector.py --name gdrive-detector
  pm2 start gdrive_auto_trigger.py --name gdrive-auto-trigger
  ```

#### 20. 【TG消息推送系统】
- **PM2进程名**: `telegram-notifier`
- **源代码文件**: `telegram_notifier.py`
- **配置文件**: `telegram_config.json`
- **功能**: 
  - 发送Telegram推送消息
  - 抄底/逃顶信号推送
  - 锚点系统极值推送
- **配置项**:
  - `bot_token`: Telegram Bot Token
  - `chat_id`: 目标Chat ID
  - 信号类型配置
- **日志文件**: `telegram_notifier.log`
- **启动命令**: `pm2 start telegram_notifier.py --name telegram-notifier`

#### 21. 【资金监控系统】
- **PM2进程名**: `fund-monitor-collector`
- **源代码文件**: `fund_monitor_collector.py`
- **数据库**: `fund_monitor.db`
- **表名**: 
  - `fund_flow` - 资金流向
  - `account_balance` - 账户余额
- **功能**: 监控账户资金变化
- **页面路由**: `/fund-monitor`
- **日志文件**: `fund_monitor_collector.log`
- **启动命令**: `pm2 start fund_monitor_collector.py --name fund-monitor-collector`

#### 22. 【锚点系统】⭐ 重点
- **PM2进程名**: 
  - `anchor-system` - 主系统
  - `anchor-maintenance-daemon` - 维护守护进程
  - `anchor-opener-daemon` - 开仓守护进程
- **源代码文件**: 
  - `anchor_system.py` - 主程序
  - `anchor_maintenance_daemon.py` - 维护程序
  - `anchor_opener_daemon.py` - 开仓程序
- **数据库**: `anchor_system.db`
- **表名**:
  - `anchor_profit_records` - 盈利记录（当前持仓）
  - `anchor_monitors` - 监控记录
  - `anchor_alerts` - 告警记录
  - `anchor_extreme_values` - 极值记录
  - `anchor_maintenance_log` - 维护日志
  - `opening_logic_suggestions` - 开仓建议
- **配置文件**: `anchor_config.json`
- **配置项**:
  ```json
  {
    "anchor": {
      "excluded_assets": ["BTC-USDT-SWAP", "ETH-USDT-SWAP"],
      "target_coins": ["CFX", "FIL", "CRO", "UNI", "CRV", "LDO"],
      "check_add_position": true,
      "add_position_trigger": -10.0,
      "prevent_duplicate_minutes": 5
    },
    "monitor": {
      "profit_target": 40.0,
      "loss_limit": -10.0,
      "check_interval": 60,
      "alert_cooldown": 30,
      "only_short_positions": false,
      "trade_mode": "real"
    },
    "telegram": {
      "bot_token": "your_bot_token",
      "chat_id": "your_chat_id",
      "enable_extreme_alerts": true
    }
  }
  ```
- **功能**:
  - 锚定持仓监控
  - 盈利/亏损告警
  - 极值突破推送（TG）
  - 自动维护/开仓
  - 7级盈利统计（≥70%, ≥60%, ≥50%, ≥40%, ≤20%, ≤10%, 亏损）
  - 多头行情判断
  - 1小时增量统计
- **页面路由**: 
  - `/anchor-system-real` - 实盘页面
  - `/anchor-system` - 模拟盘页面
- **API端点**:
  - `GET /api/anchor-system/status` - 系统状态
  - `GET /api/anchor-system/current-positions` - 当前持仓
  - `GET /api/anchor-system/profit-records` - 盈利记录
  - `GET /api/anchor-system/monitors` - 监控记录
  - `GET /api/anchor-system/alerts` - 告警记录
- **前端页面**: `templates/anchor_system_real.html`
- **日志文件**: PM2日志在 `logs/anchor-system-*.log`
- **启动命令**: 
  ```bash
  pm2 start anchor_system.py --name anchor-system
  pm2 start anchor_maintenance_daemon.py --name anchor-maintenance-daemon
  pm2 start anchor_opener_daemon.py --name anchor-opener-daemon
  ```
- **监控频率**: 每60秒检查一次
- **TG推送规则**:
  - 极值突破：无冷却时间，立即推送，显示旧值→新值和增幅
  - 盈利目标：≥40%触发，30分钟冷却期
- **币种编号**:
  - CFX-USDT-SWAP = NO.1
  - FIL-USDT-SWAP = NO.2
  - CRO-USDT-SWAP = NO.3
  - UNI-USDT-SWAP = NO.4
  - CRV-USDT-SWAP = NO.5
  - LDO-USDT-SWAP = NO.6

#### 23. 【自动交易系统】⭐ 重点
- **PM2进程名**: 
  - `conditional-order-monitor` - 条件单监控
  - `position-sync-fast` - 持仓快速同步
  - `long-position-daemon` - 多头持仓守护
  - `sync-indicators-daemon` - 指标同步守护
- **源代码文件**: 
  - `conditional_order_monitor.py`
  - `position_sync_fast.py`
  - `long_position_daemon.py`
  - `sync_indicators_daemon.py`
- **数据库**: 共享 `crypto_data.db`, `trading_decision.db`
- **表名**:
  - `conditional_orders` - 条件单
  - `order_execution_log` - 执行日志
  - `position_sync_log` - 同步日志
- **功能**:
  - 自动下单（条件触发）
  - 持仓同步
  - 多头策略执行
  - 指标实时同步
- **配置文件**: `okex_config.json`（API密钥）
- **日志文件**: 各自对应的PM2日志
- **启动命令**: 
  ```bash
  pm2 start conditional_order_monitor.py --name conditional-order-monitor
  pm2 start position_sync_fast.py --name position-sync-fast
  pm2 start long_position_daemon.py --name long-position-daemon
  pm2 start sync_indicators_daemon.py --name sync-indicators-daemon
  ```
- **安全提示**: ⚠️ 自动交易涉及真实资金，请谨慎配置

### 【额外系统】

#### 24. 【计次监控系统】
- **PM2进程名**: `count-monitor`
- **源代码文件**: `count_monitor.py`
- **数据库**: `count_monitor.db`
- **表名**: `count_records`
- **功能**: 15分钟计次统计和预警
- **页面**: 集成在支撑压力线页面
- **启动命令**: `pm2 start count_monitor.py --name count-monitor`
- **预警规则**: 45分钟增量≥2触发TG推送

#### 25. 【SAR偏离趋势采集器】
- **PM2进程名**: `sar-bias-trend-collector`
- **源代码文件**: `sar_bias_trend_collector.py`
- **数据库**: `sar_slope_data.db`
- **表名**: `sar_bias_trend`
- **功能**: 采集SAR偏离趋势数据
- **页面路由**: `/sar-bias-trend`
- **启动命令**: `pm2 start sar_bias_trend_collector.py --name sar-bias-trend-collector`

---

## 数据库对应关系

### 1. crypto_data.db
**用途**: 主数据库，存储加密货币基础数据

**表结构**:
```sql
-- 加密指数数据
CREATE TABLE crypto_index_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    symbol TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    ...
);

-- 恐慌清洗指数
CREATE TABLE panic_wash_index (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    panic_index REAL,
    wash_index REAL,
    ...
);

-- 价格对比
CREATE TABLE price_comparison (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    exchange_a_price REAL,
    exchange_b_price REAL,
    price_diff REAL,
    ...
);

-- 持仓数据
CREATE TABLE position_data (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    inst_id TEXT,
    pos_side TEXT,
    pos_size REAL,
    avg_price REAL,
    ...
);

-- 实时行情
CREATE TABLE realtime_market_data (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    last_price REAL,
    bid_price REAL,
    ask_price REAL,
    ...
);
```

**关联系统**:
- 历史数据查询系统
- 恐慌清洗指数系统
- 比价系统
- 位置系统

---

### 2. sar_slope_data.db ⭐
**用途**: SAR斜率系统专用数据库

**表结构**:
```sql
-- SAR周期数据
CREATE TABLE sar_slope_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    cycle_id INTEGER,
    cycle_type TEXT,  -- 'UP' or 'DOWN'
    start_time DATETIME,
    end_time DATETIME,
    start_price REAL,
    end_price REAL,
    price_change REAL,
    duration_minutes INTEGER,
    slope REAL,
    ...
);

-- SAR斜率分析
CREATE TABLE sar_slope_analysis (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timestamp DATETIME,
    current_slope REAL,
    slope_trend TEXT,
    signal TEXT,
    ...
);

-- SAR偏离趋势
CREATE TABLE sar_bias_trend (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timestamp DATETIME,
    sar_value REAL,
    price REAL,
    bias_percent REAL,
    trend TEXT,
    ...
);
```

**关联系统**:
- SAR斜率系统（星星系统）
- SAR偏离趋势采集器

**页面**: `/sar-slope`, `/sar-bias-trend`

---

### 3. support_resistance.db ⭐
**用途**: 支撑压力线系统专用数据库

**表结构**:
```sql
-- 支撑压力线
CREATE TABLE support_resistance_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    line_type TEXT,  -- 'SUPPORT' or 'RESISTANCE'
    price_level REAL,
    strength REAL,
    touches INTEGER,
    ...
);

-- 历史快照
CREATE TABLE support_resistance_snapshots (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    snapshot_time DATETIME,
    support_line REAL,
    resistance_line REAL,
    current_price REAL,
    ...
);

-- 逃顶统计
CREATE TABLE escape_top_stats (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    count_24h INTEGER,
    count_2h INTEGER,
    coins_list TEXT,
    ...
);

-- 抄底统计
CREATE TABLE bargain_hunting_stats (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    count_24h INTEGER,
    count_2h INTEGER,
    coins_list TEXT,
    ...
);
```

**关联系统**:
- 支撑压力线系统
- 支撑压力线快照采集器

**页面**: `/support-resistance`

---

### 4. signal_data.db
**用途**: 交易信号和采集器监控数据

**表结构**:
```sql
-- 交易信号
CREATE TABLE trading_signals (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    signal_type TEXT,  -- 'BUY', 'SELL'
    signal_source TEXT,
    confidence REAL,
    ...
);

-- 信号分析
CREATE TABLE signal_analysis (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER,
    analysis_time DATETIME,
    result TEXT,
    profit_loss REAL,
    ...
);

-- 采集器状态
CREATE TABLE collector_status (
    id INTEGER PRIMARY KEY,
    collector_name TEXT,
    last_update DATETIME,
    status TEXT,
    error_count INTEGER,
    ...
);
```

**关联系统**:
- 交易信号监控系统
- 采集器监控系统

---

### 5. trading_decision.db
**用途**: 交易决策系统数据

**表结构**:
```sql
-- 决策信号
CREATE TABLE decision_signals (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    decision TEXT,  -- 'STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'
    score REAL,
    indicators_data TEXT,  -- JSON
    ...
);

-- 信号表现
CREATE TABLE signal_performance (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER,
    entry_time DATETIME,
    entry_price REAL,
    exit_time DATETIME,
    exit_price REAL,
    pnl REAL,
    ...
);

-- 条件单
CREATE TABLE conditional_orders (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    order_type TEXT,
    trigger_condition TEXT,
    target_price REAL,
    status TEXT,
    created_at DATETIME,
    ...
);

-- 执行日志
CREATE TABLE order_execution_log (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    execution_time DATETIME,
    action TEXT,
    result TEXT,
    ...
);
```

**关联系统**:
- 决策交易信号系统
- 自动交易系统

---

### 6. anchor_system.db ⭐
**用途**: 锚点系统专用数据库

**表结构**:
```sql
-- 盈利记录（当前持仓）
CREATE TABLE anchor_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    inst_id TEXT NOT NULL,
    pos_side TEXT,  -- 'long' or 'short'
    pos_size REAL,
    avg_price REAL,
    mark_price REAL,
    upl REAL,  -- 未实现盈亏
    upl_ratio REAL,  -- 盈亏率
    profit_rate REAL,  -- 盈利率%
    record_type TEXT,  -- 'highest_profit' or 'max_loss'
    ...
);

-- 监控记录
CREATE TABLE anchor_monitors (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    inst_id TEXT,
    pos_side TEXT,
    pos_size REAL,
    profit_rate REAL,
    alert_type TEXT,
    alert_sent BOOLEAN,
    created_at DATETIME
);

-- 告警记录
CREATE TABLE anchor_alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    alert_type TEXT,  -- 'PROFIT_TARGET', 'LOSS_LIMIT', 'EXTREME_UPDATE'
    message TEXT,
    sent_status TEXT,
    ...
);

-- 极值记录
CREATE TABLE anchor_extreme_values (
    id INTEGER PRIMARY KEY,
    inst_id TEXT,
    extreme_type TEXT,  -- 'highest_profit' or 'max_loss'
    old_value REAL,
    new_value REAL,
    update_time DATETIME,
    increment_percent REAL,  -- 增加的百分比
    ...
);

-- 维护日志
CREATE TABLE anchor_maintenance_log (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    action TEXT,
    inst_id TEXT,
    details TEXT,
    ...
);

-- 开仓建议
CREATE TABLE opening_logic_suggestions (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    inst_id TEXT,
    suggestion TEXT,
    reason TEXT,
    confidence REAL,
    ...
);
```

**关联系统**:
- 锚点系统
- 锚点维护守护进程
- 锚点开仓守护进程

**页面**: `/anchor-system-real`, `/anchor-system`

**重要字段说明**:
- `record_type`: 
  - `'highest_profit'` - 最高盈利记录
  - `'max_loss'` - 最大亏损记录
- `pos_side`:
  - `'long'` - 多头
  - `'short'` - 空头
- `profit_rate`: 盈利率百分比（正数=盈利，负数=亏损）

---

### 7. v1v2_data.db
**用途**: V1/V2成交系统数据

**表结构**:
```sql
-- V1V2成交数据
CREATE TABLE v1v2_trades (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    v1_volume REAL,
    v2_volume REAL,
    total_volume REAL,
    v1_ratio REAL,
    ...
);
```

**关联系统**:
- V1V2成交系统

---

### 8. fund_monitor.db
**用途**: 资金监控系统数据

**表结构**:
```sql
-- 资金流向
CREATE TABLE fund_flow (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    flow_type TEXT,  -- 'INFLOW', 'OUTFLOW'
    amount REAL,
    currency TEXT,
    ...
);

-- 账户余额
CREATE TABLE account_balance (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    currency TEXT,
    available REAL,
    frozen REAL,
    total REAL,
    ...
);
```

**关联系统**:
- 资金监控系统

---

### 9. count_monitor.db
**用途**: 计次监控系统数据

**表结构**:
```sql
-- 计次记录
CREATE TABLE count_records (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    count_15min INTEGER,
    count_45min INTEGER,
    count_24h INTEGER,
    alert_triggered BOOLEAN,
    ...
);
```

**关联系统**:
- 计次监控系统

---

### 10. price_speed_data.db
**用途**: 1分钟涨跌幅系统数据

**表结构**:
```sql
-- 价格变化
CREATE TABLE price_changes (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol TEXT,
    price_1m_ago REAL,
    current_price REAL,
    change_percent REAL,
    ...
);
```

**关联系统**:
- 1分钟涨跌幅系统

---

## 恢复部署步骤

### 前置准备

#### 1. 系统环境检查
```bash
# 检查操作系统
uname -a

# 检查Python版本（需要3.8+）
python3 --version

# 检查pip
pip3 --version

# 检查Node.js（如果使用）
node --version
npm --version

# 检查PM2
pm2 --version

# 如果未安装PM2
npm install -g pm2
```

#### 2. 创建工作目录
```bash
# 创建恢复目录
sudo mkdir -p /home/user/webapp
sudo chown -R $USER:$USER /home/user/webapp
cd /home/user/webapp
```

---

### 步骤1: 解压备份文件

```bash
# 复制备份文件到目标服务器
scp system_backup_YYYYMMDD_HHMMSS.tar.gz user@target-server:/tmp/

# 登录目标服务器
ssh user@target-server

# 解压备份
cd /tmp
tar xzf system_backup_YYYYMMDD_HHMMSS.tar.gz

# 验证解压
ls -lh system_backup_YYYYMMDD_HHMMSS/

# 进入备份目录
cd system_backup_YYYYMMDD_HHMMSS/
```

---

### 步骤2: 恢复源代码

```bash
# 复制源代码到工作目录
cp -r source_code/* /home/user/webapp/

# 设置权限
cd /home/user/webapp
chmod +x *.py
chmod +x *.sh

# 验证文件
ls -lh
```

---

### 步骤3: 恢复Git仓库

```bash
cd /home/user/webapp

# 解压Git仓库
tar xzf /tmp/system_backup_YYYYMMDD_HHMMSS/git/git_repository_complete.tar.gz

# 验证Git状态
git status
git log --oneline -10
git branch -a

# 如果需要关联远程仓库
git remote add origin https://github.com/your-username/your-repo.git
```

---

### 步骤4: 恢复数据库

```bash
cd /home/user/webapp

# 复制所有数据库文件
cp /tmp/system_backup_YYYYMMDD_HHMMSS/databases/*.db .

# 验证数据库文件
ls -lh *.db

# 验证数据库内容（以anchor_system.db为例）
sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records;"
sqlite3 anchor_system.db "SELECT name FROM sqlite_master WHERE type='table';"

# 如果数据库损坏，使用SQL转储恢复
# sqlite3 anchor_system.db < /tmp/system_backup_YYYYMMDD_HHMMSS/databases/anchor_system_dump.sql
```

**数据库验证清单**:
```bash
# 验证所有数据库
for db in *.db; do
    echo "检查: $db"
    sqlite3 "$db" "PRAGMA integrity_check;"
done
```

---

### 步骤5: 恢复配置文件

```bash
cd /home/user/webapp

# 复制配置文件
cp /tmp/system_backup_YYYYMMDD_HHMMSS/configs/*.json .
cp /tmp/system_backup_YYYYMMDD_HHMMSS/configs/*.yaml . 2>/dev/null || true
cp /tmp/system_backup_YYYYMMDD_HHMMSS/configs/.env* . 2>/dev/null || true

# ⚠️ 重要: 检查并更新敏感配置
echo "请检查以下配置文件中的密钥和Token:"
echo "- okex_config.json (API Key/Secret)"
echo "- telegram_config.json (Bot Token/Chat ID)"
echo "- anchor_config.json (Telegram配置)"

# 编辑配置（如需要）
nano okex_config.json
nano telegram_config.json
nano anchor_config.json
```

**关键配置文件说明**:

**okex_config.json**:
```json
{
  "api_key": "your-api-key",
  "secret_key": "your-secret-key",
  "passphrase": "your-passphrase",
  "base_url": "https://www.okex.com",
  "ws_url": "wss://ws.okex.com:8443/ws/v5/public"
}
```

**telegram_config.json**:
```json
{
  "bot_token": "your-bot-token",
  "chat_id": "your-chat-id",
  "api_base_url": "https://api.telegram.org",
  "enable_notifications": true,
  "signals": {
    "buy": {
      "enabled": true,
      "label": "抄底信号",
      "min_coins": 8
    },
    "sell": {
      "enabled": true,
      "label": "逃顶信号",
      "min_coins": 8
    }
  }
}
```

**anchor_config.json**:
```json
{
  "anchor": {
    "excluded_assets": ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "LTC-USDT-SWAP", "ETC-USDT-SWAP"],
    "target_coins": ["CFX", "FIL", "CRO", "UNI", "CRV", "LDO"],
    "check_add_position": true,
    "add_position_trigger": -10.0,
    "prevent_duplicate_minutes": 5
  },
  "monitor": {
    "profit_target": 40.0,
    "loss_limit": -10.0,
    "check_interval": 60,
    "alert_cooldown": 30,
    "only_short_positions": false,
    "trade_mode": "real"
  },
  "telegram": {
    "bot_token": "your-bot-token",
    "chat_id": "your-chat-id",
    "enable_extreme_alerts": true
  }
}
```

---

### 步骤6: 安装Python依赖

```bash
cd /home/user/webapp

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 或者直接安装到系统
pip3 install -r /tmp/system_backup_YYYYMMDD_HHMMSS/dependencies/requirements.txt

# 验证安装
pip list

# 如果缺少某些依赖，手动安装
pip3 install flask requests sqlite3 websocket-client
```

**核心依赖清单**:
- `Flask` - Web框架
- `requests` - HTTP请求
- `websocket-client` - WebSocket客户端
- `ccxt` - 加密货币交易所API（如果使用）
- `pandas` - 数据处理
- `numpy` - 数值计算

---

### 步骤7: 恢复PM2进程配置

```bash
# 复制PM2配置
cp /tmp/system_backup_YYYYMMDD_HHMMSS/pm2/dump.pm2 ~/.pm2/

# 恢复PM2进程
cd /home/user/webapp
pm2 resurrect

# 或者手动启动所有进程（推荐，确保路径正确）
pm2 start app_new.py --name flask-app
pm2 start crypto_index_collector.py --name crypto-index-collector
pm2 start panic_wash_collector.py --name panic-wash-collector
pm2 start sar_slope_collector.py --name sar-slope-collector
pm2 start sar_bias_trend_collector.py --name sar-bias-trend-collector
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_resistance_snapshot_collector.py --name support-resistance-snapshot-collector
pm2 start anchor_system.py --name anchor-system
pm2 start anchor_maintenance_daemon.py --name anchor-maintenance-daemon
pm2 start anchor_opener_daemon.py --name anchor-opener-daemon
pm2 start position_system_collector.py --name position-system-collector
pm2 start v1v2_collector.py --name v1v2-collector
pm2 start fund_monitor_collector.py --name fund-monitor-collector
pm2 start count_monitor.py --name count-monitor
pm2 start collector_monitor.py --name collector-monitor
pm2 start conditional_order_monitor.py --name conditional-order-monitor
pm2 start position_sync_fast.py --name position-sync-fast
pm2 start long_position_daemon.py --name long-position-daemon
pm2 start sync_indicators_daemon.py --name sync-indicators-daemon
pm2 start telegram_notifier.py --name telegram-notifier
pm2 start gdrive_monitor.py --name gdrive-monitor
pm2 start gdrive_detector.py --name gdrive-detector
pm2 start gdrive_auto_trigger.py --name gdrive-auto-trigger
pm2 start price_comparison_collector.py --name price-comparison-collector
# websocket-collector 可能需要特殊处理（当前状态errored）

# 保存PM2配置
pm2 save

# 设置PM2开机自启（可选）
pm2 startup
```

---

### 步骤8: 启动Flask应用

```bash
cd /home/user/webapp

# 测试Flask应用
python3 app_new.py

# 如果测试正常，使用PM2启动
pm2 start app_new.py --name flask-app

# 查看日志
pm2 logs flask-app --lines 50
```

**Flask端口**: 默认5000

**访问测试**:
```bash
# 测试主页
curl http://localhost:5000/

# 测试API
curl http://localhost:5000/api/anchor-system/status
```

---

### 步骤9: 验证所有进程

```bash
# 查看PM2进程列表
pm2 list

# 查看所有日志
pm2 logs --lines 20

# 查看特定进程日志
pm2 logs anchor-system --lines 100
pm2 logs flask-app --lines 100
pm2 logs sar-slope-collector --lines 50

# 检查进程状态
pm2 status

# 重启异常进程
pm2 restart <process-name>

# 重启所有进程
pm2 restart all
```

**期望状态**: 除 `websocket-collector` 外，所有进程应为 `online`

---

### 步骤10: 验证数据库连接

```bash
cd /home/user/webapp

# 创建测试脚本
cat > test_databases.py << 'EOF'
import sqlite3
import os

databases = [
    "crypto_data.db",
    "sar_slope_data.db",
    "support_resistance.db",
    "signal_data.db",
    "trading_decision.db",
    "anchor_system.db",
    "v1v2_data.db",
    "fund_monitor.db",
    "count_monitor.db",
    "price_speed_data.db"
]

for db_name in databases:
    if os.path.exists(db_name):
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✓ {db_name}: {len(tables)} tables")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"  - {table[0]}: {count} rows")
            conn.close()
        except Exception as e:
            print(f"✗ {db_name}: ERROR - {e}")
    else:
        print(f"✗ {db_name}: NOT FOUND")
    print()
EOF

# 运行测试
python3 test_databases.py
```

---

### 步骤11: 测试Web页面访问

**测试清单**:

```bash
# 假设服务器IP为 SERVER_IP

# 1. 主页
curl http://SERVER_IP:5000/

# 2. 历史数据查询系统
curl http://SERVER_IP:5000/crypto-index

# 3. 恐慌清洗指数系统
curl http://SERVER_IP:5000/panic-wash

# 4. SAR斜率系统（星星系统）
curl http://SERVER_IP:5000/sar-slope
curl http://SERVER_IP:5000/sar-bias-trend

# 5. 支撑压力线系统
curl http://SERVER_IP:5000/support-resistance

# 6. 锚点系统
curl http://SERVER_IP:5000/anchor-system-real
curl http://SERVER_IP:5000/api/anchor-system/status
curl http://SERVER_IP:5000/api/anchor-system/current-positions

# 7. 资金监控系统
curl http://SERVER_IP:5000/fund-monitor

# 8. 其他系统
curl http://SERVER_IP:5000/position-system
curl http://SERVER_IP:5000/v1v2-system
curl http://SERVER_IP:5000/trading-decision
```

**浏览器测试** (推荐):
- http://SERVER_IP:5000/anchor-system-real
- http://SERVER_IP:5000/support-resistance
- http://SERVER_IP:5000/sar-slope

---

### 步骤12: 恢复日志（可选）

```bash
cd /home/user/webapp

# 复制历史日志
cp /tmp/system_backup_YYYYMMDD_HHMMSS/logs/app_logs/*.log .

# 复制PM2日志（如需要）
mkdir -p logs
cp /tmp/system_backup_YYYYMMDD_HHMMSS/logs/pm2_logs/* logs/
```

---

### 步骤13: 配置防火墙和端口（如需要）

```bash
# 开放Flask端口5000
sudo ufw allow 5000/tcp

# 或者使用iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# 保存规则
sudo netfilter-persistent save
```

---

### 步骤14: 设置自动启动（可选）

```bash
# PM2开机自启
pm2 startup
# 按照提示执行命令

pm2 save

# 或者创建systemd服务（更稳定）
sudo cat > /etc/systemd/system/webapp.service << 'EOF'
[Unit]
Description=WebApp Service
After=network.target

[Service]
Type=forking
User=user
WorkingDirectory=/home/user/webapp
ExecStart=/usr/bin/pm2 resurrect
ExecReload=/usr/bin/pm2 reload all
ExecStop=/usr/bin/pm2 kill
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable webapp
sudo systemctl start webapp
```

---

### 步骤15: 最终验证

```bash
# 创建最终验证脚本
cat > final_verification.sh << 'EOF'
#!/bin/bash

echo "========================================="
echo "最终系统验证"
echo "========================================="
echo ""

# 1. PM2进程检查
echo "[1] PM2进程状态:"
pm2 list | grep online | wc -l
echo "个进程在线"
echo ""

# 2. 数据库检查
echo "[2] 数据库文件:"
ls -lh *.db | wc -l
echo "个数据库文件"
echo ""

# 3. Flask应用检查
echo "[3] Flask应用:"
curl -s http://localhost:5000/ > /dev/null && echo "✓ Flask运行正常" || echo "✗ Flask未运行"
echo ""

# 4. 锚点系统API检查
echo "[4] 锚点系统API:"
curl -s http://localhost:5000/api/anchor-system/status > /dev/null && echo "✓ 锚点系统API正常" || echo "✗ 锚点系统API异常"
echo ""

# 5. SAR系统API检查
echo "[5] SAR系统API:"
curl -s "http://localhost:5000/api/sar-slope/current-cycle/BTC-USDT-SWAP" > /dev/null && echo "✓ SAR系统API正常" || echo "✗ SAR系统API异常"
echo ""

# 6. 支撑压力线API检查
echo "[6] 支撑压力线API:"
curl -s http://localhost:5000/api/support-resistance/lines > /dev/null && echo "✓ 支撑压力线API正常" || echo "✗ 支撑压力线API异常"
echo ""

# 7. 日志检查
echo "[7] PM2日志目录:"
ls -lh logs/*.log 2>/dev/null | wc -l
echo "个日志文件"
echo ""

echo "========================================="
echo "验证完成！"
echo "========================================="
EOF

chmod +x final_verification.sh
./final_verification.sh
```

---

## 重点系统专项说明

### 1. SAR斜率系统（星星系统）⭐

**恢复检查清单**:
- [x] 数据库: `sar_slope_data.db` 存在且完整
- [x] 表: `sar_slope_cycles`, `sar_slope_analysis`, `sar_bias_trend` 存在
- [x] 进程: `sar-slope-collector`, `sar-bias-trend-collector` 在线
- [x] 页面: `/sar-slope`, `/sar-bias-trend` 可访问
- [x] API: `/api/sar-slope/current-cycle/<symbol>` 返回数据

**验证脚本**:
```bash
# 检查数据库
sqlite3 sar_slope_data.db "SELECT COUNT(*) FROM sar_slope_cycles;"
sqlite3 sar_slope_data.db "SELECT COUNT(*) FROM sar_bias_trend;"

# 检查进程
pm2 describe sar-slope-collector
pm2 describe sar-bias-trend-collector

# 测试API
curl http://localhost:5000/api/sar-slope/current-cycle/BTC-USDT-SWAP | jq .

# 查看日志
pm2 logs sar-slope-collector --lines 50
```

**常见问题**:
- 如果数据为空: 等待采集器运行1-5分钟
- 如果进程异常: 检查OKEx API配置

---

### 2. 历史数据查询系统

**恢复检查清单**:
- [x] 数据库: `crypto_data.db` 存在
- [x] 表: `crypto_index_data` 有数据
- [x] 进程: `crypto-index-collector` 在线
- [x] 页面: `/crypto-index` 可访问

**验证脚本**:
```bash
sqlite3 crypto_data.db "SELECT COUNT(*) FROM crypto_index_data;"
pm2 logs crypto-index-collector --lines 20
```

---

### 3. 恐慌清洗指数系统

**恢复检查清单**:
- [x] 数据库: `crypto_data.db`
- [x] 表: `panic_wash_index`
- [x] 进程: `panic-wash-collector` 在线
- [x] 页面: `/panic-wash` 可访问

**验证脚本**:
```bash
sqlite3 crypto_data.db "SELECT COUNT(*) FROM panic_wash_index;"
pm2 logs panic-wash-collector --lines 20
curl http://localhost:5000/panic-wash
```

---

### 4. 支撑压力线系统⭐

**恢复检查清单**:
- [x] 数据库: `support_resistance.db` 存在且完整
- [x] 表: `support_resistance_lines`, `escape_top_stats`, `bargain_hunting_stats`
- [x] 进程: `support-resistance-collector`, `support-resistance-snapshot-collector` 在线
- [x] 页面: `/support-resistance` 可访问
- [x] 24小时逃顶统计显示
- [x] 2小时逃顶统计显示
- [x] 计次监控系统集成

**验证脚本**:
```bash
# 检查数据库
sqlite3 support_resistance.db "SELECT name FROM sqlite_master WHERE type='table';"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_lines;"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM escape_top_stats;"

# 检查进程
pm2 list | grep support-resistance

# 测试API
curl http://localhost:5000/api/support-resistance/lines | jq .
curl http://localhost:5000/api/support-resistance/stats | jq .

# 查看页面
curl http://localhost:5000/support-resistance
```

**重要配置**:
- 采集频率: 主采集5分钟，快照1分钟
- 统计周期: 24小时和2小时
- 计次监控: 15分钟计次，45分钟增量≥2触发TG

---

### 5. 锚点系统⭐⭐⭐（最重要）

**恢复检查清单**:
- [x] 数据库: `anchor_system.db` 存在且完整
- [x] 表: 
  - `anchor_profit_records` - 当前持仓数据完整
  - `anchor_monitors` - 监控记录
  - `anchor_alerts` - 告警记录
  - `anchor_extreme_values` - 极值记录
  - `anchor_maintenance_log` - 维护日志
  - `opening_logic_suggestions` - 开仓建议
- [x] 配置文件: `anchor_config.json` 配置正确
- [x] TG配置: `telegram_config.json` 或 `anchor_config.json` 中TG配置正确
- [x] 进程: 
  - `anchor-system` 在线
  - `anchor-maintenance-daemon` 在线
  - `anchor-opener-daemon` 在线
- [x] 页面: 
  - `/anchor-system-real` 可访问
  - 7个盈利级别卡片显示
  - 状态栏正确切换
  - 币种编号显示（NO.1-NO.6）
- [x] API: 所有API端点返回数据
- [x] TG推送: 
  - 极值突破推送正常
  - 盈利目标推送正常
  - 增幅百分比显示正确

**详细验证脚本**:
```bash
#!/bin/bash
echo "==================================================="
echo "锚点系统完整验证"
echo "==================================================="

# 1. 数据库检查
echo "[1] 数据库检查"
echo "数据库文件大小:"
ls -lh anchor_system.db
echo ""

echo "数据库表列表:"
sqlite3 anchor_system.db "SELECT name FROM sqlite_master WHERE type='table';"
echo ""

echo "当前持仓数量:"
sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records;"
echo ""

echo "最近10条持仓:"
sqlite3 anchor_system.db "SELECT inst_id, pos_side, pos_size, profit_rate, record_type FROM anchor_profit_records ORDER BY timestamp DESC LIMIT 10;"
echo ""

# 2. 配置检查
echo "[2] 配置文件检查"
if [ -f "anchor_config.json" ]; then
    echo "✓ anchor_config.json 存在"
    echo "盈利目标: $(jq -r '.monitor.profit_target' anchor_config.json)%"
    echo "止损限制: $(jq -r '.monitor.loss_limit' anchor_config.json)%"
    echo "检查间隔: $(jq -r '.monitor.check_interval' anchor_config.json)秒"
    echo "告警冷却: $(jq -r '.monitor.alert_cooldown' anchor_config.json)分钟"
else
    echo "✗ anchor_config.json 不存在"
fi
echo ""

# 3. 进程检查
echo "[3] PM2进程检查"
pm2 list | grep anchor
echo ""

# 4. API检查
echo "[4] API端点检查"
echo "系统状态:"
curl -s http://localhost:5000/api/anchor-system/status | jq .
echo ""

echo "当前持仓:"
curl -s http://localhost:5000/api/anchor-system/current-positions | jq '. | length'
echo "条持仓"
echo ""

# 5. 日志检查
echo "[5] 日志检查"
echo "最近20条anchor-system日志:"
pm2 logs anchor-system --lines 20 --nostream
echo ""

# 6. TG推送检查
echo "[6] TG推送配置检查"
if grep -q "bot_token" anchor_config.json 2>/dev/null; then
    echo "✓ TG配置存在于 anchor_config.json"
elif [ -f "telegram_config.json" ]; then
    echo "✓ TG配置存在于 telegram_config.json"
else
    echo "✗ 未找到TG配置"
fi
echo ""

# 7. 盈利统计检查
echo "[7] 盈利分级统计"
echo "盈利≥70%: $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate >= 70;")"
echo "盈利≥60%: $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate >= 60;")"
echo "盈利≥50%: $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate >= 50;")"
echo "盈利≥40%: $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate >= 40;")"
echo "盈利≤20% (且>0): $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate > 0 AND profit_rate <= 20;")"
echo "盈利≤10% (且>0): $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate > 0 AND profit_rate <= 10;")"
echo "亏损 (<0): $(sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records WHERE pos_side='short' AND profit_rate < 0;")"
echo ""

echo "==================================================="
echo "锚点系统验证完成"
echo "==================================================="
```

保存为 `verify_anchor_system.sh`，运行：
```bash
chmod +x verify_anchor_system.sh
./verify_anchor_system.sh
```

**锚点系统币种编号配置**:
```javascript
// templates/anchor_system_real.html 中的映射
const coinNumbers = {
    'CFX-USDT-SWAP': 'NO.1',
    'FIL-USDT-SWAP': 'NO.2',
    'CRO-USDT-SWAP': 'NO.3',
    'UNI-USDT-SWAP': 'NO.4',
    'CRV-USDT-SWAP': 'NO.5',
    'LDO-USDT-SWAP': 'NO.6'
};
```

**锚点系统触发规则优先级**:
1. **多头行情** (蓝色，最高优先级)
   - 空单盈利≤20% (且>0) ≥ 8
   - 空单盈利≤10% (且>0) ≥ 6
   - 空单亏损 ≥ 2

2. **触底反弹** (绿色)
   - 空单盈利≥70% ≥ 1
   - 空单盈利≥60% ≥ 2
   - 空单盈利≥50% ≥ 5
   - 空单盈利≥40% ≥ 8

3. **多转空** (红色)
   - 空单盈利≥70% = 0
   - 空单盈利≥50% ≥ 1
   - 空单盈利≥40% ≥ 3

**TG推送规则**:
- **极值突破**: 无冷却时间，立即推送
  - 显示格式: `最高盈利: 57.16% → 57.68% (+0.52%)`
- **盈利目标**: ≥40%触发，30分钟冷却期
  - 显示格式: `STX-USDT-SWAP 盈利率达到 57.68%`

**关键数据表字段**:
```sql
-- anchor_profit_records 表
inst_id TEXT          -- 合约ID，如 'STX-USDT-SWAP'
pos_side TEXT         -- 方向: 'long' or 'short'
pos_size REAL         -- 持仓量
avg_price REAL        -- 开仓均价
mark_price REAL       -- 标记价格
profit_rate REAL      -- 盈利率%（正=盈利，负=亏损）
record_type TEXT      -- 'highest_profit' or 'max_loss'
timestamp DATETIME    -- 记录时间
```

---

### 6. 自动交易系统⭐

**恢复检查清单**:
- [x] 数据库: `trading_decision.db`, `crypto_data.db`
- [x] 表: `conditional_orders`, `order_execution_log`
- [x] 配置: `okex_config.json` 的API密钥正确
- [x] 进程: 
  - `conditional-order-monitor` 在线
  - `position-sync-fast` 在线
  - `long-position-daemon` 在线
  - `sync-indicators-daemon` 在线

**⚠️ 安全警告**:
```
自动交易系统涉及真实资金操作！
恢复后请务必：
1. 检查API密钥权限（只读/交易）
2. 检查条件单触发逻辑
3. 设置止损和风控参数
4. 监控首次执行情况
5. 准备紧急停止机制
```

**验证脚本**:
```bash
# 检查条件单
sqlite3 trading_decision.db "SELECT * FROM conditional_orders WHERE status='ACTIVE';"

# 检查进程
pm2 list | grep -E "conditional|position|daemon"

# 查看执行日志
pm2 logs conditional-order-monitor --lines 50

# 测试模式运行（推荐）
# 在 okex_config.json 中设置 "test_mode": true
```

---

## 验证测试

### 完整系统测试清单

#### Level 1: 基础验证
```bash
[ ] 所有*.db文件存在
[ ] 所有*.py文件存在
[ ] 所有配置文件存在
[ ] Git仓库完整
[ ] Python依赖安装完成
```

#### Level 2: 进程验证
```bash
[ ] PM2显示24+个进程
[ ] flask-app进程在线
[ ] anchor-system进程在线
[ ] sar-slope-collector进程在线
[ ] support-resistance-collector进程在线
[ ] 其他采集器进程在线
```

#### Level 3: 数据库验证
```bash
[ ] anchor_system.db完整性检查通过
[ ] sar_slope_data.db完整性检查通过
[ ] support_resistance.db完整性检查通过
[ ] crypto_data.db完整性检查通过
[ ] 所有表能正常查询
```

#### Level 4: API验证
```bash
[ ] GET / 返回200
[ ] GET /api/anchor-system/status 返回数据
[ ] GET /api/sar-slope/current-cycle/BTC-USDT-SWAP 返回数据
[ ] GET /api/support-resistance/lines 返回数据
[ ] GET /api/anchor-system/current-positions 返回数据
```

#### Level 5: 页面验证
```bash
[ ] /anchor-system-real 页面加载
[ ] /sar-slope 页面加载
[ ] /support-resistance 页面加载
[ ] /panic-wash 页面加载
[ ] 所有图表正常显示
```

#### Level 6: 功能验证
```bash
[ ] 锚点系统7个盈利卡片显示数据
[ ] 锚点系统状态栏正确切换
[ ] 锚点系统币种编号(NO.1-6)显示
[ ] SAR斜率周期数据更新
[ ] 支撑压力线24h/2h统计显示
[ ] TG推送配置正确
```

---

## 故障排除

### 常见问题1: 数据库锁定
**症状**: `database is locked` 错误

**解决方案**:
```bash
# 检查占用进程
lsof anchor_system.db

# 重启相关进程
pm2 restart anchor-system

# 如果无效，重建数据库连接
pm2 restart all
```

---

### 常见问题2: PM2进程启动失败
**症状**: 进程状态为 `errored` 或 `stopped`

**解决方案**:
```bash
# 查看错误日志
pm2 logs <process-name> --lines 100 --err

# 检查Python路径
which python3

# 检查文件权限
ls -l <script-name>.py

# 手动测试
python3 <script-name>.py

# 重新启动
pm2 delete <process-name>
pm2 start <script-name>.py --name <process-name>
```

---

### 常见问题3: API返回空数据
**症状**: API返回 `[]` 或 `null`

**解决方案**:
```bash
# 检查数据库是否有数据
sqlite3 <database>.db "SELECT COUNT(*) FROM <table>;"

# 等待采集器运行
# 大部分采集器需要1-5分钟才能开始采集数据

# 检查OKEx API连接
curl https://www.okex.com/api/v5/public/time

# 查看采集器日志
pm2 logs <collector-name> --lines 50
```

---

### 常见问题4: Flask应用无法访问
**症状**: 无法连接到5000端口

**解决方案**:
```bash
# 检查Flask进程
pm2 describe flask-app

# 检查端口占用
netstat -tlnp | grep 5000
# 或
ss -tlnp | grep 5000

# 检查防火墙
sudo ufw status
sudo iptables -L -n | grep 5000

# 重启Flask
pm2 restart flask-app

# 查看详细日志
pm2 logs flask-app --lines 200
```

---

### 常见问题5: TG推送不工作
**症状**: 没有收到Telegram消息

**解决方案**:
```bash
# 1. 检查TG配置
cat anchor_config.json | jq '.telegram'
cat telegram_config.json

# 2. 测试TG连接
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"

# 3. 测试发送消息
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>" \
  -d "text=测试消息"

# 4. 检查telegram-notifier进程
pm2 logs telegram-notifier --lines 50

# 5. 检查锚点系统TG配置
sqlite3 anchor_system.db "SELECT * FROM anchor_alerts ORDER BY timestamp DESC LIMIT 10;"
```

---

### 常见问题6: 锚点系统统计不准确
**症状**: 盈利统计卡片显示错误

**解决方案**:
```bash
# 1. 手动检查数据库统计
sqlite3 anchor_system.db << 'SQL'
SELECT 
  COUNT(CASE WHEN profit_rate >= 70 THEN 1 END) as profit_70,
  COUNT(CASE WHEN profit_rate >= 60 THEN 1 END) as profit_60,
  COUNT(CASE WHEN profit_rate >= 50 THEN 1 END) as profit_50,
  COUNT(CASE WHEN profit_rate >= 40 THEN 1 END) as profit_40,
  COUNT(CASE WHEN profit_rate > 0 AND profit_rate <= 20 THEN 1 END) as profit_below_20,
  COUNT(CASE WHEN profit_rate > 0 AND profit_rate <= 10 THEN 1 END) as profit_below_10,
  COUNT(CASE WHEN profit_rate < 0 THEN 1 END) as loss_count
FROM anchor_profit_records
WHERE pos_side = 'short';
SQL

# 2. 清除浏览器缓存并刷新页面
# Ctrl+Shift+R (强制刷新)

# 3. 检查前端JavaScript错误
# 打开浏览器开发者工具 (F12)，查看Console

# 4. 重启anchor-system进程
pm2 restart anchor-system
```

---

### 常见问题7: websocket-collector进程错误
**症状**: PM2显示 `websocket-collector` 状态为 `errored`

**解决方案**:
```bash
# 1. 查看错误日志
pm2 logs websocket-collector --err --lines 100

# 2. 检查WebSocket配置
cat okex_config.json | jq '.ws_url'

# 3. 测试WebSocket连接（使用Python）
python3 << 'EOF'
import websocket
import json

def on_message(ws, message):
    print("Received:", message)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    # 订阅BTC-USDT行情
    ws.send(json.dumps({
        "op": "subscribe",
        "args": [{"channel": "tickers", "instId": "BTC-USDT-SWAP"}]
    }))

ws = websocket.WebSocketApp("wss://ws.okex.com:8443/ws/v5/public",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
ws.run_forever()
EOF

# 4. 如果不是关键功能，可以暂时禁用
pm2 delete websocket-collector

# 5. 或者修复后重新启动
pm2 start websocket_collector.py --name websocket-collector
```

---

### 常见问题8: 数据库文件损坏
**症状**: `database disk image is malformed`

**解决方案**:
```bash
# 1. 尝试恢复
sqlite3 <damaged>.db "PRAGMA integrity_check;"

# 2. 导出并重建
sqlite3 <damaged>.db .dump > dump.sql
mv <damaged>.db <damaged>.db.bak
sqlite3 <damaged>.db < dump.sql

# 3. 如果无法恢复，使用备份中的SQL转储
sqlite3 <damaged>.db < /tmp/system_backup_YYYYMMDD_HHMMSS/databases/<database>_dump.sql

# 4. 验证
sqlite3 <damaged>.db "PRAGMA integrity_check;"
```

---

## 附录A: 快速命令参考

### PM2命令
```bash
# 查看所有进程
pm2 list

# 启动进程
pm2 start <script>.py --name <name>

# 重启进程
pm2 restart <name>
pm2 restart all

# 停止进程
pm2 stop <name>
pm2 stop all

# 删除进程
pm2 delete <name>
pm2 delete all

# 查看日志
pm2 logs <name>
pm2 logs <name> --lines 100
pm2 logs --err  # 只看错误日志

# 保存配置
pm2 save

# 恢复配置
pm2 resurrect

# 监控
pm2 monit
```

### SQLite命令
```bash
# 进入数据库
sqlite3 database.db

# 查看表
.tables

# 查看表结构
.schema <table_name>

# 导出数据
.dump > backup.sql

# 导入数据
.read backup.sql

# 退出
.quit

# 命令行查询
sqlite3 database.db "SELECT * FROM table LIMIT 10;"
```

### Git命令
```bash
# 查看状态
git status

# 查看日志
git log --oneline -20

# 查看分支
git branch -a

# 切换分支
git checkout <branch>

# 拉取更新
git pull origin <branch>

# 推送更新
git push origin <branch>
```

---

## 附录B: 系统架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                          用户浏览器                                 │
│                     (访问 http://IP:5000)                          │
└─────────────────────────────┬──────────────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                     Flask Web应用 (端口5000)                       │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  路由层: @app.route()                                        │ │
│  │  - /anchor-system-real                                       │ │
│  │  - /sar-slope                                                │ │
│  │  - /support-resistance                                       │ │
│  │  - /api/*                                                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  业务逻辑层: Python Functions                                │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  数据访问层: SQLite Queries                                  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  10个SQLite DB   │ │  PM2守护进程      │ │  外部API         │
│                  │ │  (24+个进程)      │ │                  │
│ • crypto_data    │ │                  │ │ • OKEx API       │
│ • sar_slope_data │ │ 数据采集器:       │ │ • Telegram API   │
│ • support_res... │ │ - crypto-index   │ │ • Google Drive   │
│ • anchor_system  │ │ - sar-slope      │ │                  │
│ • signal_data    │ │ - support-res... │ │                  │
│ • trading_dec... │ │ - panic-wash     │ │                  │
│ • v1v2_data      │ │ ...              │ │                  │
│ • fund_monitor   │ │                  │ │                  │
│ • count_monitor  │ │ 业务守护进程:     │ │                  │
│ • price_speed... │ │ - anchor-system  │ │                  │
│                  │ │ - telegram-not.. │ │                  │
│                  │ │ ...              │ │                  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 附录C: 文件结构树

```
/home/user/webapp/
├── *.db (10个数据库)
│   ├── anchor_system.db ⭐
│   ├── sar_slope_data.db ⭐
│   ├── support_resistance.db ⭐
│   ├── crypto_data.db
│   ├── signal_data.db
│   ├── trading_decision.db
│   ├── v1v2_data.db
│   ├── fund_monitor.db
│   ├── count_monitor.db
│   └── price_speed_data.db
│
├── *.json (配置文件)
│   ├── anchor_config.json ⭐
│   ├── telegram_config.json ⭐
│   ├── okex_config.json ⭐
│   └── ...
│
├── *.py (Python源代码)
│   ├── app_new.py (Flask主应用) ⭐
│   ├── anchor_system.py ⭐
│   ├── anchor_maintenance_daemon.py ⭐
│   ├── anchor_opener_daemon.py ⭐
│   ├── sar_slope_collector.py ⭐
│   ├── sar_bias_trend_collector.py
│   ├── support_resistance_collector.py ⭐
│   ├── support_resistance_snapshot_collector.py
│   ├── crypto_index_collector.py
│   ├── panic_wash_collector.py
│   ├── position_system_collector.py
│   ├── v1v2_collector.py
│   ├── fund_monitor_collector.py
│   ├── count_monitor.py
│   ├── telegram_notifier.py
│   ├── conditional_order_monitor.py
│   ├── position_sync_fast.py
│   ├── long_position_daemon.py
│   ├── sync_indicators_daemon.py
│   ├── collector_monitor.py
│   ├── gdrive_monitor.py
│   ├── gdrive_detector.py
│   ├── gdrive_auto_trigger.py
│   ├── price_comparison_collector.py
│   └── websocket_collector.py
│
├── templates/ (HTML模板)
│   ├── anchor_system_real.html ⭐
│   ├── sar_slope.html
│   ├── sar_bias_trend.html
│   ├── support_resistance.html ⭐
│   ├── panic_wash.html
│   └── ...
│
├── static/ (静态资源)
│   ├── css/
│   ├── js/
│   └── images/
│
├── logs/ (PM2日志)
│   ├── flask-app-*.log
│   ├── anchor-system-*.log
│   └── ...
│
├── *.log (应用日志)
│   ├── crypto_index_collector.log
│   ├── panic_wash_collector.log
│   ├── sar_slope_collector.log
│   ├── support_resistance.log
│   └── ...
│
└── .git/ (Git仓库)
```

---

## 附录D: 关键配置文件模板

### anchor_config.json 完整模板
```json
{
  "anchor": {
    "description": "锚点单配置",
    "excluded_assets": [
      "BTC-USDT-SWAP",
      "ETH-USDT-SWAP",
      "LTC-USDT-SWAP",
      "ETC-USDT-SWAP"
    ],
    "excluded_reason": "非锚点资产",
    "target_coins": [
      "CFX",
      "FIL",
      "CRO",
      "UNI",
      "CRV",
      "LDO"
    ],
    "rules": {
      "check_add_position": true,
      "add_position_trigger": -10.0,
      "min_amount_handling": "dynamic",
      "prevent_duplicate_minutes": 5
    }
  },
  "monitor": {
    "profit_target": 40.0,
    "loss_limit": -10.0,
    "check_interval": 60,
    "alert_cooldown": 30,
    "only_short_positions": false,
    "trade_mode": "real"
  },
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE",
    "enable_extreme_alerts": true,
    "enable_profit_target_alerts": true
  },
  "database": {
    "path": "/home/user/webapp/anchor_system.db"
  },
  "last_updated": "2025-12-30",
  "updated_by": "GenSpark AI Developer"
}
```

### telegram_config.json 完整模板
```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "chat_id": "YOUR_CHAT_ID_HERE",
  "api_base_url": "https://api.telegram.org",
  "enable_notifications": true,
  "message_settings": {
    "parse_mode": "HTML",
    "disable_web_page_preview": true,
    "disable_notification": false
  },
  "signals": {
    "buy": {
      "enabled": true,
      "label": "抄底信号 🟢",
      "color": "green",
      "min_coins": 8
    },
    "sell": {
      "enabled": true,
      "label": "逃顶信号 🔴",
      "color": "red",
      "min_coins": 8
    },
    "double_buy": {
      "enabled": true,
      "label": "双重抄底信号 🟢🟢",
      "min_coins": 1
    },
    "double_sell": {
      "enabled": true,
      "label": "双重逃顶信号 🔴🔴",
      "min_coins": 1
    }
  },
  "push_conditions": {
    "min_coins": 1,
    "cooldown_seconds": 300,
    "max_retries": 3,
    "retry_delay": 5
  },
  "templates": {
    "buy_signal": "🟢 <b>{signal_type}</b>\n\n⏰ 时间: {time}\n💰 币种数量: {count}\n📋 币种列表:\n{coins}\n\n💡 提示: 价格接近支撑线\n\n🔗 <a href='{url}'>查看详情</a>",
    "sell_signal": "🔴 <b>{signal_type}</b>\n\n⏰ 时间: {time}\n💰 币种数量: {count}\n📋 币种列表:\n{coins}\n\n💡 提示: 价格接近压力线\n\n🔗 <a href='{url}'>查看详情</a>"
  }
}
```

### okex_config.json 模板
```json
{
  "api_key": "YOUR_API_KEY_HERE",
  "secret_key": "YOUR_SECRET_KEY_HERE",
  "passphrase": "YOUR_PASSPHRASE_HERE",
  "base_url": "https://www.okex.com",
  "ws_url": "wss://ws.okex.com:8443/ws/v5/public",
  "test_mode": false,
  "request_timeout": 30,
  "max_retries": 3
}
```

---

## 结语

本文档提供了完整的系统恢复部署指南，涵盖23个子系统、10个数据库、所有配置和详细步骤。

**重点系统**（必须100%完整恢复）:
1. ✅ SAR斜率系统（星星系统）
2. ✅ 历史数据查询系统  
3. ✅ 恐慌清洗指数系统
4. ✅ 支撑压力线系统
5. ✅ 锚点系统
6. ✅ 自动交易系统

**恢复原则**: 1:1完整还原，部署后直接可用

**验证标准**: 所有页面可访问，所有API返回数据，所有进程在线

如有问题，请参考"故障排除"章节或查看备份中的日志文件。

---

**文档版本**: 2.0  
**更新时间**: 2025-12-30  
**作者**: GenSpark AI Developer  
**备份位置**: `/tmp/system_backup_YYYYMMDD_HHMMSS/`  

---
