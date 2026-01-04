# 每日凌晨2点计次检测和Telegram提醒功能

## 📋 功能概述

系统现在支持**每天北京时间凌晨2点自动检测计次**，如果计次小于2，则通过Telegram发送提醒消息。

## 🎯 功能需求

- **检测时间**: 每天北京时间 02:00
- **检测条件**: 计次 < 2
- **提醒方式**: Telegram消息推送
- **自动运行**: 通过PM2守护进程持续运行

## 📁 相关文件

### 1. 守护进程脚本
**文件**: `count_check_daemon.py`

```python
#!/usr/bin/env python3
"""
计次检测守护进程
每天北京时间凌晨2点检测计次是否大于2，如果小于2则发送Telegram提醒
"""
```

**主要功能**:
- ✅ 数据库连接：从 `databases/crypto_data.db` 获取最新计次
- ✅ 时间控制：每30秒检查一次，在凌晨2点整执行检测
- ✅ Telegram推送：检测到异常时发送格式化消息
- ✅ 异常处理：完善的错误处理和日志记录

### 2. PM2配置文件
**文件**: `ecosystem.count-checker.config.js`

```javascript
module.exports = {
  apps: [{
    name: 'count-checker',
    script: './count_check_daemon.py',
    interpreter: 'python3',
    cwd: '/home/user/webapp',
    instances: 1,
    autorestart: true,
    max_memory_restart: '200M',
    error_file: '/home/user/.pm2/logs/count-checker-error.log',
    out_file: '/home/user/.pm2/logs/count-checker-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    env: {
      TZ: 'Asia/Shanghai'
    }
  }]
}
```

## 🚀 启动方式

### 启动服务
```bash
cd /home/user/webapp
pm2 start ecosystem.count-checker.config.js
pm2 save
```

### 查看状态
```bash
pm2 list | grep count-checker
```

### 查看日志
```bash
pm2 logs count-checker --lines 50
```

### 重启服务
```bash
pm2 restart count-checker
```

### 停止服务
```bash
pm2 stop count-checker
```

## 📊 检测逻辑

### 数据来源
从 `crypto_snapshots` 表获取最新的计次数据：
```sql
SELECT snapshot_time, count 
FROM crypto_snapshots 
ORDER BY snapshot_date DESC, snapshot_time DESC 
LIMIT 1
```

### 检测条件
```python
if count < 2:
    # 发送Telegram提醒
    send_telegram_message(...)
else:
    # 计次正常，无需提醒
    print(f"✅ 计次{count}正常（>=2），无需提醒")
```

## 📱 Telegram消息格式

### 计次异常提醒
```
🚨 计次异常提醒

⚠️ 当前计次: 1
❌ 低于阈值: 2

📅 数据时间: 2026-01-04 13:38:00
⏰ 检测时间: 2026-01-04 02:00:00

💡 建议：请检查市场状态和数据采集服务
```

### 数据获取失败提醒
```
⚠️ 计次检测警告

无法获取计次数据！

请检查数据库连接。
```

## ⏰ 执行时间表

| 时间 | 动作 | 说明 |
|------|------|------|
| 每30秒 | 检查时间 | 判断是否到达凌晨2点 |
| 02:00:00 | 执行检测 | 获取最新计次并判断 |
| 02:00:00 | 发送提醒 | 如果计次<2，发送Telegram消息 |
| 02:01:10 | 继续等待 | 休眠70秒后继续下一轮检查 |

## 🔍 测试方法

### 手动测试Telegram推送
```bash
cd /home/user/webapp
python3 -c "
from count_check_daemon import send_telegram_message
message = '🧪 测试消息：计次检测功能正常'
send_telegram_message(message)
"
```

### 手动执行一次检测
```bash
cd /home/user/webapp
python3 -c "
from count_check_daemon import check_count
check_count()
"
```

