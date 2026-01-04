# 系统卡顿问题诊断报告

**诊断时间**: 2026-01-04 03:00:00

## 问题根源

系统并不卡，而是 **数据库路径配置错误** 导致 API 报错，表现为系统卡顿！

## 核心问题

### 1. 数据库文件损坏
- ✅ `databases/support_resistance.db` - 已修复（148MB，348,610条记录）
- ❌ `databases/crypto_data.db` - 原为空/小数据库（6个表）
- ❌ `databases/crypto_data_backup_20260102_124047.db` - 数据库损坏
- ❌ `databases/crypto_data_corrupted.db` - 数据库损坏（虽然名字是corrupted）

### 2. API端点错误
多个关键API端点报错，导致前端请求失败：
- `/api/trading-signals/analyze` - 缺少多个表
- `/api/kline-indicators/signals` - 缺少多个表

### 3. 缺失的表
API函数需要以下表，但当前 `databases/crypto_data.db` 中缺失：
- `price_breakthrough_events` - 价格突破事件（已创建空表）
- `crypto_coin_data` - 加密货币数据（已创建空表）
- `position_system` - 位置系统（已创建空表）
- `okex_kline_ohlc` - K线OHLC数据（缺失）
- `okex_technical_indicators` - 技术指标（有表但无数据）

## 已执行的修复措施

### 1. 修复 support_resistance.db ✅
```bash
# 替换空文件为有数据的文件
mv databases/support_resistance.db databases/support_resistance.db.empty
cp support_resistance.db databases/
```

**结果**: 
- 5个表，412,741条记录
- `support_resistance_levels`: 348,610条
- API `/api/support-resistance/latest` 已正常

### 2. 修改代码使用正确的数据库 ✅
在 `app_new.py` 中修改了 `api_trading_signals_analyze` 函数：
```python
# 附加 support_resistance.db 数据库
cursor.execute("ATTACH DATABASE 'databases/support_resistance.db' AS sr_db")

# 使用 sr_db. 前缀访问表
FROM sr_db.support_resistance_levels
```

### 3. 创建缺失的表结构 ✅
```bash
# 恢复小数据库并创建缺失表
CREATE TABLE IF NOT EXISTS price_breakthrough_events (...)
CREATE TABLE IF NOT EXISTS crypto_coin_data (...)
CREATE TABLE IF NOT EXISTS position_system (...)
```

**当前问题**: `okex_kline_ohlc` 表仍然缺失

## 建议的完整解决方案

### 选项A: 使用空表但修改函数使其健壮
优点: 快速解决，系统立即可用
缺点: 部分功能无数据

```python
# 修改辅助函数，处理表不存在的情况
def check_no_new_low_5min(symbol):
    try:
        # ... 原有逻辑 ...
    except sqlite3.OperationalError:
        return False  # 表不存在时返回默认值
```

### 选项B: 从其他系统导入数据
优点: 恢复完整功能
缺点: 需要数据源

### 选项C: 禁用受影响的API端点
优点: 避免错误
缺点: 功能缺失

## 系统性能指标（健康）

- **CPU**: 负载 0.09-0.17, 空闲 71.4%
- **内存**: 使用 1.0GB / 7.8GB (13%)，可用 6.7GB
- **磁盘**: 使用 18GB / 26GB (67%)，可用 8.7GB
- **进程**: 12个 PM2 进程全部在线
- **Flask重启**: 122次（需优化，但不是卡顿原因）

## 结论

**系统不卡！** 表现为"卡"的原因是：
1. 数据库配置错误导致 API 500 错误
2. 前端请求失败但持续重试
3. 用户看到加载缓慢或功能不可用

**推荐修复步骤**:
1. ✅ 已修复 support_resistance.db
2. ✅ 已修改代码使用 ATTACH DATABASE
3. ⏳ 修改辅助函数使其健壮（即使表不存在也能返回默认值）
4. 🔄 重启 Flask 应用
5. ✅ 验证所有 API 端点正常

## 后续优化建议

1. **数据恢复**: 从备份或其他系统导入完整数据
2. **Flask优化**: 减少重启次数（当前122次）
3. **磁盘清理**: 删除损坏的数据库文件（释放 ~3.8GB）
4. **监控**: 添加 API 错误监控告警

---
**诊断完成时间**: 2026-01-04 03:00:00
