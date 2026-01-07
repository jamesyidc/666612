"""
Panic Data API Routes using JSONL Storage
恐慌清洗指数 API 路由 (基于 JSONL 存储)
"""

from flask import jsonify
from datetime import datetime, timedelta
import pytz
from panic_jsonl_storage import panic_storage

BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def register_panic_routes(app):
    """注册恐慌数据相关的API路由"""
    
    @app.route('/api/panic/latest')
    def api_panic_latest_jsonl():
        """恐慌清洗指数最新数据API (JSONL版本)"""
        try:
            # 从JSONL读取最新数据
            latest = panic_storage.read_latest(limit=1)
            
            if not latest:
                return jsonify({'success': False, 'error': '暂无数据'})
            
            record = latest[0]
            
            # 提取数据
            rush_up = record.get('rush_up', 0)
            rush_down = record.get('rush_down', 0)
            diff = record.get('diff', 0)
            count = record.get('count', 0)
            status = record.get('status', '未知')
            count_score_display = record.get('count_score_display', '-')
            count_score_type = record.get('count_score_type', '-')
            snapshot_time = record.get('snapshot_time', '')
            
            # 计算恐慌指数 (基于急跌急涨比)
            # 恐慌指数 = (急跌数量 / (急涨数量 + 急跌数量)) * 100
            total = rush_up + rush_down
            if total > 0:
                panic_index_percentage = round((rush_down / total) * 100, 2)
            else:
                panic_index_percentage = 0
            
            # 根据恐慌指数确定等级
            if panic_index_percentage < 40:
                panic_level = '低恐慌'
                level_color = 'green'
            elif panic_index_percentage < 60:
                panic_level = '中度恐慌'
                level_color = 'yellow'
            else:
                panic_level = '高度恐慌'
                level_color = 'red'
            
            return jsonify({
                'success': True,
                'data': {
                    'snapshot_time': snapshot_time,
                    'rush_up': rush_up,
                    'rush_down': rush_down,
                    'diff': diff,
                    'count': count,
                    'status': status,
                    'count_score_display': count_score_display,
                    'count_score_type': count_score_type,
                    'panic_index': panic_index_percentage,
                    'panic_level': panic_level,
                    'level_color': level_color,
                    'market_info': f'{rush_up}↑/{rush_down}↓ (差值:{diff})'
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/panic/history')
    def api_panic_history_jsonl():
        """恐慌清洗指数历史数据API (JSONL版本)"""
        try:
            from flask import request
            
            # 获取查询参数
            days = request.args.get('days', default=7, type=int)
            limit = request.args.get('limit', default=500, type=int)
            
            # 计算日期范围
            end_date = datetime.now(BEIJING_TZ)
            start_date = end_date - timedelta(days=days)
            
            # 读取数据
            records = panic_storage.read_by_date_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                limit=limit
            )
            
            # 格式化数据
            history = []
            for record in records:
                rush_up = record.get('rush_up', 0)
                rush_down = record.get('rush_down', 0)
                total = rush_up + rush_down
                
                # 计算恐慌指数
                if total > 0:
                    panic_index = round((rush_down / total) * 100, 2)
                else:
                    panic_index = 0
                
                history.append({
                    'snapshot_time': record.get('snapshot_time'),
                    'snapshot_date': record.get('snapshot_date'),
                    'rush_up': rush_up,
                    'rush_down': rush_down,
                    'diff': record.get('diff', 0),
                    'count': record.get('count', 0),
                    'status': record.get('status', ''),
                    'count_score_display': record.get('count_score_display', ''),
                    'panic_index': panic_index
                })
            
            return jsonify({
                'success': True,
                'count': len(history),
                'days': days,
                'data': history
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/panic/stats')
    def api_panic_stats_jsonl():
        """恐慌数据统计API (JSONL版本)"""
        try:
            # 获取存储统计
            stats = panic_storage.get_stats()
            
            # 获取今日数据
            today_records = panic_storage.read_today()
            
            # 获取最新数据
            latest = panic_storage.read_latest(limit=1)
            
            last_update = '-'
            current_status = '-'
            
            if latest:
                record = latest[0]
                snapshot_time = record.get('snapshot_time', '')
                if ' ' in snapshot_time:
                    last_update = snapshot_time.split(' ')[1][:5]  # HH:MM
                current_status = record.get('status', '-')
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_records': stats.get('total_records', 0),
                    'total_files': stats.get('total_files', 0),
                    'total_size_mb': stats.get('total_size_mb', 0),
                    'today_records': len(today_records),
                    'date_range': stats.get('date_range', {}),
                    'last_update': last_update,
                    'current_status': current_status
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
