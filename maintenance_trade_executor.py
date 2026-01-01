#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锚点单维护交易执行器
自动执行维护计划中的补仓和平仓操作
"""

import json
import time
from datetime import datetime
import pytz
from okex_trader import OKExTrader, SafetyGate

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class MaintenanceTradeExecutor:
    """维护交易执行器"""
    
    def __init__(self, dry_run=False):
        """
        初始化维护交易执行器
        
        Args:
            dry_run: 是否模拟运行（True不实际下单）
        """
        self.trader = OKExTrader(dry_run=dry_run)
        self.dry_run = dry_run
        self.safety_gate = SafetyGate()
    
    def get_available_balance(self):
        """获取账户可用USDT余额"""
        try:
            import requests
            method = 'GET'
            request_path = '/api/v5/account/balance'
            headers = self.trader.get_headers(method, request_path)
            
            response = requests.get(
                self.trader.base_url + request_path,
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            if data.get('code') == '0':
                for detail in data.get('data', [])[0].get('details', []):
                    if detail.get('ccy') == 'USDT':
                        avail = float(detail.get('availBal', 0))
                        return avail
            return 0
        except Exception as e:
            print(f"⚠️  获取账户余额失败: {e}")
            return 0
    
    def adjust_maintenance_plan(self, position, maintenance_plan):
        """
        根据可用余额智能调整维护计划
        
        Args:
            position: 持仓信息
            maintenance_plan: 原始维护计划
        
        Returns:
            dict: 调整后的维护计划 {'success': bool, 'plan': dict, 'message': str}
        """
        # 获取可用余额
        available_balance = self.get_available_balance()
        print(f"\n💰 账户可用余额: {available_balance:.2f} USDT")
        
        # 获取原始计划的补仓金额
        original_buy_margin = maintenance_plan['step1_buy']['margin']
        print(f"📊 原计划需要: {original_buy_margin:.2f} USDT")
        
        # 如果余额充足，直接返回原计划
        if available_balance >= original_buy_margin:
            print(f"✅ 余额充足，使用原计划")
            return {
                'success': True,
                'plan': maintenance_plan,
                'message': '余额充足'
            }
        
        # 余额不足，智能调整
        print(f"⚠️  余额不足，开始智能调整...")
        
        # 保留10 USDT作为安全余额
        SAFETY_BUFFER = 10.0
        usable_balance = max(0, available_balance - SAFETY_BUFFER)
        
        if usable_balance < 1:
            return {
                'success': False,
                'plan': None,
                'message': f'可用余额不足1 USDT（当前{available_balance:.2f}，保留{SAFETY_BUFFER} USDT安全余额）'
            }
        
        # 计算调整后的维护倍数
        original_margin = position['margin']
        max_multiplier = usable_balance / original_margin
        adjusted_multiplier = min(max_multiplier, 10)  # 最多10倍
        
        print(f"🔧 调整维护倍数: 10x → {adjusted_multiplier:.1f}x")
        print(f"   原保证金: {original_margin:.4f} USDT")
        print(f"   可用余额: {usable_balance:.2f} USDT")
        print(f"   调整后投入: {original_margin * adjusted_multiplier:.2f} USDT")
        
        # 重新计算维护计划
        current_price = position['mark_price']
        leverage = position.get('lever', 10)
        original_size = position['pos_size']
        
        # 步骤1：调整后的补仓
        adjusted_buy_margin = original_margin * adjusted_multiplier
        # 注意：不需要乘以leverage，保证金直接除以价格得到张数
        adjusted_buy_size = adjusted_buy_margin / current_price
        
        # 买入后的总仓位
        total_size_after_buy = original_size + adjusted_buy_size
        total_margin_after_buy = original_margin + adjusted_buy_margin
        
        # 步骤2：余额控制（0.6-1.1U）
        MIN_MARGIN = 0.6
        MAX_MARGIN = 1.1
        
        if total_margin_after_buy > MAX_MARGIN:
            target_remaining_margin = MAX_MARGIN
            close_margin = total_margin_after_buy - target_remaining_margin
        else:
            target_remaining_margin = total_margin_after_buy
            close_margin = 0
        
        close_percent = (close_margin / total_margin_after_buy) * 100 if total_margin_after_buy > 0 else 0
        close_size = (close_margin / total_margin_after_buy) * total_size_after_buy if total_margin_after_buy > 0 else 0
        
        # 步骤3：剩余持仓
        remaining_size = total_size_after_buy - close_size
        remaining_margin = total_margin_after_buy - close_margin
        
        adjusted_plan = {
            'step1_buy': {
                'action': 'buy',
                'size': adjusted_buy_size,
                'margin': adjusted_buy_margin,
                'leverage': leverage,
                'multiplier': adjusted_multiplier,
                'description': f'投入{adjusted_multiplier:.1f}倍保证金: {adjusted_buy_margin:.2f} USDT (开仓{adjusted_buy_size:.4f}张)'
            },
            'after_buy': {
                'total_size': total_size_after_buy,
                'total_margin': total_margin_after_buy,
                'description': f'买入后总仓位: {total_size_after_buy:.4f} 张 ({total_margin_after_buy:.2f} USDT)'
            },
            'step2_close': {
                'action': 'close',
                'size': close_size,
                'margin': close_margin,
                'percent': close_percent,
                'description': f'平掉{close_percent:.1f}%: {close_size:.4f} 张 ({close_margin:.2f} USDT)'
            },
            'step3_remaining': {
                'size': remaining_size,
                'margin': remaining_margin,
                'target_margin': target_remaining_margin,
                'description': f'保留余额{MIN_MARGIN}-{MAX_MARGIN}U: {remaining_size:.4f} 张 ({remaining_margin:.2f} USDT)'
            },
            'original': {
                'size': original_size,
                'margin': original_margin
            },
            'adjusted': True
        }
        
        return {
            'success': True,
            'plan': adjusted_plan,
            'message': f'智能调整维护倍数: {adjusted_multiplier:.1f}x（余额限制）'
        }
    
    def execute_maintenance_plan(self, position, maintenance_plan):
        """
        执行维护计划
        
        Args:
            position: 持仓信息
            maintenance_plan: 维护计划
        
        Returns:
            dict: 执行结果 {
                'success': bool,
                'step1_result': dict,  # 补仓结果
                'step2_result': dict,  # 平仓结果
                'step3_result': dict,  # 保证金验证结果
                'error': str
            }
        """
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        
        print("\n" + "=" * 80)
        print(f"🔧 开始执行维护计划: {inst_id} {pos_side}")
        print("=" * 80)
        
        result = {
            'success': False,
            'step1_result': None,
            'step2_result': None,
            'step3_result': None,
            'error': None
        }
        
        try:
            # 安全检查
            if not self._safety_check(position):
                result['error'] = '安全检查未通过'
                return result
            
            # 智能调整维护计划（根据可用余额）
            adjusted_result = self.adjust_maintenance_plan(position, maintenance_plan)
            if not adjusted_result['success']:
                result['error'] = adjusted_result['message']
                print(f"\n❌ {adjusted_result['message']}")
                return result
            
            # 使用调整后的计划
            adjusted_plan = adjusted_result['plan']
            if adjusted_result.get('message') != '余额充足':
                print(f"✅ {adjusted_result['message']}")
            
            # Step 1: 补仓（对冲）
            print("\n【步骤1】执行补仓操作...")
            step1_result = self._execute_add_position(position, adjusted_plan)
            result['step1_result'] = step1_result
            
            if not step1_result['success']:
                result['error'] = f"补仓失败: {step1_result.get('error')}"
                return result
            
            # 等待补仓成交
            print("⏳ 等待3秒确保补仓成交...")
            time.sleep(3)
            
            # Step 2: 平仓（保留底仓）
            print("\n【步骤2】执行平仓操作...")
            step2_result = self._execute_close_position(position, adjusted_plan)
            result['step2_result'] = step2_result
            
            if not step2_result['success']:
                result['error'] = f"平仓失败: {step2_result.get('error')}"
                return result
            
            # 等待平仓成交
            print("⏳ 等待3秒确保平仓成交...")
            time.sleep(3)
            
            # Step 3: 验证并调整剩余保证金到0.6-1.1U范围
            print("\n【步骤3】验证剩余保证金...")
            step3_result = self._verify_and_adjust_margin(position)
            result['step3_result'] = step3_result
            
            if not step3_result['success']:
                result['error'] = f"保证金调整失败: {step3_result.get('error')}"
                # 即使保证金调整失败，维护仍算成功（因为主要步骤已完成）
                print(f"⚠️ 警告: {result['error']}")
            
            # 所有步骤成功
            result['success'] = True
            print("\n✅ 维护计划执行完成!")
            
        except Exception as e:
            result['error'] = f"执行异常: {str(e)}"
            print(f"\n❌ 维护执行失败: {e}")
        
        return result
    
    def _safety_check(self, position):
        """安全检查"""
        print("\n🔒 执行安全检查...")
        
        # 1. 检查总开关
        if not self.safety_gate.is_master_switch_on():
            print("❌ 总开关已关闭，禁止交易")
            return False
        
        # 2. 检查币种开关
        inst_id = position['inst_id']
        if not self.safety_gate.check_coin_switch(inst_id):
            print(f"❌ {inst_id} 币种开关已关闭")
            return False
        
        print("✅ 安全检查通过")
        return True
    
    def _execute_add_position(self, position, maintenance_plan):
        """
        执行补仓（对冲）
        
        Args:
            position: 持仓信息
            maintenance_plan: 维护计划
        
        Returns:
            dict: {'success': bool, 'order_id': str, 'error': str}
        """
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        
        # 从维护计划获取补仓信息
        step1 = maintenance_plan.get('step1_buy', {})
        add_size = step1.get('size', 0)
        
        if add_size <= 0:
            return {'success': False, 'error': '补仓数量无效'}
        
        # 对数量取整（OKEx要求整数张数）
        add_size = int(add_size)
        if add_size <= 0:
            return {'success': False, 'error': '补仓数量取整后为0'}
        
        print(f"📈 补仓参数:")
        print(f"   币种: {inst_id}")
        print(f"   方向: {pos_side}")
        print(f"   数量: {add_size} (已取整)")
        print(f"   类型: 市价单")
        
        if self.dry_run:
            print("🎭 [模拟模式] 补仓操作")
            return {
                'success': True,
                'order_id': 'MOCK_ORDER_' + datetime.now().strftime('%Y%m%d%H%M%S'),
                'mode': 'dry_run'
            }
        
        # 实盘执行
        # 补仓 = 买入（做多补多，做空补空）
        side = 'buy'
        
        order_data = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式
            'side': side,
            'posSide': pos_side,
            'ordType': 'market',   # 市价单
            'sz': str(add_size)
        }
        
        success, data = self.trader.place_order(order_data)
        
        if success:
            order_id = data.get('data', [{}])[0].get('ordId', '')
            return {
                'success': True,
                'order_id': order_id,
                'order_data': order_data
            }
        else:
            return {
                'success': False,
                'error': data.get('msg', '下单失败')
            }
    
    def _execute_close_position(self, position, maintenance_plan):
        """
        执行平仓（保留底仓）
        
        Args:
            position: 持仓信息
            maintenance_plan: 维护计划
        
        Returns:
            dict: {'success': bool, 'order_id': str, 'error': str}
        """
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        
        # 从维护计划获取平仓信息
        step2 = maintenance_plan.get('step2_close', {})
        close_size = step2.get('size', 0)
        
        if close_size <= 0:
            return {'success': True, 'message': '无需平仓'}
        
        # 对数量取整（OKEx要求整数张数）
        close_size = int(close_size)
        if close_size <= 0:
            return {'success': True, 'message': '平仓数量取整后为0'}
        
        print(f"📉 平仓参数:")
        print(f"   币种: {inst_id}")
        print(f"   方向: {pos_side}")
        print(f"   数量: {close_size} (已取整)")
        print(f"   类型: 市价单")
        
        if self.dry_run:
            print("🎭 [模拟模式] 平仓操作")
            return {
                'success': True,
                'order_id': 'MOCK_ORDER_' + datetime.now().strftime('%Y%m%d%H%M%S'),
                'mode': 'dry_run'
            }
        
        # 实盘执行
        # 平多单 = 卖出，平空单 = 买入
        side = 'sell' if pos_side == 'long' else 'buy'
        
        order_data = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式
            'side': side,
            'posSide': pos_side,
            'ordType': 'market',   # 市价单
            'sz': str(close_size)
        }
        
        success, data = self.trader.place_order(order_data)
        
        if success:
            order_id = data.get('data', [{}])[0].get('ordId', '')
            return {
                'success': True,
                'order_id': order_id,
                'order_data': order_data
            }
        else:
            return {
                'success': False,
                'error': data.get('msg', '平仓失败')
            }
    
    def _verify_and_adjust_margin(self, position):
        """
        验证并调整剩余保证金到0.6-1.1U范围
        
        Args:
            position: 持仓信息
        
        Returns:
            dict: {'success': bool, 'adjusted': bool, 'final_margin': float, 'error': str}
        """
        inst_id = position['inst_id']
        pos_side = position['pos_side']
        
        MIN_MARGIN = 0.6
        MAX_MARGIN = 1.1
        
        try:
            # 获取当前持仓状态
            current_position = self._get_current_position(inst_id, pos_side)
            
            if not current_position:
                return {
                    'success': False,
                    'error': '无法获取当前持仓信息'
                }
            
            current_margin = current_position.get('margin', 0)
            current_size = current_position.get('pos_size', 0)
            current_price = current_position.get('mark_price', 0)
            
            print(f"📊 当前持仓状态:")
            print(f"   保证金: {current_margin:.4f} USDT")
            print(f"   数量: {current_size} 张")
            print(f"   目标范围: {MIN_MARGIN}-{MAX_MARGIN} USDT")
            
            # 检查保证金是否在范围内
            if MIN_MARGIN <= current_margin <= MAX_MARGIN:
                print(f"✅ 保证金在目标范围内")
                return {
                    'success': True,
                    'adjusted': False,
                    'final_margin': current_margin
                }
            
            # 保证金超出范围，需要继续平仓
            if current_margin > MAX_MARGIN:
                excess_margin = current_margin - MAX_MARGIN
                # 计算需要平仓的数量
                close_size = int((excess_margin / current_margin) * current_size)
                
                if close_size <= 0:
                    print(f"⚠️ 保证金 {current_margin:.4f} 超出范围，但计算的平仓数量为0")
                    return {
                        'success': True,
                        'adjusted': False,
                        'final_margin': current_margin,
                        'warning': f'保证金{current_margin:.4f}超出{MAX_MARGIN}，但数量不足以继续平仓'
                    }
                
                print(f"⚠️ 保证金 {current_margin:.4f} 超出 {MAX_MARGIN}，需要继续平仓")
                print(f"📉 继续平仓: {close_size} 张")
                
                # 执行额外平仓
                side = 'sell' if pos_side == 'long' else 'buy'
                order_data = {
                    'instId': inst_id,
                    'tdMode': 'isolated',
                    'side': side,
                    'posSide': pos_side,
                    'ordType': 'market',
                    'sz': str(close_size)
                }
                
                if self.dry_run:
                    print("🎭 [模拟模式] 额外平仓操作")
                    return {
                        'success': True,
                        'adjusted': True,
                        'final_margin': MAX_MARGIN,
                        'mode': 'dry_run'
                    }
                
                success, data = self.trader.place_order(order_data)
                
                if success:
                    print(f"✅ 额外平仓成功")
                    # 等待成交
                    time.sleep(2)
                    # 再次检查保证金
                    updated_position = self._get_current_position(inst_id, pos_side)
                    final_margin = updated_position.get('margin', 0) if updated_position else current_margin
                    print(f"📊 最终保证金: {final_margin:.4f} USDT")
                    return {
                        'success': True,
                        'adjusted': True,
                        'final_margin': final_margin,
                        'order_id': data.get('data', [{}])[0].get('ordId', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': f"额外平仓失败: {data.get('msg', '未知错误')}"
                    }
            
            # 保证金低于最小值（不太可能发生，但仍需处理）
            elif current_margin < MIN_MARGIN:
                print(f"⚠️ 保证金 {current_margin:.4f} 低于 {MIN_MARGIN}（可能已爆仓或接近强平）")
                return {
                    'success': True,
                    'adjusted': False,
                    'final_margin': current_margin,
                    'warning': f'保证金{current_margin:.4f}低于最小值{MIN_MARGIN}'
                }
                
        except Exception as e:
            print(f"❌ 保证金验证失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_current_position(self, inst_id, pos_side):
        """
        获取当前持仓信息
        
        Args:
            inst_id: 币种ID
            pos_side: 持仓方向
        
        Returns:
            dict: 持仓信息或None
        """
        try:
            positions = self.trader.get_positions()
            for pos in positions:
                if pos.get('instId') == inst_id and pos.get('posSide') == pos_side:
                    # 计算保证金
                    pos_size = float(pos.get('pos', 0))
                    mark_price = float(pos.get('markPx', 0))
                    leverage = float(pos.get('lever', 10))
                    
                    if pos_size > 0 and mark_price > 0:
                        margin = (pos_size * mark_price) / leverage
                        return {
                            'pos_size': pos_size,
                            'margin': margin,
                            'mark_price': mark_price,
                            'leverage': leverage
                        }
            return None
        except Exception as e:
            print(f"⚠️  获取持仓信息失败: {e}")
            return None
    
    def get_execution_summary(self, position, maintenance_plan, result):
        """
        生成执行摘要
        
        Args:
            position: 持仓信息
            maintenance_plan: 维护计划
            result: 执行结果
        
        Returns:
            dict: 执行摘要
        """
        summary = {
            'timestamp': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'),
            'inst_id': position['inst_id'],
            'pos_side': position['pos_side'],
            'original_size': position.get('pos_size', 0),
            'original_price': position.get('avg_price', 0),
            'current_price': position.get('mark_price', 0),
            'profit_rate': position.get('profit_rate', 0),
            'maintenance_plan': maintenance_plan,
            'execution_result': result,
            'success': result.get('success', False)
        }
        
        return summary


def test_executor():
    """测试维护执行器"""
    print("=" * 80)
    print("🧪 维护交易执行器测试（模拟模式）")
    print("=" * 80)
    
    # 模拟持仓
    test_position = {
        'inst_id': 'UNI-USDT-SWAP',
        'pos_side': 'long',
        'pos_size': 2.0,
        'avg_price': 5.972,
        'mark_price': 5.632,
        'profit_rate': -11.26,
        'margin': 1.139
    }
    
    # 模拟维护计划
    test_maintenance_plan = {
        'step1_buy': {
            'size': 20.2237,
            'margin': 11.39
        },
        'step2_close': {
            'size': 20.2726,
            'percent': 91.2
        },
        'step3_remaining': {
            'size': 1.9512,
            'margin': 1.1
        }
    }
    
    # 创建执行器（模拟模式）
    executor = MaintenanceTradeExecutor(dry_run=True)
    
    # 执行维护计划
    result = executor.execute_maintenance_plan(test_position, test_maintenance_plan)
    
    # 打印结果
    print("\n" + "=" * 80)
    print("📊 执行结果:")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 生成摘要
    summary = executor.get_execution_summary(test_position, test_maintenance_plan, result)
    print("\n" + "=" * 80)
    print("📋 执行摘要:")
    print("=" * 80)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    test_executor()
