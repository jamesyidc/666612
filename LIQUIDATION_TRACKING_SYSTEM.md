# 子账号爆仓记录与统计系统

## 📋 功能概述

为子账号交易系统添加完整的爆仓记录和统计功能，包括：
- 📝 爆仓事件记录
- 📊 多维度统计分析
- 📈 可视化展示界面
- 🔍 历史数据查询

## 🎯 功能特点

### 1. 爆仓记录功能
- **自动记录**: 每次爆仓事件自动记录到数据库
- **详细信息**: 记录时间、账号、币种、方向、价格、数量、损失等
- **类型标记**: 区分自动强平、手动平仓等类型
- **备注说明**: 支持添加额外备注信息

### 2. 统计分析功能
- **总体统计**: 总爆仓次数、总损失金额、多空比例
- **账号统计**: 每个账号的爆仓次数和损失
- **币种统计**: 每个币种的爆仓频率和损失
- **时间统计**: 今日/本周/本月爆仓统计

### 3. 可视化展示
- **统计卡片**: 关键指标一目了然
- **数据表格**: 详细的统计数据展示
- **历史记录**: 最近爆仓记录列表
- **自动刷新**: 30秒自动更新数据

## 📁 文件说明

### 1. 核心模块
**文件**: `sub_account_liquidation_tracker.py`

**主要功能**:
```python
# 初始化数据库
init_database()

# 记录爆仓事件
record_liquidation(
    account_name="Wu666666",
    inst_id="BTC-USDT-SWAP",
    pos_side="long",
    liquidation_price=40000.0,
    avg_price=42000.0,
    size=10.0,
    margin=100.0,
    loss_amount=50.0,
    liquidation_type="自动强平",
    remarks=""
)

# 获取爆仓记录
records = get_liquidation_records(account_name=None, inst_id=None, limit=100)

# 获取账号统计
account_stats = get_account_stats(account_name=None)

# 获取币种统计
coin_stats = get_coin_stats(inst_id=None)

# 获取总体统计
summary = get_summary_stats()
```

### 2. 前端页面
**文件**: `templates/liquidation_stats.html`

**功能特点**:
- 响应式设计，适配各种屏幕
- 实时数据展示
- 自动刷新功能
- 美观的UI设计

### 3. 测试工具
**文件**: `test_liquidation_data.py`

用于生成测试数据，方便功能测试和演示。

## 🗄️ 数据库结构

### 1. 爆仓记录表 (sub_account_liquidations)
```sql
CREATE TABLE sub_account_liquidations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_time TEXT NOT NULL,              -- 记录时间
    account_name TEXT NOT NULL,             -- 账号名称
    account_display_name TEXT,              -- 账号显示名
    inst_id TEXT NOT NULL,                  -- 交易对
    pos_side TEXT NOT NULL,                 -- 方向（long/short）
    liquidation_price REAL,                 -- 爆仓价格
    avg_price REAL,                         -- 平均价格
    size REAL,                              -- 数量
    margin REAL,                            -- 保证金
    loss_amount REAL,                       -- 损失金额
    liquidation_type TEXT,                  -- 爆仓类型
    remarks TEXT,                           -- 备注
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### 2. 账号统计表 (sub_account_liquidation_stats)
```sql
CREATE TABLE sub_account_liquidation_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name TEXT NOT NULL UNIQUE,
    account_display_name TEXT,
    total_liquidations INTEGER DEFAULT 0,   -- 总爆仓次数
    total_loss_amount REAL DEFAULT 0,       -- 总损失金额
    long_liquidations INTEGER DEFAULT 0,    -- 多单爆仓次数
    short_liquidations INTEGER DEFAULT 0,   -- 空单爆仓次数
    last_liquidation_time TEXT,             -- 最后爆仓时间
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### 3. 币种统计表 (coin_liquidation_stats)
```sql
CREATE TABLE coin_liquidation_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inst_id TEXT NOT NULL UNIQUE,
    total_liquidations INTEGER DEFAULT 0,
    total_loss_amount REAL DEFAULT 0,
    long_liquidations INTEGER DEFAULT 0,
    short_liquidations INTEGER DEFAULT 0,
    last_liquidation_time TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

## 🔌 API接口

### 1. 记录爆仓事件
**接口**: `POST /api/liquidation/record`

**请求体**:
```json
{
    "account_name": "Wu666666",
    "inst_id": "BTC-USDT-SWAP",
    "pos_side": "long",
    "liquidation_price": 40000.0,
    "avg_price": 42000.0,
    "size": 10.0,
    "margin": 100.0,
    "loss_amount": 50.0,
    "liquidation_type": "自动强平",
    "remarks": "测试记录"
}
```

**响应**:
```json
{
    "success": true,
    "message": "爆仓记录已保存"
}
```

### 2. 获取爆仓记录
**接口**: `GET /api/liquidation/records`

**参数**:
- `account_name` (可选): 账号名称
- `inst_id` (可选): 交易对
- `limit` (可选): 返回数量，默认100

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "record_time": "2026-01-04 15:13:05",
            "account_name": "Wu666666",
            "account_display_name": "吴六",
            "inst_id": "BTC-USDT-SWAP",
            "pos_side": "long",
            "liquidation_price": 40000.0,
            "avg_price": 42000.0,
            "size": 10.0,
            "margin": 100.0,
            "loss_amount": 50.0,
            "liquidation_type": "自动强平",
            "remarks": "测试记录"
        }
    ]
}
```

