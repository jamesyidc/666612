import requests, re, json
from datetime import datetime
import pytz

beijing_tz = pytz.timezone('Asia/Shanghai')
today_str = datetime.now(beijing_tz).strftime('%Y-%m-%d')
parent_folder = "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV"

url = f"https://drive.google.com/drive/folders/{parent_folder}"
headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get(url, headers=headers, timeout=15).text

pattern = rf'https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)[^>]*>{today_str}<'
match = re.search(pattern, html)

if match:
    folder_id = match.group(1)
    config = {
        "root_folder_odd": parent_folder,
        "root_folder_even": parent_folder,
        "current_date": today_str,
        "folder_id": folder_id,
        "parent_folder_id": parent_folder,
        "updated_at": datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S'),
        "folder_name": today_str
    }
    with open('daily_folder_config.json', 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"✅ 已更新到{today_str}文件夹: {folder_id}")
else:
    print(f"❌ 未找到{today_str}文件夹")
