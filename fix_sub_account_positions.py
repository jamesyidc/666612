#!/usr/bin/env python3
"""
子账户持仓纠错脚本 - 简化版
直接使用 OKX API 修正错误的持仓量
"""

import sqlite3
import json
import sys
import time
import hmac
import hashlib
import base64
from datetime import datetime
import requests

# 配置
DB_PATH = '/home/user/webapp/trading_decision.db'
CONFIG_PATH = '/home/user/webapp/sub_account_config.json'

def load_config():
    """加载OKX API配置"""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def generate_signature(timestamp, method, request_path, body, secret_key):
    """生成OKX API签名"""
    if body:
        body_str = json.dumps(body) if isinstance(body, dict) else body
    else:
        body_str = ''
    
    message = timestamp + method + request_path + body_str
    mac = hmac.new(
        bytes(secret_key, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod=hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()

def okx_request(method, endpoint, body=None, sub_account_name=None):
    """发送OKX API请求"""
    config = load_config()
    
    # 使用子账户配置
    if sub_account_name:
        # 从子账户列表中查找指定的账户
        sub_account = None
        for account in config['sub_accounts']:
            if account['account_name'] == sub_account_name:
                sub_account = account
                break
        
        if not sub_account:
            raise ValueError(f"未找到子账户: {sub_account_name}")
        
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
    else:
        # 使用第一个子账户（如果没有指定）
        sub_account = config['sub_accounts'][0]
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
    
    # 生成时间戳
    timestamp = datetime.utcnow().isoformat('T', 'milliseconds') + 'Z'
    
    # 构建请求路径
    request_path = endpoint
    if method == 'GET' and body:
        query_string = '&'.join([f"{k}={v}" for k, v in body.items()])
        request_path = f"{endpoint}?{query_string}"
        body = None
    
    # 生成签名
    signature = generate_signature(timestamp, method, request_path, body, secret_key)
    
    # 构建请求头
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    # 发送请求
    url = f"https://www.okx.com{request_path}"
    
    if method == 'GET':
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, json=body)
    
    return response.json()

def get_expected_positions():
    """从 position_opens 表获取预期的持仓配置"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            inst_id,
            pos_side,
            open_size,
            open_price,
            is_anchor
        FROM position_opens
        WHERE is_anchor = 1
        ORDER BY created_at DESC
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    expected = {}
    for inst_id, pos_side, open_size, open_price, is_anchor in records:
        key = f"{inst_id}_{pos_side}"
        if key not in expected:  # 只保留最新的记录
            expected[key] = {
                'inst_id': inst_id,
                'pos_side': pos_side,
                'expected_size': open_size,
                'open_price': open_price
            }
    
    return expected

def get_actual_positions(sub_account_name):
    """获取子账户的实际持仓"""
    try:
        response = okx_request('GET', '/api/v5/account/positions', 
                             {'instType': 'SWAP'}, 
                             sub_account_name=sub_account_name)
        
        if response['code'] != '0':
            print(f"❌ 获取持仓失败: {response}")
            return {}
        
        actual = {}
        for pos in response['data']:
            if float(pos['pos']) == 0:
                continue
                
            inst_id = pos['instId']
            pos_side = pos['posSide']
            pos_size = abs(float(pos['pos']))
            avg_price = float(pos['avgPx'])
            mgn_mode = pos['mgnMode']  # 保证金模式: cross 或 isolated
            
            key = f"{inst_id}_{pos_side}"
            actual[key] = {
                'inst_id': inst_id,
                'pos_side': pos_side,
                'actual_size': pos_size,
                'avg_price': avg_price,
                'mgn_mode': mgn_mode  # 保存保证金模式
            }
        
        return actual
        
    except Exception as e:
        print(f"❌ 获取持仓异常: {e}")
        import traceback
        traceback.print_exc()
        return {}

def close_position(inst_id, pos_side, size, mgn_mode, sub_account_name):
    """平仓指定数量的持仓"""
    try:
        # 确定平仓方向
        side = 'buy' if pos_side == 'short' else 'sell'
        
        # 构建订单参数（使用实际的保证金模式）
        order_data = {
            'instId': inst_id,
            'tdMode': mgn_mode,  # 使用实际的保证金模式: cross 或 isolated
            'side': side,
            'ordType': 'market',  # 市价单
            'sz': str(int(size)),  # 确保是整数
            'posSide': pos_side,
            'reduceOnly': True  # 只减仓
        }
        
        print(f"   📤 发送平仓请求 (保证金模式: {mgn_mode}): {json.dumps(order_data, indent=2)}")
        
        # 发送下单请求
        response = okx_request('POST', '/api/v5/trade/order', 
                             order_data, 
                             sub_account_name=sub_account_name)
        
        if response['code'] == '0':
            order_id = response['data'][0]['ordId']
            print(f"   ✅ 平仓订单已提交: {order_id}")
            return True
        else:
            print(f"   ❌ 平仓失败: {response['msg']}")
            print(f"   详细信息: {json.dumps(response, indent=2)}")
            return False
            
    except Exception as e:
        print(f"   ❌ 平仓异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_positions(sub_account_name='Wu666666', dry_run=True):
    """修正持仓
    
    Args:
        sub_account_name: 子账户名称
        dry_run: True=仅模拟，不实际操作; False=实际执行
    """
    print("=" * 100)
    print(f"🔍 子账户持仓纠错系统 - {sub_account_name}")
    print(f"模式: {'🧪 模拟运行（不实际操作）' if dry_run else '⚠️  实际执行'}")
    print("=" * 100)
    
    # 获取预期持仓和实际持仓
    expected = get_expected_positions()
    actual = get_actual_positions(sub_account_name)
    
    print(f"\n📊 预期持仓配置: {len(expected)} 个")
    print(f"📊 实际持仓: {len(actual)} 个")
    
    # 检查每个实际持仓
    issues = []
    
    for key, actual_pos in actual.items():
        inst_id = actual_pos['inst_id']
        pos_side = actual_pos['pos_side']
        actual_size = actual_pos['actual_size']
        mgn_mode = actual_pos.get('mgn_mode', 'cross')  # 获取保证金模式，默认cross
        
        if key in expected:
            expected_size = expected[key]['expected_size']
            
            # 计算差异
            diff = actual_size - expected_size
            diff_pct = (diff / expected_size * 100) if expected_size > 0 else 0
            
            if abs(diff) > 0.1:  # 容差 0.1 张
                status = "🔴 多开" if diff > 0 else "🟡 少开"
                issues.append({
                    'inst_id': inst_id,
                    'pos_side': pos_side,
                    'expected_size': expected_size,
                    'actual_size': actual_size,
                    'diff': diff,
                    'diff_pct': diff_pct,
                    'status': status,
                    'mgn_mode': mgn_mode  # 保存保证金模式
                })
        else:
            # 没有预期持仓，但有实际持仓（可能是主账户的持仓）
            print(f"\n💡 发现非锚定单持仓: {inst_id} {pos_side} {actual_size:.1f} 张（可能是主账户持仓，不处理）")
    
    # 显示问题列表
    if not issues:
        print("\n✅ 没有发现持仓异常！")
        return
    
    print(f"\n⚠️  发现 {len(issues)} 个持仓异常:")
    print("=" * 100)
    print(f"{'币种':<20} {'方向':<10} {'预期':<10} {'实际':<10} {'差异':<10} {'差异%':<12} {'状态':<15}")
    print("=" * 100)
    
    for issue in issues:
        print(f"{issue['inst_id']:<20} {issue['pos_side']:<10} "
              f"{issue['expected_size']:<10.1f} {issue['actual_size']:<10.1f} "
              f"{issue['diff']:<10.1f} {issue['diff_pct']:<12.1f}% {issue['status']:<15}")
    
    # 修正持仓
    print("\n" + "=" * 100)
    print("🔧 开始修正持仓...")
    print("=" * 100)
    
    for issue in issues:
        inst_id = issue['inst_id']
        pos_side = issue['pos_side']
        expected_size = issue['expected_size']
        actual_size = issue['actual_size']
        diff = issue['diff']
        mgn_mode = issue.get('mgn_mode', 'cross')  # 获取保证金模式
        
        if diff > 0:
            # 多开了，需要平仓
            excess_size = diff
            print(f"\n🔴 {inst_id} {pos_side} 多开了 {excess_size:.1f} 张")
            print(f"   预期: {expected_size:.1f} 张 | 实际: {actual_size:.1f} 张 | 差异: {diff:.1f} 张 ({issue['diff_pct']:.1f}%)")
            print(f"   保证金模式: {mgn_mode}")
            
            if dry_run:
                print(f"   🧪 [模拟] 应该平仓 {excess_size:.1f} 张 (保证金模式: {mgn_mode})")
            else:
                print(f"   ⚠️  [执行] 正在平仓 {excess_size:.1f} 张...")
                success = close_position(inst_id, pos_side, excess_size, mgn_mode, sub_account_name)
                if success:
                    print(f"   ✅ 平仓完成，等待3秒...")
                    time.sleep(3)
                else:
                    print(f"   ❌ 平仓失败")
        
        elif diff < 0:
            # 少开了，需要补仓（但要等亏损时才补）
            shortage = abs(diff)
            print(f"\n🟡 {inst_id} {pos_side} 少开了 {shortage:.1f} 张")
            print(f"   预期: {expected_size:.1f} 张 | 实际: {actual_size:.1f} 张 | 差异: {diff:.1f} 张 ({issue['diff_pct']:.1f}%)")
            print(f"   💡 根据策略，补仓需要等到亏损时执行，暂不处理")
    
    print("\n" + "=" * 100)
    if dry_run:
        print("🧪 模拟运行完成！如需实际执行，请使用参数: --execute")
    else:
        print("✅ 持仓修正完成！")
        print("\n💡 请等待几秒后刷新持仓页面查看结果")
    print("=" * 100)

if __name__ == '__main__':
    # 检查命令行参数
    dry_run = True
    sub_account_name = 'Wu666666'  # 默认子账户
    
    if '--execute' in sys.argv:
        dry_run = False
        print("\n⚠️  警告：将实际执行平仓操作！")
        print("⚠️  这将修正子账户中过量开仓的持仓")
        print("⚠️  按 Ctrl+C 取消，或等待 5 秒后自动开始...")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n❌ 操作已取消")
            sys.exit(0)
    
    if '--account' in sys.argv:
        idx = sys.argv.index('--account')
        if idx + 1 < len(sys.argv):
            sub_account_name = sys.argv[idx + 1]
    
    fix_positions(sub_account_name=sub_account_name, dry_run=dry_run)
