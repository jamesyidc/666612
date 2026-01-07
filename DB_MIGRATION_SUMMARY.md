# 数据库迁移JSONL总结报告

## 完成时间
2026-01-07 14:06

## 迁移成果

### 1. SAR斜率系统 ✅
- **存储格式**: JSONL (每行一个JSON)
- **位置**: `/home/user/webapp/data/sar_slope/{币种}/`
- **数据量**: 27个币种，每币种独立日期文件
- **大小**: 224KB
- **保留期**: 16天自动清理
- **采集**: PM2守护进程 `sar-collector` 每5分钟一次

### 2. 核心数据库转换 ✅
- **输出**: `/home/user/webapp/data/db_jsonl/`
- **文件列表**:
  - `support_resistance.jsonl` - 364MB (412,741行)
  - `fund_monitor.jsonl` - 78MB (253,418行)
  - `anchor_system.jsonl` - 23MB (48,627行)
  - `trading_decision.jsonl` - 9.2MB (24,577行)
  - `crypto_data.jsonl` - 3.5MB (13,435行)
- **总计**: 477MB JSONL格式

### 3. 备份
- **位置**: `/home/user/webapp/backup/old_databases/`
- **大小**: 785MB (17个.db文件)
- **状态**: 已从git移除，本地保留

## 待修复问题

### Google Drive监控系统
- **问题**: gdrive-detector依赖crypto_snapshots表（已删除）
- **影响**: TXT文件列表为空
- **解决方案**: 
  1. 重建crypto_data.db的crypto_snapshots表
  2. 或修改gdrive-detector使用JSONL存储

### 文件夹ID配置
- **当前**: folder_id = 1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM
- **问题**: 可能不是2026-01-07的文件夹
- **解决方案**: 手动从Google Drive获取正确的今日文件夹ID

## Git提交
- 最新commit: `a8ab483` - feat: DB转JSONL工具(输出本地保存)
- JSONL文件: 已添加到.gitignore (本地存储)
- 仓库: https://github.com/jamesyidc/666612

## 服务状态
- ✅ sar-collector: 运行中
- ⚠️  gdrive-detector: 运行中但数据库表缺失
- ✅ flask-app: 正常
