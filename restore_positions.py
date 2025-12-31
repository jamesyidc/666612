#!/usr/bin/env python3
"""
恢复AAVE和CRO持仓
因为测试时这两个持仓被清空了，现在重新开仓恢复
"""

import requests
import time

API_BASE = "http://localhost:5000"

def restore_position(inst_id, target_margin=10):
    """恢复持仓到目标保证金"""
    print(f"\n{'='*70}")
    print(f"🔄 恢复持仓: {inst_id}")
    print(f"{'='*70}")
    
    # 调用维护API，pos_size=0表示没有旧持仓，直接开新仓
    response = requests.post(
        f"{API_BASE}/api/anchor/maintain-sub-account",
        json={
            "account_name": "Wu666666",
            "inst_id": inst_id,
            "pos_side": "long",
            "pos_size": 0,  # 没有旧持仓
            "amount": target_margin,  # 开仓金额=目标保证金
            "target_margin": target_margin,
            "maintenance_count": 0
        },
        timeout=30
    )
    
    result = response.json()
    
    if result.get('success'):
        print(f"✅ {inst_id} 恢复成功！")
        data = result.get('data', {})
        print(f"   开仓订单ID: {data.get('open_order_id')}")
        print(f"   保留持仓: {data.get('keep_size')} 张")
        return True
    else:
        print(f"❌ {inst_id} 恢复失败")
        print(f"   错误: {result.get('message')}")
        return False

def main():
    print("\n" + "="*70)
    print("🔧 开始恢复AAVE和CRO持仓")
    print("="*70)
    
    # 恢复AAVE (目标10U保证金)
    success_aave = restore_position("AAVE-USDT-SWAP", target_margin=10)
    time.sleep(2)
    
    # 恢复CRO (目标10U保证金)
    success_cro = restore_position("CRO-USDT-SWAP", target_margin=10)
    
    print("\n" + "="*70)
    print("📊 恢复结果总结")
    print("="*70)
    print(f"AAVE-USDT-SWAP: {'✅ 成功' if success_aave else '❌ 失败'}")
    print(f"CRO-USDT-SWAP:  {'✅ 成功' if success_cro else '❌ 失败'}")
    print("="*70)
    
    if success_aave and success_cro:
        print("✅ 所有持仓恢复成功！")
        return 0
    else:
        print("⚠️  部分持仓恢复失败，请检查日志")
        return 1

if __name__ == "__main__":
    exit(main())
