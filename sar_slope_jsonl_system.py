#!/usr/bin/env python3
"""
SAR斜率系统 - JSONL存储版本
使用JSONL文件格式存储数据，替代SQLite数据库
"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz
import requests
from pathlib import Path

# 27个指定币种
MONITORED_SYMBOLS = [
    'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'XRP-USDT-SWAP', 'BNB-USDT-SWAP',
    'SOL-USDT-SWAP', 'LTC-USDT-SWAP', 'DOGE-USDT-SWAP', 'SUI-USDT-SWAP',
    'TRX-USDT-SWAP', 'TON-USDT-SWAP', 'ETC-USDT-SWAP', 'BCH-USDT-SWAP',
    'HBAR-USDT-SWAP', 'XLM-USDT-SWAP', 'FIL-USDT-SWAP', 'LINK-USDT-SWAP',
    'CRO-USDT-SWAP', 'DOT-USDT-SWAP', 'AAVE-USDT-SWAP', 'UNI-USDT-SWAP',
    'NEAR-USDT-SWAP', 'APT-USDT-SWAP', 'CFX-USDT-SWAP', 'CRV-USDT-SWAP',
    'STX-USDT-SWAP', 'LDO-USDT-SWAP', 'TAO-USDT-SWAP'
]

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DATA_DIR = Path('/home/user/webapp/data/sar_slope')
TIMEFRAME = '5m'

# OKX API配置
OKX_API_BASE = 'https://www.okx.com'

class SARSlopeJSONLSystem:
    """SAR斜率JSONL存储系统"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.ensure_directories()
        
    def ensure_directories(self):
        """确保数据目录存在"""
        # 创建主数据目录
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 为每个币种创建子目录
        for symbol in MONITORED_SYMBOLS:
            symbol_clean = symbol.replace('-USDT-SWAP', '')
            symbol_dir = self.data_dir / symbol_clean
            symbol_dir.mkdir(exist_ok=True)
        
        # 创建统计目录
        (self.data_dir / 'stats').mkdir(exist_ok=True)
        
        print(f"✅ 数据目录已初始化: {self.data_dir}")
    
    def get_symbol_file(self, symbol: str, date: datetime) -> Path:
        """获取币种数据文件路径（按日期分文件）"""
        symbol_clean = symbol.replace('-USDT-SWAP', '')
        date_str = date.strftime('%Y-%m-%d')
        return self.data_dir / symbol_clean / f"{date_str}.jsonl"
    
    def write_data_point(self, symbol: str, data: dict):
        """写入单个数据点到JSONL文件"""
        now = datetime.now(BEIJING_TZ)
        file_path = self.get_symbol_file(symbol, now)
        
        # 添加时间戳
        data['written_at'] = now.isoformat()
        
        # 追加到文件
        with open(file_path, 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')
    
    def read_latest(self, symbol: str, limit: int = 100) -> List[dict]:
        """读取最近的N条记录"""
        symbol_clean = symbol.replace('-USDT-SWAP', '')
        symbol_dir = self.data_dir / symbol_clean
        
        if not symbol_dir.exists():
            return []
        
        # 获取最近7天的文件
        all_data = []
        for days_ago in range(7):
            date = datetime.now(BEIJING_TZ) - timedelta(days=days_ago)
            file_path = self.get_symbol_file(symbol, date)
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            all_data.append(json.loads(line))
        
        # 按时间戳排序并返回最近的N条
        all_data.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return all_data[:limit]
    
    def read_date_range(self, symbol: str, start_date: datetime, end_date: datetime) -> List[dict]:
        """读取指定日期范围的数据"""
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            file_path = self.get_symbol_file(symbol, current_date)
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            all_data.append(json.loads(line))
            
            current_date += timedelta(days=1)
        
        return sorted(all_data, key=lambda x: x.get('timestamp', 0))
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """清理超过指定天数的旧数据"""
        cutoff_date = datetime.now(BEIJING_TZ) - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for symbol in MONITORED_SYMBOLS:
            symbol_clean = symbol.replace('-USDT-SWAP', '')
            symbol_dir = self.data_dir / symbol_clean
            
            if symbol_dir.exists():
                for file_path in symbol_dir.glob('*.jsonl'):
                    try:
                        # 从文件名提取日期
                        date_str = file_path.stem
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')
                        file_date = BEIJING_TZ.localize(file_date)
                        
                        if file_date < cutoff_date:
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        print(f"清理文件出错 {file_path}: {e}")
        
        print(f"🗑️ 清理了 {deleted_count} 个旧数据文件")
        return deleted_count
    
    def fetch_sar_data(self, symbol: str) -> Optional[dict]:
        """从OKX获取SAR指标数据"""
        try:
            url = f"{OKX_API_BASE}/api/v5/market/candles"
            params = {
                'instId': symbol,
                'bar': TIMEFRAME,
                'limit': '100'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == '0' and data.get('data'):
                candles = data['data']
                latest = candles[0]
                
                # 计算SAR（简化版本）
                sar_value = self.calculate_sar(candles)
                close_price = float(latest[4])
                
                # 判断多空位置
                position = 'bullish' if close_price > sar_value else 'bearish'
                
                timestamp = int(latest[0])
                dt_utc = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
                dt_beijing = dt_utc.astimezone(BEIJING_TZ)
                
                return {
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'datetime_utc': dt_utc.strftime('%Y-%m-%d %H:%M:%S'),
                    'datetime_beijing': dt_beijing.strftime('%Y-%m-%d %H:%M:%S'),
                    'sar_value': round(sar_value, 6),
                    'sar_position': position,
                    'price_close': round(close_price, 6),
                    'price_high': float(latest[2]),
                    'price_low': float(latest[3]),
                    'volume': float(latest[5])
                }
            
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
            return None
    
    def calculate_sar(self, candles: List, af_start: float = 0.02, af_max: float = 0.2) -> float:
        """
        计算抛物线SAR指标
        简化版本，使用默认参数
        """
        if len(candles) < 2:
            return float(candles[0][4])  # 返回收盘价
        
        # 获取最近的价格
        current_close = float(candles[0][4])
        prev_close = float(candles[1][4])
        current_high = float(candles[0][2])
        current_low = float(candles[0][3])
        
        # 简化的SAR计算
        if current_close > prev_close:
            # 上涨趋势，SAR在下方
            sar = current_low * 0.98
        else:
            # 下跌趋势，SAR在上方
            sar = current_high * 1.02
        
        return sar
    
    def collect_all_symbols(self):
        """采集所有币种的数据"""
        print(f"\n{'='*60}")
        print(f"开始采集 {len(MONITORED_SYMBOLS)} 个币种的SAR数据")
        print(f"时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        success_count = 0
        for symbol in MONITORED_SYMBOLS:
            try:
                data = self.fetch_sar_data(symbol)
                if data:
                    self.write_data_point(symbol, data)
                    success_count += 1
                    print(f"✅ {symbol}: SAR={data['sar_value']:.6f}, Position={data['sar_position']}, Price={data['price_close']:.6f}")
                else:
                    print(f"❌ {symbol}: 获取数据失败")
                
                time.sleep(0.2)  # 避免请求过快
                
            except Exception as e:
                print(f"❌ {symbol} 处理出错: {e}")
        
        print(f"\n✅ 采集完成: {success_count}/{len(MONITORED_SYMBOLS)} 成功")
        return success_count
    
    def get_all_latest(self) -> List[dict]:
        """获取所有币种的最新数据"""
        latest_data = []
        
        for symbol in MONITORED_SYMBOLS:
            data_points = self.read_latest(symbol, limit=1)
            if data_points:
                latest_data.append(data_points[0])
        
        return latest_data
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        latest_data = self.get_all_latest()
        
        bullish_count = sum(1 for d in latest_data if d.get('sar_position') == 'bullish')
        bearish_count = sum(1 for d in latest_data if d.get('sar_position') == 'bearish')
        
        return {
            'total_symbols': len(latest_data),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'last_update': datetime.now(BEIJING_TZ).isoformat()
        }

def main():
    """主函数"""
    system = SARSlopeJSONLSystem()
    
    print("SAR斜率JSONL系统启动")
    print(f"数据目录: {system.data_dir}")
    print(f"监控币种: {len(MONITORED_SYMBOLS)} 个")
    print(f"时间间隔: {TIMEFRAME}")
    
    # 执行一次采集
    system.collect_all_symbols()
    
    # 显示统计
    stats = system.get_stats()
    print(f"\n📊 统计信息:")
    print(f"  总币种数: {stats['total_symbols']}")
    print(f"  多头: {stats['bullish_count']}")
    print(f"  空头: {stats['bearish_count']}")
    
    # 清理旧数据
    system.cleanup_old_data(days_to_keep=7)

if __name__ == '__main__':
    main()
