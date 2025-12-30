# 系统恢复快速参考卡

**备份文件**: `system_backup_20251230_031615.tar.gz` (3.4GB)  
**备份时间**: 2025-12-30 03:16:15

---

## 🚀 5分钟快速恢复

### Step 1: 解压 (1分钟)
```bash
cd /tmp
tar xzf system_backup_20251230_031615.tar.gz
```

### Step 2: 恢复数据库 (1分钟) ⭐
```bash
cp /tmp/system_backup_20251230_031615/databases/*.db /home/user/webapp/
```

### Step 3: 恢复源代码 (1分钟)
```bash
cp -r /tmp/system_backup_20251230_031615/source_code/* /home/user/webapp/
```

### Step 4: 恢复Git (30秒)
```bash
cd /home/user/webapp
tar xzf /tmp/system_backup_20251230_031615/git/git_repository_complete.tar.gz
```

### Step 5: 更新配置 (1分钟)
```bash
cd /home/user/webapp
nano okex_config.json      # 更新API密钥
nano telegram_config.json  # 更新TG Token
```

### Step 6: 启动系统 (30秒)
```bash
cd /home/user/webapp
pm2 resurrect
pm2 list
```

---

## 📋 重点系统恢复验证

### 锚点系统⭐⭐⭐
```bash
# 数据库验证
sqlite3 anchor_system.db "SELECT COUNT(*) FROM anchor_profit_records;"

# 进程验证
pm2 list | grep anchor

# API验证
curl http://localhost:5000/api/anchor-system/status | jq .

# 页面验证
curl http://localhost:5000/anchor-system-real
```

### SAR斜率系统⭐⭐
```bash
# 数据库验证
sqlite3 sar_slope_data.db "SELECT COUNT(*) FROM sar_slope_cycles;"

# 进程验证
pm2 list | grep sar

# API验证
curl "http://localhost:5000/api/sar-slope/current-cycle/BTC-USDT-SWAP" | jq .
```

### 历史数据查询系统⭐
```bash
sqlite3 crypto_data.db "SELECT COUNT(*) FROM crypto_index_data;"
pm2 logs crypto-index-collector --lines 20
```

### 恐慌清洗指数系统⭐
```bash
sqlite3 crypto_data.db "SELECT COUNT(*) FROM panic_wash_index;"
pm2 logs panic-wash-collector --lines 20
```

### 支撑压力线系统⭐⭐
```bash
sqlite3 support_resistance.db ".tables"
pm2 list | grep support-resistance
curl http://localhost:5000/api/support-resistance/lines | jq .
```

### 自动交易系统⭐
```bash
sqlite3 trading_decision.db "SELECT * FROM conditional_orders WHERE status='ACTIVE';"
pm2 list | grep -E "conditional|position|daemon"
```

---

## 🗂️ 数据库对应表速查

| 数据库 | 核心表 | 用途 |
|--------|--------|------|
| **anchor_system.db** | `anchor_profit_records` | 锚点持仓记录 |
| | `anchor_extreme_values` | 极值记录(TG推送) |
| **sar_slope_data.db** | `sar_slope_cycles` | SAR周期数据 |
| | `sar_bias_trend` | SAR偏离趋势 |
| **support_resistance.db** | `support_resistance_lines` | 支撑压力线 |
| | `escape_top_stats` | 逃顶统计 |
| **crypto_data.db** | `crypto_index_data` | K线历史数据 |
| | `panic_wash_index` | 恐慌清洗指数 |
| | `position_data` | 持仓数据 |
| **trading_decision.db** | `conditional_orders` | 条件单 |
| | `decision_signals` | 决策信号 |
| **signal_data.db** | `trading_signals` | 交易信号 |
| **v1v2_data.db** | `v1v2_trades` | V1V2成交 |
| **fund_monitor.db** | `fund_flow` | 资金流向 |
| **count_monitor.db** | `count_records` | 计次记录 |
| **price_speed_data.db** | `price_changes` | 价格变化 |

---

## 🔧 PM2进程启动命令

### 核心进程
```bash
pm2 start app_new.py --name flask-app
pm2 start anchor_system.py --name anchor-system
pm2 start anchor_maintenance_daemon.py --name anchor-maintenance-daemon
pm2 start anchor_opener_daemon.py --name anchor-opener-daemon
```

### 采集器进程
```bash
pm2 start crypto_index_collector.py --name crypto-index-collector
pm2 start sar_slope_collector.py --name sar-slope-collector
pm2 start sar_bias_trend_collector.py --name sar-bias-trend-collector
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_resistance_snapshot_collector.py --name support-resistance-snapshot-collector
pm2 start panic_wash_collector.py --name panic-wash-collector
pm2 start position_system_collector.py --name position-system-collector
pm2 start v1v2_collector.py --name v1v2-collector
pm2 start fund_monitor_collector.py --name fund-monitor-collector
pm2 start count_monitor.py --name count-monitor
pm2 start price_comparison_collector.py --name price-comparison-collector
```

