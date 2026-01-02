#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出PM2进程配置
从 ~/.pm2/dump.pm2 读取配置，生成易读的配置文件
"""

import json
import os
from pathlib import Path

def export_pm2_config():
    """导出PM2配置"""
    pm2_dump_path = Path.home() / '.pm2' / 'dump.pm2'
    output_path = Path('/home/user/webapp/PM2_PROCESSES.json')
    
    if not pm2_dump_path.exists():
        print(f"❌ PM2配置文件不存在: {pm2_dump_path}")
        return
    
    with open(pm2_dump_path, 'r') as f:
        processes = json.load(f)
    
    # 提取关键信息
    simplified_processes = []
    for proc in processes:
        simplified = {
            "name": proc.get("name"),
            "script": proc.get("pm_exec_path"),
            "cwd": proc.get("pm_cwd"),
            "interpreter": proc.get("exec_interpreter"),
            "exec_mode": proc.get("exec_mode"),
            "autorestart": proc.get("autorestart"),
            "watch": proc.get("watch"),
            "log_out": proc.get("pm_out_log_path"),
            "log_err": proc.get("pm_err_log_path"),
            "pid_file": proc.get("pm_pid_path")
        }
        simplified_processes.append(simplified)
    
    # 保存到文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(simplified_processes, f, indent=2, ensure_ascii=False)
    
    print(f"✅ PM2配置已导出到: {output_path}")
    print(f"📊 共 {len(simplified_processes)} 个进程")
    
    # 打印进程列表
    print("\n📋 进程列表:")
    for proc in simplified_processes:
        print(f"  - {proc['name']}: {proc['script']}")

if __name__ == '__main__':
    export_pm2_config()
