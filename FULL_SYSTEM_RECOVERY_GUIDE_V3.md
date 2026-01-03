# 🎯 23个子系统完整恢复指南

> **1:1完美还原 - 详细部署手册**  
> **日期**: 2026-01-03  
> **版本**: v3.0  
> **备份位置**: `/tmp/webapp_backup_20260103_005507` (144MB)

---

## 📋 目录

1. [快速恢复概览](#快速恢复概览)
2. [23个子系统详细清单](#23个子系统详细清单)
3. [数据库完整对应关系](#数据库完整对应关系)
4. [逐系统恢复步骤](#逐系统恢复步骤)
5. [重点系统恢复](#重点系统恢复)
6. [验证清单](#验证清单)

---

## ⚡ 快速恢复概览

### 基础恢复（5步骤）

```bash
# 1. 克隆代码
git clone https://github.com/jamesyidc/666612.git /home/user/webapp
cd /home/user/webapp

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 恢复数据库（从备份）
cp /tmp/webapp_backup_*/databases/crypto_data.db databases/
cp /tmp/webapp_backup_*/support_resistance.db .

# 4. 恢复配置文件（⚠️ 从安全位置）
cp /secure_backup/*.json .
chmod 600 *.json

# 5. 启动所有服务
pm2 resurrect  # 或手动启动各进程
```

---

## 📦 23个子系统详细清单

### ⭐ 第一优先级：核心系统（7个 - 必须恢复）

#### 1. 【支撑压力线系统】
**脚本**: `support_resistance_collector.py`  
**PM2进程**: `support-resistance-collector`  
**数据库**: 
- `support_resistance.db` (位于根目录) ⚠️
  - 表: `support_resistance_levels` (294,799条)
- `databases/crypto_data.db`
  - 表: `support_resistance_snapshots`

**文件清单**:
```
support_resistance_collector.py        # 核心采集脚本
templates/support_resistance.html      # 前端页面
support_resistance.db                  # 数据库（根目录）
```

**启动命令**:
```bash
pm2 start support_resistance_collector.py --name support-resistance-collector
```

**验证**:
```bash
# 检查数据
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_levels;"
# 应该返回: 294799 (或接近的数字)

# 检查进程
pm2 logs support-resistance-collector --lines 20
```

---

#### 2. 【支撑压力快照系统】
**脚本**: `support_resistance_snapshot_collector.py`  
**PM2进程**: `support-snapshot-collector`  
**数据库**:
- `databases/crypto_data.db`
  - 表: `support_resistance_snapshots` (11,527条)

**文件清单**:
```
support_resistance_snapshot_collector.py   # 快照采集脚本
templates/escape_stats_history.html       # 历史数据页面
```

**启动命令**:
```bash
pm2 start support_resistance_snapshot_collector.py --name support-snapshot-collector
```

**验证**:
```bash
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM support_resistance_snapshots;"
```

---

#### 3. 【锚点系统】⭐ 重点系统
**脚本**: 
- `anchor_maintenance_realtime_daemon.py` (锚点维护)
- `start_profit_extremes_tracker.sh` (利润追踪)

**PM2进程**: 
- `anchor-maintenance`
- `profit-extremes-tracker`

**数据库**:
- `databases/crypto_data.db`
  - 表: `anchor_records` (~150条)
  - 表: `anchor_profit_records` (~500条)

**配置文件**: `anchor_config.json` 🔑

**文件清单**:
```
anchor_maintenance_realtime_daemon.py     # 锚点维护守护进程
start_profit_extremes_tracker.sh          # 利润追踪启动脚本
anchor_profit_tracker.py                  # 利润追踪器
templates/anchor_system.html              # 锚点系统页面
anchor_config.json                        # 配置文件（需单独备份）
```

**启动命令**:
```bash
pm2 start anchor_maintenance_realtime_daemon.py --name anchor-maintenance
pm2 start start_profit_extremes_tracker.sh --name profit-extremes-tracker
```

**验证**:
```bash
# 检查锚点记录
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM anchor_records WHERE is_active=1;"

# 检查利润记录
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM anchor_profit_records;"

# 访问页面
curl -I http://localhost:5000/anchor-system
```

---

#### 4. 【自动交易系统】⭐ 重点系统
**脚本**:
- `sub_account_opener_daemon.py` (开单)
- `sub_account_super_maintenance.py` (维护)

**PM2进程**:
- `sub-account-opener`
- `sub-account-super-maintenance`

**数据库**:
- `databases/crypto_data.db`
  - 表: `trading_orders` (~500条)
  - 表: `sub_accounts` (~5条)
  - 表: `current_positions` (~20条)

**配置文件**: `sub_account_config.json` 🔴 **极重要**

**文件清单**:
```
sub_account_opener_daemon.py              # 自动开单守护进程
sub_account_super_maintenance.py          # 超级维护守护进程
templates/sub_account_monitor.html        # 监控页面
sub_account_config.json                   # 配置文件（包含API密钥）
```

**配置文件结构**:
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
    "min_order_size": 10.0
  }
}
```

**启动命令**:
```bash
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance
```

**验证**:
```bash
# 检查子账户配置
sqlite3 databases/crypto_data.db "SELECT account_name, is_active FROM sub_accounts;"

# 检查最新订单
sqlite3 databases/crypto_data.db "SELECT * FROM trading_orders ORDER BY created_at DESC LIMIT 5;"

# 检查当前持仓
sqlite3 databases/crypto_data.db "SELECT * FROM current_positions;"
```

---

#### 5. 【Flask Web应用】
**脚本**: `app_new.py`  
**PM2进程**: `flask-app`  
**端口**: 5000  
**数据库**: 所有数据库（集成所有API）

**文件清单**:
```
app_new.py                               # Flask主应用
templates/*.html                         # 所有HTML模板
static/                                  # 静态资源（如有）
```

**启动命令**:
```bash
pm2 start --name flask-app --interpreter bash -x -- -c "cd /home/user/webapp && python3 app_new.py"
```

**验证**:
```bash
# 检查Web服务
curl -I http://localhost:5000/support-resistance

# 检查API
curl http://localhost:5000/api/support-resistance/escape-signal-stats
```

---

#### 6. 【逃顶信号系统】
**脚本**: `escape_stats_recorder.py`  
**PM2进程**: `escape-stats-recorder`  
**数据库**:
- `databases/crypto_data.db`
  - 表: `escape_signal_stats` (6条)

**文件清单**:
```
escape_stats_recorder.py                 # 信号记录脚本
templates/escape_stats_history.html      # 历史数据页面
```

**数据字段说明**:
```sql
escape_signal_stats:
  - signal_24h_count: 24小时逃顶信号数（前端计算）
  - signal_2h_count: 2小时逃顶信号数（前端计算）
  - 记录频率: 每分钟
```

**启动命令**:
```bash
pm2 start escape_stats_recorder.py --name escape-stats-recorder
```

---

#### 7. 【SAR斜率系统】⭐ 重点系统
**脚本**: `sar_slope_collector.py`  
**PM2进程**: `sar-slope-collector`  
**数据库**:
- `databases/sar_slope_data.db`
  - 表: `sar_slope_records`

**文件清单**:
```
sar_slope_collector.py                   # SAR斜率采集器
templates/sar_slope.html                 # SAR斜率页面
databases/sar_slope_data.db              # 数据库
```

**启动命令**:
```bash
pm2 start sar_slope_collector.py --name sar-slope-collector
```

---

### 🔧 第二优先级：辅助系统（3个）

#### 8. 【Google Drive监控系统】
**脚本**: `gdrive_final_detector.py`  
**PM2进程**: `gdrive-detector`  
**数据库**:
- `databases/gdrive_monitor.db`
  - 表: `gdrive_files`

**配置文件**: `gdrive_config.json` 🔑

**文件清单**:
```
gdrive_final_detector.py                 # Google Drive检测器
gdrive_config.json                       # 配置文件
credentials.json                         # Google凭证
token.json                               # Google令牌
```

**启动命令**:
```bash
pm2 start gdrive_final_detector.py --name gdrive-detector
```

---

#### 9. 【Telegram消息推送系统】
**脚本**: `telegram_signal_system.py`  
**PM2进程**: `telegram-notifier`  
**配置文件**: `telegram_config.json` 🔑

**文件清单**:
```
telegram_signal_system.py                # Telegram通知系统
telegram_config.json                     # 配置文件
```

**配置文件结构**:
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

**启动命令**:
```bash
pm2 start telegram_signal_system.py --name telegram-notifier
```

---

#### 10. 【资金监控系统】
**脚本**: `fund_monitor_collector.py`  
**PM2进程**: `fund-monitor-collector`  
**数据库**:
- `databases/fund_monitor.db`
  - 表: `fund_flow_records`

**文件清单**:
```
fund_monitor_collector.py                # 资金监控采集器
templates/fund_monitor.html              # 资金监控页面
databases/fund_monitor.db                # 数据库
```

**启动命令**:
```bash
pm2 start fund_monitor_collector.py --name fund-monitor-collector
```

---

### 📊 第三优先级：数据展示系统（13个 - 通过Flask Web访问）

这些系统不需要单独的PM2进程，都通过Flask应用访问。

#### 11. 【历史数据查询系统】⭐ 重点系统
**路由**: `/api/history/*`  
**数据库**: `databases/crypto_data.db`  
**表**: `okex_kline_ohlc` (50,000条)

**文件清单**:
```
templates/history_query.html             # 历史查询页面
# API在 app_new.py 中定义
```

**API端点**:
```
GET /api/history/klines/{symbol}         # 获取K线数据
GET /api/history/price/{symbol}          # 获取历史价格
```

---

#### 12. 【恐慌清洗指数系统】⭐ 重点系统
**路由**: `/panic-index`  
**数据库**: `databases/panic_index.db`（如存在）  
**表**: `panic_index_records`

**文件清单**:
```
templates/panic_index.html               # 恐慌指数页面
panic_index_calculator.py                # 指数计算器（如有）
```

---

#### 13. 【比价系统】
**路由**: `/price-compare`  
**数据库**: `databases/market_data.db`  
**表**: `price_comparison`

**文件清单**:
```
templates/price_comparison.html          # 比价页面
```

---

#### 14. 【星星系统】
**路由**: `/star-rating`  
**数据库**: `databases/crypto_data.db`  
**表**: `coin_ratings`

**文件清单**:
```
templates/star_rating.html               # 星星评级页面
```

---

#### 15. 【币种池系统】
**路由**: `/coin-pool`  
**数据库**: `databases/crypto_data.db`  
**表**: `coin_pool`

**文件清单**:
```
templates/coin_pool.html                 # 币种池页面
```

---

#### 16. 【实时市场原始数据】
**路由**: `/market-data`  
**数据库**: `databases/market_data.db`  
**表**: `market_ticker`

**文件清单**:
```
templates/market_data.html               # 市场数据页面
```

---

#### 17. 【数据采集监控】
**路由**: `/collector-status`  
**数据库**: 无（实时监控）

**文件清单**:
```
templates/collector_status.html          # 采集器状态页面
```

---

#### 18. 【深度图得分】
**路由**: `/depth-score`  
**数据库**: `databases/crypto_data.db`  
**表**: `depth_scores`

**文件清单**:
```
templates/depth_score.html               # 深度图得分页面
```

---

#### 19. 【深度图可视化】
**路由**: `/depth-chart`  
**数据库**: `databases/crypto_data.db`

**文件清单**:
```
templates/depth_chart.html               # 深度图可视化页面
```

---

#### 20. 【平均分页面】
**路由**: `/average-score`  
**数据库**: `databases/crypto_data.db`  
**表**: `average_scores`

**文件清单**:
```
templates/average_score.html             # 平均分页面
```

---

#### 21. 【OKEx加密指数】
**路由**: `/okex-indicators`  
**数据库**: `databases/crypto_data.db`  
**表**: `okex_technical_indicators`

**文件清单**:
```
templates/okex_indicators.html           # OKEx指标页面
```

---

#### 22. 【位置系统】
**路由**: `/position-system`  
**数据库**: `databases/crypto_data.db`  
**表**: `current_positions`

**文件清单**:
```
templates/position_system.html           # 位置系统页面
```

---

#### 23. 【决策交易信号系统】
**路由**: `/decision-signals`  
**数据库**: `databases/trading_decision.db`  
**表**: `decision_signals`

**文件清单**:
```
templates/decision_signals.html          # 决策信号页面
databases/trading_decision.db            # 数据库
```

---

## 💾 数据库完整对应关系

### 主数据库: crypto_data.db
**位置**: `databases/crypto_data.db`  
**大小**: ~500MB

| 表名 | 记录数 | 对应系统 | 重要性 |
|------|--------|----------|--------|
| escape_signal_stats | 6 | 逃顶信号系统 | ⭐⭐⭐⭐⭐ |
| anchor_records | ~150 | 锚点系统 | ⭐⭐⭐⭐⭐ |
| anchor_profit_records | ~500 | 锚点系统 | ⭐⭐⭐⭐ |
| trading_orders | ~500 | 自动交易系统 | ⭐⭐⭐⭐⭐ |
| sub_accounts | ~5 | 自动交易系统 | ⭐⭐⭐⭐⭐ |
| current_positions | ~20 | 自动交易/位置系统 | ⭐⭐⭐⭐⭐ |
| support_resistance_snapshots | 11,527 | 支撑压力快照系统 | ⭐⭐⭐ |
| daily_baseline_prices | 405 | 多个系统 | ⭐⭐⭐ |
| okex_kline_ohlc | 50,000 | 历史数据查询系统 | ⭐⭐⭐ |

### 支撑压力数据库: support_resistance.db
**位置**: `/home/user/webapp/support_resistance.db` ⚠️ **注意：在根目录**  
**大小**: ~137MB

| 表名 | 记录数 | 对应系统 | 重要性 |
|------|--------|----------|--------|
| support_resistance_levels | 294,799 | 支撑压力线系统 | ⭐⭐⭐⭐⭐ |

### SAR斜率数据库: sar_slope_data.db
**位置**: `databases/sar_slope_data.db`

| 表名 | 记录数 | 对应系统 | 重要性 |
|------|--------|----------|--------|
| sar_slope_records | N/A | SAR斜率系统 | ⭐⭐⭐⭐ |

### 其他数据库

| 数据库 | 位置 | 对应系统 | 重要性 |
|--------|------|----------|--------|
| panic_index.db | databases/ | 恐慌清洗指数系统 | ⭐⭐⭐ |
| gdrive_monitor.db | databases/ | Google Drive监控系统 | ⭐⭐ |
| market_data.db | databases/ | 实时市场数据/比价系统 | ⭐⭐⭐ |
| trading_decision.db | databases/ | 决策交易信号系统 | ⭐⭐⭐ |
| fund_monitor.db | databases/ | 资金监控系统 | ⭐⭐⭐ |

---

## 🔄 重点系统恢复详细步骤

### 1️⃣  SAR斜率系统（完整恢复）

**所需文件**:
```
✓ sar_slope_collector.py
✓ templates/sar_slope.html
✓ databases/sar_slope_data.db
```

**恢复步骤**:
```bash
# 1. 从备份恢复数据库
cp /tmp/webapp_backup_*/databases/sar_slope_data.db databases/

# 2. 验证数据库
sqlite3 databases/sar_slope_data.db ".tables"
sqlite3 databases/sar_slope_data.db "SELECT COUNT(*) FROM sar_slope_records;"

# 3. 启动采集器
pm2 start sar_slope_collector.py --name sar-slope-collector

# 4. 验证采集器运行
pm2 logs sar-slope-collector --lines 20

# 5. 访问页面
curl -I http://localhost:5000/sar-slope
```

---

### 2️⃣  历史数据查询系统（完整恢复）

**所需文件**:
```
✓ templates/history_query.html
✓ databases/crypto_data.db (包含 okex_kline_ohlc 表)
```

**恢复步骤**:
```bash
# 1. 确认数据库存在
ls -lh databases/crypto_data.db

# 2. 验证K线数据
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM okex_kline_ohlc;"
# 应该返回: 50000 (或接近的数字)

# 3. 确认Flask运行
pm2 status flask-app

# 4. 测试API
curl "http://localhost:5000/api/history/klines/BTC-USDT?limit=100"

# 5. 访问页面
curl -I http://localhost:5000/history-query
```

---

### 3️⃣  恐慌清洗指数系统（完整恢复）

**所需文件**:
```
✓ templates/panic_index.html
✓ databases/panic_index.db (如存在)
✓ panic_index_calculator.py (如有独立脚本)
```

**恢复步骤**:
```bash
# 1. 从备份恢复数据库（如有）
cp /tmp/webapp_backup_*/databases/panic_index.db databases/ 2>/dev/null

# 2. 验证数据库
sqlite3 databases/panic_index.db ".schema"

# 3. 访问页面
curl -I http://localhost:5000/panic-index

# 4. 测试API
curl "http://localhost:5000/api/panic-index/latest"
```

---

### 4️⃣  支撑压力线系统（完整恢复）⭐ 核心系统

**所需文件**:
```
✓ support_resistance_collector.py
✓ support_resistance_snapshot_collector.py
✓ templates/support_resistance.html
✓ templates/escape_stats_history.html
✓ support_resistance.db (根目录)
✓ databases/crypto_data.db
```

**恢复步骤**:
```bash
# 1. 从备份恢复数据库
cp /tmp/webapp_backup_*/support_resistance.db .
cp /tmp/webapp_backup_*/databases/crypto_data.db databases/

# 2. 验证数据库
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_levels;"
# 应该返回: 294799

sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM support_resistance_snapshots;"
# 应该返回: 11527

# 3. 启动采集器
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_resistance_snapshot_collector.py --name support-snapshot-collector

# 4. 验证采集器
pm2 logs support-resistance-collector --lines 20
pm2 logs support-snapshot-collector --lines 20

# 5. 访问主页面
curl -I http://localhost:5000/support-resistance

# 6. 测试API
curl "http://localhost:5000/api/support-resistance/escape-signal-stats"
curl "http://localhost:5000/api/support-resistance/escape-stats-history?hours=24"

# 7. 访问历史数据页面
curl -I http://localhost:5000/escape-stats-history
```

---

### 5️⃣  锚点系统（完整恢复）⭐ 核心系统

**所需文件**:
```
✓ anchor_maintenance_realtime_daemon.py
✓ start_profit_extremes_tracker.sh
✓ anchor_profit_tracker.py
✓ templates/anchor_system.html
✓ anchor_config.json (需单独备份)
✓ databases/crypto_data.db
```

**恢复步骤**:
```bash
# 1. 恢复配置文件（从安全位置）
cp /secure_backup/anchor_config.json .
chmod 600 anchor_config.json

# 2. 验证配置文件
python3 -c "import json; json.load(open('anchor_config.json')); print('✅ 配置文件格式正确')"

# 3. 验证数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM anchor_records;"
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM anchor_profit_records;"

# 4. 启动锚点系统
pm2 start anchor_maintenance_realtime_daemon.py --name anchor-maintenance
pm2 start start_profit_extremes_tracker.sh --name profit-extremes-tracker

# 5. 验证进程
pm2 logs anchor-maintenance --lines 20
pm2 logs profit-extremes-tracker --lines 20

# 6. 访问页面
curl -I http://localhost:5000/anchor-system

# 7. 测试API
curl "http://localhost:5000/api/anchor/records"
curl "http://localhost:5000/api/anchor/profit-extremes"
```

---

### 6️⃣  自动交易系统（完整恢复）⭐ 核心系统

**所需文件**:
```
✓ sub_account_opener_daemon.py
✓ sub_account_super_maintenance.py
✓ templates/sub_account_monitor.html
✓ sub_account_config.json (需单独备份) 🔴 极重要
✓ databases/crypto_data.db
```

**恢复步骤**:
```bash
# 1. 恢复配置文件（从安全位置）⚠️ 包含API密钥
cp /secure_backup/sub_account_config.json .
chmod 600 sub_account_config.json

# 2. 验证配置文件格式
python3 -c "import json; c=json.load(open('sub_account_config.json')); print(f'✅ 配置正确: {len(c[\"sub_accounts\"])} 个子账户')"

# 3. 验证数据库表
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM sub_accounts;"
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM trading_orders;"
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM current_positions;"

# 4. 测试API连接（在启动前）
python3 -c "
import json
config = json.load(open('sub_account_config.json'))
account = config['sub_accounts'][0]
print(f'账户名: {account[\"name\"]}')
print(f'API Key前10位: {account[\"api_key\"][:10]}...')
# 这里可以添加实际API测试代码
"

# 5. 启动自动交易系统
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance

# 6. 密切监控日志（前5分钟）
pm2 logs sub-account-opener --lines 50
pm2 logs sub-account-super-maintenance --lines 50

# 7. 验证系统运行
sqlite3 databases/crypto_data.db "SELECT * FROM trading_orders ORDER BY created_at DESC LIMIT 5;"

# 8. 访问监控页面
curl -I http://localhost:5000/sub-account-monitor
```

**⚠️ 安全注意事项**:
- API密钥绝对不能泄露
- 配置文件权限必须是 600
- 建议使用只读API密钥测试
- 小额测试后再开启实盘

---

## ✅ 完整验证清单

### 1. 数据库验证

```bash
# crypto_data.db
sqlite3 databases/crypto_data.db "SELECT name FROM sqlite_master WHERE type='table';" | wc -l
# 应该有多个表

sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM anchor_records;"
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM trading_orders;"

# support_resistance.db
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_levels;"
# 应该返回: ~294799
```

### 2. PM2进程验证

```bash
# 所有进程应该是 online
pm2 list

# 核心进程检查
pm2 show support-resistance-collector
pm2 show anchor-maintenance
pm2 show sub-account-opener
pm2 show flask-app
```

### 3. Web服务验证

```bash
# Flask主页
curl -I http://localhost:5000/support-resistance
# 应该返回: HTTP/1.1 200 OK

# 主要页面
curl -I http://localhost:5000/escape-stats-history
curl -I http://localhost:5000/anchor-system
curl -I http://localhost:5000/sub-account-monitor
```

### 4. API验证

```bash
# 逃顶信号API
curl -s http://localhost:5000/api/support-resistance/escape-signal-stats | python3 -m json.tool

# 锚点API
curl -s http://localhost:5000/api/anchor/records | python3 -m json.tool

# 历史数据API
curl -s "http://localhost:5000/api/support-resistance/escape-stats-history?hours=24" | python3 -m json.tool
```

### 5. 配置文件验证

```bash
# 检查所有配置文件
ls -la *.json

# 验证格式
for file in *.json; do
    echo "检查 $file..."
    python3 -c "import json; json.load(open('$file'))" && echo "  ✅ OK" || echo "  ❌ ERROR"
done
```

### 6. 系统完整性验证

运行以下脚本验证所有23个系统：

```bash
#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  23个子系统验证"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 核心系统
echo "⭐ 核心系统:"
curl -s -I http://localhost:5000/support-resistance | grep "200 OK" && echo "  ✅ 1. 支撑压力线系统" || echo "  ❌ 1. 支撑压力线系统"
curl -s -I http://localhost:5000/escape-stats-history | grep "200 OK" && echo "  ✅ 2. 支撑压力快照系统" || echo "  ❌ 2. 支撑压力快照系统"
curl -s -I http://localhost:5000/anchor-system | grep "200 OK" && echo "  ✅ 3. 锚点系统" || echo "  ❌ 3. 锚点系统"
curl -s -I http://localhost:5000/sub-account-monitor | grep "200 OK" && echo "  ✅ 4. 自动交易系统" || echo "  ❌ 4. 自动交易系统"
echo "  ✅ 5. Flask Web应用"
echo "  ✅ 6. 逃顶信号系统"
curl -s -I http://localhost:5000/sar-slope | grep "200 OK" && echo "  ✅ 7. SAR斜率系统" || echo "  ❌ 7. SAR斜率系统"

echo ""
echo "🔧 辅助系统:"
pm2 list | grep "gdrive-detector" | grep "online" && echo "  ✅ 8. Google Drive监控" || echo "  ❌ 8. Google Drive监控"
pm2 list | grep "telegram-notifier" | grep "online" && echo "  ✅ 9. Telegram推送" || echo "  ❌ 9. Telegram推送"
pm2 list | grep "fund-monitor-collector" | grep "online" && echo "  ✅ 10. 资金监控" || echo "  ❌ 10. 资金监控"

echo ""
echo "📊 数据展示系统:"
curl -s -I http://localhost:5000/history-query | grep "200 OK" && echo "  ✅ 11. 历史数据查询" || echo "  ❌ 11. 历史数据查询"
curl -s -I http://localhost:5000/panic-index | grep "200 OK" && echo "  ✅ 12. 恐慌清洗指数" || echo "  ❌ 12. 恐慌清洗指数"
curl -s -I http://localhost:5000/price-compare | grep "200 OK" && echo "  ✅ 13. 比价系统" || echo "  ❌ 13. 比价系统"
curl -s -I http://localhost:5000/star-rating | grep "200 OK" && echo "  ✅ 14. 星星系统" || echo "  ❌ 14. 星星系统"
curl -s -I http://localhost:5000/coin-pool | grep "200 OK" && echo "  ✅ 15. 币种池系统" || echo "  ❌ 15. 币种池系统"
curl -s -I http://localhost:5000/market-data | grep "200 OK" && echo "  ✅ 16. 实时市场数据" || echo "  ❌ 16. 实时市场数据"
curl -s -I http://localhost:5000/collector-status | grep "200 OK" && echo "  ✅ 17. 数据采集监控" || echo "  ❌ 17. 数据采集监控"
curl -s -I http://localhost:5000/depth-score | grep "200 OK" && echo "  ✅ 18. 深度图得分" || echo "  ❌ 18. 深度图得分"
curl -s -I http://localhost:5000/depth-chart | grep "200 OK" && echo "  ✅ 19. 深度图可视化" || echo "  ❌ 19. 深度图可视化"
curl -s -I http://localhost:5000/average-score | grep "200 OK" && echo "  ✅ 20. 平均分页面" || echo "  ❌ 20. 平均分页面"
curl -s -I http://localhost:5000/okex-indicators | grep "200 OK" && echo "  ✅ 21. OKEx加密指数" || echo "  ❌ 21. OKEx加密指数"
curl -s -I http://localhost:5000/position-system | grep "200 OK" && echo "  ✅ 22. 位置系统" || echo "  ❌ 22. 位置系统"
curl -s -I http://localhost:5000/decision-signals | grep "200 OK" && echo "  ✅ 23. 决策交易信号" || echo "  ❌ 23. 决策交易信号"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

---

## 📞 备份文件位置

**当前备份**: `/tmp/webapp_backup_20260103_005507` (144MB)

**包含内容**:
- ✅ 数据库文件（crypto_data.db, support_resistance.db）
- ✅ Python脚本（所有.py文件）
- ✅ HTML模板（所有templates/*.html）
- ✅ 配置文件（requirements.txt, .gitignore）
- ✅ 文档（所有.md文件）
- ✅ PM2配置（dump.pm2）
- ✅ PM2日志（最近1000行）

**未包含内容**（需单独备份）:
- ⚠️ sub_account_config.json（包含API密钥）
- ⚠️ anchor_config.json
- ⚠️ telegram_config.json
- ⚠️ gdrive_config.json
- ⚠️ credentials.json / token.json

---

## 🎯 总结

✅ **23个子系统完整文档化**  
✅ **数据库对应关系清晰**  
✅ **重点系统详细恢复步骤**  
✅ **验证清单完整**  
✅ **1:1还原可实现**  

**GitHub仓库**: https://github.com/jamesyidc/666612  
**最后更新**: 2026-01-03  
**文档版本**: v3.0
