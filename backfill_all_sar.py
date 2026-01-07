#!/usr/bin/env python3
"""
批量回填所有币种的今日SAR数据
"""
import os
import json
import requests
import talib
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import pytz
import time

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
OKX_API_BASE = 'https://www.okx.com'

SYMBOLS = [
    'TAO', 'BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA',
    'LINK', 'DOT', 'LTC', 'BCH', 'UNI', 'NEAR', 'AAVE', 'FIL',
    'APT', 'STX', 'SUI', 'TRX', 'TON', 'HBAR', 'XLM', 'CRO',
    'ETC', 'LDO', 'CRV', 'CFX'
]

def backfill_symbol(symbol):
    """回填单个币种"""
    try:
        inst_id = f'{symbol}-USDT-SWAP'
        print(f"\n{symbol:6} ", end='', flush=True)
        
        # 获取K线
        url = f"{OKX_API_BASE}/api/v5/market/candles"
        params = {'instId': inst_id, 'bar': '5m', 'limit': '300'}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if data['code'] != '0' or not data.get('data'):
            print(f"❌ API失败")
            return 0
        
        candles = data['data'][::-1]
        
        # 计算SAR
        high = np.array([float(c[2]) for c in candles])
        low = np.array([float(c[3]) for c in candles])
        close = np.array([float(c[4]) for c in candles])
        sar = talib.SAR(high, low, acceleration=0.02, maximum=0.2)
        
        # 提取今日数据
        records = []
        for i, candle in enumerate(candles):
            if np.isnan(sar[i]):
                continue
            
            ts_ms = int(candle[0])
            dt_utc = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            dt_beijing = dt_utc.astimezone(BEIJING_TZ)
            
            if dt_beijing.strftime('%Y-%m-%d') != '2026-01-07':
                continue
            
            records.append({
                'symbol': inst_id,
                'timestamp': ts_ms,
                'datetime_utc': dt_utc.strftime('%Y-%m-%d %H:%M:%S'),
                'datetime_beijing': dt_beijing.strftime('%Y-%m-%d %H:%M:%S'),
                'sar_value': float(sar[i]),
                'sar_position': 'bullish' if close[i] > sar[i] else 'bearish',
                'price_close': float(candle[4]),
                'price_high': float(candle[2]),
                'price_low': float(candle[3]),
                'volume': float(candle[5])
            })
        
        if not records:
            print(f"⚠️  无数据")
            return 0
        
        # 读取现有数据
        file_path = Path(f'data/sar_slope/{symbol}/2026-01-07.jsonl')
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing = []
        if file_path.exists():
            with open(file_path, 'r') as f:
                existing = [json.loads(line) for line in f]
        
        # 合并去重
        existing_times = {r['datetime_beijing'] for r in existing}
        new = [r for r in records if r['datetime_beijing'] not in existing_times]
        
        all_data = existing + new
        all_data.sort(key=lambda x: x['datetime_beijing'])
        
        # 保存
        with open(file_path, 'w') as f:
            for r in all_data:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        
        print(f"✅ {len(all_data):3}条 (新增{len(new):3}条)")
        return len(all_data)
        
    except Exception as e:
        print(f"❌ {e}")
        return 0

if __name__ == '__main__':
    print("="*60)
    print("批量回填SAR数据 (使用TA-Lib)")
    print("="*60)
    print(f"时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"币种: {len(SYMBOLS)}")
    
    total = 0
    success = 0
    
    for symbol in SYMBOLS:
        count = backfill_symbol(symbol)
        if count > 0:
            total += count
            success += 1
        time.sleep(0.2)  # 避免请求过快
    
    print()
    print("="*60)
    print(f"完成: {success}/{len(SYMBOLS)} - 总计 {total} 条记录")
    print("="*60)
