#!/usr/bin/env python3
"""
SAR斜率系统完整版 - 思路2实现
功能：
1. 判断SAR多空趋势及持续时间（从转换5分钟K线开始记录）
2. 记录每天、3天、7天、15天的平均SAR变化率
3. 计算连续SAR点之间的百分比变化
4. 异常预警机制（偏离平均值30%以上触发告警）
5. 标记极值点
6. 为27个币种建立独立SAR斜率系统
7. 存储至少7天的5分钟SAR数据（≥576根K线）
"""

import sqlite3
import requests
import time
import json
from datetime import datetime, timedelta
import pytz
import os

# ==================== 配置 ====================
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DB_PATH = '/home/user/webapp/sar_slope_data.db'

# 27个币种列表
SYMBOLS = [
    'BTC', 'ETH', 'XRP', 'BNB', 'SOL', 'LTC', 'DOGE', 'SUI', 'TRX', 'TON',
    'ETC', 'BCH', 'HBAR', 'XLM', 'FIL', 'LINK', 'CRO', 'DOT', 'AAVE', 'UNI',
    'NEAR', 'APT', 'CFX', 'CRV', 'STX', 'LDO', 'TAO'
]

# SAR参数
SAR_AF_START = 0.02  # 初始加速因子
SAR_AF_INCREMENT = 0.02  # 加速因子增量
SAR_AF_MAX = 0.2  # 最大加速因子

# 数据保留期限
DATA_RETENTION_DAYS = 16
MIN_KLINES = 4608  # 最少保留K线数量 (16天 * 24小时 * 12个5分钟 = 4608)

# 异常阈值
ANOMALY_THRESHOLD = 30.0  # 偏离平均值30%以上为异常

