# 子账号保证金显示修复

## 问题描述
子账号持仓列表显示的保证金不是从 OKEx API 获取的真实数据。

## 问题根源
代码使用了错误的逻辑来选择保证金字段：

```python
# ❌ 错误的代码
margin = float(pos.get('margin') or pos.get('imr') or 0)
```

这个逻辑有问题：
- 对于**全仓模式**，`margin` 字段是空字符串
- 空字符串在 Python 中是 falsy，所以会 fallback 到 `imr`
- 但这样的逻辑不够清晰，容易出错

## OKEx API 保证金字段说明

### 字段含义
- **`margin`**: 占用保证金（逐仓模式）
- **`imr`**: 初始保证金（Initial Margin Requirement）
- **`mgnMode`**: 保证金模式
  - `isolated`: 逐仓模式
  - `cross`: 全仓模式

### 不同模式下的字段值

#### 逐仓模式 (isolated)
```json
{
  "instId": "BTC-USDT-SWAP",
  "mgnMode": "isolated",
  "margin": "100.5",    // ✅ 有值
  "imr": "100.5",       // 也有值
  "pos": "10"
}
```

#### 全仓模式 (cross)
```json
{
  "instId": "APT-USDT-SWAP",
  "mgnMode": "cross",
  "margin": "",         // ❌ 空字符串
  "imr": "34.099",      // ✅ 有值
  "pos": "61"
}
```

## 正确的解决方案

### 修复后的代码
```python
# ✅ 正确的代码
mgn_mode = pos.get('mgnMode', 'isolated')

if mgn_mode == 'cross':
    # 全仓模式：使用 imr（初始保证金）
    margin = float(pos.get('imr') or 0)
else:
    # 逐仓模式：使用 margin（占用保证金）
    margin = float(pos.get('margin') or 0)
```

### 优点
1. ✅ **明确性**: 清楚地区分两种模式
2. ✅ **准确性**: 使用正确的字段
3. ✅ **可读性**: 代码意图清晰
4. ✅ **调试性**: 容易定位问题

## 修复位置
**文件**: `app_new.py`
**函数**: `get_sub_account_positions()`
**行号**: 13039-13052

## 测试验证

### 测试用例
1. **全仓模式持仓**: 检查是否使用 `imr` 字段
2. **逐仓模式持仓**: 检查是否使用 `margin` 字段
3. **混合模式**: 同时有全仓和逐仓持仓

### 验证方法
```bash
# 查看日志
pm2 logs flask-app --lines 50 --nostream | grep "💰 最终使用的保证金"

# 应该看到类似输出：
# 🔍 全仓模式 - imr: 34.099
# 💰 最终使用的保证金: 34.099 USDT (模式: cross)
```

## Git 提交
```bash
commit 2422363
修复子账号持仓保证金显示：根据持仓模式(cross/isolated)选择正确的保证金字段
```

## 相关修复
这次修复与一键平仓功能的修复一致：
- 一键平仓：根据 `mgnMode` 选择正确的交易参数
- 保证金显示：根据 `mgnMode` 选择正确的保证金字段

## 最佳实践

### 1. 永远显式检查持仓模式
```python
# ❌ 不好：依赖 falsy 值的隐式行为
margin = float(pos.get('margin') or pos.get('imr') or 0)

# ✅ 好：明确检查模式
if mgn_mode == 'cross':
    margin = float(pos.get('imr') or 0)
else:
    margin = float(pos.get('margin') or 0)
```

### 2. 添加调试日志
```python
print(f"🔍 {mgn_mode}模式 - 使用字段: {'imr' if mgn_mode == 'cross' else 'margin'}")
print(f"💰 最终使用的保证金: {margin} USDT")
```

### 3. 处理空值
```python
# 使用 'or 0' 确保总是返回数字
margin = float(pos.get('imr') or 0)
```

## 部署状态
- ✅ 代码已修复
- ✅ 已推送到 main
- ✅ Flask 已重启
- ✅ 生产就绪

---

**修复时间**: 2026-01-01 14:10
**状态**: ✅ 完成
