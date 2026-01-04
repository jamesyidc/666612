# 加密货币交易系统 - 完整恢复部署指南

## 📋 系统概述

**备份时间**: 2026-01-04 08:14:26  
**备份版本**: v2.0  
**系统规模**: 23个子系统  
**压缩包大小**: 518MB  
**解压后大小**: ~1.1GB  

---

## 🎯 系统架构 - 23个子系统

### 【数据采集系统】(7个)
1. **support-resistance-collector** - 支撑压力线采集器
2. **support-snapshot-collector** - 快照采集器
3. **gdrive-detector** - Google Drive监控
4. **escape-signal-recorder** - 逃顶信号记录器
5. **escape-stats-recorder** - 逃顶统计记录器
6. **position-system-collector** - 位置系统采集器
7. **sar-slope-collector** - SAR斜率采集器

### 【交易决策系统】(6个)
8. **anchor-maintenance** - 锚点维护系统 ⭐
9. **sub-account-opener** - 子账号开仓守护 ⭐
10. **sub-account-super-maintenance** - 子账号超级维护 ⭐
11. **profit-extremes-tracker** - 利润极值追踪
12. **protect-pairs** - 币对保护
13. **count-checker** - 计次检测

### 【通知系统】(1个)
14. **telegram-notifier** - Telegram消息推送 ⭐

### 【核心服务】(2个)
15. **flask-app** - Web服务(端口5000) ⭐
16. **long-position-monitor** - 多单监控

### 【Web页面】(7个重点系统)
17. **SAR斜率系统** - `/sar-slope` ⭐
18. **历史数据查询** - `/query` ⭐
19. **恐慌清洗指数** - `/panic` ⭐
20. **支撑压力线** - `/support-resistance` ⭐
21. **锚点系统(实盘)** - `/anchor-system-real` ⭐
22. **爆仓统计** - `/liquidation-stats` ⭐
23. **逃顶信号历史** - `/escape-stats-history`

> ⭐ 标记为重点系统

---

## 📦 备份内容清单

### 1. 数据库 (databases/) - 总计 724MB

#### 核心数据库 (必需)
| 数据库文件 | 大小 | 说明 | 用途系统 |
|-----------|------|------|---------|
| **crypto_data.db** | 1.1MB | 主数据库 | 历史查询、统计分析 |
| **trading_decision.db** | 4.2MB | 交易决策 | 锚点系统、自动交易 |
| **anchor_system.db** | 13MB | 锚点系统 | 锚点维护、持仓管理 |
| **support_resistance.db** | 148MB | 支撑压力 | 支撑压力线系统 |
| **sar_slope_data.db** | 505MB | SAR斜率 | SAR斜率系统 |

#### 辅助数据库
| 数据库文件 | 大小 | 说明 |
|-----------|------|------|
| fund_monitor.db | 42MB | 资金监控 |
| v1v2_data.db | 12MB | V1V2成交数据 |
| count_monitor.db | 16KB | 计次监控 |
| signal_data.db | 16KB | 信号数据 |
| price_speed_data.db | 24KB | 价格速度 |

#### 数据库表结构说明

**crypto_data.db** 包含表:
- `crypto_snapshots` - 市场快照数据
- `escape_snapshot_stats` - 逃顶快照统计
- `escape_signal_stats` - 逃顶信号统计
- `sub_account_liquidations` - 子账号爆仓记录
- `sub_account_liquidation_stats` - 账号爆仓统计
- `coin_liquidation_stats` - 币种爆仓统计
- `okex_technical_indicators` - OKEx技术指标
- `okex_kline_ohlc` - K线OHLC数据
- `price_breakthrough_events` - 价格突破事件
- `position_system` - 位置系统数据
- `trading_signal_history` - 交易信号历史
- `panic_wash_index` - 恐慌清洗指数

**trading_decision.db** 包含表:
- `anchor_positions` - 锚点持仓
- `maintenance_operations` - 维护操作记录
- `sub_account_positions` - 子账号持仓
- `sub_account_extreme_maintenance` - 极端维护记录

