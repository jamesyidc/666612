#!/usr/bin/env python3
"""
回填今日SAR历史数据
从今天0点开始到当前时间的所有数据
"""
import requests
import json
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import time

# 配置
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
OKX_API_BASE = 'https://www.okx.com'
DATA_DIR = Path('data/sar_slope')

# 监控的币种
SYMBOLS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP', 'BNB-USDT-SWAP',
    'XRP-USDT-SWAP', 'DOGE-USDT-SWAP', 'ADA-USDT-SWAP', 'LINK-USDT-SWAP',
    'DOT-USDT-SWAP', 'LTC-USDT-SWAP', 'BCH-USDT-SWAP', 'UNI-USDT-SWAP',
    'NEAR-USDT-SWAP', 'AAVE-USDT-SWAP', 'FIL-USDT-SWAP', 'APT-USDT-SWAP',
    'STX-USDT-SWAP', 'TAO-USDT-SWAP', 'SUI-USDT-SWAP', 'TRX-USDT-SWAP',
    'TON-USDT-SWAP', 'HBAR-USDT-SWAP', 'XLM-USDT-SWAP', 'CRO-USDT-SWAP',
    'ETC-USDT-SWAP', 'LDO-USDT-SWAP', 'CRV-USDT-SWAP', 'CFX-USDT-SWAP'
]

