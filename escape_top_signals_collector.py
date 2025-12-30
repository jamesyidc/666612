#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逃顶信号收集器
自动从support_resistance_levels表中提取逃顶信号并存储到escape_top_signals_24h表
"""

import sqlite3
import time
import logging
from datetime import datetime
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/escape_top_signals_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

DB_PATH = 'crypto_data.db'
COLLECTION_INTERVAL = 60  # 每60秒采集一次

def collect_escape_signals():
    """采集逃顶信号"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        
        # 插入或更新逃顶信号
        insert_sql = """
        INSERT OR REPLACE INTO escape_top_signals_24h 
        (symbol, signal_time, current_price, resistance_line_1, resistance_line_2, 
         distance_to_r1, distance_to_r2, scenario_3_count, scenario_4_count, 
         total_escape_score, is_escape_signal, position_48h, position_7d, 
         price_change_24h, change_percent_24h, alert_triggered)
        SELECT 
            symbol,
            record_time as signal_time,
            current_price,
            resistance_line_1,
            resistance_line_2,
            distance_to_resistance_1 as distance_to_r1,
            distance_to_resistance_2 as distance_to_r2,
            alert_scenario_3 as scenario_3_count,
            alert_scenario_4 as scenario_4_count,
            (alert_scenario_3 + alert_scenario_4) as total_escape_score,
            CASE WHEN (alert_scenario_3 + alert_scenario_4) >= 8 THEN 1 ELSE 0 END as is_escape_signal,
            position_48h,
            position_7d,
            price_change_24h,
            change_percent_24h,
            alert_triggered
        FROM support_resistance_levels
        WHERE datetime(record_time) >= datetime('now', '-24 hours')
          AND (alert_scenario_3 + alert_scenario_4) >= 8
        """
        
        cursor.execute(insert_sql)
        inserted_count = cursor.rowcount
        conn.commit()
        
        # 清理超过24小时的旧数据
        cursor.execute("""
            DELETE FROM escape_top_signals_24h
            WHERE datetime(signal_time) < datetime('now', '-24 hours')
        """)
        deleted_count = cursor.rowcount
        conn.commit()
        
        # 获取当前统计
        cursor.execute("SELECT COUNT(*) FROM escape_top_signals_24h")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT symbol) 
            FROM escape_top_signals_24h 
            WHERE is_escape_signal = 1
        """)
        active_coins = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(
            f"✅ 采集完成 | 新增/更新: {inserted_count} | 清理: {deleted_count} | "
            f"总计: {total_count} | 活跃币种: {active_coins}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 采集失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("逃顶信号收集器启动")
    logger.info("=" * 60)
    
    # 首次采集
    collect_escape_signals()
    
    # 定时采集
    while True:
        try:
            time.sleep(COLLECTION_INTERVAL)
            collect_escape_signals()
            
        except KeyboardInterrupt:
            logger.info("收到退出信号，停止采集")
            break
        except Exception as e:
            logger.error(f"❌ 主循环异常: {str(e)}")
            time.sleep(5)

if __name__ == '__main__':
    main()
