# 数据库表结构详细说明

**生成时间**: 2026-01-02  
**版本**: v1.0

---

## 数据库文件列表

1. **crypto_data.db** - 主数据库（位置: `databases/crypto_data.db`）
2. **support_resistance.db** - 支撑压力线数据库（位置: 根目录）
3. **panic_index.db** - 恐慌指数数据库（位置: `databases/panic_index.db`）
4. **gdrive_monitor.db** - Google Drive监控数据库（位置: `databases/gdrive_monitor.db`）
5. **market_data.db** - 市场数据数据库（位置: `databases/market_data.db`）

---

## 1. crypto_data.db

### escape_signal_stats (逃顶信号统计表) - **核心表**
**记录数**: 6条  
**用途**: 存储前端每分钟上报的逃顶信号数统计

| 列名 | 类型 | 非空 | 主键 | 说明 |
|------|------|------|------|------|
| id | INTEGER | 否 | 是 | 自增主键 |
| stat_time | TEXT | 是 | 否 | 统计时间（北京时间） |
| signal_24h_count | INTEGER | 否 | 否 | 24小时逃顶信号数 |
| signal_2h_count | INTEGER | 否 | 否 | 2小时逃顶信号数 |
| created_at | TIMESTAMP | 否 | 否 | 创建时间 |

**索引**: `idx_escape_signal_stats_time ON stat_time`

**示例数据**:
```sql
INSERT INTO escape_signal_stats (stat_time, signal_24h_count, signal_2h_count)
VALUES ('2026-01-02 22:08:27', 251, 2);
```

---

### escape_snapshot_stats (逃顶快照统计表) - **旧表，保留用于兼容**
**记录数**: 485条  
**用途**: 旧的快照统计数据（已被escape_signal_stats替代）

| 列名 | 类型 | 非空 | 主键 | 说明 |
|------|------|------|------|------|
| id | INTEGER | 否 | 是 | 自增主键 |
| stat_time | TEXT | 是 | 否 | 统计时间 |
| escape_24h_count | INTEGER | 是 | 否 | 24小时逃顶快照数 |
| escape_2h_count | INTEGER | 是 | 否 | 2小时逃顶快照数 |
| max_escape_24h | INTEGER | 是 | 否 | 24小时最大值 |
| max_escape_2h | INTEGER | 是 | 否 | 2小时最大值 |
| created_at | TIMESTAMP | 否 | 否 | 创建时间 |

---

### okex_technical_indicators (OKEx技术指标表)
**记录数**: 0条  
**用途**: 存储技术指标（RSI, SAR, 布林带等）

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| symbol | TEXT | 交易对符号 |
| timeframe | TEXT | 时间周期 |
| current_price | REAL | 当前价格 |
| rsi_14 | REAL | RSI指标(14) |
| sar | REAL | SAR指标 |
| sar_position | TEXT | SAR位置 |
| sar_quadrant | INTEGER | SAR象限 |
| sar_count_label | TEXT | SAR计数标签 |
| bb_upper | REAL | 布林带上轨 |
| bb_middle | REAL | 布林带中轨 |
| bb_lower | REAL | 布林带下轨 |
| record_time | TEXT | 记录时间 |
| created_at | TIMESTAMP | 创建时间 |

---

## 2. support_resistance.db

### support_resistance_levels (支撑压力线主表) - **核心表**
**记录数**: 294,799条  
**用途**: 存储实时计算的支撑压力线数据

