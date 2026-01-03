#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主账户交易对保护守护进程
- 每分钟检查主账户的交易对数量
- 如果发现交易对减少，立即补1U保证金仓位
- 记录所有保护操作
"""

import sys
import os
sys.path.append('/home/user/webapp')

import time
import json
import hmac
import base64
import hashlib
from datetime import datetime
import requests
from pytz import timezone

# 北京时区
BEIJING_TZ = timezone('Asia/Shanghai')

def log(msg):
    """带时间戳的日志"""
    now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] {msg}", flush=True)

def load_config():
    """加载主账户配置"""
    try:
        with open('/home/user/webapp/anchor_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"❌ 加载配置失败: {e}")
        return None

def save_config(config):
    """保存主账户配置"""
    try:
        with open('/home/user/webapp/anchor_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log(f"❌ 保存配置失败: {e}")
        return False

def load_anchor_credentials():
    """加载主账户API凭证"""
    try:
        # 从 okex_api_config.py 导入凭证
        import sys
        sys.path.append('/home/user/webapp')
        from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE
        
        return {
            'api_key': OKEX_API_KEY,
            'secret_key': OKEX_SECRET_KEY,
            'passphrase': OKEX_PASSPHRASE
        }
    except Exception as e:
        log(f"❌ 加载API凭证失败: {e}")
        return None

def sign_request(timestamp, method, request_path, body, secret_key):
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

def get_positions(api_key, secret_key, passphrase):
    """获取主账户所有持仓"""
    try:
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        method = 'GET'
        request_path = '/api/v5/account/positions?instType=SWAP'
        
        signature = sign_request(timestamp, method, request_path, '', secret_key)
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'https://www.okx.com{request_path}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0':
                # 只返回有持仓的交易对
                positions = []
                for pos in data.get('data', []):
                    pos_size = float(pos.get('pos', 0))
                    if pos_size != 0:
                        positions.append({
                            'instId': pos.get('instId'),
                            'posSide': pos.get('posSide'),
                            'pos': pos_size,
                            'margin': float(pos.get('margin', 0)),
                            'avgPx': float(pos.get('avgPx', 0))
                        })
                return positions
        
        log(f"❌ 获取持仓失败: {response.text}")
        return None
        
    except Exception as e:
        log(f"❌ 获取持仓异常: {e}")
        return None

def open_position(inst_id, pos_side, margin_usdt, api_key, secret_key, passphrase):
    """
    开1U保证金仓位
    """
    try:
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        method = 'POST'
        request_path = '/api/v5/trade/order'
        
        # 构建订单参数
        body = {
            'instId': inst_id,
            'tdMode': 'cross',  # 全仓模式
            'side': 'buy' if pos_side == 'long' else 'sell',
            'posSide': pos_side,
            'ordType': 'market',  # 市价单
            'sz': str(margin_usdt)  # 使用保证金数量
        }
        
        signature = sign_request(timestamp, method, request_path, body, secret_key)
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'https://www.okx.com{request_path}',
            headers=headers,
            json=body,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0':
                order_id = data['data'][0].get('ordId')
                log(f"✅ 补仓成功: {inst_id} {pos_side} {margin_usdt}U | 订单ID: {order_id}")
                return True
            else:
                log(f"❌ 补仓失败: {data.get('msg')}")
                return False
        else:
            log(f"❌ 补仓请求失败: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ 补仓异常: {e}")
        return False

def check_and_protect():
    """检查并保护交易对"""
    try:
        # 加载配置
        config = load_config()
        if not config:
            return
        
        # 检查是否启用
        protect_config = config.get('protect_pairs', {})
        if not protect_config.get('enabled', False):
            return
        
        # 加载主账户API凭证
        credentials = load_anchor_credentials()
        if not credentials:
            log("❌ 无法加载主账户API凭证")
            return
        
        api_key = credentials.get('api_key')
        secret_key = credentials.get('secret_key')
        passphrase = credentials.get('passphrase')
        
        if not all([api_key, secret_key, passphrase]):
            log("❌ 主账户API配置不完整")
            return
        
        # 获取当前持仓
        current_positions = get_positions(api_key, secret_key, passphrase)
        if current_positions is None:
            return
        
        # 获取当前交易对列表（去重）
        current_pairs = set()
        for pos in current_positions:
            pair_key = f"{pos['instId']}_{pos['posSide']}"
            current_pairs.add(pair_key)
        
        log(f"📊 当前持仓交易对数量: {len(current_pairs)}")
        
        # 获取保护列表
        protected_pairs = set(protect_config.get('protected_pairs', []))
        
        # 如果是第一次运行或保护列表为空，初始化保护列表
        if not protected_pairs:
            protect_config['protected_pairs'] = list(current_pairs)
            config['protect_pairs'] = protect_config
            save_config(config)
            log(f"✅ 初始化保护交易对列表: {len(current_pairs)}个交易对")
            return
        
        # 检查是否有交易对丢失
        missing_pairs = protected_pairs - current_pairs
        
        if missing_pairs:
            log(f"⚠️ 发现丢失的交易对: {missing_pairs}")
            
            min_margin = protect_config.get('min_margin_usdt', 1)
            
            # 逐个补仓
            for pair_key in missing_pairs:
                inst_id, pos_side = pair_key.split('_')
                log(f"🔧 准备补仓: {inst_id} {pos_side} {min_margin}U")
                
                success = open_position(inst_id, pos_side, min_margin, api_key, secret_key, passphrase)
                
                if success:
                    log(f"✅ 补仓成功: {pair_key}")
                    # 等待一下，避免频繁下单
                    time.sleep(2)
                else:
                    log(f"❌ 补仓失败: {pair_key}")
        
        # 更新保护列表（添加新的交易对）
        new_pairs = current_pairs - protected_pairs
        if new_pairs:
            log(f"📝 发现新交易对，添加到保护列表: {new_pairs}")
            protect_config['protected_pairs'] = list(current_pairs)
            config['protect_pairs'] = protect_config
            save_config(config)
        
    except Exception as e:
        import traceback
        log(f"❌ 保护检查失败: {e}")
        log(traceback.format_exc())

def main():
    """主函数"""
    log("=" * 80)
    log("🛡️ 主账户交易对保护守护进程启动")
    log("📊 功能: 监控主账户交易对数量，自动补仓丢失的交易对")
    log("⏰ 检查间隔: 60秒 (1分钟)")
    log("=" * 80)
    log("")
    
    while True:
        try:
            log("📊 开始检查交易对保护...")
            check_and_protect()
            log("⏰ 等待60秒后进行下次检查...")
            log("")
            time.sleep(60)
            
        except KeyboardInterrupt:
            log("👋 收到停止信号，正在退出...")
            break
        except Exception as e:
            import traceback
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())
            time.sleep(60)

if __name__ == '__main__':
    main()
