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
    """获取今天的维护次数"""
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
    """执行维护锚点单"""
    try:
        log(f"🔧 开始维护: {inst_id} {pos_side} {pos_size}")
        response = requests.post(
            f"{BASE_URL}/api/anchor/maintain-anchor",
            json={
                'inst_id': inst_id,
                'pos_side': pos_side,
                'pos_size': pos_size
            },
            timeout=30
        )
        data = response.json()
        if data.get('success'):
            log(f"✅ 维护成功: {inst_id}")
            return True
        else:
            log(f"❌ 维护失败: {data.get('message')}")
            return False
    except Exception as e:
        log(f"❌ 维护操作异常: {e}")
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
        loss_threshold = config.get('loss_threshold', -10)
        margin_min = config.get('margin_min', 0.6)
        margin_max = config.get('margin_max', 1.0)
        
        log(f"📊 配置: 多单自动维护={auto_maintain_long}, 空单自动维护={auto_maintain_short}, 阈值={loss_threshold}%")
        log(f"💰 保证金范围: {margin_min}u - {margin_max}u")
        
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
            
            # 只处理锚点单
            if not is_anchor:
                continue
            
            log(f"🔍 检查: {inst_id} {pos_side} 收益率={profit_rate:.2f}% 保证金={margin:.4f}u")
            
            # 检查持仓保证金是否小于2U
            if margin >= 2.0:
                log(f"⚠️  保证金 >= 2U，不自动维护: {margin:.4f}u")
                continue
            
            # 检查1：收益率是否达到维护阈值
            should_maintain = False
            if pos_side == 'long' and auto_maintain_long and profit_rate <= loss_threshold:
                log(f"⚠️  多单收益率达到阈值: {profit_rate:.2f}% <= {loss_threshold}%")
                should_maintain = True
            elif pos_side == 'short' and auto_maintain_short and profit_rate <= loss_threshold:
                log(f"⚠️  空单收益率达到阈值: {profit_rate:.2f}% <= {loss_threshold}%")
                should_maintain = True
            
            if should_maintain:
                # 检查今天的维护次数
                today_count = get_maintenance_count_today(inst_id, pos_side)
                log(f"📊 {inst_id} {pos_side} 今日已维护次数: {today_count}/3")
                
                if today_count >= 3:
                    log(f"⚠️  已达到每日维护上限(3次)，跳过本次维护")
                    continue
                
                # 执行维护
                success = maintain_anchor(inst_id, pos_side, pos_size)
                if success:
                    log(f"✅ 自动维护完成: {inst_id} (今日第{today_count + 1}次)")
                    time.sleep(2)  # 稍作延迟
            
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
