#!/usr/bin/env python3
"""
逃顶快照统计数据记录器
每分钟记录一次24小时和2小时的逃顶快照统计数据，同时获取市场强度等级
"""
import sqlite3
import time
from datetime import datetime, timedelta
import pytz
import sys
import requests
import json

# 配置
SUPPORT_RESISTANCE_DB = '/home/user/webapp/support_resistance.db'
CRYPTO_DATA_DB = '/home/user/webapp/databases/crypto_data.db'
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
CHECK_INTERVAL = 60  # 每60秒检查一次

def log(message):
    """输出日志"""
    timestamp = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def get_market_strength():
    """从API获取市场强度等级"""
    try:
        # 获取下跌强度等级
        response = requests.get('http://localhost:5000/api/anchor/decline-strength', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                decline_level = data.get('level', 0)
                log(f"📊 下跌强度等级: {decline_level}")
            else:
                decline_level = 0
                log("⚠️ 获取下跌强度失败，使用默认值0")
        else:
            decline_level = 0
            log(f"⚠️ 下跌强度API返回异常状态码: {response.status_code}")
        
        # 获取上涨强度等级（通过多单盈利计算）
        # 我们需要从持仓数据中获取多单盈利情况来计算上涨强度
        # 这里调用锚点系统的持仓API
        response = requests.get('http://localhost:5000/api/anchor-system/current-positions?trade_mode=real', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                positions = data.get('positions', [])
                # 统计多单盈利情况
                long_positions = [p for p in positions if p.get('pos_side') == 'long']
                
                # 计算上涨强度等级（基于多单盈利数量和收益率）
                profit_100_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 100)
                profit_90_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 90)
                profit_80_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 80)
                profit_70_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 70)
                profit_60_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 60)
                profit_40_plus = sum(1 for p in long_positions if p.get('profit_rate', 0) >= 40)
                
                # 上涨强度等级判定逻辑（与下跌强度相同，但基于多单盈利）
                if profit_100_plus >= 1 and profit_40_plus > 10:
                    rise_level = 5  # 极端上涨
                elif profit_100_plus == 0 and profit_90_plus >= 1 and profit_80_plus >= 1 and profit_40_plus > 10:
                    rise_level = 4  # 超高强度上涨
                elif profit_100_plus == 0 and profit_90_plus == 0 and profit_80_plus == 0 and profit_70_plus >= 1 and profit_60_plus >= 2 and profit_40_plus > 8:
                    rise_level = 3  # 高强度上涨
                elif profit_100_plus == 0 and profit_90_plus == 0 and profit_80_plus == 0 and profit_70_plus == 0 and profit_60_plus >= 2 and profit_40_plus > 5:
                    rise_level = 2  # 中等强度上涨
                elif profit_100_plus == 0 and profit_90_plus == 0 and profit_80_plus == 0 and profit_70_plus == 0 and profit_60_plus == 0 and profit_40_plus >= 3:
                    rise_level = 1  # 轻度上涨
                else:
                    rise_level = 0  # 正常
                
                log(f"📈 上涨强度等级: {rise_level} (多单盈利≥40%: {profit_40_plus})")
            else:
                rise_level = 0
                log("⚠️ 获取持仓数据失败，上涨强度使用默认值0")
        else:
            rise_level = 0
            log(f"⚠️ 持仓API返回异常状态码: {response.status_code}")
        
        return {
            'decline_level': decline_level,
            'rise_level': rise_level
        }
        
    except requests.Timeout:
        log("⚠️ 获取市场强度超时，使用默认值0")
        return {'decline_level': 0, 'rise_level': 0}
    except Exception as e:
        log(f"❌ 获取市场强度失败: {e}")
        return {'decline_level': 0, 'rise_level': 0}

