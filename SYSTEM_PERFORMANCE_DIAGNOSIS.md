# 🔍 系统性能诊断报告

**诊断时间**: 2026-01-04 02:50:00  
**运行时长**: 3天11分钟

---

## 📊 系统状态总览

### ✅ 整体状况：正常
- **CPU 负载**: 0.09, 0.17, 0.12 (正常)
- **CPU 使用率**: 14.3% user, 14.3% system, 71.4% idle (正常)
- **内存使用**: 1.0GB / 7.8GB (13%) ✅
- **可用内存**: 6.7GB ✅
- **磁盘使用**: 18GB / 26GB (67%) ⚠️

---

## ⚠️ 发现的问题

### 1. 磁盘空间使用率较高 (67%)

**原因**:
- 两个大数据库占用: 
  - `crypto_data_backup_20260102_124047.db` (1.9GB)
  - `crypto_data_corrupted.db` (1.9GB)
- SAR斜率数据库: `sar_slope_data.db` (505MB)
- 日志文件可能占用较大空间

**影响**: 
- 磁盘空间不足可能导致数据库写入变慢
- 日志文件过大可能影响IO性能

**建议**:
1. 清理或归档两个大数据库（如果不再需要）
2. 定期清理日志文件
3. 对数据库执行VACUUM优化

---

### 2. Flask应用内存占用较高 (217MB)

**进程**: `python3 app_new.py` (PID 375952)
- **内存**: 217MB (2.6%)
- **CPU**: 6.1%
- **重启次数**: 119次 ⚠️

**原因**:
- Flask应用重启次数过多，可能存在内存泄漏或异常退出
- 频繁的API请求（锚点系统相关）

**影响**:
- 内存占用持续增长
- 应用频繁重启影响服务稳定性

**建议**:
1. 检查Flask应用内存泄漏问题
2. 优化数据库查询，减少内存占用
3. 考虑使用gunicorn + 多worker模式

---

### 3. 数据库文件过多

**当前数据库文件**: 14个
- 包含两个1.9GB的历史数据库
- 一个空的support_resistance.db
- 一个12KB的crypto_data_fixed.db

**影响**:
- 占用磁盘空间
- 可能导致维护困难

**建议**:
1. 删除或归档不再使用的数据库
2. 合并小数据库
3. 定期清理临时数据库

---

### 4. 支撑压力线数据库为空

**问题**: `support_resistance.db` (0B)

**影响**:
- 支撑压力线系统可能无法正常工作
- 可能需要重新初始化或迁移数据

**建议**:
1. 检查支撑压力线系统是否正常运行
2. 从其他数据库迁移数据（如crypto_data_*.db）
3. 重新初始化数据库结构

---

## 🚀 性能优化建议

### 立即执行

1. **清理大数据库**
```bash
# 如果确认不再需要这两个数据库
rm /home/user/webapp/databases/crypto_data_backup_20260102_124047.db
rm /home/user/webapp/databases/crypto_data_corrupted.db
# 可释放约3.8GB空间
```

2. **清理日志文件**
```bash
# 清理30天前的日志
find /home/user/webapp/logs -name "*.log" -mtime +30 -delete

# 或者只保留最近7天的日志
find /home/user/webapp/logs -name "*.log" -mtime +7 -delete
```

3. **优化数据库**
```bash
cd /home/user/webapp
python3 << 'PYEOF'
import sqlite3

databases = [
    'databases/crypto_data.db',
    'databases/sar_slope_data.db',
    'databases/anchor_system.db',
    'databases/trading_decision.db',
    'databases/fund_monitor.db'
]

for db in databases:
    print(f"优化 {db}...")
    conn = sqlite3.connect(db)
    conn.execute('VACUUM')
    conn.close()
    print(f"  ✓ 完成")
PYEOF
```

### 中期优化

1. **Flask应用优化**
   - 添加连接池管理
   - 优化数据库查询
   - 使用缓存减少重复查询
   - 监控内存使用，及时释放资源

2. **PM2配置优化**
   - 设置合理的max_memory_restart
   - 配置日志轮转
   - 调整重启策略

3. **数据库分离**
   - 考虑将大数据库移到独立存储
   - 使用只读副本分担查询压力

---

## 📈 当前性能指标

### CPU
- **平均负载**: 0.09, 0.17, 0.12 (1/5/15分钟)
- **空闲率**: 71.4%
- **状态**: ✅ 正常

### 内存
- **总内存**: 7.8GB
- **已用**: 1.0GB (13%)
- **缓存**: 5.5GB
- **可用**: 6.7GB
- **状态**: ✅ 正常

### 磁盘
- **总空间**: 26GB
- **已用**: 18GB (67%)
- **可用**: 8.7GB
- **状态**: ⚠️ 需要关注

### 网络
- **ESTABLISHED连接数**: 17
- **状态**: ✅ 正常

---

## 🔧 PM2进程监控

| 进程名 | 状态 | 内存 | CPU | 重启次数 | 备注 |
|--------|------|------|-----|---------|------|
| flask-app | ✅ | 212MB | 6.1% | 119 | ⚠️ 重启过多 |
| gdrive-detector | ✅ | 57MB | 0.5% | 9 | 正常 |
| profit-extremes-tracker | ✅ | 35MB | 0.1% | 8 | 正常 |
| support-resistance-collector | ✅ | 28MB | 1.9% | 1 | 正常 |
| escape-stats-recorder | ✅ | 25MB | 0% | 4 | 正常 |
| escape-signal-recorder | ✅ | 25MB | 0% | 2 | 正常 |
| protect-pairs | ✅ | 24MB | 0% | 2 | 正常 |
| sub-account-opener | ✅ | 24MB | 0% | 2 | 正常 |
| telegram-notifier | ✅ | 22MB | 0% | 0 | 正常 |
| sub-account-super-maintenance | ✅ | 21MB | 0% | 2 | 正常 |
| anchor-maintenance | ✅ | 20MB | 0% | 11 | 正常 |
| support-snapshot-collector | ✅ | 11MB | 0.1% | 0 | 正常 |

**总计**: 12个进程，总内存约500MB

---

## 🎯 结论

**系统整体状态良好**，但存在以下需要注意的问题：

1. ⚠️ **磁盘空间使用率67%** - 建议清理大数据库和日志
2. ⚠️ **Flask应用重启119次** - 需要排查稳定性问题
3. ⚠️ **support_resistance.db为空** - 需要修复或初始化

**卡顿的可能原因**:
1. 磁盘空间不足导致数据库写入变慢
2. 大数据库查询导致IO阻塞
3. Flask应用频繁重启影响响应速度

**建议优先执行**:
1. 清理两个1.9GB的大数据库（可释放3.8GB）
2. 优化Flask应用，减少重启次数
3. 清理日志文件
4. 对数据库执行VACUUM优化

---

*诊断时间: 2026-01-04 02:50:00*  
*报告生成: 2026-01-04 02:52:00*
