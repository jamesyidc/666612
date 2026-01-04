# 加密货币交易系统 - 完整备份包

## 📦 备份信息

**备份日期**: 2026-01-04 08:14:26  
**备份版本**: v2.0  
**压缩包大小**: 518MB  
**解压后大小**: ~1.1GB  
**文件总数**: 1,610个文件  

---

## 📚 文档导航

### 🚀 快速开始
- **[QUICK_START.md](./QUICK_START.md)** - 5分钟快速恢复指南
- 适合：快速部署，最小化配置

### 📖 完整指南
- **[RESTORE_GUIDE.md](./RESTORE_GUIDE.md)** - 详细恢复部署指南
- 适合：完整恢复，生产环境部署

### 📋 系统清单
- **[SYSTEM_CHECKLIST.md](./SYSTEM_CHECKLIST.md)** - 系统清单和文件映射
- 适合：了解系统架构，文件定位

### ℹ️ 备份信息
- **[BACKUP_INFO.txt](./20260104_081420/BACKUP_INFO.txt)** - 备份详细信息
- 查看：备份内容统计，系统信息

---

## 🎯 系统概述

### 23个核心子系统

#### 重点系统 ⭐ (6个)
1. **SAR斜率系统** - SAR抛物线指标分析
2. **历史数据查询系统** - 市场数据查询和图表
3. **恐慌清洗指数系统** - 市场情绪指数
4. **支撑压力线系统** - 价格支撑压力识别
5. **锚点系统(实盘)** - 自动化交易和持仓管理
6. **自动交易系统** - 爆仓统计和风险管理

#### 数据采集系统 (7个)
- 支撑压力采集器
- 快照采集器
- Google Drive监控
- 逃顶信号记录器
- 逃顶统计记录器
- 位置系统采集器
- SAR斜率采集器

#### 交易决策系统 (6个)
- 锚点维护系统
- 子账号开仓守护
- 子账号超级维护
- 利润极值追踪
- 币对保护
- 计次检测

#### 其他系统 (4个)
- Telegram消息推送
- Flask Web服务
- 多单监控
- 其他辅助系统

---

## 📊 备份内容

### 数据库 (724MB)
| 数据库 | 大小 | 用途 |
|--------|------|------|
| crypto_data.db | 1.1MB | 主数据库 |
| trading_decision.db | 4.2MB | 交易决策 |
| anchor_system.db | 13MB | 锚点系统 |
| support_resistance.db | 148MB | 支撑压力 |
| sar_slope_data.db | 505MB | SAR斜率 |
| + 其他数据库 | 52.7MB | 辅助数据 |

### 源代码 (13MB)
- 806个Python文件
- 主应用: app_new.py, anchor_system.py
- 守护进程、采集器、追踪器
- 工具脚本

### Web文件 (3.1MB)
- 67个HTML模板
- 静态资源 (CSS, JS, 图片)

### 配置文件 (188KB)
- 27个配置文件
- PM2进程配置
- 系统JSON配置

### Git仓库 (364MB)
- 完整Git历史
- 最近50次提交记录

### 文档 (1.3MB)
- 134个Markdown文档
- 系统说明文档
- 修复文档

### 其他
- PM2进程状态
- 示例日志
- 依赖列表

---

## 🚀 快速恢复 (3步)

### 步骤1: 解压
```bash
tar -xzf crypto_system_backup_20260104_081420.tar.gz
cd 20260104_081420
```

### 步骤2: 恢复文件
```bash
WEBAPP="/home/user/webapp"
mkdir -p $WEBAPP
cp -r databases core_code/* web_files/* configs/* $WEBAPP/
```

### 步骤3: 启动服务
```bash
cd $WEBAPP
pip3 install -r requirements.txt
pm2 start app_new.py --name flask-app --interpreter python3
pm2 save
```

### 验证
```bash
pm2 list
curl http://localhost:5000/api/latest
# 浏览器访问: http://localhost:5000
```

详细步骤请查看: **[QUICK_START.md](./QUICK_START.md)**

---

## 📖 完整恢复流程

1. **解压备份文件** (查看 QUICK_START.md)
2. **恢复目录结构** (10步详细流程)
3. **安装Python依赖** (requirements.txt)
4. **配置PM2进程** (批量启动服务)
5. **验证数据库** (检查完整性)
6. **测试API端点** (功能验证)
7. **访问Web页面** (界面验证)
8. **验证PM2进程** (进程监控)

详细流程请查看: **[RESTORE_GUIDE.md](./RESTORE_GUIDE.md)**

---

## 🔍 故障排查

### 常见问题

1. **数据库无法打开**
   - 检查文件权限: `chmod 644 databases/*.db`
   - 验证完整性: `sqlite3 <db> "PRAGMA integrity_check;"`

2. **PM2进程启动失败**
   - 查看日志: `pm2 logs <name> --err`
   - 手动测试: `python3 <script>.py`