### 监控和守护进程
```bash
pm2 start collector_monitor.py --name collector-monitor
pm2 start telegram_notifier.py --name telegram-notifier
pm2 start conditional_order_monitor.py --name conditional-order-monitor
pm2 start position_sync_fast.py --name position-sync-fast
pm2 start long_position_daemon.py --name long-position-daemon
pm2 start sync_indicators_daemon.py --name sync-indicators-daemon
```

### Google Drive进程
```bash
pm2 start gdrive_monitor.py --name gdrive-monitor
pm2 start gdrive_detector.py --name gdrive-detector
pm2 start gdrive_auto_trigger.py --name gdrive-auto-trigger
```

### 一键启动所有
```bash
pm2 resurrect
```

---

## 🧪 一键验证脚本

```bash
#!/bin/bash
echo "=== 系统恢复验证 ==="

# 数据库
echo "[1/6] 数据库..."
ls -lh /home/user/webapp/*.db | wc -l | xargs echo "  找到 {} 个数据库"

# 进程
echo "[2/6] PM2进程..."
pm2 list | grep online | wc -l | xargs echo "  {} 个进程在线"

# Flask
echo "[3/6] Flask应用..."
curl -s http://localhost:5000/ > /dev/null && echo "  ✓ Flask运行正常" || echo "  ✗ Flask未运行"

# 锚点系统
echo "[4/6] 锚点系统..."
curl -s http://localhost:5000/api/anchor-system/status > /dev/null && echo "  ✓ 锚点API正常" || echo "  ✗ 锚点API异常"

# SAR系统
echo "[5/6] SAR系统..."
curl -s "http://localhost:5000/api/sar-slope/current-cycle/BTC-USDT-SWAP" > /dev/null && echo "  ✓ SAR API正常" || echo "  ✗ SAR API异常"

# 支撑压力线
echo "[6/6] 支撑压力线..."
curl -s http://localhost:5000/api/support-resistance/lines > /dev/null && echo "  ✓ 支撑压力线API正常" || echo "  ✗ 支撑压力线API异常"

echo ""
echo "=== 验证完成 ==="
```

保存为 `quick_verify.sh`，运行：
```bash
chmod +x quick_verify.sh
./quick_verify.sh
```

---

## 🆘 常见问题快速修复

### 问题1: 数据库锁定
```bash
lsof anchor_system.db  # 查看占用进程
pm2 restart anchor-system
```

### 问题2: 进程启动失败
```bash
pm2 logs <name> --err --lines 100  # 查看错误
python3 <script>.py  # 手动测试
```

### 问题3: API返回空数据
```bash
sqlite3 <db> "SELECT COUNT(*) FROM <table>;"  # 检查数据
pm2 logs <collector-name> --lines 50  # 查看采集日志
# 等待1-5分钟让采集器运行
```

### 问题4: Flask无法访问
```bash
pm2 restart flask-app
pm2 logs flask-app --lines 200
netstat -tlnp | grep 5000  # 检查端口
```

### 问题5: TG推送不工作
```bash
# 测试TG连接
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# 测试发送消息
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" -d "text=测试"

pm2 logs telegram-notifier --lines 50
```

---

## 📁 关键文件位置

### 备份文件
- 主备份: `/tmp/system_backup_20251230_031615.tar.gz`
- MD5: `/tmp/system_backup_20251230_031615.tar.gz.md5`
- SHA256: `/tmp/system_backup_20251230_031615.tar.gz.sha256`

### 文档
- 完整恢复指南: `/tmp/system_backup_20251230_031615/docs/COMPLETE_RESTORE_GUIDE.md`
- 备份说明: `/tmp/system_backup_20251230_031615/docs/BACKUP_README.md`
- 本快速参考: `/tmp/system_backup_20251230_031615/docs/QUICK_REFERENCE.md`

### 数据库
- 所有数据库: `/tmp/system_backup_20251230_031615/databases/*.db`
- SQL转储: `/tmp/system_backup_20251230_031615/databases/*_dump.sql`
- 表结构: `/tmp/system_backup_20251230_031615/databases/*_schema.sql`

### 配置
- 所有配置: `/tmp/system_backup_20251230_031615/configs/*.json`

### 源代码
- 所有代码: `/tmp/system_backup_20251230_031615/source_code/`

---

## 🎯 恢复成功标志

✅ PM2显示24个进程在线  
✅ Flask应用正常访问（端口5000）  
✅ 锚点系统页面显示7个盈利卡片  
✅ SAR斜率图表显示  
✅ 支撑压力线统计显示  
✅ 所有API端点返回数据  
✅ TG推送功能正常  

**当以上全部✅时，恢复成功！**

---

**打印此卡片，放在手边，随时查阅！**

**文档路径**: `/tmp/system_backup_20251230_031615/docs/QUICK_REFERENCE.md`  
**创建时间**: 2025-12-30 03:25  
**版本**: v1.0
