#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逃顶事件统计采集器 (简化版 - 使用JSON文件)
每5分钟统计一次右边"逃顶"框里的事件数量
"""

import json
import time
import logging
import requests
from datetime import datetime, timedelta
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/escape_event_stats_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

DATA_FILE = 'escape_event_stats.json'
COLLECTION_INTERVAL = 300  # 5分钟 = 300秒
API_URL = 'http://localhost:5000/api/escape-top-signals/latest'

def load_data():
    """加载历史数据"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
    return []

def save_data(data):
    """保存数据"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存数据失败: {e}")
        return False

def collect_escape_event_count():
    """统计当前的逃顶事件数量（右边框显示的徽章数量）"""
    try:
        # 从API获取当前的逃顶信号
        response = requests.get(API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # 统计 is_escape_signal=True 的记录数
                signals = data.get('data', [])
                event_count = len([s for s in signals if s.get('is_escape_signal')])
                
                # 加载历史数据
                history = load_data()
                
                # 添加新记录
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:00')
                history.append({
                    'time': current_time,
                    'count': event_count
                })
                
                # 清理超过24小时的旧数据
                cutoff_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:00')
                history = [h for h in history if h['time'] >= cutoff_time]
                
                # 保存数据
                if save_data(history):
                    logger.info(f"✅ 统计完成: {current_time} → {event_count} 个逃顶事件")
                    return event_count
                else:
                    logger.error("保存数据失败")
                    return None
            else:
                logger.error(f"API返回错误: {data.get('message', '未知错误')}")
                return None
        else:
            logger.error(f"API请求失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ 统计失败: {e}")
        return None

def main():
    logger.info("=" * 60)
    logger.info("逃顶事件统计采集器启动 (简化版 - JSON存储)")
    logger.info("=" * 60)
    
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
