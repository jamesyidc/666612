# 📚 系统备份与恢复文档导航

> **快速索引** - 根据你的需求选择对应的文档

---

## 🎯 我需要...

### 1. 🚀 **快速恢复系统（5分钟）**
   
   📄 **阅读**: `BACKUP_README.md`
   
   - ✅ 最精简的恢复步骤
   - ✅ 核心命令清单
   - ✅ 快速验证方法

---

### 2. 📖 **详细恢复指南（完整步骤）**
   
   📄 **阅读**: `COMPLETE_SYSTEM_BACKUP_GUIDE.md` ⭐ **推荐**
   
   - ✅ 23个子系统完整清单
   - ✅ 5个数据库详细结构
   - ✅ 10个PM2进程配置
   - ✅ 敏感配置文件说明
   - ✅ 1:1完美还原步骤
   - ✅ 故障排查速查表
   - ✅ 验证清单

---

### 3. 💾 **数据库结构和表说明**
   
   📄 **阅读**: `DATABASE_SCHEMA.md`
   
   - ✅ 5个数据库完整结构
   - ✅ 所有表的字段说明
   - ✅ 索引和外键关系
   - ✅ SQL查询示例
   - ✅ 备份和恢复命令

---

### 4. ⚙️ **PM2进程配置**
   
   📄 **阅读**: `PM2_PROCESSES.json`
   
   - ✅ 10个进程的完整配置
   - ✅ 启动脚本路径
   - ✅ 日志文件位置
   - ✅ 进程工作目录

---

### 5. 📊 **系统当前状态报告**
   
   📄 **阅读**: `BACKUP_FINAL_REPORT.md`
   
   - ✅ 系统架构图
   - ✅ 当前运行状态
   - ✅ 数据统计信息
   - ✅ 完成度报告

---

### 6. 🔄 **系统恢复通用指南**
   
   📄 **阅读**: `SYSTEM_RECOVERY_GUIDE.md`
   
   - ✅ 通用恢复步骤
   - ✅ 不同场景的恢复方案
   - ✅ 配置文件说明

---

## 📁 文档清单（按用途分类）

### 🌟 核心文档（必读）

| 文档 | 用途 | 适用场景 |
|------|------|----------|
| **COMPLETE_SYSTEM_BACKUP_GUIDE.md** | 完整恢复指南 | 需要详细了解所有系统 |
| **BACKUP_README.md** | 快速恢复 | 紧急恢复，时间紧迫 |
| **DATABASE_SCHEMA.md** | 数据库结构 | 需要操作数据库 |

### 📋 参考文档

| 文档 | 用途 | 适用场景 |
|------|------|----------|
| **BACKUP_FINAL_REPORT.md** | 系统状态报告 | 了解当前系统状态 |
| **SYSTEM_RECOVERY_GUIDE.md** | 通用恢复指南 | 通用恢复流程 |
| **PM2_PROCESSES.json** | PM2配置 | 需要手动配置PM2 |

---

## 🎯 快速导航（按角色）

### 👨‍💼 系统管理员

**需要完整恢复系统**:
1. 先看 `BACKUP_FINAL_REPORT.md` 了解系统全貌
2. 再看 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 执行恢复
3. 参考 `DATABASE_SCHEMA.md` 恢复数据库

---

### 👨‍💻 开发人员

**需要了解数据结构**:
1. 先看 `DATABASE_SCHEMA.md` 了解数据库
2. 再看 `PM2_PROCESSES.json` 了解进程配置
3. 参考 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 了解系统架构

---

### 🚨 运维人员

**紧急恢复系统**:
1. 直接看 `BACKUP_README.md` 快速恢复
2. 如果遇到问题，查看 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 的故障排查章节
3. 验证系统后查看 `BACKUP_FINAL_REPORT.md` 确认状态

---

## 📊 系统关键信息速查

### 数据库文件位置

```
databases/crypto_data.db          ← 主数据库（核心）
support_resistance.db             ← 支撑压力数据库（注意：在根目录）
databases/panic_index.db          ← 恐慌指数
databases/gdrive_monitor.db       ← Google Drive监控
databases/market_data.db          ← 市场数据
```

