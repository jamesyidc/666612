#!/usr/bin/env python3
"""
子账号爆仓记录与统计系统
记录子账号的爆仓情况，包括时间、币种、方向、金额等信息
"""

import sqlite3
import requests
from datetime import datetime
import pytz
import json
import time

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 数据库路径
DB_PATH = 'databases/crypto_data.db'

# OKEx API配置
OKEX_API_KEY = "3e24bef8-e68c-44d8-82da-21e1a79ec2d1"
OKEX_SECRET_KEY = "9A5753E20D3D04B4F67E84B6073EC3DB"
OKEX_PASSPHRASE = "QAZwsxedc741852#"

# 子账号配置
SUB_ACCOUNTS = {
    "Wu666666": "吴六"
}

def init_database():
    """初始化数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建爆仓记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sub_account_liquidations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_time TEXT NOT NULL,
            account_name TEXT NOT NULL,
            account_display_name TEXT,
            inst_id TEXT NOT NULL,
            pos_side TEXT NOT NULL,
            liquidation_price REAL,
            avg_price REAL,
            size REAL,
            margin REAL,
            loss_amount REAL,
            liquidation_type TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建爆仓统计表（按账号）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sub_account_liquidation_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL UNIQUE,
            account_display_name TEXT,
            total_liquidations INTEGER DEFAULT 0,
            total_loss_amount REAL DEFAULT 0,
            long_liquidations INTEGER DEFAULT 0,
            short_liquidations INTEGER DEFAULT 0,
            last_liquidation_time TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建爆仓统计表（按币种）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_liquidation_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inst_id TEXT NOT NULL UNIQUE,
            total_liquidations INTEGER DEFAULT 0,
            total_loss_amount REAL DEFAULT 0,
            long_liquidations INTEGER DEFAULT 0,
            short_liquidations INTEGER DEFAULT 0,
            last_liquidation_time TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 数据库表初始化完成")

def record_liquidation(account_name, inst_id, pos_side, liquidation_price, 
                       avg_price, size, margin, loss_amount, liquidation_type="自动强平", remarks=""):
    """记录一次爆仓事件"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        account_display_name = SUB_ACCOUNTS.get(account_name, account_name)
        
        # 插入爆仓记录
        cursor.execute("""
            INSERT INTO sub_account_liquidations 
            (record_time, account_name, account_display_name, inst_id, pos_side, 
             liquidation_price, avg_price, size, margin, loss_amount, liquidation_type, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, account_name, account_display_name, inst_id, pos_side,
              liquidation_price, avg_price, size, margin, loss_amount, liquidation_type, remarks))
        
        # 更新账号统计
        cursor.execute("""
            INSERT INTO sub_account_liquidation_stats 
            (account_name, account_display_name, total_liquidations, total_loss_amount, 
             long_liquidations, short_liquidations, last_liquidation_time, updated_at)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?)
            ON CONFLICT(account_name) DO UPDATE SET
                total_liquidations = total_liquidations + 1,
                total_loss_amount = total_loss_amount + ?,
                long_liquidations = long_liquidations + ?,
                short_liquidations = short_liquidations + ?,
                last_liquidation_time = ?,
                updated_at = ?
        """, (account_name, account_display_name, loss_amount,
              1 if pos_side == 'long' else 0,
              1 if pos_side == 'short' else 0,
              now, now,
              loss_amount,
              1 if pos_side == 'long' else 0,
              1 if pos_side == 'short' else 0,
              now, now))
        
        # 更新币种统计
        cursor.execute("""
            INSERT INTO coin_liquidation_stats 
            (inst_id, total_liquidations, total_loss_amount, 
             long_liquidations, short_liquidations, last_liquidation_time, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, ?)
            ON CONFLICT(inst_id) DO UPDATE SET
                total_liquidations = total_liquidations + 1,
                total_loss_amount = total_loss_amount + ?,
                long_liquidations = long_liquidations + ?,
                short_liquidations = short_liquidations + ?,
                last_liquidation_time = ?,
                updated_at = ?
        """, (inst_id, loss_amount,
              1 if pos_side == 'long' else 0,
              1 if pos_side == 'short' else 0,
              now, now,
              loss_amount,
              1 if pos_side == 'long' else 0,
              1 if pos_side == 'short' else 0,
              now, now))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 爆仓记录已保存: {account_display_name} - {inst_id} - {pos_side} - 损失: ${loss_amount:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ 记录爆仓失败: {e}")
        return False

def get_liquidation_records(account_name=None, inst_id=None, limit=100):
    """获取爆仓记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = """
            SELECT record_time, account_name, account_display_name, inst_id, pos_side,
                   liquidation_price, avg_price, size, margin, loss_amount, 
                   liquidation_type, remarks
            FROM sub_account_liquidations
            WHERE 1=1
        """
        params = []
        
        if account_name:
            query += " AND account_name = ?"
            params.append(account_name)
        
        if inst_id:
            query += " AND inst_id = ?"
            params.append(inst_id)
        
        query += " ORDER BY record_time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                'record_time': row[0],
                'account_name': row[1],
                'account_display_name': row[2],
                'inst_id': row[3],
                'pos_side': row[4],
                'liquidation_price': row[5],
                'avg_price': row[6],
                'size': row[7],
                'margin': row[8],
                'loss_amount': row[9],
                'liquidation_type': row[10],
                'remarks': row[11]
            })
        
        return records
        
    except Exception as e:
        print(f"❌ 获取爆仓记录失败: {e}")
        return []

