import requests
import json

print("\n" + "="*80)
print("🔍 测试页面API")
print("="*80)

# 测试query页面相关API
print("\n【1. Query页面相关API】")
apis = [
    '/api/query/latest',
    '/api/latest',
]

for api in apis:
    try:
        url = f'http://localhost:5000{api}'
        response = requests.get(url, timeout=5)
        print(f"\n  {api}")
        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"    返回: {json.dumps(data, ensure_ascii=False)[:100]}...")
            except:
                print(f"    返回: (非JSON)")
        else:
            print(f"    错误: {response.text[:100]}")
    except Exception as e:
        print(f"    异常: {e}")

# 测试gdrive-detector页面相关API
print("\n【2. GDrive Detector页面相关API】")
apis = [
    '/api/gdrive/status',
    '/api/gdrive/files',
    '/api/gdrive/latest-signal',
]

for api in apis:
    try:
        url = f'http://localhost:5000{api}'
        response = requests.get(url, timeout=5)
        print(f"\n  {api}")
        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"    返回: {json.dumps(data, ensure_ascii=False)[:100]}...")
            except:
                print(f"    返回: (非JSON)")
        else:
            print(f"    错误: {response.text[:100]}")
    except Exception as e:
        print(f"    异常: {e}")

print("\n" + "="*80)
