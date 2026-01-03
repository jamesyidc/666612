#!/usr/bin/env python3
"""
检查"首页数据"文件夹下有哪些日期文件夹
"""
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# "首页数据"文件夹ID
home_data_folder_id = "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV"

print(f"📂 访问\"首页数据\"文件夹: {home_data_folder_id}")
url = f"https://drive.google.com/embeddedfolderview?id={home_data_folder_id}"

try:
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 查找所有文件夹链接
    all_links = soup.find_all('a', href=True)
    
    print(f"\n📋 找到 {len(all_links)} 个链接")
    print("\n🔍 查找日期文件夹:")
    
    date_folders = []
    for link in all_links:
        href = link.get('href', '')
        foldername = link.get_text(strip=True)
        
        # 查找文件夹
        if '/folders/' in href:
            match = re.search(r'/folders/([a-zA-Z0-9_-]+)', href)
            if match:
                folder_id = match.group(1)
                
                # 检查是否是日期格式 (YYYY-MM-DD)
                date_match = re.match(r'^\d{4}-\d{2}-\d{2}$', foldername)
                if date_match:
                    date_folders.append((foldername, folder_id))
    
    # 按日期排序
    date_folders.sort(reverse=True)
    
    print(f"\n✅ 找到 {len(date_folders)} 个日期文件夹:")
    print(f"\n📅 最近的日期文件夹:")
    for i, (date, folder_id) in enumerate(date_folders[:10]):
        today = datetime.now().strftime('%Y-%m-%d')
        marker = " ✅ (今天)" if date == today else ""
        print(f"   {i+1}. {date}: {folder_id}{marker}")
    
    # 检查今天的文件夹
    today = datetime.now().strftime('%Y-%m-%d')
    today_folder = next((f for f in date_folders if f[0] == today), None)
    
    if today_folder:
        print(f"\n✅ 今天 ({today}) 的文件夹存在:")
        print(f"   ID: {today_folder[1]}")
        print(f"   URL: https://drive.google.com/drive/folders/{today_folder[1]}")
    else:
        print(f"\n⚠️  今天 ({today}) 的文件夹不存在")
        print(f"   最新文件夹: {date_folders[0][0] if date_folders else '无'}")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