def get_account_stats(account_name=None):
    """获取账号爆仓统计"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if account_name:
            cursor.execute("""
                SELECT account_name, account_display_name, total_liquidations, 
                       total_loss_amount, long_liquidations, short_liquidations,
                       last_liquidation_time, updated_at
                FROM sub_account_liquidation_stats
                WHERE account_name = ?
            """, (account_name,))
        else:
            cursor.execute("""
                SELECT account_name, account_display_name, total_liquidations, 
                       total_loss_amount, long_liquidations, short_liquidations,
                       last_liquidation_time, updated_at
                FROM sub_account_liquidation_stats
                ORDER BY total_liquidations DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = []
        for row in rows:
            stats.append({
                'account_name': row[0],
                'account_display_name': row[1],
                'total_liquidations': row[2],
                'total_loss_amount': row[3],
                'long_liquidations': row[4],
                'short_liquidations': row[5],
                'last_liquidation_time': row[6],
                'updated_at': row[7]
            })
        
        return stats
        
    except Exception as e:
        print(f"❌ 获取账号统计失败: {e}")
        return []

def get_coin_stats(inst_id=None):
    """获取币种爆仓统计"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if inst_id:
            cursor.execute("""
                SELECT inst_id, total_liquidations, total_loss_amount,
                       long_liquidations, short_liquidations,
                       last_liquidation_time, updated_at
                FROM coin_liquidation_stats
                WHERE inst_id = ?
            """, (inst_id,))
        else:
            cursor.execute("""
                SELECT inst_id, total_liquidations, total_loss_amount,
                       long_liquidations, short_liquidations,
                       last_liquidation_time, updated_at
                FROM coin_liquidation_stats
                ORDER BY total_liquidations DESC
                LIMIT 50
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = []
        for row in rows:
            stats.append({
                'inst_id': row[0],
                'total_liquidations': row[1],
                'total_loss_amount': row[2],
                'long_liquidations': row[3],
                'short_liquidations': row[4],
                'last_liquidation_time': row[5],
                'updated_at': row[6]
            })
        
        return stats
        
    except Exception as e:
        print(f"❌ 获取币种统计失败: {e}")
        return []

