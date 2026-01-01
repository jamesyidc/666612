#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点单实时维护守护进程 (基于Flask API)
功能：从Flask API获取实时持仓，检查是否需要维护
"""

import time
import requests
from datetime import datetime
import pytz
from anchor_maintenance_manager import AnchorMaintenanceManager

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# Flask API 配置
FLASK_API_URL = 'http://localhost:5000/api/anchor-system/current-positions'
CHECK_INTERVAL = 60  # 60秒检查一次

def get_current_positions():
    """从Flask API获取当前实盘持仓"""
    try:
        response = requests.get(f'{FLASK_API_URL}?trade_mode=real', timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Flask API返回格式: {"positions": [...]}
            if 'positions' in data:
                return data['positions']
            # 兼容其他格式
            if data.get('success'):
                return data.get('data', [])
        return []
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return []

def main():
    """主循环"""
    print("🚀 锚点单实时维护守护进程启动 (基于Flask API)")
    print(f"📊 检查间隔: {CHECK_INTERVAL}秒")
    print(f"🎯 触发条件: 亏损 ≥ 10%")
    print(f"💰 余额控制: 0.6U - 1.1U")
    print("=" * 60)
    
    manager = AnchorMaintenanceManager()
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n🔍 扫描时间: {now}")
            
            # 1. 获取当前持仓
            positions = get_current_positions()
            if not positions:
                print("⚠️  未获取到持仓数据")
                time.sleep(CHECK_INTERVAL)
                continue
            
            print(f"📊 当前持仓: {len(positions)}个")
            
            # 2. 使用AnchorMaintenanceManager检查需要维护的持仓
            maintenance_list = manager.scan_positions(positions)
            
            if not maintenance_list:
                print("✅ 扫描完成，无需维护")
            else:
                print(f"\n🚨 发现 {len(maintenance_list)} 个需要维护的持仓:")
                for m in maintenance_list:
                    print(f"   {m['inst_id']} {m['pos_side']}: 亏损{m['profit_rate']:.2f}%")
                    print(f"   触发原因: {m['trigger_reason']}")
                    
                    # 注意: 这里只是记录和显示，实际执行需要调用交易API
                    # 目前AnchorMaintenanceManager已经保存了维护日志
                    print(f"   ⚠️  维护方案已记录，需要手动或通过交易系统执行")
            
            # 3. 等待下一次检查
            print(f"\n⏳ 等待{CHECK_INTERVAL}秒后继续...\n")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n⛔ 接收到停止信号，退出...")
            break
        except Exception as e:
            print(f"\n❌ 运行时错误: {e}")
            print(f"⏳ {CHECK_INTERVAL}秒后重试...\n")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
