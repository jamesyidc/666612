#!/usr/bin/env python3
"""
测试爆仓记录功能 - 添加示例数据
"""

import sys
sys.path.append('/home/user/webapp')
from sub_account_liquidation_tracker import record_liquidation, print_summary
import random
from datetime import datetime, timedelta
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 测试数据
TEST_ACCOUNTS = ["Wu666666"]
TEST_COINS = [
    "BTC-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP", 
    "BNB-USDT-SWAP", "XRP-USDT-SWAP", "ADA-USDT-SWAP",
    "DOT-USDT-SWAP", "DOGE-USDT-SWAP", "AVAX-USDT-SWAP",
    "MATIC-USDT-SWAP"
]

def add_test_liquidations(count=10):
    """添加测试爆仓记录"""
    print(f"正在添加{count}条测试爆仓记录...")
    
    for i in range(count):
        account = random.choice(TEST_ACCOUNTS)
        inst_id = random.choice(TEST_COINS)
        pos_side = random.choice(['long', 'short'])
        
        # 随机生成价格和数量
        avg_price = random.uniform(10, 50000)
        liquidation_price = avg_price * random.uniform(0.8, 1.2)
        size = random.uniform(1, 100)
        margin = random.uniform(5, 50)
        loss_amount = random.uniform(5, 50)
        
        # 随机时间（最近7天内）
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        
        result = record_liquidation(
            account_name=account,
            inst_id=inst_id,
            pos_side=pos_side,
            liquidation_price=liquidation_price,
            avg_price=avg_price,
            size=size,
            margin=margin,
            loss_amount=loss_amount,
            liquidation_type="自动强平",
            remarks=f"测试数据 #{i+1}"
        )
        
        if result:
            print(f"  ✅ 已添加: {inst_id} - {pos_side} - ${loss_amount:.2f}")
        else:
            print(f"  ❌ 添加失败: {inst_id}")
    
    print(f"\n✅ 测试数据添加完成！")
    
    # 显示统计
    print("\n" + "="*60)
    print_summary()

if __name__ == "__main__":
    # 添加10条测试数据
    add_test_liquidations(10)
