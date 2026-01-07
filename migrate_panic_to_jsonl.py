#!/usr/bin/env python3
"""
Migrate Panic Data from SQLite to JSONL
将恐慌清洗指数数据从数据库迁移到JSONL
"""

import sqlite3
import json
from datetime import datetime
from panic_jsonl_storage import panic_storage
import pytz

def migrate_panic_data():
    """迁移crypto_snapshots表中的恐慌数据到JSONL"""
    
    print("🚀 开始迁移恐慌数据...")
    print("=" * 60)
    
    # 连接数据库
    db_path = "databases/crypto_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查询所有快照数据
        cursor.execute('''
            SELECT 
                id, snapshot_date, snapshot_time, inst_id, last_price,
                high_24h, low_24h, vol_24h, created_at, rush_up, rush_down,
                diff, count, status, count_score_display, count_score_type
            FROM crypto_snapshots
            ORDER BY snapshot_time ASC
        ''')
        
        rows = cursor.fetchall()
        total = len(rows)
        
        print(f"📊 数据库中共有 {total} 条记录")
        print()
        
        if total == 0:
            print("⚠️  数据库中没有数据，迁移完成")
            return
        
        # 逐条迁移
        success_count = 0
        error_count = 0
        
        for idx, row in enumerate(rows, 1):
            try:
                # 构建JSONL记录
                snapshot = {
                    'id': row[0],
                    'snapshot_date': row[1],
                    'snapshot_time': row[2],
                    'inst_id': row[3],
                    'last_price': row[4],
                    'high_24h': row[5],
                    'low_24h': row[6],
                    'vol_24h': row[7],
                    'created_at': row[8],
                    'rush_up': row[9],
                    'rush_down': row[10],
                    'diff': row[11],
                    'count': row[12],
                    'status': row[13],
                    'count_score_display': row[14],
                    'count_score_type': row[15]
                }
                
                # 保存到JSONL
                if panic_storage.save_snapshot(snapshot):
                    success_count += 1
                else:
                    error_count += 1
                
                # 进度显示
                if idx % 50 == 0 or idx == total:
                    print(f"进度: {idx}/{total} ({success_count} 成功, {error_count} 失败)")
            
            except Exception as e:
                error_count += 1
                print(f"❌ 迁移记录 {idx} 失败: {e}")
        
        print()
        print("=" * 60)
        print("✅ 迁移完成!")
        print(f"   总计: {total} 条")
        print(f"   成功: {success_count} 条")
        print(f"   失败: {error_count} 条")
        print()
        
        # 显示存储统计
        stats = panic_storage.get_stats()
        print("📁 JSONL 存储统计:")
        print(f"   文件数: {stats.get('total_files', 0)}")
        print(f"   记录数: {stats.get('total_records', 0)}")
        print(f"   大小: {stats.get('total_size_mb', 0)} MB")
        date_range = stats.get('date_range', {})
        if date_range.get('earliest'):
            print(f"   日期范围: {date_range['earliest']} ~ {date_range['latest']}")
        print()
        
        # 显示最新数据样本
        latest = panic_storage.read_latest(limit=3)
        if latest:
            print("📝 最新3条记录样本:")
            for record in latest:
                print(f"   {record.get('snapshot_time')} - "
                      f"rush_up:{record.get('rush_up')} rush_down:{record.get('rush_down')} "
                      f"diff:{record.get('diff')} status:{record.get('status')}")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_panic_data()