### 3. 获取账号统计
**接口**: `GET /api/liquidation/account-stats`

**参数**:
- `account_name` (可选): 账号名称

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "account_name": "Wu666666",
            "account_display_name": "吴六",
            "total_liquidations": 10,
            "total_loss_amount": 312.62,
            "long_liquidations": 4,
            "short_liquidations": 6,
            "last_liquidation_time": "2026-01-04 15:13:05",
            "updated_at": "2026-01-04 15:13:05"
        }
    ]
}
```

### 4. 获取币种统计
**接口**: `GET /api/liquidation/coin-stats`

**参数**:
- `inst_id` (可选): 交易对

**响应**:
```json
{
    "success": true,
    "data": [
        {
            "inst_id": "BTC-USDT-SWAP",
            "total_liquidations": 5,
            "total_loss_amount": 250.0,
            "long_liquidations": 2,
            "short_liquidations": 3,
            "last_liquidation_time": "2026-01-04 15:13:05",
            "updated_at": "2026-01-04 15:13:05"
        }
    ]
}
```

### 5. 获取总体统计
**接口**: `GET /api/liquidation/summary`

**响应**:
```json
{
    "success": true,
    "data": {
        "total_liquidations": 10,
        "total_loss": 312.62,
        "long_liquidations": 4,
        "long_loss": 120.21,
        "short_liquidations": 6,
        "short_loss": 192.41,
        "today_liquidations": 10,
        "today_loss": 312.62
    }
}
```

## 🌐 访问地址

### 爆仓统计页面
**URL**: https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/liquidation-stats

### API端点
- **记录爆仓**: `POST /api/liquidation/record`
- **查询记录**: `GET /api/liquidation/records`
- **账号统计**: `GET /api/liquidation/account-stats`
- **币种统计**: `GET /api/liquidation/coin-stats`
- **总体统计**: `GET /api/liquidation/summary`

## 📊 测试数据

系统已添加10条测试数据，用于演示功能：

```
总爆仓次数: 10
总损失金额: $312.62
今日爆仓: 10 次
今日损失: $312.62

多单爆仓: 4 次 ($120.21)
空单爆仓: 6 次 ($192.41)

账号统计:
  吴六 (Wu666666):
    爆仓次数: 10
    损失金额: $312.62
    多单: 4 | 空单: 6

币种统计 (Top 7):
  1. ETH-USDT-SWAP: 2次 ($75.80)
  2. DOGE-USDT-SWAP: 2次 ($58.70)
  3. BNB-USDT-SWAP: 2次 ($63.52)
  4. DOT-USDT-SWAP: 1次 ($40.06)
  5. SOL-USDT-SWAP: 1次 ($14.62)
  6. MATIC-USDT-SWAP: 1次 ($13.93)
  7. AVAX-USDT-SWAP: 1次 ($45.98)
```

## 🚀 使用方法

### 1. 查看统计页面
直接访问: https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/liquidation-stats

### 2. 记录新的爆仓事件
```python
from sub_account_liquidation_tracker import record_liquidation

