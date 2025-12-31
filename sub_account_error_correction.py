#!/usr/bin/env python3
"""
子账户纠错机制

功能：
1. 检查维护次数和实际保证金是否匹配
2. 自动调整保证金到目标值
3. 如果有维护记录但维护次数没有增加，自动修复维护次数

规则：
- 维护次数0或1：目标10U（允许范围9.5-10.5U）
- 维护次数2：目标20U（允许范围19-21U）
"""

import json
import time
import requests
import hmac
import base64
import hashlib
from datetime import datetime, timezone, timedelta
import traceback

# 配置
CHECK_INTERVAL = 300  # 5分钟检查一次
OKEX_REST_URL = 'https://www.okx.com'

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

def get_china_today():
    """获取北京时间的今天日期"""
    return get_china_time().strftime('%Y-%m-%d')

def log(msg):
    """打印日志"""
    print(f"[{get_china_time().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_config():
    """加载配置文件"""
    try:
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"❌ 加载配置文件失败: {e}")
        return None

def get_maintenance_record(account_name, inst_id, pos_side):
    """获取维护记录"""
    try:
        with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        key = f"{account_name}_{inst_id}_{pos_side}"
        if key in data:
            record = data[key]
            today = get_china_today()
            if record.get('date') == today:
                return record.get('count', 0), record
        return 0, None
    except FileNotFoundError:
        return 0, None
    except Exception as e:
        log(f"⚠️ 读取维护记录失败: {e}")
        return 0, None

def get_signature(timestamp, method, request_path, body, secret_key):
    """生成OKEx API签名"""
    if body:
        body_str = json.dumps(body)
    else:
        body_str = ''
    
    prehash_string = timestamp + method + request_path + body_str
    signature = base64.b64encode(
        hmac.new(secret_key.encode(), prehash_string.encode(), hashlib.sha256).digest()
    ).decode()
    return signature

def get_headers(method, request_path, body, api_key, secret_key, passphrase):
    """生成请求头"""
    timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
    signature = get_signature(timestamp, method, request_path, body, secret_key)
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    return headers

