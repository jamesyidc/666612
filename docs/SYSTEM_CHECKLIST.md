# 系统清单和文件映射

## 📋 23个子系统完整清单

### 【重点系统】⭐ (必须恢复)

#### 1. SAR斜率系统 ⭐
- **文件**: `sar_slope_collector.py`
- **数据库**: `sar_slope_data.db` (505MB)
- **页面**: `/sar-slope`
- **PM2**: `sar-slope-collector`
- **说明**: SAR抛物线指标斜率计算和展示

#### 2. 历史数据查询系统 ⭐
- **文件**: `app_new.py` (Flask主应用)
- **数据库**: `crypto_data.db` (表: crypto_snapshots)
- **页面**: `/query`, `/escape-stats-history`
- **API**: `/api/query`, `/api/latest`, `/api/chart`
- **PM2**: `flask-app`
- **说明**: 历史市场数据查询和图表展示

#### 3. 恐慌清洗指数系统 ⭐
- **文件**: `app_new.py`
- **数据库**: `crypto_data.db` (表: panic_wash_index)
- **页面**: `/panic`
- **API**: `/api/panic/latest`
- **PM2**: `flask-app`
- **说明**: 市场恐慌情绪和清洗程度指数

#### 4. 支撑压力线系统 ⭐
- **文件**: `support_resistance_collector.py`
- **数据库**: `support_resistance.db` (148MB)
- **页面**: `/support-resistance`
- **API**: `/api/support-resistance/*`
- **PM2**: `support-resistance-collector`
- **说明**: 价格支撑位和压力位识别

#### 5. 锚点系统(实盘) ⭐
- **文件**: 
  - `anchor_system.py`
  - `sub_account_opener_daemon.py`
  - `sub_account_maintenance_checker.py`
- **数据库**: 
  - `anchor_system.db` (13MB)
  - `trading_decision.db` (4.2MB)
- **页面**: `/anchor-system-real`
- **API**: `/api/anchor-system/*`, `/api/anchor/*`
- **PM2**: 
  - `anchor-maintenance`
  - `sub-account-opener`
  - `sub-account-super-maintenance`
- **说明**: 自动化锚点交易系统，含持仓管理和维护

#### 6. 自动交易系统 (爆仓统计) ⭐
- **文件**: `sub_account_liquidation_tracker.py`
- **数据库**: `crypto_data.db` (表: sub_account_liquidations, liquidation_stats)
- **页面**: `/liquidation-stats`
- **API**: `/api/liquidation/*`
- **说明**: 子账号爆仓记录和统计分析

---

### 【数据采集系统】(7个)

#### 7. 支撑压力采集器
- **文件**: `support_resistance_collector.py`
- **数据库**: `support_resistance.db`
- **PM2**: `support-resistance-collector`

#### 8. 快照采集器
- **文件**: `support_snapshot_collector.py`
- **数据库**: `crypto_data.db`
- **PM2**: `support-snapshot-collector`

#### 9. Google Drive监控
- **文件**: `gdrive_final_detector.py`
- **配置**: `daily_folder_config.json`
- **PM2**: `gdrive-detector`
- **页面**: `/gdrive-monitor-status`

#### 10. 逃顶信号记录器
- **文件**: `escape_signal_recorder.py`
- **数据库**: `crypto_data.db` (表: escape_signal_stats)
- **PM2**: `escape-signal-recorder`

#### 11. 逃顶统计记录器
- **文件**: `escape_stats_recorder.py`
- **数据库**: `crypto_data.db` (表: escape_snapshot_stats)
- **PM2**: `escape-stats-recorder`

#### 12. 位置系统采集器
- **文件**: `position_system_collector.py`
- **数据库**: `crypto_data.db` (表: position_system)
- **PM2**: `position-system-collector`
- **页面**: `/position-system`

#### 13. SAR斜率采集器
- **文件**: `sar_slope_collector.py`
- **数据库**: `sar_slope_data.db`
- **PM2**: `sar-slope-collector`

---

### 【交易决策系统】(6个)

#### 14. 锚点维护系统
- **文件**: `sub_account_maintenance_checker.py`
- **数据库**: `anchor_system.db`, `trading_decision.db`
- **PM2**: `anchor-maintenance`

