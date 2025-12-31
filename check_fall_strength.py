#!/usr/bin/env python3
import requests

# 从Flask API获取持仓（实盘模式）
response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real')
data = response.json()

positions = data.get('positions', [])
short_positions = [p for p in positions if p.get('pos_side') == 'short']

print(f'总持仓数: {len(positions)}')
print(f'空单数: {len(short_positions)}')
print()

if len(short_positions) == 0:
    print('⚠️  当前没有空单，无法判断下跌强度！')
    print()
    print('多单持仓情况:')
    long_positions = [p for p in positions if p.get('pos_side') == 'long']
    for p in long_positions:
        print(f"  {p.get('inst_id')}: {p.get('profit_rate', 0):.2f}%")
    exit()

# 统计空单盈利情况
profit_stats = {'70+': 0, '60+': 0, '50+': 0, '40+': 0}

print('空单详情:')
print(f'{"币种":<20} {"收益率":<12} {"未实现盈亏":<15}')
print('-' * 50)

for p in short_positions:
    inst_id = p.get('inst_id', '')
    profit_rate = p.get('profit_rate', 0)
    upl = p.get('upl', 0)
    
    print(f'{inst_id:<20} {profit_rate:>10.2f}% {upl:>14.4f} USDT')
    
    # 统计
    if profit_rate >= 70:
        profit_stats['70+'] += 1
    if profit_rate >= 60:
        profit_stats['60+'] += 1
    if profit_rate >= 50:
        profit_stats['50+'] += 1
    if profit_rate >= 40:
        profit_stats['40+'] += 1

print()
print('空单盈利统计:')
print(f'盈利≥70%: {profit_stats["70+"]}')
print(f'盈利≥60%: {profit_stats["60+"]}')
print(f'盈利≥50%: {profit_stats["50+"]}')
print(f'盈利≥40%: {profit_stats["40+"]}')
print()

# 判断下跌强度
p70 = profit_stats['70+']
p60 = profit_stats['60+']
p50 = profit_stats['50+']
p40 = profit_stats['40+']

print('下跌强度判断:')
if p70 == 0 and p60 == 0 and p50 == 0 and p40 <= 3:
    print('🟢 下跌强度: 1级【多单买入点在50%】')
    print('   条件: ≥70%=0, ≥60%=0, ≥50%=0, ≥40%≤3')
elif p70 == 0 and p60 <= 1 and p50 <= 4 and p40 <= 5:
    print('🟡 下跌强度: 2级【多单买入点在60%】')
    print('   条件: ≥70%=0, ≥60%≤1, ≥50%≤4, ≥40%≤5')
elif p70 <= 2 and p60 <= 5 and p50 <= 8 and p40 <= 11:
    print('🔴 下跌强度: 3级【多单买入点在70-80%】')
    print('   条件: ≥70%≤2, ≥60%≤5, ≥50%≤8, ≥40%≤11')
else:
    print('⚠️  下跌强度: 超出范围（市场极端下跌）')
    print(f'   实际: ≥70%={p70}, ≥60%={p60}, ≥50%={p50}, ≥40%={p40}')
