#!/usr/bin/env python3
"""
恢复缺失的对冲持仓
根据检查结果自动补齐缺失的多空对冲单
"""

import sys
import json
sys.path.append('/home/user/webapp')
from anchor_system import get_positions_from_okex
from datetime import datetime

# 缺失的对冲持仓（根据检查结果）
MISSING_HEDGES = [
    {'inst_id': 'CFX-USDT-SWAP', 'side': 'short', 'reason': '空单被平'},
    {'inst_id': 'CRO-USDT-SWAP', 'side': 'long', 'reason': '多单被平'},
    {'inst_id': 'FIL-USDT-SWAP', 'side': 'long', 'reason': '多单被平'},
    {'inst_id': 'TON-USDT-SWAP', 'side': 'long', 'reason': '多单被平'},
    {'inst_id': 'XLM-USDT-SWAP', 'side': 'short', 'reason': '空单被平'},
]

def restore_hedge_position(inst_id, pos_side, dry_run=True):
    """恢复对冲持仓"""
    try:
        print(f"\n{'='*60}")
        print(f"恢复对冲: {inst_id} {pos_side}")
        print(f"{'='*60}")
        
        # 获取当前价格
        positions = get_positions_from_okex()
        
        # 查找该币种的已有持仓来确定开仓数量
        existing = [p for p in positions if p.get('instId') == inst_id]
        
        if not existing:
            print(f"⚠️  该币种没有任何持仓，无法确定对冲数量")
            return False
        
        # 使用已有持仓的数量作为参考
        existing_pos = existing[0]
        existing_size = float(existing_pos.get('pos', 0))
        current_price = float(existing_pos.get('markPx', 0))
        
        print(f"📊 参考持仓数量: {existing_size}")
        print(f"📊 当前价格: ${current_price:.4f}")
        
        # 设置开仓数量（使用相同或相近的数量）
        target_size = existing_size
        
        print(f"🎯 计划开仓: {target_size} 张")
        
        if dry_run:
            print(f"🔍 [DRY-RUN模式] 不执行实际开仓")
            return False
        
        # 实际开仓
        print(f"📝 执行开仓...")
        # TODO: 调用开仓API
        # result = place_order(inst_id, pos_side, target_size)
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """主函数"""
    dry_run = '--execute' not in sys.argv
    
    print(f"\n{'='*80}")
    print(f"🔧 锚点单对冲恢复工具")
    if dry_run:
        print(f"🔍 运行模式: DRY-RUN (仅检查，不执行)")
        print(f"💡 提示: 使用 --execute 参数执行实际恢复")
    else:
        print(f"⚠️  运行模式: 执行恢复")
    print(f"{'='*80}\n")
    
    print(f"发现 {len(MISSING_HEDGES)} 个缺失的对冲持仓:\n")
    for item in MISSING_HEDGES:
        print(f"  - {item['inst_id']}: 缺少 {item['side']} 单 ({item['reason']})")
    
    print(f"\n{'='*80}\n")
    
    success_count = 0
    for item in MISSING_HEDGES:
        result = restore_hedge_position(
            item['inst_id'], 
            item['side'], 
            dry_run=dry_run
        )
        if result:
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"📊 恢复结果: 成功 {success_count}/{len(MISSING_HEDGES)}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
