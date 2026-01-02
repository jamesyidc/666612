#!/usr/bin/env python3
"""
子账户持仓纠错脚本
用于修正错误的持仓量，使其恢复到正确的锚定单配置
"""

import sqlite3
import json
import sys
from datetime import datetime
from trading_api import OKXTrader

# 配置
DB_PATH = '/home/user/webapp/trading_decision.db'
TRADE_MODE = 'real'  # 实盘模式

# 初始化交易API
trader = OKXTrader(trade_mode=TRADE_MODE)

def get_expected_positions():
    """从 position_opens 表获取预期的持仓配置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            inst_id,
            pos_side,
            open_size,
            open_price,
            is_anchor
        FROM position_opens
        WHERE is_anchor = 1
        ORDER BY created_at DESC
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    expected = {}
    for inst_id, pos_side, open_size, open_price, is_anchor in records:
        key = f"{inst_id}_{pos_side}"
        if key not in expected:  # 只保留最新的记录
            expected[key] = {
                'inst_id': inst_id,
                'pos_side': pos_side,
                'expected_size': open_size,
                'open_price': open_price
            }
    
    return expected

def get_actual_positions():
    """获取子账户的实际持仓"""
    try:
        response = trader.get_sub_account_positions()
        
        if response['code'] != '0':
            print(f"❌ 获取持仓失败: {response}")
            return {}
        
        actual = {}
        for pos in response['data']:
            inst_id = pos['instId']
            pos_side = pos['posSide']
            pos_size = abs(float(pos['pos']))
            avg_price = float(pos['avgPx'])
            
            key = f"{inst_id}_{pos_side}"
            actual[key] = {
                'inst_id': inst_id,
                'pos_side': pos_side,
                'actual_size': pos_size,
                'avg_price': avg_price
            }
        
        return actual
        
    except Exception as e:
        print(f"❌ 获取持仓异常: {e}")
        return {}

def close_excess_position(inst_id, pos_side, excess_size):
    """平掉多余的持仓"""
    try:
        print(f"\n🔧 准备平仓 {inst_id} {pos_side}方向，数量: {excess_size}")
        
        # 确定平仓方向
        close_side = 'buy' if pos_side == 'short' else 'sell'
        
        # 执行平仓
        result = trader.place_order(
            inst_id=inst_id,
            trade_mode=pos_side,  # long 或 short
            side=close_side,      # buy 或 sell
            order_type='market',   # 市价单
            size=excess_size,
            reduce_only=True       # 只减仓
        )
        
        if result['code'] == '0':
            print(f"✅ 平仓成功: {inst_id} {pos_side} {excess_size} 张")
            return True
        else:
            print(f"❌ 平仓失败: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 平仓异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_positions(dry_run=True):
    """修正持仓
    
    Args:
        dry_run: True=仅模拟，不实际操作; False=实际执行
    """
    print("=" * 100)
    print("🔍 子账户持仓纠错系统")
    print(f"模式: {'🧪 模拟运行（不实际操作）' if dry_run else '⚠️  实际执行'}")
    print("=" * 100)
    
    # 获取预期持仓和实际持仓
    expected = get_expected_positions()
    actual = get_actual_positions()
    
    print(f"\n📊 预期持仓配置: {len(expected)} 个")
    print(f"📊 实际持仓: {len(actual)} 个")
    
    # 检查每个实际持仓
    issues = []
    
    for key, actual_pos in actual.items():
        inst_id = actual_pos['inst_id']
        pos_side = actual_pos['pos_side']
        actual_size = actual_pos['actual_size']
        
        if key in expected:
            expected_size = expected[key]['expected_size']
            
            # 计算差异
            diff = actual_size - expected_size
            diff_pct = (diff / expected_size * 100) if expected_size > 0 else 0
            
            if abs(diff) > 0.01:  # 容差 0.01 张
                status = "🔴 多开" if diff > 0 else "🟡 少开"
                issues.append({
                    'inst_id': inst_id,
                    'pos_side': pos_side,
                    'expected_size': expected_size,
                    'actual_size': actual_size,
                    'diff': diff,
                    'diff_pct': diff_pct,
                    'status': status
                })
        else:
            # 没有预期持仓，但有实际持仓（不应该存在的持仓）
            issues.append({
                'inst_id': inst_id,
                'pos_side': pos_side,
                'expected_size': 0,
                'actual_size': actual_size,
                'diff': actual_size,
                'diff_pct': 0,
                'status': "❌ 不应存在"
            })
    
    # 显示问题列表
    if not issues:
        print("\n✅ 没有发现持仓异常！")
        return
    
    print(f"\n⚠️  发现 {len(issues)} 个持仓异常:")
    print("=" * 100)
    print(f"{'币种':<20} {'方向':<10} {'预期':<10} {'实际':<10} {'差异':<10} {'差异%':<10} {'状态':<15}")
    print("=" * 100)
    
    for issue in issues:
        print(f"{issue['inst_id']:<20} {issue['pos_side']:<10} "
              f"{issue['expected_size']:<10.1f} {issue['actual_size']:<10.1f} "
              f"{issue['diff']:<10.1f} {issue['diff_pct']:<10.1f} {issue['status']:<15}")
    
    # 修正持仓
    print("\n" + "=" * 100)
    print("🔧 开始修正持仓...")
    print("=" * 100)
    
    for issue in issues:
        inst_id = issue['inst_id']
        pos_side = issue['pos_side']
        expected_size = issue['expected_size']
        actual_size = issue['actual_size']
        diff = issue['diff']
        
        if diff > 0:
            # 多开了，需要平仓
            excess_size = diff
            print(f"\n🔴 {inst_id} {pos_side} 多开了 {excess_size:.1f} 张")
            print(f"   预期: {expected_size:.1f} 张 | 实际: {actual_size:.1f} 张")
            
            if dry_run:
                print(f"   🧪 [模拟] 应该平仓 {excess_size:.1f} 张")
            else:
                print(f"   ⚠️  [执行] 正在平仓 {excess_size:.1f} 张...")
                success = close_excess_position(inst_id, pos_side, excess_size)
                if success:
                    print(f"   ✅ 平仓完成")
                else:
                    print(f"   ❌ 平仓失败")
        
        elif diff < 0:
            # 少开了，需要补仓（但要等亏损时才补）
            shortage = abs(diff)
            print(f"\n🟡 {inst_id} {pos_side} 少开了 {shortage:.1f} 张")
            print(f"   预期: {expected_size:.1f} 张 | 实际: {actual_size:.1f} 张")
            print(f"   💡 根据策略，补仓需要等到亏损时执行，暂不处理")
    
    print("\n" + "=" * 100)
    if dry_run:
        print("🧪 模拟运行完成！如需实际执行，请使用参数: --execute")
    else:
        print("✅ 持仓修正完成！")
    print("=" * 100)

if __name__ == '__main__':
    # 检查命令行参数
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        dry_run = False
        print("\n⚠️  警告：将实际执行平仓操作！")
        print("按 Ctrl+C 取消，或等待 5 秒后自动开始...")
        import time
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n❌ 操作已取消")
            sys.exit(0)
    
    fix_positions(dry_run=dry_run)
