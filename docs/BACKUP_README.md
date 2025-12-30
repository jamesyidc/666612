# 系统完整备份说明文档

**备份时间**: 2025-12-30 03:16:15  
**备份版本**: v2.0-完整版  
**备份大小**: 3.4GB  
**备份位置**: `/tmp/system_backup_20251230_031615.tar.gz`

---

## 📦 备份文件说明

### 主备份文件
- **文件名**: `system_backup_20251230_031615.tar.gz`
- **大小**: 3.4GB  
- **MD5**: 见 `system_backup_20251230_031615.tar.gz.md5`
- **SHA256**: 见 `system_backup_20251230_031615.tar.gz.sha256`

### 备份内容概览

```
system_backup_20251230_031615.tar.gz
│
├── databases/                       # 10个数据库 + SQL转储 + 表结构
│   ├── anchor_system.db (13MB) ⭐
│   ├── sar_slope_data.db (505MB) ⭐
│   ├── support_resistance.db (0KB) ⭐
│   ├── crypto_data.db (1.9GB)
│   ├── signal_data.db (16KB)
│   ├── trading_decision.db (4.2MB)
│   ├── v1v2_data.db (12MB)
│   ├── fund_monitor.db (42MB)
│   ├── count_monitor.db (16KB)
│   ├── price_speed_data.db (24KB)
│   ├── *_dump.sql (SQL转储文件)
│   ├── *_schema.sql (表结构文件)
│   └── *_tables.txt (表名列表)
│
├── source_code/                     # 完整源代码
│   ├── *.py (100+ Python文件)
│   ├── templates/ (HTML模板)
│   ├── static/ (CSS/JS/图片)
│   ├── requirements.txt
│   └── ... (所有源代码文件)
│
├── git/                             # Git完整仓库 (2.9GB)
│   ├── git_repository_complete.tar.gz
│   ├── git_recent_commits.txt
│   ├── git_branches.txt
│   ├── git_remotes.txt
│   └── git_status.txt
│
├── configs/                         # 所有配置文件
│   ├── anchor_config.json ⭐
│   ├── telegram_config.json ⭐
│   ├── okex_config.json (需更新密钥)
│   ├── fund_monitor_config.json
│   ├── trading_config.json
│   ├── v1v2_settings.json
│   ├── daily_folder_config.json
│   └── ... (所有*.json配置)
│
├── pm2/                             # PM2进程配置
│   ├── dump.pm2
│   ├── pm2_list.txt
│   ├── pm2_flask-app_details.txt
│   ├── pm2_anchor-system_details.txt
│   └── pm2_prettylist.json
│
├── logs/                            # 日志文件
│   ├── app_logs/                    # 应用日志 (15个)
│   │   ├── crypto_index_collector.log
│   │   ├── panic_wash_collector.log
│   │   ├── support_resistance.log
│   │   ├── v1v2_collector.log
│   │   └── ...
│   ├── pm2_logs/                    # PM2日志
│   └── system_logs/                 # 系统日志
│       └── syslog_recent.txt
│
├── dependencies/                    # 依赖清单
│   ├── requirements.txt (Python)
│   ├── pip_list.txt
│   ├── python_version.txt
│   ├── package.json (Node.js)
│   ├── npm_list.txt
│   └── node_version.txt
│
├── cache/                           # 缓存数据
│
├── docs/                            # 文档
│   ├── COMPLETE_RESTORE_GUIDE.md ⭐ (64KB)
│   └── BACKUP_README.md (本文档)
│
├── SYSTEM_INFO.txt                  # 系统信息
├── BACKUP_METADATA.json             # 备份元数据
└── FILE_MANIFEST.txt                # 完整文件清单

```

---

## 🎯 23个子系统完整清单

### 数据采集层 (11个)