def get_position(account, inst_id, pos_side):
    """获取持仓信息"""
    try:
        request_path = f'/api/v5/account/positions?instType=SWAP&instId={inst_id}'
        headers = get_headers('GET', request_path, None, 
                            account['api_key'], account['secret_key'], account['passphrase'])
        
        response = requests.get(OKEX_REST_URL + request_path, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('code') == '0' and result.get('data'):
            for pos in result['data']:
                if pos.get('posSide') == pos_side and float(pos.get('pos', 0)) > 0:
                    return {
                        'inst_id': inst_id,
                        'pos_side': pos_side,
                        'pos_size': float(pos.get('pos', 0)),
                        'margin': float(pos.get('margin', 0)),
                        'mark_price': float(pos.get('markPx', 0)),
                        'lever': int(pos.get('lever', 10)),
                        'mgn_mode': pos.get('mgnMode', 'cross')
                    }
        return None
    except Exception as e:
        log(f"❌ 获取持仓失败 {inst_id} {pos_side}: {e}")
        return None

def adjust_leverage(account, inst_id, pos_side, current_lever, target_lever=10):
    """调整杠杆倍数到目标值"""
    try:
        if current_lever == target_lever:
            log(f"   ✓ 杠杆倍数正确: {current_lever}x")
            return True
        
        log(f"   ⚠️ 杠杆倍数不正确: {current_lever}x，目标: {target_lever}x")
        
        # 调用OKEx API设置杠杆倍数
        path = '/api/v5/account/set-leverage'
        
        body = {
            'instId': inst_id,
            'lever': str(target_lever),
            'mgnMode': 'isolated',  # 逐仓
            'posSide': pos_side
        }
        
        headers = get_headers('POST', path, body,
                            account['api_key'], account['secret_key'], account['passphrase'])
        
        response = requests.post(OKEX_REST_URL + path, 
                               headers=headers,
                               json=body,
                               timeout=30)
        
        result = response.json()
        
        if result.get('code') == '0':
            log(f"   ✅ 杠杆倍数调整成功: {current_lever}x → {target_lever}x")
            return True
        else:
            log(f"   ❌ 杠杆倍数调整失败: {result.get('msg', 'Unknown error')}")
            log(f"      完整响应: {result}")
            return False
            
    except Exception as e:
        log(f"   ❌ 调整杠杆倍数异常: {e}")
        log(traceback.format_exc())
        return False

def adjust_margin(account, inst_id, pos_side, current_margin, target_margin, pos_size, mark_price, lever):
    """调整保证金到目标值（逐仓模式）"""
    try:
        margin_diff = current_margin - target_margin
        
        if abs(margin_diff) < 0.5:
            log(f"   ✓ 保证金在允许范围内: {current_margin:.2f}U (目标: {target_margin}U)")
            return True
        
        # 在逐仓模式下，调整保证金需要使用 position/margin-balance API
        path = '/api/v5/account/position/margin-balance'
        
        if margin_diff > 0:
            # 保证金过多，需要转出
            # 计算安全可转出金额：需要考虑维持保证金和安全缓冲
            notional = pos_size * mark_price  # 持仓名义价值
            maintenance_margin = notional * 0.004  # 维持保证金率约0.4%（根据具体币种可能不同）
            
            # 对于大持仓，使用更大的安全缓冲
            if notional > 500:
                safety_buffer = notional * 0.02  # 2%的安全缓冲
            else:
                safety_buffer = 1.5  # 1.5U安全缓冲
            
            # 转出后必须保留：维持保证金 + 安全缓冲
            min_required_margin = maintenance_margin + safety_buffer
            
            # 最大可转出 = 当前保证金 - 最小需要保证金
            max_transferable = current_margin - min_required_margin
            
            log(f"   💡 当前保证金: {current_margin:.2f}U")
            log(f"   💡 持仓名义价值: {notional:.2f}U")
            log(f"   💡 维持保证金: {maintenance_margin:.4f}U")
            log(f"   💡 最小需要: {min_required_margin:.2f}U")
            log(f"   💡 最大可转出: {max_transferable:.2f}U")
            
            if max_transferable <= 0:
                log(f"   ⚠️ 当前无可转出保证金，跳过调整")
                return False
            
            # 选择较小的：要转出的金额 vs 最大可转出金额
            # 但为了避免OKEx 59301错误，对大持仓使用更保守的策略
            if notional > 500:
                # 大持仓：每次最多转出最大可转出的30%
                safe_reduce = max_transferable * 0.3
                ideal_reduce = min(margin_diff, safe_reduce)
            else:
                # 小持仓：每次最多5U
                ideal_reduce = min(margin_diff, max_transferable)
            
            reduce_amount = min(ideal_reduce, 5.0)  # 最终限制5U/次
            
            log(f"   🔧 保证金过多: {current_margin:.2f}U，目标: {target_margin}U")
            log(f"   💡 理想转出: {ideal_reduce:.2f}U，实际转出: {reduce_amount:.2f}U (限制5U/次)")
            log(f"   📤 转出 {reduce_amount:.2f}U 保证金")
            
            body = {
                'instId': inst_id,
                'posSide': pos_side,
                'type': 'reduce',  # 减少保证金
                'amt': str(round(reduce_amount, 4)),  # 保留4位小数
                'ccy': 'USDT'
            }
        else:
            # 保证金不足，需要转入
            add_amount = -margin_diff
            
            log(f"   🔧 保证金不足: {current_margin:.2f}U，目标: {target_margin}U")
            log(f"   📥 转入 {add_amount:.2f}U 保证金")
            
            body = {
                'instId': inst_id,
                'posSide': pos_side,
                'type': 'add',  # 增加保证金
                'amt': str(round(add_amount, 2)),
                'ccy': 'USDT'
            }
        
        # 调用OKEx API
        headers = get_headers('POST', path, body, 
                            account['api_key'], account['secret_key'], account['passphrase'])
        
        response = requests.post(OKEX_REST_URL + path, headers=headers, json=body, timeout=10)
        result = response.json()
        
        if result.get('code') == '0':
            log(f"   ✅ 保证金调整成功")
            return True
        else:
            log(f"   ❌ 保证金调整失败: {result.get('msg', '未知错误')}")
            log(f"   错误码: {result.get('code')}")
            log(f"   完整响应: {result}")
            return False
    
    except Exception as e:
        log(f"   ❌ 调整保证金异常: {e}")
        log(traceback.format_exc())
        return False

def check_and_correct(account):
    """检查并纠正一个子账户的所有持仓"""
    try:
        account_name = account['account_name']
        log(f"\n🔍 检查账户: {account_name}")
        
        # 获取所有持仓
        response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions', timeout=10)
        data = response.json()
        
        if not data.get('success'):
            log(f"❌ 获取持仓失败")
            return
        
        positions = [pos for pos in data['positions'] if pos['account_name'] == account_name]
        
        if not positions:
            log(f"   无持仓")
            return
        
        log(f"   持仓数量: {len(positions)}")
        
        # 逐个检查持仓
        for pos in positions:
            inst_id = pos['inst_id']
            pos_side = pos['pos_side']
            current_margin = pos['margin']
            
            # 获取维护次数
            maintenance_count, record = get_maintenance_record(account_name, inst_id, pos_side)
            
            # 确定目标保证金和目标持仓名义价值
            if maintenance_count in [0, 1]:
                # 维护次数0或1：目标10U保证金，约100U持仓
                target_margin = 10.0
                target_notional = 100.0  # 目标持仓名义价值
                tolerance = 0.5  # 保证金允许范围9.5-10.5U
                margin_range = "9.5-10.5U"
            elif maintenance_count == 2:
                # 维护次数2：目标20U保证金，约200U持仓
                target_margin = 20.0
                target_notional = 200.0
                tolerance = 1.0  # 保证金允许范围19-21U
                margin_range = "19-21U"
            else:
                log(f"   ⚠️  {inst_id} {pos_side}: 维护次数异常({maintenance_count})，跳过")
                continue
            
            log(f"\n   📊 {inst_id} {pos_side}:")
            log(f"      维护次数: {maintenance_count}")
            log(f"      当前保证金: {current_margin:.2f}U")
            log(f"      目标保证金: {target_margin}U (允许范围: {margin_range})")
            
            # 获取详细持仓信息
            position_detail = get_position(account, inst_id, pos_side)
            if not position_detail:
                log(f"      ❌ 无法获取详细持仓信息")
                continue
            
            pos_size = position_detail['pos_size']
            mark_price = position_detail['mark_price']
            current_notional = pos_size * mark_price
            current_lever = position_detail['lever']  # 当前杠杆倍数
            
            log(f"      持仓量: {pos_size}")
            log(f"      标记价格: {mark_price:.4f}")
            log(f"      持仓名义价值: {current_notional:.2f}U")
            log(f"      目标名义价值: {target_notional:.2f}U")
            log(f"      当前杠杆: {current_lever}x")
            
            # 1. 先检查并调整杠杆倍数
            if current_lever != 10:
                log(f"      ⚠️  杠杆倍数不正确: {current_lever}x (目标: 10x)")
                adjust_leverage(account, inst_id, pos_side, current_lever, target_lever=10)
                # 调整杠杆后等待3秒
                time.sleep(3)
            
            # 2. 检查持仓名义价值是否过大
            if current_notional > target_notional * 1.5:
                log(f"      ⚠️  持仓过大({current_notional:.2f}U > {target_notional*1.5:.2f}U)，需要先平仓")
                
                # 计算需要平掉的数量
                target_pos_size = target_notional / mark_price
                close_size = int(pos_size - target_pos_size)
                
                if close_size > 0:
                    log(f"      📤 平仓 {close_size} 张 (从{pos_size}张降到{target_pos_size:.2f}张)")
                    
                    # 调用平仓API
                    try:
                        response = requests.post('http://localhost:5000/api/anchor/close-sub-account-position',
                                               json={
                                                   'account_name': account_name,
                                                   'inst_id': inst_id,
                                                   'pos_side': pos_side,
                                                   'close_size': close_size,
                                                   'reason': '纠错机制：持仓过大'
                                               },
                                               timeout=30)
                        result = response.json()
                        
                        if result.get('success'):
                            log(f"      ✅ 平仓成功")
                            # 等待5秒再继续
                            time.sleep(5)
                        else:
                            log(f"      ❌ 平仓失败: {result.get('message')}")
                            # 平仓失败，跳过保证金调整
                            continue
                    except Exception as e:
                        log(f"      ❌ 平仓异常: {e}")
                        continue
            
            # 3. 检查保证金是否在允许范围内
            if maintenance_count in [0, 1]:
                in_range = 9.5 <= current_margin <= 10.5
            elif maintenance_count == 2:
                in_range = 19 <= current_margin <= 21
            else:
                in_range = False
            
            if in_range:
                log(f"      ✅ 保证金在允许范围内")
                continue
            
            # 4. 调整保证金
            log(f"      ⚠️  保证金超出范围，需要调整")
            
            success = adjust_margin(
                account, inst_id, pos_side,
                current_margin, target_margin,
                position_detail['pos_size'],
                position_detail['mark_price'],
                position_detail['lever']
            )
            
            if success:
                log(f"      ✅ 保证金调整完成")
            
            # 等待一段时间再处理下一个
            time.sleep(2)
    
    except Exception as e:
        log(f"❌ 检查纠错失败: {e}")
        log(traceback.format_exc())

def main_loop():
    """主循环"""
    log("🚀 子账户纠错机制启动")
    log(f"⏱️  检查间隔: {CHECK_INTERVAL}秒")
    log(f"📋 纠错规则:")
    log(f"   维护次数0或1: 目标10U (允许范围9.5-10.5U)")
    log(f"   维护次数2: 目标20U (允许范围19-21U)")
    
    while True:
        try:
            # 加载配置
            config = load_config()
            if not config:
                log("⚠️  配置文件加载失败，等待下次检查")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 检查所有启用的子账户
            for account in config['sub_accounts']:
                if account.get('enabled'):
                    check_and_correct(account)
            
            log(f"\n😴 等待 {CHECK_INTERVAL} 秒后继续检查...")
            time.sleep(CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            log("\n👋 程序退出")
            break
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())
            time.sleep(60)  # 发生异常后等待1分钟

if __name__ == '__main__':
    main_loop()
