# 子账户最大持仓数限制功能说明

## 功能概述

为子账户添加了最大持仓数限制，每个子账户最多可以持有 **10个不同的交易对**。这个限制可以：
- 防止过度分散资金
- 控制风险敞口
- 便于账户管理

## 实现细节

### 1. 配置说明

在 `sub_account_config.json` 中为每个子账户添加了 `max_positions` 字段：

```json
{
  "sub_accounts": [
    {
      "account_name": "Wu666666",
      "api_key": "...",
      "secret_key": "...",
      "passphrase": "...",
      "max_positions": 10,  // 最大持仓数，默认10
      "enabled": true,
      "maintenance_config": {
        ...
      }
    }
  ]
}
```

### 2. 生效范围

持仓数限制在以下场景生效：

#### a) 手动开仓 API
- 路径：`/api/anchor/open-sub-account-position`
- 逻辑：
  1. 获取当前子账户的所有持仓
  2. 统计不同交易对的数量（一个交易对可能有多空两个方向）
  3. 如果当前交易对不在持仓列表中，且已达到上限，则拒绝开仓
  4. 如果当前交易对已有持仓（无论多空），则允许加仓

#### b) 自动开仓守护进程
- 文件：`sub_account_opener_daemon.py`
- 逻辑：
  1. 在检查每个子账户时，首先统计当前持仓数
  2. 如果已达到最大限制，跳过该子账户的所有新开仓操作
  3. 在循环中每次尝试开仓前，再次检查是否会超过限制
  4. 成功开仓后，更新持仓统计

### 3. 统计规则

**重要**：持仓数统计的是**不同交易对的数量**，而不是持仓方向的数量。

例如：
- `BTC-USDT-SWAP` 多头 + `BTC-USDT-SWAP` 空头 = **1个交易对**
- `ETH-USDT-SWAP` 多头 = **1个交易对**
- 总计：**2个交易对**

### 4. 限制行为

当子账户达到最大持仓数时：

#### 手动开仓：
```json
{
  "success": false,
  "message": "已达到最大持仓限制（10个交易对），当前持有：10个"
}
```

#### 自动开仓：
```
⚠️ 子账号 Wu666666 已达到最大持仓限制 (10个)，跳过开仓
```

## 使用场景

### 场景1：子账户已持有10个交易对
```
当前持仓：
1. BTC-USDT-SWAP (多)
2. ETH-USDT-SWAP (多)
3. BNB-USDT-SWAP (空)
4. SOL-USDT-SWAP (多)
5. XRP-USDT-SWAP (空)
6. ADA-USDT-SWAP (多)
7. DOGE-USDT-SWAP (多)
8. DOT-USDT-SWAP (空)
9. LINK-USDT-SWAP (多)
10. UNI-USDT-SWAP (多)

操作结果：
- ❌ 开新仓位（如AVAX）：拒绝
- ✅ 为BTC加仓：允许
- ✅ 开BTC空仓：允许（同一交易对）
```

### 场景2：子账户持有9个交易对
```
当前持仓：9/10 个交易对

操作结果：
- ✅ 开第10个交易对：允许
- ❌ 开第11个交易对：拒绝
```

## 日志示例

### 1. 持仓数正常
```
🔍 检查子账号: Wu666666
   子账号已有持仓: 8个 (BTC-USDT-SWAP, ETH-USDT-SWAP, BNB-USDT-SWAP, ...)
   持仓限制: 8/10 个交易对
   ✅ 下跌强度等级5满足条件（>=5）
   🚀 准备开仓 10U...
   ✅ 开仓成功: SOL-USDT-SWAP short 10U
   📊 更新后持仓: 9/10 个交易对
```

### 2. 达到最大限制
```
🔍 检查子账号: Wu666666
   子账号已有持仓: 10个 (BTC-USDT-SWAP, ETH-USDT-SWAP, ...)
   持仓限制: 10/10 个交易对
   ⚠️ 子账号 Wu666666 已达到最大持仓限制 (10个)，跳过开仓
```

### 3. API开仓被拒绝
```
✅ 持仓检查通过: 当前 10/10 个交易对
⚠️ 子账户 Wu666666 已持有 10 个交易对，达到最大限制 10

返回响应：
{
  "success": false,
  "message": "已达到最大持仓限制（10个交易对），当前持有：10个"
}
```

## 配置修改

如需修改最大持仓数限制：

1. 编辑 `sub_account_config.json`
2. 修改 `max_positions` 字段
3. 重启相关服务：
   ```bash
   pm2 restart flask-app sub-account-opener
   ```

## 代码位置

### 1. API开仓检查
- 文件：`app_new.py`
- 函数：`open_sub_account_position()`
- 行号：约17391-17450

### 2. 自动开仓检查
- 文件：`sub_account_opener_daemon.py`
- 函数：`check_and_open_positions()`
- 行号：约344-365 和 398-433

### 3. 配置文件
- 文件：`sub_account_config.json`
- 字段：`max_positions`（默认10）

## 注意事项

1. **平仓后自动恢复**：当平仓后持仓数减少，系统会自动允许新开仓
2. **同交易对不受限**：对已持有的交易对加仓或反向开仓不受限制
3. **配置即时生效**：修改配置后需重启服务才能生效
4. **默认值**：如果配置中未设置 `max_positions`，默认为10
5. **检查失败处理**：如果持仓检查API失败，系统会继续尝试开仓，避免因检查失败影响正常交易

## 测试验证

### 当前状态
```bash
# 查看子账户开仓守护进程日志
pm2 logs sub-account-opener --lines 50

# 查看当前持仓数
curl "http://localhost:5000/api/anchor-system/sub-account-positions" | jq '.data[0].positions | length'
```

### 实际测试结果
```
📊 主账号亏损仓位: 2个

🔍 检查子账号: Wu666666
   子账号已有持仓: 10个 (LINK-USDT-SWAP, TON-USDT-SWAP, SOL-USDT-SWAP, CRO-USDT-SWAP, STX-USDT-SWAP, TAO-USDT-SWAP, LDO-USDT-SWAP, CRV-USDT-SWAP, BNB-USDT-SWAP, CFX-USDT-SWAP)
   持仓限制: 10/10 个交易对
   ⚠️ 子账号 Wu666666 已达到最大持仓限制 (10个)，跳过开仓
```

✅ **功能正常工作！**

## 更新记录

- **2026-01-03**：首次实现最大持仓数限制功能
  - 添加配置字段 `max_positions`
  - 实现手动开仓API检查
  - 实现自动开仓守护进程检查
  - 添加详细日志输出

---

**提交记录**：`591882e` - feat: 添加子账户最大持仓数限制
