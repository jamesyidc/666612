#!/usr/bin/env python3
"""
修复escape_signal_stats表中的错误数据
问题：由于前端时区计算错误，导致2h信号数不准确
解决：根据support_resistance_snapshots重新计算正确的2h信号数
"""

import sqlite3
from datetime import datetime, timedelta
import pytz

# 数据库路径
CRYPTO_DB = 'databases/crypto_data.db'
SR_DB = 'support_resistance.db'

# 北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')

def calculate_correct_2h_signals(stat_time_str):
    """
    根据给定时间，计算正确的2小时逃顶信号数
    
    Args:
        stat_time_str: 统计时间字符串，格式：'2026-01-03 20:46:11'
    
    Returns:
        int: 2小时内的逃顶信号数
    """
    # 解析统计时间（北京时间）
    stat_time = datetime.strptime(stat_time_str, '%Y-%m-%d %H:%M:%S')
    
    # 计算2小时前的时间
    two_hours_ago = stat_time - timedelta(hours=2)
    two_hours_ago_str = two_hours_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    # 查询support_resistance_snapshots中2小时内scenario_4_count > 0的记录数
    conn = sqlite3.connect(SR_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*)
        FROM support_resistance_snapshots
        WHERE scenario_4_count > 0
        AND snapshot_time >= ?
        AND snapshot_time <= ?
    """, (two_hours_ago_str, stat_time_str))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count

def fix_escape_signal_stats():
    """
    修复escape_signal_stats表中的错误数据
    """
    print("=" * 80)
    print("开始修复escape_signal_stats表中的错误数据")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(CRYPTO_DB)
    cursor = conn.cursor()
    
    # 1. 查询所有需要修复的记录（2h >= 100）
    cursor.execute("""
        SELECT id, stat_time, signal_24h_count, signal_2h_count
        FROM escape_signal_stats
        WHERE signal_2h_count >= 100
        ORDER BY stat_time
    """)
    
    error_records = cursor.fetchall()
    total_count = len(error_records)
    
    if total_count == 0:
        print("✅ 未发现需要修复的错误记录")
        conn.close()
        return
    
    print(f"📊 发现 {total_count} 条错误记录，开始修复...")
    print()
    
    # 2. 逐条修复
    fixed_count = 0
    skipped_count = 0
    
    for i, record in enumerate(error_records, 1):
        record_id, stat_time, signal_24h, old_signal_2h = record
        
        try:
            # 计算正确的2h信号数
            new_signal_2h = calculate_correct_2h_signals(stat_time)
            
            # 更新数据库
            cursor.execute("""
                UPDATE escape_signal_stats
                SET signal_2h_count = ?
                WHERE id = ?
            """, (new_signal_2h, record_id))
            
            fixed_count += 1
            
            if i <= 10 or i % 50 == 0:
                print(f"  [{i}/{total_count}] {stat_time} | "
                      f"旧: {old_signal_2h:3d} → 新: {new_signal_2h:3d}")
        
        except Exception as e:
            print(f"  ❌ [{i}/{total_count}] {stat_time} 修复失败: {e}")
            skipped_count += 1
    
    # 3. 提交更改
    conn.commit()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ 修复完成！")
    print("=" * 80)
    print(f"  总记录数: {total_count}")
    print(f"  成功修复: {fixed_count}")
    print(f"  跳过: {skipped_count}")
    print()

def verify_fix():
    """
    验证修复结果
    """
    print("=" * 80)
    print("验证修复结果")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(CRYPTO_DB)
    cursor = conn.cursor()
    
    # 检查是否还有错误记录
    cursor.execute("""
        SELECT COUNT(*)
        FROM escape_signal_stats
        WHERE signal_2h_count >= 100
    """)
    
    remaining_errors = cursor.fetchone()[0]
    
    if remaining_errors > 0:
        print(f"⚠️ 仍有 {remaining_errors} 条错误记录")
    else:
        print("✅ 所有错误记录已修复")
    
    # 查看最近的数据
    cursor.execute("""
        SELECT stat_time, signal_24h_count, signal_2h_count
        FROM escape_signal_stats
        ORDER BY stat_time DESC
        LIMIT 10
    """)
    
    print()
    print("最近10条记录:")
    print("-" * 80)
    for row in cursor.fetchall():
        stat_time, signal_24h, signal_2h = row
        print(f"{stat_time} | 24h: {signal_24h:4d} | 2h: {signal_2h:3d}")
    
    # 统计2h信号数的分布
    cursor.execute("""
        SELECT 
            CASE 
                WHEN signal_2h_count = 0 THEN '0'
                WHEN signal_2h_count <= 5 THEN '1-5'
                WHEN signal_2h_count <= 10 THEN '6-10'
                WHEN signal_2h_count <= 20 THEN '11-20'
                WHEN signal_2h_count <= 50 THEN '21-50'
                ELSE '50+'
            END as range,
            COUNT(*) as count
        FROM escape_signal_stats
        GROUP BY range
        ORDER BY 
            CASE range
                WHEN '0' THEN 1
                WHEN '1-5' THEN 2
                WHEN '6-10' THEN 3
                WHEN '11-20' THEN 4
                WHEN '21-50' THEN 5
                ELSE 6
            END
    """)
    
    print()
    print("2h信号数分布:")
    print("-" * 80)
    for row in cursor.fetchall():
        range_name, count = row
        print(f"  {range_name:>8} : {count:4d} 条")
    
    conn.close()
    print()

if __name__ == '__main__':
    try:
        # 1. 修复错误数据
        fix_escape_signal_stats()
        
        # 2. 验证修复结果
        verify_fix()
        
        print("🎉 任务完成！")
        
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