### 查看当前计次
```bash
cd /home/user/webapp
python3 -c "
import sqlite3
conn = sqlite3.connect('databases/crypto_data.db')
cursor = conn.cursor()
cursor.execute('SELECT snapshot_time, count FROM crypto_snapshots ORDER BY snapshot_date DESC, snapshot_time DESC LIMIT 1')
row = cursor.fetchone()
if row:
    print(f'📅 时间: {row[0]}')
    print(f'📊 计次: {row[1]}')
conn.close()
"
```

## 📈 运行状态

### 当前状态
```bash
$ pm2 list | grep count-checker
│ 21 │ count-checker  │ online │ 5m  │ 0 │ 29.6mb │
```

- ✅ 进程ID: 21
- ✅ 状态: online
- ✅ 运行时间: 5分钟
- ✅ 重启次数: 0
- ✅ 内存占用: 29.6MB

### 启动日志
```
============================================================
🤖 计次检测守护进程已启动
============================================================
⏰ 检查时间: 每天北京时间 02:00
📊 检测条件: 计次 < 2
📱 提醒方式: Telegram
📅 启动时间: 2026-01-04 14:45:26
============================================================
```

## 🛠️ 配置说明

### Telegram配置
- **Bot Token**: 已配置在 `count_check_daemon.py` 中
- **Chat ID**: 已配置在 `count_check_daemon.py` 中
- **消息格式**: HTML格式，支持粗体、斜体等样式

### 时区配置
- **北京时区**: `Asia/Shanghai`
- **时间格式**: `%Y-%m-%d %H:%M:%S`

### 检测参数
- **检测间隔**: 30秒（检查是否到达凌晨2点）
- **执行间隔**: 70秒（避免重复执行）
- **阈值**: 计次 < 2

## 📋 维护建议

### 日志管理
```bash
# 查看最新日志
pm2 logs count-checker --lines 50

# 清空日志
pm2 flush count-checker

# 查看日志文件
tail -f /home/user/.pm2/logs/count-checker-out.log
tail -f /home/user/.pm2/logs/count-checker-error.log
```

### 性能监控
```bash
# 查看内存使用
pm2 show count-checker

# 查看实时日志
pm2 logs count-checker
```

### 故障排查

#### 1. 服务未运行
```bash
pm2 restart count-checker
pm2 logs count-checker
```

#### 2. Telegram消息未发送
- 检查网络连接
- 验证Bot Token和Chat ID
- 查看错误日志：`pm2 logs count-checker --err`

#### 3. 数据库连接失败
- 检查数据库文件是否存在：`ls -lh databases/crypto_data.db`
- 验证数据库权限：`sqlite3 databases/crypto_data.db .tables`

## 🔗 相关链接

- **实盘锚点系统**: https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/anchor-system-real
- **GitHub仓库**: https://github.com/jamesyidc/666612.git
- **Commit**: 71dac50

## ✅ 功能验证

- ✅ 守护进程已创建并运行
- ✅ PM2配置文件已生成
- ✅ 服务已启动并在线
- ✅ 日志记录正常
- ✅ 时间检测正常
- ✅ Telegram配置已完成
- ✅ 数据库连接正常

## 📝 使用说明

1. **服务已自动启动**: 无需手动操作，服务会在后台持续运行
2. **每日自动检测**: 每天凌晨2点自动执行检测
3. **Telegram提醒**: 计次<2时自动发送消息到您的Telegram
4. **查看日志**: 使用 `pm2 logs count-checker` 查看运行日志
5. **修改配置**: 如需修改检测时间或阈值，编辑 `count_check_daemon.py` 后重启服务

## 🎉 总结

✅ **每日凌晨2点计次检测功能已完成并上线！**

- 守护进程运行正常
- Telegram推送已配置
- PM2自动管理和重启
- 完善的日志记录
- 异常情况自动提醒

系统将在每天凌晨2点自动检测计次，如果发现异常（计次<2）会立即通过Telegram通知您！
