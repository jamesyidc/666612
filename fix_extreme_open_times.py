#!/usr/bin/env python3
"""
修复盈利极值记录的开仓时间
从position_opens表中获取正确的开仓时间，更新position_profit_extremes表
"""

import sqlite3

def fix_open_times():
    conn = sqlite3.connect('/home/user/webapp/trading_decision.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有极值记录
    cursor.execute('SELECT DISTINCT inst_id, pos_side, open_time FROM position_profit_extremes')
    extremes = cursor.fetchall()
    
    fixed_count = 0
    
    for extreme in extremes:
        inst_id = extreme['inst_id']
        pos_side = extreme['pos_side']
        old_open_time = extreme['open_time']
        
        # 从position_opens获取正确的开仓时间
        cursor.execute('''
            SELECT created_at, updated_time, timestamp
            FROM position_opens
            WHERE inst_id = ? AND pos_side = ? AND open_size != 0
            ORDER BY created_at DESC
            LIMIT 1
        ''', (inst_id, pos_side))
        
        pos_row = cursor.fetchone()
        if pos_row:
            # 使用created_at或timestamp作为开仓时间
            correct_open_time = pos_row['created_at'] or pos_row['timestamp']
            
            if correct_open_time and correct_open_time != old_open_time:
                # 更新开仓时间
                cursor.execute('''
                    UPDATE position_profit_extremes
                    SET open_time = ?
                    WHERE inst_id = ? AND pos_side = ? AND open_time = ?
                ''', (correct_open_time, inst_id, pos_side, old_open_time))
                
                print(f"✅ {inst_id} {pos_side}: {old_open_time} → {correct_open_time}")
                fixed_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ 修复完成！共更新 {fixed_count} 条记录")

if __name__ == '__main__':
    print("开始修复开仓时间...\n")
    fix_open_times()
