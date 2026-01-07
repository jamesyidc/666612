import requests, re, json
from datetime import datetime
import pytz

beijing_tz = pytz.timezone('Asia/Shanghai')
today_str = datetime.now(beijing_tz).strftime('%Y-%m-%d')

# 爷爷文件夹
root_folder = "1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH"
print(f"步骤1: 访问爷爷文件夹 {root_folder}")

url = f"https://drive.google.com/drive/folders/{root_folder}"
headers = {'User-Agent': 'Mozilla/5.0'}
html = requests.get(url, headers=headers, timeout=15).text

# 查找"首页数据"文件夹
pattern = r'https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)[^>]*>首页数据<'
match = re.search(pattern, html)

if not match:
    print("❌ 未找到'首页数据'文件夹")
    exit(1)

parent_folder = match.group(1)
print(f"✅ 找到'首页数据'文件夹: {parent_folder}")

# 访问"首页数据"文件夹，查找今天的日期文件夹
print(f"\n步骤2: 访问'首页数据'文件夹查找 {today_str}")
url = f"https://drive.google.com/drive/folders/{parent_folder}"
html = requests.get(url, headers=headers, timeout=15).text

# 查找今天日期的文件夹
pattern = rf'https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)[^>]*>{today_str}<'
match = re.search(pattern, html)

if match:
    today_folder = match.group(1)
    print(f"✅ 找到今天的文件夹: {today_folder}")
else:
    # 如果没有今天的，列出所有日期文件夹
    dates = re.findall(r'>(\d{4}-\d{2}-\d{2})<', html)
    if dates:
        latest_date = sorted(dates)[-1]
        pattern = rf'https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)[^>]*>{latest_date}<'
        match = re.search(pattern, html)
        today_folder = match.group(1) if match else None
        print(f"⚠️ 未找到{today_str}，使用最新日期 {latest_date}: {today_folder}")
    else:
        print("❌ 未找到任何日期文件夹")
        exit(1)

# 更新配置
config = {
    "root_folder_odd": parent_folder,
    "root_folder_even": parent_folder,
    "current_date": today_str,
    "folder_id": today_folder,
    "parent_folder_id": parent_folder,
    "updated_at": datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S'),
    "folder_name": today_str
}

with open('daily_folder_config.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"\n✅ 配置已更新到: {today_folder}")
