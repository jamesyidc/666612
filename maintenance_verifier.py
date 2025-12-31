#!/usr/bin/env python3
"""
维护后自动验证和纠错系统
功能：在维护完成后，自动检查持仓是否正确，如有偏差则自动纠正
"""

import requests
import time
import json
import math
from datetime import datetime, timezone, timedelta

# 配置
TOLERANCE = 0.5  # 保证金容差（U），超过此值触发纠错
MAX_RETRY = 3  # 最大重试次数
VERIFY_DELAY = 5  # 维护后等待多少秒再验证（秒）
API_BASE_URL = 'http://localhost:5000'

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def log(msg):
    """打印日志"""
    print(f"[{get_china_time().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_position_data(account_name, inst_id, pos_side):
    """获取持仓数据"""
    try:
        if account_name == 'JAMESYI':  # 主账号
            response = requests.get(f'{API_BASE_URL}/api/anchor-system/positions', timeout=10)
        else:  # 子账户
            response = requests.get(f'{API_BASE_URL}/api/anchor-system/sub-account-positions', timeout=10)
        
        data = response.json()
        if not data.get('success'):
            log(f"❌ 获取持仓失败: {data.get('message', 'Unknown error')}")
            return None
        
        positions = data.get('positions', [])
        for pos in positions:
            if pos.get('inst_id') == inst_id and pos.get('pos_side') == pos_side:
                return pos
        
        log(f"❌ 未找到持仓: {inst_id} {pos_side}")
        return None
    except Exception as e:
        log(f"❌ 获取持仓异常: {e}")
        return None

def calculate_theoretical_margin(pos_size, mark_price, leverage=10):
    """计算理论保证金"""
    return pos_size * mark_price / leverage

def verify_and_correct(account_name, inst_id, pos_side, target_margin, maintenance_count=0, retry_count=0):
    """
    验证维护结果并自动纠错
    
    参数:
        account_name: 账户名称（JAMESYI 或子账户名）
        inst_id: 合约ID
        pos_side: 持仓方向（long/short）
        target_margin: 目标保证金（U）
        maintenance_count: 当前维护次数
        retry_count: 当前重试次数
    
    返回:
        {
            'success': bool,
            'verified': bool,  # 是否通过验证
            'corrected': bool,  # 是否进行了纠错
            'final_margin': float,  # 最终保证金
            'deviation': float,  # 偏差（U）
            'message': str
        }
    """
    log(f"\n{'='*60}")
    log(f"🔍 开始验证维护结果")
    log(f"   账户: {account_name}")
    log(f"   合约: {inst_id} {pos_side}")
    log(f"   目标保证金: {target_margin}U")
    log(f"   重试次数: {retry_count}/{MAX_RETRY}")
    
    # 等待一段时间让订单完全成交
    if retry_count == 0:
        log(f"⏳ 等待{VERIFY_DELAY}秒让订单完全成交...")
        time.sleep(VERIFY_DELAY)
    
    # 获取最新持仓数据
    pos = get_position_data(account_name, inst_id, pos_side)
    if not pos:
        return {
            'success': False,
            'verified': False,
            'corrected': False,
            'message': '无法获取持仓数据'
        }
    
    # 提取数据
    pos_size = float(pos.get('pos_size', 0))
    mark_price = float(pos.get('mark_price', 0))
    api_margin = float(pos.get('margin', 0))
    leverage = 10
    
    # 计算理论保证金
    theoretical_margin = calculate_theoretical_margin(pos_size, mark_price, leverage)
    
    # 计算偏差（使用理论保证金，因为API返回的margin可能不准确）
    deviation = abs(theoretical_margin - target_margin)
    
    log(f"\n📊 持仓验证数据:")
    log(f"   持仓量: {pos_size} 张")
    log(f"   标记价格: {mark_price}")
    log(f"   杠杆: {leverage}x")
    log(f"   API返回保证金: {api_margin}U")
    log(f"   理论保证金: {theoretical_margin:.2f}U")
    log(f"   目标保证金: {target_margin}U")
    log(f"   偏差: {deviation:.2f}U")
    log(f"   容差: {TOLERANCE}U")
    
    # 判断是否需要纠错
    if deviation <= TOLERANCE:
        log(f"✅ 验证通过！偏差 {deviation:.2f}U 在容差范围内")
        return {
            'success': True,
            'verified': True,
            'corrected': False,
            'final_margin': theoretical_margin,
            'deviation': deviation,
            'message': f'验证通过，偏差{deviation:.2f}U'
        }
    
    # 需要纠错
    log(f"⚠️ 偏差超过容差！需要纠错")
    
    # 检查重试次数
    if retry_count >= MAX_RETRY:
        log(f"❌ 已达到最大重试次数({MAX_RETRY})，放弃纠错")
        return {
            'success': False,
            'verified': False,
            'corrected': False,
            'final_margin': theoretical_margin,
            'deviation': deviation,
            'message': f'纠错失败，已重试{MAX_RETRY}次，偏差{deviation:.2f}U'
        }
    
    # 执行纠错
    log(f"\n🔧 开始纠错操作（第{retry_count + 1}次）")
    
    # 计算需要调整的持仓量
    target_pos_size = (target_margin * leverage) / mark_price
    target_pos_size = math.floor(target_pos_size)
    
    # 计算需要平仓或加仓的数量
    adjust_size = pos_size - target_pos_size
    
    log(f"   当前持仓: {pos_size} 张")
    log(f"   目标持仓: {target_pos_size} 张")
    log(f"   需要调整: {adjust_size} 张")
    
    if adjust_size > 0:
        # 需要平仓
        log(f"   操作: 平仓 {adjust_size} 张")
        correction_result = execute_correction(
            account_name, inst_id, pos_side, pos_size,
            adjust_size, target_margin, 'close', maintenance_count
        )
    elif adjust_size < 0:
        # 需要加仓
        add_size = abs(adjust_size)
        log(f"   操作: 加仓 {add_size} 张")
        correction_result = execute_correction(
            account_name, inst_id, pos_side, pos_size,
            add_size, target_margin, 'open', maintenance_count
        )
    else:
        log(f"   持仓量正确，无需调整")
        return {
            'success': True,
            'verified': True,
            'corrected': False,
            'final_margin': theoretical_margin,
            'deviation': deviation,
            'message': '持仓量正确，无需调整'
        }
    
    # 检查纠错结果
    if not correction_result.get('success'):
        log(f"❌ 纠错失败: {correction_result.get('message')}")
        return {
            'success': False,
            'verified': False,
            'corrected': False,
            'final_margin': theoretical_margin,
            'deviation': deviation,
            'message': f"纠错失败: {correction_result.get('message')}"
        }
    
    log(f"✅ 纠错操作已执行")
    
    # 递归验证纠错结果
    log(f"\n🔄 重新验证纠错结果...")
    return verify_and_correct(
        account_name, inst_id, pos_side, target_margin,
        maintenance_count, retry_count + 1
    )

def execute_correction(account_name, inst_id, pos_side, pos_size, 
                      adjust_size, target_margin, action, maintenance_count):
    """
    执行纠错操作
    
    参数:
        account_name: 账户名称
        inst_id: 合约ID
        pos_side: 持仓方向
        pos_size: 当前持仓量
        adjust_size: 调整数量（正数表示平仓，负数表示加仓）
        target_margin: 目标保证金
        action: 'close' 或 'open'
        maintenance_count: 维护次数
    """
    try:
        if action == 'close':
            # 平仓纠错
            if account_name == 'JAMESYI':
                # 主账号平仓
                # TODO: 实现主账号平仓API调用
                log(f"⚠️ 主账号平仓纠错功能待实现")
                return {'success': False, 'message': '主账号平仓功能待实现'}
            else:
                # 子账户平仓
                payload = {
                    'account_name': account_name,
                    'inst_id': inst_id,
                    'pos_side': pos_side,
                    'close_size': adjust_size,
                    'reason': f'自动纠错：平仓到{target_margin}U'
                }
                response = requests.post(
                    f'{API_BASE_URL}/api/anchor/close-sub-account-position',
                    json=payload,
                    timeout=30
                )
        else:
            # 加仓纠错（使用维护API，但金额很小）
            # 计算需要加仓的金额
            mark_price = get_position_data(account_name, inst_id, pos_side).get('mark_price', 0)
            add_margin = abs(adjust_size) * float(mark_price) / 10
            add_margin = max(1, math.ceil(add_margin))  # 至少1U
            
            if account_name == 'JAMESYI':
                # 主账号加仓
                # TODO: 实现主账号加仓API调用
                log(f"⚠️ 主账号加仓纠错功能待实现")
                return {'success': False, 'message': '主账号加仓功能待实现'}
            else:
                # 子账户加仓（使用维护API）
                payload = {
                    'account_name': account_name,
                    'inst_id': inst_id,
                    'pos_side': pos_side,
                    'pos_size': pos_size,
                    'amount': add_margin,
                    'target_margin': target_margin,
                    'maintenance_count': maintenance_count
                }
                response = requests.post(
                    f'{API_BASE_URL}/api/anchor/maintain-sub-account',
                    json=payload,
                    timeout=30
                )
        
        result = response.json()
        if result.get('success'):
            log(f"✅ 纠错操作成功")
            return {'success': True, 'message': '纠错成功'}
        else:
            log(f"❌ 纠错操作失败: {result.get('message')}")
            return {'success': False, 'message': result.get('message')}
    
    except Exception as e:
        log(f"❌ 纠错操作异常: {e}")
        return {'success': False, 'message': str(e)}

# 测试代码
if __name__ == '__main__':
    # 测试验证CFX
    result = verify_and_correct(
        account_name='Wu666666',
        inst_id='CFX-USDT-SWAP',
        pos_side='long',
        target_margin=10,
        maintenance_count=1
    )
    
    log(f"\n{'='*60}")
    log(f"📊 最终验证结果:")
    log(f"   成功: {result['success']}")
    log(f"   验证通过: {result['verified']}")
    log(f"   是否纠错: {result['corrected']}")
    log(f"   最终保证金: {result.get('final_margin', 'N/A')}U")
    log(f"   偏差: {result.get('deviation', 'N/A')}U")
    log(f"   消息: {result['message']}")
    log(f"{'='*60}\n")