3. **API返回500错误**
   - 查看Flask日志: `pm2 logs flask-app`
   - 重启服务: `pm2 restart flask-app`

4. **页面无法访问**
   - 检查进程: `pm2 list | grep flask`
   - 检查端口: `lsof -i :5000`

更多故障排查请查看: **[RESTORE_GUIDE.md](./RESTORE_GUIDE.md)** 第9章

---

## ✅ 验证检查清单

### 数据完整性
- [ ] 所有数据库文件已复制
- [ ] 数据库可正常打开
- [ ] 表结构完整

### 代码完整性
- [ ] app_new.py 存在
- [ ] anchor_system.py 存在
- [ ] 所有脚本文件完整

### 服务运行
- [ ] Flask服务运行正常
- [ ] PM2所有进程online
- [ ] 无进程频繁重启

### 功能验证
- [ ] 所有API正常响应
- [ ] 所有Web页面可访问
- [ ] 数据采集正常

---

## 📞 技术支持

### 联系方式
- GitHub: https://github.com/jamesyidc/666612.git
- 查看备份时的最后提交: `git log -1`

### 日志位置
- PM2日志: `/home/user/.pm2/logs/`
- 应用日志: `/home/user/webapp/logs/`

### 常用命令
```bash
# PM2管理
pm2 list                      # 查看所有进程
pm2 logs <name>               # 查看日志
pm2 restart <name>            # 重启进程
pm2 monit                     # 监控进程

# 数据库
sqlite3 <db> ".tables"        # 查看表
sqlite3 <db> "SELECT COUNT(*) FROM <table>;"  # 查询数据

# 系统监控
df -h                         # 磁盘空间
du -sh /path/to/dir           # 目录大小
ps aux | grep python          # Python进程
```

---

## 📝 备份文件结构

```
crypto_system_backup_20260104_081420.tar.gz (518MB)
│
└── 20260104_081420/
    ├── databases/              # 数据库文件 (724MB)
    │   ├── crypto_data.db
    │   ├── trading_decision.db
    │   ├── anchor_system.db
    │   ├── support_resistance.db
    │   ├── sar_slope_data.db
    │   └── ...
    │
    ├── core_code/              # Python源码 (13MB, 806个文件)
    │   ├── app_new.py
    │   ├── anchor_system.py
    │   ├── *_daemon.py
    │   ├── *_collector.py
    │   └── ...
    │
    ├── web_files/              # Web文件 (3.1MB)
    │   ├── templates/          # 67个HTML
    │   └── static/             # CSS, JS, 图片
    │
    ├── configs/                # 配置文件 (188KB, 27个文件)
    │   ├── ecosystem.*.config.js
    │   └── *.json
    │
    ├── pm2/                    # PM2配置 (40KB)
    │   ├── dump.pm2
    │   └── pm2_processes.txt
    │
    ├── git/                    # Git仓库 (364MB)
    │   └── .git/
    │
    ├── docs/                   # 文档 (1.3MB, 134个MD文件)
    │
    ├── logs_sample/            # 示例日志 (6.6MB)
    │
    ├── requirements.txt        # Python依赖
    ├── python_version.txt      # Python版本
    └── BACKUP_INFO.txt         # 备份信息
```

---

## 🎉 关键特性

### ✅ 完整性
- 所有23个子系统完整备份
- 所有数据库包含完整数据
- Git历史完整保留

### ✅ 易用性
- 3步快速恢复
- 详细文档指导
- 故障排查指南

### ✅ 可靠性
- 数据完整性验证
- 文件校验和
- 测试验证流程

### ✅ 高效性
- 压缩包仅518MB
- 无需分割
- 快速解压部署

---

## 🏆 恢复成功标志

部署完成后，以下指标表示恢复成功:

✅ 所有PM2进程状态为 **online**  
✅ Flask API正常响应  
✅ Web页面全部可访问  
✅ 数据库查询正常  
✅ 采集器正常运行并写入数据  
✅ 锚点系统正常交易  

**恢复后的系统应与备份时完全一致，实现1:1还原！**

---

## 📋 文档更新日志

**v2.0 (2026-01-04)**
- 完整备份23个子系统
- 优化数据库备份(删除重复文件)
- 详细的恢复文档
- 系统对应关系表
- 故障排查指南
- 快速恢复指南

---

## 💡 最佳实践

### 备份策略
- 定期备份(建议每周)
- 保留最近3个备份
- 验证备份完整性

### 恢复测试
- 在测试环境先恢复
- 验证所有功能
- 记录遇到的问题

### 文档维护
- 及时更新配置变更
- 记录新增系统
- 更新依赖列表

---

**备份创建工具**: full_backup_v2.sh  
**恢复指导文档**: RESTORE_GUIDE.md  
**快速开始文档**: QUICK_START.md  
**系统清单文档**: SYSTEM_CHECKLIST.md  

**完整恢复部署后，系统即可正常运行！** 🎯
