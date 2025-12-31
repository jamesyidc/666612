#!/usr/bin/env python3
"""
自动维护检查器
功能：
1. 检查多单/空单收益率是否达到-10%
2. 检查锚点单保证金是否在0.6u-1u之间
3. 自动执行维护操作
"""

import requests
import json
import time
from datetime import datetime
import traceback

BASE_URL = 'http://localhost:5000'

def log(message):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_maintenance_count_today(inst_id, pos_side):
    """获取今天的维护次数（普通维护+1，超级维护+1）"""
    try:
        response = requests.get(f"{BASE_URL}/api/anchor/maintenance-stats", timeout=5)
        data = response.json()
        if data.get('success'):
            stats = data.get('stats', {})
            key = f"{inst_id}:{pos_side}"
            return stats.get(key, 0)
        return 0
    except Exception as e:
        log(f"❌ 获取维护次数失败: {e}")
        return 0

def get_main_account_maintenance_count(inst_id, pos_side):
    """获取主账户今日超级维护次数"""
    try:
        with open('main_account_maintenance.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{inst_id}_{pos_side}"
        if key in data:
            record = data[key]
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            if record.get('date') == today:
                return record.get('count', 0)
        return 0
    except FileNotFoundError:
        return 0
    except Exception as e:
        log(f"⚠️ 读取主账户维护次数失败: {e}")
        return 0

def update_main_account_maintenance_count(inst_id, pos_side):
    """更新主账户维护次数+1"""
    try:
        try:
            with open('main_account_maintenance.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        
        key = f"{inst_id}_{pos_side}"
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if key not in data:
            data[key] = {
                'count': 1,
                'date': today,
                'last_maintenance': now
            }
        else:
            record = data[key]
            if record.get('date') == today:
                record['count'] = record.get('count', 0) + 1
            else:
                record['count'] = 1
                record['date'] = today
            record['last_maintenance'] = now
        
        with open('main_account_maintenance.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return data[key]['count']
    except Exception as e:
        log(f"❌ 更新主账户维护次数失败: {e}")
        return 0

def get_config():
    """获取自动维护配置"""
    try:
        response = requests.get(f"{BASE_URL}/api/anchor/auto-maintenance-config", timeout=5)
        data = response.json()
        if data.get('success'):
            return data.get('config', {})
        return None
    except Exception as e:
        log(f"❌ 获取配置失败: {e}")
        return None

def get_positions():
    """获取当前持仓"""
    try:
        response = requests.get(f"{BASE_URL}/api/anchor-system/current-positions?trade_mode=real", timeout=10)
        data = response.json()
        if data.get('success'):
            return data.get('positions', [])
        return []
    except Exception as e:
        log(f"❌ 获取持仓失败: {e}")
        return []

def maintain_anchor(inst_id, pos_side, pos_size):
    """执行维护锚点单（自动维护模式，会调整保证金）"""
    try:
        log(f"🔧 开始自动维护: {inst_id} {pos_side} {pos_size}")
        response = requests.post(
            f"{BASE_URL}/api/anchor/maintain-anchor",
            json={
                'inst_id': inst_id,
                'pos_side': pos_side,
                'pos_size': pos_size,
                'auto_adjust': True  # 自动维护模式，启用保证金自动调整
            },
            timeout=30
        )
        data = response.json()
        if data.get('success'):
            log(f"✅ 自动维护成功: {inst_id}")
            if data.get('data', {}).get('adjustment_order_id'):
                log(f"   📊 已自动调整保证金，平仓数量: {data['data'].get('adjustment_size', 0)}")
            return True
        else:
            log(f"❌ 自动维护失败: {data.get('message')}")
            return False
    except Exception as e:
        log(f"❌ 自动维护操作异常: {e}")
        return False

def super_maintain_anchor(inst_id, pos_side, pos_size):
    """执行主账户超级维护：每次100U留10U，共2次"""
    try:
        # 获取今日超级维护次数（独立计数）
        current_count = get_main_account_maintenance_count(inst_id, pos_side)
        
        # 超级维护固定参数：每次100U留10U
        if current_count >= 2:
            log(f"⚠️  主账户今日超级维护次数已达上限: {current_count}/2")
            return False
        
        maintenance_amount = 100  # 固定100U
        target_margin = 10        # 固定留10U
        
        log(f"🚀 开始超级维护: {inst_id} {pos_side} {pos_size}")
        log(f"   当前超级维护次数: {current_count}/2")
        log(f"   本次维护金额: {maintenance_amount}U")
        log(f"   本次目标保证金: {target_margin}U")
        
        response = requests.post(
            f"{BASE_URL}/api/anchor/super-maintain-anchor",
            json={
                'inst_id': inst_id,
                'pos_side': pos_side,
                'current_pos_size': pos_size,
                'maintenance_amount': maintenance_amount,
                'target_margin': target_margin
            },
            timeout=30
        )
        data = response.json()
        if data.get('success'):
            # 更新维护次数
            new_count = update_main_account_maintenance_count(inst_id, pos_side)
            
            log(f"✅ 超级维护成功: {inst_id}")
            log(f"   📊 买入: {data['data'].get('buy_size', 0)}, 卖出: {data['data'].get('sell_size', 0)}, 保留: {data['data'].get('keep_size', 0)}")
            log(f"   今日超级维护次数: {new_count}/2")
            
            if new_count >= 2:
                log(f"⚠️  已完成全部超级维护(2次)，已达上限")
            
            return True
        else:
            log(f"❌ 超级维护失败: {data.get('message')}")
            return False
    except Exception as e:
        log(f"❌ 超级维护操作异常: {e}")
        return False

def adjust_margin(inst_id, pos_side, margin, target_margin=0.8):
    """调整保证金到目标值（通过部分平仓）"""
    try:
        log(f"💰 调整保证金: {inst_id} {pos_side} 当前:{margin:.4f}u 目标:{target_margin}u")
        
        # 获取持仓详情
        positions = get_positions()
        target_pos = None
        for pos in positions:
            if pos['inst_id'] == inst_id and pos['pos_side'] == pos_side:
                target_pos = pos
                break
        
        if not target_pos:
            log(f"❌ 未找到持仓: {inst_id} {pos_side}")
            return False
        
        # 计算需要平仓的比例
        # margin = pos_size * mark_price / lever
        # target_margin = new_pos_size * mark_price / lever
        # new_pos_size = target_margin * lever / mark_price
        
        pos_size = target_pos['pos_size']
        mark_price = target_pos['mark_price']
        lever = target_pos['lever']
        
        # 计算目标持仓量
        target_pos_size = (target_margin * lever) / mark_price
        
        # 计算需要平仓的数量
        close_size = pos_size - target_pos_size
        
        if close_size <= 0:
            log(f"⚠️  不需要平仓: 当前持仓量已低于目标")
            return False
        
        log(f"📉 计划平仓: {close_size:.4f} (保留: {target_pos_size:.4f})")
        
        # TODO: 调用OKEx API执行部分平仓
        # 这里需要实现部分平仓逻辑
        
        return True
    except Exception as e:
        log(f"❌ 调整保证金失败: {e}")
        return False

def check_and_maintain():
    """检查并执行自动维护"""
    try:
        # 获取配置
        config = get_config()
        if not config:
            log("⚠️  无法获取配置，跳过检查")
            return
        
        auto_maintain_long = config.get('auto_maintain_long_enabled', False)
        auto_maintain_short = config.get('auto_maintain_short_enabled', False)
        super_maintain_long = config.get('super_maintain_long_enabled', False)
        super_maintain_short = config.get('super_maintain_short_enabled', False)
        loss_threshold = config.get('loss_threshold', -10)
        margin_min = config.get('margin_min', 0.6)
        margin_max = config.get('margin_max', 1.0)
        
        log(f"📊 配置: 多单自动维护={auto_maintain_long}, 空单自动维护={auto_maintain_short}")
        log(f"🚀 配置: 多单超级维护={super_maintain_long}, 空单超级维护={super_maintain_short}")
        log(f"💰 阈值={loss_threshold}%, 保证金范围: {margin_min}u - {margin_max}u")
        
        # 获取持仓
        positions = get_positions()
        log(f"📦 当前持仓数量: {len(positions)}")
        
        for pos in positions:
            inst_id = pos['inst_id']
            pos_side = pos['pos_side']
            pos_size = pos['pos_size']
            profit_rate = pos['profit_rate']
            margin = pos['margin']
            is_anchor = pos.get('is_anchor', 0)
            
            # 跳过非锚点单（is_anchor=0）的持仓，除非它们满足自动维护条件
            # 如果是锚点单，继续检查
            # 如果不是锚点单，只有在满足维护条件时才处理
            
            log(f"🔍 检查: {inst_id} {pos_side} 收益率={profit_rate:.2f}% 保证金={margin:.4f}u {'[锚点单]' if is_anchor else '[普通单]'}")
            
            # 检查持仓保证金是否小于2U
            if margin >= 2.0:
                log(f"⚠️  保证金 >= 2U，不自动维护: {margin:.4f}u")
                continue
            
            # 检查1：收益率是否达到维护阈值
            should_maintain = False
            prepare_maintain = False  # 准备维护状态
            
            # 判断是否需要准备维护（-8%）或立即维护（-10%）
            if pos_side == 'long' and auto_maintain_long:
                if profit_rate <= loss_threshold:  # <= -10%
                    log(f"⚠️  多单收益率达到维护阈值: {profit_rate:.2f}% <= {loss_threshold}%")
                    should_maintain = True
                elif profit_rate <= -8:  # <= -8%
                    log(f"📢 多单收益率达到准备维护阈值: {profit_rate:.2f}% <= -8%")
                    prepare_maintain = True
            elif pos_side == 'short' and auto_maintain_short:
                if profit_rate <= loss_threshold:  # <= -10%
                    log(f"⚠️  空单收益率达到维护阈值: {profit_rate:.2f}% <= {loss_threshold}%")
                    should_maintain = True
                elif profit_rate <= -8:  # <= -8%
                    log(f"📢 空单收益率达到准备维护阈值: {profit_rate:.2f}% <= -8%")
                    prepare_maintain = True
            
            if should_maintain:
                # 获取今天的总维护次数（包括普通维护和超级维护）
                today_count = get_maintenance_count_today(inst_id, pos_side)
                log(f"📊 {inst_id} {pos_side} 今日已维护次数: {today_count}/5")
                
                # 判断使用哪种维护方式
                if today_count >= 5:
                    log(f"🛑 已达到每日维护上限(5次)，停止维护")
                    continue
                elif today_count >= 3:
                    # 第4次和第5次使用超级维护（每次100U留10U）
                    should_super = False
                    if pos_side == 'long' and super_maintain_long:
                        log(f"🚀 多单维护次数={today_count}，触发超级维护（第{today_count + 1}次）")
                        should_super = True
                    elif pos_side == 'short' and super_maintain_short:
                        log(f"🚀 空单维护次数={today_count}，触发超级维护（第{today_count + 1}次）")
                        should_super = True
                    
                    if should_super:
                        # 执行超级维护（计数+1）
                        success = super_maintain_anchor(inst_id, pos_side, pos_size)
                        if success:
                            log(f"✅ 超级维护完成: {inst_id} (今日第{today_count + 1}次)")
                            time.sleep(2)
                    else:
                        log(f"⚠️  超级维护开关未开启，跳过")
                else:
                    # 前3次使用普通维护（计数+1）
                    success = maintain_anchor(inst_id, pos_side, pos_size)
                    if success:
                        log(f"✅ 自动维护完成: {inst_id} (今日第{today_count + 1}次)")
                        time.sleep(2)
            
            # 检查2：保证金是否超出范围
            if margin > margin_max:
                log(f"⚠️  保证金超出上限: {margin:.4f}u > {margin_max}u")
                # 部分平仓，降低保证金到0.8u
                adjust_margin(inst_id, pos_side, margin, target_margin=0.8)
            elif margin < margin_min and margin > 0:
                log(f"⚠️  保证金低于下限: {margin:.4f}u < {margin_min}u")
                # 这种情况通常不需要处理，因为维护操作会增加持仓
        
        log("✅ 检查完成")
        
    except Exception as e:
        log(f"❌ 检查过程异常: {e}")
        log(traceback.format_exc())

if __name__ == '__main__':
    log("🚀 自动维护检查器启动")
    
    # 持续运行，每30秒检查一次
    while True:
        try:
            check_and_maintain()
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
        
        # 等待30秒
        time.sleep(30)
