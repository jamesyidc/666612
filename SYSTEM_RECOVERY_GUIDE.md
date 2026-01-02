# 🚀 系统完整恢复指南

**创建时间**: 2026-01-02  
**版本**: v2.0  
**系统名称**: 加密货币交易分析系统

---

## 📋 目录

1. [系统概述](#系统概述)
2. [23个子系统详细说明](#23个子系统详细说明)
3. [数据库架构](#数据库架构)
4. [恢复步骤](#恢复步骤)
5. [PM2进程配置](#pm2进程配置)
6. [重点系统详解](#重点系统详解)

---

## 📊 系统概述

### 技术栈
- **后端**: Python 3.x + Flask
- **数据库**: SQLite3
- **进程管理**: PM2
- **版本控制**: Git
- **部署环境**: Linux

### 系统架构
```
/home/user/webapp/
├── app_new.py              # 主Flask应用
├── databases/              # 数据库目录
│   ├── crypto_data.db     # 主数据库
│   ├── gdrive_monitor.db  # Google Drive监控
│   ├── panic_index.db     # 恐慌指数
│   └── market_data.db     # 市场数据
├── support_resistance.db   # 支撑压力线数据库
├── templates/              # HTML模板
├── static/                 # 静态资源
├── *.py                   # 各子系统脚本
└── *.json                 # 配置文件

---

## 🎯 23个子系统详细说明

### 1. 历史数据查询系统 📜
**文件**: 
- `app_new.py` (路由: `/api/history/*`)
- `templates/history.html`

**数据库表**:
- `crypto_data.db`: `historical_data`, `kline_data`

**功能**: 查询历史K线、交易数据

**API端点**:
- `GET /api/history/kline`
- `GET /api/history/trades`

**恢复优先级**: ⭐⭐⭐

---

### 2. 交易信号监控系统 🚦
**文件**:
- `signal_monitor.py`
- `templates/signals.html`

**数据库表**:
- `crypto_data.db`: `trade_signals`, `signal_history`

**PM2进程**: `signal-monitor`

**功能**: 实时监控交易信号、买卖点提示

**恢复优先级**: ⭐⭐⭐⭐

---

### 3. 恐慌清洗指数系统 😱
**文件**:
- `panic_index_collector.py`
- `templates/panic_index.html`
- `app_new.py` (路由: `/panic-index`, `/api/panic-index/*`)

**数据库**:
- `panic_index.db`

**表结构**:
```sql
CREATE TABLE panic_records (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    panic_index REAL,
    wash_index REAL,
    created_at DATETIME
);
```

**PM2进程**: `panic-index-collector`

**API端点**:
- `GET /panic-index` - 页面
- `GET /api/panic-index/latest` - 最新数据
- `GET /api/panic-index/history` - 历史数据

**恢复优先级**: ⭐⭐⭐⭐⭐

---

### 4. 比价系统 💰
**文件**:
- `price_comparison.py`
- `templates/price_comparison.html`

**数据库表**:
- `crypto_data.db`: `price_comparison`

**功能**: 多交易所价格对比

---

### 5. 星星系统 ⭐
**文件**:
- `star_rating_collector.py`
- `templates/star_ratings.html`

**数据库表**:
- `crypto_data.db`: `star_ratings`

**PM2进程**: `star-rating-collector`

---

### 6. 币种池系统 🪙
**文件**:
- `coin_pool_manager.py`
- `templates/coin_pool.html`

**数据库表**:
- `crypto_data.db`: `coin_pool`, `coin_selections`

---

### 7. 实时市场原始数据 📊
**文件**:
- `market_data_collector.py`

**数据库**:
- `market_data.db`

**表**: `raw_market_data`

**PM2进程**: `market-data-collector`

---

### 8. 数据采集监控 📡
**文件**:
- `data_collection_monitor.py`

**功能**: 监控所有采集器状态

**PM2进程**: `collection-monitor`

---

### 9. 深度图得分 📈
**文件**:
- `depth_score_calculator.py`
- `templates/depth_scores.html`

**数据库表**:
- `crypto_data.db`: `depth_scores`

---

### 10. 深度图可视化 🎨
**文件**:
- `templates/depth_visualization.html`
- `app_new.py` (路由: `/depth-visual`)

**API**: `/api/depth/visual-data`

---

### 11. 平均分页面 📊
**文件**:
- `templates/average_scores.html`
- `app_new.py` (路由: `/average-scores`)

**数据库表**:
- `crypto_data.db`: `average_scores`

---

### 12. OKEx加密指数 🔐
**文件**:
- `okex_index_collector.py`

**数据库表**:
- `crypto_data.db`: `okex_index`

**PM2进程**: `okex-index-collector`

---

### 13. 位置系统 📍
**文件**:
- `position_tracker.py`
- `templates/positions.html`

**数据库表**:
- `crypto_data.db`: `positions`, `position_history`

**功能**: 跟踪交易位置和持仓

---

### 14. 支撑压力线系统 📉📈
**文件**:
- `support_resistance_collector.py`
- `support_snapshot_collector.py`
- `escape_stats_recorder.py`
- `templates/support_resistance.html`
- `templates/escape_stats_history.html`

**数据库**:
- `support_resistance.db`

**表结构**:
```sql
-- 支撑压力线数据
CREATE TABLE support_resistance_levels (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timeframe TEXT,
    support_level REAL,
    resistance_level REAL,
    timestamp DATETIME
);

-- 快照数据
CREATE TABLE support_resistance_snapshots (
    id INTEGER PRIMARY KEY,
    snapshot_time DATETIME,
    scenario_1_count INTEGER,
    scenario_2_count INTEGER,
    scenario_3_count INTEGER,
    scenario_4_count INTEGER,
    scenario_1_coins TEXT,
    scenario_2_coins TEXT,
    scenario_3_coins TEXT,
    scenario_4_coins TEXT,
    total_coins INTEGER
);

-- K线数据
CREATE TABLE okex_kline_ohlc (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timestamp DATETIME,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL
);

-- 每日基准价格
CREATE TABLE daily_baseline_prices (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    date TEXT,
    baseline_price REAL,
    created_at DATETIME
);
```

**另一个数据库**: `crypto_data.db`
```sql
-- 逃顶信号统计
CREATE TABLE escape_signal_stats (
    id INTEGER PRIMARY KEY,
    stat_time TEXT,
    signal_24h_count INTEGER,
    signal_2h_count INTEGER,
    created_at TIMESTAMP
);

-- 历史快照统计（旧表，仅供参考）
CREATE TABLE escape_snapshot_stats (
    id INTEGER PRIMARY KEY,
    stat_time TEXT,
    escape_24h_count INTEGER,
    escape_2h_count INTEGER,
    max_escape_24h INTEGER,
    max_escape_2h INTEGER,
    created_at TIMESTAMP
);
```

**PM2进程**:
- `support-resistance-collector` - 支撑压力线采集
- `support-snapshot-collector` - 快照采集
- `escape-stats-recorder` - 逃顶统计记录（已停用，由前端记录）

**页面路由**:
- `/support-resistance` - 主页面
- `/escape-stats-history` - 历史数据页面

**API端点**:
- `GET /api/support-resistance/latest` - 最新数据
- `GET /api/support-resistance/snapshots` - 快照数据
- `GET /api/support-resistance/escape-signal-stats` - 逃顶信号统计
- `GET /api/support-resistance/escape-stats-history` - 历史数据
- `POST /api/support-resistance/record-escape-signal-stats` - 记录信号数

**关键功能**:
1. 实时计算支撑/压力线
2. 4种场景监控（S1接近支撑1、S2接近支撑2、S3接近压力1、S4接近压力2）
3. 逃顶信号数统计（24小时/2小时）
4. 历史极值统计
5. 每分钟快照记录

**数据采集频率**:
- 支撑压力线: 每分钟
- 快照: 每分钟
- 信号统计: 前端每分钟上报

**恢复优先级**: ⭐⭐⭐⭐⭐

---

### 15. 决策交易信号系统 🎯
**文件**:
- `decision_signal_generator.py`
- `templates/decision_signals.html`

**数据库表**:
- `crypto_data.db`: `decision_signals`

**PM2进程**: `decision-signal-generator`

---

### 16. 决策K线指标系统 📊
**文件**:
- `kline_indicator_calculator.py`
- `templates/kline_indicators.html`

**数据库表**:
- `crypto_data.db`: `kline_indicators`

---

### 17. V1V2成交系统 💹
**文件**:
- `v1v2_transaction_monitor.py`
- `templates/v1v2_transactions.html`

**数据库表**:
- `crypto_data.db`: `v1_transactions`, `v2_transactions`

**PM2进程**: `v1v2-monitor`

---

### 18. 1分钟涨跌幅系统 📈📉
**文件**:
- `one_minute_change_monitor.py`
- `templates/one_minute_changes.html`

**数据库表**:
- `crypto_data.db`: `minute_changes`

**PM2进程**: `minute-change-monitor`

---

### 19. Google Drive监控系统 💾
**文件**:
- `gdrive_detector.py`

**数据库**:
- `gdrive_monitor.db`

**表结构**:
```sql
CREATE TABLE gdrive_files (
    id INTEGER PRIMARY KEY,
    file_id TEXT UNIQUE,
    file_name TEXT,
    file_size INTEGER,
    modified_time DATETIME,
    detected_time DATETIME
);
```

**PM2进程**: `gdrive-detector`

**配置文件**: `gdrive_config.json`

**恢复优先级**: ⭐⭐⭐

---

### 20. Telegram消息推送系统 📱
**文件**:
- `telegram_notifier.py`

**配置文件**: `telegram_config.json`

**PM2进程**: `telegram-notifier`

**功能**: 发送交易信号、警报到Telegram

**恢复优先级**: ⭐⭐⭐⭐

---

### 21. 资金监控系统 💰
**文件**:
- `fund_monitor.py`
- `templates/fund_monitoring.html`

**数据库表**:
- `crypto_data.db`: `fund_flow`, `balance_history`

---

### 22. 锚点系统 ⚓
**文件**:
- `anchor_maintenance.py`
- `anchor_profit_tracker.py`
- `templates/anchor_system.html`

**数据库表** (`crypto_data.db`):
```sql
-- 锚点记录
CREATE TABLE anchor_records (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    anchor_price REAL,
    current_price REAL,
    profit_rate REAL,
    status TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- 利润记录
CREATE TABLE anchor_profit_records (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    profit REAL,
    profit_rate REAL,
    trade_mode TEXT,
    timestamp DATETIME
);

-- 监控记录
CREATE TABLE anchor_monitors (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    monitor_type TEXT,
    value REAL,
    threshold REAL,
    created_at DATETIME
);

-- 告警记录
CREATE TABLE anchor_alerts (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    alert_type TEXT,
    message TEXT,
    severity TEXT,
    created_at DATETIME
);

-- 持仓记录
CREATE TABLE anchor_positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    position_size REAL,
    entry_price REAL,
    current_price REAL,
    unrealized_pnl REAL,
    trade_mode TEXT,
    created_at DATETIME
);

-- 警告记录
CREATE TABLE anchor_warnings (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    warning_type TEXT,
    message TEXT,
    trade_mode TEXT,
    created_at DATETIME
);
```

**PM2进程**:
- `anchor-maintenance` - 锚点维护
- `profit-extremes-tracker` - 利润极值跟踪

**API端点**:
- `GET /anchor-system` - 主页面
- `GET /api/anchor-system/status` - 系统状态
- `GET /api/anchor-system/records` - 锚点记录
- `GET /api/anchor-system/profit-records` - 利润记录
- `GET /api/anchor-system/monitors` - 监控数据
- `GET /api/anchor-system/alerts` - 告警信息
- `GET /api/anchor-system/current-positions` - 当前持仓
- `GET /api/anchor-system/warnings` - 警告信息

**配置文件**: `anchor_config.json`

**功能**:
1. 自动维护交易锚点
2. 实时监控利润变化
3. 记录历史极值
4. 多交易模式支持（模拟/实盘）
5. 风险告警

**恢复优先级**: ⭐⭐⭐⭐⭐

---

### 23. 自动交易系统 🤖
**文件**:
- `auto_trading_engine.py`
- `sub_account_opener.py`
- `sub_account_super_maintenance.py`
- `templates/auto_trading.html`

**数据库表** (`crypto_data.db`):
```sql
-- 交易记录
CREATE TABLE trading_orders (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    order_type TEXT,
    side TEXT,
    price REAL,
    quantity REAL,
    status TEXT,
    order_id TEXT,
    created_at DATETIME,
    filled_at DATETIME
);

-- 子账户记录
CREATE TABLE sub_accounts (
    id INTEGER PRIMARY KEY,
    account_name TEXT UNIQUE,
    api_key TEXT,
    secret_key TEXT,
    passphrase TEXT,
    status TEXT,
    created_at DATETIME
);

-- 持仓记录
CREATE TABLE current_positions (
    id INTEGER PRIMARY KEY,
    account_name TEXT,
    symbol TEXT,
    position_side TEXT,
    quantity REAL,
    entry_price REAL,
    current_price REAL,
    unrealized_pnl REAL,
    leverage INTEGER,
    updated_at DATETIME
);
```

**PM2进程**:
- `auto-trading-engine` (如果有)
- `sub-account-opener` - 子账户开仓
- `sub-account-super-maintenance` - 子账户超级维护

**API端点**:
- `GET /auto-trading` - 主页面
- `POST /api/auto-trading/order` - 下单
- `GET /api/auto-trading/positions` - 持仓查询
- `POST /api/sub-account/open-position` - 开仓
- `POST /api/sub-account/close-position` - 平仓
- `POST /api/sub-account/close-position-percent` - 按比例平仓
- `POST /api/sub-account/close-position-to-amount` - 平仓到指定金额
- `GET /api/sub-account/positions` - 子账户持仓

**配置文件**:
- `sub_account_config.json` - 子账户配置
- `trading_config.json` - 交易配置

**OKX API配置**:
```json
{
  "api_key": "YOUR_API_KEY",
  "secret_key": "YOUR_SECRET_KEY",
  "passphrase": "YOUR_PASSPHRASE",
  "base_url": "https://www.okx.com"
}
```

**功能**:
1. 自动下单执行
2. 多子账户管理
3. 持仓自动维护
4. 风险控制
5. 智能平仓（按比例/到指定金额）

**恢复优先级**: ⭐⭐⭐⭐⭐

---

## 💾 数据库架构

### 主数据库: crypto_data.db
**位置**: `/home/user/webapp/databases/crypto_data.db`

**核心表**:
```sql
-- 逃顶信号统计（新）
escape_signal_stats (
    id, stat_time, signal_24h_count, signal_2h_count, created_at
)

-- 锚点系统
anchor_records, anchor_profit_records, anchor_monitors, 
anchor_alerts, anchor_positions, anchor_warnings

-- 自动交易
trading_orders, sub_accounts, current_positions

-- 其他系统
historical_data, trade_signals, star_ratings, coin_pool, 
depth_scores, average_scores, okex_index, positions, 
decision_signals, kline_indicators, v1_transactions, 
v2_transactions, minute_changes, fund_flow, balance_history
```

### 支撑压力线数据库: support_resistance.db
**位置**: `/home/user/webapp/support_resistance.db`

**表**:
```sql
support_resistance_levels
support_resistance_snapshots
okex_kline_ohlc
daily_baseline_prices
```

### 其他数据库:
- `gdrive_monitor.db` - Google Drive监控
- `panic_index.db` - 恐慌指数
- `market_data.db` - 市场原始数据

---

## 🔧 恢复步骤

### 阶段1: 环境准备

```bash
# 1. 更新系统
sudo apt update

# 2. 安装Python依赖
cd /home/user/webapp
pip3 install -r requirements.txt

# 3. 安装PM2（如果未安装）
npm install -g pm2

# 4. 检查Python版本
python3 --version  # 应该是 3.8+
```

### 阶段2: 恢复代码

```bash
# 1. 克隆仓库（如果是新环境）
cd /home/user
git clone https://github.com/jamesyidc/666612.git webapp
cd webapp

# 2. 或者从备份恢复
# 如果有tar.gz备份：
tar -xzf webapp_source.tar.gz -C /home/user/webapp

# 3. 设置权限
chmod +x /home/user/webapp/*.py
```

### 阶段3: 恢复数据库

```bash
# 1. 创建数据库目录
mkdir -p /home/user/webapp/databases

# 2. 从SQL dump恢复（推荐）
cd /home/user/webapp/databases
sqlite3 crypto_data.db < crypto_data_dump.sql
sqlite3 ../support_resistance.db < support_resistance_dump.sql

# 3. 或从.db文件直接复制
cp /backup/databases/*.db /home/user/webapp/databases/
cp /backup/databases/support_resistance.db /home/user/webapp/

# 4. 验证数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_snapshots;"
```

### 阶段4: 配置文件恢复

```bash
# 1. 恢复配置文件
cp /backup/config/*.json /home/user/webapp/
cp /backup/config/.env /home/user/webapp/

# 2. 关键配置文件检查清单：
# - sub_account_config.json
# - anchor_config.json
# - telegram_config.json
# - gdrive_config.json
# - trading_config.json

# 3. 验证配置
cat /home/user/webapp/sub_account_config.json
```

### 阶段5: 启动PM2进程

```bash
cd /home/user/webapp

# 1. 启动Flask主应用
pm2 start app_new.py --name flask-app --interpreter python3

# 2. 启动支撑压力线系统
pm2 start support_resistance_collector.py --name support-resistance-collector --interpreter python3
pm2 start support_snapshot_collector.py --name support-snapshot-collector --interpreter python3

# 3. 启动锚点系统
pm2 start anchor_maintenance.py --name anchor-maintenance --interpreter python3
pm2 start anchor_profit_tracker.py --name profit-extremes-tracker --interpreter python3

# 4. 启动自动交易系统
pm2 start sub_account_opener.py --name sub-account-opener --interpreter python3
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance --interpreter python3

# 5. 启动监控系统
pm2 start gdrive_detector.py --name gdrive-detector --interpreter python3
pm2 start telegram_notifier.py --name telegram-notifier --interpreter python3

# 6. 查看进程状态
pm2 list

# 7. 保存PM2配置
pm2 save

# 8. 设置开机自启
pm2 startup
```

### 阶段6: 验证系统

```bash
# 1. 检查Flask应用
curl http://localhost:5000/

# 2. 检查支撑压力线系统
curl http://localhost:5000/support-resistance

# 3. 检查API
curl http://localhost:5000/api/support-resistance/latest
curl http://localhost:5000/api/support-resistance/escape-signal-stats

# 4. 检查锚点系统
curl http://localhost:5000/anchor-system
curl http://localhost:5000/api/anchor-system/status

# 5. 查看PM2日志
pm2 logs flask-app --lines 50
pm2 logs support-resistance-collector --lines 20

# 6. 检查数据库连接
python3 << EOF
import sqlite3
conn = sqlite3.connect('databases/crypto_data.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM escape_signal_stats")
print(f"逃顶信号记录数: {cursor.fetchone()[0]}")
conn.close()
EOF
```

---

## ⚙️ PM2进程配置

### 完整进程列表

```bash
# 核心进程（必须启动）
pm2 start app_new.py --name flask-app --interpreter python3

# 支撑压力线系统（重点）
pm2 start support_resistance_collector.py --name support-resistance-collector --interpreter python3
pm2 start support_snapshot_collector.py --name support-snapshot-collector --interpreter python3

# 锚点系统（重点）
pm2 start anchor_maintenance.py --name anchor-maintenance --interpreter python3
pm2 start anchor_profit_tracker.py --name profit-extremes-tracker --interpreter python3

# 自动交易系统（重点）
pm2 start sub_account_opener.py --name sub-account-opener --interpreter python3
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance --interpreter python3

# 监控系统
pm2 start gdrive_detector.py --name gdrive-detector --interpreter python3
pm2 start telegram_notifier.py --name telegram-notifier --interpreter python3

# 其他采集器（按需启动）
pm2 start panic_index_collector.py --name panic-index-collector --interpreter python3
pm2 start star_rating_collector.py --name star-rating-collector --interpreter python3
pm2 start market_data_collector.py --name market-data-collector --interpreter python3
# ... 更多采集器
```

### PM2常用命令

```bash
# 查看所有进程
pm2 list

# 查看单个进程详情
pm2 show flask-app

# 查看日志
pm2 logs                      # 所有进程
pm2 logs flask-app            # 单个进程
pm2 logs --lines 100          # 最近100行

# 重启进程
pm2 restart flask-app
pm2 restart all

# 停止进程
pm2 stop flask-app
pm2 stop all

# 删除进程
pm2 delete flask-app

# 保存配置
pm2 save

# 从配置恢复
pm2 resurrect
```

---

## 🎯 重点系统详解

### 1. SAR斜率系统

**说明**: 此系统未在当前代码中找到独立模块，可能已集成到其他系统中

**相关文件**: 需要进一步确认

---

### 2. 历史数据查询系统 ⭐⭐⭐

**核心文件**:
- `app_new.py` - Flask路由

**API端点**:
```python
@app.route('/api/history/kline')
@app.route('/api/history/trades')
```

**数据表**: `historical_data`, `kline_data`

**恢复检查**:
```bash
# 检查API
curl http://localhost:5000/api/history/kline?symbol=BTC-USDT

# 检查数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM historical_data;"
```

---

### 3. 恐慌清洗指数系统 ⭐⭐⭐⭐⭐

**核心文件**:
- `panic_index_collector.py` - 数据采集
- `templates/panic_index.html` - 前端页面
- `panic_index.db` - 专用数据库

**数据表结构**:
```sql
CREATE TABLE panic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    panic_index REAL NOT NULL,
    wash_index REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**PM2进程**:
```bash
pm2 start panic_index_collector.py --name panic-index-collector --interpreter python3
```

**页面访问**: `http://localhost:5000/panic-index`

**API端点**:
- `GET /api/panic-index/latest` - 最新指数
- `GET /api/panic-index/history?hours=24` - 历史数据

**恢复步骤**:
1. 确保 `panic_index.db` 存在
2. 启动采集器进程
3. 验证页面可访问
4. 检查数据采集是否正常

**验证命令**:
```bash
# 检查数据库
sqlite3 databases/panic_index.db "SELECT * FROM panic_records ORDER BY timestamp DESC LIMIT 5;"

# 检查进程
pm2 logs panic-index-collector --lines 20

# 测试API
curl http://localhost:5000/api/panic-index/latest
```

---

### 4. 支撑压力线系统 ⭐⭐⭐⭐⭐

**核心文件**:
- `support_resistance_collector.py` - 主采集器
- `support_snapshot_collector.py` - 快照采集器
- `templates/support_resistance.html` - 主页面
- `templates/escape_stats_history.html` - 历史数据页面
- `support_resistance.db` - 专用数据库
- `crypto_data.db` - 信号统计表

**数据表映射**:

**support_resistance.db**:
```sql
-- 支撑压力线数据
support_resistance_levels (
    id, symbol, timeframe, support_level, resistance_level, timestamp
)

-- 快照数据（每分钟）
support_resistance_snapshots (
    id, snapshot_time, 
    scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
    scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
    total_coins
)

-- K线OHLC数据
okex_kline_ohlc (
    id, symbol, timestamp, open, high, low, close, volume
)

-- 每日基准价格
daily_baseline_prices (
    id, symbol, date, baseline_price, created_at
)
```

**crypto_data.db**:
```sql
-- 逃顶信号统计（前端每分钟记录）
escape_signal_stats (
    id, stat_time, signal_24h_count, signal_2h_count, created_at
)
```

**PM2进程**:
```bash
pm2 start support_resistance_collector.py --name support-resistance-collector --interpreter python3
pm2 start support_snapshot_collector.py --name support-snapshot-collector --interpreter python3
```

**页面路由**:
- `/support-resistance` - 主页面
- `/escape-stats-history` - 历史数据页面

**API端点**:
```
GET  /api/support-resistance/latest
GET  /api/support-resistance/snapshots?date=2026-01-02
GET  /api/support-resistance/snapshots?all=true
GET  /api/support-resistance/escape-signal-stats
GET  /api/support-resistance/escape-stats-history?hours=24&limit=1000
POST /api/support-resistance/record-escape-signal-stats
```

**关键功能**:
1. **支撑压力线计算**: 基于48小时和7天的价格数据
2. **4种场景监控**:
   - S1: 接近支撑线1（7天最低）
   - S2: 接近支撑线2（48小时最低）
   - S3: 接近压力线1（7天最高）
   - S4: 接近压力线2（48小时最高）
3. **逃顶信号**: S3 + S4 ≥ 5 触发
4. **前端实时记录**: 每分钟记录24h和2h的信号数
5. **历史极值**: 自动计算并显示历史最大值

**数据流**:
```
OKX API → support_resistance_collector → support_resistance.db
                                       ↓
support_snapshot_collector → 每分钟快照 → support_resistance.db
                                       ↓
前端页面 → 计算信号数 → 每分钟上报 → crypto_data.db (escape_signal_stats)
```

**恢复步骤**:
1. 恢复两个数据库文件
2. 启动两个采集器进程
3. 访问主页面，确保前端正常加载
4. 等待1分钟，检查是否有新的信号记录

**验证命令**:
```bash
# 1. 检查支撑压力线数据
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_snapshots;"

# 2. 检查逃顶信号统计
sqlite3 databases/crypto_data.db "SELECT * FROM escape_signal_stats ORDER BY stat_time DESC LIMIT 5;"

# 3. 检查进程状态
pm2 list | grep support

# 4. 查看采集器日志
pm2 logs support-resistance-collector --lines 20

# 5. 测试API
curl http://localhost:5000/api/support-resistance/latest | python3 -m json.tool
curl http://localhost:5000/api/support-resistance/escape-signal-stats | python3 -m json.tool

# 6. 测试前端记录功能（需要访问页面）
# 打开浏览器访问: http://localhost:5000/support-resistance
# 等待1分钟后检查：
sqlite3 databases/crypto_data.db "SELECT * FROM escape_signal_stats ORDER BY stat_time DESC LIMIT 3;"
```

**重要提示**:
- 前端信号记录需要有用户访问页面才会工作
- 如果长时间无人访问，数据库不会有新记录
- 24h和2h信号数是基于前端图表上的实际标记点计算的
- 历史最大值会随着新数据自动更新

---

### 5. 锚点系统 ⭐⭐⭐⭐⭐

**核心文件**:
- `anchor_maintenance.py` - 锚点维护
- `anchor_profit_tracker.py` - 利润跟踪
- `templates/anchor_system.html` - 前端页面
- `anchor_config.json` - 配置文件

**数据表** (`crypto_data.db`):
```sql
anchor_records          -- 锚点记录
anchor_profit_records   -- 利润记录
anchor_monitors         -- 监控数据
anchor_alerts           -- 告警信息
anchor_positions        -- 持仓信息
anchor_warnings         -- 警告信息
```

**PM2进程**:
```bash
pm2 start anchor_maintenance.py --name anchor-maintenance --interpreter python3
pm2 start anchor_profit_tracker.py --name profit-extremes-tracker --interpreter python3
```

**页面访问**: `http://localhost:5000/anchor-system`

**API端点**:
```
GET /api/anchor-system/status
GET /api/anchor-system/records
GET /api/anchor-system/profit-records?trade_mode=real
GET /api/anchor-system/monitors?limit=50
GET /api/anchor-system/alerts?limit=10
GET /api/anchor-system/current-positions?trade_mode=real
GET /api/anchor-system/warnings?trade_mode=real
```

**配置文件** (`anchor_config.json`):
```json
{
  "update_interval": 60,
  "profit_thresholds": {
    "warning": 0.05,
    "alert": 0.10
  },
  "trade_modes": ["real", "simulate"]
}
```

**恢复步骤**:
1. 确保 `crypto_data.db` 包含所有锚点相关表
2. 恢复 `anchor_config.json`
3. 启动两个PM2进程
4. 验证页面和API

**验证命令**:
```bash
# 检查数据表
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM anchor_records;"
sqlite3 databases/crypto_data.db "SELECT * FROM anchor_profit_records ORDER BY timestamp DESC LIMIT 5;"

# 检查进程
pm2 logs anchor-maintenance --lines 20

# 测试API
curl http://localhost:5000/api/anchor-system/status | python3 -m json.tool
```

---

### 6. 自动交易系统 ⭐⭐⭐⭐⭐

**核心文件**:
- `sub_account_opener.py` - 子账户开仓
- `sub_account_super_maintenance.py` - 超级维护
- `templates/auto_trading.html` - 前端页面
- `sub_account_config.json` - 子账户配置
- `trading_config.json` - 交易配置

**数据表** (`crypto_data.db`):
```sql
trading_orders      -- 交易订单
sub_accounts        -- 子账户信息
current_positions   -- 当前持仓
```

**PM2进程**:
```bash
pm2 start sub_account_opener.py --name sub-account-opener --interpreter python3
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance --interpreter python3
```

**API端点**:
```
POST /api/auto-trading/order
GET  /api/auto-trading/positions
POST /api/sub-account/open-position
POST /api/sub-account/close-position
POST /api/sub-account/close-position-percent
POST /api/sub-account/close-position-to-amount
GET  /api/sub-account/positions
GET  /api/sub-account/sub-account-positions
```

**配置文件** (`sub_account_config.json`):
```json
{
  "sub_accounts": [
    {
      "account_name": "Wu666666",
      "api_key": "YOUR_API_KEY",
      "secret_key": "YOUR_SECRET_KEY",
      "passphrase": "YOUR_PASSPHRASE"
    }
  ]
}
```

**OKX API配置**:
- API Key: 需要交易权限
- Secret Key: 加密签名
- Passphrase: API密码
- Base URL: `https://www.okx.com`

**关键功能**:
1. **智能开仓**: 自动分析市场并开仓
2. **智能平仓**:
   - 按比例平仓（20%, 33%, 50%, 66%, 75%）
   - 平仓到指定保证金金额
3. **持仓监控**: 实时跟踪保证金、收益率
4. **风险控制**: 自动止损止盈
5. **多账户管理**: 支持多个子账户

**平仓逻辑**:
```python
# 按比例平仓
close_size = current_position * (percent / 100)

# 平仓到指定金额
需要平仓比例 = (当前保证金 - 目标保证金) / 当前保证金
close_size = current_position * 需要平仓比例

# 优先选择逐仓持仓（有margin字段）
```

**恢复步骤**:
1. 恢复 `sub_account_config.json`（**重要！包含API密钥**）
2. 恢复 `trading_config.json`
3. 确保数据库表存在
4. 启动PM2进程
5. 验证API连接

**验证命令**:
```bash
# 检查配置
cat sub_account_config.json

# 检查持仓
curl -X GET http://localhost:5000/api/sub-account/positions | python3 -m json.tool

# 测试查询
curl -X GET "http://localhost:5000/api/sub-account/sub-account-positions" | python3 -m json.tool

# 检查进程日志
pm2 logs sub-account-opener --lines 30
```

**安全注意**:
- ⚠️ **API密钥必须妥善保管**
- ⚠️ **不要提交到Git仓库**
- ⚠️ **定期更换API密钥**
- ⚠️ **使用IP白名单**

---

## 📝 重要配置文件清单

### 必须恢复的配置文件

1. **sub_account_config.json** ⭐⭐⭐⭐⭐
   - 包含所有子账户的API密钥
   - 格式: `{"sub_accounts": [{"account_name", "api_key", "secret_key", "passphrase"}]}`

2. **anchor_config.json** ⭐⭐⭐⭐
   - 锚点系统配置
   - 更新间隔、阈值等

3. **telegram_config.json** ⭐⭐⭐
   - Telegram Bot Token
   - Chat ID

4. **gdrive_config.json** ⭐⭐⭐
   - Google Drive API凭证
   - 监控文件夹ID

5. **trading_config.json** ⭐⭐⭐⭐
   - 交易参数
   - 风险控制参数

6. **requirements.txt** ⭐⭐⭐⭐⭐
   - Python依赖包列表

---

## 🔍 故障排查

### 常见问题

**问题1: 数据库表不存在**
```bash
# 解决方法：从SQL dump重新创建
sqlite3 databases/crypto_data.db < backup/crypto_data_dump.sql
```

**问题2: PM2进程频繁重启**
```bash
# 查看错误日志
pm2 logs <process-name> --err --lines 50

# 常见原因：
# - 数据库文件路径错误
# - 配置文件缺失
# - API密钥无效
# - 端口被占用
```

**问题3: API返回500错误**
```bash
# 检查Flask日志
pm2 logs flask-app --lines 100

# 检查数据库连接
python3 -c "import sqlite3; conn = sqlite3.connect('databases/crypto_data.db'); print('OK')"
```

**问题4: 前端页面空白**
```bash
# 检查静态文件
ls -la /home/user/webapp/static/
ls -la /home/user/webapp/templates/

# 检查Flask路由
curl -I http://localhost:5000/support-resistance
```

**问题5: 数据不更新**
```bash
# 检查采集器进程
pm2 list | grep collector

# 查看采集器日志
pm2 logs support-resistance-collector --lines 50

# 检查最新数据
sqlite3 support_resistance.db "SELECT * FROM support_resistance_snapshots ORDER BY snapshot_time DESC LIMIT 1;"
```

---

## ✅ 恢复验证清单

### 核心系统验证

- [ ] Flask应用启动成功 (http://localhost:5000/)
- [ ] 支撑压力线系统正常
  - [ ] 页面可访问
  - [ ] 数据采集正常
  - [ ] 信号统计正常
- [ ] 锚点系统正常
  - [ ] 页面可访问
  - [ ] 数据更新正常
  - [ ] API响应正常
- [ ] 自动交易系统正常
  - [ ] 子账户配置正确
  - [ ] 持仓查询正常
  - [ ] 平仓功能正常
- [ ] 所有PM2进程在线
- [ ] 所有数据库文件存在且可访问
- [ ] 所有配置文件已恢复

### 数据库验证

```bash
# 验证所有关键数据库
for db in crypto_data.db support_resistance.db panic_index.db gdrive_monitor.db; do
    echo "检查 $db..."
    sqlite3 "databases/$db" "SELECT name FROM sqlite_master WHERE type='table';" 2>&1
done

# 检查support_resistance.db（在webapp根目录）
sqlite3 support_resistance.db "SELECT name FROM sqlite_master WHERE type='table';"
```

### API验证

```bash
# 测试所有关键API
curl http://localhost:5000/api/support-resistance/latest
curl http://localhost:5000/api/support-resistance/escape-signal-stats
curl http://localhost:5000/api/anchor-system/status
curl http://localhost:5000/api/sub-account/sub-account-positions
```

---

## 📚 附录

### A. Python依赖包

主要依赖（requirements.txt）:
```
Flask==2.3.0
SQLite3 (内置)
requests==2.28.0
python-dotenv==1.0.0
pytz==2023.3
ccxt==4.0.0  # OKX交易
pandas==2.0.0
numpy==1.24.0
```

### B. 目录结构

```
/home/user/webapp/
├── app_new.py                    # Flask主应用
├── support_resistance_collector.py
├── support_snapshot_collector.py
├── anchor_maintenance.py
├── anchor_profit_tracker.py
├── sub_account_opener.py
├── sub_account_super_maintenance.py
├── gdrive_detector.py
├── telegram_notifier.py
├── panic_index_collector.py
├── ... (其他脚本)
├── templates/                    # HTML模板
│   ├── support_resistance.html
│   ├── escape_stats_history.html
│   ├── anchor_system.html
│   ├── auto_trading.html
│   └── ...
├── static/                       # 静态资源
├── databases/                    # 数据库目录
│   ├── crypto_data.db
│   ├── panic_index.db
│   ├── gdrive_monitor.db
│   └── market_data.db
├── support_resistance.db         # 支撑压力线数据库（根目录）
├── sub_account_config.json       # 配置文件
├── anchor_config.json
├── telegram_config.json
├── trading_config.json
├── requirements.txt
├── .env
├── .git/
└── SYSTEM_RECOVERY_GUIDE.md     # 本文档
```

### C. Git仓库信息

**仓库**: https://github.com/jamesyidc/666612.git  
**主分支**: main  
**最新提交**: 请查看 `git log -1`

### D. 联系信息

如遇恢复问题，请参考：
- 本文档的故障排查部分
- PM2日志: `pm2 logs <process-name>`
- Flask日志: `pm2 logs flask-app`

---

## 🎉 结语

本文档提供了完整的系统恢复指南，涵盖所有23个子系统。重点关注以下6个核心系统：

1. ⭐ SAR斜率系统（待确认）
2. ⭐⭐⭐ 历史数据查询系统
3. ⭐⭐⭐⭐⭐ 恐慌清洗指数系统
4. ⭐⭐⭐⭐⭐ 支撑压力线系统
5. ⭐⭐⭐⭐⭐ 锚点系统
6. ⭐⭐⭐⭐⭐ 自动交易系统

按照本文档的步骤操作，可以实现**1:1完美还原**，确保重新部署后系统立即可用。

**最后更新**: 2026-01-02  
**文档版本**: v2.0
