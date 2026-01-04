"""
修复跨日期自动更新功能
问题：last_reset_date 在进程重启后会重置为当前日期
解决：将 last_reset_date 保存到配置文件中
"""
import json
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
CONFIG_FILE = "daily_folder_config.json"

# 读取配置
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 添加 last_reset_date 字段（如果不存在）
current_date = datetime.now(BEIJING_TZ).date().strftime('%Y-%m-%d')

if 'last_reset_date' not in config:
    config['last_reset_date'] = config.get('current_date', current_date)
    print(f"✅ 添加 last_reset_date 字段: {config['last_reset_date']}")
else:
    print(f"ℹ️  last_reset_date 已存在: {config['last_reset_date']}")

# 保存配置
with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✅ 配置已更新")
print(f"   current_date: {config['current_date']}")
print(f"   last_reset_date: {config['last_reset_date']}")
