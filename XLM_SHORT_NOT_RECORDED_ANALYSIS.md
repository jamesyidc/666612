# XLM做空未被记录到历史极值的问题分析

## 问题描述
XLM做空持仓存在，但历史极值记录中没有相应数据。

## 根本原因

### 1. 数据库写满 (`database or disk is full`)
- trading_decision.db 有 1,701 条记录
- 实际只应该有 28 条（每个持仓1条）
- **冗余数据：1,673 条**

### 2. 脚本逻辑错误
**问题代码**（position_profit_extremes_tracker.py 第243-246行）：
```python
# 获取开仓时间
open_time = get_position_open_time(inst_id, pos_side)
if not open_time:
    print(f"⚠️  {inst_id} {pos_side} 无法获取开仓时间，使用当前时间")
    open_time = get_beijing_time()  # ❌ 错误：每分钟都创建新记录
```

**后果**：
- 每分钟扫描一次持仓
- 每次都用**当前时间**作为 `open_time`
- 导致每个持仓每分钟创建一条新记录
- XLM做空产生了 **809条记录**（应该只有1条）

### 3. 历史极值未写入
**问题代码**（第141-148行）：
```python
# 插入历史极值记录
if pos_info:
    insert_to_history_records(
        inst_id, pos_side, 'max_profit', current_profit_rate,
        pos_info.get('pos_size', 0),
        pos_info.get('avg_price', 0),
        pos_info.get('mark_price', 0)
    )
```

但由于数据库已满，写入失败。

## 数据分析

### XLM做空的极值数据（已保存在数据库中）
```
XLM-USDT-SWAP short:
  最高盈利: 13.70%  ✅
  最大亏损: -28.79% ✅
  当前盈亏: 13.70%
```

### 冗余记录统计
- SOL-USDT-SWAP short: 866 条记录（应为1条）
- XLM-USDT-SWAP short: 809 条记录（应为1条）
- 总删除：1,673 条冗余记录

## 已采取的修复措施

### 1. 数据清理 ✅
- 创建临时表 `position_profit_extremes_clean`
- 合并每个持仓的极值数据（取最大盈利、最小亏损）
- 删除冗余记录
- 结果：从 1,701 条减少到 28 条

### 2. 添加UNIQUE约束 ✅
```sql
UNIQUE(inst_id, pos_side)
```
防止同一持仓产生多条记录。

## 仍需解决的问题

### 1. 开仓时间获取失败
```
⚠️  XLM-USDT-SWAP short 无法获取开仓时间，使用当前时间
```

**原因**：
- `get_position_open_time()` 从 `position_opens` 表查询
- 可能该表没有XLM做空的开仓记录
- 或者数据结构不匹配

**需要检查**：
- position_opens 表是否有XLM-USDT-SWAP short的记录
- created_at、updated_time、timestamp 字段是否有值

### 2. 数据库锁定问题
```
❌ database is locked
```

多个进程可能同时访问 trading_decision.db。

### 3. UNIQUE约束冲突
```
❌ UNIQUE constraint failed: position_profit_extremes.inst_id, position_profit_extremes.pos_side
```

因为脚本仍然试图 INSERT 而不是 UPDATE。

## 推荐的最终解决方案

### 方案1：修改脚本逻辑
1. 不再依赖 `open_time` 作为唯一标识
2. 改用 `(inst_id, pos_side)` 作为唯一标识
3. 总是 `INSERT OR REPLACE`，而不是先查询再决定 INSERT/UPDATE

### 方案2：简化数据结构
- 删除 `open_time` 字段（不需要）
- 只保留当前持仓的极值
- 历史极值写入 `anchor_real_profit_records` 表（前端展示用）

### 方案3：修复 position_opens 表
- 确保每次开仓都记录到 position_opens
- 或者使用 OKEx API 的 cTime 字段作为开仓时间

## 当前状态

### ✅ 已修复
- 数据库空间问题（删除1,673条冗余记录）
- XLM做空极值数据已保存（最高13.70%，最低-28.79%）

### ⚠️ 部分修复
- 添加了UNIQUE约束，但导致脚本INSERT失败

### ❌ 未修复
- 历史极值未写入 `anchor_real_profit_records` 表（前端需要此表）
- 开仓时间获取失败
- 脚本逻辑需要重构

## 建议下一步操作

1. **立即执行**：手动将XLM做空的最高盈利13.70%写入 `anchor_real_profit_records`
2. **短期修复**：修改脚本使用 `INSERT OR REPLACE` 而不是查询后决定
3. **长期优化**：重构脚本，简化数据结构，移除对 `open_time` 的依赖

## 相关文件
- `/home/user/webapp/position_profit_extremes_tracker.py` - 守护进程脚本
- `/home/user/webapp/trading_decision.db` - 持仓极值数据库
- `/home/user/webapp/anchor_system.db` - 历史记录数据库（anchor_real_profit_records表）

## 时间线
- 2025-12-29 17:53:18 - 最早记录
- 2026-01-03 12:56:53 - 最新记录
- 2026-01-03 13:00 - 数据清理完成
- 5天内累积了 1,701 条记录（平均每天340条，每分钟0.236条）
