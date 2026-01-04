# 网络连接错误修复指南

## 错误信息
```
错误: Failed to fetch
net::ERR_CONNECTION_REFUSED
```

## 问题分析

### ✅ 后端系统状态（正常）
- **Flask应用**: ✅ 运行中（PID 470654）
- **端口5000**: ✅ 正常监听
- **PM2进程**: ✅ 12个进程全部在线
- **API响应**: ✅ 所有端点正常

### ❌ 可能的原因
1. **前端访问地址错误** - 使用了沙盒内部地址而不是公共URL
2. **CORS配置问题** - 跨域请求被阻止
3. **网络超时** - 请求超时或连接被重置
4. **浏览器缓存** - 旧的配置被缓存

## 解决方案

### 方案1: 使用正确的公共访问地址 ✅

**沙盒公共URL（外部访问）**:
```
https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai
```

**错误的地址（仅沙盒内部可用）**:
- `http://localhost:5000` ❌
- `http://127.0.0.1:5000` ❌

**正确使用方式**:
```javascript
// 前端配置 - 使用公共URL
const API_BASE_URL = 'https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai';

// 示例请求
fetch(`${API_BASE_URL}/api/support-resistance/latest`)
  .then(response => response.json())
  .then(data => console.log(data));
```

### 方案2: 检查CORS配置

确保Flask应用允许跨域请求：

```python
# app_new.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有域名访问
```

### 方案3: 清除浏览器缓存

1. 打开浏览器开发者工具（F12）
2. 右键点击刷新按钮
3. 选择"清空缓存并硬性重新加载"

或使用快捷键：
- Chrome/Edge: `Ctrl + Shift + Delete`
- Firefox: `Ctrl + Shift + Del`

### 方案4: 使用代理（如果需要）

如果直接访问有问题，可以配置nginx反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 快速测试

### 1. 测试API连接（命令行）
```bash
curl https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/api/support-resistance/latest
```

**预期结果**: 返回JSON数据，包含27个币种信息

### 2. 测试API连接（浏览器）
直接访问：
```
https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/api/support-resistance/latest
```

**预期结果**: 浏览器显示JSON数据

### 3. 检查前端配置

**查找配置文件**:
```bash
# 在前端代码中搜索API基础URL
grep -r "localhost:5000" templates/
grep -r "127.0.0.1" templates/
grep -r "sandbox.novita.ai" templates/
```

## 常见API端点

所有API端点都可以通过公共URL访问：

| 端点 | 完整URL |
|------|---------|
| 支撑压力线 | `https://5000-.../api/support-resistance/latest` |
| 交易信号 | `https://5000-.../api/trading-signals/analyze` |
| 锚点系统 | `https://5000-.../api/anchor-system/current-positions` |
| K线指标 | `https://5000-.../api/kline-indicators/signals` |

## 验证步骤

### ✅ 步骤1: 测试后端API
```bash
curl -s https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai/api/support-resistance/latest | head -10
```

如果返回JSON数据 → 后端正常 ✅

### ✅ 步骤2: 检查前端配置
```bash
cd /home/user/webapp
grep -r "http://localhost:5000" templates/*.html
```

如果找到 `localhost:5000` → 需要替换为公共URL

### ✅ 步骤3: 修改前端配置（如果需要）
```bash
# 批量替换所有HTML文件中的localhost为公共URL
sed -i 's|http://localhost:5000|https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai|g' templates/*.html
```

### ✅ 步骤4: 重启Flask（如果修改了代码）
```bash
pm2 restart flask-app
```

## 系统状态检查

### 当前状态（2026-01-04 03:10:00）
```
✅ Flask应用: 运行中（uptime: 2分钟）
✅ 端口5000: 正常监听
✅ 内存使用: 112.5 MB（正常）
✅ API响应: 200 OK
✅ 所有PM2进程: 在线
```

### 实时状态检查命令
```bash
# 检查所有服务
pm2 status

# 检查Flask日志
pm2 logs flask-app --lines 20

# 测试API
curl http://localhost:5000/api/support-resistance/latest
```

## 总结

**根本原因**: 前端使用了错误的访问地址（localhost）而不是公共URL

**解决方案**: 
1. ✅ 使用正确的公共URL: `https://5000-ifbgdsngd9an7si2g7jy0-5634da27.sandbox.novita.ai`
2. ✅ 确保CORS配置正确
3. ✅ 清除浏览器缓存
4. ✅ 如果修改了前端配置，重启Flask应用

**验证方法**:
- 在浏览器直接访问公共URL
- 检查开发者工具的网络面板
- 确认API返回200状态码

---

**文档创建时间**: 2026-01-04 03:15:00  
**系统状态**: 🟢 正常运行  
**公共URL有效期**: 沙盒运行期间持续有效
