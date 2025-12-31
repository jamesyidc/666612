import requests
import json

response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions')
data = response.json()

if data.get('success') and data.get('positions'):
    for pos in data['positions']:
        print(f"\n币种: {pos['inst_id']}")
        print(f"账户: {pos['account_name']}")
        print(f"持仓方向: {pos['pos_side']}")
        print(f"保证金: {pos['margin']:.4f} USDT")
        print(f"未实现盈亏: {pos['upl']:.4f} USDT")
        print(f"收益率: {pos['profit_rate']:.2f}%")
        print(f"名义价值: {pos['notional_usd']:.2f} USDT")
        print(f"杠杆: {pos['leverage']}x")
        
        print('\n✅ 验证计算:')
        calculated = (pos['upl'] / pos['margin']) * 100
        print(f"  收益率 = 未实现盈亏 / 保证金 * 100")
        print(f"  收益率 = {pos['upl']:.4f} / {pos['margin']:.4f} * 100")
        print(f"  收益率 = {calculated:.2f}%")
        
        if abs(calculated - pos['profit_rate']) < 0.01:
            print(f"  ✅ 计算正确！")
        else:
            print(f"  ❌ 计算错误！API返回 {pos['profit_rate']:.2f}%，实际应为 {calculated:.2f}%")
else:
    print('❌ API返回错误')
    print(data)
