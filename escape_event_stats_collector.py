#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逃顶事件统计采集器
每5分钟统计一次右边"逃顶"框里的事件数量
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/escape_event_stats_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

DB_PATH = 'crypto_data.db'
COLLECTION_INTERVAL = 300  # 5分钟 = 300秒

def create_table():
    """创建统计表"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escape_event_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_time TIMESTAMP NOT NULL,
                event_count INTEGER NOT NULL,
                UNIQUE(record_time)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_escape_event_time 
            ON escape_event_stats(record_time DESC)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ 表 escape_event_stats 创建成功")
        return True
    except Exception as e:
        logger.error(f"❌ 创建表失败: {e}")
        return False

def collect_escape_event_count():
    """统计当前的逃顶事件数量"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        
        # 统计最近24小时内不同时间点的逃顶事件
        # 条件：alert_triggered=1 且 (情况3+情况4)>=8 且 情况3>=1 且 情况4>=1
        cursor.execute('''
            SELECT COUNT(DISTINCT strftime('%Y-%m-%d %H:%M', record_time)) as event_count
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', '-24 hours')
              AND alert_triggered = 1
              AND (alert_scenario_3 + alert_scenario_4) >= 8
              AND alert_scenario_3 >= 1
              AND alert_scenario_4 >= 1
        ''')
        
        result = cursor.fetchone()
        event_count = result[0] if result else 0
        
        # 插入统计数据
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:00')
        
        cursor.execute('''
            INSERT OR REPLACE INTO escape_event_stats (record_time, event_count)
            VALUES (?, ?)
        ''', (current_time, event_count))
        
        # 清理超过24小时的旧数据
        cursor.execute('''
            DELETE FROM escape_event_stats
            WHERE datetime(record_time) < datetime('now', '-24 hours')
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 统计完成: {current_time} → {event_count} 个逃顶事件")
        return event_count
        
    except Exception as e:
        logger.error(f"❌ 统计失败: {e}")
        return None

def main():
    logger.info("=" * 60)
    logger.info("逃顶事件统计采集器启动")
    logger.info("=" * 60)
    
    # 创建表
    create_table()
    
    # 立即采集一次
    collect_escape_event_count()
    
    # 定时采集
    while True:
        try:
            time.sleep(COLLECTION_INTERVAL)
            collect_escape_event_count()
        except KeyboardInterrupt:
            logger.info("收到退出信号，停止采集")
            break
        except Exception as e:
            logger.error(f"采集出错: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()