def calculate_stats():
    """计算逃顶快照统计数据"""
    try:
        conn = sqlite3.connect(SUPPORT_RESISTANCE_DB)
        cursor = conn.cursor()
        
        # 计算24小时前和2小时前的时间
        now = datetime.now()
        time_24h_ago = (now - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        time_2h_ago = (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取24小时内的数据
        cursor.execute('''
            SELECT 
                snapshot_time,
                scenario_3_count + scenario_4_count as escape_count
            FROM support_resistance_snapshots
            WHERE snapshot_time >= ?
            ORDER BY snapshot_time DESC
        ''', (time_24h_ago,))
        
        rows_24h = cursor.fetchall()
        
        # 计算24小时内的逃顶快照数和最大的逃顶信号数
        escape_snapshot_count_24h = sum(1 for row in rows_24h if row[1] >= 5)
        max_escape_count_24h = max([row[1] for row in rows_24h], default=0)
        
        # 获取2小时内的数据
        cursor.execute('''
            SELECT 
                snapshot_time,
                scenario_3_count + scenario_4_count as escape_count
            FROM support_resistance_snapshots
            WHERE snapshot_time >= ?
            ORDER BY snapshot_time DESC
        ''', (time_2h_ago,))
        
        rows_2h = cursor.fetchall()
        
        # 计算2小时内的逃顶快照数和最大的逃顶信号数
        escape_snapshot_count_2h = sum(1 for row in rows_2h if row[1] >= 5)
        max_escape_count_2h = max([row[1] for row in rows_2h], default=0)
        
        conn.close()
        
        return {
            'escape_24h_count': escape_snapshot_count_24h,
            'escape_2h_count': escape_snapshot_count_2h,
            'max_escape_24h': max_escape_count_24h,
            'max_escape_2h': max_escape_count_2h
        }
        
    except Exception as e:
        log(f"❌ 计算统计数据失败: {e}")
        return None

def save_stats(stats, market_strength):
    """保存统计数据到数据库"""
    try:
        stat_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:00')  # 精确到分钟
        
        conn = sqlite3.connect(CRYPTO_DATA_DB)
        cursor = conn.cursor()
        
        # 插入或更新统计数据（包含市场强度等级）
        cursor.execute('''
            INSERT OR REPLACE INTO escape_snapshot_stats 
            (stat_time, escape_24h_count, escape_2h_count, max_escape_24h, max_escape_2h, 
             decline_strength_level, rise_strength_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (stat_time, stats['escape_24h_count'], stats['escape_2h_count'], 
              stats['max_escape_24h'], stats['max_escape_2h'],
              market_strength['decline_level'], market_strength['rise_level']))
        
        conn.commit()
        conn.close()
        
        log(f"✅ 保存统计数据: 24H快照数={stats['escape_24h_count']}, "
            f"2H快照数={stats['escape_2h_count']}, "
            f"24H最大值={stats['max_escape_24h']}, "
            f"2H最大值={stats['max_escape_2h']}, "
            f"下跌强度={market_strength['decline_level']}, "
            f"上涨强度={market_strength['rise_level']}")
        return True
        
    except Exception as e:
        log(f"❌ 保存统计数据失败: {e}")
        return False

def main():
    """主函数"""
    log("=" * 80)
    log("🚀 逃顶快照统计数据记录器启动")
    log(f"📊 数据源: {SUPPORT_RESISTANCE_DB}")
    log(f"💾 目标数据库: {CRYPTO_DATA_DB}")
    log(f"⏰ 记录间隔: {CHECK_INTERVAL}秒 (1分钟)")
    log("=" * 80)
    
    while True:
        try:
            log("")
            log("📊 开始记录逃顶快照统计数据...")
            
            # 计算统计数据
            stats = calculate_stats()
            
            # 获取市场强度等级
            market_strength = get_market_strength()
            
            if stats:
                # 保存到数据库（包含市场强度）
                save_stats(stats, market_strength)
            else:
                log("⚠️  未能获取统计数据")
            
            log(f"⏰ 等待{CHECK_INTERVAL}秒后进行下次记录...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("\n👋 收到停止信号，正在退出...")
            sys.exit(0)
        except Exception as e:
            log(f"❌ 发生错误: {e}")
            log(f"⏰ 等待{CHECK_INTERVAL}秒后重试...")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
