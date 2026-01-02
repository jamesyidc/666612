# 🚀 系统备份与恢复文档

## 📚 文档列表

### 1. 系统完整恢复指南
**文件**: `SYSTEM_RECOVERY_GUIDE.md`  
**内容**:
- 23个子系统详细说明
- 恢复步骤（分6个阶段）
- PM2进程配置
- 重点系统详解（SAR斜率、历史数据查询、恐慌清洗指数、支撑压力线、锚点、自动交易）
- 故障排查指南
- 验证清单

### 2. 数据库结构文档
**文件**: `DATABASE_SCHEMA.md`  
**内容**:
- 所有数据库表结构
- 字段说明
- 数据关系图
- SQL查询示例
- 备份与恢复方法
- 数据维护建议

## 🎯 23个子系统清单

1. ⭐⭐⭐ 历史数据查询系统
2. ⭐⭐⭐⭐ 交易信号监控系统
3. ⭐⭐⭐⭐⭐ 恐慌清洗指数系统
4. ⭐⭐⭐ 比价系统
5. ⭐⭐⭐ 星星系统
6. ⭐⭐⭐ 币种池系统
7. ⭐⭐⭐⭐ 实时市场原始数据
8. ⭐⭐⭐ 数据采集监控
9. ⭐⭐⭐ 深度图得分
10. ⭐⭐⭐ 深度图可视化
11. ⭐⭐⭐ 平均分页面
12. ⭐⭐⭐ OKEx加密指数
13. ⭐⭐⭐⭐ 位置系统
14. ⭐⭐⭐⭐⭐ **支撑压力线系统** (重点)
15. ⭐⭐⭐⭐ 决策交易信号系统
16. ⭐⭐⭐ 决策K线指标系统
17. ⭐⭐⭐ V1V2成交系统
18. ⭐⭐⭐ 1分钟涨跌幅系统
19. ⭐⭐⭐ Google Drive监控系统
20. ⭐⭐⭐⭐ Telegram消息推送系统
21. ⭐⭐⭐ 资金监控系统
22. ⭐⭐⭐⭐⭐ **锚点系统** (重点)
23. ⭐⭐⭐⭐⭐ **自动交易系统** (重点)

## 💾 核心数据库

### crypto_data.db (`databases/crypto_data.db`)
- `escape_signal_stats` - 逃顶信号统计 ⭐⭐⭐⭐⭐
- `anchor_records` - 锚点记录
- `anchor_profit_records` - 利润记录
- `trading_orders` - 交易订单
- `sub_accounts` - 子账户信息
- `current_positions` - 当前持仓

### support_resistance.db (根目录)
- `support_resistance_levels` - 支撑压力线主表 ⭐⭐⭐⭐⭐
- `support_resistance_snapshots` - 快照表 ⭐⭐⭐⭐⭐
- `okex_kline_ohlc` - K线OHLC数据
- `daily_baseline_prices` - 每日基准价格

## 🔧 快速恢复步骤

### 1. 克隆仓库
```bash
git clone https://github.com/jamesyidc/666612.git /home/user/webapp
cd /home/user/webapp
```

### 2. 安装依赖
```bash
pip3 install -r requirements.txt
```

### 3. 恢复数据库
```bash
# 从备份恢复（如果有）
cp /backup/databases/*.db databases/
cp /backup/support_resistance.db ./

# 或从SQL dump恢复
sqlite3 databases/crypto_data.db < crypto_data_backup.sql
sqlite3 support_resistance.db < support_resistance_backup.sql
```

### 4. 恢复配置文件
```bash
# 重要！必须恢复这些配置
cp /backup/sub_account_config.json ./
cp /backup/anchor_config.json ./
cp /backup/telegram_config.json ./
cp /backup/gdrive_config.json ./
```

### 5. 启动核心进程
```bash
# Flask主应用
pm2 start app_new.py --name flask-app --interpreter python3

# 支撑压力线系统
pm2 start support_resistance_collector.py --name support-resistance-collector --interpreter python3
pm2 start support_snapshot_collector.py --name support-snapshot-collector --interpreter python3

# 锚点系统
pm2 start anchor_maintenance.py --name anchor-maintenance --interpreter python3
pm2 start anchor_profit_tracker.py --name profit-extremes-tracker --interpreter python3

# 自动交易系统
pm2 start sub_account_opener.py --name sub-account-opener --interpreter python3
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance --interpreter python3

# 监控系统
pm2 start gdrive_detector.py --name gdrive-detector --interpreter python3
pm2 start telegram_notifier.py --name telegram-notifier --interpreter python3

# 保存配置
pm2 save
```

### 6. 验证系统
```bash
# 检查进程
pm2 list

# 检查主页面
curl http://localhost:5000/

# 检查支撑压力线系统
curl http://localhost:5000/support-resistance
curl http://localhost:5000/api/support-resistance/latest

# 检查逃顶信号统计
curl http://localhost:5000/api/support-resistance/escape-signal-stats

# 检查锚点系统
curl http://localhost:5000/anchor-system
curl http://localhost:5000/api/anchor-system/status

# 检查数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_snapshots;"
```

## ⚠️ 重要注意事项

### 必须恢复的配置文件
1. **sub_account_config.json** - 包含OKX API密钥（极其重要！）
2. **anchor_config.json** - 锚点系统配置
3. **telegram_config.json** - Telegram推送配置
4. **gdrive_config.json** - Google Drive监控配置

### 数据库优先级
1. ⭐⭐⭐⭐⭐ **crypto_data.db**  
   - `escape_signal_stats`（逃顶信号）
   - 锚点相关表
   - 交易相关表

2. ⭐⭐⭐⭐⭐ **support_resistance.db**  
   - `support_resistance_levels`
   - `support_resistance_snapshots`
   - `okex_kline_ohlc`

### PM2进程优先级
1. ⭐⭐⭐⭐⭐ `flask-app` - 主应用
2. ⭐⭐⭐⭐⭐ `support-resistance-collector` - 支撑压力线采集
3. ⭐⭐⭐⭐⭐ `support-snapshot-collector` - 快照采集
4. ⭐⭐⭐⭐⭐ `anchor-maintenance` - 锚点维护
5. ⭐⭐⭐⭐ `sub-account-opener` - 自动交易
6. ⭐⭐⭐ 其他采集器

## 📖 详细文档

查看完整文档：
- 系统恢复: `SYSTEM_RECOVERY_GUIDE.md`
- 数据库结构: `DATABASE_SCHEMA.md`

## 🆘 问题排查

如遇问题，请：
1. 查看 `SYSTEM_RECOVERY_GUIDE.md` 的"故障排查"部分
2. 检查PM2日志: `pm2 logs <process-name>`
3. 检查数据库连接: `sqlite3 databases/crypto_data.db "SELECT 1;"`
4. 验证配置文件: `cat sub_account_config.json`

---

**创建时间**: 2026-01-02  
**版本**: v1.0  
**维护**: 加密货币交易分析系统团队
