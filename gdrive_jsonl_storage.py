#!/usr/bin/env python3
"""Google Drive监控 - JSONL存储模块"""
import json
import os
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DATA_DIR = '/home/user/webapp/data/gdrive_snapshots'

class GDriveJSONLStorage:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def save_snapshot(self, data):
        """保存快照到JSONL"""
        date_str = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        file_path = os.path.join(DATA_DIR, f"{date_str}.jsonl")
        
        record = {
            'snapshot_time': data.get('snapshot_time'),
            'snapshot_date': data.get('snapshot_date'),
            'rush_up': data.get('rush_up'),
            'rush_down': data.get('rush_down'),
            'diff': data.get('diff'),
            'count': data.get('count'),
            'status': data.get('status'),
            'count_score_display': data.get('count_score_display'),
            'count_score_type': data.get('count_score_type'),
            'created_at': datetime.now(BEIJING_TZ).isoformat()
        }
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        return True
    
    def get_latest(self, limit=10):
        """获取最新记录"""
        date_str = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        file_path = os.path.join(DATA_DIR, f"{date_str}.jsonl")
        
        if not os.path.exists(file_path):
            return []
        
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        return records[-limit:] if limit > 0 else records
    
    def check_exists(self, snapshot_time):
        """检查记录是否存在"""
        date_str = snapshot_time[:10] if snapshot_time else datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        file_path = os.path.join(DATA_DIR, f"{date_str}.jsonl")
        
        if not os.path.exists(file_path):
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record.get('snapshot_time') == snapshot_time:
                        return True
        return False

storage = GDriveJSONLStorage()