| 列名 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| symbol | TEXT | 交易对符号（非空） |
| current_price | REAL | 当前价格 |
| support_line_1 | REAL | 支撑线1（7天最低） |
| support_line_2 | REAL | 支撑线2（48小时最低） |
| resistance_line_1 | REAL | 压力线1（7天最高） |
| resistance_line_2 | REAL | 压力线2（48小时最高） |
| support_1_days | INTEGER | 支撑线1天数 |
| support_2_hours | INTEGER | 支撑线2小时数 |
| resistance_1_days | INTEGER | 压力线1天数 |
| resistance_2_hours | INTEGER | 压力线2小时数 |
| distance_to_support_1 | REAL | 到支撑线1的距离（%） |
| distance_to_support_2 | REAL | 到支撑线2的距离（%） |
| distance_to_resistance_1 | REAL | 到压力线1的距离（%） |
| distance_to_resistance_2 | REAL | 到压力线2的距离（%） |
| position_s2_r1 | REAL | S2-R1位置 |
| position_s1_r2 | REAL | S1-R2位置 |
| position_s1_r2_upper | REAL | S1-R2上部位置 |
| position_s1_r1 | REAL | S1-R1位置 |
| alert_scenario_1 | INTEGER | 场景1告警（接近S2） |
| alert_scenario_2 | INTEGER | 场景2告警（接近S1） |
| alert_scenario_3 | INTEGER | 场景3告警（接近R2） |
| alert_scenario_4 | INTEGER | 场景4告警（接近R1） |
| alert_triggered | INTEGER | 告警触发标志 |
| position_7d | REAL | 7天位置 |
| position_48h | REAL | 48小时位置 |
| alert_7d_low | INTEGER | 7天低点告警 |
| alert_7d_high | INTEGER | 7天高点告警 |
| alert_48h_low | INTEGER | 48小时低点告警 |
| alert_48h_high | INTEGER | 48小时高点告警 |
| price_change_24h | REAL | 24小时价格变化 |
| change_percent_24h | REAL | 24小时涨跌幅 |
| baseline_price_24h | REAL | 24小时基准价格 |
| record_time | TIMESTAMP | 记录时间 |

**4种场景说明**:
- **Scenario 1**: 接近支撑线2（48小时最低点），抄底信号
- **Scenario 2**: 接近支撑线1（7天最低点），抄底信号
- **Scenario 3**: 接近压力线2（48小时最高点），逃顶信号
- **Scenario 4**: 接近压力线1（7天最高点），逃顶信号

**逃顶信号判定**: Scenario 3 + Scenario 4 ≥ 5

---

### support_resistance_snapshots (快照表) - **核心表**
**记录数**: 11,527条  
**用途**: 每分钟快照数据，记录4种场景的币种数量

| 列名 | 类型 | 非空 | 说明 |
|------|------|------|------|
| id | INTEGER | | 主键 |
| snapshot_time | TEXT | 是 | 快照时间（北京时间） |
| snapshot_date | TEXT | 是 | 快照日期 |
| scenario_1_count | INTEGER | 否 | 场景1币种数 |
| scenario_2_count | INTEGER | 否 | 场景2币种数 |
| scenario_3_count | INTEGER | 否 | 场景3币种数 |
| scenario_4_count | INTEGER | 否 | 场景4币种数 |
| scenario_1_coins | TEXT | 否 | 场景1币种列表（JSON） |
| scenario_2_coins | TEXT | 否 | 场景2币种列表（JSON） |
| scenario_3_coins | TEXT | 否 | 场景3币种列表（JSON） |
| scenario_4_coins | TEXT | 否 | 场景4币种列表（JSON） |
| total_coins | INTEGER | 否 | 总币种数 |
| created_at | TIMESTAMP | 否 | 创建时间 |

**示例数据**:
```sql
INSERT INTO support_resistance_snapshots 
(snapshot_time, snapshot_date, scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count, total_coins)
VALUES ('2026-01-02 21:30:54', '2026-01-02', 5, 8, 1, 3, 100);
```

---

### okex_kline_ohlc (K线OHLC数据表)
**记录数**: 50,000条  
**用途**: 存储K线数据（开高低收）

| 列名 | 类型 | 非空 | 主键 | 说明 |
|------|------|------|------|------|
| symbol | TEXT | 是 | 是(1) | 交易对符号 |
| timeframe | TEXT | 是 | 是(2) | 时间周期 |
| timestamp | INTEGER | 是 | 是(3) | 时间戳 |
| open | REAL | 否 | 否 | 开盘价 |
| high | REAL | 否 | 否 | 最高价 |
| low | REAL | 否 | 否 | 最低价 |
| close | REAL | 否 | 否 | 收盘价 |
| volume | REAL | 否 | 否 | 成交量 |
| created_at | TEXT | 否 | 否 | 创建时间 |

**复合主键**: (symbol, timeframe, timestamp)

---

### daily_baseline_prices (每日基准价格表)
**记录数**: 405条  
**用途**: 存储每日0点的基准价格