| # | 系统名称 | PM2进程 | 源代码 | 数据库 | 表名 | 状态 |
|---|---------|---------|--------|--------|------|------|
| 1 | 历史数据查询系统 | `crypto-index-collector` | `crypto_index_collector.py` | `crypto_data.db` | `crypto_index_data` | ✅ |
| 2 | 交易信号监控系统 | `collector-monitor` | `collector_monitor.py` | `signal_data.db` | `trading_signals`, `signal_analysis` | ✅ |
| 3 | 恐慌清洗指数系统⭐ | `panic-wash-collector` | `panic_wash_collector.py` | `crypto_data.db` | `panic_wash_index` | ✅ |
| 4 | 比价系统 | `price-comparison-collector` | `price_comparison_collector.py` | `crypto_data.db` | `price_comparison` | ✅ |
| 5 | SAR斜率系统⭐⭐ | `sar-slope-collector` | `sar_slope_collector.py` | `sar_slope_data.db` | `sar_slope_cycles`, `sar_slope_analysis` | ✅ |
| 6 | SAR偏离趋势 | `sar-bias-trend-collector` | `sar_bias_trend_collector.py` | `sar_slope_data.db` | `sar_bias_trend` | ✅ |
| 7 | 币种池系统 | (集成在Flask) | `app_new.py` | `crypto_data.db` | `coin_pool` | ✅ |
| 8 | 实时市场数据 | `websocket-collector` | `websocket_collector.py` | `crypto_data.db` | `realtime_market_data` | ⚠️ |
| 9 | 深度图得分 | (集成在Flask) | `app_new.py` | - | - | ✅ |
| 10 | 深度图可视化 | (前端) | `templates/depth_chart.html` | - | - | ✅ |
| 11 | 平均分页面 | (前端) | `templates/average_score.html` | - | - | ✅ |

### 数据处理层 (6个)

| # | 系统名称 | PM2进程 | 源代码 | 数据库 | 表名 | 状态 |
|---|---------|---------|--------|--------|------|------|
| 12 | OKEx加密指数 | (集成在历史数据系统) | `crypto_index_collector.py` | `crypto_data.db` | - | ✅ |
| 13 | 位置系统 | `position-system-collector` | `position_system_collector.py` | `crypto_data.db` | `position_data`, `position_history` | ✅ |
| 14 | 支撑压力线系统⭐⭐ | `support-resistance-collector`, `support-resistance-snapshot-collector` | `support_resistance_collector.py`, `support_resistance_snapshot_collector.py` | `support_resistance.db` | `support_resistance_lines`, `escape_top_stats`, `bargain_hunting_stats` | ✅ |
| 15 | 决策交易信号系统 | (集成在Flask) | `trading_decision_system.py` | `trading_decision.db` | `decision_signals`, `signal_performance` | ✅ |
| 16 | K线指标系统 | (集成在Flask) | `app_new.py` | - | - | ✅ |
| 17 | V1V2成交系统 | `v1v2-collector` | `v1v2_collector.py` | `v1v2_data.db` | `v1v2_trades` | ✅ |
| 18 | 1分钟涨跌幅系统 | (集成在Flask) | `price_speed_collector.py` | `price_speed_data.db` | `price_changes` | ✅ |

### 业务应用层 (6个)

| # | 系统名称 | PM2进程 | 源代码 | 数据库 | 表名 | 状态 |
|---|---------|---------|--------|--------|------|------|
| 19 | Google Drive监控 | `gdrive-monitor`, `gdrive-detector`, `gdrive-auto-trigger` | `gdrive_monitor.py`, `gdrive_detector.py`, `gdrive_auto_trigger.py` | Google Drive API | - | ✅ |
| 20 | TG消息推送系统 | `telegram-notifier` | `telegram_notifier.py` | - | - | ✅ |
| 21 | 资金监控系统 | `fund-monitor-collector` | `fund_monitor_collector.py` | `fund_monitor.db` | `fund_flow`, `account_balance` | ✅ |
| 22 | 锚点系统⭐⭐⭐ | `anchor-system`, `anchor-maintenance-daemon`, `anchor-opener-daemon` | `anchor_system.py`, `anchor_maintenance_daemon.py`, `anchor_opener_daemon.py` | `anchor_system.db` | `anchor_profit_records`, `anchor_monitors`, `anchor_alerts`, `anchor_extreme_values`, `anchor_maintenance_log`, `opening_logic_suggestions` | ✅ |
| 23 | 自动交易系统⭐ | `conditional-order-monitor`, `position-sync-fast`, `long-position-daemon`, `sync-indicators-daemon` | `conditional_order_monitor.py`, `position_sync_fast.py`, `long_position_daemon.py`, `sync_indicators_daemon.py` | `trading_decision.db`, `crypto_data.db` | `conditional_orders`, `order_execution_log` | ✅ |

### 额外系统

| # | 系统名称 | PM2进程 | 源代码 | 数据库 | 表名 | 状态 |
|---|---------|---------|--------|--------|------|------|
| 24 | 计次监控系统 | `count-monitor` | `count_monitor.py` | `count_monitor.db` | `count_records` | ✅ |
| 25 | Flask Web应用 | `flask-app` | `app_new.py` | (所有数据库) | - | ✅ |

**总计**: 25个系统，24个在线（1个websocket-collector状态异常但不影响主要功能）

---

## 💾 10个数据库详细说明

