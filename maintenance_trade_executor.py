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
            'error': None
        }
        
        try:
            # 安全检查
            if not self._safety_check(position):
                result['error'] = '安全检查未通过'
                return result
            
            # Step 1: 补仓（对冲）
            print("\n【步骤1】执行补仓操作...")
            step1_result = self._execute_add_position(position, maintenance_plan)
            result['step1_result'] = step1_result
            
            if not step1_result['success']:
                result['error'] = f"补仓失败: {step1_result.get('error')}"
                return result
            
            # 等待补仓成交
            print("⏳ 等待3秒确保补仓成交...")
            time.sleep(3)
            
            # Step 2: 平仓（保留底仓）
            print("\n【步骤2】执行平仓操作...")
            step2_result = self._execute_close_position(position, maintenance_plan)
            result['step2_result'] = step2_result
            
            if not step2_result['success']:
                result['error'] = f"平仓失败: {step2_result.get('error')}"
                return result
            
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