**anchor_system.db** 包含表:
- (锚点系统相关表)

**support_resistance.db** 包含表:
- (支撑压力线数据表)

**sar_slope_data.db** 包含表:
- (SAR斜率数据表)

### 2. 核心代码 (core_code/) - 13MB, 806个文件

#### 主应用
- **app_new.py** - Flask主应用，所有API端点
- **anchor_system.py** - 锚点系统核心逻辑

#### 守护进程 (*_daemon.py)
- `sub_account_opener_daemon.py` - 子账号开仓
- `sub_account_maintenance_checker.py` - 维护检查
- `count_check_daemon.py` - 计次检测
- `gdrive_final_detector.py` - Google Drive检测

#### 数据采集器 (*_collector.py)
- `support_resistance_collector.py` - 支撑压力采集
- `escape_signal_recorder.py` - 逃顶信号记录
- `escape_stats_recorder.py` - 逃顶统计记录
- `sar_slope_collector.py` - SAR斜率采集
- (其他采集器)

#### 追踪器和监控 (*_tracker.py, *_monitor.py)
- `sub_account_liquidation_tracker.py` - 爆仓追踪
- `profit_extremes_tracker.py` - 利润极值追踪
- (其他监控器)

#### 工具脚本
- `test_liquidation_data.py` - 测试数据生成
- `close_positions.py` - 批量平仓
- `change_to_isolated.py` - 切换逐仓模式
- (其他工具)

### 3. Web文件 (web_files/) - 3.1MB

#### 模板文件 (templates/) - 67个HTML
- `index.html` - 首页
- `query.html` / `escape_stats_history.html` - 历史查询
- `panic_new.html` - 恐慌指数
- `support_resistance.html` - 支撑压力
- `anchor_system_real.html` - 锚点系统实盘
- `sar_slope.html` - SAR斜率
- `liquidation_stats.html` - 爆仓统计
- (其他模板文件)

#### 静态文件 (static/)
- CSS样式
- JavaScript脚本
- 图片资源

### 4. 配置文件 (configs/) - 188KB, 27个文件

#### PM2配置
- `ecosystem.anchor.config.js` - 锚点系统进程
- `ecosystem.collector.config.js` - 采集器进程
- `ecosystem.count-checker.config.js` - 计次检测
- (其他PM2配置)

#### 系统配置
- `daily_folder_config.json` - 每日文件夹配置
- (其他JSON配置)

### 5. PM2进程 (pm2/) - 40KB
- `dump.pm2` - PM2进程状态
- `pm2_processes.txt` - 进程列表

### 6. Git仓库 (git/) - 364MB
- `.git/` - 完整Git仓库
- `recent_commits.txt` - 最近50次提交
- `status.txt` - Git状态
- `remotes.txt` - 远程仓库

### 7. 文档 (docs/) - 1.3MB, 134个Markdown文件
- 各系统修复文档
- 功能说明文档
- 配置文档

### 8. 日志样本 (logs_sample/) - 6.6MB
- 最近1小时的示例日志
- (用于参考和调试)

### 9. 依赖文件
- `requirements.txt` - Python依赖
- `python_version.txt` - Python版本

---

## 🚀 完整恢复步骤

### 前提条件

1. **系统要求**
   - Ubuntu 20.04+ / Debian 11+
   - Python 3.8+
   - Node.js 14+ (可选)
   - 至少 5GB 可用磁盘空间

2. **必需工具**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip git sqlite3 curl wget
   ```

3. **PM2安装**
   ```bash
   npm install -g pm2
   # 或使用pip
   pip3 install pm2
   ```

### 步骤1: 解压备份文件

```bash
# 1.1 如果是分割文件，先合并
bash merge_and_extract.sh

# 1.2 如果是完整文件，直接解压
tar -xzf crypto_system_backup_20260104_081420.tar.gz

