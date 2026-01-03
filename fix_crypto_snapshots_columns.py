#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复crypto_snapshots表结构
添加缺失的列以匹配gdrive_final_detector.py的数据插入需求
"""

import sqlite3

DB_PATH = 'databases/crypto_data.db'

def fix_table_structure():
    """修复表结构，添加缺失的列"""
    try:
        print(f"📊 连接数据库: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取当前表结构
        cursor.execute("PRAGMA table_info(crypto_snapshots)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"✅ 当前字段: {existing_columns}")
        
        # 需要添加的字段
        columns_to_add = [
            ('rush_up', 'INTEGER DEFAULT 0'),
            ('rush_down', 'INTEGER DEFAULT 0'),
            ('diff', 'INTEGER DEFAULT 0'),
            ('count', 'INTEGER DEFAULT 0'),
            ('status', 'TEXT DEFAULT ""'),
            ('count_score_display', 'TEXT DEFAULT ""'),
            ('count_score_type', 'TEXT DEFAULT ""')
        ]
        
        # 逐个添加缺失的列
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                print(f"➕ 添加字段: {col_name} {col_type}")
                cursor.execute(f"ALTER TABLE crypto_snapshots ADD COLUMN {col_name} {col_type}")
            else:
                print(f"✓  字段已存在: {col_name}")
        
        conn.commit()
        
        # 再次确认表结构
        cursor.execute("PRAGMA table_info(crypto_snapshots)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n✅ 修复后的表结构:")
        for col in final_columns:
            print(f"   - {col}")
        
        conn.close()
        print(f"\n✅ 表结构修复完成！")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    fix_table_structure()