#### 15. 子账号开仓守护
- **文件**: `sub_account_opener_daemon.py`
- **数据库**: `trading_decision.db`
- **PM2**: `sub-account-opener`

#### 16. 子账号超级维护
- **文件**: `sub_account_super_maintenance.py`
- **数据库**: `trading_decision.db`
- **PM2**: `sub-account-super-maintenance`

#### 17. 利润极值追踪
- **文件**: `profit_extremes_tracker.py`
- **PM2**: `profit-extremes-tracker`

#### 18. 币对保护
- **文件**: `protect_pairs.py`
- **PM2**: `protect-pairs`

#### 19. 计次检测
- **文件**: `count_check_daemon.py`
- **数据库**: `crypto_data.db`
- **PM2**: `count-checker`
- **说明**: 每天凌晨2点检测计次，Telegram提醒

---

### 【通知系统】(1个)

#### 20. Telegram消息推送
- **PM2**: `telegram-notifier`
- **说明**: 自动发送Telegram通知

---

### 【核心服务】(2个)

#### 21. Flask Web服务
- **文件**: `app_new.py`
- **端口**: 5000
- **PM2**: `flask-app`
- **说明**: 主Web服务，提供所有API和页面

#### 22. 多单监控
- **PM2**: `long-position-monitor`

---

### 【其他数据系统】

#### 23. 比价系统
- **页面**: `/price-comparison`
- **数据库**: `crypto_data.db`

#### 24. 星星系统
- **页面**: `/star-system`

#### 25. 币种池系统
- **页面**: `/coin-pool`

#### 26. 实时市场原始数据
- **页面**: `/market-data`

#### 27. 数据采集监控
- **页面**: `/collector-monitor`

#### 28. 深度图得分
- **页面**: `/depth-score`

#### 29. 深度图可视化
- **页面**: `/depth-chart`

#### 30. 平均分页面
- **页面**: `/average-score`

#### 31. OKEx加密指数
- **数据库**: `crypto_data.db` (表: okex_technical_indicators)
- **页面**: `/crypto-index`

#### 32. 决策交易信号系统
- **数据库**: `crypto_data.db` (表: trading_signal_history)

#### 33. 决策K线指标系统
- **数据库**: `crypto_data.db` (表: okex_kline_ohlc)
- **页面**: `/kline-indicators`

#### 34. V1V2成交系统
- **数据库**: `v1v2_data.db`

#### 35. 1分钟涨跌幅系统
- **页面**: `/minute-change`

#### 36. 资金监控系统
- **数据库**: `fund_monitor.db`
- **页面**: `/fund-monitor`

---

## 📊 数据库表结构映射

### crypto_data.db (主数据库)
| 表名 | 用途 | 对应系统 |
|------|------|---------|
| crypto_snapshots | 市场快照 | 历史查询 |
| escape_snapshot_stats | 逃顶快照 | 支撑压力 |
| escape_signal_stats | 逃顶信号 | 支撑压力 |
| sub_account_liquidations | 爆仓记录 | 爆仓统计 |
| sub_account_liquidation_stats | 账号爆仓统计 | 爆仓统计 |
| coin_liquidation_stats | 币种爆仓统计 | 爆仓统计 |
| panic_wash_index | 恐慌指数 | 恐慌清洗 |
| okex_technical_indicators | 技术指标 | K线指标 |
| okex_kline_ohlc | K线数据 | K线指标 |
| price_breakthrough_events | 价格突破 | 比价系统 |
| position_system | 位置数据 | 位置系统 |
| trading_signal_history | 交易信号 | 决策信号 |

### trading_decision.db (交易决策)
| 表名 | 用途 | 对应系统 |
|------|------|---------|
| anchor_positions | 锚点持仓 | 锚点系统 |
| maintenance_operations | 维护操作 | 锚点维护 |
| sub_account_positions | 子账号持仓 | 子账号系统 |
| sub_account_extreme_maintenance | 极端维护 | 子账号维护 |

### anchor_system.db (锚点系统)
| 用途 | 对应系统 |
|------|---------|
| 锚点系统专用数据 | 锚点系统 |

### support_resistance.db (支撑压力)
| 用途 | 对应系统 |
|------|---------|
| 支撑压力线数据 | 支撑压力系统 |

