#!/usr/bin/env python3
"""
支撑压力线采集器
每30秒采集一次27个币种的支撑线和压力线
同时采集当前价格、7天周期(1W)和48小时周期(2D)的最高最低价
"""

import os
import sys
import time
import sqlite3
import requests
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(__file__), 'support_resistance.db')
DB_TIMEOUT = 60.0  # 60秒超时

# 日志文件
LOG_FILE = os.path.join(os.path.dirname(__file__), 'support_resistance.log')

# 监控的币种列表（27个永续合约）
SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT',
    'LTCUSDT', 'DOGEUSDT', 'SUIUSDT', 'TRXUSDT', 'TONUSDT',
    'ETCUSDT', 'BCHUSDT', 'HBARUSDT', 'XLMUSDT', 'FILUSDT',
    'LINKUSDT', 'CROUSDT', 'DOTUSDT', 'AAVEUSDT', 'UNIUSDT',
    'NEARUSDT', 'APTUSDT', 'CFXUSDT', 'CRVUSDT', 'STXUSDT',
    'LDOUSDT', 'TAOUSDT'
]

# OKX API配置
OKX_API_BASE = 'https://www.okx.com'

# 北京时区配置
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    except Exception as e:
        print(f"写入日志失败: {e}")

def get_current_price(symbol: str) -> Optional[float]:
    """获取当前价格（永续合约）"""
    try:
        # 转换为OKX永续合约格式 (BTCUSDT -> BTC-USDT-SWAP)
        okx_symbol = f"{symbol[:-4]}-{symbol[-4:]}-SWAP"
        
        url = f"{OKX_API_BASE}/api/v5/market/ticker"
        params = {'instId': okx_symbol}
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            price = float(data['data'][0]['last'])
            return price
        return None
    except Exception as e:
        log(f"获取 {symbol} 当前价格失败: {e}")
        return None

