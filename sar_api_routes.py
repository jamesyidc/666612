"""
SAR斜率系统 - Flask API路由
基于JSONL存储
"""
from flask import jsonify, request
from sar_slope_jsonl_system import SARSlopeJSONLSystem, MONITORED_SYMBOLS
from datetime import datetime, timedelta
import pytz
from calculate_sequences import calculate_sequences

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 创建全局实例
sar_system = SARSlopeJSONLSystem()

def register_sar_routes(app):
    """注册SAR相关的API路由"""
    
    @app.route('/api/sar-slope/latest')
    def api_sar_slope_latest():
        """获取所有币种的最新SAR数据"""
        try:
            symbol_filter = request.args.get('symbol', '').upper()
            position_filter = request.args.get('position', '')  # bullish/bearish
            
            # 获取所有最新数据
            all_data = sar_system.get_all_latest()
            
            # 过滤
            results = []
            for item in all_data:
                # 符号过滤
                if symbol_filter and symbol_filter not in item.get('symbol', ''):
                    continue
                
                # 位置过滤
                if position_filter and item.get('sar_position') != position_filter:
                    continue
                
                results.append({
                    'symbol': item['symbol'].replace('-USDT-SWAP', ''),
                    'datetime': item.get('datetime_beijing'),
                    'sar_value': item.get('sar_value'),
                    'sar_position': item.get('sar_position'),
                    'price': item.get('price_close'),
                    'timestamp': item.get('timestamp')
                })
            
            # 排序
            results.sort(key=lambda x: x['symbol'])
            
            # 统计
            stats = sar_system.get_stats()
            
            return jsonify({
                'success': True,
                'data': results,
                'stats': stats,
                'timestamp': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            import traceback
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500
    
    @app.route('/api/sar-slope/history/<symbol>')
    def api_sar_slope_history(symbol):
        """获取指定币种的历史数据"""
        try:
            # 获取时间范围参数
            hours = request.args.get('hours', 24, type=int)
            limit = request.args.get('limit', 100, type=int)
            
            symbol_full = f"{symbol.upper()}-USDT-SWAP"
            
            # 读取最近的数据
            data_points = sar_system.read_latest(symbol_full, limit=limit)
            
            # 如果指定了小时数，进行过滤
            if hours > 0:
                cutoff_time = datetime.now(BEIJING_TZ) - timedelta(hours=hours)
                cutoff_timestamp = int(cutoff_time.timestamp() * 1000)
                data_points = [d for d in data_points if d.get('timestamp', 0) >= cutoff_timestamp]
            
            # 格式化输出
            results = []
            for item in data_points:
                results.append({
                    'symbol': item['symbol'].replace('-USDT-SWAP', ''),
                    'datetime': item.get('datetime_beijing'),
                    'sar_value': item.get('sar_value'),
                    'sar_position': item.get('sar_position'),
                    'price': item.get('price_close'),
                    'price_high': item.get('price_high'),
                    'price_low': item.get('price_low'),
                    'volume': item.get('volume'),
                    'timestamp': item.get('timestamp')
                })
            
            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'data': results,
                'count': len(results),
                'timestamp': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            import traceback
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500
    
    @app.route('/api/sar-slope/collector-status')
    def api_sar_slope_collector_status():
        """获取采集器状态"""
        try:
            stats = sar_system.get_stats()
            
            # 检查数据新鲜度
            latest_data = sar_system.get_all_latest()
            if latest_data:
                # 获取最新的时间戳
                latest_timestamps = [d.get('timestamp', 0) for d in latest_data]
                latest_timestamp = max(latest_timestamps) if latest_timestamps else 0
                
                if latest_timestamp:
                    latest_dt = datetime.fromtimestamp(latest_timestamp / 1000, tz=BEIJING_TZ)
                    time_diff = datetime.now(BEIJING_TZ) - latest_dt
                    is_fresh = time_diff.total_seconds() < 600  # 10分钟内为新鲜
                else:
                    is_fresh = False
            else:
                is_fresh = False
            
            return jsonify({
                'success': True,
                'status': 'running' if is_fresh else 'stale',
                'is_fresh': is_fresh,
                'total_symbols': stats['total_symbols'],
                'bullish_count': stats['bullish_count'],
                'bearish_count': stats['bearish_count'],
                'last_update': stats['last_update'],
                'data_dir': str(sar_system.data_dir),
                'storage_type': 'JSONL'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/sar-slope/symbol/<symbol>')
    def api_sar_slope_symbol(symbol):
        """获取单个币种的最新数据"""
        try:
            symbol_full = f"{symbol.upper()}-USDT-SWAP"
            
            # 读取更多历史数据用于序列计算
            data_points = sar_system.read_latest(symbol_full, limit=500)
            
            if not data_points:
                return jsonify({
                    'success': False,
                    'error': f'No data found for {symbol}'
                }), 404
            
            item = data_points[0]
            
            # 计算序列
            sequences = calculate_sequences(data_points[::-1])  # 反转为时间正序
            sequences = sequences[::-1]  # 再反转，最新序列在前
            
            return jsonify({
                'success': True,
                'sequences': sequences,
                'total_sequences': len(sequences),
                'bias_statistics': {'slope_30m': 0, 'slope_1h': 0, 'slope_4h': 0},
                'current_status': {
                    'position': 'long' if item.get('sar_position') == 'bullish' else 'short',
                    'position_cn': '多头' if item.get('sar_position') == 'bullish' else '空头',
                    'cycle_info': item.get('datetime_beijing', ''),
                    'oscillation_cn': item.get('sar_position', ''),
                    'current_sequence': 1,
                    'cycle_start': item.get('datetime_beijing', ''),
                    'cycle_end': item.get('datetime_beijing', ''),
                    'duration': '0小时',
                    'last_update': item.get('datetime_beijing', '')
                },
                'data': {
                    'symbol': item['symbol'].replace('-USDT-SWAP', ''),
                    'datetime': item.get('datetime_beijing'),
                    'sar_value': item.get('sar_value'),
                    'sar_position': item.get('sar_position'),
                    'price': item.get('price_close'),
                    'price_high': item.get('price_high'),
                    'price_low': item.get('price_low'),
                    'volume': item.get('volume'),
                    'timestamp': item.get('timestamp')
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/sar-slope/collect-now')
    def api_sar_slope_collect_now():
        """立即执行一次数据采集"""
        try:
            success_count = sar_system.collect_all_symbols()
            stats = sar_system.get_stats()
            
            return jsonify({
                'success': True,
                'message': f'Successfully collected {success_count} symbols',
                'success_count': success_count,
                'total_symbols': len(MONITORED_SYMBOLS),
                'stats': stats
            })
            
        except Exception as e:
            import traceback
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500


    @app.route('/api/sar-slope/current-cycle/<symbol>')
    def api_sar_slope_current_cycle(symbol):
        """获取当前周期数据（兼容旧API）"""
        return api_sar_slope_symbol(symbol)
