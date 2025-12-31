#!/usr/bin/env python3
"""测试15分钟维护间隔检查"""

import json
from datetime import datetime, timezone, timedelta

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def check_maintenance_interval(account_name, inst_id, pos_side, min_interval_minutes=15):
    """检查距离上次维护是否已经过了足够的时间（默认15分钟）"""
    try:
        with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{account_name}_{inst_id}_{pos_side}"
        if key not in data:
            return True, "没有维护记录"
        
        last_maintenance_str = data[key].get('last_maintenance')
        if not last_maintenance_str:
            return True, "没有上次维护时间"
        
        # 解析上次维护时间
        last_maintenance = datetime.strptime(last_maintenance_str, '%Y-%m-%d %H:%M:%S')
        last_maintenance = last_maintenance.replace(tzinfo=timezone(timedelta(hours=8)))
        
        # 计算时间差
        now = get_china_time()
        time_diff = (now - last_maintenance).total_seconds() / 60  # 转换为分钟
        
        if time_diff < min_interval_minutes:
            remaining = min_interval_minutes - time_diff
            return False, f"距离上次维护仅 {time_diff:.1f} 分钟，需等待 {remaining:.1f} 分钟"
        
        return True, f"距离上次维护已 {time_diff:.1f} 分钟，可以维护"
    except FileNotFoundError:
        return True, "文件不存在"
    except Exception as e:
        return True, f"检查失败: {e}"

print("\n" + "="*80)
print("测试15分钟维护间隔检查")
print("="*80 + "\n")

# 测试几个币种
test_cases = [
    ("Wu666666", "CFX-USDT-SWAP", "long"),
    ("Wu666666", "APT-USDT-SWAP", "long"),
    ("Wu666666", "CRV-USDT-SWAP", "long"),
    ("Wu666666", "TON-USDT-SWAP", "long"),
]

for account, inst_id, pos_side in test_cases:
    allowed, msg = check_maintenance_interval(account, inst_id, pos_side)
    status = "✅ 允许" if allowed else "❌ 不允许"
    print(f"{inst_id:20s} {status:10s} {msg}")

print("\n" + "="*80 + "\n")
