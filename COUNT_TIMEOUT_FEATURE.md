# 计次数据超时判断功能

## 功能说明
在实盘锚点系统首页的"当前计次"卡片中，增加数据超时检测：
- 如果最后更新时间距离现在**超过20分钟**，显示"**超时**"提示
- 否则显示正常的计次数值

## 修改时间
**2026-01-04 11:58:00**

---

## 功能效果

### 正常状态（数据更新在20分钟内）
```
🔢 当前计次
    1
最新15分钟数据
```
- 显示实际计次数值
- 字体颜色：橙色（#b45309）
- 字体大小：48px

### 超时状态（数据超过20分钟未更新）
```
🔢 当前计次
  超时
最新15分钟数据
```
- 显示"超时"文字
- 字体颜色：红色（#dc2626）
- 字体大小：36px
- 控制台警告：`⚠️ 计次数据已超时 XX 分钟`

---

## 技术实现

### 修改文件
`templates/anchor_system_real.html`

### 修改位置
JavaScript 代码中的 `loadData()` 函数（约第1078-1083行）

### 代码实现

#### 修改前 ❌
```javascript
// 处理计次数据
if (countData && countData.count !== undefined) {
    document.getElementById('currentCount').textContent = countData.count;
} else {
    document.getElementById('currentCount').textContent = '0';
}
```

#### 修改后 ✅
```javascript
// 处理计次数据 - 增加超时判断
if (countData && countData.count !== undefined) {
    // 检查数据时间是否超过20分钟
    const currentTime = new Date();
    const snapshotTime = new Date(countData.snapshot_time);
    const timeDiffMinutes = (currentTime - snapshotTime) / (1000 * 60);
    
    const countElement = document.getElementById('currentCount');
    if (timeDiffMinutes > 20) {
        // 超过20分钟，显示超时提示
        countElement.textContent = '超时';
        countElement.style.color = '#dc2626'; // 红色
        countElement.style.fontSize = '36px';
        console.warn(`⚠️ 计次数据已超时 ${Math.floor(timeDiffMinutes)} 分钟`);
    } else {
        // 正常显示计次
        countElement.textContent = countData.count;
        countElement.style.color = '#b45309'; // 原来的橙色
        countElement.style.fontSize = '48px';
    }
} else {
    const countElement = document.getElementById('currentCount');
    countElement.textContent = '0';
    countElement.style.color = '#b45309';
    countElement.style.fontSize = '48px';
}
```

---

## 数据来源

### API接口
`/api/latest`

### 返回数据结构
```json
{
  "snapshot_time": "2026-01-04 11:37:00",
  "count": 1,
  "rush_up": 9,
  "rush_down": 4,
  "ratio": 2.25,
  "status": "震荡无序"
}
```

### 关键字段
- `snapshot_time` - 快照时间，用于计算时间差
- `count` - 计次数值

---

## 超时判断逻辑

### 时间计算
```javascript
const currentTime = new Date();              // 当前时间
const snapshotTime = new Date(countData.snapshot_time);  // 数据时间
const timeDiffMinutes = (currentTime - snapshotTime) / (1000 * 60);  // 时间差（分钟）
```

### 判断条件
```javascript
if (timeDiffMinutes > 20) {
    // 超时：显示"超时"
} else {
    // 正常：显示计次数值
}
```

### 超时阈值
- **20分钟** - 超过此时间显示超时提示

---

## 使用场景

### 1. 数据采集正常
- 计次数据每分钟更新
- 显示最新的计次数值
- 用户可正常查看系统状态

### 2. 数据采集异常
- 采集服务停止或出错
- 超过20分钟未更新
- 显示"超时"提醒用户数据异常
- 提示运维人员检查服务

### 3. 系统维护
- 维护期间数据可能停止更新
- 自动显示超时状态
- 避免用户误读过期数据

---

## 视觉效果

