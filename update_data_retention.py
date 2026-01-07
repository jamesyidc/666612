# 修改数据保留期为16天
import sys
sys.path.insert(0, '/home/user/webapp')
from sar_slope_jsonl_system import SARSlopeJSONLSystem

# 更新系统配置
config_file = 'sar_slope_jsonl_system.py'
with open(config_file, 'r') as f:
    content = f.read()

# 修改保留天数
content = content.replace('self.keep_days = 7', 'self.keep_days = 16')

with open(config_file, 'w') as f:
    f.write(content)

print("✅ 数据保留期已更新为16天")
