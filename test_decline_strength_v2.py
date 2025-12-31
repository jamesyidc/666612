#!/usr/bin/env python3
"""
测试下跌强度等级判断逻辑 V2
"""

def test_decline_strength(profit100, profit90, profit80, profit70, profit60, profit50, profit40):
    """测试下跌强度等级判断"""
    print(f"\n{'='*60}")
    print(f"测试数据:")
    print(f"  profit100={profit100}, profit90={profit90}, profit80={profit80}")
    print(f"  profit70={profit70}, profit60={profit60}, profit50={profit50}, profit40={profit40}")
    print(f"{'='*60}")
    
    level = 0
    title = ''
    suggestion = ''
    
    # 下跌等级5：极端下跌
    # 空单盈利≥100%的数量≥1
    if profit100 >= 1:
        level = 5
        title = '下跌强度5级 - 极端下跌'
        suggestion = '多单买入点在100%以上'
    # 下跌等级4：超高强度下跌
    # 空单盈利≥100%=0 且 ≥90%≥1 且 ≥80%≥1
    elif profit100 == 0 and profit90 >= 1 and profit80 >= 1:
        level = 4
        title = '下跌强度4级 - 超高强度下跌'
        suggestion = '多单买入点在90%'
    # 下跌等级3：高强度下跌
    # 空单盈利≥100%=0 且 ≥90%=0 且 ≥80%=0 且 ≥70%≥1 且 ≥60%≥2
    elif profit100 == 0 and profit90 == 0 and profit80 == 0 and profit70 >= 1 and profit60 >= 2:
        level = 3
        title = '下跌强度3级 - 高强度下跌'
        suggestion = '多单买入点在70-80%'
    # 下跌等级2：中等强度下跌
    # 空单盈利≥100%=0 且 ≥90%=0 且 ≥80%=0 且 ≥70%=0 且 ≥60%≥2
    elif profit100 == 0 and profit90 == 0 and profit80 == 0 and profit70 == 0 and profit60 >= 2:
        level = 2
        title = '下跌强度2级 - 中等强度下跌'
        suggestion = '多单买入点在60%'
    # 下跌等级1：轻微下跌
    # 空单盈利≥100%=0 且 ≥90%=0 且 ≥80%=0 且 ≥70%=0 且 ≥60%=0 且 ≥50%=0 且 ≥40%≥3
    elif profit100 == 0 and profit90 == 0 and profit80 == 0 and profit70 == 0 and profit60 == 0 and profit50 == 0 and profit40 >= 3:
        level = 1
        title = '下跌强度1级 - 轻微下跌'
        suggestion = '多单买入点在50%'
    # 未达到任何级别
    else:
        level = 0
        title = '市场正常'
        suggestion = '暂无明显下跌信号'
    
    print(f"\n判断结果:")
    print(f"  等级: {level}")
    print(f"  标题: {title}")
    print(f"  建议: {suggestion}")
    
    return level, title, suggestion

# 测试用例
print("="*60)
print("下跌强度等级判断逻辑测试 V2")
print("="*60)

# 测试用例1：当前真实数据（应该显示市场正常）
print("\n【测试用例1】当前真实数据")
test_decline_strength(
    profit100=2, profit90=3, profit80=5, profit70=7, 
    profit60=7, profit50=7, profit40=9
)

# 测试用例2：等级1（轻微下跌）
print("\n【测试用例2】等级1 - 轻微下跌")
test_decline_strength(
    profit100=0, profit90=0, profit80=0, profit70=0, 
    profit60=0, profit50=0, profit40=3
)

# 测试用例3：等级2（中等强度下跌）
print("\n【测试用例3】等级2 - 中等强度下跌")
test_decline_strength(
    profit100=0, profit90=0, profit80=0, profit70=0, 
    profit60=2, profit50=5, profit40=7
)

# 测试用例4：等级3（高强度下跌）
print("\n【测试用例4】等级3 - 高强度下跌")
test_decline_strength(
    profit100=0, profit90=0, profit80=0, profit70=1, 
    profit60=2, profit50=5, profit40=8
)

# 测试用例5：等级4（超高强度下跌）
print("\n【测试用例5】等级4 - 超高强度下跌")
test_decline_strength(
    profit100=0, profit90=1, profit80=1, profit70=3, 
    profit60=5, profit50=7, profit40=10
)

# 测试用例6：等级5（极端下跌）
print("\n【测试用例6】等级5 - 极端下跌")
test_decline_strength(
    profit100=1, profit90=3, profit80=5, profit70=7, 
    profit60=9, profit50=11, profit40=13
)

# 测试用例7：边界测试 - profit100=2（应该是等级5）
print("\n【测试用例7】边界测试 - profit100=2")
test_decline_strength(
    profit100=2, profit90=0, profit80=0, profit70=0, 
    profit60=0, profit50=0, profit40=0
)

print("\n" + "="*60)
print("测试完成！")
print("="*60)

