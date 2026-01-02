#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支撑阻力信号监控守护进程
每1分钟抓取一次 24小时顶信号 和 2小时底信号
存储为JSON列表，保留最近1000条记录
"""

import time
import json
import requests
from datetime import datetime
import pytz

# 数据文件
SIGNAL_DATA_FILE = 'signal_monitor_data.json'

# API端点
API_URL = 'http://localhost:5000/api/support-resistance/latest-signal'

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取北京时间字符串"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

def load_history():
    """加载历史数据"""
    try:
        with open(SIGNAL_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {
            'history': [],
            'latest': {
                'top_signal': 0,
                'bottom_signal': 0,
                'update_time': None
            }
        }
    except Exception as e:
        print(f"⚠️ 加载历史数据失败: {e}")
        return {
            'history': [],
            'latest': {
                'top_signal': 0,
                'bottom_signal': 0,
                'update_time': None
            }
        }

def save_history(data):
    """保存历史数据"""
    try:
        with open(SIGNAL_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存历史数据失败: {e}")

def fetch_signals():
    """抓取信号数据"""
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()
        
        if data.get('success'):
            s1 = data.get('scenario_1_count', 0)
            s2 = data.get('scenario_2_count', 0)
            s3 = data.get('scenario_3_count', 0)
            s4 = data.get('scenario_4_count', 0)
            
            # 计算信号
            top_signal = s3 + s4  # 24小时顶信号 = 情况3 + 情况4
            bottom_signal = s1 + s2  # 2小时底信号 = 情况1 + 情况2
            
            return {
                'top_signal': top_signal,
                'bottom_signal': bottom_signal,
                'scenario_1': s1,
                'scenario_2': s2,
                'scenario_3': s3,
                'scenario_4': s4,
                'timestamp': get_beijing_time()
            }
        else:
            print(f"⚠️ API返回失败: {data.get('message', '未知错误')}")
            return None
            
    except Exception as e:
        print(f"❌ 抓取信号失败: {e}")
        return None

def monitor_loop():
    """主监控循环"""
    print("=" * 60)
    print("🚀 支撑阻力信号监控守护进程已启动")
    print(f"⏰ 启动时间: {get_beijing_time()}")
    print(f"📊 抓取间隔: 1分钟")
    print(f"💾 数据文件: {SIGNAL_DATA_FILE}")
    print("=" * 60)
    
    while True:
        try:
            # 抓取信号
            signals = fetch_signals()
            
            if signals:
                # 加载历史数据
                data = load_history()
                
                # 添加新记录
                data['history'].append(signals)
                
                # 只保留最近1000条
                if len(data['history']) > 1000:
                    data['history'] = data['history'][-1000:]
                
                # 更新最新值
                data['latest'] = {
                    'top_signal': signals['top_signal'],
                    'bottom_signal': signals['bottom_signal'],
                    'update_time': signals['timestamp']
                }
                
                # 保存到文件
                save_history(data)
                
                # 打印日志
                print(f"✅ [{signals['timestamp']}] 顶信号: {signals['top_signal']} | 底信号: {signals['bottom_signal']} | 情况1-4: {signals['scenario_1']}/{signals['scenario_2']}/{signals['scenario_3']}/{signals['scenario_4']}")
            else:
                print(f"⚠️ [{get_beijing_time()}] 本次抓取失败")
            
        except Exception as e:
            print(f"❌ [{get_beijing_time()}] 监控循环异常: {e}")
            import traceback
            print(traceback.format_exc())
        
        # 等待60秒
        print(f"⏳ 等待60秒后进行下一次抓取...")
        time.sleep(60)

if __name__ == '__main__':
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n⛔ 监控程序已停止")
    except Exception as e:
        print(f"❌ 程序异常退出: {e}")
        import traceback
        print(traceback.format_exc())
