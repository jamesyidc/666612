# 维护次数清零功能修复报告

**日期**: 2026-01-01 15:26  
**问题**: 前端"清零"按钮无法清零主账户的维护次数  
**状态**: ✅ 已修复并测试成功

---

## 📋 问题诊断

### 症状
- 用户点击前端"清零"按钮
- 弹出错误: "JSON.parse: unexpected character at line 1 column 1 of the JSON data"
- 维护次数没有被清零

### 根本原因
**文件不匹配问题**：

1. **守护进程使用的文件**: `anchor_maintenance_records.json`
   ```python
   # anchor_maintenance_realtime_daemon.py 第59行, 138行
   maintenance_file = '/home/user/webapp/anchor_maintenance_records.json'
   ```

2. **清零API使用的文件**: `main_account_maintenance.json`（错误！）
   ```python
   # app_new.py 第16517行（修复前）
   maintenance_file = 'main_account_maintenance.json'
   ```

3. **结果**: 
   - `main_account_maintenance.json` 是空文件 `{}`
   - API返回 "该持仓没有维护记录"
   - 实际数据在 `anchor_maintenance_records.json` 中

### 字段名不匹配

**守护进程使用的字段**:
```json
{
  "FIL-USDT-SWAP_short": {
    "today_count": 5,    // ← 守护进程使用这个
    "total_count": 5,
    "date": "2026-01-01"
  }
}
```

**清零API使用的字段**（修复前）:
```python
old_count = record.get('count', 0)  # ❌ 错误：应该是 'today_count'
record['count'] = 0                  # ❌ 错误：应该是 'today_count'
```

---

## 🔧 修复方案

### 修改1: 文件路径

**文件**: `app_new.py`  
**行数**: 16516-16522

**修复前**:
```python
# 读取维护记录文件
maintenance_file = 'main_account_maintenance.json'
try:
    with open(maintenance_file, 'r', encoding='utf-8') as f:
        maintenance_data = json.load(f)
```

**修复后**:
```python
# 读取维护记录文件（使用守护进程同样的文件）
maintenance_file = 'anchor_maintenance_records.json'
try:
    with open(maintenance_file, 'r', encoding='utf-8') as f:
        maintenance_data = json_lib.load(f)
```

### 修改2: 字段名

**文件**: `app_new.py`  
**行数**: 16537-16549

**修复前**:
```python
record = maintenance_data[record_key]

# 清零今日维护次数
old_count = record.get('count', 0)

# 重置记录
record['count'] = 0
record['date'] = today_date
record['last_reset'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 保存更新后的数据
with open(maintenance_file, 'w', encoding='utf-8') as f:
    json.dump(maintenance_data, f, ensure_ascii=False, indent=2)
```

**修复后**:
```python
record = maintenance_data[record_key]

# 清零今日维护次数（使用守护进程的字段名）
old_count = record.get('today_count', 0)

# 重置记录
record['today_count'] = 0
record['date'] = today_date
record['last_reset'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 保存更新后的数据
with open(maintenance_file, 'w', encoding='utf-8') as f:
    json_lib.dump(maintenance_data, f, ensure_ascii=False, indent=2)
```

---

## 🧪 测试验证

### 测试用例: FIL-USDT-SWAP short

#### 修复前状态
```json
{
  "FIL-USDT-SWAP_short": {
    "inst_id": "FIL-USDT-SWAP",
    "pos_side": "short",
    "today_count": 5,
    "total_count": 5,
    "last_maintenance": "2026-01-01 23:10:03",
    "date": "2026-01-01"
  }
}
```

#### 测试命令
```bash
curl -X POST http://localhost:5000/api/main-account/reset-maintenance-count \
  -H "Content-Type: application/json" \
  -d '{"inst_id":"FIL-USDT-SWAP","pos_side":"short"}'
```

#### API 响应（修复后）
```json
{
  "inst_id": "FIL-USDT-SWAP",
  "message": "清零成功！原超级维护次数: 5次",
  "new_count": 0,
  "old_count": 5,
  "pos_side": "short",
  "reset_time": "2026-01-01 15:26:07",
  "success": true
}
```

#### 修复后状态
```json
{
  "FIL-USDT-SWAP_short": {
    "inst_id": "FIL-USDT-SWAP",
    "pos_side": "short",
    "today_count": 0,           // ✅ 从5清零到0
    "total_count": 5,            // ✅ 保持历史记录
    "last_maintenance": "2026-01-01 23:10:03",
    "date": "2026-01-01",
    "last_reset": "2026-01-01 15:26:07"  // ✅ 添加重置时间戳
  }
}
```