### 1. anchor_system.db ⭐⭐⭐ (13MB)
**用途**: 锚点系统专用  
**重要性**: 🔥🔥🔥 极其重要  
**表数量**: 6个

**表结构**:
```
anchor_profit_records      # 当前持仓盈亏记录（核心表）
  - inst_id (币种合约ID)
  - pos_side (long/short)
  - pos_size (持仓量)
  - profit_rate (盈利率%)
  - record_type (highest_profit/max_loss)
  - timestamp

anchor_monitors            # 监控记录
anchor_alerts              # 告警记录  
anchor_extreme_values      # 极值记录（TG推送）
anchor_maintenance_log     # 维护日志
opening_logic_suggestions  # 开仓建议
```

**关键数据**:
- 当前持仓: 29个空单
- 盈利≥40%: 8个
- 亏损: 15个

---

### 2. sar_slope_data.db ⭐⭐ (505MB)
**用途**: SAR斜率系统（星星系统）  
**重要性**: 🔥🔥 非常重要  
**表数量**: 3个

**表结构**:
```
sar_slope_cycles      # SAR周期数据
  - symbol
  - cycle_type (UP/DOWN)
  - slope (斜率)
  - duration_minutes
  
sar_slope_analysis    # 斜率分析
sar_bias_trend        # 偏离趋势
```

---

### 3. support_resistance.db ⭐⭐ (0KB - 新建或空)
**用途**: 支撑压力线系统  
**重要性**: 🔥🔥 非常重要  
**表数量**: 4个

**表结构**:
```
support_resistance_lines      # 支撑压力线
support_resistance_snapshots  # 历史快照
escape_top_stats              # 逃顶统计
bargain_hunting_stats         # 抄底统计
```

---

### 4. crypto_data.db (1.9GB)
**用途**: 主数据库，存储所有加密货币基础数据  
**重要性**: 🔥🔥🔥 极其重要  
**表数量**: 10+个

**主要表**:
```
crypto_index_data         # K线历史数据
panic_wash_index          # 恐慌清洗指数
price_comparison          # 价格对比
position_data             # 持仓数据
realtime_market_data      # 实时行情
coin_pool                 # 币种池
...
```

---

### 5. signal_data.db (16KB)
**用途**: 交易信号和采集器监控  
**表**: `trading_signals`, `signal_analysis`, `collector_status`

---

### 6. trading_decision.db (4.2MB)
**用途**: 交易决策和自动交易  
**表**: `decision_signals`, `signal_performance`, `conditional_orders`, `order_execution_log`

---

### 7. v1v2_data.db (12MB)
**用途**: V1/V2成交系统  
**表**: `v1v2_trades`

---

### 8. fund_monitor.db (42MB)
**用途**: 资金监控  
**表**: `fund_flow`, `account_balance`

---

### 9. count_monitor.db (16KB)
**用途**: 计次监控  
**表**: `count_records`

---

### 10. price_speed_data.db (24KB)
**用途**: 1分钟涨跌幅  
**表**: `price_changes`

---

## 🔑 关键配置文件说明

### anchor_config.json ⭐⭐⭐
```json
{
  "monitor": {
    "profit_target": 40.0,      # 盈利目标(%)
    "loss_limit": -10.0,         # 止损限制(%)
    "check_interval": 60,        # 检查间隔(秒)
    "alert_cooldown": 30         # 告警冷却(分钟)
  },
  "telegram": {
    "bot_token": "...",
    "chat_id": "...",
    "enable_extreme_alerts": true
  },
  "anchor": {
    "target_coins": ["CFX", "FIL", "CRO", "UNI", "CRV", "LDO"],
    "excluded_assets": ["BTC-USDT-SWAP", "ETH-USDT-SWAP", ...]
  }
}
```

### telegram_config.json ⭐⭐
```json
{
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID",
  "signals": {
    "buy": { "min_coins": 8 },
    "sell": { "min_coins": 8 }
  }
}
```

### okex_config.json (需更新密钥)
```json
{
  "api_key": "YOUR_API_KEY",
  "secret_key": "YOUR_SECRET_KEY",
  "passphrase": "YOUR_PASSPHRASE"
}
```

---

## 🚀 快速恢复步骤

### 1. 解压备份
```bash
cd /tmp
tar xzf system_backup_20251230_031615.tar.gz
cd system_backup_20251230_031615
```

### 2. 查看完整文档
```bash
cat docs/COMPLETE_RESTORE_GUIDE.md
```

### 3. 恢复数据库（最重要）
```bash
cd /home/user/webapp
cp /tmp/system_backup_20251230_031615/databases/*.db .
```

