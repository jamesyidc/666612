#!/usr/bin/env python3
"""
测试超级维护 - 优化顺序：先平仓再开仓
"""
import requests
import json

print("🧪 测试超级维护（优化版）\n")
print("策略：先平仓释放保证金 → 再开新仓 → 最后调整保证金\n")

# 步骤1：获取当前APT持仓信息
response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions', timeout=10)
data = response.json()

if not data.get('success'):
    print("❌ 获取持仓失败")
    exit(1)

apt_pos = next((p for p in data['positions'] 
                if p['account_name'] == 'Wu666666' 
                and p['inst_id'] == 'APT-USDT-SWAP' 
                and p['pos_side'] == 'long'), None)

if not apt_pos:
    print("❌ 未找到APT持仓")
    exit(1)

print(f"当前APT持仓:")
print(f"  保证金: {apt_pos['margin']:.2f}U")
print(f"  持仓量: {apt_pos.get('pos_size', 'N/A')}")
print(f"  收益率: {apt_pos['profit_rate']:.2f}%")
print(f"  维护次数: {apt_pos['maintenance_count']}/3\n")

# 步骤2：先平掉所有持仓（释放保证金）
print("📤 步骤1：平掉当前持仓...\n")
close_response = requests.post('http://localhost:5000/api/anchor/close-sub-account-position',
                               json={
                                   'account_name': 'Wu666666',
                                   'inst_id': 'APT-USDT-SWAP',
                                   'pos_side': 'long',
                                   'close_size': apt_pos.get('pos_size'),
                                   'reason': '超级维护：先平仓释放保证金'
                               },
                               timeout=30)

close_result = close_response.json()

if close_result.get('success'):
    print(f"✅ 平仓成功！订单ID: {close_result.get('order_id', 'N/A')}\n")
else:
    print(f"❌ 平仓失败: {close_result.get('message', 'Unknown')}\n")
    exit(1)

# 步骤3：等待3秒让平仓生效
import time
print("⏳ 等待3秒让平仓生效...")
time.sleep(3)

# 步骤4：开100U新仓
print("\n📥 步骤2：开100U新仓...\n")
open_response = requests.post('http://localhost:5000/api/anchor/open-sub-account-position',
                              json={
                                  'account_name': 'Wu666666',
                                  'inst_id': 'APT-USDT-SWAP',
                                  'pos_side': 'long',
                                  'amount': 100
                              },
                              timeout=30)

open_result = open_response.json()

if open_result.get('success'):
    print(f"✅ 开仓成功！")
    print(f"  订单ID: {open_result.get('order_id', 'N/A')}")
    print(f"  开仓数量: {open_result.get('open_size', 'N/A')}\n")
else:
    print(f"❌ 开仓失败: {open_result.get('message', 'Unknown')}\n")
    exit(1)

# 步骤5：调整保证金到10U
print("💰 步骤3：调整保证金到10U...\n")
print("（如果是逐仓模式，需要手动转出多余保证金）")
print("（纠错机制会在5分钟内自动处理）\n")

print("🎉 超级维护完成！")