def calculate_sar(candles):
    """
    计算抛物线SAR指标
    使用标准的SAR算法
    """
    if len(candles) < 5:
        return []
    
    sar_data = []
    
    # 初始参数
    af = 0.02  # 加速因子
    max_af = 0.2  # 最大加速因子
    
    # 初始化：假设第一个是上升趋势
    ep = float(candles[0][2])  # extreme point (最高价)
    sar = float(candles[0][3])  # 初始SAR为最低价
    is_uptrend = True
    
    for i in range(len(candles)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        close = float(candles[i][4])
        
        if i == 0:
            # 第一根K线
            sar_data.append({
                'sar': sar,
                'position': 'bullish' if close > sar else 'bearish'
            })
            continue
        
        # 计算新的SAR值
        sar = sar + af * (ep - sar)
        
        # 检查是否需要反转
        if is_uptrend:
            # 上升趋势中
            if low < sar:
                # 反转到下降趋势
                is_uptrend = False
                sar = ep  # SAR跳到之前的EP
                ep = low  # 新的EP是当前最低价
                af = 0.02  # 重置加速因子
            else:
                # 继续上升趋势
                if high > ep:
                    ep = high
                    af = min(af + 0.02, max_af)
        else:
            # 下降趋势中
            if high > sar:
                # 反转到上升趋势
                is_uptrend = True
                sar = ep  # SAR跳到之前的EP
                ep = high  # 新的EP是当前最高价
                af = 0.02  # 重置加速因子
            else:
                # 继续下降趋势
                if low < ep:
                    ep = low
                    af = min(af + 0.02, max_af)
        
        sar_data.append({
            'sar': sar,
            'position': 'bullish' if close > sar else 'bearish'
        })
    
    return sar_data

def fetch_historical_candles(symbol, start_time, end_time):
    """获取指定时间范围的K线数据"""
    url = f"{OKX_API_BASE}/api/v5/market/candles"
    
    all_candles = []
    current_end = end_time
    
    while current_end > start_time:
        params = {
            'instId': symbol,
            'bar': '5m',
            'before': str(current_end),
            'limit': '300'  # 每次最多300条
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['code'] != '0':
                print(f"  ❌ API错误: {data.get('msg', 'Unknown error')}")
                break
            
            candles = data['data']
            if not candles:
                break
            
            # 添加到结果（注意：API返回的是倒序）
            all_candles.extend(candles)
            
            # 更新下一次查询的结束时间
            oldest_timestamp = int(candles[-1][0])
            if oldest_timestamp <= start_time:
                break
            
            current_end = oldest_timestamp
            time.sleep(0.2)  # 避免请求过快
            
        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            break
    
    # 反转顺序（最旧的在前）
    all_candles.reverse()
    
    # 过滤时间范围
    filtered_candles = []
    for candle in all_candles:
        ts = int(candle[0])
        if start_time <= ts <= end_time:
            filtered_candles.append(candle)
    
    return filtered_candles

def backfill_symbol(symbol):
    """回填单个币种的今日数据"""
    print(f"\n{'='*60}")
    print(f"处理 {symbol}")
    print(f"{'='*60}")
    
    # 计算今天0点到现在的时间范围
    now = datetime.now(BEIJING_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    start_ts = int(today_start.timestamp() * 1000)
    end_ts = int(now.timestamp() * 1000)
    
    print(f"时间范围: {today_start.strftime('%Y-%m-%d %H:%M')} ~ {now.strftime('%H:%M')}")
    
    # 获取历史K线
    print(f"📡 获取历史K线数据...")
    candles = fetch_historical_candles(symbol, start_ts, end_ts)
    
    if not candles:
        print(f"  ⚠️  未获取到数据")
        return 0
    
    print(f"  ✅ 获取到 {len(candles)} 根K线")
    
    # 计算SAR指标
    print(f"📊 计算SAR指标...")
    sar_results = calculate_sar(candles)
    
    if len(sar_results) != len(candles):
        print(f"  ⚠️  SAR计算结果数量不匹配")
        return 0
    
    # 准备写入数据
    records = []
    for i, candle in enumerate(candles):
        timestamp = int(candle[0])
        dt_utc = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
        dt_beijing = dt_utc.astimezone(BEIJING_TZ)
        
        record = {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime_utc': dt_utc.strftime('%Y-%m-%d %H:%M:%S'),
            'datetime_beijing': dt_beijing.strftime('%Y-%m-%d %H:%M:%S'),
            'sar_value': round(sar_results[i]['sar'], 4),
            'sar_position': sar_results[i]['position'],
            'price_close': float(candle[4]),
            'price_high': float(candle[2]),
            'price_low': float(candle[3]),
            'price_open': float(candle[1]),
            'volume': float(candle[5]),
            'written_at': datetime.now(BEIJING_TZ).isoformat()
        }
        records.append(record)
    
    # 写入JSONL文件
    symbol_dir = DATA_DIR / symbol
    symbol_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = now.strftime('%Y-%m-%d')
    file_path = symbol_dir / f'{date_str}.jsonl'
    
    # 备份现有文件
    if file_path.exists():
        backup_path = symbol_dir / f'{date_str}.jsonl.backup'
        import shutil
        shutil.copy(file_path, backup_path)
        print(f"  💾 已备份现有文件")
    
    # 写入新数据
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"  ✅ 已写入 {len(records)} 条记录到 {file_path}")
    
    # 显示摘要
    print(f"\n  📝 数据摘要:")
    print(f"     第一条: {records[0]['datetime_beijing']} - {records[0]['sar_position']}")
    print(f"     最后条: {records[-1]['datetime_beijing']} - {records[-1]['sar_position']}")
    
    bullish_count = sum(1 for r in records if r['sar_position'] == 'bullish')
    bearish_count = sum(1 for r in records if r['sar_position'] == 'bearish')
    print(f"     多头: {bullish_count}, 空头: {bearish_count}")
    
    return len(records)

def main():
    print("="*60)
    print("SAR数据回填工具 - 今日完整数据")
    print("="*60)
    print(f"开始时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"币种数量: {len(SYMBOLS)}")
    print()
    
    total_records = 0
    success_count = 0
    
    for idx, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{idx}/{len(SYMBOLS)}] ", end='')
        try:
            count = backfill_symbol(symbol)
            if count > 0:
                total_records += count
                success_count += 1
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("回填完成")
    print("="*60)
    print(f"成功: {success_count}/{len(SYMBOLS)}")
    print(f"总记录数: {total_records}")
    print()

if __name__ == '__main__':
    main()
