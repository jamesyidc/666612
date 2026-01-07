#!/usr/bin/env python3
"""
临时脚本：将SAR路由集成到app_new.py
"""

# 在app_new.py中添加导入
import_statement = """
# SAR斜率系统 - JSONL存储
from sar_api_routes import register_sar_routes
"""

# 在app创建后添加注册调用
register_call = """
# 注册SAR斜率路由
register_sar_routes(app)
"""

# 读取app_new.py
with open('app_new.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否已经添加
if 'from sar_api_routes import' not in content:
    # 在导入部分添加
    import_pos = content.find('from flask import')
    if import_pos != -1:
        # 找到Flask导入后的位置
        next_newline = content.find('\n', import_pos)
        content = content[:next_newline+1] + import_statement + content[next_newline+1:]
        print("✅ 已添加导入语句")
    
    # 在app创建后添加注册
    app_creation = "app = Flask(__name__)"
    app_pos = content.find(app_creation)
    if app_pos != -1:
        # 找到app创建后的位置
        next_newline = content.find('\n', app_pos + len(app_creation))
        content = content[:next_newline+1] + register_call + content[next_newline+1:]
        print("✅ 已添加路由注册")
    
    # 保存
    with open('app_new.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ SAR路由已集成到app_new.py")
else:
    print("ℹ️  SAR路由已经集成过了")