### 4. 恢复源代码
```bash
cp -r /tmp/system_backup_20251230_031615/source_code/* /home/user/webapp/
```

### 5. 恢复Git仓库
```bash
cd /home/user/webapp
tar xzf /tmp/system_backup_20251230_031615/git/git_repository_complete.tar.gz
```

### 6. 恢复配置文件
```bash
cp /tmp/system_backup_20251230_031615/configs/*.json /home/user/webapp/
# ⚠️ 记得更新API密钥！
nano okex_config.json
nano telegram_config.json
```

### 7. 启动PM2进程
```bash
cd /home/user/webapp
pm2 resurrect
# 或手动启动所有进程（见文档）
```

### 8. 验证系统
```bash
pm2 list
curl http://localhost:5000/
curl http://localhost:5000/api/anchor-system/status
```

---

## ⚠️ 重要提醒

### 恢复前必读
1. **检查Python版本**: 需要Python 3.8+
2. **安装依赖**: `pip install -r dependencies/requirements.txt`
3. **更新API密钥**: okex_config.json, telegram_config.json
4. **检查端口**: 确保5000端口未被占用
5. **检查防火墙**: 开放5000端口

### 数据库完整性验证
```bash
# 验证所有数据库
for db in *.db; do
    echo "检查: $db"
    sqlite3 "$db" "PRAGMA integrity_check;"
done
```

### 重点系统验证（必须100%成功）
- [ ] 锚点系统 - anchor_system.db完整，API返回数据
- [ ] SAR斜率系统 - sar_slope_data.db完整，周期数据可查
- [ ] 历史数据系统 - crypto_data.db完整，K线数据存在
- [ ] 恐慌清洗系统 - panic_wash_index表有数据
- [ ] 支撑压力线系统 - 表结构完整
- [ ] 自动交易系统 - API密钥正确配置

---

## 📊 备份统计

- **总文件数**: 10,000+ 个文件
- **数据库总大小**: 2.5GB
- **Git仓库**: 2.9GB
- **日志文件**: 230MB
- **源代码**: ~100MB
- **配置文件**: ~1MB
- **压缩后大小**: 3.4GB

---

## 📞 获取帮助

### 查看详细文档
```bash
less /tmp/system_backup_20251230_031615/docs/COMPLETE_RESTORE_GUIDE.md
```

### 查看备份元数据
```bash
cat /tmp/system_backup_20251230_031615/BACKUP_METADATA.json
```

### 查看文件清单
```bash
cat /tmp/system_backup_20251230_031615/FILE_MANIFEST.txt
```

### 查看数据库表结构
```bash
cat /tmp/system_backup_20251230_031615/databases/*_schema.sql
```

---

## ✅ 验证清单

恢复完成后，请验证以下项目：

### Level 1: 基础
- [ ] 所有.db文件存在且完整
- [ ] 所有.py文件存在
- [ ] 配置文件存在且已更新密钥
- [ ] Git仓库完整

### Level 2: 进程
- [ ] PM2显示24个进程在线
- [ ] flask-app运行正常
- [ ] anchor-system运行正常
- [ ] 采集器运行正常

### Level 3: 数据库
- [ ] 所有数据库integrity_check通过
- [ ] anchor_profit_records有数据
- [ ] sar_slope_cycles有数据
- [ ] crypto_index_data有数据

### Level 4: API
- [ ] GET /api/anchor-system/status 返回200
- [ ] GET /api/sar-slope/current-cycle/BTC-USDT-SWAP 返回数据
- [ ] GET /api/support-resistance/lines 返回数据

### Level 5: 功能
- [ ] 锚点系统页面显示7个盈利卡片
- [ ] 锚点系统状态栏正确切换
- [ ] SAR斜率图表显示
- [ ] 支撑压力线统计显示
- [ ] TG推送功能正常

---

## 🎉 完成标志

当以上所有验证清单都✅时，系统恢复成功！

您将获得一个与备份时**完全相同**的系统，包括：
- ✅ 29个空单持仓数据
- ✅ SAR周期历史数据
- ✅ 所有配置和代码
- ✅ 完整Git历史
- ✅ 所有日志文件

**部署后即可直接使用！**

---

**备份脚本**: `/tmp/COMPLETE_SYSTEM_BACKUP_2025-12-30.sh`  
**恢复文档**: `/tmp/system_backup_20251230_031615/docs/COMPLETE_RESTORE_GUIDE.md`  
**备份时间**: 2025-12-30 03:16:15 ~ 03:22:40 (耗时6分25秒)  
**制作者**: GenSpark AI Developer

---
