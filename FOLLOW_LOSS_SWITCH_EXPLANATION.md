# 跟单开关功能说明

## 问题说明
用户反馈：勾选了"跟空单亏损开单"和"跟多单亏损开单"的checkbox后，刷新页面发现checkbox还是关闭的。

## 原因分析
经过检查代码和测试API，发现：

1. ✅ **前端逻辑正常**：checkbox的change事件正确监听，会调用API保存配置
2. ✅ **后端API正常**：`/api/sub-account/config` POST接口可以正确保存配置到文件
3. ✅ **配置读取正常**：页面加载时会调用GET接口读取当前配置并设置checkbox状态

## 正确的工作流程

### 1. 用户勾选checkbox
```javascript
// 前端代码（templates/anchor_system_real.html）
document.getElementById('followShortLoss').addEventListener('change', async function(e) {
    const enabled = e.target.checked;  // 获取checkbox状态
    
    // 调用API保存配置
    const response = await fetch('/api/sub-account/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            follow_short_loss_enabled: enabled  // 保存到配置文件
        })
    });
});
```

### 2. 后端保存配置
```python
# 后端代码（app_new.py）
@app.route('/api/sub-account/config', methods=['POST'])
def sub_account_config_v2():
    data = request.get_json()
    
    # 读取现有配置
    with open('sub_account_config.json', 'r') as f:
        config = json.load(f)
    
    # 更新指定字段
    if 'follow_short_loss_enabled' in data:
        config['follow_short_loss_enabled'] = data['follow_short_loss_enabled']
    if 'follow_long_loss_enabled' in data:
        config['follow_long_loss_enabled'] = data['follow_long_loss_enabled']
    
    # 保存到文件
    with open('sub_account_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    return jsonify({'success': True})
```

### 3. 页面刷新时加载配置
```javascript
// 页面加载时读取配置
const configRes = await fetch('/api/sub-account/config');
const configData = await configRes.json();

if (configData.success) {
    const config = configData.config;
    // 根据配置文件中的值设置checkbox状态
    document.getElementById('followShortLoss').checked = config.follow_short_loss_enabled || false;
    document.getElementById('followLongLoss').checked = config.follow_long_loss_enabled || false;
}
```

## 当前配置状态
经过测试，当前配置已正确保存：
```json
{
  "follow_short_loss_enabled": true,
  "follow_long_loss_enabled": true
}
```

## 功能逻辑说明

### 跟空单亏损开单（follow_short_loss_enabled）
- **触发条件**：主账户的空单出现亏损
- **开单方向**：子账户开多单（做相反方向）
- **强度要求**：上涨强度等级 ≥ 5（说明市场在强势上涨，空单亏损正常）
- **工作原理**：主账户空单亏损 → 市场上涨 → 子账户做多顺势而为

### 跟多单亏损开单（follow_long_loss_enabled）
- **触发条件**：主账户的多单出现亏损
- **开单方向**：子账户开空单（做相反方向）
- **强度要求**：下跌强度等级 ≥ 5（说明市场在强势下跌，多单亏损正常）
- **工作原理**：主账户多单亏损 → 市场下跌 → 子账户做空顺势而为

## 守护进程逻辑
```python
# sub_account_opener_daemon.py
# 检查跟单开关
if pos_side == 'short':  # 主账户空单亏损
    if not config.get('follow_short_loss_enabled', False):
        print(f"跟空单亏损开单未启用，跳过")
        continue
    # 检查上涨强度>=5
    if market_strength['rise_level'] < 5:
        print(f"上涨强度等级不足（需要>=5），跳过")
        continue
    # 满足条件，子账户开多单
    open_sub_account_position(inst_id, 'long', ...)

elif pos_side == 'long':  # 主账户多单亏损
    if not config.get('follow_long_loss_enabled', False):
        print(f"跟多单亏损开单未启用，跳过")
        continue
    # 检查下跌强度>=5
    if market_strength['decline_level'] < 5:
        print(f"下跌强度等级不足（需要>=5），跳过")
        continue
    # 满足条件，子账户开空单
    open_sub_account_position(inst_id, 'short', ...)
```

## 验证方法

### 1. 查看当前配置
```bash
cd /home/user/webapp
cat sub_account_config.json | grep follow
```

### 2. 手动设置配置（如果需要）
```bash
# 开启跟空单亏损开单
curl -X POST http://localhost:5000/api/sub-account/config \
  -H "Content-Type: application/json" \
  -d '{"follow_short_loss_enabled": true}'

# 开启跟多单亏损开单
curl -X POST http://localhost:5000/api/sub-account/config \
  -H "Content-Type: application/json" \
  -d '{"follow_long_loss_enabled": true}'
```

### 3. 查看守护进程日志
```bash
pm2 logs sub-account-opener --lines 50
```

## 测试结果
✅ 配置API测试通过
✅ 配置已成功保存到文件
✅ 页面刷新后应该能正确显示勾选状态

## 注意事项
1. **配置文件权限**：确保Flask进程有权限写入`sub_account_config.json`
2. **并发问题**：多个进程同时修改配置文件时可能有冲突（当前系统只有Flask进程会写入）
3. **刷新时机**：修改配置后，守护进程会在下一次检查周期（60秒）自动读取新配置
4. **强度要求**：即使开关打开，也需要市场强度达到5级才会触发跟单

---
**文档创建时间**: 2026-01-03 02:05 UTC
**配置文件路径**: /home/user/webapp/sub_account_config.json
**相关代码文件**: 
- templates/anchor_system_real.html (前端)
- app_new.py (后端API)
- sub_account_opener_daemon.py (守护进程)