# ==================== 数据库初始化 ====================
def init_database():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. SAR原始数据表（存储每个5分钟K线的SAR值）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sar_raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            kline_time TEXT NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            sar_value REAL NOT NULL,
            position TEXT NOT NULL,
            position_sequence INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
    ''')
    
    # 2. SAR转换点表（记录多空转换的关键点）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sar_conversion_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            kline_time TEXT NOT NULL,
            from_position TEXT NOT NULL,
            to_position TEXT NOT NULL,
            conversion_sar REAL NOT NULL,
            conversion_price REAL NOT NULL,
            previous_duration INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. SAR连续变化表（记录连续SAR点之间的变化）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sar_consecutive_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            position TEXT NOT NULL,
            sequence_num INTEGER NOT NULL,
            prev_sar REAL NOT NULL,
            current_sar REAL NOT NULL,
            change_value REAL NOT NULL,
            change_percent REAL NOT NULL,
            kline_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. SAR平均值表（存储不同周期的平均变化率）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sar_period_averages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            position TEXT NOT NULL,
            period_type TEXT NOT NULL,
            avg_change_percent REAL NOT NULL,
            sample_count INTEGER NOT NULL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, position, period_type)
        )
    ''')
    
    # 5. SAR异常告警表（偏离平均值30%以上）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sar_anomaly_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            position TEXT NOT NULL,
            sequence_num INTEGER NOT NULL,
            sar_value REAL NOT NULL,
            change_percent REAL NOT NULL,
            period_avg REAL NOT NULL,
            deviation_percent REAL NOT NULL,
            alert_level TEXT NOT NULL,
            is_extreme_point INTEGER DEFAULT 0,
            extreme_type TEXT,
            kline_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 6. 系统状态表（记录最后更新时间等）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            last_update_time INTEGER,
            last_kline_time TEXT,
            total_klines INTEGER DEFAULT 0,
            current_position TEXT,
            current_sequence INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sar_raw_symbol_time ON sar_raw_data(symbol, timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sar_conversion_symbol ON sar_conversion_points(symbol, timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sar_changes_symbol ON sar_consecutive_changes(symbol, position, sequence_num)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sar_alerts_symbol ON sar_anomaly_alerts(symbol, created_at DESC)')
    
    conn.commit()
    conn.close()
    
    return True

# ==================== 数据获取 ====================
def fetch_kline_data(symbol, limit=5000):
    """
    从OKX获取5分钟K线数据
    由于OKX API单次最多返回300根K线，需要分批获取
    limit=5000 表示目标获取5000根5分钟K线 = 17.36天的数据（超过16天要求）
    """
    url = "https://www.okx.com/api/v5/market/candles"
    all_klines = []
    after = None  # 用于分页
    
    # 由于OKX限制，每次最多300根，需要循环获取
    max_iterations = (limit // 300) + 1
    
    try:
        for i in range(max_iterations):
            params = {
                'instId': f'{symbol}-USDT-SWAP',
                'bar': '5m',
                'limit': 300
            }
            
            if after:
                params['after'] = after
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '0' and data.get('data'):
                    klines = data['data']
                    
                    if not klines:
                        break
                    
                    all_klines.extend(klines)
                    
                    # 检查是否已达到目标数量
                    if len(all_klines) >= limit:
                        break
                    
                    # 设置下一次请求的after参数（最旧的K线时间戳）
                    after = klines[-1][0]
                    
                    # 短暂延迟避免API限流
                    time.sleep(0.2)
                else:
                    break
            else:
                break
        
        # 反转顺序（从旧到新）
        if all_klines:
            all_klines.reverse()
        
        return all_klines[:limit] if len(all_klines) > limit else all_klines
        
    except Exception as e:
        print(f"    ✗ 获取{symbol} K线数据失败: {e}")
        return None

# ==================== SAR计算 ====================
def calculate_sar_with_position(klines):
    """
    计算SAR指标并判断多空状态
    
    多空判定规则（根据用户要求）：
    - SAR > K线开盘价 = 空头
    - SAR < K线开盘价 = 多头
    
    返回: [
        {
            'timestamp': int,
            'kline_time': str,
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'sar': float,
            'position': 'long'/'short',
            'is_conversion': bool
        },
        ...
    ]
    """
    if not klines or len(klines) < 2:
        return []
    
    results = []
    
    # 初始化SAR
    first_kline = klines[0]
    first_timestamp = int(first_kline[0])
    first_open = float(first_kline[1])
    first_high = float(first_kline[2])
    first_low = float(first_kline[3])
    first_close = float(first_kline[4])
    
    # 初始SAR值取第一根K线的最低价
    sar = first_low
    ep = first_high  # 极值点 (Extreme Point)
    af = SAR_AF_START  # 加速因子
    is_uptrend = True  # 初始假设为上升趋势
    
    # 根据第一根K线判断初始position
    first_position = 'long' if sar < first_open else 'short'
    
    for i, kline in enumerate(klines):
        timestamp = int(kline[0])
        open_price = float(kline[1])
        high = float(kline[2])
        low = float(kline[3])
        close = float(kline[4])
        
        # 判断当前position（根据SAR与开盘价关系）
        current_position = 'long' if sar < open_price else 'short'
        
        # 判断是否为转换点
        is_conversion = False
        if i > 0:
            prev_position = results[-1]['position']
            if current_position != prev_position:
                is_conversion = True
        
        # 记录当前K线数据
        kline_time = datetime.fromtimestamp(timestamp/1000, BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        results.append({
            'timestamp': timestamp,
            'kline_time': kline_time,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'sar': sar,
            'position': current_position,
            'is_conversion': is_conversion
        })
        
        # 计算下一个SAR值
        if i < len(klines) - 1:
            # 更新SAR
            sar = sar + af * (ep - sar)
            
            # 确保SAR不会进入前两根K线的范围
            if is_uptrend:
                sar = min(sar, low, float(klines[max(0, i-1)][3]))
            else:
                sar = max(sar, high, float(klines[max(0, i-1)][2]))
            
            # 检查是否需要转势
            next_kline = klines[i + 1]
            next_high = float(next_kline[2])
            next_low = float(next_kline[3])
            
            if is_uptrend:
                # 上升趋势中
                if next_low <= sar:
                    # 转为下降趋势
                    is_uptrend = False
                    sar = ep
                    ep = next_low
                    af = SAR_AF_START
                else:
                    # 继续上升趋势
                    if next_high > ep:
                        ep = next_high
                        af = min(af + SAR_AF_INCREMENT, SAR_AF_MAX)
            else:
                # 下降趋势中
                if next_high >= sar:
                    # 转为上升趋势
                    is_uptrend = True
                    sar = ep
                    ep = next_high
                    af = SAR_AF_START
                else:
                    # 继续下降趋势
                    if next_low < ep:
                        ep = next_low
                        af = min(af + SAR_AF_INCREMENT, SAR_AF_MAX)
    
    return results

# ==================== 序列号分配 ====================
def assign_position_sequences(sar_data):
    """
    为SAR数据分配position_sequence和duration
    
    例如：
    - 多01, 多02, 多03, ... (多头持续期间)
    - 空01, 空02, 空03, ... (空头持续期间)
    - 当转换时重新从01开始
    """
    if not sar_data:
        return []
    
    results = []
    current_position = sar_data[0]['position']
    sequence = 1
    conversion_start_idx = 0
    
    for i, item in enumerate(sar_data):
        # 检查是否转换
        if item['position'] != current_position:
            current_position = item['position']
            sequence = 1
            conversion_start_idx = i
        
        # 计算持续时间（分钟）
        duration_minutes = (i - conversion_start_idx) * 5
        
        # 添加序列号和持续时间
        item['position_sequence'] = sequence
        item['duration_minutes'] = duration_minutes
        
        results.append(item)
        sequence += 1
    
    return results

# ==================== 数据存储 ====================
def save_sar_data(symbol, sar_data):
    """保存SAR原始数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
    conversion_count = 0
    
    for item in sar_data:
        try:
            # 保存原始SAR数据
            cursor.execute('''
                INSERT OR REPLACE INTO sar_raw_data
                (symbol, timestamp, kline_time, open_price, high_price, low_price,
                 close_price, sar_value, position, position_sequence, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, item['timestamp'], item['kline_time'],
                item['open'], item['high'], item['low'], item['close'],
                item['sar'], item['position'], item['position_sequence'],
                item['duration_minutes']
            ))
            saved_count += 1
            
            # 如果是转换点，保存到转换点表
            if item['is_conversion'] and item['position_sequence'] == 1:
                # 获取前一个position的持续时间
                cursor.execute('''
                    SELECT position, MAX(duration_minutes)
                    FROM sar_raw_data
                    WHERE symbol = ? AND timestamp < ?
                    GROUP BY position
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (symbol, item['timestamp']))
                
                prev_row = cursor.fetchone()
                prev_position = prev_row[0] if prev_row else 'unknown'
                prev_duration = prev_row[1] if prev_row else 0
                
                cursor.execute('''
                    INSERT INTO sar_conversion_points
                    (symbol, timestamp, kline_time, from_position, to_position,
                     conversion_sar, conversion_price, previous_duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, item['timestamp'], item['kline_time'],
                    prev_position, item['position'],
                    item['sar'], item['open'], prev_duration
                ))
                conversion_count += 1
        
        except Exception as e:
            print(f"      ✗ 保存数据失败: {e}")
    
    # 更新系统状态
    if sar_data:
        last_item = sar_data[-1]
        cursor.execute('''
            INSERT OR REPLACE INTO system_status
            (symbol, last_update_time, last_kline_time, total_klines,
             current_position, current_sequence, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (
            symbol, last_item['timestamp'], last_item['kline_time'],
            len(sar_data), last_item['position'], last_item['position_sequence']
        ))
    
    conn.commit()
    conn.close()
    
    return saved_count, conversion_count

# ==================== 变化率计算 ====================
def calculate_consecutive_changes(symbol):
    """
    计算连续SAR点之间的变化率
    
    按照用户提供的例子：
    Sar空01=0.3797, Sar空02=0.3797, 变化率=0%
    Sar空02=0.3797, Sar空03=0.3796, 变化率=0.02633%
    
    同时记录持续时间(duration_minutes)用于后续按时间段分组统计
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空之前的变化记录
    cursor.execute('DELETE FROM sar_consecutive_changes WHERE symbol = ?', (symbol,))
    
    # 按position分组处理
    for position in ['long', 'short']:
        # 获取该position的所有SAR数据（按时间升序），包含duration_minutes
        cursor.execute('''
            SELECT timestamp, sar_value, position_sequence, kline_time, duration_minutes
            FROM sar_raw_data
            WHERE symbol = ? AND position = ?
            ORDER BY timestamp ASC
        ''', (symbol, position))
        
        rows = cursor.fetchall()
        
        if len(rows) < 2:
            continue
        
        # 计算连续变化
        for i in range(len(rows) - 1):
            prev_sar = rows[i][1]
            current_sar = rows[i+1][1]
            sequence_num = rows[i+1][2]
            kline_time = rows[i+1][3]
            duration = rows[i+1][4]  # 获取持续时间
            
            # 计算变化值和变化率
            change_value = current_sar - prev_sar
            change_percent = abs(change_value / prev_sar * 100) if prev_sar != 0 else 0
            
            # 保存变化记录，包含duration_minutes
            cursor.execute('''
                INSERT INTO sar_consecutive_changes
                (symbol, position, sequence_num, prev_sar, current_sar,
                 change_value, change_percent, kline_time, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, position, sequence_num, prev_sar, current_sar,
                change_value, change_percent, kline_time, duration
            ))
    
    conn.commit()
    conn.close()

# ==================== 平均值计算 ====================
def calculate_period_averages(symbol):
    """
    计算不同周期的平均变化率
    - 1天 (当天): 最近 288 条记录 (24小时 * 12个5分钟)
    - 3天: 最近 864 条记录 (3 * 24 * 12)
    - 7天: 最近 2016 条记录 (7 * 24 * 12)
    - 15天: 最近 4320 条记录 (15 * 24 * 12)
    
    同时计算按序列号分组的平均值（用户需求）：
    - 空头01->空头02 的全天平均值
    - 空头02->空头03 的全天平均值
    - 多头01->多头02 的全天平均值
    等等
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空之前的平均值记录
    cursor.execute('DELETE FROM sar_period_averages WHERE symbol = ?', (symbol,))
    
    for position in ['long', 'short']:
        # 1. 计算整体周期平均值
        cursor.execute('''
            SELECT change_percent
            FROM sar_consecutive_changes
            WHERE symbol = ? AND position = ?
            ORDER BY id ASC
        ''', (symbol, position))
        
        changes = [row[0] for row in cursor.fetchall()]
        
        if not changes:
            continue
        
        # 计算各周期平均值
        periods = {
            '1day': 288,
            '3day': 864,
            '7day': 2016,
            '15day': 4320
        }
        
        for period_type, period_count in periods.items():
            if len(changes) >= period_count:
                recent_changes = changes[-period_count:]
            else:
                recent_changes = changes
            
            if recent_changes:
                avg_change = sum(recent_changes) / len(recent_changes)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sar_period_averages
                    (symbol, position, period_type, avg_change_percent, sample_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol, position, period_type, avg_change, len(recent_changes)))
        
        # 2. 计算按序列号分组的平均值（新增）
        # 获取每个序列号的所有变化率
        cursor.execute('''
            SELECT sequence_num, change_percent
            FROM sar_consecutive_changes
            WHERE symbol = ? AND position = ?
            ORDER BY id ASC
        ''', (symbol, position))
        
        sequence_data = {}
        for row in cursor.fetchall():
            seq_num = row[0]
            change_pct = row[1]
            
            if seq_num not in sequence_data:
                sequence_data[seq_num] = []
            sequence_data[seq_num].append(change_pct)
        
        # 保存每个序列号的平均值
        for seq_num, changes_list in sequence_data.items():
            if changes_list:
                avg_change = sum(changes_list) / len(changes_list)
                
                # 使用特殊的period_type格式: seq_01, seq_02, seq_03 等
                period_type = f'seq_{seq_num:02d}'
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sar_period_averages
                    (symbol, position, period_type, avg_change_percent, sample_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol, position, period_type, avg_change, len(changes_list)))
        
        # 3. 计算按持续时间(duration)分组的平均值（新增 - 用户最新需求）
        # 对每个持续时间段，计算1天、3天、7天、15天的平均变化率
        cursor.execute('''
            SELECT DISTINCT duration_minutes
            FROM sar_consecutive_changes
            WHERE symbol = ? AND position = ? AND duration_minutes IS NOT NULL
            ORDER BY duration_minutes
        ''', (symbol, position))
        
        durations = [row[0] for row in cursor.fetchall()]
        
        for duration in durations:
            # 获取该duration的所有变化率（按时间升序）
            cursor.execute('''
                SELECT change_percent, id
                FROM sar_consecutive_changes
                WHERE symbol = ? AND position = ? AND duration_minutes = ?
                ORDER BY id ASC
            ''', (symbol, position, duration))
            
            duration_changes = [row[0] for row in cursor.fetchall()]
            
            if not duration_changes:
                continue
            
            # 计算该duration的各周期平均值
            duration_periods = {
                '1day': 288,
                '3day': 864,
                '7day': 2016,
                '15day': 4320
            }
            
            for period_type, period_count in duration_periods.items():
                if len(duration_changes) >= period_count:
                    recent_changes = duration_changes[-period_count:]
                else:
                    recent_changes = duration_changes
                
                if recent_changes:
                    avg_change = sum(recent_changes) / len(recent_changes)
                    
                    # 使用格式: dur_<时长>_<周期>, 例如 dur_15_1day, dur_30_3day
                    period_type_name = f'dur_{duration}_{period_type}'
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO sar_period_averages
                        (symbol, position, period_type, avg_change_percent, sample_count)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (symbol, position, period_type_name, avg_change, len(recent_changes)))
    
    conn.commit()
    conn.close()

# ==================== 异常检测 ====================
def detect_anomalies(symbol):
    """
    检测异常并标记极值点
    - 偏离3天平均值30%以上触发告警
    - 标记极值点（最高/最低变化率）
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空之前的告警记录
    cursor.execute('DELETE FROM sar_anomaly_alerts WHERE symbol = ?', (symbol,))
    
    for position in ['long', 'short']:
        # 获取3天平均值
        cursor.execute('''
            SELECT avg_change_percent
            FROM sar_period_averages
            WHERE symbol = ? AND position = ? AND period_type = '3day'
        ''', (symbol, position))
        
        avg_row = cursor.fetchone()
        if not avg_row:
            continue
        
        period_avg = avg_row[0]
        
        # 获取最近的变化率数据
        cursor.execute('''
            SELECT sequence_num, current_sar, change_percent, kline_time
            FROM sar_consecutive_changes
            WHERE symbol = ? AND position = ?
            ORDER BY id DESC
            LIMIT 100
        ''', (symbol, position))
        
        recent_changes = cursor.fetchall()
        
        if not recent_changes:
            continue
        
        # 找出最高和最低变化率
        max_change = max(recent_changes, key=lambda x: x[2])
        min_change = min(recent_changes, key=lambda x: x[2])
        
        for change in recent_changes:
            sequence_num, sar_value, change_percent, kline_time = change
            
            # 计算偏离度
            if period_avg != 0:
                deviation = abs(change_percent - period_avg) / period_avg * 100
            else:
                deviation = 0
            
            # 判断是否异常（偏离30%以上）
            if deviation >= ANOMALY_THRESHOLD:
                # 判断告警级别
                if deviation >= 50:
                    alert_level = 'critical'
                elif deviation >= 40:
                    alert_level = 'high'
                else:
                    alert_level = 'warning'
                
                # 判断是否为极值点
                is_extreme = 0
                extreme_type = None
                
                if change == max_change:
                    is_extreme = 1
                    extreme_type = 'max'
                elif change == min_change:
                    is_extreme = 1
                    extreme_type = 'min'
                
                # 保存告警记录
                cursor.execute('''
                    INSERT INTO sar_anomaly_alerts
                    (symbol, position, sequence_num, sar_value, change_percent,
                     period_avg, deviation_percent, alert_level, is_extreme_point,
                     extreme_type, kline_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, position, sequence_num, sar_value, change_percent,
                    period_avg, deviation, alert_level, is_extreme, extreme_type, kline_time
                ))
    
    conn.commit()
    conn.close()

# ==================== 数据清理 ====================
def cleanup_old_data():
    """清理超过7天的旧数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cutoff_time = int((datetime.now(BEIJING_TZ) - timedelta(days=DATA_RETENTION_DAYS)).timestamp() * 1000)
    
    # 清理各表的旧数据
    total_deleted = 0
    
    # sar_raw_data 和 sar_conversion_points 有 timestamp 字段
    for table in ['sar_raw_data', 'sar_conversion_points']:
        cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_time,))
        deleted = cursor.rowcount
        total_deleted += deleted
    
    # sar_consecutive_changes 表没有 timestamp 字段，使用 created_at
    cursor.execute('DELETE FROM sar_consecutive_changes WHERE created_at < datetime(?, "unixepoch")', 
                   (cutoff_time / 1000,))
    total_deleted += cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return total_deleted

# ==================== 主采集函数 ====================
def collect_symbol_data(symbol):
    """采集单个币种的SAR数据"""
    print(f"  正在处理 {symbol}...")
    
    # 1. 获取K线数据
    klines = fetch_kline_data(symbol, limit=5000)
    if not klines:
        print(f"    ✗ 获取K线数据失败")
        return False
    
    print(f"    ✓ 获取了 {len(klines)} 根K线")
    
    # 2. 计算SAR
    sar_data = calculate_sar_with_position(klines)
    if not sar_data:
        print(f"    ✗ SAR计算失败")
        return False
    
    print(f"    ✓ 计算了 {len(sar_data)} 个SAR点")
    
    # 3. 分配序列号
    sar_data_with_seq = assign_position_sequences(sar_data)
    
    # 4. 保存原始数据
    saved, conversions = save_sar_data(symbol, sar_data_with_seq)
    print(f"    ✓ 保存了 {saved} 条数据, {conversions} 个转换点")
    
    # 5. 计算变化率
    calculate_consecutive_changes(symbol)
    print(f"    ✓ 计算了连续变化率")
    
    # 6. 计算平均值
    calculate_period_averages(symbol)
    print(f"    ✓ 计算了周期平均值")
    
    # 7. 检测异常
    detect_anomalies(symbol)
    print(f"    ✓ 完成异常检测")
    
    return True

def collect_all_symbols():
    """采集所有币种的数据"""
    print("\n" + "="*80)
    print("SAR斜率系统完整版 - 数据采集")
    print("思路2实现：判断多空趋势 + 持续时间 + 平均值 + 异常预警")
    print("="*80)
    print(f"\n初始化数据库...")
    
    # 初始化数据库
    init_database()
    print(f"✓ 数据库初始化完成\n")
    
    print(f"开始采集 {len(SYMBOLS)} 个币种的数据...")
    print(f"数据周期: 5分钟K线")
    print(f"数据量: 至少 {MIN_KLINES} 根K线 (约7天)")
    print("="*80 + "\n")
    
    success_count = 0
    fail_count = 0
    
    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"[{i}/{len(SYMBOLS)}] {symbol}")
        
        try:
            if collect_symbol_data(symbol):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"    ✗ 处理失败: {e}")
            fail_count += 1
        
        # 避免请求过快
        if i < len(SYMBOLS):
            time.sleep(0.5)
        
        print()
    
    # 清理旧数据
    print("="*80)
    print("清理旧数据...")
    deleted = cleanup_old_data()
    print(f"✓ 清理了 {deleted} 条超过7天的旧数据\n")
    
    # 输出统计信息
    print("="*80)
    print("采集完成！")
    print("="*80)
    print(f"✓ 成功: {success_count} 个币种")
    print(f"✗ 失败: {fail_count} 个币种")
    print(f"📊 总计: {len(SYMBOLS)} 个币种")
    print(f"💾 数据库: {DB_PATH}")
    print("="*80 + "\n")

# ==================== 数据查询函数 ====================
def get_symbol_status(symbol=None):
    """获取币种状态信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if symbol:
        cursor.execute('''
            SELECT symbol, last_kline_time, total_klines,
                   current_position, current_sequence, updated_at
            FROM system_status
            WHERE symbol = ?
        ''', (symbol,))
    else:
        cursor.execute('''
            SELECT symbol, last_kline_time, total_klines,
                   current_position, current_sequence, updated_at
            FROM system_status
            ORDER BY symbol
        ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_recent_alerts(symbol=None, limit=10):
    """获取最近的异常告警"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if symbol:
        cursor.execute('''
            SELECT symbol, position, sequence_num, sar_value,
                   change_percent, deviation_percent, alert_level,
                   is_extreme_point, extreme_type, kline_time
            FROM sar_anomaly_alerts
            WHERE symbol = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (symbol, limit))
    else:
        cursor.execute('''
            SELECT symbol, position, sequence_num, sar_value,
                   change_percent, deviation_percent, alert_level,
                   is_extreme_point, extreme_type, kline_time
            FROM sar_anomaly_alerts
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_conversion_points(symbol, limit=10):
    """获取最近的转换点"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, kline_time, from_position, to_position,
               conversion_sar, conversion_price, previous_duration
        FROM sar_conversion_points
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (symbol, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

# ==================== 主程序 ====================
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'status':
            # 查看系统状态
            status = get_symbol_status()
            print("\n系统状态:")
            print("="*100)
            for s in status:
                print(f"{s[0]:<8} | 最新时间: {s[1]} | K线数: {s[2]:<5} | 当前状态: {s[3]:<6} | 序列: {s[4]}")
            print("="*100)
        
        elif command == 'alerts':
            # 查看最近告警
            alerts = get_recent_alerts(limit=20)
            print("\n最近告警:")
            print("="*120)
            for a in alerts:
                extreme = " ⭐极值" if a[7] else ""
                print(f"{a[0]:<8} | {a[1]:<6} | 序列{a[2]:<4} | SAR:{a[3]:.6f} | 变化:{a[4]:.4f}% | 偏离:{a[5]:.2f}% | {a[6]}{extreme}")
            print("="*120)
        
        else:
            print(f"未知命令: {command}")
            print("可用命令: status, alerts")
    
    else:
        # 默认执行采集
        collect_all_symbols()
