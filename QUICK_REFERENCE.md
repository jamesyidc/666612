# 🚀 系统恢复快速参考卡

> **最快的恢复指南 - 5分钟上手**

---

## 📖 文档导航（6个核心文档）

### 🌟 **最重要的文档**

```
DOCS_INDEX.md                       ← 📖 从这里开始！文档导航索引
  └─> 帮你找到需要的文档

COMPLETE_SYSTEM_BACKUP_GUIDE.md    ← ⭐ 最完整的恢复指南
  └─> 23个子系统 + 5个数据库 + 1:1还原步骤

BACKUP_README.md                    ← 🚀 5分钟快速恢复
  └─> 紧急恢复，核心命令

DATABASE_SCHEMA.md                  ← 💾 数据库结构完整文档
  └─> 所有表结构和SQL示例

BACKUP_FINAL_REPORT.md              ← 📊 系统状态报告
  └─> 当前系统全貌和统计

PM2_PROCESSES.json                  ← ⚙️  PM2配置导出
  └─> 10个进程完整配置
```

---

## ⚡ 5分钟快速恢复

### 步骤1: 克隆代码 (1分钟)
```bash
git clone https://github.com/jamesyidc/666612.git /home/user/webapp
cd /home/user/webapp
```

### 步骤2: 安装依赖 (2分钟)
```bash
pip3 install -r requirements.txt
```

### 步骤3: 恢复数据库 (1分钟)
```bash
# 从备份复制数据库
cp /backup/crypto_data.db databases/
cp /backup/support_resistance.db .
cp /backup/panic_index.db databases/
cp /backup/gdrive_monitor.db databases/
cp /backup/market_data.db databases/
```

### 步骤4: 恢复配置文件 (30秒) ⚠️ **关键步骤**
```bash
# 从安全位置恢复敏感配置
cp /secure_backup/sub_account_config.json .
cp /secure_backup/anchor_config.json .
cp /secure_backup/telegram_config.json .
cp /secure_backup/gdrive_config.json .

# 设置权限
chmod 600 *.json
```

### 步骤5: 启动服务 (1分钟)
```bash
# 方法1: 使用保存的PM2配置（推荐）
pm2 resurrect
pm2 list

# 方法2: 手动启动核心进程
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start support_resistance_snapshot_collector.py --name support-snapshot-collector
pm2 start anchor_maintenance_realtime_daemon.py --name anchor-maintenance
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_super_maintenance.py --name sub-account-super-maintenance
pm2 start --name flask-app --interpreter bash -x -- -c "cd /home/user/webapp && python3 app_new.py"

# 保存配置
pm2 save
```

---

## ✅ 快速验证

```bash
# 1. 检查数据库
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"

# 2. 检查PM2进程（所有应该是 online）
pm2 list

# 3. 检查Web服务
curl -I http://localhost:5000/support-resistance

# 4. 检查API
curl http://localhost:5000/api/support-resistance/escape-signal-stats
```

---

## 🔑 关键信息速查

### 数据库位置
```
databases/crypto_data.db          ← 主数据库（核心）
support_resistance.db             ← 支撑压力（⚠️ 在根目录）
databases/panic_index.db
databases/gdrive_monitor.db
databases/market_data.db
```

### 敏感配置文件（⚠️ 不在git中）
```
sub_account_config.json           ← 🔴 OKEx API密钥（极重要）
anchor_config.json                ← 锚点配置
telegram_config.json              ← Telegram Bot Token
gdrive_config.json                ← Google Drive凭证
```

### 核心PM2进程
```
support-resistance-collector      ← 支撑压力线采集
support-snapshot-collector        ← 快照采集
anchor-maintenance                ← 锚点维护
sub-account-opener                ← 自动交易（开单）
sub-account-super-maintenance     ← 自动交易（维护）
flask-app                         ← Web应用 (端口5000)
```

---

## 🆘 故障排查速查表

| 问题 | 解决方案 |
|------|----------|
| PM2进程 errored | `pip3 install -r requirements.txt` |
| Flask无法访问 | `lsof -i:5000` 检查端口占用 |
| 数据库错误 | 从备份恢复数据库文件 |
| API返回空 | 检查采集器: `pm2 logs support-resistance-collector` |
| 自动交易失败 | 检查配置: `cat sub_account_config.json` |

**详细故障排查**: 查看 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 故障排查章节

---

## 📊 系统核心数据

### 23个子系统
- **7个核心系统**（必须恢复）
- **3个辅助系统**（重要）
- **17个数据展示系统**（通过Web访问）

### 5个数据库
- crypto_data.db（10个核心表）
- support_resistance.db（294,799条记录）
- panic_index.db
- gdrive_monitor.db
- market_data.db

### 10个PM2进程
全部运行状态: 🟢 在线

---

## 📞 需要帮助？

### 根据场景选择文档

| 场景 | 阅读文档 |
|------|----------|
| 🔰 第一次使用 | `DOCS_INDEX.md` |
| 🚀 紧急恢复 | `BACKUP_README.md` |
| 📚 详细了解 | `COMPLETE_SYSTEM_BACKUP_GUIDE.md` |
| 💾 数据库操作 | `DATABASE_SCHEMA.md` |
| 📊 查看系统状态 | `BACKUP_FINAL_REPORT.md` |

---

## 🎯 总结

✅ **完整备份**: 23个子系统、5个数据库、10个PM2进程  
✅ **详细文档**: 6个核心文档，涵盖所有场景  
✅ **1:1还原**: 5个步骤，5分钟完成  
✅ **验证完整**: 数据库、PM2、Web、API全覆盖  

**GitHub仓库**: https://github.com/jamesyidc/666612  
**最后更新**: 2026-01-02  
**文档版本**: v2.0

---

🎉 **开始恢复**: 从 `BACKUP_README.md` 或 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 开始！
