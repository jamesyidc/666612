#!/usr/bin/env python3
"""
主账号止盈守护进程
功能：
1. 多单止盈规则（保证金>1U才执行）：
   - 盈利25% → 止盈剩余30%
   - 盈利35% → 止盈剩余50%
   - 盈利50% → 止盈剩余50%
   - 同一交易对空单亏损 → 保留1U，其他全止盈
   
2. 空单止盈规则（保证金>1U才执行）：
   - 盈利35% → 止盈剩余30%
   - 盈利45% → 止盈剩余50%
   - 盈利55% → 止盈剩余50%
   - 同一交易对多单亏损 → 保留1U，其他全止盈
"""

import json
import time
import requests
from datetime import datetime, timezone, timedelta
import traceback

# 配置
CHECK_INTERVAL = 10  # 10秒检查一次
MIN_MARGIN = 1.0  # 最小保证金要求1U
KEEP_MARGIN = 1.0  # 对冲平仓时保留1U底仓

# 多单止盈规则（按剩余仓位计算，递进式）
LONG_RULES = [
    {'profit': 25, 'close_percent': 30},  # 第1档：盈利25% → 止盈30%（剩余70%）
    {'profit': 35, 'close_percent': 50},  # 第2档：盈利35% → 再止盈剩余50%（剩余35%）
    {'profit': 50, 'close_percent': 50},  # 第3档：盈利50% → 再止盈剩余50%（剩余17.5%）
]

# 空单止盈规则（按剩余仓位计算，递进式）
SHORT_RULES = [
    {'profit': 35, 'close_percent': 30},  # 第1档：盈利35% → 止盈30%（剩余70%）
    {'profit': 45, 'close_percent': 50},  # 第2档：盈利45% → 再止盈剩余50%（剩余35%）
    {'profit': 55, 'close_percent': 50},  # 第3档：盈利55% → 再止盈剩余50%（剩余17.5%）
]

# 止盈记录文件
TAKE_PROFIT_RECORDS_FILE = 'main_account_take_profit_records.json'
# 持仓止盈状态文件（记录每个持仓触发过哪些阈值）
POSITION_STATE_FILE = 'main_account_position_state.json'

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def get_china_today():
    """获取北京时间的今天日期"""
    return get_china_time().strftime('%Y-%m-%d')

