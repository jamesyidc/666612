#!/usr/bin/env python3
"""
批量修复采集器的数据库连接泄漏问题
将 try-except 改为 try-except-finally 确保连接总是被关闭
"""
import os
import re

def fix_collector_file(filepath):
    """
    修复单个采集器文件
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 模式1: 查找 conn = sqlite3.connect ... 后没有 finally 的情况
    # 使用正则查找所有的 try 块
    pattern = re.compile(
        r'([ \t]*)try:\s*\n'  # try:
        r'(.*?)'  # try块的内容
        r'([ \t]*)except\s+.*?:\s*\n'  # except:
        r'(.*?)'  # except块的内容
        r'(?!\1[ \t]+finally:)',  # 没有finally
        re.DOTALL
    )
    
    # 检查是否需要修复
    needs_fix = False
    for match in pattern.finditer(content):
        try_content = match.group(2)
        if 'sqlite3.connect' in try_content and 'conn.close()' in try_content:
            # 检查except块中是否有连接关闭
            except_content = match.group(4)
            if 'conn.close()' not in except_content:
                needs_fix = True
                break
    
    if not needs_fix:
        return False
    
    # 进行修复：在每个有 conn.close() 的 try-except 后添加 finally
    # 这里简化处理：只打印需要修复的文件
    return True

# 需要检查的采集器列表
collectors = [
    'panic_wash_collector.py',
    'price_comparison_collector.py',
    'position_system_collector.py',
    'crypto_index_collector.py',
    'okex_websocket_realtime_collector.py',
    'escape_top_signals_collector.py',
]

print("="*60)
print("🔍 检查采集器数据库连接管理")
print("="*60)

for collector in collectors:
    filepath = f'/home/user/webapp/{collector}'
    if os.path.exists(filepath):
        if fix_collector_file(filepath):
            print(f"⚠️  {collector}: 需要修复")
        else:
            print(f"✅ {collector}: 正常")
    else:
        print(f"❌ {collector}: 文件不存在")

print("\n" + "="*60)
print("💡 建议：手动修复需要处理的文件")
print("   将 try-except 改为 try-finally 或 try-except-finally")
print("   确保 conn.close() 在 finally 块中")
print("="*60)