| 列名 | 类型 | 非空 | 说明 |
|------|------|------|------|
| id | INTEGER | | 主键 |
| symbol | TEXT | 是 | 交易对符号 |
| baseline_date | DATE | 是 | 基准日期 |
| baseline_price | REAL | 是 | 基准价格 |
| baseline_time | TIMESTAMP | 是 | 基准时间 |
| created_at | TIMESTAMP | 否 | 创建时间 |

---

## 数据关系图

```
support_resistance.db
├── support_resistance_levels (实时数据)
│   └── 每条记录包含当前价格和4条支撑压力线
│
├── support_resistance_snapshots (每分钟快照)
│   └── 记录4种场景的币种数量
│
├── okex_kline_ohlc (K线数据)
│   └── 用于计算支撑压力线
│
└── daily_baseline_prices (基准价格)
    └── 用于计算24小时涨跌幅

crypto_data.db
├── escape_signal_stats (信号统计)
│   └── 前端每分钟上报
│       ├── signal_24h_count (24小时信号数)
│       └── signal_2h_count (2小时信号数)
│
└── escape_snapshot_stats (旧表，保留)
```

---

## 重要SQL查询示例

### 1. 获取最新的逃顶信号统计
```sql
SELECT * FROM escape_signal_stats 
ORDER BY stat_time DESC 
LIMIT 1;
```

### 2. 获取历史最大值
```sql
SELECT 
    MAX(signal_24h_count) as max_24h,
    MAX(signal_2h_count) as max_2h
FROM escape_signal_stats;
```

### 3. 获取最新的支撑压力线快照
```sql
SELECT * FROM support_resistance_snapshots 
ORDER BY snapshot_time DESC 
LIMIT 1;
```

### 4. 统计某日期的快照数据
```sql
SELECT 
    COUNT(*) as total_snapshots,
    AVG(scenario_3_count + scenario_4_count) as avg_escape_count
FROM support_resistance_snapshots 
WHERE snapshot_date = '2026-01-02';
```

### 5. 查询当前逃顶信号的币种
```sql
SELECT symbol, current_price, 
       distance_to_resistance_1, distance_to_resistance_2
FROM support_resistance_levels 
WHERE alert_scenario_3 = 1 OR alert_scenario_4 = 1
ORDER BY record_time DESC;
```

---

## 数据备份与恢复

### 备份数据库
```bash
# 导出为SQL
sqlite3 databases/crypto_data.db .dump > crypto_data_backup.sql
sqlite3 support_resistance.db .dump > support_resistance_backup.sql

# 复制数据库文件
cp databases/crypto_data.db /backup/
cp support_resistance.db /backup/
```

### 恢复数据库
```bash
# 从SQL恢复
sqlite3 databases/crypto_data.db < crypto_data_backup.sql
sqlite3 support_resistance.db < support_resistance_backup.sql

# 从文件恢复
cp /backup/crypto_data.db databases/
cp /backup/support_resistance.db ./
```

---

## 数据维护建议

### 定期清理旧数据
```sql
-- 清理3个月前的支撑压力线数据
DELETE FROM support_resistance_levels 
WHERE record_time < datetime('now', '-3 months');

-- 清理3个月前的快照数据
DELETE FROM support_resistance_snapshots 
WHERE snapshot_time < datetime('now', '-3 months');

-- 清理3个月前的K线数据
DELETE FROM okex_kline_ohlc 
WHERE timestamp < strftime('%s', 'now', '-3 months') * 1000;
```

### 优化数据库
```sql
-- 重建索引
REINDEX;

-- 分析表
ANALYZE;

-- 清理碎片
VACUUM;
```

### 检查数据完整性
```sql
-- 检查表结构
PRAGMA integrity_check;

-- 检查记录数
SELECT 'escape_signal_stats' as table_name, COUNT(*) as count FROM escape_signal_stats
UNION ALL
SELECT 'support_resistance_snapshots', COUNT(*) FROM support_resistance_snapshots
UNION ALL
SELECT 'support_resistance_levels', COUNT(*) FROM support_resistance_levels;
```

---

**最后更新**: 2026-01-02  
**文档版本**: v1.0