def log(msg):
    """打印日志"""
    print(f"[{get_china_time().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_position_states():
    """加载持仓止盈状态"""
    try:
        with open(POSITION_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        log(f"⚠️ 加载持仓状态失败: {e}")
        return {}

def save_position_states(states):
    """保存持仓止盈状态"""
    try:
        with open(POSITION_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(states, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        log(f"❌ 保存持仓状态失败: {e}")
        return False

def get_position_key(inst_id, pos_side):
    """生成持仓唯一键"""
    return f"{inst_id}_{pos_side}"

def clean_old_states(states, positions):
    """清理不存在的持仓状态"""
    active_keys = {get_position_key(p['inst_id'], p['pos_side']) for p in positions}
    return {k: v for k, v in states.items() if k in active_keys}

def get_main_account_positions():
    """获取主账户持仓"""
    try:
        response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            return data['positions']
        return []
    except Exception as e:
        log(f"❌ 获取主账户持仓失败: {e}")
        return []

def save_take_profit_record(inst_id, pos_side, profit_rate, close_percent, reason):
    """保存止盈记录"""
    try:
        try:
            with open(TAKE_PROFIT_RECORDS_FILE, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except FileNotFoundError:
            records = []
        
        record = {
            'inst_id': inst_id,
            'pos_side': pos_side,
            'profit_rate': profit_rate,
            'close_percent': close_percent,
            'reason': reason,
            'timestamp': get_china_time().strftime('%Y-%m-%d %H:%M:%S'),
            'date': get_china_today()
        }
        
        records.append(record)
        
        with open(TAKE_PROFIT_RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        log(f"❌ 保存止盈记录失败: {e}")
        return False

def calculate_keep_size(margin, mark_price, lever):
    """计算需要保留的仓位数量（保留1U保证金）"""
    # 1U保证金对应的持仓名义价值
    keep_notional = KEEP_MARGIN * lever
    # 持仓数量 = 名义价值 / 价格
    keep_size = keep_notional / mark_price
    return keep_size

def execute_take_profit(inst_id, pos_side, pos_size, margin, profit_rate, close_percent, reason, mark_price, lever):
    """执行止盈操作"""
    try:
        # 计算止盈数量
        if close_percent >= 100:
            # 对冲平仓：保留1U
            keep_size = calculate_keep_size(margin, mark_price, lever)
            close_size = pos_size - keep_size
            actual_close_percent = (close_size / pos_size) * 100 if pos_size > 0 else 0
        else:
            # 按百分比止盈
            close_size = pos_size * (close_percent / 100)
            actual_close_percent = close_percent
        
        # 确保close_size为正数且不超过持仓
        close_size = max(0, min(close_size, pos_size))
        
        if close_size <= 0:
            log(f"⚠️  {inst_id} {pos_side}: 计算的平仓数量<=0，跳过")
            return False
        
        # 对于小数位数，向下取整（避免超出持仓）
        # BCH等币种是整数，FIL等是小数
        if close_size >= 1:
            close_size = int(close_size)
        else:
            close_size = round(close_size, 8)  # 保留8位小数
        
        log(f"🎯 执行止盈: {inst_id} {pos_side}")
        log(f"   当前收益率: {profit_rate:.2f}%")
        log(f"   当前保证金: {margin:.2f}U")
        log(f"   持仓数量: {pos_size}")
        log(f"   止盈比例: {actual_close_percent:.1f}%")
        log(f"   止盈数量: {close_size}")
        log(f"   止盈原因: {reason}")
        
        # 调用后端API执行止盈
        response = requests.post('http://localhost:5000/api/anchor/close-position',
                                json={
                                    'inst_id': inst_id,
                                    'pos_side': pos_side,
                                    'close_size': close_size,
                                    'reason': reason,
                                    'trade_mode': 'real'
                                },
                                timeout=30)
        
        result = response.json()
        
        if result.get('success'):
            # 保存止盈记录
            save_take_profit_record(inst_id, pos_side, profit_rate, actual_close_percent, reason)
            
            log(f"✅ 止盈成功!")
            log(f"   平仓订单ID: {result.get('order_id', 'N/A')}")
            log(f"   平仓数量: {close_size}")
            log(f"   剩余持仓: {pos_size - close_size}")
            
            return True
        else:
            log(f"❌ 止盈失败: {result.get('message', '未知错误')}")
            return False
            
    except Exception as e:
        log(f"❌ 止盈异常: {e}")
        log(traceback.format_exc())
        return False

def check_profit_rules(positions, states):
    """检查盈利规则触发（分档递进式止盈）"""
    log(f"  🔍 检查盈利规则")
    
    for pos in positions:
        inst_id = pos['inst_id']
        pos_side = pos['pos_side']
        profit_rate = pos.get('profit_rate', 0)
        pos_size = pos.get('pos_size', 0)
        margin = pos.get('margin', 0)
        mark_price = pos.get('mark_price', 0)
        lever = int(pos.get('leverage', 10))
        
        # 检查最小保证金要求
        if margin <= MIN_MARGIN:
            log(f"    ⊘ {inst_id} {pos_side}: 保证金{margin:.2f}U <= {MIN_MARGIN}U，跳过")
            continue
        
        # 根据方向选择规则
        rules = LONG_RULES if pos_side == 'long' else SHORT_RULES
        
        # 获取持仓状态
        pos_key = get_position_key(inst_id, pos_side)
        if pos_key not in states:
            states[pos_key] = {'triggered_levels': [], 'last_update': get_china_today()}
        
        pos_state = states[pos_key]
        triggered_levels = pos_state.get('triggered_levels', [])
        
        # 从低到高顺序检查规则（递进式止盈）
        triggered = False
        for rule in rules:
            profit_threshold = rule['profit']
            
            # 如果这个阈值已经触发过，跳过
            if profit_threshold in triggered_levels:
                continue
            
            if profit_rate >= profit_threshold:
                log(f"    ⚠️  {inst_id} {pos_side} 盈利{profit_rate:.2f}% >= {profit_threshold}%，触发第{len(triggered_levels)+1}档止盈")
                
                success = execute_take_profit(
                    inst_id, pos_side, pos_size, margin, profit_rate,
                    rule['close_percent'],
                    f"第{len(triggered_levels)+1}档：盈利{profit_rate:.1f}%触发，止盈剩余{rule['close_percent']}%",
                    mark_price, lever
                )
                
                if success:
                    # 记录已触发的阈值
                    triggered_levels.append(profit_threshold)
                    pos_state['triggered_levels'] = triggered_levels
                    pos_state['last_update'] = get_china_today()
                    states[pos_key] = pos_state
                    save_position_states(states)
                    
                    log(f"    ✅ 第{len(triggered_levels)}档止盈完成，已触发档位: {triggered_levels}")
                    time.sleep(3)  # 等待3秒
                else:
                    log(f"    ❌ 止盈失败")
                
                triggered = True
                break
        
        if not triggered:
            # 找到下一个未触发的阈值
            next_threshold = None
            for rule in rules:
                if rule['profit'] not in triggered_levels:
                    next_threshold = rule['profit']
                    break
            
            if next_threshold:
                triggered_info = f"已触发{len(triggered_levels)}档" if triggered_levels else "未触发"
                log(f"    ✓ {inst_id} {pos_side} 盈利{profit_rate:.2f}%（{triggered_info}），下一阈值{next_threshold}%")
            else:
                log(f"    ✓ {inst_id} {pos_side} 盈利{profit_rate:.2f}%，所有档位已触发")

def check_hedge_loss(positions):
    """检查对冲亏损规则"""
    log(f"  🔍 检查对冲亏损规则")
    
    # 构建持仓字典：{inst_id: {pos_side: position}}
    pos_dict = {}
    for pos in positions:
        inst_id = pos['inst_id']
        pos_side = pos['pos_side']
        
        if inst_id not in pos_dict:
            pos_dict[inst_id] = {}
        pos_dict[inst_id][pos_side] = pos
    
    # 检查每个交易对
    for inst_id, sides in pos_dict.items():
        # 检查是否有多空双向持仓
        if 'long' in sides and 'short' in sides:
            long_pos = sides['long']
            short_pos = sides['short']
            
            long_profit = long_pos.get('profit_rate', 0)
            short_profit = short_pos.get('profit_rate', 0)
            long_margin = long_pos.get('margin', 0)
            short_margin = short_pos.get('margin', 0)
            
            # 规则：多单盈利时，空单亏损则平掉空单（保留1U）
            if long_profit > 0 and short_profit < 0:
                if short_margin > MIN_MARGIN:
                    log(f"    ⚠️  {inst_id}: 多单盈利{long_profit:.2f}%，空单亏损{short_profit:.2f}%，触发对冲止盈")
                    
                    success = execute_take_profit(
                        inst_id, 'short', 
                        short_pos['pos_size'], short_margin, short_profit,
                        100,  # 对冲平仓（保留1U）
                        f"对冲规则：多单盈利{long_profit:.1f}%，空单亏损{short_profit:.1f}%",
                        short_pos['mark_price'], int(short_pos.get('leverage', 10))
                    )
                    
                    if success:
                        log(f"    ✅ 对冲止盈完成")
                        time.sleep(3)
                    else:
                        log(f"    ❌ 对冲止盈失败")
                else:
                    log(f"    ⊘ {inst_id} short: 保证金{short_margin:.2f}U <= {MIN_MARGIN}U，跳过")
            
            # 规则：空单盈利时，多单亏损则平掉多单（保留1U）
            elif short_profit > 0 and long_profit < 0:
                if long_margin > MIN_MARGIN:
                    log(f"    ⚠️  {inst_id}: 空单盈利{short_profit:.2f}%，多单亏损{long_profit:.2f}%，触发对冲止盈")
                    
                    success = execute_take_profit(
                        inst_id, 'long',
                        long_pos['pos_size'], long_margin, long_profit,
                        100,  # 对冲平仓（保留1U）
                        f"对冲规则：空单盈利{short_profit:.1f}%，多单亏损{long_profit:.1f}%",
                        long_pos['mark_price'], int(long_pos.get('leverage', 10))
                    )
                    
                    if success:
                        log(f"    ✅ 对冲止盈完成")
                        time.sleep(3)
                    else:
                        log(f"    ❌ 对冲止盈失败")
                else:
                    log(f"    ⊘ {inst_id} long: 保证金{long_margin:.2f}U <= {MIN_MARGIN}U，跳过")
            else:
                log(f"    ✓ {inst_id}: 多单{long_profit:.2f}%，空单{short_profit:.2f}%，未触发对冲")

def main_loop():
    """主循环"""
    log("🚀 主账号止盈守护进程启动")
    log(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    log(f"📊 最小保证金要求: {MIN_MARGIN}U")
    log(f"📈 多单止盈规则:")
    for rule in LONG_RULES:
        log(f"   盈利{rule['profit']}% → 止盈剩余{rule['close_percent']}%")
    log(f"📉 空单止盈规则:")
    for rule in SHORT_RULES:
        log(f"   盈利{rule['profit']}% → 止盈剩余{rule['close_percent']}%")
    log(f"🔄 对冲规则: 反向交易对亏损 → 保留1U，其他全止盈")
    
    while True:
        try:
            log(f"\n{'='*60}")
            log(f"🔍 检查主账户持仓")
            
            # 获取主账户持仓
            positions = get_main_account_positions()
            log(f"📊 持仓数量: {len(positions)}")
            
            if not positions:
                log("✅ 无持仓")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 加载持仓状态
            states = load_position_states()
            
            # 清理不存在的持仓状态
            states = clean_old_states(states, positions)
            
            # 检查盈利规则
            check_profit_rules(positions, states)
            
            # 检查对冲亏损规则
            check_hedge_loss(positions)
            
            log(f"{'='*60}")
            
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())
        
        # 等待下次检查
        log(f"\n😴 等待 {CHECK_INTERVAL} 秒后继续检查...")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        log("\n👋 程序退出")
    except Exception as e:
        log(f"❌ 程序异常退出: {e}")
        log(traceback.format_exc())
