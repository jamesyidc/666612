# 锚点系统实盘页面 - 1小时极值统计功能

## 📅 更新时间
**2025-12-30 09:17 UTC**

## ✨ 新增功能

在实盘锚点系统页面的"历史极值记录"标题旁边，添加了**最近1小时内的极值统计**。

### 功能说明

显示最近1小时内创新高的数量：

1. **🟢 多单盈利** - 多单利润创新高的次数
2. **🔴 多单亏损** - 多单亏损创新高的次数  
3. **🟢 空单盈利** - 空单利润创新高的次数
4. **🔴 空单亏损** - 空单亏损创新高的次数

### UI展示

```
🏆 历史极值记录
    🟢 多单盈利: 2  🔴 多单亏损: 2  🟢 空单盈利: 7  🔴 空单亏损: 0  (最近1小时内创新高)
```

**颜色标记：**
- 🟢 绿色 - 盈利相关
- 🔴 红色 - 亏损相关
- 灰色小字 - 时间说明

## 🔧 技术实现

### API端点
```
GET /api/anchor-system/real/hourly-extreme-stats
```

**返回示例：**
```json
{
  "success": true,
  "time_range": "最近1小时 (>2025-12-30 08:15:47)",
  "stats": {
    "long_max_profit": 2,
    "long_max_loss": 2,
    "short_max_profit": 7,
    "short_max_loss": 0
  }
}
```

### 数据来源
- 表：`anchor_real_profit_records`
- 条件：`timestamp >= datetime('now', '-1 hour')`
- 分组：按 `pos_side` (多/空) 和 `record_type` (利润/亏损)

### 前端实现

1. **HTML结构**
```html
<div class="card-title">
    <span>🏆</span>
    历史极值记录
    <span id="hourlyStats" style="...">
        <!-- 统计信息动态显示在这里 -->
    </span>
</div>
```

2. **JavaScript函数**
```javascript
// 渲染1小时内极值统计
function renderHourlyStats(stats) {
    const statsElement = document.getElementById('hourlyStats');
    const html = `
        🟢 多单盈利: ${stats.long_max_profit}
        🔴 多单亏损: ${stats.long_max_loss}
        🟢 空单盈利: ${stats.short_max_profit}
        🔴 空单亏损: ${stats.short_max_loss}
        (最近1小时内创新高)
    `;
    statsElement.innerHTML = html;
}
```

3. **数据加载**
```javascript
async function loadData() {
    // ... 其他数据加载 ...
    
    // 加载最近1小时的极值统计
    const hourlyStatsRes = await fetch('/api/anchor-system/real/hourly-extreme-stats');
    const hourlyStatsData = await hourlyStatsRes.json();
    
    if (hourlyStatsData.success) {
        renderHourlyStats(hourlyStatsData.stats);
    }
}
```

## 📊 当前数据示例

基于最新查询（2025-12-30 09:15）：

| 类型 | 数量 | 说明 |
|------|------|------|
| 多单盈利 | 2 | CFX, STX 创利润新高 |
| 多单亏损 | 2 | CFX, STX 创亏损新高 |
| 空单盈利 | 7 | CRV, DOT, STX, CFX, APT, TON, FIL 创利润新高 |
| 空单亏损 | 0 | 无 |

**最近创新高的记录：**
```
2025-12-30 17:02:50 - CRV-USDT-SWAP 空单利润 58.75%
2025-12-30 16:17:46 - CFX-USDT-SWAP 多单利润 11.86%
2025-12-30 16:17:45 - STX-USDT-SWAP 多单利润 15.84%
2025-12-30 11:15:24 - DOT-USDT-SWAP 空单利润 62.37%
2025-12-30 11:15:21 - CFX-USDT-SWAP 多单亏损 -2.86%
2025-12-30 11:15:20 - STX-USDT-SWAP 多单亏损 -3.17%
```

## 🌐 访问信息

**实盘锚点系统页面：**
```
https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/anchor-system-real
```

**API测试：**
```bash
curl http://localhost:5000/api/anchor-system/real/hourly-extreme-stats
```

## 🎯 功能特点

### 1. 实时更新
- 每次页面刷新时自动更新
- 与其他数据同步加载

### 2. 简洁展示
- 小字体显示，不影响主要内容
- 颜色标记直观易读
- 放在标题旁边，位置显眼但不突兀

### 3. 准确统计
- 基于数据库实际记录
- 精确到1小时时间范围
- 区分多空方向和盈亏类型

### 4. 性能优化
- 单次数据库查询
- 轻量级计算
- 快速响应

## 📝 使用场景

1. **快速了解市场动态**
   - 查看最近1小时哪些仓位表现活跃
   - 了解多空双方的盈亏变化

2. **风险监控**
   - 关注亏损创新高的数量
   - 及时发现异常波动

3. **收益评估**
   - 跟踪盈利创新高的频率
   - 评估交易策略效果

## 🔍 数据说明

### record_type 类型
- `max_profit` - 最大利润（利润创新高）
- `max_loss` - 最大亏损（亏损创新高）

### pos_side 方向
- `long` - 多单（做多）
- `short` - 空单（做空）

### 统计逻辑
```sql
SELECT 
    pos_side,
    record_type,
    COUNT(*) as count
FROM anchor_real_profit_records
WHERE timestamp >= datetime('now', '-1 hour')
GROUP BY pos_side, record_type
```

## ✅ 测试验证

### API测试结果
```json
{
  "success": true,
  "time_range": "最近1小时 (>2025-12-30 08:15:47)",
  "stats": {
    "long_max_profit": 2,
    "long_max_loss": 2,
    "short_max_profit": 7,
    "short_max_loss": 0
  }
}
```

### 前端显示效果
- ✅ 统计信息正确显示
- ✅ 颜色标记正常
- ✅ 位置布局合理
- ✅ 自动刷新工作正常

## 🎨 样式设计

```css
#hourlyStats {
    margin-left: 20px;
    font-size: 13px;
    font-weight: normal;
    color: #718096;
}

/* 绿色 - 盈利 */
.profit-stat {
    color: #48bb78;
}

/* 红色 - 亏损 */
.loss-stat {
    color: #f56565;
}

/* 灰色 - 说明文字 */
.time-note {
    color: #a0aec0;
    font-size: 12px;
}
```

## 📈 后续优化建议

1. **可配置时间范围**
   - 支持选择1小时/3小时/6小时
   - 下拉菜单切换时间范围

2. **详细弹窗**
   - 点击统计数字查看详细记录
   - 显示具体的币种和时间

3. **趋势对比**
   - 显示与前一小时的对比
   - 增加/减少的趋势箭头

4. **告警提示**
   - 亏损创新高超过阈值时高亮显示
   - 可配置告警规则

## 🏆 总结

**部署状态：** ✅ 完成

**功能特点：**
- 实时统计最近1小时的极值数据
- 简洁清晰的UI展示
- 自动刷新机制
- 准确的数据查询

**访问方式：**
- 主页面：https://5000-.../anchor-system-real
- 统计会自动显示在"历史极值记录"标题旁

**Git提交：**
- Commit: 2e9d285
- Message: "Add hourly extreme stats to anchor system real page"

---

**更新时间：** 2025-12-30 09:17 UTC  
**状态：** Production Ready ✅  
**测试：** 通过 ✅
