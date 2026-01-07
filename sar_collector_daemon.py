#!/usr/bin/env python3
"""
SAR斜率数据采集守护进程
每5分钟采集一次数据
"""
import time
import traceback
from datetime import datetime
from sar_slope_jsonl_system import SARSlopeJSONLSystem
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
COLLECT_INTERVAL = 300  # 5分钟

def main():
    print("="*60)
    print("SAR斜率数据采集守护进程启动")
    print(f"采集间隔: {COLLECT_INTERVAL}秒 ({COLLECT_INTERVAL/60}分钟)")
    print(f"启动时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    system = SARSlopeJSONLSystem()
    
    while True:
        try:
            print(f"\n{'='*60}")
            print(f"开始采集 - {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 执行采集
            success_count = system.collect_all_symbols()
            
            # 显示统计
            stats = system.get_stats()
            print(f"\n📊 统计:")
            print(f"  成功: {success_count}/27")
            print(f"  多头: {stats['bullish_count']}")
            print(f"  空头: {stats['bearish_count']}")
            
            # 每天清理一次旧数据（在凌晨2点）
            now = datetime.now(BEIJING_TZ)
            if now.hour == 2 and now.minute < 5:
                print("\n🗑️ 执行每日数据清理...")
                deleted = system.cleanup_old_data(days_to_keep=7)
                print(f"✅ 清理了 {deleted} 个旧文件")
            
            print(f"\n⏰ 下次采集: {(datetime.now(BEIJING_TZ).timestamp() + COLLECT_INTERVAL)}")
            print(f"💤 等待 {COLLECT_INTERVAL} 秒...")
            time.sleep(COLLECT_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  收到中断信号，正在停止...")
            break
        except Exception as e:
            print(f"\n❌ 采集出错: {e}")
            print(traceback.format_exc())
            print(f"💤 等待 {COLLECT_INTERVAL} 秒后重试...")
            time.sleep(COLLECT_INTERVAL)
    
    print("\n👋 SAR斜率采集守护进程已停止")

if __name__ == '__main__':
    main()
