#!/usr/bin/env python3
"""
子账户保证金紧急纠错脚本

规则（正确的）：
- 维护次数 0次: 10 USDT
- 维护次数 1次: 10 USDT
- 维护次数 2次: 20 USDT
- 维护次数 3次及以上: 30 USDT
"""

import json
import requests
import hmac
import base64
import hashlib
from datetime import datetime, timezone, timedelta
import time
import traceback

OKEX_REST_URL = 'https://www.okx.com'

def get_china_time():
    """获取北京时间"""
    return datetime.now(timezone(timedelta(hours=8)))

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

def add_margin(account, inst_id, pos_side, add_amount):
    """增加保证金"""
    try:
        path = '/api/v5/account/position/margin-balance'
        
        body = {
            'instId': inst_id,
            'posSide': pos_side,
            'type': 'add',
            'amt': str(round(add_amount, 2)),
            'ccy': 'USDT'
        }
        
        headers = get_headers('POST', path, body, 
                            account['api_key'], account['secret_key'], account['passphrase'])
        
        response = requests.post(OKEX_REST_URL + path, headers=headers, json=body, timeout=30)
        result = response.json()
        
        if result.get('code') == '0':
            log(f"   ✅ 保证金增加成功: +{add_amount:.2f} USDT")
            return True
        else:
            log(f"   ❌ 保证金增加失败: {result.get('msg', '未知错误')}")
            log(f"   错误码: {result.get('code')}")
            return False
    
    except Exception as e:
        log(f"   ❌ 增加保证金异常: {e}")
        log(traceback.format_exc())
        return False

def fix_all_positions():
    """修复所有子账户持仓的保证金"""
    log("=" * 120)
    log("🚨 开始执行子账户保证金紧急纠错")
    log("=" * 120)
    
    # 加载配置
    config = load_config()
    if not config:
        log("❌ 无法加载配置文件")
        return
    
    # 获取子账户
    sub_accounts = config.get('sub_accounts', [])
    if not sub_accounts:
        log("❌ 未找到子账户配置")
        return
    
    account = sub_accounts[0]  # 假设只有一个子账户
    account_name = account['account_name']
    
    log(f"\n📋 子账户: {account_name}")
    
    # 加载纠错列表
    try:
        with open('/tmp/subaccount_corrections.json', 'r') as f:
            corrections = json.load(f)
    except Exception as e:
        log(f"❌ 无法加载纠错列表: {e}")
        return
    
    log(f"📊 需要纠错的持仓数量: {len(corrections)}")
    
    # 逐个纠错
    success_count = 0
    failed_count = 0
    
    for i, correction in enumerate(corrections, 1):
        inst_id = correction['inst_id']
        pos_side = correction['pos_side']
        current_margin = correction['current_margin']
        expected_margin = correction['expected_margin']
        margin_diff = correction['margin_diff']
        maintenance_count = correction['maintenance_count']
        
        log(f"\n【{i}/{len(corrections)}】 {inst_id} {pos_side}")
        log(f"   当前保证金: {current_margin:.4f} USDT")
        log(f"   目标保证金: {expected_margin:.1f} USDT")
        log(f"   需要补充: {margin_diff:.4f} USDT")
        log(f"   维护次数: {maintenance_count} 次")
        
        # 执行补仓
        success = add_margin(account, inst_id, pos_side, margin_diff)
        
        if success:
            success_count += 1
            log(f"   ✅ 纠错成功 ({success_count}/{len(corrections)})")
        else:
            failed_count += 1
            log(f"   ❌ 纠错失败 ({failed_count}/{len(corrections)})")
        
        # 等待2秒再处理下一个
        if i < len(corrections):
            time.sleep(2)
    
    # 总结
    log("\n" + "=" * 120)
    log(f"🎯 纠错完成!")
    log(f"   ✅ 成功: {success_count} 个")
    log(f"   ❌ 失败: {failed_count} 个")
    log(f"   📊 总计: {len(corrections)} 个")
    log("=" * 120)

if __name__ == '__main__':
    try:
        fix_all_positions()
    except KeyboardInterrupt:
        log("\n👋 用户中断")
    except Exception as e:
        log(f"\n❌ 程序异常: {e}")
        log(traceback.format_exc())
