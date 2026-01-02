# 完整系统备份与恢复指南

> **最后更新**: 2026-01-02  
> **版本**: v2.0  
> **维护者**: System Admin

---

## 📚 目录

1. [快速恢复（5分钟）](#快速恢复5分钟)
2. [完整系统架构](#完整系统架构)
3. [数据库完整结构](#数据库完整结构)
4. [PM2进程配置](#pm2进程配置)
5. [配置文件清单](#配置文件清单)
6. [详细恢复步骤](#详细恢复步骤)
7. [验证清单](#验证清单)
8. [故障排查](#故障排查)

---

## ⚡ 快速恢复（5分钟）

### 1. 克隆仓库
```bash
git clone https://github.com/jamesyidc/666612.git webapp
cd webapp
```

### 2. 安装依赖
```bash
pip3 install -r requirements.txt
```

### 3. 恢复数据库
```bash
# 从备份恢复（如果有备份）
cp /backup/crypto_data.db databases/crypto_data.db
cp /backup/support_resistance.db support_resistance.db
cp /backup/panic_index.db databases/panic_index.db
cp /backup/gdrive_monitor.db databases/gdrive_monitor.db

# 或者从SQL导出恢复
sqlite3 databases/crypto_data.db < crypto_data_dump.sql
sqlite3 support_resistance.db < support_resistance_dump.sql
```

### 4. 恢复配置文件（⚠️ 必须）
```bash
# 这些文件包含敏感信息，不在git中，必须手动恢复
cp /backup/sub_account_config.json .
cp /backup/anchor_config.json .
cp /backup/telegram_config.json .
cp /backup/gdrive_config.json .
```

### 5. 启动核心服务
```bash
# 启动所有PM2进程
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_resistance_snapshot_collector.py --name support-snapshot-collector
pm2 start anchor_maintenance_realtime_daemon.py --name anchor-maintenance
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance
pm2 start gdrive_final_detector.py --name gdrive-detector
pm2 start telegram_signal_system.py --name telegram-notifier

# 启动Flask应用
pm2 start --name flask-app --interpreter bash -x -- -c "cd /home/user/webapp && python3 app_new.py"

# 保存PM2配置
pm2 save
```

### 6. 验证系统
```bash
# 检查PM2进程
pm2 status

# 访问主页面
curl http://localhost:5000/support-resistance

# 检查API
curl http://localhost:5000/api/support-resistance/escape-signal-stats
```

---

## 🏗️ 完整系统架构

### 系统组成（23个子系统）

#### ⭐ 核心系统（必须恢复）

| # | 系统名称 | 脚本文件 | PM2进程名 | 数据库 | 配置文件 | 端口 |
|---|---------|---------|-----------|--------|---------|------|
| 1 | **支撑压力线系统** | `support_resistance_collector.py` | `support-resistance-collector` | `support_resistance.db`, `crypto_data.db` | - | - |
| 2 | **支撑压力线快照系统** | `support_resistance_snapshot_collector.py` | `support-snapshot-collector` | `support_resistance.db`, `crypto_data.db` | - | - |
| 3 | **锚点系统** | `anchor_maintenance_realtime_daemon.py` | `anchor-maintenance` | `crypto_data.db` | `anchor_config.json` | - |
| 4 | **锚点利润追踪** | `start_profit_extremes_tracker.sh` | `profit-extremes-tracker` | `crypto_data.db` | `anchor_config.json` | - |
| 5 | **自动交易系统（开单）** | `sub_account_opener_daemon.py` | `sub-account-opener` | `crypto_data.db` | `sub_account_config.json` | - |
| 6 | **自动交易系统（维护）** | `sub_account_super_maintenance.py` | `sub-account-super-maintenance` | `crypto_data.db` | `sub_account_config.json` | - |
| 7 | **Flask Web应用** | `app_new.py` | `flask-app` | 所有数据库 | 所有配置 | 5000 |

#### 🔧 辅助系统

| # | 系统名称 | 脚本文件 | PM2进程名 | 数据库 | 配置文件 |
|---|---------|---------|-----------|--------|---------|
| 8 | Google Drive监控 | `gdrive_final_detector.py` | `gdrive-detector` | `gdrive_monitor.db` | `gdrive_config.json` |
| 9 | Telegram通知 | `telegram_signal_system.py` | `telegram-notifier` | - | `telegram_config.json` |
| 10 | 逃顶信号记录器 | `escape_stats_recorder.py` | `escape-stats-recorder` | `crypto_data.db` | - |

#### 📊 数据系统（通过Web访问）

| # | 系统名称 | 路由路径 | 数据库表 | 说明 |
|---|---------|---------|---------|------|
| 11 | 历史数据查询 | `/api/history/*` | 多表 | 历史K线、价格查询 |
| 12 | 恐慌清洗指数 | `/panic-index` | `panic_index.db` | 恐慌指数计算与展示 |
| 13 | 比价系统 | `/price-compare` | `market_data.db` | 跨交易所价格对比 |
| 14 | 星星系统 | `/star-rating` | `crypto_data.db` | 币种评级系统 |
| 15 | 币种池 | `/coin-pool` | `crypto_data.db` | 币种筛选与管理 |
| 16 | 实时市场数据 | `/market-data` | `market_data.db` | 实时行情展示 |
| 17 | 数据采集监控 | `/collector-status` | - | 采集器状态监控 |
| 18 | 深度图得分 | `/depth-score` | `crypto_data.db` | 深度图分析 |
| 19 | 深度图可视化 | `/depth-chart` | `crypto_data.db` | 深度图展示 |
| 20 | 平均分页面 | `/average-score` | `crypto_data.db` | 综合评分 |
| 21 | OKEx加密指数 | `/okex-indicators` | `crypto_data.db` | OKEx技术指标 |
| 22 | 位置系统 | `/position-system` | `crypto_data.db` | 持仓管理 |
| 23 | 决策交易信号 | `/decision-signals` | `crypto_data.db` | 智能决策信号 |
| 24 | K线指标系统 | `/kline-indicators` | `crypto_data.db` | K线技术指标 |
| 25 | V1V2成交系统 | `/v1v2-volume` | `market_data.db` | 成交量分析 |
| 26 | 1分钟涨跌幅 | `/minute-changes` | `market_data.db` | 短期涨跌分析 |
| 27 | 资金监控 | `/fund-monitor` | `crypto_data.db` | 资金流向监控 |

---

## 💾 数据库完整结构

### 1. crypto_data.db（主数据库）
**位置**: `/home/user/webapp/databases/crypto_data.db`

#### 核心表（⭐ 必须备份）

##### escape_signal_stats（逃顶信号统计）
```sql
CREATE TABLE escape_signal_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_time TEXT NOT NULL,           -- 统计时间 (北京时间)
    signal_24h_count INTEGER NOT NULL, -- 24小时逃顶信号数
    signal_2h_count INTEGER NOT NULL,  -- 2小时逃顶信号数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_escape_signal_stat_time ON escape_signal_stats(stat_time);
```
- **数据来源**: 前端每分钟计算 `sellSignals.length` 和 `sellSignals2h.length`
- **记录频率**: 每分钟一次
- **当前数据**: 24h=251, 2h=2（示例）
- **历史最大值**: 24h=275, 2h=18（示例）

##### anchor_records（锚点记录）
```sql
CREATE TABLE anchor_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,              -- 币种符号
    anchor_price REAL NOT NULL,        -- 锚点价格
    anchor_time TIMESTAMP NOT NULL,    -- 锚点时间
    anchor_type TEXT NOT NULL,         -- 锚点类型 (high/low)
    is_active INTEGER DEFAULT 1,       -- 是否激活
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### anchor_profit_records（锚点利润记录）
```sql
CREATE TABLE anchor_profit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id INTEGER NOT NULL,        -- 锚点ID
    symbol TEXT NOT NULL,              -- 币种符号
    profit_percent REAL NOT NULL,      -- 利润百分比
    current_price REAL NOT NULL,       -- 当前价格
    check_time TIMESTAMP NOT NULL,     -- 检查时间
    is_max_profit INTEGER DEFAULT 0,   -- 是否最大利润
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anchor_id) REFERENCES anchor_records(id)
);
```

##### trading_orders（交易订单）
```sql
CREATE TABLE trading_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_account TEXT NOT NULL,         -- 子账户名
    symbol TEXT NOT NULL,              -- 币种符号
    order_id TEXT UNIQUE NOT NULL,     -- 订单ID
    order_type TEXT NOT NULL,          -- 订单类型 (limit/market)
    side TEXT NOT NULL,                -- 买卖方向 (buy/sell)
    price REAL,                        -- 订单价格
    quantity REAL NOT NULL,            -- 订单数量
    filled_quantity REAL DEFAULT 0,    -- 已成交数量
    status TEXT NOT NULL,              -- 订单状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### sub_accounts（子账户配置）
```sql
CREATE TABLE sub_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT UNIQUE NOT NULL, -- 子账户名
    api_key TEXT NOT NULL,             -- API Key
    secret_key TEXT NOT NULL,          -- Secret Key
    passphrase TEXT,                   -- Passphrase
    is_active INTEGER DEFAULT 1,       -- 是否激活
    max_position_size REAL,            -- 最大持仓
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### current_positions（当前持仓）
```sql
CREATE TABLE current_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sub_account TEXT NOT NULL,         -- 子账户名
    symbol TEXT NOT NULL,              -- 币种符号
    quantity REAL NOT NULL,            -- 持仓数量
    entry_price REAL NOT NULL,         -- 开仓价格
    current_value REAL,                -- 当前价值
    unrealized_pnl REAL,              -- 未实现盈亏
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sub_account, symbol)
);
```

#### 历史表（可选备份）

##### escape_snapshot_stats（旧的快照统计，已废弃）
```sql
-- 这个表由旧脚本 escape_stats_recorder.py 写入
-- 新系统不再使用，可以删除
```

##### support_resistance_snapshots（支撑压力快照）
```sql
CREATE TABLE support_resistance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    s1_price REAL, s1_count INTEGER, s1_status INTEGER,
    s2_price REAL, s2_count INTEGER, s2_status INTEGER,
    s3_price REAL, s3_count INTEGER, s3_status INTEGER,
    s4_price REAL, s4_count INTEGER, s4_status INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_snapshot_time ON support_resistance_snapshots(snapshot_time);
CREATE INDEX idx_snapshot_symbol ON support_resistance_snapshots(symbol);
```

##### daily_baseline_prices（每日基准价格）
```sql
CREATE TABLE daily_baseline_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    baseline_price REAL NOT NULL,
    volume_24h REAL,
    price_change_24h REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);
```

##### okex_kline_ohlc（OKEx K线数据）
```sql
CREATE TABLE okex_kline_ohlc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp)
);
```

---

### 2. support_resistance.db（支撑压力数据库）
**位置**: `/home/user/webapp/support_resistance.db`（注意：在根目录，不在databases/）

#### support_resistance_levels（支撑压力位）
```sql
CREATE TABLE support_resistance_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    price_level REAL NOT NULL,
    level_type TEXT NOT NULL,          -- 'support' or 'resistance'
    strength INTEGER NOT NULL,         -- 强度 (1-5)
    test_count INTEGER DEFAULT 1,      -- 测试次数
    last_test_time TIMESTAMP,          -- 最后测试时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sr_symbol ON support_resistance_levels(symbol);
CREATE INDEX idx_sr_price ON support_resistance_levels(price_level);
```
- **记录数**: 294,799 条
- **核心字段**: symbol, price_level, level_type, strength
- **用途**: 存储所有币种的支撑压力位

---

### 3. panic_index.db（恐慌指数数据库）
**位置**: `/home/user/webapp/databases/panic_index.db`

```sql
CREATE TABLE panic_index_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    panic_score REAL NOT NULL,         -- 恐慌得分
    cleanup_score REAL NOT NULL,       -- 清洗得分
    volume_spike REAL,                 -- 成交量异常
    price_drop REAL,                   -- 价格跌幅
    depth_imbalance REAL,              -- 深度失衡
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 4. gdrive_monitor.db（Google Drive监控数据库）
**位置**: `/home/user/webapp/databases/gdrive_monitor.db`

```sql
CREATE TABLE gdrive_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    modified_time TIMESTAMP,
    detected_time TIMESTAMP NOT NULL,
    is_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 5. market_data.db（市场数据数据库）
**位置**: `/home/user/webapp/databases/market_data.db`

```sql
-- 实时行情数据
CREATE TABLE market_ticker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    last_price REAL NOT NULL,
    volume_24h REAL,
    price_change_24h REAL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 跨交易所价差
CREATE TABLE price_comparison (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    exchange1 TEXT NOT NULL,
    exchange2 TEXT NOT NULL,
    price1 REAL NOT NULL,
    price2 REAL NOT NULL,
    price_diff_percent REAL NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 PM2进程配置

### 完整进程列表

详细配置见 `PM2_PROCESSES.json` 文件。

#### 启动所有进程的命令

```bash
# 1. 支撑压力线采集器（核心）
pm2 start support_resistance_collector.py \
    --name support-resistance-collector \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/support-resistance-collector.log

# 2. 支撑压力线快照采集器（核心）
pm2 start support_resistance_snapshot_collector.py \
    --name support-snapshot-collector \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/support-snapshot-collector.log

# 3. Google Drive 监控
pm2 start gdrive_final_detector.py \
    --name gdrive-detector \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/gdrive-detector.log

# 4. Telegram 通知
pm2 start telegram_signal_system.py \
    --name telegram-notifier \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/telegram-notifier.log

# 5. 锚点维护（核心）
pm2 start anchor_maintenance_realtime_daemon.py \
    --name anchor-maintenance \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/anchor-maintenance.log

# 6. 利润极值追踪（核心）
pm2 start start_profit_extremes_tracker.sh \
    --name profit-extremes-tracker \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/profit-extremes-tracker.log

# 7. Flask Web应用（核心）
pm2 start --name flask-app --interpreter bash -x -- -c \
    "cd /home/user/webapp && python3 app_new.py"

# 8. 子账户开单守护进程（核心）
pm2 start sub_account_opener_daemon.py \
    --name sub-account-opener \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/sub-account-opener.log

# 9. 子账户超级维护（核心）
pm2 start sub_account_super_maintenance.py \
    --name sub-account-super-maintenance \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/sub-account-super-maintenance.log

# 10. 逃顶信号记录器（可选）
pm2 start escape_stats_recorder.py \
    --name escape-stats-recorder \
    --interpreter python3 \
    --cwd /home/user/webapp \
    --log /home/user/.pm2/logs/escape-stats-recorder.log

# 保存PM2配置
pm2 save

# 设置开机自启
pm2 startup
```

### PM2常用命令

```bash
# 查看进程列表
pm2 list

# 查看进程详情
pm2 show <进程名>

# 查看日志
pm2 logs <进程名>

# 重启进程
pm2 restart <进程名>

# 停止进程
pm2 stop <进程名>

# 删除进程
pm2 delete <进程名>

# 监控
pm2 monit

# 保存配置
pm2 save

# 恢复保存的配置
pm2 resurrect
```

---

## 📄 配置文件清单

### ⚠️ 必须手动备份的配置文件（包含敏感信息）

这些文件不在git仓库中，必须单独备份：

#### 1. sub_account_config.json（自动交易配置）
**位置**: `/home/user/webapp/sub_account_config.json`

```json
{
  "sub_accounts": [
    {
      "name": "sub1",
      "api_key": "YOUR_API_KEY",
      "secret_key": "YOUR_SECRET_KEY",
      "passphrase": "YOUR_PASSPHRASE",
      "is_active": true,
      "max_position_size": 1000.0
    }
  ],
  "trading_rules": {
    "max_open_orders": 10,
    "min_order_size": 10.0,
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
  }
}
```

#### 2. anchor_config.json（锚点配置）
**位置**: `/home/user/webapp/anchor_config.json`

```json
{
  "symbols": ["BTC-USDT", "ETH-USDT"],
  "check_interval": 60,
  "profit_alert_threshold": 5.0,
  "max_anchor_age_hours": 24
}
```

#### 3. telegram_config.json（Telegram配置）
**位置**: `/home/user/webapp/telegram_config.json`

```json
{
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_ids": ["YOUR_CHAT_ID"],
  "enable_notifications": true,
  "notification_types": [
    "anchor_alert",
    "trading_signal",
    "profit_alert",
    "error_alert"
  ]
}
```

#### 4. gdrive_config.json（Google Drive配置）
**位置**: `/home/user/webapp/gdrive_config.json`

```json
{
  "credentials_file": "credentials.json",
  "token_file": "token.json",
  "folder_ids": ["YOUR_FOLDER_ID"],
  "check_interval": 300
}
```

### 📦 其他配置文件（在git中）

- `requirements.txt` - Python依赖
- `.gitignore` - Git忽略规则
- `README.md` - 项目说明
- `SYSTEM_RECOVERY_GUIDE.md` - 系统恢复指南
- `DATABASE_SCHEMA.md` - 数据库结构文档
- `BACKUP_README.md` - 备份说明

---

## 🔄 详细恢复步骤

### 步骤1: 准备环境

```bash
# 创建工作目录
mkdir -p /home/user/webapp
cd /home/user/webapp

# 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3 python3-pip sqlite3 git nodejs npm

# 安装PM2
sudo npm install -g pm2
```

### 步骤2: 克隆代码

```bash
# 克隆仓库
git clone https://github.com/jamesyidc/666612.git .

# 查看当前分支
git branch -a

# 切换到main分支
git checkout main
```

### 步骤3: 安装Python依赖

```bash
# 安装依赖
pip3 install -r requirements.txt

# 验证关键库
python3 -c "import flask, sqlite3, requests, pandas; print('✅ 依赖安装成功')"
```

### 步骤4: 恢复数据库

```bash
# 创建数据库目录
mkdir -p databases

# 方法1: 从.db文件恢复（推荐）
cp /backup/crypto_data.db databases/crypto_data.db
cp /backup/support_resistance.db support_resistance.db
cp /backup/panic_index.db databases/panic_index.db
cp /backup/gdrive_monitor.db databases/gdrive_monitor.db
cp /backup/market_data.db databases/market_data.db

# 方法2: 从SQL导出恢复
sqlite3 databases/crypto_data.db < backups/crypto_data_dump.sql
sqlite3 support_resistance.db < backups/support_resistance_dump.sql

# 验证数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_levels;"

# 设置权限
chmod 644 databases/*.db
chmod 644 support_resistance.db
```

### 步骤5: 恢复配置文件

```bash
# 恢复敏感配置文件（从安全备份位置）
cp /secure_backup/sub_account_config.json .
cp /secure_backup/anchor_config.json .
cp /secure_backup/telegram_config.json .
cp /secure_backup/gdrive_config.json .

# 如果有Google Drive凭证
cp /secure_backup/credentials.json .
cp /secure_backup/token.json .

# 设置权限（重要！）
chmod 600 *.json
chmod 600 credentials.json token.json

# 验证配置文件格式
python3 -c "import json; json.load(open('sub_account_config.json')); print('✅ 配置文件格式正确')"
```

### 步骤6: 启动PM2进程

#### 6.1 启动核心系统

```bash
# 1. 支撑压力线系统（最重要）
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_resistance_snapshot_collector.py --name support-snapshot-collector

# 2. 锚点系统
pm2 start anchor_maintenance_realtime_daemon.py --name anchor-maintenance
pm2 start start_profit_extremes_tracker.sh --name profit-extremes-tracker

# 3. 自动交易系统
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance

# 4. Flask Web应用
pm2 start --name flask-app --interpreter bash -x -- -c "cd /home/user/webapp && python3 app_new.py"
```

#### 6.2 启动辅助系统

```bash
# 5. Google Drive监控
pm2 start gdrive_final_detector.py --name gdrive-detector

# 6. Telegram通知
pm2 start telegram_signal_system.py --name telegram-notifier

# 7. 逃顶信号记录器（可选）
pm2 start escape_stats_recorder.py --name escape-stats-recorder
```

#### 6.3 保存配置

```bash
# 保存PM2配置
pm2 save

# 设置开机自启
pm2 startup

# 检查进程状态
pm2 list
```

### 步骤7: 验证系统

```bash
# 等待服务启动（30秒）
sleep 30

# 检查PM2进程
pm2 list

# 检查Flask是否运行
curl -I http://localhost:5000/support-resistance

# 检查API
curl -s http://localhost:5000/api/support-resistance/escape-signal-stats | python3 -m json.tool

# 检查数据库连接
python3 -c "
import sqlite3
conn = sqlite3.connect('databases/crypto_data.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM escape_signal_stats')
print(f'✅ escape_signal_stats 表有 {cursor.fetchone()[0]} 条记录')
conn.close()
"

# 查看最新日志
pm2 logs --lines 50
```

---

## ✅ 验证清单

### 1. 数据库验证

```bash
# crypto_data.db
sqlite3 databases/crypto_data.db "SELECT name FROM sqlite_master WHERE type='table';"
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"
sqlite3 databases/crypto_data.db "SELECT * FROM escape_signal_stats ORDER BY stat_time DESC LIMIT 3;"

# support_resistance.db
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_levels;"
sqlite3 support_resistance.db "SELECT symbol, COUNT(*) FROM support_resistance_levels GROUP BY symbol LIMIT 10;"
```

### 2. PM2进程验证

```bash
# 所有进程应该是 online 状态
pm2 list

# 检查进程详情
pm2 show flask-app
pm2 show support-resistance-collector

# 检查日志是否有错误
pm2 logs --err --lines 100
```

### 3. Web界面验证

访问以下页面，确认正常显示：

- 主页面: http://localhost:5000/support-resistance
- 历史数据: http://localhost:5000/escape-stats-history
- 恐慌指数: http://localhost:5000/panic-index
- 锚点系统: http://localhost:5000/anchor-system
- 持仓管理: http://localhost:5000/positions

### 4. API验证

```bash
# 逃顶信号API
curl http://localhost:5000/api/support-resistance/escape-signal-stats

# 历史数据API
curl http://localhost:5000/api/support-resistance/escape-stats-history?hours=24

# 支撑压力位API
curl http://localhost:5000/api/support-resistance/levels/BTC-USDT
```

### 5. 配置文件验证

```bash
# 检查配置文件是否存在
ls -la *.json

# 验证JSON格式
for file in *.json; do
    echo "Checking $file..."
    python3 -c "import json; json.load(open('$file'))" && echo "✅ $file OK" || echo "❌ $file ERROR"
done
```

---

## 🔧 故障排查

### 问题1: PM2进程无法启动

**症状**: `pm2 list` 显示进程状态为 `errored` 或 `stopped`

**解决方案**:
```bash
# 查看错误日志
pm2 logs <进程名> --err --lines 100

# 常见原因1: 缺少依赖
pip3 install -r requirements.txt

# 常见原因2: 数据库文件不存在
ls -la databases/*.db
# 如果缺少，恢复数据库文件

# 常见原因3: 配置文件错误
python3 -c "import json; json.load(open('sub_account_config.json'))"

# 常见原因4: 端口被占用（Flask）
lsof -i:5000
# 杀掉占用进程或更改端口

# 重启进程
pm2 restart <进程名>
```

### 问题2: Flask无法访问

**症状**: `curl http://localhost:5000` 无响应

**解决方案**:
```bash
# 检查Flask进程
pm2 show flask-app

# 检查Flask日志
pm2 logs flask-app --lines 100

# 检查端口占用
netstat -tlnp | grep 5000

# 手动启动Flask测试
cd /home/user/webapp
python3 app_new.py
# 看是否有错误输出

# 检查防火墙
sudo ufw status
sudo ufw allow 5000
```

### 问题3: 数据库查询错误

**症状**: API返回 "no such table" 或其他数据库错误

**解决方案**:
```bash
# 检查数据库文件是否存在
ls -la databases/crypto_data.db
ls -la support_resistance.db

# 检查表结构
sqlite3 databases/crypto_data.db ".tables"
sqlite3 databases/crypto_data.db ".schema escape_signal_stats"

# 如果表不存在，从备份恢复
cp /backup/crypto_data.db databases/crypto_data.db

# 或者从SQL创建表
sqlite3 databases/crypto_data.db < create_tables.sql
```

### 问题4: 前端显示数据为空

**症状**: 页面打开正常，但没有数据显示

**解决方案**:
```bash
# 1. 检查API是否返回数据
curl http://localhost:5000/api/support-resistance/escape-signal-stats

# 2. 检查数据库是否有数据
sqlite3 databases/crypto_data.db "SELECT * FROM escape_signal_stats ORDER BY stat_time DESC LIMIT 5;"

# 3. 如果数据库为空，检查采集器是否运行
pm2 list | grep support-resistance-collector

# 4. 查看采集器日志
pm2 logs support-resistance-collector --lines 100

# 5. 手动运行采集器测试
python3 support_resistance_collector.py
```

### 问题5: 自动交易系统无法开单

**症状**: 订单无法创建，或API错误

**解决方案**:
```bash
# 1. 检查配置文件
cat sub_account_config.json
python3 -c "import json; print(json.load(open('sub_account_config.json')))"

# 2. 检查API密钥是否有效
# 手动测试API连接
python3 -c "
import json
config = json.load(open('sub_account_config.json'))
account = config['sub_accounts'][0]
print(f'API Key: {account[\"api_key\"][:10]}...')
# 这里添加API测试代码
"

# 3. 检查守护进程日志
pm2 logs sub-account-opener --lines 200
pm2 logs sub-account-super-maintenance --lines 200

# 4. 检查数据库表
sqlite3 databases/crypto_data.db "SELECT * FROM sub_accounts;"
sqlite3 databases/crypto_data.db "SELECT * FROM trading_orders ORDER BY created_at DESC LIMIT 10;"
```

### 问题6: Telegram通知不工作

**症状**: 没有收到Telegram消息

**解决方案**:
```bash
# 1. 检查配置
cat telegram_config.json

# 2. 检查进程状态
pm2 logs telegram-notifier --lines 100

# 3. 手动测试Telegram Bot
python3 -c "
import json
import requests
config = json.load(open('telegram_config.json'))
token = config['bot_token']
chat_id = config['chat_ids'][0]
url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {'chat_id': chat_id, 'text': '测试消息'}
response = requests.post(url, json=data)
print(response.json())
"
```

---

## 📊 关键数据统计

### 当前系统状态（示例数据）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 系统运行状态报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
📊 数据库统计:
  - escape_signal_stats:         6 条记录
  - support_resistance_levels:   294,799 条记录
  - support_resistance_snapshots: 11,527 条记录
  - okex_kline_ohlc:             50,000 条记录
  - anchor_records:              150 条记录
  - trading_orders:              500 条记录
  
⚙️  PM2进程状态:
  - 运行中: 10 个进程
  - 在线: 10/10
  - 重启次数: 总计 120 次
  
🌐 Web服务:
  - Flask: http://localhost:5000
  - 状态: ✅ 正常运行
  
📈 最新数据:
  - 24小时逃顶信号数: 251
  - 2小时逃顶信号数: 2
  - 历史最大值 24h: 275
  - 历史最大值 2h: 18
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📦 备份建议

### 自动备份脚本

创建 `/home/user/webapp/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backup/webapp_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份数据库
echo "📦 备份数据库..."
cp databases/crypto_data.db "$BACKUP_DIR/"
cp support_resistance.db "$BACKUP_DIR/"
cp databases/panic_index.db "$BACKUP_DIR/"
cp databases/gdrive_monitor.db "$BACKUP_DIR/"
cp databases/market_data.db "$BACKUP_DIR/"

# 备份配置文件
echo "📄 备份配置文件..."
cp *.json "$BACKUP_DIR/" 2>/dev/null || true
cp credentials.json token.json "$BACKUP_DIR/" 2>/dev/null || true

# 导出SQL
echo "📝 导出SQL..."
sqlite3 databases/crypto_data.db .dump > "$BACKUP_DIR/crypto_data.sql"
sqlite3 support_resistance.db .dump > "$BACKUP_DIR/support_resistance.sql"

# 备份PM2配置
echo "⚙️  备份PM2配置..."
pm2 save
cp ~/.pm2/dump.pm2 "$BACKUP_DIR/"

# 压缩
echo "🗜️  压缩备份..."
tar -czf "$BACKUP_DIR.tar.gz" -C /backup "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "✅ 备份完成: $BACKUP_DIR.tar.gz"
```

设置定时备份:
```bash
chmod +x backup.sh

# 添加到crontab，每天凌晨2点备份
crontab -e
# 添加: 0 2 * * * /home/user/webapp/backup.sh
```

---

## 📖 相关文档

- `SYSTEM_RECOVERY_GUIDE.md` - 系统恢复详细指南
- `DATABASE_SCHEMA.md` - 数据库结构完整文档
- `BACKUP_README.md` - 备份快速说明
- `PM2_PROCESSES.json` - PM2进程配置导出
- `README.md` - 项目说明

---

## 🎯 总结

### 核心系统恢复优先级

1. **必须恢复**（否则系统无法运行）:
   - crypto_data.db 数据库
   - support_resistance.db 数据库
   - Flask Web应用
   - 支撑压力线采集器
   - 配置文件（*.json）

2. **重要恢复**（影响核心功能）:
   - 锚点系统
   - 自动交易系统
   - 子账户配置

3. **可选恢复**（辅助功能）:
   - Google Drive监控
   - Telegram通知
   - 其他辅助脚本

### 快速恢复检查表

- [ ] Git仓库已克隆
- [ ] Python依赖已安装
- [ ] 数据库文件已恢复
- [ ] 配置文件已恢复
- [ ] PM2进程已启动
- [ ] Flask可以访问
- [ ] API返回正常
- [ ] 前端显示正常
- [ ] 数据采集正常
- [ ] 自动交易正常（如需要）

---

**维护者**: System Admin  
**最后更新**: 2026-01-02  
**文档版本**: v2.0  
**GitHub**: https://github.com/jamesyidc/666612
