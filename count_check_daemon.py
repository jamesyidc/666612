#!/usr/bin/env python3
"""
计次检测守护进程
每天北京时间凌晨2点检测计次是否大于2，如果小于2则发送Telegram提醒
"""

import time
import sqlite3
import requests
from datetime import datetime
import pytz

# Telegram配置
TELEGRAM_BOT_TOKEN = "7791348931:AAGufym6KUqRxX8oNd9h5fRp0xtk05UdOuU"
TELEGRAM_CHAT_ID = "6827427968"

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def send_telegram_message(message):
    """发送Telegram消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Telegram消息发送成功")
            return True
        else:
            print(f"❌ Telegram消息发送失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 发送Telegram消息异常: {e}")
        return False

def get_latest_count():
    """获取最新的计次数据"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT snapshot_time, count 
            FROM crypto_snapshots 
            ORDER BY snapshot_date DESC, snapshot_time DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'snapshot_time': row[0],
                'count': row[1]
            }
        return None
        
    except Exception as e:
        print(f"❌ 获取计次数据失败: {e}")
        return None

def check_count():
    """检测计次并发送提醒"""
    now = datetime.now(BEIJING_TZ)
    print(f"\n{'='*60}")
    print(f"⏰ 开始检测计次... ({now.strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"{'='*60}")
    
    # 获取最新计次
    data = get_latest_count()
    
    if not data:
        message = "⚠️ <b>计次检测警告</b>\n\n无法获取计次数据！\n\n请检查数据库连接。"
        print("⚠️ 无法获取计次数据")
        send_telegram_message(message)
        return
    
    count = data['count']
    snapshot_time = data['snapshot_time']
    
    print(f"📊 当前计次: {count}")
    print(f"📅 数据时间: {snapshot_time}")
    
    # 检查计次是否小于2
    if count < 2:
        # 发送Telegram提醒
        message = f"""
🚨 <b>计次异常提醒</b>

⚠️ 当前计次: <b>{count}</b>
❌ 低于阈值: 2

📅 数据时间: {snapshot_time}
⏰ 检测时间: {now.strftime('%Y-%m-%d %H:%M:%S')}

💡 建议：请检查市场状态和数据采集服务
"""
        print(f"⚠️ 计次{count}小于2，发送Telegram提醒...")
        send_telegram_message(message)
    else:
        print(f"✅ 计次{count}正常（>=2），无需提醒")

def wait_until_2am():
    """等待到凌晨2点"""
    while True:
        now = datetime.now(BEIJING_TZ)
        
        # 检查是否是凌晨2点
        if now.hour == 2 and now.minute == 0:
            check_count()
            # 等待70秒，避免在同一分钟内重复执行
            time.sleep(70)
        
        # 每30秒检查一次时间
        time.sleep(30)

def main():
    """主函数"""
    print("="*60)
    print("🤖 计次检测守护进程已启动")
    print("="*60)
    print(f"⏰ 检查时间: 每天北京时间 02:00")
    print(f"📊 检测条件: 计次 < 2")
    print(f"📱 提醒方式: Telegram")
    print(f"📅 启动时间: {datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 启动定时检测
    wait_until_2am()

if __name__ == "__main__":
    main()
