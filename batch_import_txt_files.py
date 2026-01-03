#!/usr/bin/env python3
"""
批量导入2026-01-03的所有TXT文件到数据库
"""
import requests
from bs4 import BeautifulSoup
import re
import sqlite3
from datetime import datetime
import pytz
import time
import sys

# 导入gdrive_final_detector中的解析函数
sys.path.insert(0, '/home/user/webapp')
from gdrive_final_detector import parse_content

# 配置
TODAY_FOLDER_ID = "1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ"  # 2026-01-03文件夹
DB_PATH = "/home/user/webapp/databases/crypto_data.db"
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def log(msg):
    """打印日志"""
    print(f"[{datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_all_txt_files():
    """获取文件夹中所有TXT文件"""
    log(f"📂 访问文件夹: {TODAY_FOLDER_ID}")
    url = f"https://drive.google.com/embeddedfolderview?id={TODAY_FOLDER_ID}"
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        txt_files = []
        
        for link in all_links:
            href = link.get('href', '')
            filename = link.get_text(strip=True)
            
            if filename.endswith('.txt'):
                # 提取文件ID
                if '/file/d/' in href:
                    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', href)
                    if match:
                        file_id = match.group(1)
                        txt_files.append({
                            'name': filename,
                            'id': file_id
                        })
        
        # 按文件名排序
        txt_files.sort(key=lambda x: x['name'])
        log(f"✅ 找到 {len(txt_files)} 个TXT文件")
        return txt_files
        
    except Exception as e:
        log(f"❌ 获取文件列表失败: {e}")
        return []



def download_and_parse_file(file_info):
    """下载并解析单个文件"""
    file_id = file_info['id']
    filename = file_info['name']
    
    try:
        # 下载文件内容
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        content = response.text
        
        # 从文件名提取时间戳
        # 文件名格式: 2026-01-03_1952.txt -> 2026-01-03 19:52:00
        filename_match = re.search(r'(\d{4}-\d{2}-\d{2})_(\d{2})(\d{2})\.txt', filename)
        if not filename_match:
            return None
        
        date_str = filename_match.group(1)
        hour = filename_match.group(2)
        minute = filename_match.group(3)
        file_timestamp = f"{date_str} {hour}:{minute}:00"
        
        # 使用gdrive_final_detector的解析函数
        data = parse_content(content, file_timestamp)
        
        if data:
            return data
        else:
            return None
            
    except Exception as e:
        log(f"   ❌ 下载失败: {e}")
        return None

def import_to_database(data):
    """导入数据到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute("""
            SELECT COUNT(*) FROM crypto_snapshots 
            WHERE snapshot_time = ?
        """, (data['snapshot_time'],))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False  # 已存在
        
        # 插入数据
        cursor.execute("""
            INSERT INTO crypto_snapshots 
            (snapshot_time, snapshot_date, rush_up, rush_down, diff, count, status, count_score_display, count_score_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))
        """, (
            data['snapshot_time'],
            data['snapshot_date'],
            data['rush_up'],
            data['rush_down'],
            data['diff'],
            data['count'],
            data['status'],
            data['count_score_display'],
            data['count_score_type']
        ))
        
        conn.commit()
        conn.close()
        return True  # 导入成功
        
    except Exception as e:
        log(f"   ❌ 数据库错误: {e}")
        return False

def main():
    """主函数"""
    log("=" * 80)
    log("🚀 开始批量导入2026-01-03的所有TXT文件")
    log("=" * 80)
    
    # 1. 获取所有文件
    txt_files = get_all_txt_files()
    
    if not txt_files:
        log("❌ 未找到任何TXT文件")
        return
    
    total = len(txt_files)
    success_count = 0
    skip_count = 0
    error_count = 0
    
    log(f"\n📊 准备导入 {total} 个文件...\n")
    
    # 2. 逐个处理文件
    for i, file_info in enumerate(txt_files, 1):
        filename = file_info['name']
        log(f"[{i}/{total}] 处理: {filename}")
        
        # 下载并解析
        data = download_and_parse_file(file_info)
        
        if data:
            # 导入数据库
            result = import_to_database(data)
            
            if result:
                success_count += 1
                log(f"   ✅ 导入成功: {data['snapshot_time']} | 急涨{data['rush_up']} 急跌{data['rush_down']} | {data['status']}")
            else:
                skip_count += 1
                log(f"   ⏭️  已存在，跳过")
        else:
            error_count += 1
            log(f"   ❌ 解析失败")
        
        # 避免请求过快
        time.sleep(0.5)
    
    # 3. 统计结果
    log("\n" + "=" * 80)
    log("📊 批量导入完成！")
    log("=" * 80)
    log(f"   总文件数: {total}")
    log(f"   ✅ 成功导入: {success_count}")
    log(f"   ⏭️  跳过(已存在): {skip_count}")
    log(f"   ❌ 失败: {error_count}")
    log("=" * 80)

if __name__ == '__main__':
    main()