def get_historical_klines(symbol: str, hours: int) -> List[Dict]:
    """获取历史K线数据（永续合约）"""
    try:
        # 转换为OKX永续合约格式
        okx_symbol = f"{symbol[:-4]}-{symbol[-4:]}-SWAP"
        
        # 计算需要多少根K线（每根5分钟）
        bars = (hours * 60) // 5 + 10  # 多取一些以确保有足够数据
        
        url = f"{OKX_API_BASE}/api/v5/market/candles"
        params = {
            'instId': okx_symbol,
            'bar': '5m',
            'limit': min(bars, 300)  # OKX限制最多300根
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('code') == '0' and data.get('data'):
            klines = []
            for k in data['data']:
                klines.append({
                    'timestamp': int(k[0]),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return klines
        return []
    except Exception as e:
        log(f"获取 {symbol} K线数据失败: {e}")
        return []

def get_or_create_baseline_price(symbol: str, current_price: float) -> dict:
    """
    获取或创建今日基准价格（北京时间0点）
    返回: {'baseline_price': float, 'price_change': float, 'change_percent': float}
    """
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    conn.execute("PRAGMA busy_timeout = 60000")  # 60秒busy timeout
    cursor = conn.cursor()
    
    # 获取北京时间当前日期
    beijing_now = datetime.now(BEIJING_TZ)
    today_date = beijing_now.date().isoformat()
    
    # 查询今日基准价格
    cursor.execute('''
        SELECT baseline_price FROM daily_baseline_prices
        WHERE symbol = ? AND baseline_date = ?
    ''', (symbol, today_date))
    
    row = cursor.fetchone()
    
    if row:
        # 已有今日基准价格
        baseline_price = row[0]
    else:
        # 创建今日基准价格（使用当前价格）
        baseline_price = current_price
        baseline_time = beijing_now.strftime('%Y-%m-%d 00:00:00')
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_baseline_prices
                (symbol, baseline_date, baseline_price, baseline_time)
                VALUES (?, ?, ?, ?)
            ''', (symbol, today_date, baseline_price, baseline_time))
            conn.commit()
            log(f"✅ 创建 {symbol} 今日基准价格: ${baseline_price:.2f}")
        except Exception as e:
            log(f"❌ 创建基准价格失败: {e}")
    
    # 计算涨跌
    price_change = current_price - baseline_price
    change_percent = (price_change / baseline_price * 100) if baseline_price > 0 else 0
    
    conn.close()
    
    return {
        'baseline_price': baseline_price,
        'price_change': round(price_change, 4),
        'change_percent': round(change_percent, 2)
    }

def calculate_support_resistance(symbol: str) -> Optional[Dict]:
    """计算支撑线和压力线"""
    try:
        # 1. 获取当前价格
        current_price = get_current_price(symbol)
        if not current_price:
            log(f"⚠️ {symbol} 无法获取当前价格")
            return None
        
        # 2. 直接从OKX API获取大周期K线（1根1W + 1根2D，避免取几千根5m数据）
        # 转换币种格式: BTCUSDT -> BTC-USDT-SWAP
        okx_symbol = f"{symbol[:-4]}-{symbol[-4:]}-SWAP"
        
        # 3. 获取1周K线（最新1根）
        try:
            url_1w = f"https://www.okx.com/api/v5/market/candles?instId={okx_symbol}&bar=1W&limit=1"
            response_1w = requests.get(url_1w, timeout=10)
            response_1w.raise_for_status()
            data_1w = response_1w.json()
            
            if data_1w['code'] != '0' or not data_1w['data']:
                log(f"⚠️ {symbol} OKX API返回错误: {data_1w.get('msg')}")
                return None
            
            # OKX K线格式: [timestamp, open, high, low, close, volume, ...]
            kline_1w = data_1w['data'][0]
            historical_7d_high = float(kline_1w[2])  # 1周最高价
            historical_7d_low = float(kline_1w[3])   # 1周最低价
            
        except Exception as e:
            log(f"❌ {symbol} 获取1周K线失败: {str(e)}")
            return None
        
        # 支撑/压力线：包含当前价格，用于计算距离（防止负值）
        support_line_1 = min(historical_7d_low, current_price)
        resistance_line_1 = max(historical_7d_high, current_price)
        
        # 4. 获取2天K线（最新1根）- 用于48小时数据
        try:
            url_2d = f"https://www.okx.com/api/v5/market/candles?instId={okx_symbol}&bar=2D&limit=1"
            response_2d = requests.get(url_2d, timeout=10)
            response_2d.raise_for_status()
            data_2d = response_2d.json()
            
            if data_2d['code'] != '0' or not data_2d['data']:
                log(f"⚠️ {symbol} OKX API返回2天K线错误: {data_2d.get('msg')}")
                # 使用7天数据作为后备
                historical_48h_high = historical_7d_high
                historical_48h_low = historical_7d_low
            else:
                kline_2d = data_2d['data'][0]
                historical_48h_high = float(kline_2d[2])  # 2天最高价
                historical_48h_low = float(kline_2d[3])   # 2天最低价
                
        except Exception as e:
            log(f"⚠️ {symbol} 获取2天K线失败: {str(e)}，使用7天数据")
            historical_48h_high = historical_7d_high
            historical_48h_low = historical_7d_low
        
        # 5. 计算48小时支撑线和压力线
        # 支撑/压力线：包含当前价格，用于计算距离（防止负值）
        support_line_2 = min(historical_48h_low, current_price)
        resistance_line_2 = max(historical_48h_high, current_price)
        
        # 6. 计算距离百分比（原有的绝对距离）
        # 确保分母不为0，并且结果为非负值
        distance_to_support_1 = ((current_price - support_line_1) / support_line_1) * 100 if support_line_1 > 0 else 0
        distance_to_support_2 = ((current_price - support_line_2) / support_line_2) * 100 if support_line_2 > 0 else 0
        distance_to_resistance_1 = ((resistance_line_1 - current_price) / current_price) * 100 if current_price > 0 else 0
        distance_to_resistance_2 = ((resistance_line_2 - current_price) / current_price) * 100 if current_price > 0 else 0
        
        # 修正：如果当前价格创新高/新低，距离应该为0
        distance_to_support_1 = max(0, distance_to_support_1)
        distance_to_support_2 = max(0, distance_to_support_2)
        distance_to_resistance_1 = max(0, distance_to_resistance_1)
        distance_to_resistance_2 = max(0, distance_to_resistance_2)
        
        # 7. 计算位置百分比
        # 用户需求：位置不能超出0-100%范围
        # 当价格创新高/低时，使用包含当前价的区间（support_line/resistance_line）来计算
        
        # 7天范围位置: 使用support_line_1(0%) → resistance_line_1(100%)
        # 这样即使创新高/低，位置也会在0-100%范围内
        if resistance_line_1 != support_line_1:
            position_7d = ((current_price - support_line_1) / (resistance_line_1 - support_line_1)) * 100
        else:
            position_7d = 50.0
        
        # 48小时范围位置: 使用support_line_2(0%) → resistance_line_2(100%)
        if resistance_line_2 != support_line_2:
            position_48h = ((current_price - support_line_2) / (resistance_line_2 - support_line_2)) * 100
        else:
            position_48h = 50.0
        
        # 8. 计算4种情况的位置百分比（用于警报）
        # 情况1: 支撑线2(0%) → 压力线1(100%) 的位置
        if resistance_line_1 != support_line_2:
            position_s2_r1 = ((current_price - support_line_2) / (resistance_line_1 - support_line_2)) * 100
        else:
            position_s2_r1 = 50.0  # 如果相等，设为中间值
            
        # 情况2: 支撑线1(0%) → 压力线2(100%) 的位置
        if resistance_line_2 != support_line_1:
            position_s1_r2 = ((current_price - support_line_1) / (resistance_line_2 - support_line_1)) * 100
        else:
            position_s1_r2 = 50.0
            
        # 情况3: 支撑线1(0%) → 压力线2(100%) 的位置 (与情况2相同)
        position_s1_r2_upper = position_s1_r2
        
        # 情况4: 支撑线1(0%) → 压力线1(100%) 的位置 (与7天位置相同)
        position_s1_r1 = position_7d
        
        # 9. 判断是否触发警报
        # 支撑线警报：使用位置百分比 <= 5%
        # 压力线警报：使用距离百分比 <= 5%（用于实时提醒）
        # 注意：4种情况(scenario)的压力线使用位置 >= 95%（用于统计展示）
        
        # 7天范围警报（统一使用位置百分比判断）
        alert_7d_low = position_7d <= 5                    # 位置 <= 5% (接近7天最低支撑线)
        alert_7d_high = position_7d >= 95                  # 位置 >= 95% (接近7天最高压力线)
        
        # 48小时范围警报（统一使用位置百分比判断）
        alert_48h_low = position_48h <= 5                  # 位置 <= 5% (接近48h最低支撑线)
        alert_48h_high = position_48h >= 95                # 位置 >= 95% (接近48h最高压力线)
        
        # 保留原有4种情况警报(用于兼容性)
        # 支撑线：使用位置 <= 5%，且支撑线1和支撑线2都>=8
        # 压力线：使用位置 >= 95%（改回位置判断，符合业务需求）
        # 场景1（抄底信号）：位置<=5% 且 支撑线1和支撑线2都>=8
        alert_scenario_1 = (position_s2_r1 <= 5 and 
                           support_line_1 >= 8 and 
                           support_line_2 >= 8)              # 接近支撑线2（位置判断）+ 支撑线条件
        # 场景2（抄底信号）：位置<=5% 且 支撑线1和支撑线2都>=8
        alert_scenario_2 = (position_s1_r2 <= 5 and 
                           support_line_1 >= 8 and 
                           support_line_2 >= 8)              # 接近支撑线1（位置判断）+ 支撑线条件
        # 场景3（逃顶信号）：位置>=95% 且 支撑线1和支撑线2都>=1
        alert_scenario_3 = (position_s1_r2_upper >= 95 and 
                           support_line_1 >= 1 and 
                           support_line_2 >= 1)              # 接近压力线2（位置判断）+ 支撑线条件
        alert_scenario_4 = position_s1_r1 >= 95             # 接近压力线1（位置判断）
        
        # 汇总警报
        alert_triggered = alert_scenario_1 or alert_scenario_2 or alert_scenario_3 or alert_scenario_4
        
        # 10. 计算24小时涨跌幅（基于北京时间0点基准）
        change_data = get_or_create_baseline_price(symbol, current_price)
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'support_line_1': support_line_1,
            'support_line_2': support_line_2,
            'resistance_line_1': resistance_line_1,
            'resistance_line_2': resistance_line_2,
            'distance_to_support_1': distance_to_support_1,
            'distance_to_support_2': distance_to_support_2,
            'distance_to_resistance_1': distance_to_resistance_1,
            'distance_to_resistance_2': distance_to_resistance_2,
            # 新增：7天和48小时范围位置百分比
            'position_7d': position_7d,   # 7天范围位置 (7天最低=0%, 7天最高=100%)
            'position_48h': position_48h,  # 48小时范围位置 (48h最低=0%, 48h最高=100%)
            # 4种情况位置百分比
            'position_s2_r1': position_s2_r1,  # 情况1
            'position_s1_r2': position_s1_r2,  # 情况2
            'position_s1_r2_upper': position_s1_r2_upper,  # 情况3
            'position_s1_r1': position_s1_r1,  # 情况4
            # 新增：7天和48小时警报
            'alert_7d_low': alert_7d_low,
            'alert_7d_high': alert_7d_high,
            'alert_48h_low': alert_48h_low,
            'alert_48h_high': alert_48h_high,
            # 原有4种情况警报
            'alert_scenario_1': alert_scenario_1,
            'alert_scenario_2': alert_scenario_2,
            'alert_scenario_3': alert_scenario_3,
            'alert_scenario_4': alert_scenario_4,
            'alert_triggered': alert_triggered or alert_7d_low or alert_7d_high or alert_48h_low or alert_48h_high,
            # 新增：24小时涨跌幅（基于北京时间0点）
            'baseline_price_24h': change_data['baseline_price'],
            'price_change_24h': change_data['price_change'],
            'change_percent_24h': change_data['change_percent']
        }
        
    except Exception as e:
        log(f"❌ {symbol} 计算支撑压力线失败: {e}")
        return None

def save_to_database(data: Dict) -> bool:
    """保存到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        conn.execute("PRAGMA busy_timeout = 60000")
        cursor = conn.cursor()
        
        # 使用 Python UTC 时间而不是 SQLite datetime函数
        from datetime import datetime as dt_class
        utc_now = dt_class.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO support_resistance_levels (
                symbol, current_price,
                support_line_1, support_line_2,
                resistance_line_1, resistance_line_2,
                distance_to_support_1, distance_to_support_2,
                distance_to_resistance_1, distance_to_resistance_2,
                position_s2_r1, position_s1_r2, position_s1_r2_upper, position_s1_r1,
                position_7d, position_48h,
                alert_scenario_1, alert_scenario_2, alert_scenario_3, alert_scenario_4,
                alert_7d_low, alert_7d_high, alert_48h_low, alert_48h_high,
                alert_triggered,
                baseline_price_24h, price_change_24h, change_percent_24h,
                record_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['symbol'], data['current_price'],
            data['support_line_1'], data['support_line_2'],
            data['resistance_line_1'], data['resistance_line_2'],
            data['distance_to_support_1'], data['distance_to_support_2'],
            data['distance_to_resistance_1'], data['distance_to_resistance_2'],
            data['position_s2_r1'], data['position_s1_r2'], data['position_s1_r2_upper'], data['position_s1_r1'],
            data['position_7d'], data['position_48h'],
            int(data['alert_scenario_1']), int(data['alert_scenario_2']), 
            int(data['alert_scenario_3']), int(data['alert_scenario_4']),
            int(data['alert_7d_low']), int(data['alert_7d_high']),
            int(data['alert_48h_low']), int(data['alert_48h_high']),
            int(data['alert_triggered']),
            data['baseline_price_24h'], data['price_change_24h'], data['change_percent_24h'],
            utc_now
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        log(f"❌ 保存数据库失败: {e}")
        return False

def collect_all_symbols():
    """采集所有币种的支撑压力线"""
    log("=" * 60)
    log("🚀 开始采集支撑压力线数据")
    
    success_count = 0
    failed_count = 0
    
    for i, symbol in enumerate(SYMBOLS, 1):
        log(f"📊 [{i}/{len(SYMBOLS)}] 正在处理 {symbol}...")
        
        data = calculate_support_resistance(symbol)
        
        if data:
            if save_to_database(data):
                log(f"✅ {symbol} 采集成功 | 当前价: ${data['current_price']:.2f} | "
                    f"支撑1: ${data['support_line_1']:.2f} ({data['distance_to_support_1']:.2f}%) | "
                    f"压力1: ${data['resistance_line_1']:.2f} ({data['distance_to_resistance_1']:.2f}%)")
                success_count += 1
            else:
                failed_count += 1
        else:
            failed_count += 1
        
        # 避免请求过快
        time.sleep(0.5)
    
    log(f"✅ 采集完成! 成功: {success_count}, 失败: {failed_count}")
    log("=" * 60)

def main():
    """主函数"""
    log("🎯 支撑压力线采集器启动")
    log(f"📊 监控币种数量: {len(SYMBOLS)}")
    log(f"⏰ 采集间隔: 30秒")
    log(f"📁 数据库路径: {DB_PATH}")
    log(f"📈 数据来源: OKX API (1W K线 + 2D K线 + 实时价格)")
    
    while True:
        try:
            collect_all_symbols()
            log("⏳ 等待30秒后进行下一次采集...")
            time.sleep(30)  # 30秒
            
        except KeyboardInterrupt:
            log("⚠️ 收到停止信号，正在退出...")
            break
        except Exception as e:
            log(f"❌ 采集出错: {e}")
            log("⏳ 等待30秒后重试...")
            time.sleep(30)

if __name__ == '__main__':
    main()
