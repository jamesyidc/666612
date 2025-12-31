#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点单平仓保护模块
防止锚点单被完全平掉，确保至少保留0.6U以上的底仓
"""

# 最小底仓保护配置
MIN_KEEP_MARGIN = 0.6  # 平仓时必须保留的最小保证金（USDT）

def calculate_safe_close_size(pos_size, mark_price, leverage, keep_margin=MIN_KEEP_MARGIN):
    """
    计算安全的平仓数量，确保保留最小底仓
    
    参数:
        pos_size: 当前持仓数量
        mark_price: 标记价格
        leverage: 杠杆倍数
        keep_margin: 最小保留保证金（默认0.6U）
    
    返回:
        (safe_close_size, remain_size, remain_margin): 安全平仓量、保留量、保留保证金
    """
    # 计算当前总保证金
    current_margin = pos_size * mark_price / leverage
    
    # 计算最小保留持仓量
    min_remain_size = (keep_margin * leverage) / mark_price
    
    # 安全检查：如果当前保证金小于最小保留保证金，不允许平仓
    if current_margin <= keep_margin:
        return 0, pos_size, current_margin
    
    # 计算安全平仓量
    safe_close_size = pos_size - min_remain_size
    
    # 确保平仓量不为负
    if safe_close_size <= 0:
        return 0, pos_size, current_margin
    
    # 计算保留后的保证金
    remain_size = pos_size - safe_close_size
    remain_margin = remain_size * mark_price / leverage
    
    return safe_close_size, remain_size, remain_margin

def validate_close_request(pos_size, close_size, mark_price, leverage, keep_margin=MIN_KEEP_MARGIN):
    """
    验证平仓请求是否安全
    
    参数:
        pos_size: 当前持仓数量
        close_size: 请求平仓数量
        mark_price: 标记价格
        leverage: 杠杆倍数
        keep_margin: 最小保留保证金（默认0.6U）
    
    返回:
        (is_safe, adjusted_close_size, warning_msg)
    """
    # 计算平仓后的保留量
    remain_size = pos_size - close_size
    
    if remain_size <= 0:
        # 完全平仓，违反底仓保护
        safe_close_size, remain_size, remain_margin = calculate_safe_close_size(
            pos_size, mark_price, leverage, keep_margin
        )
        return (
            False,
            safe_close_size,
            f"⚠️ 底仓保护: 请求平仓{close_size:.4f}将导致完全平仓，已调整为{safe_close_size:.4f}，保留{remain_size:.4f}({remain_margin:.4f}U)"
        )
    
    # 计算平仓后的保证金
    remain_margin = remain_size * mark_price / leverage
    
    if remain_margin < keep_margin:
        # 保留保证金不足，需要调整
        safe_close_size, remain_size, remain_margin = calculate_safe_close_size(
            pos_size, mark_price, leverage, keep_margin
        )
        return (
            False,
            safe_close_size,
            f"⚠️ 底仓保护: 请求平仓{close_size:.4f}后保证金仅{remain_margin:.4f}U < {keep_margin}U，已调整为{safe_close_size:.4f}，保留{remain_size:.4f}({remain_margin:.4f}U)"
        )
    
    # 平仓请求安全
    return True, close_size, "✅ 平仓请求安全"

def get_min_keep_margin():
    """获取最小保留保证金配置"""
    try:
        import json
        with open('/home/user/webapp/anchor_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('anchor_config', {}).get('rules', {}).get('min_keep_margin', MIN_KEEP_MARGIN)
    except Exception:
        return MIN_KEEP_MARGIN

# 更新全局配置
MIN_KEEP_MARGIN = get_min_keep_margin()

if __name__ == '__main__':
    # 测试示例
    print("="*60)
    print("锚点单平仓保护测试")
    print("="*60)
    print(f"最小保留保证金: {MIN_KEEP_MARGIN}U")
    print()
    
    # 测试案例1: 正常平仓
    pos_size = 100
    close_size = 50
    mark_price = 1.0
    leverage = 10
    
    print(f"案例1: 持仓{pos_size}张，请求平仓{close_size}张")
    is_safe, adjusted_size, msg = validate_close_request(pos_size, close_size, mark_price, leverage)
    print(f"  结果: {msg}")
    print(f"  调整后平仓量: {adjusted_size:.4f}")
    print()
    
    # 测试案例2: 完全平仓（应该被阻止）
    print(f"案例2: 持仓{pos_size}张，请求完全平仓{pos_size}张")
    is_safe, adjusted_size, msg = validate_close_request(pos_size, pos_size, mark_price, leverage)
    print(f"  结果: {msg}")
    print(f"  调整后平仓量: {adjusted_size:.4f}")
    print()
    
    # 测试案例3: 小持仓情况
    small_pos = 10
    print(f"案例3: 小持仓{small_pos}张，请求平仓{small_pos}张")
    is_safe, adjusted_size, msg = validate_close_request(small_pos, small_pos, mark_price, leverage)
    print(f"  结果: {msg}")
    print(f"  调整后平仓量: {adjusted_size:.4f}")
    print()
    
    # 测试案例4: 计算安全平仓量
    print(f"案例4: 持仓{pos_size}张，计算最大安全平仓量")
    safe_close, remain, remain_margin = calculate_safe_close_size(pos_size, mark_price, leverage)
    print(f"  最大安全平仓量: {safe_close:.4f}")
    print(f"  保留持仓: {remain:.4f}张")
    print(f"  保留保证金: {remain_margin:.4f}U")
