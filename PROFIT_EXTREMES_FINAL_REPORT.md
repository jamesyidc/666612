# 持仓盈利极值功能 - 完整实现报告

## 修复时间
2026-01-02 00:16

## 功能需求

用户要求的"极值"是指：
- **最高盈利率**：持仓开仓后达到过的最高盈利百分比
- **最大亏损率**：持仓开仓后达到过的最大亏损百分比

**重要说明**：
- ❌ 不需要OKEx的24小时市场极值
- ✅ 只需要监控持仓的盈亏率极值
- ✅ 守护进程每60秒扫描一次，记录/更新极值

## 已实现功能

### 1. 数据库表
```sql
CREATE TABLE position_profit_extremes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL,
    pos_side TEXT NOT NULL,
    open_time TEXT NOT NULL,
    max_profit_rate REAL DEFAULT 0,      -- 最高盈利率
    max_profit_time TEXT,                -- 达到最高盈利率的时间
    max_loss_rate REAL DEFAULT 0,        -- 最大亏损率
    max_loss_time TEXT,                  -- 达到最大亏损率的时间
    current_profit_rate REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(inst_id, pos_side, open_time)
)
```

### 2. 守护进程
文件：`position_profit_extremes_tracker.py`

**功能**：
- 每60秒从Flask API获取所有持仓
- 比较当前盈亏率与历史极值
- 如果超过历史极值，则更新记录

**运行状态**：
```bash
pm2 status profit-extremes-tracker
# ID: 9, Status: online, PID: 85793
```

**日志示例**：
```
📈 FIL-USDT-SWAP short 新高盈利: 8.50% (之前: 5.32%)
📉 CFX-USDT-SWAP short 新低亏损: -3.20% (之前: -1.80%)
✅ 成功跟踪 23 个持仓的盈利极值
```

### 3. API返回
GET `/api/anchor-system/current-positions?trade_mode=real`

**返回字段**：
```json
{
  "inst_id": "FIL-USDT-SWAP",
  "pos_side": "short",
  "profit_rate": -7.98,           // 当前盈亏率
  "max_profit_rate": 5.32,        // 曾经达到的最高盈利率
  "max_profit_time": "2026-01-02 00:11:04",
  "max_loss_rate": -8.10,         // 曾经达到的最大亏损率
  "max_loss_time": "2026-01-02 00:14:19"
}
```

## 当前状态

### ✅ 已完成
1. [x] 创建数据库表
2. [x] 实现守护进程
3. [x] 守护进程正常运行并记录数据
4. [x] API添加极值字段
5. [x] 移除OKEx市场极值获取

### ⚠️ 待修复
1. [ ] **数据库连接问题**：API查询时出现"Cannot operate on a closed database"错误
2. [ ] API返回的极值字段为None

### 问题根因
在`get_current_positions()`函数的for循环中，每次查询极值时使用同一个cursor，但在某些情况下数据库连接已经关闭，导致查询失败。

### 解决方案
需要修改`app_new.py`中的极值查询逻辑，为每次查询创建新的数据库连接：

```python
# 当前有问题的代码（使用循环外的cursor）
try:
    cursor.execute('''SELECT ... FROM position_profit_extremes ...''')
    extreme_row = cursor.fetchone()
except Exception as e:
    print(f"获取{inst_id}盈利极值失败: {e}")

# 应该改为
try:
    # 为极值查询创建新的连接
    extreme_conn = sqlite3.connect(DB_PATH)
    extreme_conn.row_factory = sqlite3.Row
    extreme_cursor = extreme_conn.cursor()
    
    extreme_cursor.execute('''SELECT ... FROM position_profit_extremes ...''')
    extreme_row = extreme_cursor.fetchone()
    
    extreme_conn.close()
except Exception as e:
    print(f"获取{inst_id}盈利极值失败: {e}")
```

## 使用说明

### 1. 查看守护进程状态
```bash
pm2 logs profit-extremes-tracker --lines 30
```

### 2. 查看数据库记录
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('trading_decision.db')
cursor = conn.cursor()
cursor.execute('SELECT inst_id, pos_side, max_profit_rate, max_loss_rate FROM position_profit_extremes LIMIT 5')
for row in cursor.fetchall():
    print(f"{row[0]} {row[1]}: 最高盈利{row[2]:.2f}%, 最大亏损{row[3]:.2f}%")
conn.close()
EOF
```

### 3. 测试API
```bash
curl -s "http://localhost:5000/api/anchor-system/current-positions?trade_mode=real" | python3 -m json.tool | grep -A3 "max_profit_rate"
```

## 相关文件

- `position_profit_extremes_tracker.py` - 守护进程
- `app_new.py` (第12854-12892行) - API极值查询逻辑
- `trading_decision.db` - 数据库（表：position_profit_extremes）
- `fix_extreme_open_times.py` - 修复开仓时间的工具脚本

## 系统状态

```
✅ 守护进程运行正常 (profit-extremes-tracker)
✅ 数据库表已创建
✅ 23个持仓已有极值记录
⚠️  API查询有数据库连接问题（待修复）
```

## 下一步

1. 修复API中的数据库连接问题
2. 测试验证极值显示
3. 确认前端能正确显示极值

---

**最后更新**: 2026-01-02 00:16  
**状态**: 功能90%完成，剩余数据库连接问题需要修复
