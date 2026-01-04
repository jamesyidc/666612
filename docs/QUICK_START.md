# 快速恢复指南 (Quick Start)

## 🚀 5分钟快速恢复

### 1. 解压备份 (1分钟)
```bash
tar -xzf crypto_system_backup_20260104_081420.tar.gz
cd 20260104_081420
```

### 2. 恢复文件 (2分钟)
```bash
# 一键复制所有文件
WEBAPP="/home/user/webapp"
mkdir -p $WEBAPP
cp -r databases $WEBAPP/
cp -r core_code/* $WEBAPP/
cp -r web_files/templates $WEBAPP/
cp -r web_files/static $WEBAPP/
cp -r configs/* $WEBAPP/
cp -r git/.git $WEBAPP/
cp requirements.txt $WEBAPP/
```

### 3. 安装依赖 (1分钟)
```bash
cd $WEBAPP
pip3 install -r requirements.txt
```

### 4. 启动服务 (1分钟)
```bash
cd $WEBAPP

# 启动Flask
pm2 start app_new.py --name flask-app --interpreter python3

# 启动核心采集器
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start sar_slope_collector.py --name sar-slope-collector
pm2 start escape_signal_recorder.py --name escape-signal-recorder
pm2 start escape_stats_recorder.py --name escape-stats-recorder

# 启动锚点系统
pm2 start sub_account_opener_daemon.py --name sub-account-opener
pm2 start sub_account_maintenance_checker.py --name anchor-maintenance

# 启动Google Drive监控
pm2 start gdrive_final_detector.py --name gdrive-detector

# 保存PM2配置
pm2 save
```

### 5. 验证 (<1分钟)
```bash
# 检查进程
pm2 list

# 测试API
curl http://localhost:5000/api/latest

# 浏览器访问
# http://localhost:5000
```

## ✅ 验证检查

- [ ] `pm2 list` 显示所有进程 online
- [ ] `curl http://localhost:5000/api/latest` 返回JSON数据
- [ ] 浏览器可以访问 http://localhost:5000/
- [ ] http://localhost:5000/sar-slope 页面正常
- [ ] http://localhost:5000/query 页面正常
- [ ] http://localhost:5000/anchor-system-real 页面正常

## 🔧 常用PM2命令

```bash
pm2 list              # 查看所有进程
pm2 logs flask-app    # 查看Flask日志
pm2 restart all       # 重启所有进程
pm2 stop all          # 停止所有进程
pm2 monit             # 监控进程
```

## 📊 核心系统快速启动

### 只启动重点系统 (最小化配置)
```bash
# 只启动必需服务
pm2 start app_new.py --name flask-app --interpreter python3
pm2 start support_resistance_collector.py --name support-resistance-collector
pm2 start sar_slope_collector.py --name sar-slope-collector
pm2 start sub_account_opener_daemon.py --name sub-account-opener

# 验证
pm2 list
curl http://localhost:5000/api/latest
```

### 完整系统启动 (全部功能)
```bash
# 使用PM2配置文件批量启动
cd /home/user/webapp

# 如果有ecosystem配置文件
pm2 start ecosystem.collector.config.js
pm2 start ecosystem.anchor.config.js
pm2 start ecosystem.flask.config.js

# 保存
pm2 save
```

## ⚠️ 常见问题

### Q1: PM2进程启动失败
```bash
# 查看错误日志
pm2 logs <进程名> --err --lines 50

# 手动测试脚本
cd /home/user/webapp
python3 app_new.py
```

### Q2: 数据库无法打开
```bash
# 检查权限
chmod 644 /home/user/webapp/databases/*.db

# 测试数据库
sqlite3 /home/user/webapp/databases/crypto_data.db "SELECT COUNT(*) FROM crypto_snapshots;"
```

### Q3: API返回错误
```bash
# 重启Flask
pm2 restart flask-app

# 查看日志
pm2 logs flask-app --lines 100
```

## 📖 详细文档

完整恢复步骤请查看: [RESTORE_GUIDE.md](./RESTORE_GUIDE.md)

系统架构和配置说明请查看备份目录中的 `BACKUP_INFO.txt`

## 🎯 恢复成功标志

✅ 所有PM2进程状态为 **online**  
✅ Flask API正常响应  
✅ Web页面可访问  
✅ 数据库查询正常  
✅ 采集器正常运行并写入数据  

恢复完成后，系统应与备份时完全一致！
