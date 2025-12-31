import requests
import json

response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions')
data = response.json()

if data.get('success') and data.get('positions'):
    print("\n" + "=" * 80)
    print("合并后的持仓数据")
    print("=" * 80)
    
    for i, pos in enumerate(data['positions'], 1):
        print(f"\n【持仓 {i}】")
        print(f"  账户: {pos['account_name']}")
        print(f"  币种: {pos['inst_id']}")
        print(f"  方向: {pos['pos_side']}")
        print(f"  开仓价: {pos['avg_price']:.8f} (加权平均)")
        print(f"  当前价: {pos['mark_price']:.8f}")
        print(f"  数量: {pos['pos_size']:.1f} 张")
        print(f"  保证金: {pos['margin']:.4f} USDT")
        print(f"  未实现盈亏: {pos['upl']:.4f} USDT")
        print(f"  收益率: {pos['profit_rate']:.2f}%")
        print(f"  名义价值: {pos['notional_usd']:.2f} USDT")
        print(f"  杠杆: {pos['leverage']}x")
        print(f"  今日维护次数: {pos['maintenance_count']}")
    
    print("\n" + "=" * 80)
    print(f"总持仓数: {len(data['positions'])} 个 (已合并)")
    print("=" * 80)
    
    # 验证计算
    if len(data['positions']) > 0:
        pos = data['positions'][0]
        print("\n✅ 验证合并计算:")
        
        # 原始两个持仓的数据（从之前的测试）
        print("\n  原持仓1: 开仓价 0.09191, 数量 108, 保证金 9.9187, 盈亏 -0.0756")
        print("  原持仓2: 开仓价 0.09256267, 数量 108, 保证金 9.9973, 盈亏 -0.7805")
        
        print("\n  合并后计算:")
        total_size = 216
        weighted_price = (0.09191 * 108 + 0.09256267 * 108) / 216
        total_margin = 9.9187 + 9.9973
        total_upl = -0.0756 + (-0.7805)
        profit_rate = (total_upl / total_margin) * 100
        
        print(f"    总数量: {total_size} 张")
        print(f"    加权平均开仓价: {weighted_price:.8f}")
        print(f"    总保证金: {total_margin:.4f} USDT")
        print(f"    总盈亏: {total_upl:.4f} USDT")
        print(f"    收益率: {profit_rate:.2f}%")
        
        print("\n  API返回值:")
        print(f"    总数量: {pos['pos_size']:.1f} 张")
        print(f"    加权平均开仓价: {pos['avg_price']:.8f}")
        print(f"    总保证金: {pos['margin']:.4f} USDT")
        print(f"    总盈亏: {pos['upl']:.4f} USDT")
        print(f"    收益率: {pos['profit_rate']:.2f}%")
        
        if abs(pos['pos_size'] - total_size) < 0.1 and abs(pos['margin'] - total_margin) < 0.01:
            print("\n  ✅ 合并计算正确！")
        else:
            print("\n  ❌ 合并计算有误！")
else:
    print('❌ API返回错误')
    print(data)
