#!/usr/bin/env python3
"""
锚点单保护脚本
确保主账户的多空对冲持仓完整性
"""

import sys
sys.path.append('/home/user/webapp')
from anchor_system import get_positions_from_okex
from datetime import datetime

def check_anchor_positions():
    """检查锚点单完整性"""
    positions = get_positions_from_okex()
    
    # 统计每个币种的多空持仓
    position_map = {}
    for p in positions:
        inst_id = p.get('instId')
        pos_side = p.get('posSide')
        pos_size = float(p.get('pos', 0))
        
        if inst_id not in position_map:
            position_map[inst_id] = {'long': 0, 'short': 0}
        
        position_map[inst_id][pos_side] = pos_size
    
    # 检查哪些币种缺少对冲
    print(f"\n{'='*80}")
    print(f"{'锚点单完整性检查':<30} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    total_positions = len(positions)
    missing_hedge = []
    complete_hedge = []
    
    print(f"{'币种':<20} {'多单':<15} {'空单':<15} {'状态'}")
    print(f"{'-'*80}")
    
    for inst_id, sides in sorted(position_map.items()):
        long_size = sides['long']
        short_size = sides['short']
        
        if long_size > 0 and short_size > 0:
            status = '✅ 完整对冲'
            complete_hedge.append(inst_id)
        elif long_size > 0 and short_size == 0:
            status = '⚠️  缺少空单'
            missing_hedge.append((inst_id, 'short'))
        elif long_size == 0 and short_size > 0:
            status = '⚠️  缺少多单'
            missing_hedge.append((inst_id, 'long'))
        else:
            status = '❓ 无持仓'
        
        print(f"{inst_id:<20} {long_size:<15.2f} {short_size:<15.2f} {status}")
    
    print(f"{'-'*80}")
    print(f"\n📊 统计:")
    print(f"   总持仓数: {total_positions}")
    print(f"   完整对冲: {len(complete_hedge)} 个")
    print(f"   缺少对冲: {len(missing_hedge)} 个")
    
    if missing_hedge:
        print(f"\n⚠️  警告：以下币种缺少对冲持仓:")
        for inst_id, missing_side in missing_hedge:
            print(f"   - {inst_id}: 缺少 {missing_side} 单")
    
    print(f"\n{'='*80}\n")
    
    return missing_hedge

if __name__ == '__main__':
    missing = check_anchor_positions()
    
    if missing:
        print(f"🚨 发现 {len(missing)} 个不完整的锚点单！")
        print(f"💡 建议：立即检查这些持仓是否被误平，并补仓")
        sys.exit(1)
    else:
        print(f"✅ 所有锚点单对冲完整！")
        sys.exit(0)
