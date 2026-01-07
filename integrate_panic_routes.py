#!/usr/bin/env python3
"""
将panic JSONL路由集成到app_new.py
"""

# 在app_new.py中添加import和路由注册
with open('app_new.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加import（在合适的位置）
if 'from panic_api_routes import' not in content:
    # 找到其他类似的import
    import_pos = content.find('from flask import')
    if import_pos != -1:
        # 在Flask imports之后添加
        next_line = content.find('\n', import_pos)
        content = (content[:next_line + 1] + 
                   'from panic_api_routes import register_panic_routes\n' +
                   content[next_line + 1:])
        print("✅ 已添加 panic_api_routes import")

# 添加路由注册（在app创建之后）
if 'register_panic_routes(app)' not in content:
    # 找到app初始化的地方
    app_init = content.find('app = Flask(__name__)')
    if app_init != -1:
        # 找到下一个空行或路由定义
        next_section = content.find('\n\n', app_init)
        if next_section != -1:
            content = (content[:next_section + 2] + 
                       '# 注册 panic JSONL 路由\n' +
                       'register_panic_routes(app)\n\n' +
                       content[next_section + 2:])
            print("✅ 已添加 panic 路由注册")

# 写回文件
with open('app_new.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 集成完成")
