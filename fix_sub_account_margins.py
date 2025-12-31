#!/usr/bin/env python3
"""
子账户保证金修正工具
根据维护次数自动调整保证金到目标值

使用方法：
  python3 fix_sub_account_margins.py              # 仅检查，不执行修正
  python3 fix_sub_account_margins.py --fix        # 执行修正
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta

BASE_URL = 'http://localhost:5000'
DRY_RUN = '--fix' not in sys.argv  # 默认dry-run模式

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def log(msg):
    """打印日志"""
    print(f"[{get_china_time().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_maintenance_count(account_name, inst_id, pos_side):
    """获取维护次数"""
    try:
        with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{account_name}_{inst_id}_{pos_side}"
        if key in data:
            record = data[key]
            today = get_china_time().strftime('%Y-%m-%d')
            if record.get('date') == today:
                return record.get('count', 0)
        return 0
    except FileNotFoundError:
        return 0
    except Exception as e:
        log(f"⚠️ 读取维护次数失败: {e}")
        return 0

def get_sub_account_positions(account_name):
    """获取子账户持仓"""
    try:
        response = requests.get(f'{BASE_URL}/api/anchor-system/sub-account-positions', timeout=10)
        data = response.json()
        
        if data.get('success') and data.get('positions'):
            return [pos for pos in data['positions'] if pos['account_name'] == account_name]
        return []
    except Exception as e:
        log(f"❌ 获取子账户持仓失败: {e}")
        return []

def calculate_target_margin(maintenance_count):
    """根据维护次数计算目标保证金"""
    if maintenance_count == 0:
        return 10  # 第0次：10U
    elif maintenance_count == 1:
        return 10  # 第1次：10U
    elif maintenance_count == 2:
        return 20  # 第2次：20U
    elif maintenance_count == 3:
        return 30  # 第3次：30U
    else:
        return 10  # 默认10U

def fix_margin(account_config, inst_id, pos_side, pos_size, current_margin, target_margin, leverage):
    """修正保证金（通过部分平仓）"""
    try:
        account_name = account_config['account_name']
        
        log(f"🔧 修正保证金: {inst_id} {pos_side}")
        log(f"   当前保证金: {current_margin:.4f}U")
        log(f"   目标保证金: {target_margin}U")
        
        margin_diff = current_margin - target_margin
        
        if abs(margin_diff) < 0.5:
            log(f"   ✅ 保证金已接近目标值，无需调整")
            return True
        
        if margin_diff > 0.5:
            # 保证金过多，需要平仓
            log(f"   ⚠️  保证金过多，需要平掉 {margin_diff:.4f}U")
            
            # 计算需要平掉的数量
            # 保证金 = 持仓量 * 标记价格 / 杠杆
            # 需要减少的持仓量 = (当前保证金 - 目标保证金) * 杠杆 / 标记价格
            # 但是我们不知道标记价格，所以用持仓量计算
            # 持仓量减少比例 = (当前保证金 - 目标保证金) / 当前保证金
            
            reduce_ratio = margin_diff / current_margin
            close_size = pos_size * reduce_ratio
            
            log(f"   📊 当前持仓量: {pos_size}")
            log(f"   📉 需要平仓量: {close_size:.4f} (比例: {reduce_ratio*100:.2f}%)")
            
            if DRY_RUN:
                log(f"   🔍 [DRY-RUN模式] 不执行实际平仓")
                return False
            
            # 调用平仓API
            response = requests.post(f'{BASE_URL}/api/anchor/close-sub-account-position',
                                   json={
                                       'account_name': account_name,
                                       'inst_id': inst_id,
                                       'pos_side': pos_side,
                                       'close_size': close_size,
                                       'reason': f'保证金修正: {current_margin:.2f}U -> {target_margin}U'
                                   },
                                   timeout=30)
            
            result = response.json()
            
            if result.get('success'):
                log(f"   ✅ 平仓成功")
                log(f"   📝 订单ID: {result.get('order_id', 'N/A')}")
                return True
            else:
                log(f"   ❌ 平仓失败: {result.get('message', '未知错误')}")
                return False
        else:
            # 保证金不足（这种情况不应该出现）
            log(f"   ⚠️  保证金不足，当前: {current_margin:.4f}U < 目标: {target_margin}U")
            return False
            
    except Exception as e:
        log(f"❌ 修正保证金失败: {e}")
        import traceback
        log(traceback.format_exc())
        return False

def main():
    """主函数"""
    log("="*60)
    log("🚀 子账户保证金修正工具启动")
    if DRY_RUN:
        log("🔍 运行模式: DRY-RUN (仅检查，不执行)")
        log("💡 提示: 使用 --fix 参数执行实际修正")
    else:
        log("⚠️  运行模式: 执行修正")
    log("="*60)
    
    # 加载子账户配置
    try:
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        config = config_data.get('sub_accounts', [])
    except Exception as e:
        log(f"❌ 加载配置失败: {e}")
        return
    
    # 找到第一个启用的子账户
    sub_account = None
    for account in config:
        if account.get('enabled', False):
            sub_account = account
            break
    
    if not sub_account:
        log("❌ 没有启用的子账户")
        return
    
    account_name = sub_account['account_name']
    log(f"📊 检查账户: {account_name}")
    
    # 获取持仓
    positions = get_sub_account_positions(account_name)
    log(f"📦 持仓数量: {len(positions)}")
    
    if not positions:
        log("✅ 无持仓")
        return
    
    # 检查每个持仓
    fix_count = 0
    success_count = 0
    
    for pos in positions:
        inst_id = pos['inst_id']
        pos_side = pos['pos_side']
        margin = pos.get('margin', 0)
        pos_size = pos.get('pos_size', 0)
        lever = pos.get('lever', 10)
        
        log(f"\n📍 检查持仓: {inst_id} {pos_side}")
        log(f"   当前保证金: {margin:.4f}U")
        log(f"   持仓量: {pos_size}")
        log(f"   杠杆: {lever}x")
        
        # 获取维护次数
        count = get_maintenance_count(account_name, inst_id, pos_side)
        log(f"   今日维护次数: {count}次")
        
        # 计算目标保证金
        target_margin = calculate_target_margin(count)
        log(f"   目标保证金: {target_margin}U")
        
        # 检查是否需要调整
        margin_diff = margin - target_margin
        if abs(margin_diff) > 0.5:
            log(f"   ⚠️  保证金偏差: {margin_diff:+.4f}U (超过阈值0.5U)")
            
            if margin_diff > 0.5:
                log(f"   🔧 需要平掉多余的 {margin_diff:.4f}U")
                fix_count += 1
                
                # 执行修正
                success = fix_margin(sub_account, inst_id, pos_side, pos_size, margin, target_margin, lever)
                if success:
                    log(f"   ✅ 修正成功")
                    success_count += 1
                else:
                    log(f"   ❌ 修正失败")
        else:
            log(f"   ✅ 保证金正常 (偏差: {margin_diff:+.4f}U)")
    
    log(f"\n{'='*60}")
    if fix_count > 0:
        log(f"⚠️  发现 {fix_count} 个持仓需要修正保证金")
        log(f"✅ 成功修正 {success_count} 个")
        log(f"❌ 修正失败 {fix_count - success_count} 个")
    else:
        log(f"✅ 所有持仓保证金正常")
    log(f"{'='*60}")

if __name__ == '__main__':
    main()
