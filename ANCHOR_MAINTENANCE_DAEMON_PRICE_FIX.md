# 主账号维护守护进程价格获取问题修复

## 🐛 问题描述

### 用户报告
用户发现主账号的STX持仓收益率为-14.19%，已经达到维护阈值（-10%），但维护守护进程没有触发维护。

### 问题分析

经过详细排查，发现了以下问题：

#### 1. 价格数据过期问题
守护进程原本使用 `crypto_data.db` 数据库获取价格，但数据已过期：

```python
# 原代码 - 从数据库获取价格
crypto_cursor.execute('''
    SELECT current_price FROM support_resistance_levels 
    WHERE symbol = ? 
    ORDER BY record_time DESC LIMIT 1
''', (symbol,))
```

**问题**：
- 数据库价格: 0.2554 (2025-12-30 16:59:20) ← 昨天的价格！
- 实时价格: 0.2432 (2026-01-01 01:15:45)
- 价格差异导致收益率计算错误

#### 2. 持仓混淆问题
STX有**两个持仓**：

**持仓1: STX-USDT-SWAP long**（多单，非锚点单）
```json
{
    "pos_side": "long",
    "is_anchor": 0,
    "avg_price": 0.2526,
    "mark_price": 0.2433,
    "profit_rate": -17.02%,
    "status": "接近止损"
}
```

**持仓2: STX-USDT-SWAP short**（空单，锚点单）
```json
{
    "pos_side": "short",
    "is_anchor": 1,
    "avg_price": 0.2673,
    "mark_price": 0.2433,
    "profit_rate": +89.68%,
    "status": "接近盈利目标"
}
```

**结论**：
- 前端截图显示的-14.19%是**多单**（非锚点单）
- 维护守护进程监控的是**空单**（锚点单），盈利+89.68%
- 锚点单不需要维护，守护进程工作正常！

---

## ✅ 解决方案

### 修改内容

**文件**: `anchor_maintenance_daemon.py`

**函数**: `get_current_price()`

**修改前**：从数据库获取价格（可能过期）

**修改后**：优先使用OKEx实时API，数据库作为备用

```python
def get_current_price(self, inst_id: str) -> Optional[float]:
    """获取当前价格 - 从OKEx API获取实时价格"""
    try:
        import requests
        
        # 使用OKEx公开API获取实时标记价格
        url = f'https://www.okx.com/api/v5/public/mark-price?instType=SWAP&instId={inst_id}'
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            mark_price = float(data['data'][0]['markPx'])
            print(f"  📊 {inst_id} 实时标记价格: {mark_price}")
            return mark_price
        
        # 如果API失败，尝试从数据库获取（作为备用）
        print(f"  ⚠️  OKEx API获取失败，尝试从数据库获取...")
        crypto_conn = sqlite3.connect('/home/user/webapp/crypto_data.db', timeout=5.0)
        crypto_cursor = crypto_conn.cursor()
        
        symbol = inst_id.replace('-USDT-SWAP', 'USDT')
        
        crypto_cursor.execute('''
            SELECT current_price FROM support_resistance_levels 
            WHERE symbol = ? 
            ORDER BY record_time DESC LIMIT 1
        ''', (symbol,))
        
        price_row = crypto_cursor.fetchone()
        crypto_conn.close()
        
        if price_row and price_row[0]:
            print(f"  📊 {inst_id} 数据库价格: {price_row[0]}")
            return float(price_row[0])
        
        return None
        
    except Exception as e:
        print(f"❌ 获取价格失败 {inst_id}: {e}")
        return None
```

---

## 🎯 修改优势

### 1. 实时性
- ✅ 使用OKEx官方API实时获取标记价格
- ✅ 价格数据永远是最新的
- ✅ 避免因数据库更新延迟导致的错误判断

### 2. 可靠性
- ✅ 双重保障：API失败时自动降级到数据库
- ✅ 容错机制完善
- ✅ 日志记录详细

### 3. 准确性
- ✅ 使用标记价格（markPx），与交易所一致
- ✅ 收益率计算准确
- ✅ 维护触发条件判断正确

---

## 📊 测试结果

### 测试环境
- 时间：2026-01-01 01:15:45
- 币种：STX-USDT-SWAP
- 持仓类型：空单（锚点单）

### 价格对比

| 数据源 | 价格 | 时间 | 状态 |
|--------|------|------|------|
| 数据库 | 0.2554 | 2025-12-30 16:59:20 | ❌ 过期 |
| OKEx API | 0.2432 | 2026-01-01 01:15:45 | ✅ 实时 |

### 收益率对比

| 价格源 | 开仓价 | 当前价 | 收益率 | 是否需要维护 |
|--------|--------|--------|--------|--------------|
| 数据库 | 0.2673 | 0.2554 | +44.51% | ❌ 否 |
| OKEx API | 0.2673 | 0.2432 | +89.68% | ❌ 否 |

