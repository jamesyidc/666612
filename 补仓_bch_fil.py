#!/usr/bin/env python3
"""
为BCH和FIL补仓到10U
"""
import requests
import json
from datetime import datetime, timezone, timedelta

def log(msg):
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")

def add_margin_to_position(account_name, inst_id, pos_side, target_margin):
    """为指定持仓增加保证金到目标值"""
    try:
        # 获取当前持仓信息
        response = requests.get('http://localhost:5000/api/anchor-system/sub-account-positions', timeout=10)
        data = response.json()
        
        # 查找目标持仓
        target_pos = None
        for pos in data['positions']:
            if pos['account_name'] == account_name and pos['inst_id'] == inst_id and pos['pos_side'] == pos_side:
                target_pos = pos
                break
        
        if not target_pos:
            log(f"❌ 未找到持仓: {inst_id} {pos_side}")
            return False
        
        current_margin = target_pos['margin']
        add_amount = target_margin - current_margin
        
        if add_amount <= 0.5:
            log(f"✅ {inst_id} 保证金已足够: {current_margin:.2f}U")
            return True
        
        log(f"📊 {inst_id} {pos_side}")
        log(f"   当前保证金: {current_margin:.2f}U")
        log(f"   目标保证金: {target_margin}U")
        log(f"   需要补: {add_amount:.2f}U")
        
        # 加载子账户配置
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 查找目标子账户
        sub_account = None
        for account in config['sub_accounts']:
            if account['account_name'] == account_name:
                sub_account = account
                break
        
        if not sub_account:
            log(f"❌ 未找到子账户: {account_name}")
            return False
        
        # 使用补仓脚本中的逻辑
        import hmac
        import hashlib
        import base64
        
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        # 获取当前价格
        ticker_url = "https://www.okx.com/api/v5/market/ticker"
        ticker_response = requests.get(ticker_url, params={'instId': inst_id}, timeout=10)
        
        if ticker_response.status_code != 200:
            log(f"❌ 获取价格失败: {ticker_response.status_code}")
            return False
        
        ticker_data = ticker_response.json()
        if ticker_data.get('code') != '0':
            log(f"❌ 获取价格失败: {ticker_data.get('msg')}")
            return False
        
        last_price = float(ticker_data['data'][0]['last'])
        log(f"   📊 当前价格: ${last_price:.4f}")
        
        # 计算需要加仓的张数（10倍杠杆）
        lever = 10
        size = round((add_amount * lever) / last_price)
        
        if size < 1:
            size = 1
        
        log(f"   📊 计算补仓张数: {size}张 (目标补保证金: {add_amount:.2f}U)")
        
        # 生成OKEx签名
        def get_okex_headers(api_key, secret_key, passphrase, method, request_path, body=''):
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            
            if body:
                body_str = json.dumps(body)
            else:
                body_str = ''
            
            message = timestamp + method + request_path + body_str
            mac = hmac.new(
                bytes(secret_key, encoding='utf8'),
                bytes(message, encoding='utf8'),
                digestmod=hashlib.sha256
            )
            signature = base64.b64encode(mac.digest()).decode()
            
            headers = {
                'OK-ACCESS-KEY': api_key,
                'OK-ACCESS-SIGN': signature,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': passphrase,
                'Content-Type': 'application/json'
            }
            
            return headers
        
        # 下单
        request_path = '/api/v5/trade/order'
        order_data = {
            'instId': inst_id,
            'tdMode': 'isolated',
            'side': 'buy' if pos_side == 'long' else 'sell',
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(size)
        }
        
        headers = get_okex_headers(api_key, secret_key, passphrase, 'POST', request_path, order_data)
        
        url = f"https://www.okx.com{request_path}"
        response = requests.post(url, headers=headers, json=order_data, timeout=10)
        
        if response.status_code != 200:
            log(f"❌ 补仓失败: HTTP {response.status_code}")
            return False
        
        result = response.json()
        
        if result.get('code') == '0':
            order_id = result['data'][0]['ordId']
            log(f"   ✅ 补仓成功: 订单ID {order_id}")
            return True
        else:
            log(f"❌ 补仓失败: {result.get('msg')}")
            return False
            
    except Exception as e:
        log(f"❌ 补仓异常: {e}")
        import traceback
        log(traceback.format_exc())
        return False

def main():
    log("="*60)
    log("🚀 BCH和FIL补仓工具")
    log("="*60)
    
    # 补仓列表
    补仓列表 = [
        {'account_name': 'Wu666666', 'inst_id': 'BCH-USDT-SWAP', 'pos_side': 'long', 'target_margin': 10},
        {'account_name': 'Wu666666', 'inst_id': 'FIL-USDT-SWAP', 'pos_side': 'long', 'target_margin': 10},
    ]
    
    成功 = 0
    失败 = 0
    
    for 补仓 in 补仓列表:
        log(f"\n📍 处理: {补仓['inst_id']} {补仓['pos_side']}")
        
        success = add_margin_to_position(
            补仓['account_name'],
            补仓['inst_id'],
            补仓['pos_side'],
            补仓['target_margin']
        )
        
        if success:
            成功 += 1
        else:
            失败 += 1
    
    log("\n" + "="*60)
    log(f"📊 补仓完成: 成功{成功}个，失败{失败}个")
    log("="*60)

if __name__ == '__main__':
    main()