record_liquidation(
    account_name="Wu666666",
    inst_id="BTC-USDT-SWAP",
    pos_side="long",
    liquidation_price=40000.0,
    avg_price=42000.0,
    size=10.0,
    margin=100.0,
    loss_amount=50.0,
    liquidation_type="自动强平",
    remarks="市场剧烈波动"
)
```

### 3. 查询统计数据
```python
from sub_account_liquidation_tracker import get_summary_stats, print_summary

# 获取统计数据
summary = get_summary_stats()
print(summary)

# 打印格式化摘要
print_summary()
```

### 4. 添加测试数据
```bash
cd /home/user/webapp
python3 test_liquidation_data.py
```

## 🔧 命令行工具

### 查看统计摘要
```bash
cd /home/user/webapp
python3 sub_account_liquidation_tracker.py
```

### 查询API
```bash
# 总体统计
curl http://localhost:5000/api/liquidation/summary

# 获取记录
curl http://localhost:5000/api/liquidation/records?limit=10

# 账号统计
curl http://localhost:5000/api/liquidation/account-stats

# 币种统计
curl http://localhost:5000/api/liquidation/coin-stats
```

## 📈 统计维度

### 1. 时间维度
- 总计统计
- 今日统计
- 最近N天统计

### 2. 账号维度
- 各账号爆仓次数
- 各账号损失金额
- 多空比例

### 3. 币种维度
- 各币种爆仓频率
- 各币种损失金额
- 风险币种排名

### 4. 方向维度
- 多单爆仓统计
- 空单爆仓统计
- 多空比例分析

## 🔍 应用场景

### 1. 风险监控
- 实时监控爆仓情况
- 识别高风险币种
- 识别高风险账号

### 2. 交易优化
- 分析爆仓原因
- 优化止损策略
- 调整仓位管理

### 3. 绩效分析
- 统计总体损失
- 分析爆仓模式
- 评估交易策略

### 4. 历史回溯
- 查看历史爆仓记录
- 分析爆仓趋势
- 总结经验教训

## 📋 扩展功能

### 已实现
- ✅ 爆仓记录存储
- ✅ 多维度统计
- ✅ 可视化展示
- ✅ API接口
- ✅ 测试工具

### 待扩展
- 📊 图表展示（折线图、饼图）
- 📧 邮件通知
- 📱 Telegram推送
- 📈 趋势预测
- 🔔 风险预警

## 🛠️ 维护建议

### 数据备份
```bash
# 备份数据库
cp databases/crypto_data.db databases/crypto_data_backup_$(date +%Y%m%d).db

# 导出统计数据
python3 -c "
from sub_account_liquidation_tracker import get_summary_stats
import json
summary = get_summary_stats()
print(json.dumps(summary, indent=2))
" > liquidation_stats_$(date +%Y%m%d).json
```

### 定期清理
```bash
# 清理3个月前的记录
sqlite3 databases/crypto_data.db "DELETE FROM sub_account_liquidations WHERE record_time < date('now', '-3 months')"

# 重建统计表
python3 -c "
from sub_account_liquidation_tracker import init_database
init_database()
"
```

## 🔗 相关链接

- **统计页面**: https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/liquidation-stats
- **实盘锚点系统**: https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/anchor-system-real
- **GitHub仓库**: https://github.com/jamesyidc/666612.git

## ✅ 功能验证

- ✅ 数据库表已创建
- ✅ 记录功能正常
- ✅ 统计功能正常
- ✅ API接口正常
- ✅ 前端页面正常
- ✅ 测试数据已添加
- ✅ 文档已完成

## 🎉 总结

子账号爆仓记录与统计系统已完成开发并上线！

**核心功能**:
- 📝 完整的爆仓记录功能
- 📊 多维度统计分析
- 📈 可视化展示界面
- 🔌 RESTful API接口
- 🧪 完善的测试工具

**系统特点**:
- 自动化记录
- 实时统计
- 多维度分析
- 易于扩展

**访问方式**:
- 统计页面: https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/liquidation-stats
- API接口: `/api/liquidation/*`
- 命令行工具: `python3 sub_account_liquidation_tracker.py`

系统现在可以完整记录和统计子账号的爆仓情况，为风险管理和交易优化提供数据支持！
