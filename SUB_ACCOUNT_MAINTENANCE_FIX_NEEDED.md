# 子账户维护逻辑需要修复

## 问题现状

### CRO-USDT-SWAP 超级维护失败

**症状**：
```
[2025-12-31 23:32:56] 🔧 执行超级维护: CRO-USDT-SWAP long
[2025-12-31 23:32:56]    当前收益率: -10.94%
[2025-12-31 23:32:56]    当前维护次数: 0/3
[2025-12-31 23:32:56]    本次维护金额: 100U
[2025-12-31 23:32:56]    本次目标保证金: 10U
[2025-12-31 23:32:58] ❌ 超级维护失败: 开仓失败: All operations failed
```

**详细错误**：
```
📤 开仓请求: {'instId': 'CRO-USDT-SWAP', 'tdMode': 'cross', ...}
❌ 完整响应: {'sCode': '51008', 'sMsg': 'Order failed. Insufficient USDT margin in account'}
```

## 根本原因分析

### 1. 使用了全仓模式（已修复）
**问题**：子账户维护使用 `'tdMode': 'cross'`（全仓模式）
**后果**：账户总保证金不足，导致开仓失败
**修复**：已改为 `'tdMode': 'isolated'`（逐仓模式）

### 2. 缺少"先平掉旧持仓"步骤（❌ 未修复）
**问题**：子账户维护流程：
```
第零步：增加保证金
第一步：开仓新持仓
第二步：平掉多余仓位
```

**后果**：
- 旧持仓还在（如CRO 108张）
- 新开仓（如10928张）
- 总持仓 = 108 + 10928 = 11036张！
- 保证金严重不足！

**对比主账号**（已修复）：
```
第1步：平掉旧持仓（释放保证金）  ← 关键！
第2步：开仓新持仓
第3步：平到目标保证金
```

## 需要修改的代码

### 文件：`app_new.py`
### 函数：`maintain_sub_account()` (约15287-15700行)

### 当前流程 ❌
```python
# 第零步：向逐仓仓位增加保证金
margin_body = {
    'instId': inst_id,
    'posSide': pos_side,
    'type': 'add',
    'amt': str(round(required_margin, 2)),
    'ccy': 'USDT'
}

# 第一步：开仓
open_order_body = {
    'instId': inst_id,
    'tdMode': 'cross',  # ← 已改为 isolated
    'side': side,
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(order_size)
}

# 第二步：平掉多余仓位
close_order_body = {
    'instId': inst_id,
    'tdMode': 'cross',  # ← 已改为 isolated
    'side': close_side,
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(close_size)
}
```

### 需要改成 ✅
```python
# 第1步：平掉旧持仓（释放保证金）← 新增！
old_close_body = {
    'instId': inst_id,
    'tdMode': 'isolated',
    'side': close_side,
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(pos_size)  # 全部平掉，支持小数
}

# 第2步：开仓新持仓
open_order_body = {
    'instId': inst_id,
    'tdMode': 'isolated',
    'side': side,
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(order_size),
    'lever': str(lever)  # 逐仓需要指定杠杆
}

# 第3步：平到目标保证金
close_order_body = {
    'instId': inst_id,
    'tdMode': 'isolated',
    'side': close_side,
    'posSide': pos_side,
    'ordType': 'market',
    'sz': str(close_size)
}
```

## 修复优先级

### 🔴 高优先级（必须）
1. ✅ 将 `tdMode` 从 `cross` 改为 `isolated` - **已完成**
2. ❌ 添加"第1步：平掉旧持仓"逻辑 - **待完成**
3. ❌ 移除"第零步：增加保证金"（不再需要）- **待完成**

### 🟡 中优先级（建议）
4. ❌ 统一主账号和子账户维护流程 - **待完成**
5. ❌ 添加详细的成交明细记录 - **待完成**
6. ❌ 更新TG通知格式 - **待完成**

## 测试计划

### 测试用例：CRO-USDT-SWAP long
- 当前持仓：108张
- 保证金：20.59 USDT
- 收益率：-10.73%
- 应触发：超级维护

### 预期结果
1. 第1步：平掉旧持仓108张，释放保证金20.59U
2. 第2步：开仓新持仓10928张（100U*10杠杆/0.0915价格）
3. 第3步：平掉多余仓位，保留10U对应的仓位（约1093张）

### 验证点
- ✅ 订单全部成功
- ✅ 最终保证金约10U
- ✅ 收益率重置
- ✅ 无51008错误

## 当前状态

- ✅ `tdMode` 已改为 `isolated`
- ✅ Flask服务已重启
- ⏳ 等待自动触发测试
- ❌ **核心问题未修复**：仍缺少"先平掉旧持仓"逻辑

## 后续步骤

1. 监控下一次自动维护是否还会失败
2. 如果失败，立即修改添加"第1步平掉旧持仓"
3. 手动测试修复后的流程
4. 提交代码并推送GitHub