### sar_slope_data.db (SAR斜率)
| 用途 | 对应系统 |
|------|---------|
| SAR斜率计算数据 | SAR斜率系统 |

### fund_monitor.db (资金监控)
| 用途 | 对应系统 |
|------|---------|
| 资金流向监控 | 资金监控系统 |

### v1v2_data.db (V1V2成交)
| 用途 | 对应系统 |
|------|---------|
| V1V2成交数据 | V1V2系统 |

---

## 🔗 文件依赖关系

### Flask主应用 (app_new.py)
**依赖**:
- 所有数据库文件
- templates/ 所有HTML文件
- static/ 所有静态资源

**提供服务**:
- 所有Web页面路由
- 所有API端点
- 静态文件服务

### 锚点系统核心 (anchor_system.py)
**依赖**:
- anchor_system.db
- trading_decision.db

**被依赖**:
- sub_account_opener_daemon.py
- sub_account_maintenance_checker.py
- app_new.py (API调用)

### 采集器群组
**共同特点**:
- 独立运行
- 写入各自数据库
- 定时采集数据
- PM2守护进程管理

**采集器列表**:
1. support_resistance_collector.py → support_resistance.db
2. sar_slope_collector.py → sar_slope_data.db
3. escape_signal_recorder.py → crypto_data.db
4. escape_stats_recorder.py → crypto_data.db
5. position_system_collector.py → crypto_data.db

---

## 🎯 恢复优先级

### P0 (最高优先级 - 必须恢复)
1. crypto_data.db (主数据库)
2. app_new.py (Flask主应用)
3. trading_decision.db (交易决策)
4. anchor_system.py (锚点核心)

### P1 (高优先级 - 核心功能)
1. sar_slope_data.db + sar_slope_collector.py
2. support_resistance.db + support_resistance_collector.py
3. sub_account_opener_daemon.py
4. sub_account_maintenance_checker.py

### P2 (中优先级 - 重要功能)
1. anchor_system.db
2. gdrive_final_detector.py
3. escape_signal_recorder.py
4. escape_stats_recorder.py
5. sub_account_liquidation_tracker.py

### P3 (低优先级 - 辅助功能)
1. fund_monitor.db
2. v1v2_data.db
3. 其他辅助脚本
4. 日志文件

---

## 📝 配置文件说明

### PM2配置 (ecosystem.*.config.js)
- `ecosystem.flask.config.js` - Flask主应用
- `ecosystem.collector.config.js` - 所有采集器
- `ecosystem.anchor.config.js` - 锚点系统
- `ecosystem.count-checker.config.js` - 计次检测

### 系统配置 (JSON)
- `daily_folder_config.json` - Google Drive每日文件夹配置
- 其他配置JSON文件

---

## ✅ 验证文件完整性

### 必需文件检查清单
```bash
# 核心Python文件
[ -f app_new.py ] && echo "✅ Flask主应用"
[ -f anchor_system.py ] && echo "✅ 锚点系统"

# 核心数据库
[ -f databases/crypto_data.db ] && echo "✅ 主数据库"
[ -f databases/trading_decision.db ] && echo "✅ 交易数据库"

# 守护进程
[ -f sub_account_opener_daemon.py ] && echo "✅ 开仓守护"
[ -f sub_account_maintenance_checker.py ] && echo "✅ 维护检查"

# 采集器
[ -f support_resistance_collector.py ] && echo "✅ 支撑压力采集"
[ -f sar_slope_collector.py ] && echo "✅ SAR采集"

# Web文件
[ -d templates ] && echo "✅ 模板目录"
[ -d static ] && echo "✅ 静态资源"

# 配置文件
[ -f daily_folder_config.json ] && echo "✅ 每日文件夹配置"
```

---

## 🎉 总结

本清单详细列出了:
- ✅ 23个核心子系统
- ✅ 12个数据库文件
- ✅ 所有关键Python脚本
- ✅ 数据库表结构映射
- ✅ 文件依赖关系
- ✅ 恢复优先级

使用本清单可以:
1. 快速定位系统对应的文件
2. 了解系统之间的依赖关系
3. 按优先级恢复系统
4. 验证备份文件完整性

**重点系统标记 ⭐ 务必优先恢复！**
