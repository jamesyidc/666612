# 加密货币交易系统 - 完整备份

## 📊 备份信息

- **备份时间**: 2026-01-04 08:36:06
- **备份版本**: v3.0 完整版
- **源目录**: /home/user/webapp
- **原始大小**: 5.5GB
- **压缩后大小**: 3.6G
- **分片数量**: 3 个
- **每片大小**: 最大 1300m

## 📦 备份内容

### 完整内容清单

1. **Git仓库** (2.9GB)
   - 完整的Git历史
   - 所有分支和标签
   - .git目录完整保留

2. **数据库** (725MB)
   - crypto_data.db (1.1MB) - 核心数据
   - trading_decision.db (8.3MB) - 交易决策
   - anchor_system.db (21MB) - 锚点系统
   - fund_monitor.db (63MB) - 资金监控
   - support_resistance.db (151MB) - 支撑压力
   - sar_slope_data.db (505MB) - SAR斜率
   - v1v2_data.db (12MB) - V1V2数据
   - 其他数据库文件

3. **日志文件** (583MB)
   - 所有系统运行日志
   - PM2日志
   - 采集器日志
   - 错误日志

4. **源代码**
   - app_new.py - 主Flask应用
   - 所有Python脚本
   - source_code/ 目录
   - 配置文件

5. **Web文件**
   - templates/ - HTML模板
   - static/ - 静态资源

6. **配置和文档**
   - 所有配置文件
   - Markdown文档
   - PM2配置

## 🚀 快速恢复（3步）

### 1. 准备环境

```bash
# 确保所有分片文件都在同一目录
ls -lh webapp_full_20260104_083239.tar.gz.part*
```

### 2. 执行恢复

```bash
chmod +x restore.sh
./restore.sh
```

### 3. 验证系统

```bash
# 检查服务状态
pm2 list

# 测试API
curl http://localhost:5000/api/latest

# 访问页面
http://localhost:5000/
```

## 📋 23个子系统清单

所有23个子系统完整备份，包括：

1. 历史数据查询系统
2. 交易信号监控系统
3. 恐慌清洗指数系统
4. 比价系统
5. 星星系统
6. 币种池系统
7. 实时市场原始数据
8. 数据采集监控
9. 深度图得分
10. 深度图可视化
11. 平均分页面
12. OKEx加密指数
13. 位置系统
14. 支撑压力线系统
15. 决策交易信号系统
16. 决策-K线指标系统
17. V1V2成交系统
18. 1分钟涨跌幅系统
19. Google Drive监控系统
20. Telegram消息推送系统
21. 资金监控系统
22. 锚点系统（实盘）
23. 自动交易系统

## 🎯 6大核心系统

重点保障1:1还原，部署后直接可用：

1. **SAR斜率系统**
   - 数据库: sar_slope_data.db (505MB)
   - 采集器: sar_slope_collector.py
   - 页面: /sar-slope

2. **历史数据查询系统**
   - 数据库: crypto_data.db
   - 页面: /query, /escape-stats-history

3. **恐慌清洗指数系统**
   - 数据库: crypto_data.db (panic_wash_index表)
   - 页面: /panic

4. **支撑压力线系统**
   - 数据库: support_resistance.db (148MB)
   - 采集器: support_resistance_collector.py
   - 页面: /support-resistance

5. **锚点系统（实盘）**
   - 数据库: anchor_system.db + trading_decision.db
   - 守护进程: sub_account_opener_daemon.py
   - 页面: /anchor-system-real

6. **自动交易系统**
   - 数据库: crypto_data.db (liquidation表)
   - 页面: /liquidation-stats

## 📝 文件列表

```
webapp_full_20260104_083239.tar.gz          # 完整压缩包
webapp_full_20260104_083239.tar.gz.part01   # 分片1
webapp_full_20260104_083239.tar.gz.part02   # 分片2
...
checksums.md5                   # MD5校验和
restore.sh                      # 恢复脚本
README_FULL_BACKUP.md          # 本文件
```

## 🔐 校验文件完整性

```bash
# 验证所有文件的MD5
md5sum -c checksums.md5
```

## ⚠️ 重要提醒

1. **数据安全**
   - 备份包含生产数据库
   - 包含API密钥和配置
   - 请妥善保管，建议加密

2. **存储建议**
   - 保存到AI Drive: /mnt/aidrive/
   - 异地备份
   - 定期验证备份完整性

3. **恢复前检查**
   - 确保所有分片文件完整
   - 验证MD5校验和
   - 备份现有系统（如有）

## 📞 技术支持

如恢复过程中遇到问题，请检查：
1. backup.log - 备份日志
2. PM2日志: pm2 logs
3. 系统日志: /home/user/webapp/logs/

---

**备份完成时间**: 2026-01-04 08:36:06
**备份质量**: ⭐⭐⭐⭐⭐ 完整版
**恢复难度**: ⭐⭐ 简单（3步完成）
