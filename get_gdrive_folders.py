import requests
import re

# 尝试不同的文件夹路径
folders = {
    "爷爷文件夹": "1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH",
    "旧父文件夹": "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV",
    "当前子文件夹": "1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM"
}

headers = {'User-Agent': 'Mozilla/5.0'}

for name, folder_id in folders.items():
    print(f"\n=== {name}: {folder_id} ===")
    try:
        url = f"https://drive.google.com/drive/folders/{folder_id}"
        html = requests.get(url, headers=headers, timeout=10).text
        
        # 查找所有日期格式的文件夹
        dates = re.findall(r'2026-01-\d{2}', html)
        if dates:
            unique_dates = sorted(set(dates))
            print(f"找到日期: {unique_dates}")
            
            # 尝试提取2026-01-07的文件夹ID
            pattern = r'https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)'
            folder_ids = re.findall(pattern, html)
            print(f"找到 {len(folder_ids)} 个子文件夹")
        else:
            print("未找到日期文件夹")
            
    except Exception as e:
        print(f"错误: {e}")

print("\n=== 当前配置 ===")
import json
with open('daily_folder_config.json', 'r') as f:
    print(json.dumps(json.load(f), indent=2, ensure_ascii=False))