### 敏感配置文件（⚠️ 需单独备份）

```
sub_account_config.json           ← OKEx API密钥 🔴 极重要
anchor_config.json                ← 锚点配置
telegram_config.json              ← Telegram Bot Token
gdrive_config.json                ← Google Drive凭证
```

### PM2核心进程

```
support-resistance-collector      ← 支撑压力线采集
support-snapshot-collector        ← 快照采集
anchor-maintenance                ← 锚点维护
sub-account-opener                ← 自动交易（开单）
sub-account-super-maintenance     ← 自动交易（维护）
flask-app                         ← Web应用 (端口5000)
```

### 重要API端点

```
GET  /api/support-resistance/escape-signal-stats          ← 获取最新信号数
POST /api/support-resistance/record-escape-signal-stats   ← 记录信号数
GET  /api/support-resistance/escape-stats-history         ← 历史数据
```

---

## 🔑 核心数据表

### escape_signal_stats（逃顶信号）

```sql
-- 字段: id, stat_time, signal_24h_count, signal_2h_count, created_at
-- 当前: 24h=251, 2h=2
-- 历史最大: 24h=275, 2h=18
-- 记录频率: 每分钟
```

### support_resistance_levels（支撑压力位）

```sql
-- 字段: id, symbol, price_level, level_type, strength, test_count, ...
-- 记录数: 294,799 条
-- 用途: 所有币种的支撑和压力位
```

### anchor_records（锚点记录）

```sql
-- 字段: id, symbol, anchor_price, anchor_time, anchor_type, is_active, ...
-- 用途: 锚点系统核心表
```

### trading_orders（交易订单）

```sql
-- 字段: id, sub_account, symbol, order_id, side, price, quantity, status, ...
-- 用途: 自动交易订单记录
```

---

## ✅ 快速验证命令

### 检查数据库

```bash
sqlite3 databases/crypto_data.db "SELECT COUNT(*) FROM escape_signal_stats;"
sqlite3 support_resistance.db "SELECT COUNT(*) FROM support_resistance_levels;"
```

### 检查PM2进程

```bash
pm2 list
pm2 logs --lines 50
```

### 检查Web服务

```bash
curl -I http://localhost:5000/support-resistance
curl http://localhost:5000/api/support-resistance/escape-signal-stats
```

---

## 🆘 紧急联系

### 故障排查优先级

1. **数据库问题** → 查看 `DATABASE_SCHEMA.md`
2. **PM2进程问题** → 查看 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 故障排查章节
3. **配置文件问题** → 查看 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 配置文件章节
4. **API问题** → 查看 PM2日志 `pm2 logs flask-app`

### 常见问题快速解决

| 问题 | 文档章节 | 页面/行号 |
|------|----------|-----------|
| 数据库恢复 | `COMPLETE_SYSTEM_BACKUP_GUIDE.md` | 步骤4 |
| PM2进程启动 | `COMPLETE_SYSTEM_BACKUP_GUIDE.md` | 步骤6 |
| 配置文件格式 | `COMPLETE_SYSTEM_BACKUP_GUIDE.md` | 配置文件清单 |
| API不返回数据 | `COMPLETE_SYSTEM_BACKUP_GUIDE.md` | 故障排查 - 问题4 |

---

## 📞 文档更新

- **最后更新**: 2026-01-02
- **文档版本**: v2.0
- **GitHub仓库**: https://github.com/jamesyidc/666612
- **最后提交**: d491bea

---

## 🎉 总结

✅ **5个核心文档**，涵盖所有恢复场景  
✅ **23个子系统**，完整文档化  
✅ **5个数据库**，详细结构说明  
✅ **10个PM2进程**，配置已导出  
✅ **1:1完美还原**，步骤详细可操作

**开始恢复**: 从 `BACKUP_README.md` 或 `COMPLETE_SYSTEM_BACKUP_GUIDE.md` 开始！
