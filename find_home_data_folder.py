#!/usr/bin/env python3
"""
查找Google Drive中的"首页数据"文件夹ID
"""
import requests
from bs4 import BeautifulSoup
import re

# 父文件夹ID
parent_folder_id = "1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH"

print(f"📂 访问父文件夹: {parent_folder_id}")
url = f"https://drive.google.com/embeddedfolderview?id={parent_folder_id}"

try:
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 查找所有文件夹链接
    all_links = soup.find_all('a', href=True)
    
    print(f"\n📋 找到 {len(all_links)} 个链接")
    print("\n🔍 查找文件夹:")
    
    for link in all_links:
        href = link.get('href', '')
        foldername = link.get_text(strip=True)
        
        # 查找文件夹
        if '/folders/' in href:
            match = re.search(r'/folders/([a-zA-Z0-9_-]+)', href)
            if match:
                folder_id = match.group(1)
                print(f"   📁 {foldername}: {folder_id}")
                
                # 特别标注"首页数据"文件夹
                if '首页数据' in foldername or 'home' in foldername.lower():
                    print(f"   ✅ 找到首页数据文件夹！")
                    print(f"   ID: {folder_id}")
                    print(f"   URL: https://drive.google.com/drive/folders/{folder_id}")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
