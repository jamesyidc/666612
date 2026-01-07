#!/usr/bin/env python3
"""
使用TA-Lib回填今日SAR数据
"""
import os
import requests
import json
from datetime import datetime
import pytz
from pathlib import Path
import talib
import numpy as np
import time
import shutil

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DATA_DIR = Path('data/sar_slope')
OKX_API = 'https://www.okx.com/api/v5/market/candles'

SYMBOLS = [
    'TAO-USDT-SWAP', 'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP',
    'BNB-USDT-SWAP', 'XRP-USDT-SWAP', 'DOGE-USDT-SWAP', 'ADA-USDT-SWAP',
    'LINK-USDT-SWAP', 'DOT-USDT-SWAP', 'LTC-USDT-SWAP', 'BCH-USDT-SWAP',
    'UNI-USDT-SWAP', 'NEAR-USDT-SWAP', 'AAVE-USDT-SWAP', 'FIL-USDT-SWAP',
    'APT-USDT-SWAP', 'STX-USDT-SWAP', 'SUI-USDT-SWAP', 'TRX-USDT-SWAP',
    'TON-USDT-SWAP', 'HBAR-USDT-SWAP', 'XLM-USDT-SWAP', 'CRO-USDT-SWAP',
    'ETC-USDT-SWAP', 'LDO-USDT-SWAP', 'CRV-USDT-SWAP', 'CFX-USDT-SWAP'
]

def backfill_symbol(symbol):
    """回填单个币种"""
    try:
        print(f"\n[{symbol}] ", end='', flush=True)
        
        # 获取最近300根5分钟K线
        response = requests.get(OKX_API, params={
            'instId': symbol,
            'bar': '5m',
            'limit': '300'
        }, timeout=10)
        
        data = response.json()
        if data['code'] != '0' or not data['data']:
            print(f"❌ 获取失败")
            return 0
        
        candles = data['data']
        candles.reverse()  # 反转为时间正序
        
        # 计算SAR
        highs = np.array([float(c[2]) for c in candles])
        lows = np.array([float(c[3]) for c in candles])
        closes = np.array([float(c[4]) for c in candles])
        sar_values = talib.SAR(highs, lows, acceleration=0.02, maximum=0.2)
        
        # 提取今日数据
        today_records = []
        for i, candle in enumerate(candles):
            ts = int(candle[0])
            dt = datetime.fromtimestamp(ts/1000, tz=BEIJING_TZ)
            
            if dt.date().isoformat() == '2026-01-07':
                record = {
                    'symbol': symbol,
                    'timestamp': ts,
                    'datetime_utc': datetime.fromtimestamp(ts/1000, tz=pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                    'datetime_beijing': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'sar_value': round(float(sar_values[i]), 6),
                    'sar_position': 'bullish' if closes[i] > sar_values[i] else 'bearish',
                    'price_close': round(float(candle[4]), 6),
                    'price_high': float(candle[2]),
                    'price_low': float(candle[3]),
                    'price_open': float(candle[1]),
                    'volume': float(candle[5]),
                    'written_at': datetime.now(BEIJING_TZ).isoformat()
                }
                today_records.append(record)
        
        if not today_records:
            print(f"⚠️  无今日数据")
            return 0
        
        # 写入文件
        symbol_dir = DATA_DIR / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        file_path = symbol_dir / '2026-01-07.jsonl'
        
        # 备份
        if file_path.exists():
            backup_path = symbol_dir / '2026-01-07.jsonl.backup'
            shutil.copy(file_path, backup_path)
        
        # 读取现有数据
        existing_records = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_records = [json.loads(line) for line in f]
        
        # 合并数据（去重）
        existing_times = {r['datetime_beijing'] for r in existing_records}
        new_records = [r for r in today_records if r['datetime_beijing'] not in existing_times]
        
        # 合并并排序
        all_records = existing_records + new_records
        all_records.sort(key=lambda x: x['datetime_beijing'])
        
        # 写入
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        print(f"✅ {len(today_records)}条(新增{len(new_records)}条,总计{len(all_records)}条)")
        return len(all_records)
        
    except Exception as e:
        print(f"❌ {e}")
        return 0

def main():
    print("="*60)
    print("SAR数据回填 (使用TA-Lib)")
    print("="*60)
    print(f"时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"币种: {len(SYMBOLS)}")
    print()
    
    total = 0
    success = 0
    
    for symbol in SYMBOLS:
        count = backfill_symbol(symbol)
        if count > 0:
            total += count
            success += 1
        time.sleep(0.3)  # 避免请求过快
    
    print(f"\n{'='*60}")
    print(f"完成: {success}/{len(SYMBOLS)} - 总计 {total} 条记录")
    print("="*60)

if __name__ == '__main__':
    main()
