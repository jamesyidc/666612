#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多单开仓预警系统
根据下跌强度分级发送Telegram预警
"""

import requests
import json
import time
import sys
from datetime import datetime
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 加载配置
with open('/home/user/webapp/anchor_config.json', 'r') as f:
    config = json.load(f)

TELEGRAM_BOT_TOKEN = config['telegram']['bot_token']
TELEGRAM_CHAT_ID = config['telegram']['chat_id']

# 预警间隔（秒）
ALERT_INTERVAL = 3600  # 1小时

# 记录最后预警时间
last_alert_times = {}

def send_telegram_message(message):
    """发送Telegram消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        return response.json().get('ok', False)
    except Exception as e:
        print(f"❌ Telegram发送失败: {e}")
        return False

def get_decline_strength():
    """获取下跌强度数据"""
    try:
        response = requests.get('http://localhost:5000/api/anchor/decline-strength?trade_mode=real', timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ 获取下跌强度失败: {e}")
        return None

def check_alert_conditions(data):
    """
    检查预警条件
    
    1级强度：空单盈利>=50% 时预警
    2级强度：空单盈利>=60% 时预警  
    3级强度：空单盈利>=70% 时预警
    """
    if not data or not data.get('success'):
        return None
    
    strength_data = data['data']
    strength_level = strength_data['strength_level']
    statistics = strength_data['statistics']
    short_positions = strength_data['short_positions']
    
    # 收集高盈利空单
    high_profit_shorts = []
    
    if strength_level == 1:
        # 1级：查找盈利>=50%的空单
        high_profit_shorts = [p for p in short_positions if p['profit_rate'] >= 50]
        threshold = 50
    elif strength_level == 2:
        # 2级：查找盈利>=60%的空单
        high_profit_shorts = [p for p in short_positions if p['profit_rate'] >= 60]
        threshold = 60
    elif strength_level == 3:
        # 3级：查找盈利>=70%的空单
        high_profit_shorts = [p for p in short_positions if p['profit_rate'] >= 70]
        threshold = 70
    else:
        # 无空单或极端情况，不预警
        return None
    
    # 如果没有达到阈值的空单，不预警
    if len(high_profit_shorts) == 0:
        return None
    
    # 检查冷却时间
    alert_key = f"level_{strength_level}_threshold_{threshold}"
    now = time.time()
    if alert_key in last_alert_times:
        if now - last_alert_times[alert_key] < ALERT_INTERVAL:
            # 还在冷却期，不发送
            return None
    
    # 更新最后预警时间
    last_alert_times[alert_key] = now
    
    return {
        'strength_level': strength_level,
        'threshold': threshold,
        'high_profit_shorts': high_profit_shorts,
        'statistics': statistics,
        'buy_suggestion': strength_data['buy_suggestion']
    }

def format_alert_message(alert_data):
    """格式化预警消息"""
    level = alert_data['strength_level']
    threshold = alert_data['threshold']
    shorts = alert_data['high_profit_shorts']
    stats = alert_data['statistics']
    suggestion = alert_data['buy_suggestion']
    
    # 时间戳
    now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建消息
    message = f"""
🚨 <b>多单开仓预警</b> 🚨

⏰ 时间: {now}
📊 下跌强度: {level}级
🎯 触发条件: 空单盈利≥{threshold}%

📈 空单盈利统计:
• 总空单数: {stats['total_shorts']}
• 盈利≥70%: {stats['profit_70']}个
• 盈利≥60%: {stats['profit_60']}个
• 盈利≥50%: {stats['profit_50']}个
• 盈利≥40%: {stats['profit_40']}个

🔥 高盈利空单 (≥{threshold}%):
"""
    
    # 按盈利率排序
    shorts_sorted = sorted(shorts, key=lambda x: x['profit_rate'], reverse=True)
    for i, pos in enumerate(shorts_sorted[:10], 1):  # 最多显示前10个
        coin = pos['inst_id'].replace('-USDT-SWAP', '')
        profit = pos['profit_rate']
        message += f"{i}. {coin}: {profit:.1f}%\n"
    
    if len(shorts_sorted) > 10:
        message += f"... 还有{len(shorts_sorted) - 10}个\n"
    
    message += f"\n💡 操作建议: {suggestion}"
    
    return message

def main():
    """主函数"""
    print("🚀 多单开仓预警系统启动")
    print(f"⏱️  检查间隔: 60秒")
    print(f"🔔 预警间隔: {ALERT_INTERVAL}秒 ({ALERT_INTERVAL//3600}小时)")
    print(f"📱 Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print()
    
    while True:
        try:
            now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] 检查下跌强度...")
            
            # 获取下跌强度数据
            data = get_decline_strength()
            if data and data.get('success'):
                strength_level = data['data']['strength_level']
                strength_name = data['data']['strength_name']
                print(f"  当前: {strength_name}")
                
                # 检查是否需要预警
                alert_data = check_alert_conditions(data)
                if alert_data:
                    print(f"  ⚠️  触发预警条件！")
                    message = format_alert_message(alert_data)
                    success = send_telegram_message(message)
                    if success:
                        print(f"  ✅ Telegram预警已发送")
                    else:
                        print(f"  ❌ Telegram预警发送失败")
                else:
                    print(f"  ✓ 无需预警")
            else:
                print(f"  ❌ 获取数据失败")
            
        except Exception as e:
            print(f"❌ 主循环异常: {e}")
            import traceback
            traceback.print_exc()
        
        # 等待下一次检查
        time.sleep(60)

if __name__ == '__main__':
    main()
