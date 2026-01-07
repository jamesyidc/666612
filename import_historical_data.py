#!/usr/bin/env python3
"""导入OKX历史数据（过去16天的5分钟K线）"""
import requests
import json
import time
from datetime import datetime, timedelta
import pytz
from sar_slope_jsonl_system import SARSlopeJSONLSystem, MONITORED_SYMBOLS

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def fetch_okx_history(symbol, days=16):
    """获取OKX历史K线数据"""
    url = "https://www.okx.com/api/v5/market/candles"
    end_time = int(time.time() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)
    
    all_data = []
    current_end = end_time
    
    while current_end > start_time:
        params = {
            'instId': symbol,
            'bar': '5m',
            'limit': 300,
            'before': current_end
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['code'] == '0' and data['data']:
                candles = data['data']
                all_data.extend(candles)
                current_end = int(candles[-1][0])
                print(f"  获取 {len(candles)} 条记录，时间范围: {candles[0][0]} - {candles[-1][0]}")
                time.sleep(0.2)
            else:
                break
                
        except Exception as e:
            print(f"  错误: {e}")
            break
    
    return all_data[::-1]  # 反转为时间正序

def main():
    sar_system = SARSlopeJSONLSystem()
    total_imported = 0
    
    for symbol in MONITORED_SYMBOLS:
        print(f"\n处理 {symbol}...")
        candles = fetch_okx_history(symbol, days=16)
        
        if not candles:
            print(f"  ⚠️ 未获取到数据")
            continue
        
        # 使用系统的collect_data方法处理每条K线
        for candle in candles:
            try:
                sar_system.collect_data(symbol, candle)
            except Exception as e:
                print(f"  处理错误: {e}")
                continue
        
        total_imported += len(candles)
        print(f"  ✅ 导入 {len(candles)} 条历史数据")
    
    print(f"\n总计导入 {total_imported} 条历史记录")

if __name__ == '__main__':
    main()
