#!/usr/bin/env python3
"""
测试主账号普通维护（maintain_anchor_order）
测试币对：CRO-USDT-SWAP
流程：先平旧仓 → 开10倍仓 → 平掉92%
"""

import requests
import json
import time

# 测试参数
BASE_URL = "http://localhost:5000"
TEST_INST_ID = "CRO-USDT-SWAP"
TEST_POS_SIDE = "long"

def get_position(inst_id, pos_side):
    """获取持仓信息"""
    url = f"{BASE_URL}/api/anchor-system/current-positions?trade_mode=real"
    response = requests.get(url)
    data = response.json()
    
    for pos in data.get('positions', []):
        if pos['inst_id'] == inst_id and pos['pos_side'] == pos_side:
            return pos
    return None

def test_maintain_anchor():
    """测试主账号普通维护"""
    print("=" * 80)
    print("🧪 测试主账号普通维护（maintain_anchor_order）")
    print("=" * 80)
    
    # 1. 获取当前持仓
    print("\n📊 步骤1：获取当前持仓信息")
    pos = get_position(TEST_INST_ID, TEST_POS_SIDE)
    
    if not pos:
        print(f"❌ 未找到持仓: {TEST_INST_ID} {TEST_POS_SIDE}")
        return
    
    print(f"✅ 当前持仓:")
    print(f"   币对: {pos['inst_id']}")
    print(f"   方向: {pos['pos_side']}")
    print(f"   持仓量: {pos['pos_size']}")
    print(f"   保证金: {pos['margin']:.2f}U")
    print(f"   收益率: {pos['profit_rate']:.2f}%")
    print(f"   标记价格: ${pos['mark_price']}")
    
    pos_size = pos['pos_size']
    
    # 2. 执行维护
    print(f"\n📊 步骤2：执行主账号普通维护")
    print(f"   操作: 开10倍仓 ({pos_size} × 10 = {pos_size * 10}) → 平掉92%")
    
    url = f"{BASE_URL}/api/anchor/maintain-anchor"
    payload = {
        "inst_id": TEST_INST_ID,
        "pos_side": TEST_POS_SIDE,
        "pos_size": pos_size
    }
    
    print(f"\n📤 发送请求:")
    print(f"   URL: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload)
    
    print(f"\n📥 响应状态码: {response.status_code}")
    
    try:
        result = response.json()
        print(f"\n📝 响应内容:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            print(f"\n✅ 维护成功！")
            
            # 等待5秒后查看新持仓
            print(f"\n⏳ 等待5秒后查看新持仓...")
            time.sleep(5)
            
            new_pos = get_position(TEST_INST_ID, TEST_POS_SIDE)
            if new_pos:
                print(f"\n📊 维护后持仓:")
                print(f"   持仓量: {new_pos['pos_size']}")
                print(f"   保证金: {new_pos['margin']:.2f}U")
                print(f"   收益率: {new_pos['profit_rate']:.2f}%")
                
                # 对比
                print(f"\n📈 变化对比:")
                print(f"   持仓量: {pos_size} → {new_pos['pos_size']} (变化: {new_pos['pos_size'] - pos_size:+.1f})")
                print(f"   保证金: {pos['margin']:.2f}U → {new_pos['margin']:.2f}U (变化: {new_pos['margin'] - pos['margin']:+.2f}U)")
        else:
            print(f"\n❌ 维护失败: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ 解析响应失败: {e}")
        print(f"原始响应: {response.text}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_maintain_anchor()