### 颜色变化
| 状态 | 颜色 | 字体大小 | 说明 |
|------|------|----------|------|
| 正常 | 🟧 橙色 (#b45309) | 48px | 数据新鲜 |
| 超时 | 🔴 红色 (#dc2626) | 36px | 数据过期 |

### UI位置
```
📊 实盘锚点系统
├─ 主账户持仓: 27
├─ 主账户盈亏: +12.26
├─ 子账户持仓: 9
├─ 子账户盈亏: -53.71
├─ 总盈利大价: 87328
├─ 总累计盈利: 6263
├─ 盈利多倍警戒: +40%
├─ 做空警戒下限: -10%
└─ 🔢 当前计次: 1 ← 这里会显示超时
```

---

## Git 提交记录

### Commit
```
403d5d2 - feat: 添加计次数据超时判断 - 超过20分钟显示超时提示
```

### 修改统计
```
2 files changed, 28 insertions(+), 8 deletions(-)
```

### GitHub
https://github.com/jamesyidc/666612.git

---

## 测试方法

### 1. 正常数据测试
```bash
# 确保数据采集服务正常运行
pm2 status | grep "escape-stats-recorder"

# 访问页面
# https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/anchor-system-real

# 预期：显示正常的计次数值（如：1）
```

### 2. 超时数据测试
```bash
# 方法1：停止数据采集服务
pm2 stop escape-stats-recorder

# 等待20分钟后访问页面
# 预期：显示"超时"

# 方法2：修改数据库中的时间戳
sqlite3 databases/crypto_data.db "UPDATE crypto_snapshots SET snapshot_time = datetime('now', '-30 minutes') WHERE id = (SELECT MAX(id) FROM crypto_snapshots)"

# 刷新页面
# 预期：显示"超时"
```

### 3. 控制台日志测试
```javascript
// 打开浏览器开发者工具 (F12)
// 查看Console标签

// 正常状态：无警告
// 超时状态：显示
⚠️ 计次数据已超时 25 分钟
```

---

## 访问地址

### 实盘锚点系统页面
https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/anchor-system-real

### 导航栏入口
```
首页 → 📊 系统页面 → 🔴 实盘锚点系统 (Real Trading)
```

---

## 相关服务

### 数据采集服务
- `escape-stats-recorder` - 计次数据记录器
- 每分钟自动采集一次
- 数据存储在 `crypto_snapshots` 表

### 监控建议
1. 设置服务监控告警
2. 定期检查数据采集状态
3. 关注"超时"提示
4. 确保数据库写入正常

---

## 系统状态

### 当前状态
- 🟢 **Flask应用**: 正常运行
- 🟢 **数据采集**: 正常运行
- 🟢 **超时判断**: 已启用
- 🟢 **页面显示**: 正常

### PM2进程
```bash
pm2 status
```

| 进程 | 状态 | 说明 |
|------|------|------|
| flask-app | online | Web服务 |
| escape-stats-recorder | online | 计次数据采集 |

---

## 注意事项

### 1. 时间同步
- 确保服务器时间准确
- 使用 `date` 命令检查系统时间
- 避免时区问题导致误判

### 2. 数据格式
- `snapshot_time` 必须是有效的日期时间字符串
- 格式：`YYYY-MM-DD HH:MM:SS`
- 示例：`2026-01-04 11:37:00`

### 3. 浏览器缓存
- 修改后需要刷新页面（Ctrl+F5）
- 或清除浏览器缓存

### 4. 控制台日志
- 超时时会输出警告信息
- 便于调试和监控

---

## 未来优化方向

### 1. 可配置的超时阈值
```javascript
// 可以从配置API读取超时时间
const timeoutMinutes = config.count_timeout_minutes || 20;
```

### 2. 显示倒计时
```
当前计次: 1
(18分钟前更新)
```

### 3. 超时提醒
```javascript
if (timeDiffMinutes > 20) {
    // 发送桌面通知
    new Notification('数据超时', {
        body: '计次数据已超过20分钟未更新'
    });
}
```

### 4. 颜色渐变
```javascript
// 10-15分钟：黄色
// 15-20分钟：橙色
// 20+分钟：红色
```

---

## 修复完成时间
**2026-01-04 11:58:00**

## 修复人员
Claude AI Assistant

## 文档版本
v1.0

---

**✅ 计次超时判断功能已上线！**
