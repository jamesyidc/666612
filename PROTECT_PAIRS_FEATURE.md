# 🛡️ 保护交易对功能说明

## 功能概述

保护交易对功能用于监控主账户的交易对数量，防止交易对意外减少。当检测到交易对减少时，系统会自动补1U保证金仓位。

## 功能特点

### 1. 自动监控
- **检查频率**: 每分钟检查一次
- **监控范围**: 主账户所有SWAP永续合约持仓
- **记录交易对**: 包含交易对名称和方向（long/short）

### 2. 自动补仓
- **触发条件**: 当前交易对数量少于保护列表中的数量
- **补仓金额**: 1 USDT保证金
- **补仓方式**: 市价单，全仓模式
- **补仓延迟**: 每次补仓间隔2秒，避免频繁下单

### 3. 智能更新
- **初始化**: 首次启动时自动记录当前所有交易对
- **动态更新**: 发现新交易对时自动添加到保护列表
- **持久化**: 保护列表保存在配置文件中

## 使用方法

### 1. 前端操作

访问锚点系统页面：
```
https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/anchor-system-real
```

找到子账户控制面板，勾选 **🛡️ 保护交易对** 开关。

### 2. 配置文件

配置保存在 `/home/user/webapp/sub_account_config.json`:

```json
{
  "protect_pairs_enabled": false,  // 是否启用保护
  "protect_pairs_config": {
    "check_interval": 60,          // 检查间隔（秒）
    "min_margin_usdt": 1,          // 最小保证金（USDT）
    "protected_pairs": [           // 保护的交易对列表
      "BTC-USDT-SWAP_long",
      "ETH-USDT-SWAP_short",
      ...
    ]
  }
}
```

### 3. 守护进程

守护进程名称: `protect-pairs`

**查看日志**:
```bash
pm2 logs protect-pairs
```

**重启进程**:
```bash
pm2 restart protect-pairs
```

**停止进程**:
```bash
pm2 stop protect-pairs
```

## 工作原理

### 1. 初始化阶段
```
1. 启动守护进程
2. 读取配置文件
3. 检查 protect_pairs_enabled 状态
4. 如果保护列表为空，获取当前持仓并初始化保护列表
```

### 2. 监控循环
```
每分钟执行一次：
1. 获取主账户当前持仓
2. 提取交易对列表（格式：instId_posSide）
3. 对比保护列表
4. 如果发现缺失，立即补仓
5. 如果发现新交易对，添加到保护列表
```

### 3. 补仓流程
```
对于每个缺失的交易对：
1. 解析交易对信息（instId, posSide）
2. 构造市价单
3. 提交OKX API
4. 记录操作日志
5. 等待2秒（避免频繁下单）
```

## 日志示例

### 正常运行
```
[2026-01-03 11:51:47] 📊 开始检查交易对保护...
[2026-01-03 11:51:48] 📊 当前持仓交易对数量: 27
[2026-01-03 11:51:48] ⏰ 等待60秒后进行下次检查...
```

### 初始化保护列表
```
[2026-01-03 11:52:48] 📊 当前持仓交易对数量: 27
[2026-01-03 11:52:48] ✅ 初始化保护交易对列表: 27个交易对
```

### 发现缺失并补仓
```
[2026-01-03 11:53:48] 📊 当前持仓交易对数量: 25
[2026-01-03 11:53:48] ⚠️ 发现丢失的交易对: {'BTC-USDT-SWAP_long', 'ETH-USDT-SWAP_short'}
[2026-01-03 11:53:48] 🔧 准备补仓: BTC-USDT-SWAP long 1U
[2026-01-03 11:53:49] ✅ 补仓成功: BTC-USDT-SWAP long 1U | 订单ID: 123456789
[2026-01-03 11:53:51] 🔧 准备补仓: ETH-USDT-SWAP short 1U
[2026-01-03 11:53:52] ✅ 补仓成功: ETH-USDT-SWAP short 1U | 订单ID: 987654321
```

### 发现新交易对
```
[2026-01-03 11:54:48] 📊 当前持仓交易对数量: 29
[2026-01-03 11:54:48] 📝 发现新交易对，添加到保护列表: {'SOL-USDT-SWAP_long', 'ADA-USDT-SWAP_short'}
```

## 注意事项

### 1. API权限
确保主账户API具有以下权限：
- 读取账户信息
- 交易权限（下单、撤单）

### 2. 保证金要求
- 补仓金额固定为1 USDT
- 请确保账户有足够的可用保证金
- 如果补仓失败，会记录错误日志

### 3. 开关控制
- 关闭保护开关后，守护进程不会进行检查
- 保护列表会保留在配置文件中
- 重新开启时，会基于当前保护列表继续监控

### 4. 交易对格式
保护列表中的交易对格式：
```
{instId}_{posSide}
例如: BTC-USDT-SWAP_long, ETH-USDT-SWAP_short
```

### 5. 补仓策略
- 使用市价单，确保成交
- 全仓模式（tdMode: cross）
- 每次补仓间隔2秒

## 配置更新

### 修改检查间隔
编辑配置文件 `sub_account_config.json`:
```json
{
  "protect_pairs_config": {
    "check_interval": 120  // 改为2分钟检查一次
  }
}
```

### 修改补仓金额
编辑配置文件 `sub_account_config.json`:
```json
{
  "protect_pairs_config": {
    "min_margin_usdt": 2  // 改为补2U
  }
}
```

### 手动编辑保护列表
编辑配置文件 `sub_account_config.json`:
```json
{
  "protect_pairs_config": {
    "protected_pairs": [
      "BTC-USDT-SWAP_long",
      "ETH-USDT-SWAP_short",
      "SOL-USDT-SWAP_long"
    ]
  }
}
```

修改后需要重启守护进程：
```bash
pm2 restart protect-pairs
```

## 相关文件

- **守护进程**: `/home/user/webapp/protect_pairs_daemon.py`
- **配置文件**: `/home/user/webapp/sub_account_config.json`
- **前端模板**: `/home/user/webapp/templates/anchor_system_real.html`
- **API接口**: `/api/sub-account/config` (GET/POST)

## 版本信息

- **创建时间**: 2026-01-03
- **Git Commit**: f7c8fe5
- **守护进程**: protect-pairs (PM2 进程ID: 20)

## 总结

保护交易对功能提供了一个自动化的交易对监控和补仓机制，确保主账户的交易对数量不会意外减少。通过前端开关可以方便地启用或关闭此功能，配置文件提供了灵活的参数调整能力。
