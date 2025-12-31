#!/usr/bin/env python3
"""
子账户超级维护守护进程
功能：监控子账户持仓，收益率跌破-10%时自动维护
"""

import json
import time
import requests
import hmac
import base64
from datetime import datetime, timezone, timedelta
import traceback

# 配置
CHECK_INTERVAL = 30  # 30秒检查一次
TRIGGER_RATE = -10  # 触发维护的收益率阈值
MAINTENANCE_AMOUNT = 20  # 维护金额20U（进一步降低以确保成功）
MAX_MAINTENANCE_COUNT = 3  # 最大维护次数
STOP_LOSS_RATE = -20  # 止损线

# 跳过列表：这些币种暂时不维护（已知问题币种）
SKIP_INSTRUMENTS = ['STX-USDT-SWAP']  # STX存在OKEx 51008错误，暂时跳过

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def get_china_today():
    """获取北京时间的今天日期"""
    return get_china_time().strftime('%Y-%m-%d')

def log(msg):
    """打印日志"""
    print(f"[{get_china_time().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_sub_account_config():
    """加载子账户配置"""
    try:
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取第一个启用的子账户
        for acc in config['sub_accounts']:
            if acc.get('enabled'):
                return acc
        return None
    except Exception as e:
        log(f"❌ 加载子账户配置失败: {e}")
        return None

def get_maintenance_count(account_name, inst_id, pos_side):
    """获取维护次数（不再按日期重置）"""
    try:
        with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{account_name}_{inst_id}_{pos_side}"
        if key in data:
            record = data[key]
            return record.get('count', 0)
        return 0
    except FileNotFoundError:
        return 0
    except Exception as e:
        log(f"⚠️ 读取维护次数失败: {e}")
        return 0

def check_maintenance_interval(account_name, inst_id, pos_side, min_interval_minutes=15):
    """检查距离上次维护是否已经过了足够的时间（默认15分钟）"""
    try:
        with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{account_name}_{inst_id}_{pos_side}"
        if key not in data:
            return True  # 没有维护记录，允许维护
        
        last_maintenance_str = data[key].get('last_maintenance')
        if not last_maintenance_str:
            return True  # 没有上次维护时间，允许维护
        
        # 解析上次维护时间
        last_maintenance = datetime.strptime(last_maintenance_str, '%Y-%m-%d %H:%M:%S')
        last_maintenance = last_maintenance.replace(tzinfo=timezone(timedelta(hours=8)))
        
        # 计算时间差
        now = get_china_time()
        time_diff = (now - last_maintenance).total_seconds() / 60  # 转换为分钟
        
        if time_diff < min_interval_minutes:
            remaining = min_interval_minutes - time_diff
            log(f"    ⏰ 距离上次维护仅 {time_diff:.1f} 分钟，需等待 {remaining:.1f} 分钟")
            return False
        
        return True
    except FileNotFoundError:
        return True  # 文件不存在，允许维护
    except Exception as e:
        log(f"⚠️ 检查维护间隔失败: {e}")
        return True  # 出错时允许维护，避免影响正常流程

def update_maintenance_count(account_name, inst_id, pos_side):
    """更新维护次数+1（不再按日期重置）"""
    try:
        try:
            with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        
        key = f"{account_name}_{inst_id}_{pos_side}"
        now = get_china_time().strftime('%Y-%m-%d %H:%M:%S')
        
        if key not in data:
            data[key] = {
                'count': 1,
                'last_maintenance': now
            }
        else:
            record = data[key]
            record['count'] = record.get('count', 0) + 1
            record['last_maintenance'] = now
        
        with open('sub_account_maintenance.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return data[key]['count']
    except Exception as e:
        log(f"❌ 更新维护次数失败: {e}")
        return 0

def get_sub_account_positions(account_name):
    """获取子账户持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            # 返回该子账户的持仓
            return [pos for pos in data['positions'] if pos['account_name'] == account_name]
        return []
    except Exception as e:
        log(f"❌ 获取子账户持仓失败: {e}")
        return []

def execute_super_maintenance(account_config, inst_id, pos_side, pos_size, profit_rate):
    """执行超级维护"""
    try:
        account_name = account_config['account_name']
        
        # 获取当前维护次数
        current_count = get_maintenance_count(account_name, inst_id, pos_side)
        
        # 根据维护次数确定参数（进一步降低维护金额）
        if current_count == 0:
            # 第1次维护：买入20U，留10U
            maintenance_amount = 20
            target_margin = 10
        elif current_count == 1:
            # 第2次维护：买入20U，留20U
            maintenance_amount = 20
            target_margin = 20
        elif current_count == 2:
            # 第3次维护：买入50U，留20U，设置-20%止损
            maintenance_amount = 50
            target_margin = 20
        else:
            log(f"⚠️  今日维护次数已达上限: {current_count}/{MAX_MAINTENANCE_COUNT}")
            return False
        
        log(f"🔧 执行超级维护: {inst_id} {pos_side}")
        log(f"   当前收益率: {profit_rate:.2f}%")
        log(f"   当前维护次数: {current_count}/{MAX_MAINTENANCE_COUNT}")
        log(f"   本次维护金额: {maintenance_amount}U")
        log(f"   本次目标保证金: {target_margin}U")
        
        # 调用后端API执行维护
        response = requests.post('http://localhost:5000/api/anchor/maintain-sub-account', 
                                json={
                                    'account_name': account_name,
                                    'inst_id': inst_id,
                                    'pos_side': pos_side,
                                    'pos_size': pos_size,
                                    'amount': maintenance_amount,
                                    'target_margin': target_margin,
                                    'maintenance_count': current_count
                                },
                                timeout=120)
        
        result = response.json()
        
        if result.get('success'):
            # API已经更新了维护次数，从响应中获取
            data = result.get('data', {})
            new_count = data.get('today_count', current_count + 1)
            
            log(f"✅ 超级维护成功!")
            log(f"   开仓订单ID: {data.get('open_order_id', 'N/A')}")
            log(f"   平仓订单ID: {data.get('close_order_id', 'N/A')}")
            log(f"   今日维护次数: {new_count}/{MAX_MAINTENANCE_COUNT}")
            
            # 第3次维护后设置止损
            if new_count == 3:
                log(f"⚠️  已完成第3次维护，设置-20%止损线...")
                # TODO: 调用设置止损API
            
            # 如果维护次数=2，设置止损
            if new_count == 2:
                log(f"⚠️ 维护次数达到2次，建议设置-20%止损线")
            elif new_count >= MAX_MAINTENANCE_COUNT:
                log(f"🚫 维护次数达到上限({MAX_MAINTENANCE_COUNT}次)，停止超级维护")
            
            return True
        else:
            log(f"❌ 超级维护失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        log(f"❌ 超级维护异常: {e}")
        log(traceback.format_exc())
        return False

def main_loop():
    """主循环"""
    log("🚀 子账户超级维护守护进程启动")
    log(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    log(f"📉 触发阈值: 收益率≤{TRIGGER_RATE}%")
    log(f"💰 维护金额: {MAINTENANCE_AMOUNT}U")
    log(f"🔢 最大维护次数: {MAX_MAINTENANCE_COUNT}次")
    log(f"🛑 止损线: {STOP_LOSS_RATE}%")
    log(f"⏰ 维护间隔: 同一币种两次维护之间需间隔15分钟")
    
    while True:
        try:
            # 加载子账户配置
            sub_account = load_sub_account_config()
            if not sub_account:
                log("❌ 没有启用的子账户，等待30秒后重试")
                time.sleep(CHECK_INTERVAL)
                continue
            
            account_name = sub_account['account_name']
            log(f"\n{'='*60}")
            log(f"🔍 检查账户: {account_name}")
            
            # 获取子账户持仓
            positions = get_sub_account_positions(account_name)
            log(f"📊 持仓数量: {len(positions)}")
            
            if not positions:
                log("✅ 无持仓")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 检查每个持仓
            for pos in positions:
                inst_id = pos['inst_id']
                pos_side = pos['pos_side']
                profit_rate = pos.get('profit_rate', 0)
                pos_size = pos.get('pos_size', 0)
                
                log(f"  检查 {inst_id} {pos_side}: 收益率 {profit_rate:.2f}%")
                
                # 跳过黑名单中的币种
                if inst_id in SKIP_INSTRUMENTS:
                    log(f"    ⏭️  已跳过（在黑名单中）")
                    continue
                
                # 检查是否触发准备维护或立即维护
                should_maintain = False
                prepare_maintain = False
                
                if profit_rate <= TRIGGER_RATE:  # <= -10%
                    should_maintain = True
                    log(f"    ⚠️  收益率跌破维护阈值{TRIGGER_RATE}%")
                elif profit_rate <= -8:  # <= -8%
                    prepare_maintain = True
                    log(f"    📢 收益率跌破准备维护阈值-8%")
                
                if should_maintain:
                    # 获取今日维护次数
                    count = get_maintenance_count(account_name, inst_id, pos_side)
                    log(f"    今日维护{count}/{MAX_MAINTENANCE_COUNT}次")
                    
                    # 检查是否达到上限
                    if count >= MAX_MAINTENANCE_COUNT:
                        log(f"    🚫 维护次数已达上限，跳过")
                        continue
                    
                    # 检查维护间隔（同一个币两次维护之间需要间隔15分钟）
                    if not check_maintenance_interval(account_name, inst_id, pos_side, min_interval_minutes=15):
                        log(f"    ⏱️  维护间隔不足15分钟，跳过")
                        continue
                    
                    # 检查是否达到止损线（维护次数=2时）
                    if count == 2 and profit_rate <= STOP_LOSS_RATE:
                        log(f"    🛑 触发止损线({STOP_LOSS_RATE}%)，建议手动平仓")
                        continue
                    
                    # 执行超级维护
                    success = execute_super_maintenance(sub_account, inst_id, pos_side, pos_size, profit_rate)
                    
                    if success:
                        log(f"    ✅ 超级维护完成")
                        # 维护成功后等待一段时间
                        time.sleep(10)
                    else:
                        log(f"    ❌ 超级维护失败")
                else:
                    log(f"    ✓ 收益率正常")
            
            log(f"{'='*60}\n")
            
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())
        
        # 等待下一次检查
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main_loop()