# 1.3 进入备份目录
cd 20260104_081420
```

### 步骤2: 恢复目录结构

```bash
# 2.1 创建工作目录
mkdir -p /home/user/webapp
cd /home/user/webapp

# 2.2 复制数据库
cp -r /path/to/backup/databases ./

# 2.3 复制核心代码
cp -r /path/to/backup/core_code/* ./

# 2.4 复制Web文件
cp -r /path/to/backup/web_files/templates ./
cp -r /path/to/backup/web_files/static ./

# 2.5 复制配置文件
cp -r /path/to/backup/configs/* ./

# 2.6 恢复Git仓库
cp -r /path/to/backup/git/.git ./

# 2.7 复制文档
cp -r /path/to/backup/docs/* ./
```

### 步骤3: 安装Python依赖

```bash
cd /home/user/webapp

# 3.1 创建虚拟环境(可选但推荐)
python3 -m venv venv
source venv/bin/activate

# 3.2 安装依赖
pip3 install -r requirements.txt

# 或手动安装核心依赖
pip3 install flask requests sqlite3 pytz pandas numpy
```

### 步骤4: 配置PM2进程

```bash
cd /home/user/webapp

# 4.1 复制PM2配置
cp /path/to/backup/pm2/dump.pm2 /home/user/.pm2/

# 4.2 启动Flask服务
pm2 start ecosystem.flask.config.js

# 4.3 启动采集器
pm2 start ecosystem.collector.config.js

# 4.4 启动锚点系统
pm2 start ecosystem.anchor.config.js

# 4.5 启动其他服务
pm2 start ecosystem.count-checker.config.js

# 4.6 保存PM2配置
pm2 save

# 4.7 设置开机自启
pm2 startup
```

### 步骤5: 验证数据库

```bash
cd /home/user/webapp/databases

# 5.1 检查主数据库
sqlite3 crypto_data.db "SELECT COUNT(*) FROM crypto_snapshots;"

# 5.2 检查交易数据库
sqlite3 trading_decision.db "SELECT COUNT(*) FROM anchor_positions;"

# 5.3 检查锚点系统数据库
sqlite3 anchor_system.db ".tables"

# 5.4 检查支撑压力数据库
sqlite3 support_resistance.db ".tables"

# 5.5 检查SAR斜率数据库
sqlite3 sar_slope_data.db ".tables"
```

### 步骤6: 测试API端点

```bash
# 6.1 测试Flask服务
curl http://localhost:5000/

# 6.2 测试最新数据API
curl http://localhost:5000/api/latest

# 6.3 测试历史查询API
curl "http://localhost:5000/api/query?time=2026-01-04%2010:00:00"

# 6.4 测试爆仓统计API
curl http://localhost:5000/api/liquidation/summary

# 6.5 测试锚点系统API
curl http://localhost:5000/api/anchor-system/current-positions

# 6.6 测试支撑压力API
curl http://localhost:5000/api/support-resistance/escape-stats-history
```

### 步骤7: 访问Web页面

在浏览器中访问以下页面:

1. **首页**: http://localhost:5000/
2. **SAR斜率系统**: http://localhost:5000/sar-slope
3. **历史数据查询**: http://localhost:5000/query
4. **恐慌清洗指数**: http://localhost:5000/panic
5. **支撑压力线**: http://localhost:5000/support-resistance
6. **锚点系统实盘**: http://localhost:5000/anchor-system-real
7. **爆仓统计**: http://localhost:5000/liquidation-stats
8. **逃顶信号历史**: http://localhost:5000/escape-stats-history

### 步骤8: 验证PM2进程

```bash
# 8.1 查看所有进程
pm2 list

# 8.2 查看Flask日志
pm2 logs flask-app --lines 50

# 8.3 查看采集器日志
pm2 logs support-resistance-collector --lines 50

# 8.4 查看锚点系统日志
pm2 logs anchor-maintenance --lines 50

# 8.5 监控所有进程
pm2 monit
```

---

## 🔧 重点系统恢复指南

### 1. SAR斜率系统 ⭐

**关键文件**:
- 数据库: `databases/sar_slope_data.db` (505MB)
- 采集器: `sar_slope_collector.py`
- 页面: `templates/sar_slope.html`
- PM2配置: `ecosystem.sar.config.js`

**恢复步骤**:
```bash
# 复制数据库
cp backup/databases/sar_slope_data.db /home/user/webapp/databases/

# 启动采集器
pm2 start ecosystem.sar.config.js

# 访问页面
curl http://localhost:5000/sar-slope
```

**验证**:
```bash
sqlite3 databases/sar_slope_data.db ".tables"
sqlite3 databases/sar_slope_data.db "SELECT COUNT(*) FROM sar_data;"
```

### 2. 历史数据查询系统 ⭐

**关键文件**:
- 数据库: `databases/crypto_data.db` (1.1MB)
- API: `app_new.py` (路由: `/api/query`, `/api/latest`)
- 页面: `templates/escape_stats_history.html`

**恢复步骤**:
```bash
# 复制数据库
cp backup/databases/crypto_data.db /home/user/webapp/databases/

# 启动Flask
pm2 start ecosystem.flask.config.js

# 测试API
curl http://localhost:5000/api/latest
```

**验证**:
```bash
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM crypto_snapshots;"
curl "http://localhost:5000/api/query?time=2026-01-04"
```

### 3. 恐慌清洗指数系统 ⭐

**关键文件**:
- 数据库: `databases/crypto_data.db` (表: `panic_wash_index`)
- 页面: `templates/panic_new.html`
- API: `/api/panic/latest`

**恢复步骤**:
```bash
# 数据库已在步骤2恢复
# 访问页面
curl http://localhost:5000/panic
```

**验证**:
```bash
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM panic_wash_index;"
curl http://localhost:5000/api/panic/latest
```

### 4. 支撑压力线系统 ⭐

**关键文件**:
- 数据库: `databases/support_resistance.db` (148MB)
- 采集器: `support_resistance_collector.py`
- 页面: `templates/support_resistance.html`
- API: `/api/support-resistance/*`

**恢复步骤**:
```bash
# 复制数据库
cp backup/databases/support_resistance.db /home/user/webapp/databases/

# 启动采集器
pm2 start support_resistance_collector.py

# 测试
curl http://localhost:5000/api/support-resistance/escape-stats-history
```

**验证**:
```bash
sqlite3 databases/support_resistance.db ".tables"
curl http://localhost:5000/support-resistance
```

### 5. 锚点系统(实盘) ⭐

**关键文件**:
- 数据库: 
  - `databases/anchor_system.db` (13MB)
  - `databases/trading_decision.db` (4.2MB)
- 核心代码: `anchor_system.py`
- 守护进程:
  - `sub_account_opener_daemon.py`
  - `sub_account_maintenance_checker.py`
- 页面: `templates/anchor_system_real.html`
- API: `/api/anchor-system/*`, `/api/anchor/*`

**恢复步骤**:
```bash
# 复制数据库
cp backup/databases/anchor_system.db /home/user/webapp/databases/
cp backup/databases/trading_decision.db /home/user/webapp/databases/

# 启动锚点维护
pm2 start ecosystem.anchor.config.js

# 启动子账号系统
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_maintenance_checker.py --name sub-account-maintenance

# 测试API
curl http://localhost:5000/api/anchor-system/current-positions
```

**验证**:
```bash
sqlite3 databases/anchor_system.db ".tables"
sqlite3 databases/trading_decision.db "SELECT * FROM anchor_positions LIMIT 5;"
pm2 logs anchor-maintenance --lines 20
```

### 6. 自动交易系统 (爆仓统计) ⭐

**关键文件**:
- 数据库: `databases/crypto_data.db` (表: `sub_account_liquidations`)
- 追踪器: `sub_account_liquidation_tracker.py`
- 页面: `templates/liquidation_stats.html`
- API: `/api/liquidation/*`

**恢复步骤**:
```bash
# 数据库已恢复
# 测试追踪器
python3 sub_account_liquidation_tracker.py

# 测试API
curl http://localhost:5000/api/liquidation/summary
```

**验证**:
```bash
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM sub_account_liquidations;"
curl http://localhost:5000/liquidation-stats
```

---

## 📊 系统对应关系表

### 子系统 - 文件 - 数据库 对应关系

| # | 系统名称 | 核心文件 | 数据库 | PM2进程 | Web页面 |
|---|---------|---------|--------|---------|---------|
| 1 | SAR斜率系统 | sar_slope_collector.py | sar_slope_data.db | sar-slope-collector | /sar-slope |
| 2 | 历史数据查询 | app_new.py | crypto_data.db | flask-app | /query, /escape-stats-history |
| 3 | 恐慌清洗指数 | app_new.py | crypto_data.db (panic_wash_index) | flask-app | /panic |
| 4 | 支撑压力线 | support_resistance_collector.py | support_resistance.db | support-resistance-collector | /support-resistance |
| 5 | 锚点系统 | anchor_system.py | anchor_system.db, trading_decision.db | anchor-maintenance | /anchor-system-real |
| 6 | 子账号开仓 | sub_account_opener_daemon.py | trading_decision.db | sub-account-opener | - |
| 7 | 子账号维护 | sub_account_maintenance_checker.py | trading_decision.db | sub-account-super-maintenance | - |
| 8 | 爆仓统计 | sub_account_liquidation_tracker.py | crypto_data.db (liquidations) | - | /liquidation-stats |
| 9 | 计次检测 | count_check_daemon.py | crypto_data.db | count-checker | - |
| 10 | Google Drive监控 | gdrive_final_detector.py | - | gdrive-detector | /gdrive-monitor-status |
| 11 | 逃顶信号记录 | escape_signal_recorder.py | crypto_data.db (escape_signal_stats) | escape-signal-recorder | - |
| 12 | 逃顶统计记录 | escape_stats_recorder.py | crypto_data.db (escape_snapshot_stats) | escape-stats-recorder | - |
| 13 | Telegram推送 | - | - | telegram-notifier | - |
| 14 | 位置系统 | - | crypto_data.db (position_system) | position-system-collector | /position-system |
| 15 | 资金监控 | - | fund_monitor.db | - | /fund-monitor |
| 16 | V1V2成交 | - | v1v2_data.db | - | - |
| 17 | 利润极值追踪 | profit_extremes_tracker.py | - | profit-extremes-tracker | - |

---

## 🔍 故障排查

### 问题1: 数据库无法打开

**现象**: `sqlite3.OperationalError: unable to open database file`

**解决方案**:
```bash
# 检查文件权限
ls -l /home/user/webapp/databases/*.db

# 修复权限
chmod 644 /home/user/webapp/databases/*.db
chown user:user /home/user/webapp/databases/*.db

# 检查数据库完整性
sqlite3 databases/crypto_data.db "PRAGMA integrity_check;"
```

### 问题2: PM2进程无法启动

**现象**: `pm2 start` 失败或进程立即退出

**解决方案**:
```bash
# 查看错误日志
pm2 logs <进程名> --err --lines 50

# 检查Python路径
which python3

# 检查依赖
pip3 list | grep flask

# 手动测试脚本
python3 app_new.py
```

### 问题3: API返回500错误

**现象**: API请求返回Internal Server Error

**解决方案**:
```bash
# 查看Flask日志
pm2 logs flask-app --lines 100

# 检查数据库连接
python3 -c "import sqlite3; conn = sqlite3.connect('databases/crypto_data.db'); print('OK')"

# 重启Flask
pm2 restart flask-app
```

### 问题4: 页面无法访问

**现象**: 浏览器显示连接被拒绝

**解决方案**:
```bash
# 检查Flask是否运行
pm2 list | grep flask-app

# 检查端口占用
lsof -i :5000

# 检查防火墙
sudo ufw status

# 重启Flask
pm2 restart flask-app
```

---

## ✅ 恢复检查清单

### 数据完整性检查
- [ ] 所有数据库文件已复制
- [ ] crypto_data.db 可正常打开
- [ ] trading_decision.db 可正常打开
- [ ] anchor_system.db 可正常打开
- [ ] support_resistance.db 可正常打开
- [ ] sar_slope_data.db 可正常打开

### 代码完整性检查
- [ ] app_new.py 存在
- [ ] anchor_system.py 存在
- [ ] 所有守护进程脚本存在
- [ ] 所有采集器脚本存在
- [ ] templates/ 目录完整
- [ ] static/ 目录完整

### 配置完整性检查
- [ ] PM2配置文件存在
- [ ] daily_folder_config.json 存在
- [ ] 其他JSON配置文件完整

### 服务运行检查
- [ ] Flask服务正常运行
- [ ] PM2进程全部online
- [ ] 无进程频繁重启
- [ ] 日志无严重错误

### API功能检查
- [ ] /api/latest 正常返回
- [ ] /api/query 正常返回
- [ ] /api/liquidation/summary 正常返回
- [ ] /api/anchor-system/current-positions 正常返回
- [ ] /api/support-resistance/* 正常返回

### Web页面检查
- [ ] 首页可访问
- [ ] /sar-slope 正常显示
- [ ] /query 正常显示
- [ ] /panic 正常显示
- [ ] /support-resistance 正常显示
- [ ] /anchor-system-real 正常显示
- [ ] /liquidation-stats 正常显示

### 数据采集检查
- [ ] 支撑压力采集器运行
- [ ] SAR斜率采集器运行
- [ ] 逃顶信号采集器运行
- [ ] Google Drive监控运行
- [ ] 数据正常写入数据库

---

## 📞 技术支持

### 日志位置
- PM2日志: `/home/user/.pm2/logs/`
- 应用日志: `/home/user/webapp/logs/`
- 系统日志: `/var/log/`

### 常用命令
```bash
# PM2管理
pm2 list                 # 查看所有进程
pm2 logs <name>          # 查看日志
pm2 restart <name>       # 重启进程
pm2 stop <name>          # 停止进程
pm2 delete <name>        # 删除进程
pm2 monit                # 监控所有进程

# 数据库查询
sqlite3 <db_file> ".tables"              # 查看所有表
sqlite3 <db_file> "SELECT * FROM <table> LIMIT 10;"  # 查询数据
sqlite3 <db_file> "PRAGMA integrity_check;"  # 检查完整性

# 系统监控
df -h                    # 磁盘空间
du -sh /path/to/dir      # 目录大小
ps aux | grep python     # Python进程
netstat -tlnp | grep 5000  # 端口监听
```

---

## 📝 更新记录

**v2.0 (2026-01-04)**
- 完整备份所有23个子系统
- 优化数据库备份(删除重复备份文件)
- 添加详细的恢复步骤
- 添加系统对应关系表
- 添加故障排查指南
- 压缩包大小: 518MB (无需分割)

---

## 🎉 总结

本备份包含完整的加密货币交易系统，包括:
- ✅ 23个子系统
- ✅ 12个数据库(总计724MB)
- ✅ 806个Python文件
- ✅ 67个HTML模板
- ✅ 完整的Git仓库
- ✅ 所有配置文件
- ✅ PM2进程配置
- ✅ 示例日志文件

按照本指南操作，可以实现**1:1完整还原**，确保系统部署后立即可用，无数据丢失！

**重点系统**保证恢复:
1. ⭐ SAR斜率系统
2. ⭐ 历史数据查询系统
3. ⭐ 恐慌清洗指数系统
4. ⭐ 支撑压力线系统
5. ⭐ 锚点系统(实盘)
6. ⭐ 自动交易系统(爆仓统计)

**恢复成功标志**: 所有PM2进程online，所有Web页面可访问，所有API正常响应！
