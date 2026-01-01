#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复5个问题的补丁脚本
1. 清零操作JSON parse错误
2. 手动维护leverage变量未定义
3. CRO维护失败All operations failed
4. 维护后今日维护数量未增加
5. 单个币种15分钟维护间隔限制
"""

import sys

# 问题1: app_new.py line 15181 - 清零JSON parse错误
# 原因：json已经在开头导入，但又import json as json_lib导致冲突
FIX_1_OLD = '''    try:
        import json as json_lib
        from datetime import datetime
        import pytz
        
        data = request.json'''

FIX_1_NEW = '''    try:
        from datetime import datetime
        import pytz
        
        data = request.json'''

# 问题2: app_new.py line 15446 - leverage变量未定义
# 应该使用lever而不是leverage
FIX_2_OLD = '''        print(f"📊 第1步：设置逐仓杠杆 {leverage}x")
        leverage_path = '/api/v5/account/set-leverage'
        leverage_body = {
            'instId': inst_id,
            'lever': str(leverage),'''

FIX_2_NEW = '''        print(f"📊 第1步：设置逐仓杠杆 {lever}x")
        leverage_path = '/api/v5/account/set-leverage'
        leverage_body = {
            'instId': inst_id,
            'lever': str(lever),'''

# 问题3: maintenance_trade_executor.py - 增加更详细的错误信息
# 已在之前修复中处理（数量取整）

# 问题4: 增加维护计数更新逻辑 - 在anchor_maintenance_realtime_daemon.py中添加
# 需要在执行成功后调用Flask API更新计数

# 问题5: 增加15分钟间隔检查
# 在手动维护和自动维护中都要检查

FIX_5_CHECK = '''
        # 检查15分钟维护间隔
        if record_key in maintenance_data:
            record = maintenance_data[record_key]
            last_maintenance_str = record.get('last_maintenance', '')
            if last_maintenance_str:
                try:
                    last_time = datetime.strptime(last_maintenance_str, '%Y-%m-%d %H:%M:%S')
                    last_time = beijing_tz.localize(last_time)
                    time_diff = (now_beijing - last_time).total_seconds() / 60
                    
                    if time_diff < 15:
                        return jsonify({
                            'success': False,
                            'message': f'距离上次维护仅{time_diff:.1f}分钟，需要至少15分钟间隔',
                            'last_maintenance': last_maintenance_str,
                            'next_available': (last_time + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                        })
                except:
                    pass
'''

print("=" * 80)
print("修复5个问题的代码已准备好")
print("=" * 80)
print("\n问题1: 清零JSON parse错误")
print("  - 移除重复的json导入")
print("\n问题2: 手动维护leverage变量未定义") 
print("  - 将leverage改为lever")
print("\n问题3: CRO维护失败")
print("  - 已通过数量取整修复")
print("\n问题4: 维护后计数未增加")
print("  - 需要在守护进程中添加计数更新")
print("\n问题5: 15分钟维护间隔")
print("  - 添加时间间隔检查")
print("\n" + "=" * 80)
