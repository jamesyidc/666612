"""
Panic Data JSONL Storage System
恐慌清洗指数数据 JSONL 存储系统
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytz

class PanicJSONLStorage:
    def __init__(self, data_dir="data/panic_snapshots"):
        """初始化JSONL存储系统"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.keep_days = 30  # 保留30天数据
        self.tz = pytz.timezone('Asia/Shanghai')
    
    def _get_date_file(self, date_str):
        """获取指定日期的文件路径"""
        return self.data_dir / f"{date_str}.jsonl"
    
    def save_snapshot(self, snapshot_data):
        """保存快照数据到JSONL"""
        try:
            # 获取北京时间
            snapshot_time = snapshot_data.get('snapshot_time')
            if isinstance(snapshot_time, str):
                dt = datetime.fromisoformat(snapshot_time.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = self.tz.localize(dt)
                else:
                    dt = dt.astimezone(self.tz)
            else:
                dt = datetime.now(self.tz)
            
            date_str = dt.strftime('%Y-%m-%d')
            file_path = self._get_date_file(date_str)
            
            # 添加写入时间戳
            snapshot_data['written_at'] = datetime.now(self.tz).isoformat()
            
            # 追加写入JSONL
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(snapshot_data, ensure_ascii=False) + '\n')
            
            # 清理旧数据
            self._cleanup_old_data()
            
            return True
        except Exception as e:
            print(f"❌ 保存快照失败: {e}")
            return False
    
    def read_latest(self, limit=1):
        """读取最新的N条记录"""
        try:
            # 获取最近几天的文件
            files = sorted(self.data_dir.glob('*.jsonl'), reverse=True)
            
            records = []
            for file_path in files[:7]:  # 最多检查最近7天
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if line.strip():
                            records.append(json.loads(line))
                            if len(records) >= limit:
                                return records
            
            return records
        except Exception as e:
            print(f"❌ 读取数据失败: {e}")
            return []
    
    def read_by_date_range(self, start_date, end_date, limit=1000):
        """读取指定日期范围的记录"""
        try:
            records = []
            current_date = datetime.strptime(end_date, '%Y-%m-%d')
            start = datetime.strptime(start_date, '%Y-%m-%d')
            
            while current_date >= start:
                date_str = current_date.strftime('%Y-%m-%d')
                file_path = self._get_date_file(date_str)
                
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                record = json.loads(line)
                                records.append(record)
                                if len(records) >= limit:
                                    return records
                
                current_date -= timedelta(days=1)
            
            return records
        except Exception as e:
            print(f"❌ 读取日期范围数据失败: {e}")
            return []
    
    def read_today(self):
        """读取今天的所有记录"""
        try:
            now = datetime.now(self.tz)
            date_str = now.strftime('%Y-%m-%d')
            file_path = self._get_date_file(date_str)
            
            if not file_path.exists():
                return []
            
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            
            return records
        except Exception as e:
            print(f"❌ 读取今日数据失败: {e}")
            return []
    
    def _cleanup_old_data(self):
        """清理超过保留期的旧数据"""
        try:
            cutoff_date = datetime.now(self.tz) - timedelta(days=self.keep_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            for file_path in self.data_dir.glob('*.jsonl'):
                file_date = file_path.stem
                if file_date < cutoff_str:
                    file_path.unlink()
                    print(f"🗑️  已删除过期文件: {file_path.name}")
        except Exception as e:
            print(f"⚠️  清理旧数据失败: {e}")
    
    def get_stats(self):
        """获取存储统计信息"""
        try:
            files = list(self.data_dir.glob('*.jsonl'))
            total_size = sum(f.stat().st_size for f in files)
            
            total_records = 0
            for file_path in files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_records += sum(1 for line in f if line.strip())
            
            return {
                'total_files': len(files),
                'total_records': total_records,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'date_range': {
                    'earliest': min(f.stem for f in files) if files else None,
                    'latest': max(f.stem for f in files) if files else None
                }
            }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}

# 全局实例
panic_storage = PanicJSONLStorage()
