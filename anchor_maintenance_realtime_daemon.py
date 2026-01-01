#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点单实时维护守护进程 (基于Flask API)
功能：从Flask API获取实时持仓，检查是否需要维护
"""

import time
import requests
import json
from datetime import datetime, timedelta
import pytz
from anchor_maintenance_manager import AnchorMaintenanceManager
from maintenance_trade_executor import MaintenanceTradeExecutor

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# Flask API 配置
FLASK_API_URL = 'http://localhost:5000/api/anchor-system/current-positions'
AUTO_MAINTENANCE_CONFIG_PATH = '/home/user/webapp/auto_maintenance_config.json'
CHECK_INTERVAL = 60  # 60秒检查一次

# 自动执行配置
AUTO_EXECUTE_ENABLED = True  # 是否自动执行交易（True=实盘自动执行，False=仅检测记录）

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

def load_config():
    """加载自动维护配置"""
    try:
        with open(AUTO_MAINTENANCE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except:
        return {
            'auto_maintain_long_enabled': False,
            'auto_maintain_short_enabled': False
        }

def update_maintenance_count(inst_id, pos_side):
    """更新维护计数"""
    try:
        maintenance_file = '/home/user/webapp/anchor_maintenance_records.json'
        now_beijing = datetime.now(BEIJING_TZ)
        today_date = now_beijing.strftime('%Y-%m-%d')
        
        # 读取现有记录
        try:
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            records = {}
        
        # 构建记录键
        record_key = f"{inst_id}_{pos_side}"
        
        if record_key not in records:
            records[record_key] = {
                'inst_id': inst_id,
                'pos_side': pos_side,
                'today_count': 1,
                'total_count': 1,
                'last_maintenance': now_beijing.strftime('%Y-%m-%d %H:%M:%S'),
                'date': today_date
            }
        else:
            record = records[record_key]
            # 检查是否是同一天
            if record.get('date') == today_date:
                record['today_count'] = record.get('today_count', 0) + 1
            else:
                # 新的一天，重置today_count
                record['today_count'] = 1
                record['date'] = today_date
            
            record['total_count'] = record.get('total_count', 0) + 1
            record['last_maintenance'] = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存更新后的记录
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"   📊 维护计数已更新: 今日{records[record_key]['today_count']}次，总计{records[record_key]['total_count']}次")
        
    except Exception as e:
        print(f"   ⚠️  更新维护计数失败: {e}")

def check_maintenance_interval(inst_id, pos_side):
    """检查15分钟维护间隔"""
    try:
        maintenance_file = '/home/user/webapp/anchor_maintenance_records.json'
        now_beijing = datetime.now(BEIJING_TZ)
        
        # 读取现有记录
        try:
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 没有记录，允许执行
            return True
        
        record_key = f"{inst_id}_{pos_side}"
        if record_key not in records:
            # 没有该币种的记录，允许执行
            return True
        
        last_maintenance_str = records[record_key].get('last_maintenance', '')
        if not last_maintenance_str:
            return True
        
        try:
            last_time = datetime.strptime(last_maintenance_str, '%Y-%m-%d %H:%M:%S')
            last_time = BEIJING_TZ.localize(last_time)
            time_diff = (now_beijing - last_time).total_seconds() / 60
            
            if time_diff < 15:
                print(f"   ⚠️  距离上次维护仅{time_diff:.1f}分钟，需要至少15分钟间隔")
                next_time = (last_time + timedelta(minutes=15)).strftime('%H:%M:%S')
                print(f"   ⏰ 下次可维护时间: {next_time}")
                return False
        except Exception as e:
            print(f"   ⚠️  解析上次维护时间失败: {e}")
            return True
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  检查维护间隔失败: {e}")
        return True  # 出错时允许执行

def main():
    """主循环"""
    print("🚀 锚点单实时维护守护进程启动 (基于Flask API)")
    print(f"📊 检查间隔: {CHECK_INTERVAL}秒")
    print(f"🎯 触发条件: 亏损 ≥ 10%")
    print(f"💰 余额控制: 0.6U - 1.1U")
    print(f"⚡ 自动执行: {'开启 (实盘交易)' if AUTO_EXECUTE_ENABLED else '关闭 (仅检测记录)'}")
    print("=" * 60)
    
    manager = AnchorMaintenanceManager()
    executor = MaintenanceTradeExecutor(dry_run=not AUTO_EXECUTE_ENABLED)
    
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
                
                # 加载配置
                config = load_config()
                
                for m in maintenance_list:
                    print(f"\n{'=' * 60}")
                    print(f"📍 {m['inst_id']} {m['pos_side']}: 亏损{m['profit_rate']:.2f}%")
                    print(f"   触发原因: {m['trigger_reason']}")
                    
                    # 检查该方向是否开启自动维护
                    pos_side = m['pos_side']
                    auto_enabled = False
                    
                    if pos_side == 'long' and config.get('auto_maintain_long_enabled'):
                        auto_enabled = True
                    elif pos_side == 'short' and config.get('auto_maintain_short_enabled'):
                        auto_enabled = True
                    
                    if not auto_enabled:
                        print(f"   ⚠️  {pos_side} 方向自动维护未开启，跳过执行")
                        continue
                    
                    if not AUTO_EXECUTE_ENABLED:
                        print(f"   ⚠️  自动执行功能未开启，仅记录维护计划")
                        continue
                    
                    # 自动执行维护
                    print(f"   🤖 自动执行维护...")
                    
                    try:
                        # 检查15分钟维护间隔
                        if not check_maintenance_interval(m['inst_id'], m['pos_side']):
                            continue
                        
                        # 找到对应的持仓对象
                        position = None
                        for p in positions:
                            if (p.get('inst_id') == m['inst_id'] and 
                                p.get('pos_side') == m['pos_side']):
                                position = p
                                break
                        
                        if not position:
                            print(f"   ❌ 未找到对应持仓，跳过")
                            continue
                        
                        # 执行维护计划
                        maintenance_plan = m.get('maintenance_plan', {})
                        result = executor.execute_maintenance_plan(position, maintenance_plan)
                        
                        if result['success']:
                            print(f"   ✅ 维护执行成功!")
                            print(f"      补仓订单: {result['step1_result'].get('order_id', 'N/A')}")
                            print(f"      平仓订单: {result['step2_result'].get('order_id', 'N/A')}")
                            
                            # 更新维护计数
                            update_maintenance_count(m['inst_id'], m['pos_side'])
                        else:
                            print(f"   ❌ 维护执行失败: {result.get('error')}")
                        
                        # 等待5秒再处理下一个
                        if len(maintenance_list) > 1:
                            print(f"   ⏳ 等待5秒后处理下一个持仓...")
                            time.sleep(5)
                            
                    except Exception as e:
                        print(f"   ❌ 维护执行异常: {e}")
                        import traceback
                        traceback.print_exc()
            
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