### 测试结果

| 项目 | 修复前 | 修复后 | 状态 |
|------|--------|--------|------|
| API响应 | "该持仓没有维护记录" | "清零成功！原超级维护次数: 5次" | ✅ |
| today_count | 5 | 0 | ✅ |
| total_count | 5 | 5 (保留) | ✅ |
| last_reset | 无 | "2026-01-01 15:26:07" | ✅ |
| 文件 | main_account_maintenance.json | anchor_maintenance_records.json | ✅ |

---

## 📊 维护记录文件对比

### anchor_maintenance_records.json（正确）
**使用者**: 
- ✅ 锚点维护守护进程 (`anchor_maintenance_realtime_daemon.py`)
- ✅ 清零API (`app_new.py` 第16499行，修复后)

**数据结构**:
```json
{
  "{inst_id}_{pos_side}": {
    "inst_id": "FIL-USDT-SWAP",
    "pos_side": "short",
    "today_count": 0,        // ← 今日维护次数
    "total_count": 5,        // ← 总维护次数
    "last_maintenance": "2026-01-01 23:10:03",
    "date": "2026-01-01",
    "last_reset": "2026-01-01 15:26:07"  // ← 最后清零时间
  }
}
```

### main_account_maintenance.json（已废弃）
**内容**: `{}`（空文件）

**状态**: ⚠️ 已不再使用

---

## 🎯 修复总结

### 问题本质
1. **文件路径错误**: 清零API读取了错误的文件
2. **字段名错误**: 清零API使用了错误的字段名
3. **数据不同步**: 守护进程和API使用了不同的数据文件

### 修复要点
1. ✅ 统一使用 `anchor_maintenance_records.json`
2. ✅ 统一使用字段名 `today_count`
3. ✅ 统一使用 `json_lib.load()` 和 `json_lib.dump()`
4. ✅ 添加 `last_reset` 时间戳记录

### 影响范围
- ✅ 主账户维护次数清零功能
- ✅ FIL-USDT-SWAP 测试通过
- ✅ 其他币种（如CRO）理论上也能清零

### 测试覆盖
- [x] FIL-USDT-SWAP short（已测试 ✅）
- [ ] CRO-USDT-SWAP long（待有维护记录后测试）
- [ ] 其他币种（待有维护记录后测试）

---

## 📝 相关文件

### 修改的文件
- `app_new.py` 第16516-16549行

### 涉及的数据文件
- `anchor_maintenance_records.json` - 实际使用的维护记录（✅ 正确）
- `main_account_maintenance.json` - 已废弃的文件（❌ 已不再使用）

### 相关守护进程
- `anchor_maintenance_realtime_daemon.py` - 自动维护守护进程

---

## 🚀 部署状态

### Git 提交
- **提交哈希**: 894009e
- **提交信息**: "修复主账户维护次数清零：使用正确的文件和字段名"
- **修改文件**: 3个文件，65行新增，7行删除
- **提交状态**: ✅ 本地已提交

### 服务状态
- **Flask**: ✅ 已重启（PID 79683）
- **守护进程**: ✅ 正常运行（PID 22542，运行10小时）
- **其他服务**: ✅ 全部在线

### 推送状态
- **GitHub推送**: ⚠️ 需要重新配置认证
- **本地代码**: ✅ 已提交并应用

---

## 🎓 经验教训

### 问题根源
**数据源不一致**：不同组件使用了不同的数据文件和字段名，导致功能失效。

### 解决原则
1. **统一数据源**: 所有组件应使用同一个数据文件
2. **统一字段名**: 数据结构和字段名应保持一致
3. **代码审查**: 修改数据结构时，检查所有使用该数据的地方
4. **测试验证**: 修复后立即测试验证

### 预防措施
1. **文档化**: 明确记录每个数据文件的用途和使用者
2. **配置统一**: 将文件路径和字段名定义为常量
3. **版本管理**: 数据结构变更时，更新所有相关代码

---

## 📚 相关文档

- [FIXES_SUMMARY.md](FIXES_SUMMARY.md) - 今日所有修复汇总
- [MARGIN_FIX_COMPLETE_REPORT.md](MARGIN_FIX_COMPLETE_REPORT.md) - 保证金显示修复
- [CLOSE_ALL_POSITIONS_FIX_FINAL.md](CLOSE_ALL_POSITIONS_FIX_FINAL.md) - 一键平仓修复

---

**修复完成时间**: 2026-01-01 15:26  
**测试状态**: ✅ 已验证  
**部署状态**: ✅ 已上线  
**问题状态**: 🟢 已解决