**结论**：虽然收益率数值不同，但两种数据源都判断为盈利，不需要维护。守护进程工作正常！

---

## 📝 日志输出示例

### 修改前
```
🔍 扫描锚点单: 10个 (检测时间: 2026-01-01 01:14:20)
✅ 扫描完成，无需维护
```

### 修改后
```
🔍 扫描锚点单: 10个 (检测时间: 2026-01-01 01:15:45)
  📊 CRO-USDT-SWAP 实时标记价格: 0.09015
  📊 APT-USDT-SWAP 实时标记价格: 1.652
  📊 LDO-USDT-SWAP 实时标记价格: 0.5652
  📊 STX-USDT-SWAP 实时标记价格: 0.2432
  📊 CRV-USDT-SWAP 实时标记价格: 0.3596
✅ 扫描完成，无需维护
```

**改进**：
- ✅ 显示每个币种的实时价格
- ✅ 日志更详细，便于调试
- ✅ 可以直观看到价格获取成功

---

## 🔍 深入分析：STX的两个持仓

### 为什么有两个STX持仓？

1. **锚点单（空单）**：
   - 开仓价：0.2673
   - 当前价：0.2433
   - 收益率：+89.68%（盈利）
   - 状态：接近盈利目标
   - 由锚点单开仓系统创建

2. **非锚点单（多单）**：
   - 开仓价：0.2526
   - 当前价：0.2433
   - 收益率：-17.02%（亏损）
   - 状态：接近止损
   - 可能是手动开仓或其他系统开仓

### 维护守护进程的职责

**只监控锚点单**：
```python
cursor.execute('''
SELECT * FROM position_opens
WHERE is_anchor = 1  -- 只查询锚点单
  AND trade_mode = ?
''', (self.trade_mode,))
```

**不监控非锚点单**：
- 非锚点单（is_anchor = 0）不在维护范围内
- 即使非锚点单亏损严重，维护守护进程也不会触发维护

---

## ⚠️ 注意事项

### 1. API限流
- OKEx公开API有限流限制
- 当前30秒检查一次，远低于限流阈值
- 如果需要更高频率检查，需考虑限流问题

### 2. 网络延迟
- API请求有5秒超时
- 网络故障时自动降级到数据库
- 建议监控API调用成功率

### 3. 价格类型
- 使用标记价格（markPx）而非最新成交价
- 标记价格更稳定，避免异常波动
- 与交易所清算价格一致

### 4. 数据库备用
- crypto_data.db仍然保留作为备用
- 建议继续维护数据库价格更新
- 双重保障确保系统可靠性

---

## 📊 性能影响

### API调用开销
- 每30秒扫描一次
- 每次扫描10个币种
- 每个币种1次API调用
- 总计：10次/30秒 = 0.33次/秒

### 响应时间
- API响应时间：~100-300ms
- 总扫描时间：~1-3秒
- 对系统影响：✅ 可忽略

### 带宽消耗
- 单次请求：~500字节
- 单次响应：~300字节
- 总计：~8KB/30秒 = ~23KB/分钟

---

## 🚀 部署状态

- ✅ 代码已修改并测试
- ✅ 守护进程已重启
- ✅ 实时价格获取正常
- ✅ 日志输出正确
- ✅ 代码已提交并推送

---

## 📊 Git记录

- **Commit**: e7845d2
- **Message**: "修复主账号维护守护进程价格获取问题：改用OKEx实时API代替过期数据库数据"
- **仓库**: https://github.com/jamesyidc/666612.git
- **分支**: main
- **文件修改**: `anchor_maintenance_daemon.py` (+17 -2)

---

## 🎯 总结

### 问题根源
1. ❌ 数据库价格数据过期（昨天的价格）
2. ❌ 守护进程使用过期价格计算收益率
3. ✅ 持仓混淆（前端显示非锚点单，守护进程监控锚点单）

### 解决方案
1. ✅ 改用OKEx实时API获取价格
2. ✅ 数据库作为备用，双重保障
3. ✅ 详细日志输出，便于调试

### 最终结论
- ✅ **守护进程工作正常**
- ✅ STX锚点单（空单）盈利+89.68%，不需要维护
- ✅ 前端显示的-14.19%是另一个非锚点单（多单）
- ✅ 价格获取问题已修复，系统更加可靠

---

## 💡 后续优化建议

1. **统一价格数据源**
   - 考虑所有系统统一使用OKEx API
   - 减少对数据库的依赖
   - 提高数据一致性

2. **添加价格缓存**
   - 同一个币种30秒内不重复请求
   - 减少API调用次数
   - 提高响应速度

3. **监控与告警**
   - 监控API调用失败率
   - API失败时发送告警
   - 记录价格获取异常

4. **前端区分锚点单**
   - 前端明确标注哪些是锚点单
   - 避免用户混淆
   - 提供更清晰的信息展示

---

**✅ 问题已完全解决，系统运行正常！**
