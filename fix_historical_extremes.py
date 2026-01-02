#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复历史极值记录 - 清理重复记录并插入初始历史记录
"""

import sqlite3
import requests
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DECISION_DB = '/home/user/webapp/trading_decision.db'
ANCHOR_DB = '/home/user/webapp/anchor_system.db'
FLASK_API = 'http://localhost:5000/api/anchor-system/current-positions?trade_mode=real'

def get_beijing_time():
    """获取北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

def get_current_positions():
    """从Flask API获取当前实盘持仓"""
    try:
        response = requests.get(FLASK_API, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('positions', [])
        
        print(f"⚠️  Flask API返回错误: {response.text[:200]}")
        return []
        
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return []

def fix_extremes_for_position(inst_id, pos_side, pos_info):
    """修复单个持仓的极值记录"""
    print(f"\n{'='*70}")
    print(f"修复: {inst_id} {pos_side}")
    print(f"{'='*70}")
    
    # 连接两个数据库
    decision_conn = sqlite3.connect(DECISION_DB)
    decision_conn.row_factory = sqlite3.Row
    decision_cursor = decision_conn.cursor()
    
    anchor_conn = sqlite3.connect(ANCHOR_DB)
    anchor_cursor = anchor_conn.cursor()
    
    # 1. 查询该持仓的所有极值记录
    decision_cursor.execute("""
        SELECT open_time, max_profit_rate, max_loss_rate, current_profit_rate, updated_at
        FROM position_profit_extremes 
        WHERE inst_id = ? AND pos_side = ?
        ORDER BY updated_at DESC
    """, (inst_id, pos_side))
    
    rows = decision_cursor.fetchall()
    
    if not rows:
        print(f"⚠️  没有找到极值记录")
        decision_conn.close()
        anchor_conn.close()
        return False
    
    print(f"📊 发现 {len(rows)} 条极值记录")
    
    # 2. 找到最高盈利率和最大亏损率
    max_profit = max(row['max_profit_rate'] for row in rows)
    max_loss = min(row['max_loss_rate'] for row in rows)
    latest_time = rows[0]['updated_at']
    
    # 从position_opens获取真实的开仓时间
    decision_cursor.execute("""
        SELECT created_at FROM position_opens 
        WHERE inst_id = ? AND pos_side = ? AND open_size != 0
        ORDER BY created_at DESC
        LIMIT 1
    """, (inst_id, pos_side))
    
    open_row = decision_cursor.fetchone()
    if open_row:
        open_time = open_row['created_at']
    else:
        # 使用第一条极值记录的时间
        open_time = rows[-1]['open_time']
    
    print(f"开仓时间: {open_time}")
    print(f"最高盈利率: {max_profit:.2f}%")
    print(f"最大亏损率: {max_loss:.2f}%")
    print(f"当前盈亏率: {pos_info['profit_rate']:.2f}%")
    
    # 3. 删除所有旧记录
    decision_cursor.execute("""
        DELETE FROM position_profit_extremes 
        WHERE inst_id = ? AND pos_side = ?
    """, (inst_id, pos_side))
    
    deleted_count = decision_cursor.rowcount
    print(f"✅ 已删除 {deleted_count} 条旧极值记录")
    
    # 4. 插入一条新的正确记录
    now = get_beijing_time()
    
    decision_cursor.execute("""
        INSERT INTO position_profit_extremes 
        (inst_id, pos_side, open_time, max_profit_rate, max_profit_time, 
         max_loss_rate, max_loss_time, current_profit_rate, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inst_id, 
        pos_side, 
        open_time, 
        max_profit if max_profit > 0 else 0,
        now if max_profit > 0 else None,
        max_loss if max_loss < 0 else 0,
        now if max_loss < 0 else None,
        pos_info['profit_rate'], 
        now
    ))
    
    print(f"✅ 已创建新的极值记录")
    
    decision_conn.commit()
    
    # 5. 检查并插入历史极值记录
    # 插入最高盈利记录
    if max_profit > 0:
        anchor_cursor.execute("""
            DELETE FROM anchor_real_profit_records 
            WHERE inst_id = ? AND pos_side = ? AND record_type = 'max_profit'
        """, (inst_id, pos_side))
        
        anchor_cursor.execute("""
            INSERT INTO anchor_real_profit_records 
            (inst_id, pos_side, record_type, profit_rate, timestamp, pos_size, avg_price, mark_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inst_id, 
            pos_side, 
            'max_profit', 
            max_profit, 
            now,
            pos_info['pos_size'],
            pos_info['avg_price'],
            pos_info['mark_price']
        ))
        
        print(f"✅ 已插入历史最高盈利记录: {max_profit:.2f}%")
    
    # 插入最大亏损记录
    if max_loss < 0:
        anchor_cursor.execute("""
            DELETE FROM anchor_real_profit_records 
            WHERE inst_id = ? AND pos_side = ? AND record_type = 'max_loss'
        """, (inst_id, pos_side))
        
        anchor_cursor.execute("""
            INSERT INTO anchor_real_profit_records 
            (inst_id, pos_side, record_type, profit_rate, timestamp, pos_size, avg_price, mark_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inst_id, 
            pos_side, 
            'max_loss', 
            max_loss, 
            now,
            pos_info['pos_size'],
            pos_info['avg_price'],
            pos_info['mark_price']
        ))
        
        print(f"✅ 已插入历史最大亏损记录: {max_loss:.2f}%")
    
    anchor_conn.commit()
    
    # 6. 验证结果
    decision_cursor.execute("""
        SELECT COUNT(*) FROM position_profit_extremes 
        WHERE inst_id = ? AND pos_side = ?
    """, (inst_id, pos_side))
    
    new_count = decision_cursor.fetchone()[0]
    print(f"✅ 极值记录数: {new_count}")
    
    anchor_cursor.execute("""
        SELECT COUNT(*) FROM anchor_real_profit_records 
        WHERE inst_id = ? AND pos_side = ?
    """, (inst_id, pos_side))
    
    history_count = anchor_cursor.fetchone()[0]
    print(f"✅ 历史记录数: {history_count}")
    
    decision_conn.close()
    anchor_conn.close()
    
    return True

def main():
    """主函数"""
    print("="*70)
    print("🔧 修复历史极值记录")
    print("="*70)
    print(f"当前时间: {get_beijing_time()}")
    print("")
    
    # 获取当前持仓
    positions = get_current_positions()
    
    if not positions:
        print("⚠️  没有获取到持仓数据")
        return
    
    print(f"📊 发现 {len(positions)} 个持仓\n")
    
    # 需要修复的持仓（TAO和LINK做空）
    target_positions = [
        ('TAO-USDT-SWAP', 'short'),
        ('LINK-USDT-SWAP', 'short'),
        ('HBAR-USDT-SWAP', 'short'),
        ('CFX-USDT-SWAP', 'short'),
        ('BNB-USDT-SWAP', 'short')
    ]
    
    fixed_count = 0
    
    for inst_id, pos_side in target_positions:
        # 查找对应的持仓信息
        pos_info = None
        for pos in positions:
            if pos['inst_id'] == inst_id and pos['pos_side'] == pos_side:
                pos_info = pos
                break
        
        if not pos_info:
            print(f"⚠️  {inst_id} {pos_side} 没有找到持仓")
            continue
        
        if fix_extremes_for_position(inst_id, pos_side, pos_info):
            fixed_count += 1
    
    print("\n" + "="*70)
    print(f"✅ 修复完成！共修复 {fixed_count} 个持仓的历史极值记录")
    print("="*70)
    print("\n💡 提示：")
    print("  - 现在可以在锚点系统页面看到历史极值记录")
    print("  - 极值追踪服务将继续监控并更新")
    print("  - 可以刷新页面查看结果")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
