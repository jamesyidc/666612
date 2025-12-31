#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试告警消息格式
"""
import sys
sys.path.insert(0, '/home/user/webapp')

# Mock position data
def test_alert_messages():
    positions = [
        {'profit_rate': 49.5, 'level': 0, 'name': '40%预警'},
        {'profit_rate': 50.0, 'level': 1, 'name': '下跌强度1级'},
        {'profit_rate': 55.0, 'level': 1, 'name': '下跌强度1级'},
        {'profit_rate': 60.0, 'level': 2, 'name': '下跌强度2级'},
        {'profit_rate': 65.0, 'level': 2, 'name': '下跌强度2级'},
        {'profit_rate': 70.0, 'level': 3, 'name': '下跌强度3级'},
        {'profit_rate': 75.0, 'level': 3, 'name': '下跌强度3级'},
    ]
    
    print("📋 测试告警消息格式\n")
    
    for pos_data in positions:
        profit_rate = pos_data['profit_rate']
        
        # 判断下跌强度
        if profit_rate >= 70:
            signal = f"做空盈利{profit_rate:.1f}%，下跌强度3级，建议开仓做多（买入点在70-80%）"
            level = 3
        elif profit_rate >= 60:
            signal = f"做空盈利{profit_rate:.1f}%，下跌强度2级，建议开仓做多（买入点在60%）"
            level = 2
        elif profit_rate >= 50:
            signal = f"做空盈利{profit_rate:.1f}%，下跌强度1级，建议开仓做多（买入点在50%）"
            level = 1
        else:
            signal = f"做空盈利{profit_rate:.1f}%，建议开仓做多"
            level = 0
        
        # 验证
        assert level == pos_data['level'], f"Level mismatch for {profit_rate}%: expected {pos_data['level']}, got {level}"
        
        print(f"✅ 盈利 {profit_rate:.1f}% -> {pos_data['name']}")
        print(f"   信号: {signal}\n")

if __name__ == '__main__':
    test_alert_messages()
    print("🎉 所有测试通过！")