def get_summary_stats():
    """获取总体统计"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 总爆仓次数和总损失
        cursor.execute("""
            SELECT COUNT(*), SUM(loss_amount)
            FROM sub_account_liquidations
        """)
        total_liquidations, total_loss = cursor.fetchone()
        
        # 多空统计
        cursor.execute("""
            SELECT pos_side, COUNT(*), SUM(loss_amount)
            FROM sub_account_liquidations
            GROUP BY pos_side
        """)
        pos_stats = cursor.fetchall()
        
        # 今日统计
        today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*), SUM(loss_amount)
            FROM sub_account_liquidations
            WHERE record_time LIKE ?
        """, (f"{today}%",))
        today_liquidations, today_loss = cursor.fetchone()
        
        conn.close()
        
        long_count = 0
        long_loss = 0
        short_count = 0
        short_loss = 0
        
        for pos_side, count, loss in pos_stats:
            if pos_side == 'long':
                long_count = count
                long_loss = loss or 0
            elif pos_side == 'short':
                short_count = count
                short_loss = loss or 0
        
        return {
            'total_liquidations': total_liquidations or 0,
            'total_loss': total_loss or 0,
            'long_liquidations': long_count,
            'long_loss': long_loss,
            'short_liquidations': short_count,
            'short_loss': short_loss,
            'today_liquidations': today_liquidations or 0,
            'today_loss': today_loss or 0
        }
        
    except Exception as e:
        print(f"❌ 获取总体统计失败: {e}")
        return None

def print_summary():
    """打印统计摘要"""
    print("\n" + "="*60)
    print("📊 子账号爆仓统计摘要")
    print("="*60)
    
    # 总体统计
    summary = get_summary_stats()
    if summary:
        print(f"\n📈 总体统计:")
        print(f"  总爆仓次数: {summary['total_liquidations']}")
        print(f"  总损失金额: ${summary['total_loss']:.2f}")
        print(f"  今日爆仓: {summary['today_liquidations']} 次")
        print(f"  今日损失: ${summary['today_loss']:.2f}")
        print(f"\n  多单爆仓: {summary['long_liquidations']} 次 (${summary['long_loss']:.2f})")
        print(f"  空单爆仓: {summary['short_liquidations']} 次 (${summary['short_loss']:.2f})")
    
    # 账号统计
    print(f"\n📋 账号统计:")
    account_stats = get_account_stats()
    if account_stats:
        for stat in account_stats:
            print(f"  {stat['account_display_name']} ({stat['account_name']}):")
            print(f"    爆仓次数: {stat['total_liquidations']}")
            print(f"    损失金额: ${stat['total_loss_amount']:.2f}")
            print(f"    多单: {stat['long_liquidations']} | 空单: {stat['short_liquidations']}")
            print(f"    最后爆仓: {stat['last_liquidation_time']}")
    else:
        print("  暂无数据")
    
    # 币种统计 (Top 10)
    print(f"\n🪙 币种统计 (Top 10):")
    coin_stats = get_coin_stats()
    if coin_stats:
        for i, stat in enumerate(coin_stats[:10], 1):
            print(f"  {i}. {stat['inst_id']}: {stat['total_liquidations']}次 (${stat['total_loss_amount']:.2f})")
    else:
        print("  暂无数据")
    
    print("="*60 + "\n")

def main():
    """主函数"""
    print("="*60)
    print("🚀 子账号爆仓记录与统计系统")
    print("="*60)
    
    # 初始化数据库
    init_database()
    
    # 显示统计摘要
    print_summary()
    
    # 显示最近10条爆仓记录
    print("📝 最近10条爆仓记录:")
    records = get_liquidation_records(limit=10)
    if records:
        for i, record in enumerate(records, 1):
            print(f"  {i}. [{record['record_time']}] {record['account_display_name']} - "
                  f"{record['inst_id']} - {record['pos_side']} - "
                  f"损失: ${record['loss_amount']:.2f}")
    else:
        print("  暂无记录")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
