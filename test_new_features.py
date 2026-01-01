#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新功能：
1. 平仓后保证金验证（0.6-1.1U范围）
2. 维护计数同步更新
"""

import json
from datetime import datetime
import pytz
from maintenance_trade_executor import MaintenanceTradeExecutor
from okex_trader import OKExTrader

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def test_margin_verification():
    """测试保证金验证功能"""
    print("\n" + "=" * 80)
    print("🧪 测试1：保证金验证功能（模拟模式）")
    print("=" * 80)
    
    # 模拟一个保证金超出范围的持仓
    test_position = {
        'inst_id': 'TEST-USDT-SWAP',
        'pos_side': 'long',
        'pos_size': 100.0,
        'margin': 10.5,  # 超出1.1U的上限
        'mark_price': 1.0,
        'lever': 10
    }
    
    executor = MaintenanceTradeExecutor(dry_run=True)
    
    print(f"\n📊 测试场景：持仓保证金 {test_position['margin']} USDT（超出0.6-1.1U范围）")
    
    # 测试验证函数
    result = executor._verify_and_adjust_margin(test_position)
    
    print(f"\n✅ 测试结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('adjusted'):
        print("\n✅ 保证金调整逻辑已触发！")
    else:
        print("\n⚠️  保证金未调整（可能因为模拟模式或无法获取实时持仓）")

def test_maintenance_count_update():
    """测试维护计数更新"""
    print("\n" + "=" * 80)
    print("🧪 测试2：维护计数更新")
    print("=" * 80)
    
    from anchor_maintenance_realtime_daemon import update_maintenance_count
    
    test_inst_id = "TEST-USDT-SWAP"
    test_pos_side = "long"
    
    print(f"\n📊 测试币种: {test_inst_id} {test_pos_side}")
    
    # 更新维护计数
    update_maintenance_count(test_inst_id, test_pos_side)
    
    # 读取并验证记录
    try:
        with open('/home/user/webapp/anchor_maintenance_records.json', 'r') as f:
            records = json.load(f)
        
        record_key = f"{test_inst_id}_{test_pos_side}"
        if record_key in records:
            record = records[record_key]
            print(f"\n✅ 守护进程记录文件已更新:")
            print(f"   今日维护: {record['today_count']}次")
            print(f"   总维护: {record['total_count']}次")
            print(f"   最后维护: {record['last_maintenance']}")
    except Exception as e:
        print(f"\n❌ 读取守护进程记录失败: {e}")
    
    # 验证Flask记录文件
    try:
        with open('/home/user/webapp/maintenance_orders.json', 'r') as f:
            flask_records = json.load(f)
        
        flask_key = f"{test_inst_id}_{test_pos_side}"
        if flask_key in flask_records:
            count = len(flask_records[flask_key])
            print(f"\n✅ Flask记录文件已更新:")
            print(f"   维护记录数: {count}条")
            if count > 0:
                latest = flask_records[flask_key][-1]
                print(f"   最新记录: {latest['timestamp']}")
    except Exception as e:
        print(f"\n❌ 读取Flask记录失败: {e}")

def test_real_position_check():
    """检查实际持仓状态"""
    print("\n" + "=" * 80)
    print("🧪 测试3：检查实际持仓状态")
    print("=" * 80)
    
    trader = OKExTrader(dry_run=False)
    positions = trader.get_positions()
    
    print(f"\n📊 当前持仓数: {len(positions)}个")
    
    for pos in positions:
        inst_id = pos.get('instId', '')
        pos_side = pos.get('posSide', '')
        pos_size = float(pos.get('pos', 0))
        mark_price = float(pos.get('markPx', 0))
        leverage = float(pos.get('lever', 10))
        
        if pos_size > 0:
            margin = (pos_size * mark_price) / leverage
            
            # 检查保证金是否在范围内
            in_range = 0.6 <= margin <= 1.1
            status = "✅ 范围内" if in_range else "⚠️ 超出范围"
            
            print(f"\n{inst_id} {pos_side}:")
            print(f"   持仓: {pos_size} 张")
            print(f"   保证金: {margin:.4f} USDT {status}")
            
            if not in_range:
                print(f"   ⚠️  需要调整保证金到0.6-1.1U范围！")

if __name__ == '__main__':
    print("\n🚀 开始测试新功能...")
    print(f"⏰ 测试时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试1：保证金验证
    test_margin_verification()
    
    # 测试2：维护计数更新
    test_maintenance_count_update()
    
    # 测试3：实际持仓检查
    test_real_position_check()
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)
