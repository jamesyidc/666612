#!/usr/bin/env python3
"""
加密货币数据分析系统 - 完全仿照参考页面风格
"""
from flask import Flask, render_template_string, render_template, request, jsonify, send_from_directory, make_response, redirect
import sqlite3
from datetime import datetime, timedelta
import json
import pytz
import os
from functools import wraps
import time
import traceback

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_china_today():
    """获取中国时区的今日日期字符串 (YYYY-MM-DD)"""
    return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')

def get_china_now():
    """获取中国时区的当前时间"""
    return datetime.now(BEIJING_TZ)

# 导入交易API Blueprint
from trading_api import trading_bp
app.register_blueprint(trading_bp)

# K线图服务URL配置
CHART_BASE_URL = "https://5000-iz6uddj6rs3xe48ilsyqq-2e1b9533.sandbox.novita.ai"

# ============================================
# 服务器端缓存系统
# ============================================
class ServerCache:
    """服务器端内存缓存，存储计算结果"""
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        
    def get(self, key, max_age=60):
        """
        获取缓存数据
        key: 缓存键
        max_age: 最大缓存时间（秒），默认60秒
        """
        if key not in self.cache:
            return None
        
        # 检查是否过期
        if time.time() - self.timestamps.get(key, 0) > max_age:
            # 过期，删除缓存
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def set(self, key, value):
        """设置缓存数据"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self, key=None):
        """清除缓存"""
        if key:
            if key in self.cache:
                del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]
        else:
            self.cache.clear()
            self.timestamps.clear()
    
    def get_stats(self):
        """获取缓存统计信息"""
        return {
            'total_keys': len(self.cache),
            'keys': list(self.cache.keys())
        }

# 创建全局缓存实例
server_cache = ServerCache()

def cached_response(max_age=60):
    """
    缓存装饰器 - 在服务器端缓存API响应
    max_age: 缓存有效期（秒）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{f.__name__}:{':'.join(map(str, args))}"
            
            # 尝试从缓存获取
            cached_data = server_cache.get(cache_key, max_age=max_age)
            if cached_data is not None:
                # 创建响应副本并添加缓存标记
                response_data = cached_data.copy()
                response_data['_from_server_cache'] = True
                response_data['_cache_age_seconds'] = int(time.time() - server_cache.timestamps.get(cache_key, 0))
                return jsonify(response_data)
            
            # 执行原函数获取结果
            result = f(*args, **kwargs)
            
            # 提取并缓存JSON数据
            if hasattr(result, 'json') and callable(result.json):
                try:
                    data = result.json
                    if isinstance(data, dict) and data.get('success'):
                        server_cache.set(cache_key, data)
                except:
                    pass
            
            return result
        
        return decorated_function
    return decorator

# 主页面HTML - 完全仿照参考设计
MAIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>加密货币数据历史回看</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: #1e2139;
            color: #fff;
            overflow-x: hidden;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
            padding: 0;
        }
        
        /* 顶部导航栏 */
        .top-nav {
            background: #2a2d47;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            justify-content: space-between;
        }
        
        .nav-left {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .nav-right {
            display: flex;
            gap: 10px;
        }
        
        /* 系统导航栏 */
        .systems-nav {
            background: linear-gradient(135deg, #2a2d47 0%, #3a3d5c 100%);
            padding: 15px 20px;
            border-bottom: 2px solid #3b7dff;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .systems-nav-title {
            font-size: 14px;
            font-weight: 600;
            color: #8b92b8;
            margin-right: 10px;
        }
        
        .system-link {
            background: rgba(59, 125, 255, 0.1);
            border: 1px solid rgba(59, 125, 255, 0.3);
            color: #00d4ff;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .system-link:hover {
            background: rgba(59, 125, 255, 0.2);
            border-color: #3b7dff;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 125, 255, 0.3);
        }
        
        .system-link.featured {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: #fff;
        }
        
        .system-link.featured:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        .home-btn {
            background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
            color: #fff;
            border: none;
            padding: 8px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .home-btn:hover {
            background: linear-gradient(135deg, #0099ff 0%, #00d4ff 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 212, 255, 0.4);
        }
        
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 8px;
            background: #3b7dff;
            padding: 6px 15px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .nav-title {
            font-size: 18px;
            font-weight: 500;
            color: #fff;
            margin-left: 10px;
        }
        
        /* 控制栏 */
        .control-bar {
            background: #2a2d47;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
            border-bottom: 1px solid #3a3d5c;
        }
        
        .control-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .control-label {
            color: #8b92b8;
            font-size: 13px;
        }
        
        .control-input {
            background: #1e2139;
            border: 1px solid #3a3d5c;
            color: #fff;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 13px;
            outline: none;
        }
        
        .control-input:focus {
            border-color: #3b7dff;
        }
        
        .control-btn {
            background: #3b7dff;
            border: none;
            color: white;
            padding: 7px 18px;
            border-radius: 4px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .control-btn:hover {
            background: #2563eb;
        }
        
        .control-btn.secondary {
            background: #4a5178;
        }
        
        .control-btn.secondary:hover {
            background: #5a6188;
        }
        
        /* 数据统计栏 */
        .stats-bar {
            background: #2a2d47;
            padding: 12px 20px;
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
            border-bottom: 1px solid #3a3d5c;
            font-size: 13px;
        }
        
        .stat-item {
            display: flex;
            gap: 5px;
        }
        
        .stat-label {
            color: #8b92b8;
        }
        
        .stat-value {
            color: #fff;
            font-weight: 500;
            margin-left: 8px;
        }
        
        .stat-value.rise {
            color: #10b981;
        }
        
        .stat-value.fall {
            color: #ef4444;
        }
        
        /* 次级统计栏 */
        .secondary-stats {
            background: #1e2139;
            padding: 10px 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 13px;
        }
        
        /* 时间轴容器 - 竖直布局 */
        .timeline-container {
            background: #2a2d47;
            padding: 15px 20px;
            border-top: 1px solid #3a3d5c;
            max-height: 500px;  /* 增加高度以显示更多信息 */
            overflow-y: auto;
        }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            position: sticky;
            top: 0;
            background: #2a2d47;
            padding-bottom: 10px;
            border-bottom: 1px solid #3a3d5c;
        }
        
        .timeline-title {
            color: #8b92b8;
            font-size: 13px;
            font-weight: 500;
        }
        
        .timeline-info {
            color: #3b7dff;
            font-size: 12px;
        }
        
        /* 竖直时间轴轨道 */
        .timeline-track {
            position: relative;
            padding-left: 30px;
            margin-top: 10px;
        }
        
        /* 竖直线 */
        .timeline-line {
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #3a3d5c;
        }
        
        /* 竖直排列的时间点容器 */
        .timeline-points {
            display: flex;
            flex-direction: column;
            gap: 20px;  /* 增加间距以容纳更多信息 */
        }
        
        /* 时间点项 */
        .timeline-point {
            position: relative;
            display: flex;
            align-items: flex-start;  /* 改为顶部对齐，适应多行内容 */
            cursor: pointer;
            padding: 10px 12px;  /* 增加padding */
            border-radius: 4px;
            transition: all 0.3s;
            min-height: 80px;  /* 最小高度确保显示多行信息 */
        }
        
        .timeline-point:hover {
            background: rgba(59, 125, 255, 0.1);
        }
        
        /* 时间点圆圈 */
        .timeline-point::before {
            content: '';
            position: absolute;
            left: -22px;
            width: 12px;
            height: 12px;
            background: #3b7dff;
            border: 2px solid #2a2d47;
            border-radius: 50%;
            transition: all 0.3s;
            z-index: 2;
        }
        
        .timeline-point:hover::before {
            width: 16px;
            height: 16px;
            left: -24px;
            background: #2563eb;
            box-shadow: 0 0 10px rgba(59, 125, 255, 0.5);
        }
        
        .timeline-point.active::before {
            background: #10b981;
            width: 16px;
            height: 16px;
            left: -24px;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }
        
        /* 时间标签 */
        .timeline-label {
            color: #8b92b8;
            font-size: 12px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        
        .timeline-point:hover .timeline-label {
            color: #fff;
        }
        
        .timeline-point.active .timeline-label {
            color: #10b981;
            font-weight: 500;
        }
        
        .timeline-label-time {
            font-size: 13px;
            font-weight: 500;
        }
        
        .timeline-label-stats {
            font-size: 11px;
            opacity: 0.85;
            line-height: 1.5;
            color: #a0aec0;
            max-width: 600px;  /* 限制最大宽度 */
        }
        
        .timeline-label-stats div {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* 图表区域 */
        .chart-section {
            background: #2a2d47;
            margin: 0;
            padding: 20px;
        }
        
        .chart-title {
            color: #8b92b8;
            font-size: 14px;
            margin-bottom: 15px;
            text-align: center;
        }
        
        #mainChart {
            width: 100%;
            height: 450px;  /* 增加高度，让图表更清晰 */
        }
        
        /* 数据列表标题 */
        .data-list-header {
            background: #2a2d47;
            padding: 12px 20px;
            color: #3b7dff;
            font-size: 14px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* 表格容器 */
        .table-container {
            background: #1e2139;
            overflow-x: auto;
        }
        
        /* 数据表格 */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        .data-table thead {
            background: #ef4444;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .data-table th {
            padding: 10px 8px;
            text-align: center;
            font-weight: 500;
            color: #fff;
            border-right: 1px solid #dc2626;
            white-space: nowrap;
        }
        
        .data-table tbody tr {
            border-bottom: 1px solid #2a2d47;
        }
        
        .data-table tbody tr:hover {
            background: #2a2d47;
        }
        
        .data-table td {
            padding: 8px 6px;
            text-align: center;
            border-right: 1px solid #2a2d47;
            white-space: nowrap;
        }
        
        /* 操作列 */
        .action-btn {
            background: #ef4444;
            border: none;
            color: white;
            padding: 4px 10px;
            border-radius: 3px;
            font-size: 11px;
            cursor: pointer;
            font-weight: 500;
        }
        
        .action-btn:hover {
            background: #dc2626;
        }
        
        /* 币种名称 */
        .coin-symbol {
            font-weight: 600;
            color: #fff;
        }
        
        /* 数值颜色 */
        .value-positive {
            color: #ef4444;
        }
        
        .value-negative {
            color: #10b981;
        }
        
        .value-neutral {
            color: #8b92b8;
        }
        
        /* 状态标签 */
        .status-tag {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }
        
        .status-tag.rise {
            background: #dc2626;
            color: white;
        }
        
        .status-tag.fall {
            background: #10b981;
            color: white;
        }
        
        /* 优先级颜色 */
        .priority-1 { color: #ff0000; font-weight: bold; }
        .priority-2 { color: #ff6600; font-weight: bold; }
        .priority-3 { color: #ff9900; }
        .priority-4 { color: #ffcc00; }
        .priority-5 { color: #99cc00; }
        .priority-6 { color: #8b92b8; }
        
        /* 加载状态 */
        .loading {
            text-align: center;
            padding: 40px;
            color: #8b92b8;
            font-size: 14px;
        }
        
        /* 响应式 */
        @media (max-width: 768px) {
            .control-bar {
                flex-direction: column;
                align-items: stretch;
            }
            
            .stats-bar {
                flex-direction: column;
                gap: 10px;
            }
            
            .data-table {
                font-size: 11px;
            }
            
            .data-table th,
            .data-table td {
                padding: 6px 4px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 顶部导航 -->
        <div class="top-nav">
            <div class="nav-left">
                <div class="nav-brand">
                    <span>📊</span> 数据回看
                </div>
                <div class="nav-title">加密货币数据历史回看</div>
            </div>
            <div class="nav-right">
                <button class="home-btn" onclick="window.location.href='/'">
                    <span>🏠</span> 返回首页
                </button>
            </div>
        </div>
        
        <!-- 系统导航栏 -->
        <div class="systems-nav">
            <div class="systems-nav-title">快速访问:</div>
            <a href="/sar-slope" class="system-link featured">
                <span>📈</span> SAR斜率系统
            </a>
            <a href="/kline-indicators" class="system-link">
                <span>📊</span> K线指标系统
            </a>
            <a href="/support-resistance" class="system-link">
                <span>📉</span> 支撑阻力系统
            </a>
            <a href="/position-system" class="system-link">
                <span>💼</span> 仓位系统
            </a>
            <a href="/gdrive-monitor-status" class="system-link">
                <span>☁️</span> Google Drive监控
            </a>
            <a href="/crypto-index" class="system-link">
                <span>📈</span> 指数系统
            </a>
            <a href="/coin-pool" class="system-link">
                <span>🏊</span> 币池系统
            </a>
            <a href="/price-comparison" class="system-link">
                <span>💱</span> 比价系统
            </a>
            <a href="/fund-monitor" class="system-link featured">
                <span>💰</span> 资金监控系统
            </a>
        </div>
        
        <!-- 控制栏 -->
        <div class="control-bar">
            <div class="control-group">
                <span class="control-label">选项日期:</span>
                <input type="date" id="queryDate" class="control-input">
            </div>
            
            <div class="control-group">
                <span class="control-label">时间选择:</span>
                <input type="time" id="queryTime" class="control-input" value="00:00">
            </div>
            
            <div class="control-group">
                <span class="control-label">至</span>
                <input type="time" id="endTime" class="control-input" value="23:59">
            </div>
            
            <button class="control-btn" onclick="queryData()">🔍 查询</button>
            <button class="control-btn secondary" onclick="loadToday()">📊 今天</button>
            <button class="control-btn secondary" onclick="loadLatest()">📡 立即加载</button>
            <button class="control-btn secondary" onclick="batchImportData()" id="batchImportBtn">📥 批量导入今日数据</button>
        </div>
        
        <!-- 主要统计栏 -->
        <div class="stats-bar">
            <div class="stat-item">
                <span class="stat-label">运算时间:</span>
                <span class="stat-value" id="calcTime">2025-12-06 13:42:42</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">急涨:</span>
                <span class="stat-value rise" id="rushUp">1</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">急跌:</span>
                <span class="stat-value fall" id="rushDown">22</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">本轮急涨:</span>
                <span class="stat-value" id="roundRushUp">1</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">本轮急跌:</span>
                <span class="stat-value" id="roundRushDown">22</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">计次:</span>
                <span class="stat-value" id="countTimes">10</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">计次得分:</span>
                <span class="stat-value" id="countScore">☆☆☆</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">状态:</span>
                <span class="stat-value" id="status">震荡无序</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">比值:</span>
                <span class="stat-value" id="ratio">10</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">差值:</span>
                <span class="stat-value" id="diff">-21</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">比价最低:</span>
                <span class="stat-value" id="priceLowest">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">比价创新高:</span>
                <span class="stat-value" id="priceNewhigh">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">24h涨≥10%:</span>
                <span class="stat-value rise" id="rise24hCount">0</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">24h跌≤-10%:</span>
                <span class="stat-value fall" id="fall24hCount">0</span>
            </div>

        </div>
        
        <!-- 次级统计栏 -->
        <div class="secondary-stats">
            <div class="stat-item">
                <span class="stat-label">已回调历史: 无</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">回调天数: 168 秒/0次</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">时间偏限: 2025-12-04 10:22:00 ~ 2025-12-04 18:32:00</span>
            </div>
        </div>
        
        <!-- 图表区域 -->
        <div class="chart-section">
            <div class="chart-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div class="chart-title">急涨/急跌历史趋势图</div>
                <div class="chart-pagination" style="display: flex; gap: 10px; align-items: center;">
                    <span id="chartTimeRange" style="color: #8b92b8; font-size: 12px;"></span>
                    <button id="btnPrevPage" class="page-btn" style="padding: 5px 12px; background: #3a3d5c; color: #8b92b8; border: 1px solid #4a4d6c; border-radius: 4px; cursor: pointer;" disabled>
                        ◀ 上一页
                    </button>
                    <span id="chartPageInfo" style="color: #8b92b8; font-size: 12px;">第1页</span>
                    <button id="btnNextPage" class="page-btn" style="padding: 5px 12px; background: #3a3d5c; color: #8b92b8; border: 1px solid #4a4d6c; border-radius: 4px; cursor: pointer;" disabled>
                        下一页 ▶
                    </button>
                </div>
            </div>
            <div id="mainChart"></div>
        </div>
        
        <!-- 时间轴 - 放在图表下方 -->
        <div class="timeline-container">
            <div class="timeline-header">
                <span class="timeline-title">历史数据时间轴</span>
                <span class="timeline-info" id="timelineInfo">加载中...</span>
            </div>
            <div class="timeline-track">
                <div class="timeline-line"></div>
                <div id="timelinePoints" class="timeline-points"></div>
            </div>
        </div>
        
        <!-- 数据列表标题 -->
        <div class="data-list-header">
            <span>📋</span> 币列表
        </div>
        
        <!-- 数据表格 -->
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>优先级</th>
                        <th>序号</th>
                        <th>币名</th>
                        <th>涨跌</th>
                        <th>急涨</th>
                        <th>急跌</th>
                        <th>更新时间</th>
                        <th>历史高点</th>
                        <th>高点时间</th>
                        <th>跌幅</th>
                        <th>24h%</th>
                        <th>排行</th>
                        <th>当前价格</th>
                        <th>最高占比</th>
                        <th>最低占比</th>
                    </tr>
                </thead>
                <tbody id="dataTableBody">
                    <tr>
                        <td colspan="15" class="loading">正在加载数据...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // 初始化图表
        const chart = echarts.init(document.getElementById('mainChart'));
        
        // 初始化日期
        const today = new Date();
        document.getElementById('queryDate').valueAsDate = today;
        
        // 图表配置
        function updateChart(data) {
            const option = {
                backgroundColor: 'transparent',
                grid: {
                    left: '50px',
                    right: '50px',
                    bottom: '120px',  // 增加底部空间给旋转的横轴标签
                    top: '50px',
                    containLabel: true
                },
                tooltip: {
                    trigger: 'axis',  // 改为axis触发，显示同一时间点所有数据
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    borderColor: '#3a3d5c',
                    borderWidth: 1,
                    textStyle: { color: '#fff', fontSize: 12 },
                    axisPointer: {
                        type: 'cross',
                        crossStyle: {
                            color: '#8b92b8'
                        }
                    },
                    formatter: function(params) {
                        if (!params || params.length === 0) return '';
                        const time = params[0].axisValue;
                        let html = `<div style="padding: 8px;">
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 13px; border-bottom: 1px solid #3a3d5c; padding-bottom: 5px;">${time}</div>`;
                        
                        params.forEach(item => {
                            html += `<div style="margin-top: 5px; display: flex; align-items: center; justify-content: space-between; gap: 15px;">
                                <span style="display: flex; align-items: center;">
                                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: ${item.color}; margin-right: 8px;"></span>
                                    ${item.seriesName}
                                </span>
                                <span style="color: ${item.color}; font-weight: bold;">${item.value}</span>
                            </div>`;
                        });
                        
                        html += '</div>';
                        return html;
                    }
                },
                legend: {
                    data: ['急涨', '急跌', '差值(急涨-急跌)', '计次'],
                    top: 10,
                    left: 'center',
                    textStyle: { color: '#8b92b8', fontSize: 13 },
                    itemWidth: 30,
                    itemHeight: 14,
                    itemGap: 20
                },
                xAxis: {
                    type: 'category',
                    data: data.times || [],
                    axisLine: { 
                        lineStyle: { color: '#3a3d5c', width: 1 }
                    },
                    axisLabel: { 
                        color: '#8b92b8',
                        fontSize: 10,
                        rotate: 45,  // 旋转45度，避免重叠
                        interval: 0,  // 显示所有标签
                        margin: 12,
                        align: 'right',  // 右对齐
                        verticalAlign: 'middle'
                    },
                    axisTick: {
                        show: true,
                        lineStyle: { color: '#3a3d5c' }
                    },
                    splitLine: { 
                        show: true,  // 显示分隔线
                        lineStyle: {
                            color: '#3a3d5c',
                            type: 'solid',  // 实线
                            width: 1,
                            opacity: 0.3
                        }
                    }
                },
                yAxis: [
                    {
                        type: 'value',
                        name: '数量',
                        nameTextStyle: { 
                            color: '#8b92b8', 
                            fontSize: 12,
                            padding: [0, 0, 0, 10]
                        },
                        axisLine: { 
                            show: true,
                            lineStyle: { color: '#3a3d5c' } 
                        },
                        axisLabel: { 
                            color: '#8b92b8', 
                            fontSize: 11 
                        },
                        splitLine: { 
                            lineStyle: { 
                                color: '#3a3d5c', 
                                type: 'dashed',
                                opacity: 0.5
                            } 
                        }
                    },
                    {
                        type: 'value',
                        name: '计次',
                        nameTextStyle: { 
                            color: '#3b7dff', 
                            fontSize: 12,
                            padding: [0, 10, 0, 0]
                        },
                        axisLine: { 
                            show: true,
                            lineStyle: { color: '#3a3d5c' } 
                        },
                        axisLabel: { 
                            color: '#3b7dff', 
                            fontSize: 11 
                        },
                        splitLine: { show: false }
                    }
                ],
                series: [
                    {
                        name: '急涨',
                        type: 'line',
                        data: data.rush_up || [],
                        smooth: true,
                        connectNulls: true,  // 连接所有数据点，形成连续线段
                        lineStyle: {
                            width: 3,
                            color: '#ef4444'
                        },
                        itemStyle: { 
                            color: '#ef4444',
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        symbolSize: 8,
                        emphasis: {
                            scale: true,
                            scaleSize: 12
                        }
                    },
                    {
                        name: '急跌',
                        type: 'line',
                        data: data.rush_down || [],
                        smooth: true,
                        connectNulls: true,  // 连接所有数据点，形成连续线段
                        lineStyle: {
                            width: 3,
                            color: '#10b981'
                        },
                        itemStyle: { 
                            color: '#10b981',
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        symbolSize: 8,
                        emphasis: {
                            scale: true,
                            scaleSize: 12
                        }
                    },
                    {
                        name: '差值(急涨-急跌)',
                        type: 'line',
                        data: data.diff || [],
                        smooth: true,
                        connectNulls: true,  // 连接所有数据点，形成连续线段
                        lineStyle: {
                            width: 3,
                            color: '#fbbf24'
                        },
                        itemStyle: { 
                            color: '#fbbf24',
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        symbolSize: 8,
                        emphasis: {
                            scale: true,
                            scaleSize: 12
                        }
                    },
                    {
                        name: '计次',
                        type: 'line',
                        yAxisIndex: 1,
                        data: data.count || [],
                        smooth: true,
                        connectNulls: true,  // 连接所有数据点，形成连续线段
                        lineStyle: {
                            width: 3,
                            color: '#3b7dff'
                        },
                        itemStyle: { 
                            color: '#3b7dff',
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        symbolSize: 8,
                        emphasis: {
                            scale: true,
                            scaleSize: 12
                        }
                    }
                ]
            };
            
            chart.setOption(option);
        }
        
        // 查询数据
        function queryData() {
            const date = document.getElementById('queryDate').value;
            const time = document.getElementById('queryTime').value;
            const datetime = date + ' ' + time;
            
            fetch('/api/query?time=' + encodeURIComponent(datetime))
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('❌ ' + data.error);
                        return;
                    }
                    updateUI(data);
                    loadChartData();  // 加载所有历史数据趋势图
                })
                .catch(error => {
                    alert('查询失败: ' + error);
                });
        }
        
        // 加载今天
        function loadToday() {
            const today = new Date();
            document.getElementById('queryDate').valueAsDate = today;
            queryData();
        }
        
        // 加载最新
        function loadLatest() {
            fetch('/api/latest')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert('❌ ' + data.error);
                        return;
                    }
                    updateUI(data);
                    loadChartData();  // 加载所有历史数据趋势图
                })
                .catch(error => {
                    alert('加载失败: ' + error);
                });
        }
        
        // 批量导入今日数据
        function batchImportData() {
            const btn = document.getElementById('batchImportBtn');
            const originalText = btn.innerHTML;
            
            // 禁用按钮并显示加载状态
            btn.disabled = true;
            btn.innerHTML = '⏳ 正在批量导入...';
            btn.style.opacity = '0.6';
            btn.style.cursor = 'not-allowed';
            
            fetch('/api/query/batch-import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const stats = data.stats;
                    let message = `✅ 批量导入完成！\n\n`;
                    message += `📊 统计结果：\n`;
                    message += `   总文件数: ${stats.total}\n`;
                    message += `   ✅ 成功导入: ${stats.success}\n`;
                    message += `   ℹ️  已存在: ${stats.exists}\n`;
                    if (stats.invalid > 0) {
                        message += `   ⚠️  无效数据: ${stats.invalid}\n`;
                    }
                    if (stats.error > 0) {
                        message += `   ❌ 失败: ${stats.error}\n`;
                    }
                    
                    alert(message);
                    
                    // 如果有新数据导入，则刷新页面数据
                    if (stats.success > 0) {
                        loadToday();
                    }
                } else {
                    alert('❌ 批量导入失败: ' + data.error);
                }
            })
            .catch(error => {
                alert('❌ 批量导入失败: ' + error);
            })
            .finally(() => {
                // 恢复按钮状态
                btn.disabled = false;
                btn.innerHTML = originalText;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            });
        }
        
        // 加载涨跌速数据
        function loadPriceSpeedData() {
            fetch('/api/price-speed/latest')
                .then(response => response.json())
                .then(response => {
                    if (response.success && response.data) {
                        const data = response.data;
                        
                        // 统计各级别数量
                        const upCount = data.filter(coin => 
                            coin.alert_level && coin.alert_level.includes('up') && coin.alert_level !== 'normal'
                        ).length;
                        
                        const downCount = data.filter(coin => 
                            coin.alert_level && coin.alert_level.includes('down') && coin.alert_level !== 'normal'
                        ).length;
                        
                        const normalCount = data.filter(coin => 
                            coin.alert_level === 'normal'
                        ).length;
                        
                        // 更新UI (已移除急涨速、急跌速、正常统计)
                    }
                })
                .catch(err => {
                    console.error('加载涨跌速数据失败:', err);
                    // 如果失败，显示默认值 (已移除急涨速、急跌速、正常统计)
                });
        }
        
        // 更新UI
        function updateUI(data) {
            document.getElementById('calcTime').textContent = data.snapshot_time;
            document.getElementById('rushUp').textContent = data.rush_up;
            document.getElementById('rushDown').textContent = data.rush_down;
            document.getElementById('roundRushUp').textContent = data.round_rush_up || data.rush_up;
            document.getElementById('roundRushDown').textContent = data.round_rush_down || data.rush_down;
            document.getElementById('countTimes').textContent = data.count;
            document.getElementById('countScore').textContent = data.count_score_display || '---';
            document.getElementById('status').textContent = data.status;
            document.getElementById('ratio').textContent = data.ratio;
            document.getElementById('diff').textContent = data.diff;
            document.getElementById('priceLowest').textContent = data.price_lowest || 0;
            document.getElementById('priceNewhigh').textContent = data.price_newhigh || 0;
            document.getElementById('rise24hCount').textContent = data.rise_24h_count || 0;
            document.getElementById('fall24hCount').textContent = data.fall_24h_count || 0;
            
            // 加载涨跌速数据
            loadPriceSpeedData();
            
            // 更新表格
            const tbody = document.getElementById('dataTableBody');
            if (data.coins && data.coins.length > 0) {
                let html = '';
                data.coins.forEach((coin, idx) => {
                    const changeClass = coin.change > 0 ? 'value-positive' : (coin.change < 0 ? 'value-negative' : 'value-neutral');
                    const change24Class = coin.change_24h > 0 ? 'value-positive' : (coin.change_24h < 0 ? 'value-negative' : 'value-neutral');
                    const priority = coin.priority || '未知';
                    const priorityClass = 'priority-' + priority.replace('等级', '');
                    
                    const rushUpTag = coin.rush_up > 0 ? '<span class="status-tag rise">' + coin.rush_up + '</span>' : coin.rush_up;
                    const rushDownTag = coin.rush_down > 0 ? '<span class="status-tag fall">' + coin.rush_down + '</span>' : coin.rush_down;
                    
                    html += '<tr>';
                    html += '<td class="' + priorityClass + '">' + priority + '</td>';
                    html += '<td>' + (idx + 1) + '</td>';
                    html += '<td class="coin-symbol">' + coin.symbol + '</td>';
                    html += '<td class="' + changeClass + '">' + coin.change.toFixed(2) + '</td>';
                    html += '<td>' + rushUpTag + '</td>';
                    html += '<td>' + rushDownTag + '</td>';
                    html += '<td>' + coin.update_time + '</td>';
                    html += '<td>' + coin.high_price.toFixed(2) + '</td>';
                    html += '<td>' + coin.high_time + '</td>';
                    html += '<td class="value-negative">' + coin.decline.toFixed(2) + '</td>';
                    html += '<td class="' + change24Class + '">' + coin.change_24h.toFixed(2) + '</td>';
                    html += '<td>' + coin.rank + '</td>';
                    html += '<td>' + coin.current_price.toFixed(4) + '</td>';
                    html += '<td>' + (coin.ratio1 || 'N/A') + '</td>';
                    html += '<td>' + (coin.ratio2 || 'N/A') + '</td>';
                    html += '</tr>';
                });
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<tr><td colspan="15" class="loading">暂无数据</td></tr>';
            }
        }
        
        // 加载图表数据
        // 当前页码（全局变量）
        let currentPage = 0;
        
        function loadChartData(page = 0) {
            // 加载指定页的历史数据点（12小时/页，显示所有数据点）
            currentPage = page;
            fetch(`/api/chart?page=${page}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(data.error);
                        return;
                    }
                    updateChart(data);
                    
                    // 更新分页信息
                    document.getElementById('chartPageInfo').textContent = 
                        `第${page + 1}/${data.total_pages}页`;
                    document.getElementById('chartTimeRange').textContent = 
                        `${data.time_range.start} - ${data.time_range.end}`;
                    
                    // 更新按钮状态
                    document.getElementById('btnPrevPage').disabled = !data.has_prev;
                    document.getElementById('btnNextPage').disabled = !data.has_next;
                })
                .catch(error => {
                    console.error('图表加载失败:', error);
                });
        }
        
        // 翻页按钮事件
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('btnPrevPage').addEventListener('click', function() {
                loadChartData(currentPage + 1);  // 上一页（更早的数据）
            });
            
            document.getElementById('btnNextPage').addEventListener('click', function() {
                loadChartData(currentPage - 1);  // 下一页（更新的数据）
            });
        });
        
        // 页面加载时自动加载最新数据
        // 加载时间轴数据 - 竖直布局
        function loadTimeline() {
            fetch('/api/timeline')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('timelineInfo').textContent = data.error;
                        return;
                    }
                    
                    document.getElementById('timelineInfo').textContent = 
                        `共 ${data.snapshots.length} 个数据点`;
                    
                    const pointsContainer = document.getElementById('timelinePoints');
                    pointsContainer.innerHTML = '';
                    
                    // 时间从上到下：最早的在上面，最新的在下面
                    data.snapshots.forEach((snapshot, index) => {
                        const point = document.createElement('div');
                        point.className = 'timeline-point';
                        point.setAttribute('data-time', snapshot.snapshot_time);
                        
                        // 最后一个（最新的）标记为激活
                        if (index === data.snapshots.length - 1) {
                            point.classList.add('active');
                        }
                        
                        const label = document.createElement('div');
                        label.className = 'timeline-label';
                        
                        // 时间显示
                        const timeSpan = document.createElement('div');
                        timeSpan.className = 'timeline-label-time';
                        timeSpan.textContent = snapshot.snapshot_time;
                        
                        // 统计信息显示 - 显示所有关键字段
                        const statsSpan = document.createElement('div');
                        statsSpan.className = 'timeline-label-stats';
                        
                        // 第一行：急涨、急跌、计次、得分
                        const line1 = `急涨:${snapshot.rush_up} 急跌:${snapshot.rush_down} 计次:${snapshot.count} ${snapshot.count_score_display || ''}`;
                        
                        // 第二行：状态、比值、差值
                        const line2 = `状态:${snapshot.status || ''} 比值:${snapshot.ratio || 0} 差值:${snapshot.diff}`;
                        
                        // 第三行：本轮、比价、24h
                        const line3 = `本轮急涨:${snapshot.round_rush_up || 0} 本轮急跌:${snapshot.round_rush_down || 0} 24h涨≥10%:${snapshot.rise_24h_count || 0} 24h跌≤-10%:${snapshot.fall_24h_count || 0}`;
                        
                        statsSpan.innerHTML = `
                            <div style="margin-bottom: 2px;">${line1}</div>
                            <div style="margin-bottom: 2px;">${line2}</div>
                            <div>${line3}</div>
                        `;
                        
                        label.appendChild(timeSpan);
                        label.appendChild(statsSpan);
                        point.appendChild(label);
                        
                        point.onclick = function() {
                            // 移除所有激活状态
                            document.querySelectorAll('.timeline-point').forEach(p => {
                                p.classList.remove('active');
                            });
                            // 激活当前点
                            this.classList.add('active');
                            // 加载数据
                            loadSnapshotData(snapshot.snapshot_time);
                        };
                        
                        pointsContainer.appendChild(point);
                    });
                })
                .catch(error => {
                    console.error('加载时间轴失败:', error);
                    document.getElementById('timelineInfo').textContent = '加载失败';
                });
        }
        
        // 加载指定快照的数据
        function loadSnapshotData(snapshotTime) {
            fetch('/api/query?time=' + encodeURIComponent(snapshotTime))
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    updateUI(data);
                    updateChart(data);
                    
                    // 更新时间轴激活状态
                    document.querySelectorAll('.timeline-point').forEach(point => {
                        point.classList.remove('active');
                    });
                    event.target.classList.add('active');
                })
                .catch(error => console.error('加载数据失败:', error));
        }
        
        window.onload = function() {
            loadLatest();
            loadTimeline();
        };
        
        // 响应式调整
        window.addEventListener('resize', function() {
            chart.resize();
        });
    </script>
</body>
</html>
"""

# API路由保持不变，使用之前的代码
@app.route('/')
def index():
    """首页 - 功能导航"""
    return render_template('index.html')

@app.route('/query')
def query_page():
    """历史数据查询页面"""
    return render_template_string(MAIN_HTML)

@app.route('/chart')
def chart_page():
    """趋势图表页面"""
    return render_template_string(MAIN_HTML)

@app.route('/timeline')
def timeline_page():
    """时间轴页面"""
    return render_template_string(MAIN_HTML)

@app.route('/status')
def status_page():
    """系统状态页面"""
    return render_template('status.html')

@app.route('/panic')
def panic_page():
    """恐慌清洗指数页面"""
    return render_template('panic_new.html')

@app.route('/api/panic/latest')
def api_panic_latest():
    """恐慌清洗指数最新数据API"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 使用新的 panic_wash_index 表
        cursor.execute('''
            SELECT record_time, panic_index, hour_24_people, total_position, 
                   hour_1_amount, hour_24_amount
            FROM panic_wash_index 
            ORDER BY record_time DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            panic_index_percentage = row[1]  # 百分比形式（如 8.67）
            # 如果是整数就不显示小数部分，否则保留2位小数
            panic_index = int(panic_index_percentage) if panic_index_percentage == int(panic_index_percentage) else round(panic_index_percentage, 2)
            
            people_wan = round(row[2] / 10000, 2)  # 人 -> 万人（去掉4个0）
            position_yi = round(row[3] / 100000000, 2)  # 美元 -> 亿美元（去掉8个0 = 除以1亿）
            hour_1_amount_usd = row[4]  # 1小时爆仓金额（美元）
            hour_24_amount_usd = row[5]  # 24小时爆仓金额（美元）
            
            # 单位转换：美元 -> 万美元
            hour_1_amount_wan = round(hour_1_amount_usd / 10000, 2)  # 美元 -> 万美元（去掉4个0）
            hour_24_amount_wan = round(hour_24_amount_usd / 10000, 2)  # 美元 -> 万美元（去掉4个0）
            
            # 根据恐慌指数确定等级（现在使用百分比形式判断：8.67% 在低恐慌范围）
            if panic_index_percentage < 5:
                panic_level = '低恐慌'
                level_color = 'green'
            elif panic_index_percentage < 10:
                panic_level = '中度恐慌'
                level_color = 'yellow'
            else:
                panic_level = '高度恐慌'
                level_color = 'red'
            
            return jsonify({
                'success': True,
                'data': {
                    'record_time': row[0],
                    'panic_index': panic_index,
                    'panic_level': panic_level,
                    'level_color': level_color,
                    'hour_24_people': people_wan,
                    'total_position': position_yi,
                    'hour_1_amount': hour_1_amount_wan,  # 返回万美元
                    'hour_24_amount': hour_24_amount_wan,  # 返回万美元
                    'market_zone': f'{people_wan}万人/{position_yi}亿美元'
                }
            })
        else:
            return jsonify({'success': False, 'error': '暂无数据'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """统计数据API - 包含本轮急涨急跌和恐慌清洗指数"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM crypto_snapshots")
        total_records = cursor.fetchone()[0]
        
        # 今日记录数
        today = datetime.now(BEIJING_TZ).date().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM crypto_snapshots WHERE snapshot_date = ?", (today,))
        today_records = cursor.fetchone()[0]
        
        # 数据天数
        cursor.execute("SELECT COUNT(DISTINCT snapshot_date) FROM crypto_snapshots")
        data_days = cursor.fetchone()[0]
        
        # 获取最新两条记录用于计算本轮差值
        cursor.execute("""
            SELECT snapshot_time, rush_up, rush_down, round_rush_up, round_rush_down
            FROM crypto_snapshots
            ORDER BY snapshot_date DESC, snapshot_time DESC
            LIMIT 2
        """)
        latest_records = cursor.fetchall()
        
        last_update_time = '-'
        current_round_rush_up = 0
        current_round_rush_down = 0
        
        if latest_records and len(latest_records) >= 1:
            # snapshot_time 格式: "2025-12-10 16:35:00", 提取时间部分 HH:MM
            time_str = latest_records[0][0]
            if time_str:
                # 如果包含日期，提取时间部分（格式：YYYY-MM-DD HH:MM:SS）
                if ' ' in time_str:
                    last_update_time = time_str.split(' ')[1][:5]  # 提取 HH:MM
                else:
                    # 如果只有时间（格式：HH:MM:SS）
                    last_update_time = time_str[:5]
            else:
                last_update_time = '-'
            current_rush_up = latest_records[0][1]
            current_rush_down = latest_records[0][2]
            
            if len(latest_records) >= 2:
                prev_rush_up = latest_records[1][1]
                prev_rush_down = latest_records[1][2]
                
                # 本轮急涨 = 当前急涨 - 上一轮急涨
                current_round_rush_up = current_rush_up - prev_rush_up
                # 本轮急跌 = 当前急跌 - 上一轮急跌
                current_round_rush_down = current_rush_down - prev_rush_down
        
        # 获取恐慌清洗指数（从新的独立采集表）
        cursor.execute("""
            SELECT panic_index, hour_24_people, total_position, record_time
            FROM panic_wash_index
            ORDER BY record_time DESC
            LIMIT 1
        """)
        panic_data = cursor.fetchone()
        
        panic_indicator = '-'
        panic_color = 'gray'
        panic_trend_rating = 0
        panic_market_zone = '-'
        panic_people_wan = 0
        panic_position_yi = 0
        
        if panic_data:
            panic_indicator = panic_data[0]  # 恐慌指数（百分比）
            panic_people_wan = round(panic_data[1] / 10000, 2)  # 爆仓人数（万人）
            panic_position_yi = round(panic_data[2] / 100000000, 2)  # 持仓量（亿美元）
            
            # 根据恐慌指数设置颜色（现在是百分比形式：如8.67%）
            if panic_indicator < 5:
                panic_color = '绿'  # 低恐慌（<5%）
            elif panic_indicator < 10:
                panic_color = '黄'  # 中恐慌（5-10%）
            else:
                panic_color = '红'  # 高恐慌（>10%）
            
            # 市场区间描述
            panic_market_zone = f"{panic_people_wan}万人/{panic_position_yi}亿美元"
        
        conn.close()
        
        return jsonify({
            'total_records': total_records,
            'today_records': today_records,
            'data_days': data_days,
            'last_update_time': last_update_time,
            'current_round_rush_up': current_round_rush_up,
            'current_round_rush_down': current_round_rush_down,
            'panic_indicator': panic_indicator,
            'panic_color': panic_color,
            'panic_trend_rating': panic_trend_rating,
            'panic_market_zone': panic_market_zone
        })
    except Exception as e:
        return jsonify({
            'total_records': 0,
            'today_records': 0,
            'data_days': 0,
            'last_update_time': '-',
            'current_round_rush_up': 0,
            'current_round_rush_down': 0,
            'panic_indicator': '-',
            'panic_color': 'gray',
            'panic_trend_rating': 0,
            'panic_market_zone': '-',
            'error': str(e)
        })

@app.route('/api/homepage/summary')
def api_homepage_summary():
    """首页聚合数据API - 一次返回所有首页需要的数据"""
    try:
        result = {
            'success': True,
            'timestamp': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 1. 统计栏数据（本轮急涨急跌和恐慌指数）
        cursor.execute("SELECT COUNT(*) FROM crypto_snapshots")
        total_records = cursor.fetchone()[0]
        
        today = datetime.now(BEIJING_TZ).date().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM crypto_snapshots WHERE snapshot_date = ?", (today,))
        today_records = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT snapshot_time, rush_up, rush_down
            FROM crypto_snapshots
            ORDER BY snapshot_date DESC, snapshot_time DESC
            LIMIT 2
        """)
        latest_records = cursor.fetchall()
        
        last_update_time = '-'
        current_round_rush_up = 0
        current_round_rush_down = 0
        
        if latest_records and len(latest_records) >= 1:
            time_str = latest_records[0][0]
            if time_str and ' ' in time_str:
                last_update_time = time_str.split(' ')[1][:5]
            current_rush_up = latest_records[0][1]
            current_rush_down = latest_records[0][2]
            
            if len(latest_records) >= 2:
                prev_rush_up = latest_records[1][1]
                prev_rush_down = latest_records[1][2]
                current_round_rush_up = current_rush_up - prev_rush_up
                current_round_rush_down = current_rush_down - prev_rush_down
        
        cursor.execute("""
            SELECT panic_index, hour_24_people, total_position
            FROM panic_wash_index
            ORDER BY record_time DESC
            LIMIT 1
        """)
        panic_data = cursor.fetchone()
        
        panic_indicator = '-'
        panic_color = 'gray'
        panic_market_zone = '-'
        
        if panic_data:
            panic_indicator = panic_data[0]
            panic_people_wan = round(panic_data[1] / 10000, 2)
            panic_position_yi = round(panic_data[2] / 100000000, 2)
            
            if panic_indicator < 5:
                panic_color = '绿'
            elif panic_indicator < 10:
                panic_color = '黄'
            else:
                panic_color = '红'
            
            panic_market_zone = f"{panic_people_wan}万人/{panic_position_yi}亿美元"
        
        result['stats'] = {
            'total_records': total_records,
            'today_records': today_records,
            'last_update_time': last_update_time,
            'current_round_rush_up': current_round_rush_up,
            'current_round_rush_down': current_round_rush_down,
            'panic_indicator': panic_indicator,
            'panic_color': panic_color,
            'panic_market_zone': panic_market_zone
        }
        
        # 2. 模块统计数据
        cursor.execute("SELECT MIN(snapshot_date), MAX(snapshot_date) FROM crypto_snapshots")
        date_range = cursor.fetchone()
        data_days = 0
        if date_range and date_range[0] and date_range[1]:
            data_days = (datetime.strptime(date_range[1], '%Y-%m-%d') - 
                        datetime.strptime(date_range[0], '%Y-%m-%d')).days + 1
        
        cursor.execute("SELECT MAX(snapshot_time) FROM crypto_snapshots")
        last_snapshot = cursor.fetchone()
        last_update = last_snapshot[0] if last_snapshot else '-'
        
        result['modules_stats'] = {
            'query_module': {
                'total_records': total_records,
                'data_days': data_days,
                'last_update': last_update
            }
        }
        
        # 3. 价格突破统计（创新高/创新低）
        cursor.execute("""
            SELECT event_type, COUNT(*) 
            FROM price_breakthrough_events 
            WHERE DATE(event_time) = ?
            GROUP BY event_type
        """, (today,))
        breakthrough_today = dict(cursor.fetchall())
        
        result['price_breakthrough'] = {
            'today': {
                'new_high': breakthrough_today.get('new_high', 0),
                'new_low': breakthrough_today.get('new_low', 0)
            }
        }
        
        # 4. V1V2成交系统数据（从实际API获取或占位）
        # 暂时使用占位数据，后续可以调用原有的v1v2 API
        result['v1v2_system'] = {
            'v1_count': 0,
            'v2_count': 0,
            'update_time': last_update
        }
        
        # 5. 支撑压力线系统数据
        cursor.execute("""
            SELECT 
                symbol, 
                alert_scenario_1, alert_scenario_2, alert_scenario_3, alert_scenario_4,
                position_s2_r1, position_s1_r2, position_s1_r1
            FROM support_resistance_levels
            WHERE record_time = (SELECT MAX(record_time) FROM support_resistance_levels)
        """)
        sr_data = cursor.fetchall()
        
        scenario1_coins = []
        scenario2_coins = []
        scenario3_coins = []
        scenario4_coins = []
        
        for row in sr_data:
            symbol, s1, s2, s3, s4, pos_s2_r1, pos_s1_r2, pos_s1_r1 = row
            coin_symbol = symbol.replace('USDT', '')
            
            if s1:
                scenario1_coins.append({'symbol': coin_symbol, 'position': pos_s2_r1})
            if s2:
                scenario2_coins.append({'symbol': coin_symbol, 'position': pos_s1_r2})
            if s3:
                scenario3_coins.append({'symbol': coin_symbol, 'position': pos_s1_r2})
            if s4:
                scenario4_coins.append({'symbol': coin_symbol, 'position': pos_s1_r1})
        
        result['support_resistance'] = {
            'total_count': len(sr_data),
            'scenario1_coins': scenario1_coins,
            'scenario2_coins': scenario2_coins,
            'scenario3_coins': scenario3_coins,
            'scenario4_coins': scenario4_coins,
            'update_time': last_update
        }
        
        # 6. 交易信号系统数据
        # 简化版本，返回基本计数
        result['trading_signals'] = {
            'buy_point_1_count': 0,
            'buy_point_2_count': 0,
            'total_coins': 27,
            'update_time': last_update
        }
        
        # 7. 1分钟涨跌速数据（占位，需要实际数据源）
        result['price_speed'] = {
            'up_count': 0,
            'down_count': 0,
            'update_time': last_update
        }
        
        # 8. 监控状态
        cursor.execute("""
            SELECT snapshot_time 
            FROM crypto_snapshots 
            ORDER BY snapshot_date DESC, snapshot_time DESC 
            LIMIT 1
        """)
        latest_snapshot_row = cursor.fetchone()
        latest_snapshot_time = latest_snapshot_row[0] if latest_snapshot_row else None
        
        need_collection = False
        minutes_since_last = None
        
        if latest_snapshot_time:
            latest_dt = datetime.strptime(latest_snapshot_time, '%Y-%m-%d %H:%M:%S')
            latest_dt = BEIJING_TZ.localize(latest_dt)
            now = datetime.now(BEIJING_TZ)
            minutes_since_last = (now - latest_dt).total_seconds() / 60
            
            if minutes_since_last > 15:
                need_collection = True
        
        result['monitor_status'] = {
            'need_collection': need_collection,
            'latest_snapshot': latest_snapshot_time,
            'minutes_since_last': round(minutes_since_last, 1) if minutes_since_last else None
        }
        
        # 9. Google Drive检测器状态（占位）
        result['gdrive_detector'] = {
            'detector_running': False,
            'file_timestamp': None,
            'delay_minutes': None,
            'latest_file': None
        }
        
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        })

@app.route('/api/query')
def api_query():
    """查询API"""
    query_time = request.args.get('time', '')
    if not query_time:
        return jsonify({'error': '请提供查询时间'})
    
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                snapshot_date, snapshot_time, rush_up, rush_down, diff, count, ratio, status,
                round_rush_up, round_rush_down, price_lowest, price_newhigh,
                count_score_display, count_score_type, rise_24h_count, fall_24h_count
            FROM crypto_snapshots
            WHERE snapshot_time LIKE ?
            ORDER BY snapshot_date DESC, snapshot_time DESC
            LIMIT 1
        """, (f"{query_time}%",))
        
        snapshot = cursor.fetchone()
        
        if not snapshot:
            conn.close()
            return jsonify({'error': f'未找到 {query_time} 的数据'})
        
        (snapshot_date, snapshot_time, rush_up, rush_down, diff, count, ratio, status,
         round_rush_up, round_rush_down, price_lowest, price_newhigh,
         count_score_display, count_score_type, rise_24h_count, fall_24h_count) = snapshot
        
        # snapshot_time已经是完整的日期时间，无需拼接
        # 格式: '2025-12-09 22:40:00'
        
        cursor.execute("""
            SELECT 
                symbol, change, rush_up, rush_down, update_time,
                high_price, high_time, decline, change_24h, rank,
                current_price, priority_level, ratio1, ratio2
            FROM crypto_coin_data
            WHERE snapshot_time = ?
            ORDER BY index_order ASC
        """, (snapshot_time,))
        
        coins = []
        for row in cursor.fetchall():
            coins.append({
                'symbol': row[0],
                'change': row[1],
                'rush_up': row[2],
                'rush_down': row[3],
                'update_time': row[4],
                'high_price': row[5],
                'high_time': row[6],
                'decline': row[7],
                'change_24h': row[8],
                'rank': row[9],
                'current_price': row[10],
                'priority': row[11],
                'ratio1': row[12],
                'ratio2': row[13]
            })
        
        conn.close()
        
        return jsonify({
            'snapshot_time': snapshot_time,
            'rush_up': rush_up,
            'rush_down': rush_down,
            'diff': diff,
            'count': count,
            'ratio': ratio,
            'status': status,
            'round_rush_up': round_rush_up,
            'round_rush_down': round_rush_down,
            'price_lowest': price_lowest,
            'price_newhigh': price_newhigh,
            'count_score_display': count_score_display,
            'count_score_type': count_score_type,
            'rise_24h_count': rise_24h_count,
            'fall_24h_count': fall_24h_count,
            'coins': coins
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/latest')
def api_latest():
    """获取最新数据API"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                snapshot_date, snapshot_time, rush_up, rush_down, diff, count, ratio, status,
                round_rush_up, round_rush_down, price_lowest, price_newhigh,
                count_score_display, count_score_type, rise_24h_count, fall_24h_count
            FROM crypto_snapshots
            ORDER BY snapshot_date DESC, snapshot_time DESC
            LIMIT 1
        """)
        
        snapshot = cursor.fetchone()
        
        if not snapshot:
            conn.close()
            return jsonify({'error': '数据库中暂无数据'})
        
        (snapshot_date, snapshot_time, rush_up, rush_down, diff, count, ratio, status,
         round_rush_up, round_rush_down, price_lowest, price_newhigh,
         count_score_display, count_score_type, rise_24h_count, fall_24h_count) = snapshot
        
        # snapshot_time已经是完整的日期时间，无需拼接
        # 格式: '2025-12-09 22:40:00'
        
        cursor.execute("""
            SELECT 
                symbol, change, rush_up, rush_down, update_time,
                high_price, high_time, decline, change_24h, rank,
                current_price, priority_level, ratio1, ratio2
            FROM crypto_coin_data
            WHERE snapshot_time = ?
            ORDER BY index_order ASC
        """, (snapshot_time,))
        
        coins = []
        for row in cursor.fetchall():
            coins.append({
                'symbol': row[0],
                'change': row[1],
                'rush_up': row[2],
                'rush_down': row[3],
                'update_time': row[4],
                'high_price': row[5],
                'high_time': row[6],
                'decline': row[7],
                'change_24h': row[8],
                'rank': row[9],
                'current_price': row[10],
                'priority': row[11],
                'ratio1': row[12],
                'ratio2': row[13]
            })
        
        conn.close()
        
        return jsonify({
            'snapshot_time': snapshot_time,
            'rush_up': rush_up,
            'rush_down': rush_down,
            'diff': diff,
            'count': count,
            'ratio': ratio,
            'status': status,
            'round_rush_up': round_rush_up,
            'round_rush_down': round_rush_down,
            'price_lowest': price_lowest,
            'price_newhigh': price_newhigh,
            'count_score_display': count_score_display,
            'count_score_type': count_score_type,
            'rise_24h_count': rise_24h_count,
            'fall_24h_count': fall_24h_count,
            'coins': coins
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chart')
def api_chart():
    """图表数据API - 支持分页的12小时趋势图数据（显示所有数据点）"""
    try:
        from datetime import datetime, timedelta
        
        # 获取分页参数
        page = request.args.get('page', '0')  # 默认第0页（最新）
        page = int(page)
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取所有历史数据点，按时间升序排列
        cursor.execute("""
            SELECT 
                snapshot_time, rush_up, rush_down, diff, count
            FROM crypto_snapshots
            ORDER BY snapshot_date ASC, snapshot_time ASC
        """)
        
        all_data = cursor.fetchall()
        conn.close()
        
        if not all_data:
            return jsonify({'error': '无数据'})
        
        # 转换为datetime对象
        all_points = []
        for row in all_data:
            dt = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            all_points.append({
                'time': dt,
                'formatted_time': dt.strftime('%m-%d %H:%M'),
                'rush_up': row[1],
                'rush_down': row[2],
                'diff': row[3],
                'count': row[4]
            })
        
        # 计算总页数（每页12小时）
        earliest = all_points[0]['time']
        latest = all_points[-1]['time']
        total_hours = (latest - earliest).total_seconds() / 3600
        total_pages = max(1, int(total_hours / 12) + 1)
        
        # 确保page在有效范围内
        if page < 0:
            page = 0
        if page >= total_pages:
            page = total_pages - 1
        
        # 计算当前页的时间范围（从最新往前推）
        # page=0 是最新的12小时，page=1 是之前的12小时，以此类推
        page_end_time = latest - timedelta(hours=12 * page)
        page_start_time = page_end_time - timedelta(hours=12)
        
        # 筛选当前页的数据点
        page_points = [
            p for p in all_points 
            if page_start_time <= p['time'] <= page_end_time
        ]
        
        # 如果当前页没有数据，返回空数组
        if not page_points:
            return jsonify({
                'times': [],
                'rush_up': [],
                'rush_down': [],
                'diff': [],
                'count': [],
                'page': page,
                'total_pages': total_pages,
                'has_prev': page < total_pages - 1,
                'has_next': page > 0,
                'time_range': {
                    'start': page_start_time.strftime('%Y-%m-%d %H:%M'),
                    'end': page_end_time.strftime('%Y-%m-%d %H:%M')
                }
            })
        
        # 提取数据
        times = [p['formatted_time'] for p in page_points]
        rush_up = [p['rush_up'] for p in page_points]
        rush_down = [p['rush_down'] for p in page_points]
        diff = [p['diff'] for p in page_points]
        count = [p['count'] for p in page_points]
        
        return jsonify({
            'times': times,
            'rush_up': rush_up,
            'rush_down': rush_down,
            'diff': diff,
            'count': count,
            'page': page,
            'total_pages': total_pages,
            'has_prev': page < total_pages - 1,  # 有上一页（更早的数据）
            'has_next': page > 0,  # 有下一页（更新的数据）
            'time_range': {
                'start': page_start_time.strftime('%Y-%m-%d %H:%M'),
                'end': page_end_time.strftime('%Y-%m-%d %H:%M')
            },
            'data_count': len(page_points)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/timeline')
def api_timeline():
    """获取所有历史数据点API - 返回完整的统计数据"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 查询所有字段 - 倒序排列（时间晚的在上，时间早的在下）
        cursor.execute("""
            SELECT 
                id, snapshot_time, snapshot_date,
                rush_up, rush_down, diff, count, ratio, status,
                round_rush_up, round_rush_down,
                price_lowest, price_newhigh, ratio_diff,
                init_rush_up, init_rush_down,
                count_score_display, count_score_type,
                rise_24h_count, fall_24h_count,
                green_count, percentage, filename
            FROM crypto_snapshots
            ORDER BY snapshot_date DESC, snapshot_time DESC
        """)
        
        snapshots = []
        for row in cursor.fetchall():
            snapshots.append({
                'id': row[0],
                'snapshot_time': row[1],
                'snapshot_date': row[2],
                # 主要统计
                'rush_up': row[3],
                'rush_down': row[4],
                'diff': row[5],
                'count': row[6],
                'ratio': row[7],
                'status': row[8],
                # 本轮数据
                'round_rush_up': row[9],
                'round_rush_down': row[10],
                # 比价数据
                'price_lowest': row[11],
                'price_newhigh': row[12],
                'ratio_diff': row[13],
                # 初始数据
                'init_rush_up': row[14],
                'init_rush_down': row[15],
                # 计次得分
                'count_score_display': row[16],
                'count_score_type': row[17],
                # 24小时涨跌
                'rise_24h_count': row[18],
                'fall_24h_count': row[19],
                # 其他
                'green_count': row[20],
                'percentage': row[21],
                'filename': row[22]
            })
        
        conn.close()
        
        return jsonify({
            'snapshots': snapshots,
            'total': len(snapshots)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

# ==================== 交易信号监控 API ====================

@app.route('/signals')
def signals_page():
    """交易信号监控页面"""
    return render_template('signals.html')

@app.route('/popup-demo')
def popup_demo():
    """弹窗效果演示页面"""
    with open('popup_demo.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/signals/stats')
def api_signals_stats():
    """获取信号统计数据"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新记录
        cursor.execute('''
            SELECT record_time, long_signals, short_signals, 
                   total_signals, long_ratio, short_ratio
            FROM trading_signals
            ORDER BY record_time DESC
            LIMIT 1
        ''')
        latest = cursor.fetchone()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM trading_signals')
        total_records = cursor.fetchone()[0]
        
        conn.close()
        
        if latest:
            return jsonify({
                'success': True,
                'data': {
                    'latest_time': latest[0],
                    'latest_long': latest[1],
                    'latest_short': latest[2],
                    'latest_total': latest[3],
                    'long_ratio': latest[4],
                    'short_ratio': latest[5],
                    'total_records': total_records
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': '暂无数据'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/signals/chart')
def api_signals_chart():
    """获取图表数据（支持分页和时间范围）"""
    try:
        page = int(request.args.get('page', 0))
        time_range = request.args.get('range', '12h')
        
        # 计算时间范围对应的数据点数量（每3分钟一个点）
        range_minutes = {
            '1h': 60,
            '6h': 360,
            '12h': 720,
            '24h': 1440
        }
        
        minutes = range_minutes.get(time_range, 720)
        points_per_page = minutes // 3  # 每3分钟一个数据点
        offset = page * points_per_page
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM trading_signals')
        total = cursor.fetchone()[0]
        total_pages = (total + points_per_page - 1) // points_per_page
        
        # 获取分页数据
        cursor.execute('''
            SELECT record_time, long_signals, short_signals, total_signals
            FROM trading_signals
            ORDER BY record_time DESC
            LIMIT ? OFFSET ?
        ''', (points_per_page, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 反转顺序，使时间从早到晚
        rows.reverse()
        
        data = [{
            'time': row[0].split(' ')[1][:5],  # 只取时分
            'long_signals': row[1],
            'short_signals': row[2],
            'total_signals': row[3]
        } for row in rows]
        
        return jsonify({
            'success': True,
            'data': data,
            'page': page,
            'total_pages': total_pages,
            'range': time_range
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/signals/history')
def api_signals_history():
    """获取历史记录列表"""
    try:
        limit = int(request.args.get('limit', 50))
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT record_time, long_signals, short_signals,
                   total_signals, long_ratio, short_ratio
            FROM trading_signals
            ORDER BY record_time DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = [{
            'record_time': row[0],
            'long_signals': row[1],
            'short_signals': row[2],
            'total_signals': row[3],
            'long_ratio': row[4],
            'short_ratio': row[5]
        } for row in rows]
        
        return jsonify({
            'success': True,
            'data': data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/liquidation/30days')
def api_liquidation_30days():
    """30日爆仓数据API"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, long_amount, short_amount, total_amount, updated_at
            FROM liquidation_30days
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'date': row[0],
                'long_amount': round(row[1] / 100000000, 2),  # 转换为亿
                'short_amount': round(row[2] / 100000000, 2),
                'total_amount': round(row[3] / 100000000, 2),
                'updated_at': row[4]
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/panic/history')
def api_panic_history():
    """恐慌清洗指数历史数据API（支持时间查询）"""
    try:
        limit = int(request.args.get('limit', 50))
        query_time = request.args.get('time', None)  # 可选的时间查询参数
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        if query_time:
            # 时间范围查询：查询指定时间前后的数据
            half_limit = limit // 2
            
            # 先查询指定时间之前的记录（过滤掉异常数据）
            cursor.execute('''
                SELECT record_time, panic_index, hour_24_people, total_position, hour_1_amount, hour_24_amount
                FROM panic_wash_index
                WHERE record_time <= ?
                  AND panic_index > 0 
                  AND hour_24_people > 0 
                  AND total_position > 1000000000
                  AND hour_1_amount > 100000
                  AND hour_24_amount > 1000000
                ORDER BY record_time DESC
                LIMIT ?
            ''', (query_time, half_limit))
            before_rows = cursor.fetchall()
            
            # 再查询指定时间之后的记录（过滤掉异常数据）
            cursor.execute('''
                SELECT record_time, panic_index, hour_24_people, total_position, hour_1_amount, hour_24_amount
                FROM panic_wash_index
                WHERE record_time > ?
                  AND panic_index > 0 
                  AND hour_24_people > 0 
                  AND total_position > 1000000000
                  AND hour_1_amount > 100000
                  AND hour_24_amount > 1000000
                ORDER BY record_time ASC
                LIMIT ?
            ''', (query_time, half_limit))
            after_rows = cursor.fetchall()
            
            # 合并结果并按时间倒序排列（最新的在前面）
            rows = list(before_rows) + list(reversed(after_rows))
        else:
            # 默认查询：最新的N条记录（过滤掉异常数据，最新的在前面）
            # total_position > 1000000000 表示大于10亿（原始值以美元计）
            # hour_1_amount > 100000 表示大于10万（原始值以美元计）
            # hour_24_amount > 1000000 表示大于100万（原始值以美元计）
            cursor.execute('''
                SELECT record_time, panic_index, hour_24_people, total_position, hour_1_amount, hour_24_amount
                FROM panic_wash_index
                WHERE panic_index > 0 
                  AND hour_24_people > 0 
                  AND total_position > 1000000000
                  AND hour_1_amount > 100000
                  AND hour_24_amount > 1000000
                ORDER BY record_time DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
        
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'record_time': row[0],
                'panic_index': row[1],
                'hour_24_people': round(row[2] / 10000, 2),  # 转换为万人
                'total_position': round(row[3] / 100000000, 2),  # 转换为亿美元
                'hour_1_amount': round(row[4] / 10000, 2),  # 转换为万美元
                'hour_24_amount': round(row[5] / 10000, 2)  # 转换为万美元
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'query_time': query_time  # 返回查询的时间
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/modules/stats')
def api_modules_stats():
    """获取所有模块的统计信息"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 1. 历史数据查询模块统计
        cursor.execute("SELECT COUNT(*) FROM crypto_snapshots")
        query_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT snapshot_date) FROM crypto_snapshots")
        query_days = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(snapshot_time) FROM crypto_snapshots")
        query_last_time = cursor.fetchone()[0] or '-'
        if query_last_time != '-':
            # 处理时间格式：可能是 "HH:MM:SS" 或 "YYYY-MM-DD HH:MM:SS"
            if ' ' in query_last_time:
                query_last_time = query_last_time.split(' ')[1][:5]  # 取HH:MM
            else:
                query_last_time = query_last_time[:5]  # 已经是HH:MM:SS，取HH:MM
        
        # 2. 交易信号监控模块统计
        cursor.execute("SELECT COUNT(*) FROM trading_signals")
        signal_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT record_date) FROM trading_signals")
        signal_days = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(record_time) FROM trading_signals")
        signal_last_time = cursor.fetchone()[0] or '-'
        if signal_last_time != '-':
            # 处理时间格式：可能是 "HH:MM:SS" 或 "YYYY-MM-DD HH:MM:SS"
            if ' ' in signal_last_time:
                signal_last_time = signal_last_time.split(' ')[1][:5]  # 取HH:MM
            else:
                signal_last_time = signal_last_time[:5]  # 已经是HH:MM:SS，取HH:MM
        
        # 3. 恐慌清洗指数模块统计
        cursor.execute("SELECT COUNT(*) FROM panic_wash_index")
        panic_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT DATE(record_time)) FROM panic_wash_index")
        panic_days = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(record_time) FROM panic_wash_index")
        panic_last_time = cursor.fetchone()[0] or '-'
        if panic_last_time != '-':
            # 处理时间格式：可能是 "HH:MM:SS" 或 "YYYY-MM-DD HH:MM:SS"
            if ' ' in panic_last_time:
                panic_last_time = panic_last_time.split(' ')[1][:5]  # 取HH:MM
            else:
                panic_last_time = panic_last_time[:5]  # 已经是HH:MM:SS，取HH:MM
        
        conn.close()
        
        return jsonify({
            'success': True,
            'query_module': {
                'total_records': query_total,
                'data_days': query_days,
                'last_update': query_last_time
            },
            'signal_module': {
                'total_records': signal_total,
                'data_days': signal_days,
                'last_update': signal_last_time
            },
            'panic_module': {
                'total_records': panic_total,
                'data_days': panic_days,
                'last_update': panic_last_time
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/price-comparison')
def price_comparison_page():
    """比价系统页面"""
    return render_template('price_comparison.html')

@app.route('/api/price-comparison/list')
def api_price_comparison_list():
    """获取比价系统所有币种数据 - 按用户指定顺序，使用北京时间"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, highest_price, highest_count, lowest_price, lowest_count,
                   highest_ratio, lowest_ratio, last_update_time
            FROM price_baseline
            ORDER BY display_order
        ''')
        
        rows = cursor.fetchall()
        data = []
        for row in rows:
            # 从 symbol 提取币种名称 (例如: BTC-USDT-SWAP -> BTC)
            symbol = row[0]
            coin_name = symbol.split('-')[0] if symbol else ''
            
            # 转换时间为北京时间格式
            update_time = row[7]
            if update_time:
                try:
                    # 如果数据库时间是UTC，需要转换
                    from datetime import datetime
                    import pytz
                    dt = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
                    # 假设数据库存的是北京时间，直接使用
                    beijing_time = update_time
                except:
                    beijing_time = update_time
            else:
                beijing_time = None
            
            data.append({
                'coin_name': coin_name,
                'symbol': symbol,
                'highest_price': row[1],
                'highest_count': row[2],
                'lowest_price': row[3],
                'lowest_count': row[4],
                'highest_ratio': row[5],
                'lowest_ratio': row[6],
                'last_update_time': beijing_time
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/price-comparison/update', methods=['POST'])
def api_price_comparison_update():
    """更新币种价格并进行比价判断
    
    逻辑:
    - 新价格 > 最高价: 更新最高价，最高计次清零
    - 新价格 < 最低价: 更新最低价，最低计次清零  
    - 最低价 <= 新价格 <= 最高价: 两个计次都+1
    """
    try:
        data = request.get_json()
        coin_name = data.get('coin_name')
        new_price = float(data.get('price'))
        
        if not coin_name or new_price is None:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: coin_name 或 price'
            })
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取当前币种的最高价和最低价
        cursor.execute('''
            SELECT highest_price, highest_count, lowest_price, lowest_count
            FROM price_baseline
            WHERE symbol = ?
        ''', (coin_name,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'币种 {coin_name} 不存在'
            })
        
        highest_price, highest_count, lowest_price, lowest_count = row
        old_highest_price = highest_price
        old_lowest_price = lowest_price
        
        # 价格比较逻辑
        action = ''
        if new_price > highest_price:
            # 新价格创新高
            old_highest_price = highest_price
            highest_price = new_price
            highest_count = 0
            action = 'new_high'
        elif new_price < lowest_price:
            # 新价格创新低
            old_lowest_price = lowest_price
            lowest_price = new_price
            lowest_count = 0
            action = 'new_low'
        else:
            # 价格在区间内
            highest_count += 1
            lowest_count += 1
            action = 'in_range'
        
        # 计算占比
        # 最高价占比 = (当前价 / 最高价) × 100
        highest_ratio = round((new_price / highest_price) * 100, 2) if highest_price > 0 else 0
        # 最低价占比 = (当前价 / 最低价) × 100
        lowest_ratio = round((new_price / lowest_price) * 100, 2) if lowest_price > 0 else 0
        
        # 更新数据库 - 使用北京时间
        from datetime import datetime
        import pytz
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE price_baseline
            SET highest_price = ?,
                highest_count = ?,
                lowest_price = ?,
                lowest_count = ?,
                highest_ratio = ?,
                lowest_ratio = ?,
                last_update_time = ?
            WHERE symbol = ?
        ''', (highest_price, highest_count, lowest_price, lowest_count, 
              highest_ratio, lowest_ratio, beijing_time, coin_name))
        
        # 如果发生创新高或创新低，记录事件
        if action in ['new_high', 'new_low']:
            cursor.execute('''
                INSERT INTO price_breakthrough_events 
                (symbol, event_type, price, event_time)
                VALUES (?, ?, ?, ?)
            ''', (coin_name, action, new_price, beijing_time))
            
            # 更新统计表缓存（清除今天的缓存，下次查询时会重新计算）
            today_date = beijing_tz.localize(datetime.now()).strftime('%Y-%m-%d')
            cursor.execute('''
                DELETE FROM price_comparison_stats
                WHERE stat_date = ?
            ''', (today_date,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'action': action,
            'data': {
                'coin_name': coin_name,
                'new_price': new_price,
                'highest_price': highest_price,
                'highest_count': highest_count,
                'lowest_price': lowest_price,
                'lowest_count': lowest_count
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/price-comparison/breakthrough-stats')
def api_breakthrough_stats():
    """获取创新高/低统计
    
    返回:
    - 当天创新高次数、创新低次数
    - 3天内创新高次数、创新低次数
    - 7天内创新高次数、创新低次数
    
    优先从统计表读取，如果没有则实时计算并保存
    """
    try:
        from datetime import datetime, timedelta
        import pytz
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        today_date = now.strftime('%Y-%m-%d')
        
        # 先尝试从统计表读取今天的数据
        cursor.execute('''
            SELECT today_new_high, today_new_low, 
                   three_days_new_high, three_days_new_low,
                   seven_days_new_high, seven_days_new_low
            FROM price_comparison_stats
            WHERE stat_date = ?
        ''', (today_date,))
        
        cached_stats = cursor.fetchone()
        
        # 如果缓存存在且不超过5分钟，直接返回
        if cached_stats:
            conn.close()
            return jsonify({
                'success': True,
                'data': {
                    'today': {
                        'new_high': cached_stats[0],
                        'new_low': cached_stats[1]
                    },
                    'three_days': {
                        'new_high': cached_stats[2],
                        'new_low': cached_stats[3]
                    },
                    'seven_days': {
                        'new_high': cached_stats[4],
                        'new_low': cached_stats[5]
                    }
                },
                'from_cache': True
            })
        
        # 如果没有缓存，实时计算
        # 计算时间边界
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        three_days_ago = now - timedelta(days=3)
        seven_days_ago = now - timedelta(days=7)
        
        # 转换为字符串格式
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
        three_days_ago_str = three_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        
        # 当天统计
        cursor.execute('''
            SELECT event_type, COUNT(*) 
            FROM price_breakthrough_events 
            WHERE event_time >= ?
            GROUP BY event_type
        ''', (today_start_str,))
        today_stats = dict(cursor.fetchall())
        
        # 3天统计
        cursor.execute('''
            SELECT event_type, COUNT(*) 
            FROM price_breakthrough_events 
            WHERE event_time >= ?
            GROUP BY event_type
        ''', (three_days_ago_str,))
        three_days_stats = dict(cursor.fetchall())
        
        # 7天统计
        cursor.execute('''
            SELECT event_type, COUNT(*) 
            FROM price_breakthrough_events 
            WHERE event_time >= ?
            GROUP BY event_type
        ''', (seven_days_ago_str,))
        seven_days_stats = dict(cursor.fetchall())
        
        # 保存统计结果到数据库
        cursor.execute('''
            INSERT OR REPLACE INTO price_comparison_stats
            (stat_date, today_new_high, today_new_low, 
             three_days_new_high, three_days_new_low,
             seven_days_new_high, seven_days_new_low, record_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            today_date,
            today_stats.get('new_high', 0),
            today_stats.get('new_low', 0),
            three_days_stats.get('new_high', 0),
            three_days_stats.get('new_low', 0),
            seven_days_stats.get('new_high', 0),
            seven_days_stats.get('new_low', 0),
            now.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'new_high': today_stats.get('new_high', 0),
                    'new_low': today_stats.get('new_low', 0)
                },
                'three_days': {
                    'new_high': three_days_stats.get('new_high', 0),
                    'new_low': three_days_stats.get('new_low', 0)
                },
                'seven_days': {
                    'new_high': seven_days_stats.get('new_high', 0),
                    'new_low': seven_days_stats.get('new_low', 0)
                }
            },
            'from_cache': False
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/price-comparison/breakthrough-logs')
def api_breakthrough_logs():
    """获取创新高/低详细日志
    
    参数:
    - limit: 返回记录数量，默认50
    - days: 查询最近N天的记录，默认7天
    - coin: 筛选特定币种
    - type: 筛选类型 (new_high/new_low)
    
    返回:
    - 时间、币名、事件类型(创新高/创新低)、价格、之前极值价格
    """
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # 获取参数
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 7, type=int)
        coin_filter = request.args.get('coin', None)
        type_filter = request.args.get('type', None)
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
            SELECT symbol, event_type, price, event_time
            FROM price_breakthrough_events
            WHERE 1=1
        '''
        params = []
        
        # 时间过滤
        if days > 0:
            beijing_tz = pytz.timezone('Asia/Shanghai')
            now = datetime.now(beijing_tz)
            cutoff_time = now - timedelta(days=days)
            cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
            query += ' AND event_time >= ?'
            params.append(cutoff_str)
        
        # 币种过滤
        if coin_filter:
            query += ' AND symbol = ?'
            params.append(coin_filter)
        
        # 类型过滤
        if type_filter in ['new_high', 'new_low']:
            query += ' AND event_type = ?'
            params.append(type_filter)
        
        query += ' ORDER BY event_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # 格式化结果
        logs = []
        for row in results:
            symbol, event_type, price, event_time = row
            # 从 symbol 提取币种名称
            coin_name = symbol.split('-')[0] if symbol else ''
            logs.append({
                'coin_name': coin_name,
                'symbol': symbol,
                'event_type': event_type,
                'event_label': '创新高' if event_type == 'new_high' else '创新低',
                'price': price,
                'event_time': event_time
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': logs,
            'count': len(logs),
            'filters': {
                'days': days,
                'coin': coin_filter,
                'type': type_filter,
                'limit': limit
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/price-comparison/update-ratios')
def api_update_price_ratios():
    """批量更新所有币种的价格占比
    
    从最新快照数据获取当前价格，计算并更新占比:
    - 最高价占比 = (当前价 / 最高价) × 100%
    - 最低价占比 = (当前价 / 最低价) × 100%
    """
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新快照时间
        cursor.execute('SELECT MAX(snapshot_time) FROM crypto_coin_data')
        latest_time = cursor.fetchone()[0]
        
        if not latest_time:
            return jsonify({
                'success': False,
                'error': '没有找到快照数据'
            })
        
        # 获取最新快照的所有币种价格
        cursor.execute('''
            SELECT symbol, current_price
            FROM crypto_coin_data
            WHERE snapshot_time = ?
        ''', (latest_time,))
        
        current_prices = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 获取所有币种的最高价和最低价
        cursor.execute('''
            SELECT symbol, highest_price, lowest_price
            FROM price_baseline
        ''')
        
        from datetime import datetime
        import pytz
        beijing_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        updated_count = 0
        update_details = []
        
        for row in cursor.fetchall():
            coin_name, highest_price, lowest_price = row
            
            # 查找当前价格
            current_price = current_prices.get(coin_name)
            
            if current_price is not None and current_price > 0:
                # 计算占比
                highest_ratio = round((current_price / highest_price) * 100, 2) if highest_price > 0 else 0
                lowest_ratio = round((current_price / lowest_price) * 100, 2) if lowest_price > 0 else 0
                
                # 更新数据库
                cursor.execute('''
                    UPDATE price_baseline
                    SET highest_ratio = ?,
                        lowest_ratio = ?,
                        last_update_time = ?
                    WHERE symbol = ?
                ''', (highest_ratio, lowest_ratio, current_time, coin_name))
                
                updated_count += 1
                update_details.append({
                    'coin_name': coin_name,
                    'current_price': current_price,
                    'highest_ratio': highest_ratio,
                    'lowest_ratio': lowest_ratio
                })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {updated_count} 个币种的占比',
            'snapshot_time': latest_time,
            'updated_count': updated_count,
            'details': update_details[:10]  # 只返回前10个作为示例
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/monitor/data-collection')
def api_monitor_data_collection():
    """监控数据采集状态"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        # 获取最新快照时间
        cursor.execute('SELECT MAX(snapshot_time) FROM crypto_snapshots')
        latest_snapshot = cursor.fetchone()[0]
        
        if not latest_snapshot:
            return jsonify({
                'success': False,
                'error': '数据库中没有任何快照数据',
                'status': 'no_data'
            })
        
        # 计算时间差
        latest_time = datetime.strptime(latest_snapshot, '%Y-%m-%d %H:%M:%S')
        latest_time = beijing_tz.localize(latest_time)
        time_diff_minutes = (now - latest_time).total_seconds() / 60
        
        # 获取今天的采集次数
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT COUNT(*) FROM crypto_snapshots 
            WHERE snapshot_time >= ?
        ''', (today_start_str,))
        today_count = cursor.fetchone()[0]
        
        conn.close()
        
        # 判断状态
        status = 'normal'
        message = '数据采集正常'
        alert_level = 'success'
        
        if time_diff_minutes > 20:
            status = 'critical'
            message = f'严重: 已经 {time_diff_minutes:.1f} 分钟没有新数据'
            alert_level = 'danger'
        elif time_diff_minutes > 15:
            status = 'warning'
            message = f'警告: 已经 {time_diff_minutes:.1f} 分钟没有新数据'
            alert_level = 'warning'
        
        # 计算预期采集次数（每10分钟一次）
        expected_count = int((now.hour * 60 + now.minute) / 10)
        
        return jsonify({
            'success': True,
            'status': status,
            'message': message,
            'alert_level': alert_level,
            'data': {
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'latest_snapshot': latest_snapshot,
                'time_diff_minutes': round(time_diff_minutes, 1),
                'today_count': today_count,
                'expected_count': expected_count,
                'collection_rate': round((today_count / expected_count * 100) if expected_count > 0 else 0, 1)
            }
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/monitor')
def monitor_page():
    """数据采集监控页面（增强版）- 支持执行日志、开关控制、刷新间隔"""
    return render_template('unified_monitor_enhanced.html')

@app.route('/monitor-old')
def monitor_page_old():
    """原始监控页面（旧版）"""
    return render_template('monitor.html')

@app.route('/star-system')
def star_system_page():
    """星星系统页面"""
    return render_template('star_system.html')

@app.route('/api/star-system/data')
def api_star_system_data():
    """获取星星系统所有指标数据"""
    try:
        import sys
        sys.path.insert(0, '/home/user/webapp')
        from star_system import calculate_star_system
        from datetime import datetime, timedelta
        import pytz
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        beijing_tz = pytz.timezone('Asia/Shanghai')
        
        # 获取最新快照数据
        cursor.execute('''
            SELECT rush_up, rush_down, diff, count, snapshot_time
            FROM crypto_snapshots
            ORDER BY snapshot_date DESC, snapshot_time DESC
            LIMIT 1
        ''')
        snapshot = cursor.fetchone()
        
        if not snapshot:
            return jsonify({'success': False, 'error': '暂无快照数据'})
        
        rush_up, rush_down, diff, count, snapshot_time = snapshot
        
        # 确保数值不为None
        rush_up = rush_up if rush_up is not None else 0
        rush_down = rush_down if rush_down is not None else 0
        diff = diff if diff is not None else 0
        count = count if count is not None else 0
        
        # 获取全网持仓量（从恐慌清洗指数表）
        cursor.execute('''
            SELECT total_position
            FROM panic_wash_index
            ORDER BY record_time DESC
            LIMIT 1
        ''')
        holdings_row = cursor.fetchone()
        holdings = holdings_row[0] if holdings_row and holdings_row[0] is not None else 10000000000  # 默认100亿（元）
        
        # 获取做多做空信号（从交易信号表）
        cursor.execute('''
            SELECT long_signals, short_signals
            FROM trading_signals
            ORDER BY record_time DESC
            LIMIT 1
        ''')
        signals_row = cursor.fetchone()
        long_signals = signals_row[0] if signals_row and signals_row[0] is not None else 0
        short_signals = signals_row[1] if signals_row and signals_row[1] is not None else 0
        
        # 获取今日创新高新低次数
        today_start = datetime.now(beijing_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT event_type, COUNT(*) 
            FROM price_breakthrough_events 
            WHERE event_time >= ?
            GROUP BY event_type
        ''', (today_start_str,))
        today_breakthrough = dict(cursor.fetchall())
        new_high_today = today_breakthrough.get('new_high', 0)
        new_low_today = today_breakthrough.get('new_low', 0)
        
        # 获取币种统计数据（从最新快照的详细数据）
        cursor.execute('''
            SELECT symbol, rush_up, rush_down, priority_level
            FROM crypto_coin_data
            WHERE snapshot_time = ?
        ''', (snapshot_time,))
        coin_data = cursor.fetchall()
        
        # 统计特殊情况并记录具体币种
        only_rush_up_coins = [c[0] for c in coin_data if c[1] > 0 and c[2] == 0]
        only_rush_up_count = len(only_rush_up_coins)
        
        rush_up_gt_down_coins = [c[0] for c in coin_data if c[1] > c[2]]
        rush_up_gt_down_count = len(rush_up_gt_down_coins)
        
        only_rush_down_coins = [c[0] for c in coin_data if c[1] == 0 and c[2] > 0]
        only_rush_down_count = len(only_rush_down_coins)
        
        rush_down_gt_up_coins = [c[0] for c in coin_data if c[2] > c[1]]
        rush_down_gt_up_count = len(rush_down_gt_up_coins)
        
        # 优先级≥4 means 等级1,2,3,4 (priority_level values: '等级1', '等级2', etc.)
        priority_high_coins = [c[0] for c in coin_data if c[3] in ['等级1', '等级2', '等级3', '等级4']]
        priority_high_count = len(priority_high_coins)
        
        # ========== 新增功能3: 位置系统平均位置（在conn.close()之前查询） ==========
        try:
            # 计算48小时前的北京时间
            hours_ago_48 = datetime.now(beijing_tz) - timedelta(hours=48)
            hours_ago_48_str = hours_ago_48.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT 
                    AVG(position_4h) as avg_4h,
                    AVG(position_12h) as avg_12h,
                    AVG(position_24h) as avg_24h,
                    AVG(position_48h) as avg_48h
                FROM position_system
                WHERE record_time >= ?
            """, (hours_ago_48_str,))
            pos_row = cursor.fetchone()
            
            position_avg = {
                '4h': round(pos_row[0], 2) if pos_row and pos_row[0] else 0,
                '12h': round(pos_row[1], 2) if pos_row and pos_row[1] else 0,
                '24h': round(pos_row[2], 2) if pos_row and pos_row[2] else 0,
                '48h': round(pos_row[3], 2) if pos_row and pos_row[3] else 0
            }
        except Exception as e:
            position_avg = {'4h': 0, '12h': 0, '24h': 0, '48h': 0}
            print(f"位置系统平均位置查询错误: {e}")
        
        # ========== 新增功能4: 创新高/创新低统计（在conn.close()之前查询） ==========
        try:
            # 当天统计（今天0点到现在）
            today_start = datetime.now(beijing_tz).replace(hour=0, minute=0, second=0, microsecond=0)
            today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
            
            # 3天统计
            three_days_ago = datetime.now(beijing_tz) - timedelta(days=3)
            three_days_ago_str = three_days_ago.strftime('%Y-%m-%d %H:%M:%S')
            
            # 7天统计
            seven_days_ago = datetime.now(beijing_tz) - timedelta(days=7)
            seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')
            
            # 查询当天创新高/创新低
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN event_type = 'new_high' THEN 1 ELSE 0 END) as today_high,
                    SUM(CASE WHEN event_type = 'new_low' THEN 1 ELSE 0 END) as today_low
                FROM price_breakthrough_events
                WHERE event_time >= ?
            """, (today_start_str,))
            today_bt = cursor.fetchone()
            
            # 查询3天创新高/创新低
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN event_type = 'new_high' THEN 1 ELSE 0 END) as three_days_high,
                    SUM(CASE WHEN event_type = 'new_low' THEN 1 ELSE 0 END) as three_days_low
                FROM price_breakthrough_events
                WHERE event_time >= ?
            """, (three_days_ago_str,))
            three_days_bt = cursor.fetchone()
            
            # 查询7天创新高/创新低
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN event_type = 'new_high' THEN 1 ELSE 0 END) as seven_days_high,
                    SUM(CASE WHEN event_type = 'new_low' THEN 1 ELSE 0 END) as seven_days_low
                FROM price_breakthrough_events
                WHERE event_time >= ?
            """, (seven_days_ago_str,))
            seven_days_bt = cursor.fetchone()
            
            breakthrough_stats = {
                'today': {
                    'new_high': today_bt[0] if today_bt and today_bt[0] else 0,
                    'new_low': today_bt[1] if today_bt and today_bt[1] else 0
                },
                'three_days': {
                    'new_high': three_days_bt[0] if three_days_bt and three_days_bt[0] else 0,
                    'new_low': three_days_bt[1] if three_days_bt and three_days_bt[1] else 0
                },
                'seven_days': {
                    'new_high': seven_days_bt[0] if seven_days_bt and seven_days_bt[0] else 0,
                    'new_low': seven_days_bt[1] if seven_days_bt and seven_days_bt[1] else 0
                }
            }
        except Exception as e:
            breakthrough_stats = {
                'today': {'new_high': 0, 'new_low': 0},
                'three_days': {'new_high': 0, 'new_low': 0},
                'seven_days': {'new_high': 0, 'new_low': 0}
            }
            print(f"创新高/创新低统计查询错误: {e}")
        
        conn.close()
        
        # 准备数据给星星系统计算
        data = {
            'rush_up': rush_up,
            'rush_down': rush_down,
            'diff': diff,
            'holdings': holdings,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'only_rush_up_count': only_rush_up_count,
            'rush_up_gt_down_count': rush_up_gt_down_count,
            'priority_high_count': priority_high_count,
            'only_rush_down_count': only_rush_down_count,
            'rush_down_gt_up_count': rush_down_gt_up_count,
            'new_low_today': new_low_today,
            'new_high_today': new_high_today,
            'count': count,
            'snapshot_time': snapshot_time
        }
        
        # 计算星星系统
        results = calculate_star_system(data)
        
        # 保存到历史记录表（每次调用API时保存）
        try:
            import json as json_lib
            cursor.execute('''
                INSERT INTO star_system_history 
                (timestamp, total_stars, solid_stars, hollow_stars, solid_percentage, hollow_percentage, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_time,
                results.get('total_stars', 0),
                results.get('solid_stars', 0),
                results.get('hollow_stars', 0),
                results.get('solid_percentage', 0),
                results.get('hollow_percentage', 0),
                json_lib.dumps(results, ensure_ascii=False)
            ))
            conn.commit()
        except Exception as save_err:
            print(f"保存历史数据失败: {save_err}")
        
        # 添加币种列表到结果中
        coin_lists = {
            'only_rush_up_coins': only_rush_up_coins,
            'rush_up_gt_down_coins': rush_up_gt_down_coins,
            'priority_high_coins': priority_high_coins,
            'only_rush_down_coins': only_rush_down_coins,
            'rush_down_gt_up_coins': rush_down_gt_up_coins
        }
        
        # ========== 新增功能1: V1/V2币种统计 ==========
        try:
            conn_v1v2 = sqlite3.connect('v1v2_data.db')
            cursor_v1v2 = conn_v1v2.cursor()
            
            coins_list = ['BTC', 'ETH', 'XRP', 'SOL', 'BNB', 'LTC', 'DOGE', 'SUI', 'TRX', 'TON', 
                         'ETC', 'BCH', 'HBAR', 'XLM', 'FIL', 'ADA', 'LINK', 'CRO', 'DOT', 'UNI',
                         'NEAR', 'APT', 'CFX', 'CRV', 'STX', 'LDO', 'TAO', 'AAVE']
            
            v1_coins_list = []
            v2_coins_list = []
            
            for coin in coins_list:
                try:
                    cursor_v1v2.execute(f"""
                        SELECT level FROM volume_{coin.lower()}
                        ORDER BY id DESC LIMIT 1
                    """)
                    row = cursor_v1v2.fetchone()
                    if row and row[0] == 'V1':
                        v1_coins_list.append(coin)
                    elif row and row[0] == 'V2':
                        v2_coins_list.append(coin)
                except:
                    pass
            
            conn_v1v2.close()
        except:
            v1_coins_list = []
            v2_coins_list = []
        
        # ========== 新增功能2: 1分钟涨跌速预警统计 ==========
        try:
            conn_ps = sqlite3.connect('price_speed_data.db')
            cursor_ps = conn_ps.cursor()
            
            # 获取各类型预警的币种
            cursor_ps.execute("""
                SELECT alert_type, symbol
                FROM latest_price_speed
                WHERE alert_type != 'NORMAL'
            """)
            
            alert_coins = {
                'super_strong_up': [],
                'very_strong_up': [],
                'strong_up': [],
                'general_up': [],
                'super_strong_down': [],
                'very_strong_down': [],
                'strong_down': [],
                'general_down': []
            }
            
            for alert_type, symbol in cursor_ps.fetchall():
                if alert_type == 'SUPER_STRONG_UP':
                    alert_coins['super_strong_up'].append(symbol)
                elif alert_type == 'VERY_STRONG_UP':
                    alert_coins['very_strong_up'].append(symbol)
                elif alert_type == 'STRONG_UP':
                    alert_coins['strong_up'].append(symbol)
                elif alert_type == 'GENERAL_UP':
                    alert_coins['general_up'].append(symbol)
                elif alert_type == 'SUPER_STRONG_DOWN':
                    alert_coins['super_strong_down'].append(symbol)
                elif alert_type == 'VERY_STRONG_DOWN':
                    alert_coins['very_strong_down'].append(symbol)
                elif alert_type == 'STRONG_DOWN':
                    alert_coins['strong_down'].append(symbol)
                elif alert_type == 'GENERAL_DOWN':
                    alert_coins['general_down'].append(symbol)
            
            conn_ps.close()
        except:
            alert_coins = {
                'super_strong_up': [],
                'very_strong_up': [],
                'strong_up': [],
                'general_up': [],
                'super_strong_down': [],
                'very_strong_down': [],
                'strong_down': [],
                'general_down': []
            }
        
        return jsonify({
            'success': True,
            'data': results,
            'raw_data': data,
            'coin_lists': coin_lists,
            'update_time': snapshot_time,
            # 新增数据
            'v1v2_data': {
                'v1_coins': v1_coins_list,
                'v1_count': len(v1_coins_list),
                'v2_coins': v2_coins_list,
                'v2_count': len(v2_coins_list)
            },
            'price_speed_alerts': {
                'up': {
                    'super_strong': {'count': len(alert_coins['super_strong_up']), 'coins': alert_coins['super_strong_up']},
                    'very_strong': {'count': len(alert_coins['very_strong_up']), 'coins': alert_coins['very_strong_up']},
                    'strong': {'count': len(alert_coins['strong_up']), 'coins': alert_coins['strong_up']},
                    'general': {'count': len(alert_coins['general_up']), 'coins': alert_coins['general_up']}
                },
                'down': {
                    'super_strong': {'count': len(alert_coins['super_strong_down']), 'coins': alert_coins['super_strong_down']},
                    'very_strong': {'count': len(alert_coins['very_strong_down']), 'coins': alert_coins['very_strong_down']},
                    'strong': {'count': len(alert_coins['strong_down']), 'coins': alert_coins['strong_down']},
                    'general': {'count': len(alert_coins['general_down']), 'coins': alert_coins['general_down']}
                }
            },
            'position_avg': position_avg,
            'breakthrough_stats': breakthrough_stats
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# ==================== 星星系统历史数据 API ====================
@app.route('/api/star-system/history')
def api_star_system_history():
    """获取星星系统历史数据"""
    try:
        date = request.args.get('date')  # 格式: YYYY-MM-DD
        limit = int(request.args.get('limit', 100))
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        if date:
            # 查询指定日期的数据
            start_time = f"{date} 00:00:00"
            end_time = f"{date} 23:59:59"
            cursor.execute('''
                SELECT id, timestamp, total_stars, solid_stars, hollow_stars, 
                       solid_percentage, hollow_percentage, raw_data
                FROM star_system_history
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (start_time, end_time, limit))
        else:
            # 查询最近的记录
            cursor.execute('''
                SELECT id, timestamp, total_stars, solid_stars, hollow_stars, 
                       solid_percentage, hollow_percentage, raw_data
                FROM star_system_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        
        history_data = []
        for row in rows:
            try:
                import json as json_lib
                raw_data = json_lib.loads(row[7]) if row[7] else {}
            except:
                raw_data = {}
            
            history_data.append({
                'id': row[0],
                'timestamp': row[1],
                'total_stars': row[2],
                'solid_stars': row[3],
                'hollow_stars': row[4],
                'solid_percentage': row[5],
                'hollow_percentage': row[6],
                'details': raw_data
            })
        
        # 获取可用日期列表
        cursor.execute('''
            SELECT DISTINCT DATE(timestamp) as date
            FROM star_system_history
            ORDER BY date DESC
            LIMIT 30
        ''')
        available_dates = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': history_data,
            'available_dates': available_dates,
            'total_records': len(history_data)
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# ==================== 数据采集监控 API ====================
@app.route('/api/monitor/status')
def api_monitor_status():
    """获取数据采集监控状态"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'monitor_data_collection.py', 'status'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=10
        )
        status = json.loads(result.stdout)
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/monitor/history')
def api_monitor_history():
    """获取采集历史"""
    import subprocess
    try:
        hours = request.args.get('hours', '2')
        result = subprocess.run(
            ['python3', 'monitor_data_collection.py', 'history', hours],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=10
        )
        history = json.loads(result.stdout)
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/monitor/trigger', methods=['POST'])
def api_monitor_trigger():
    """手动触发数据采集"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'monitor_data_collection.py', 'force'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        collection_result = json.loads(result.stdout) if result.stdout else {}
        return jsonify({
            'success': result.returncode == 0,
            'result': collection_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/monitor/check', methods=['POST'])
def api_monitor_check():
    """检查并自动恢复数据采集"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'monitor_data_collection.py', 'check'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        check_result = json.loads(result.stdout) if result.stdout else {}
        return jsonify({
            'success': True,
            'result': check_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ==================== 多模块监控 API ====================
@app.route('/api/monitor/all-modules')
def api_monitor_all_modules():
    """获取所有模块监控状态"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'multi_module_monitor.py', 'status'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=10
        )
        # 从stdout提取JSON部分（跳过前面的文本输出）
        output = result.stdout
        # 找到JSON开始的位置
        json_start = output.find('{')
        if json_start >= 0:
            json_str = output[json_start:]
            statuses = json.loads(json_str)
            return jsonify({
                'success': True,
                'modules': statuses
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No JSON output found'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/monitor/check-all', methods=['POST'])
def api_monitor_check_all():
    """检查并自动恢复所有模块"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'multi_module_monitor.py', 'check', '--silent'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时（多个模块可能需要更长时间）
        )
        check_result = json.loads(result.stdout) if result.stdout else {}
        return jsonify({
            'success': True,
            'result': check_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/monitor/force-update/<module_key>', methods=['POST'])
def api_monitor_force_update(module_key):
    """强制更新指定模块"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', 'multi_module_monitor.py', 'force', module_key],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        update_result = json.loads(result.stdout) if result.stdout else {}
        return jsonify({
            'success': result.returncode == 0,
            'result': update_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ==================== 得分系统 API ====================
from score_calculator import ScoreCalculator

@app.route('/control-center')
def control_center_page():
    """深度图得分页面（控制中心）"""
    return render_template('control_center.html')

@app.route('/depth-score')
def depth_score_page():
    """深度图得分页面"""
    return render_template('depth_score.html')

@app.route('/depth-chart')
def depth_chart_page():
    """深度图可视化页面"""
    return render_template('depth_chart.html')

@app.route('/score-overview')
def score_overview_page():
    """平均分页面"""
    return render_template('score_overview.html')

@app.route('/crypto-index')
def crypto_index_page():
    """OKEX加密指数页面"""
    return render_template('crypto_index.html')

@app.route('/api/depth-scores')
def api_depth_scores():
    """获取深度得分数据"""
    try:
        timeframe = int(request.args.get('timeframe', 24))
        limit = int(request.args.get('limit', 50))
        
        calculator = ScoreCalculator()
        scores = calculator.calculate_all_coins_depth_scores(timeframe, limit)
        
        # 计算平均分
        avg_score = sum(s['score'] for s in scores) / len(scores) if scores else 0
        
        return jsonify({
            'success': True,
            'data': {
                'scores': scores,
                'total_coins': len(scores),
                'average_score': round(avg_score, 2),
                'timeframe': f'{timeframe}h'
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/depth-chart-data')
def api_depth_chart_data():
    """获取深度图表数据"""
    try:
        timeframe = int(request.args.get('timeframe', 24))
        top_n = int(request.args.get('top_n', 20))
        
        calculator = ScoreCalculator()
        chart_data = calculator.get_depth_chart_data(timeframe, top_n)
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/market-average-score')
def api_market_average_score():
    """获取市场平均得分"""
    try:
        timeframe = int(request.args.get('timeframe', 24))
        
        calculator = ScoreCalculator()
        market_score = calculator.calculate_average_market_score(timeframe)
        
        return jsonify({
            'success': True,
            'data': market_score
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/okex-crypto-index')
def api_okex_crypto_index():
    """获取OKEX加密货币指数"""
    try:
        calculator = ScoreCalculator()
        index_data = calculator.calculate_okex_crypto_index()
        
        return jsonify({
            'success': True,
            'data': index_data
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# ============================================================================
# OKEX加密指数页面专用API端点
# ============================================================================

@app.route('/api/index/start', methods=['POST'])
def api_index_start():
    """启动指数监控"""
    return jsonify({
        'success': True,
        'message': '指数监控已启动'
    })

@app.route('/api/index/current')
def api_index_current():
    """获取当前指数值 - 基于27币种加权指数"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新的K线数据
        cursor.execute('''
            SELECT timestamp, index_value, open_price, high_price, low_price, close_price
            FROM crypto_index_klines
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        
        # 获取有多少个币种有有效的基准价格
        cursor.execute('SELECT COUNT(*) FROM crypto_index_base_prices WHERE base_price > 0')
        valid_components = cursor.fetchone()[0]
        
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'message': '暂无指数数据，请等待数据采集'
            })
        
        current_value = row[1]
        base_value = 1000.00
        change = current_value - base_value
        change_percent = (change / base_value) * 100
        
        # 获取BTC的4个周期平均位置数据
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT position_4h, position_12h, position_24h, position_48h
            FROM position_system
            WHERE symbol = 'BTC-USDT-SWAP'
            ORDER BY record_time DESC
            LIMIT 1
        ''')
        position_row = cursor.fetchone()
        conn.close()
        
        # 准备周期位置数据
        period_positions = {}
        if position_row:
            period_positions = {
                'position_4h': round(position_row[0], 2) if position_row[0] else None,
                'position_12h': round(position_row[1], 2) if position_row[1] else None,
                'position_24h': round(position_row[2], 2) if position_row[2] else None,
                'position_48h': round(position_row[3], 2) if position_row[3] else None
            }
        
        return jsonify({
            'success': True,
            'data': {
                'value': current_value,
                'base_value': base_value,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'valid_components': valid_components,
                'timestamp': row[0],
                'open': row[2],
                'high': row[3],
                'low': row[4],
                'close': row[5],
                'period_positions': period_positions
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'获取指数失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/index/components')
def api_index_components():
    """获取成分详情 - 27币种权重明细"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取所有币种的基准价格和权重
        cursor.execute('''
            SELECT coin_id, base_price, weight
            FROM crypto_index_base_prices
            ORDER BY weight DESC, coin_id
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # 币种名称映射
        coin_name_map = {
            'bitcoin': 'BTC', 'ethereum': 'ETH', 'ripple': 'XRP',
            'binancecoin': 'BNB', 'solana': 'SOL', 'litecoin': 'LTC',
            'dogecoin': 'DOGE', 'sui': 'SUI', 'tron': 'TRX',
            'the-open-network': 'TON', 'ethereum-classic': 'ETC',
            'bitcoin-cash': 'BCH', 'hedera-hashgraph': 'HBAR',
            'stellar': 'XLM', 'filecoin': 'FIL', 'chainlink': 'LINK',
            'crypto-com-chain': 'CRO', 'polkadot': 'DOT', 'aave': 'AAVE',
            'uniswap': 'UNI', 'near': 'NEAR', 'aptos': 'APT',
            'conflux-token': 'CFX', 'curve-dao-token': 'CRV',
            'stacks': 'STX', 'lido-dao': 'LDO', 'bittensor': 'TAO'
        }
        
        # 获取当前价格（从CoinGecko）- 简化版，仅用基准价格模拟
        import requests
        try:
            coin_ids = ','.join([r[0] for r in rows])
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': coin_ids, 'vs_currencies': 'usd'},
                timeout=5
            )
            current_prices = response.json() if response.status_code == 200 else {}
        except:
            current_prices = {}
        
        # 构建成分数据（以对象形式返回，key为币种symbol）
        components = {}
        for row in rows:
            coin_id = row[0]
            symbol = coin_name_map.get(coin_id, coin_id.upper())
            base_price = row[1]
            weight = row[2]
            
            # 获取当前价格
            current_price = current_prices.get(coin_id, {}).get('usd', base_price)
            price_change = ((current_price - base_price) / base_price * 100) if base_price > 0 else 0
            weighted_contribution = price_change * weight
            
            components[symbol] = {
                'name': symbol,
                'coin_id': coin_id,
                'price': current_price,
                'base_price': base_price,
                'weight': weight,
                'weight_percent': f"{weight*100:.2f}%",
                'change_percent': round(price_change, 2),
                'weighted_contribution': round(weighted_contribution, 3)
            }
        
        return jsonify({
            'success': True,
            'total_coins': len(components),
            'data': components
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'获取成分失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/test-refresh')
def test_refresh():
    """测试刷新页面 - 用于验证缓存问题"""
    return render_template('test_refresh.html')

@app.route('/test-btc-eth')
def test_btc_eth():
    """测试BTC和ETH数据显示"""
    return render_template('test_btc_eth.html')

@app.route('/api/index/history')
def api_index_history():
    """获取历史数据 - 基于K线数据，支持分页（12小时一页）"""
    try:
        page = int(request.args.get('page', 1))  # 当前页，默认第1页
        hours_per_page = 12  # 每页12小时
        records_per_hour = 60  # 每小时60条（1分钟K线）
        page_size = hours_per_page * records_per_hour  # 每页720条
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取总记录数
        cursor.execute('SELECT COUNT(*) FROM crypto_index_klines')
        total_records = cursor.fetchone()[0]
        
        # 计算总页数
        total_pages = (total_records + page_size - 1) // page_size
        
        # 确保页码有效
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        # 计算偏移量（从最新数据开始倒数）
        offset = (page - 1) * page_size
        
        # 获取当前页的K线数据
        cursor.execute('''
            SELECT timestamp, index_value, close_price
            FROM crypto_index_klines
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (page_size, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({
                'success': False,
                'message': '暂无历史数据'
            })
        
        history = []
        base_value = 1000.00
        for row in rows:
            index_value = row[1]
            change_percent = ((index_value - base_value) / base_value * 100)
            history.append({
                'time': row[0],
                'value': index_value,
                'close': row[2],
                'change_percent': round(change_percent, 2)
            })
        
        history.reverse()  # 时间正序
        
        return jsonify({
            'success': True,
            'total': len(history),
            'total_records': total_records,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
            'data': history
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/index/klines')
def api_index_klines():
    """获取K线数据 - 5分钟K线"""
    try:
        limit = int(request.args.get('limit', 100))
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最近的K线数据
        cursor.execute('''
            SELECT timestamp, open_price, high_price, low_price, close_price, index_value
            FROM crypto_index_klines
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({
                'success': False,
                'message': '暂无K线数据，请等待数据采集'
            })
        
        klines = []
        for row in rows:
            klines.append({
                'timestamp': row[0],
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'value': row[5]
            })
        
        klines.reverse()  # 时间正序
        
        return jsonify({
            'success': True,
            'total': len(klines),
            'interval': '5m',
            'data': klines
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'获取K线失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

# ==================== 位置系统 API ====================

@app.route('/position-system')
def position_system():
    """位置系统页面"""
    return render_template('position_system.html')

@app.route('/api/position/latest')
def api_position_latest():
    """获取最新位置数据"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新的记录时间
        cursor.execute('SELECT MAX(record_time) FROM position_system')
        latest_time = cursor.fetchone()[0]
        
        if not latest_time:
            return jsonify({
                'success': False,
                'message': '暂无数据'
            })
        
        # 获取该时间的所有币种数据
        cursor.execute('''
            SELECT symbol, current_price,
                   position_4h, position_12h, position_24h, position_48h,
                   high_4h, low_4h, high_12h, low_12h, high_24h, low_24h, high_48h, low_48h
            FROM position_system
            WHERE record_time = ?
            ORDER BY symbol
        ''', (latest_time,))
        
        rows = cursor.fetchall()
        
        # 构造返回数据
        data_list = []
        symbol_set = set()
        for row in rows:
            symbol_set.add(row[0])
            data_list.append({
                'symbol': row[0],
                'current_price': row[1],
                'position_4h': row[2],
                'position_12h': row[3],
                'position_24h': row[4],
                'position_48h': row[5],
                'high_4h': row[6],
                'low_4h': row[7],
                'high_12h': row[8],
                'low_12h': row[9],
                'high_24h': row[10],
                'low_24h': row[11],
                'high_48h': row[12],
                'low_48h': row[13]
            })
        
        # 检查BTC和ETH是否存在，如果不存在则从最近记录中补充
        missing_coins = []
        if 'BTC-USDT-SWAP' not in symbol_set:
            missing_coins.append('BTC-USDT-SWAP')
        if 'ETH-USDT-SWAP' not in symbol_set:
            missing_coins.append('ETH-USDT-SWAP')
        
        if missing_coins:
            for coin in missing_coins:
                cursor.execute('''
                    SELECT symbol, current_price,
                           position_4h, position_12h, position_24h, position_48h,
                           high_4h, low_4h, high_12h, low_12h, high_24h, low_24h, high_48h, low_48h
                    FROM position_system
                    WHERE symbol = ?
                    ORDER BY record_time DESC
                    LIMIT 1
                ''', (coin,))
                coin_row = cursor.fetchone()
                if coin_row:
                    data_list.append({
                        'symbol': coin_row[0],
                        'current_price': coin_row[1],
                        'position_4h': coin_row[2],
                        'position_12h': coin_row[3],
                        'position_24h': coin_row[4],
                        'position_48h': coin_row[5],
                        'high_4h': coin_row[6],
                        'low_4h': coin_row[7],
                        'high_12h': coin_row[8],
                        'low_12h': coin_row[9],
                        'high_24h': coin_row[10],
                        'low_24h': coin_row[11],
                        'high_48h': coin_row[12],
                        'low_48h': coin_row[13]
                    })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'record_time': latest_time,
            'total_count': len(data_list),
            'data': data_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        })

@app.route('/api/position/summary')
def api_position_summary():
    """获取位置统计摘要"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新的记录时间
        cursor.execute('SELECT MAX(record_time) FROM position_system')
        latest_time = cursor.fetchone()[0]
        
        if not latest_time:
            return jsonify({
                'success': False,
                'message': '暂无数据'
            })
        
        # 统计各周期的平均位置
        cursor.execute('''
            SELECT 
                AVG(position_4h) as avg_4h,
                AVG(position_12h) as avg_12h,
                AVG(position_24h) as avg_24h,
                AVG(position_48h) as avg_48h,
                COUNT(*) as total_count
            FROM position_system
            WHERE record_time = ?
        ''', (latest_time,))
        
        row = cursor.fetchone()
        
        # 统计各区间的币种数量（以24h为例）
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN position_24h >= 80 THEN 1 ELSE 0 END) as high_zone,
                SUM(CASE WHEN position_24h >= 50 AND position_24h < 80 THEN 1 ELSE 0 END) as mid_high_zone,
                SUM(CASE WHEN position_24h >= 20 AND position_24h < 50 THEN 1 ELSE 0 END) as mid_low_zone,
                SUM(CASE WHEN position_24h < 20 THEN 1 ELSE 0 END) as low_zone
            FROM position_system
            WHERE record_time = ?
        ''', (latest_time,))
        
        zone_counts = cursor.fetchone()
        
        # 新增：统计各周期>=95%的币种数量
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN position_4h >= 95 THEN 1 ELSE 0 END) as count_4h_ge95,
                SUM(CASE WHEN position_12h >= 95 THEN 1 ELSE 0 END) as count_12h_ge95,
                SUM(CASE WHEN position_24h >= 95 THEN 1 ELSE 0 END) as count_24h_ge95,
                SUM(CASE WHEN position_48h >= 95 THEN 1 ELSE 0 END) as count_48h_ge95
            FROM position_system
            WHERE record_time = ?
        ''', (latest_time,))
        
        ge95_counts = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'record_time': latest_time,
            'averages': {
                '4h': round(row[0], 2) if row[0] else 0,
                '12h': round(row[1], 2) if row[1] else 0,
                '24h': round(row[2], 2) if row[2] else 0,
                '48h': round(row[3], 2) if row[3] else 0
            },
            'total_count': row[4],
            'zone_distribution_24h': {
                'high': zone_counts[0] or 0,      # 80-100%
                'mid_high': zone_counts[1] or 0,  # 50-80%
                'mid_low': zone_counts[2] or 0,   # 20-50%
                'low': zone_counts[3] or 0        # 0-20%
            },
            'high_position_counts': {
                '4h': ge95_counts[0] or 0,   # 4小时>=95%
                '12h': ge95_counts[1] or 0,  # 12小时>=95%
                '24h': ge95_counts[2] or 0,  # 24小时>=95%
                '48h': ge95_counts[3] or 0   # 48小时>=95%
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        })

@app.route('/api/position/history/<symbol>')
def api_position_history(symbol):
    """获取指定币种的历史位置数据"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最近24小时的数据
        cursor.execute('''
            SELECT record_time, current_price,
                   position_4h, position_12h, position_24h, position_48h
            FROM position_system
            WHERE symbol = ?
            ORDER BY record_time DESC
            LIMIT 288
        ''', (symbol,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'time': row[0],
                'price': row[1],
                '4h': row[2],
                '12h': row[3],
                '24h': row[4],
                '48h': row[5]
            })
        
        history.reverse()  # 时间正序
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}'
        })

@app.route('/api/position/stats/latest')
def api_position_stats_latest():
    """获取最新的位置统计数据（低于1%的币种数量）"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新的统计数据
        cursor.execute('''
            SELECT record_time, count_below_1_4h, count_below_1_12h, 
                   count_below_1_24h, count_below_1_48h, total_coins
            FROM position_system_stats
            ORDER BY record_time DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'message': '暂无统计数据'
            })
        
        return jsonify({
            'success': True,
            'record_time': row[0],
            'stats': {
                '4h': {'below_1': row[1], 'total': row[5]},
                '12h': {'below_1': row[2], 'total': row[5]},
                '24h': {'below_1': row[3], 'total': row[5]},
                '48h': {'below_1': row[4], 'total': row[5]}
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        })

@app.route('/api/position/stats/history')
def api_position_stats_history():
    """获取统计数据历史记录"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', default=100, type=int)
        start_time = request.args.get('start_time', default=None, type=str)
        end_time = request.args.get('end_time', default=None, type=str)
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 构建查询条件
        query = '''
            SELECT record_time, count_below_1_4h, count_below_1_12h, 
                   count_below_1_24h, count_below_1_48h, total_coins
            FROM position_system_stats
            WHERE 1=1
        '''
        params = []
        
        if start_time:
            query += ' AND record_time >= ?'
            params.append(start_time)
        
        if end_time:
            query += ' AND record_time <= ?'
            params.append(end_time)
        
        query += ' ORDER BY record_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'time': row[0],
                '4h': {'below_1': row[1], 'total': row[5]},
                '12h': {'below_1': row[2], 'total': row[5]},
                '24h': {'below_1': row[3], 'total': row[5]},
                '48h': {'below_1': row[4], 'total': row[5]}
            })
        
        history.reverse()  # 时间正序
        
        return jsonify({
            'success': True,
            'count': len(history),
            'data': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史统计失败: {str(e)}'
        })

@app.route('/v1v2-volume')
def v1v2_volume():
    """V1V2成交量系统页面"""
    return render_template('v1v2_volume.html')

@app.route('/v1v2-monitor')
def v1v2_monitor():
    """V1V2成交额监控页面"""
    return render_template('v1v2_monitor.html')

@app.route('/api/v1v2/latest')
def api_v1v2_latest():
    """获取所有币种的最新V1V2数据"""
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('v1v2_data.db')
        cursor = conn.cursor()
        
        # 27个币种配置
        coins_config = {
            'BTC': {'v1': 200000, 'v2': 100000},
            'ETH': {'v1': 1300000, 'v2': 500000},
            'XRP': {'v1': 200000, 'v2': 87000},
            'SOL': {'v1': 351620, 'v2': 246380},
            'BNB': {'v1': 2388300, 'v2': 1737500},
            'LTC': {'v1': 50000, 'v2': 15000},
            'DOGE': {'v1': 150000, 'v2': 60000},
            'SUI': {'v1': 2000000, 'v2': 800000},
            'TRX': {'v1': 13280, 'v2': 6022},
            'TON': {'v1': 350000, 'v2': 200000},
            'ETC': {'v1': 12000, 'v2': 2000},
            'BCH': {'v1': 103500, 'v2': 50000},
            'HBAR': {'v1': 103500, 'v2': 40000},
            'XLM': {'v1': 103500, 'v2': 30000},
            'FIL': {'v1': 5003500, 'v2': 3700000},
            'ADA': {'v1': 67210, 'v2': 44230},
            'LINK': {'v1': 280000, 'v2': 200000},
            'CRO': {'v1': 100000, 'v2': 40000},
            'DOT': {'v1': 300000, 'v2': 250000},
            'UNI': {'v1': 140000, 'v2': 100000},
            'NEAR': {'v1': 100000, 'v2': 50000},
            'APT': {'v1': 300000, 'v2': 200000},
            'CFX': {'v1': 300000, 'v2': 250000},
            'CRV': {'v1': 1500000, 'v2': 1000000},
            'STX': {'v1': 50000, 'v2': 30000},
            'LDO': {'v1': 1000000, 'v2': 600000},
            'TAO': {'v1': 300000, 'v2': 180000}
        }
        
        result = []
        update_time = None
        
        for symbol, thresholds in coins_config.items():
            table_name = f'volume_{symbol.lower()}'
            
            try:
                # 获取最新一条记录（按ID降序，确保获取最新插入的数据）
                cursor.execute(f'''
                    SELECT volume, collect_time, level, timestamp
                    FROM {table_name}
                    ORDER BY id DESC
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                
                if row:
                    result.append({
                        'symbol': symbol,
                        'volume': row[0],
                        'collect_time': row[1],
                        'level': row[2],
                        'v1': thresholds['v1'],
                        'v2': thresholds['v2']
                    })
                    
                    if not update_time:
                        update_time = row[1]
                        
            except sqlite3.OperationalError:
                # 表不存在,跳过
                continue
        
        conn.close()
        
        # 按级别排序: V1 > V2 > NONE
        level_order = {'V1': 0, 'V2': 1, 'NONE': 2}
        result.sort(key=lambda x: (level_order.get(x['level'], 3), -x['volume']))
        
        return jsonify({
            'success': True,
            'count': len(result),
            'data': result,
            'update_time': update_time
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        })

@app.route('/v1v2-settings')
def v1v2_settings():
    """V1V2阈值设置页面"""
    return render_template('v1v2_settings.html')

@app.route('/api/v1v2/settings', methods=['GET', 'POST'])
def api_v1v2_settings():
    """获取或更新V1V2阈值设置"""
    import json
    import os
    
    SETTINGS_FILE = 'v1v2_settings.json'
    
    # 默认配置
    DEFAULT_SETTINGS = {
        'BTC': {'v1': 200000, 'v2': 100000},
        'ETH': {'v1': 1300000, 'v2': 500000},
        'XRP': {'v1': 200000, 'v2': 87000},
        'SOL': {'v1': 351620, 'v2': 246380},
        'BNB': {'v1': 2388300, 'v2': 1737500},
        'LTC': {'v1': 50000, 'v2': 15000},
        'DOGE': {'v1': 150000, 'v2': 60000},
        'SUI': {'v1': 2000000, 'v2': 800000},
        'TRX': {'v1': 13280, 'v2': 6022},
        'TON': {'v1': 350000, 'v2': 200000},
        'ETC': {'v1': 12000, 'v2': 2000},
        'BCH': {'v1': 103500, 'v2': 50000},
        'HBAR': {'v1': 103500, 'v2': 40000},
        'XLM': {'v1': 103500, 'v2': 30000},
        'FIL': {'v1': 5003500, 'v2': 3700000},
        'ADA': {'v1': 67210, 'v2': 44230},
        'LINK': {'v1': 280000, 'v2': 200000},
        'CRO': {'v1': 100000, 'v2': 40000},
        'DOT': {'v1': 300000, 'v2': 250000},
        'UNI': {'v1': 140000, 'v2': 100000},
        'NEAR': {'v1': 100000, 'v2': 50000},
        'APT': {'v1': 300000, 'v2': 200000},
        'CFX': {'v1': 300000, 'v2': 250000},
        'CRV': {'v1': 1500000, 'v2': 1000000},
        'STX': {'v1': 50000, 'v2': 30000},
        'LDO': {'v1': 1000000, 'v2': 600000},
        'TAO': {'v1': 300000, 'v2': 180000}
    }
    
    if request.method == 'GET':
        # 读取设置
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = DEFAULT_SETTINGS
                # 保存默认设置
                with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'settings': settings
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'读取设置失败: {str(e)}'
            })
    
    elif request.method == 'POST':
        # 更新设置
        try:
            data = request.get_json()
            new_settings = data.get('settings', {})
            
            # 验证数据
            for symbol, config in new_settings.items():
                if 'v1' not in config or 'v2' not in config:
                    return jsonify({
                        'success': False,
                        'message': f'币种 {symbol} 配置不完整'
                    })
                
                # 确保V1 > V2
                if config['v1'] <= config['v2']:
                    return jsonify({
                        'success': False,
                        'message': f'币种 {symbol}: V1阈值必须大于V2阈值'
                    })
            
            # 保存设置
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=2, ensure_ascii=False)
            
            # 触发采集器重新加载配置（通过创建标记文件）
            with open('.v1v2_settings_updated', 'w') as f:
                f.write(str(int(time.time())))
            
            return jsonify({
                'success': True,
                'message': '设置已保存，采集器将在下次采集时使用新配置'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'保存设置失败: {str(e)}'
            })

@app.route('/api/v1v2/statistics')
def api_v1v2_statistics():
    """获取V1V2信号统计数据（1h/3h/12h/1day/3day/7day）"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('v1v2_data.db', timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        cursor = conn.cursor()
        
        # 获取所有币种表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'volume_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 定义时间范围
        now = datetime.now()
        time_ranges = {
            '1h': now - timedelta(hours=1),
            '3h': now - timedelta(hours=3),
            '12h': now - timedelta(hours=12),
            '1day': now - timedelta(days=1),
            '3day': now - timedelta(days=3),
            '7day': now - timedelta(days=7)
        }
        
        statistics = []
        
        for table_name in tables:
            symbol = table_name.replace('volume_', '').upper()
            
            try:
                coin_stats = {
                    'symbol': symbol,
                    '1h': {'v1': 0, 'v2': 0, 'total': 0},
                    '3h': {'v1': 0, 'v2': 0, 'total': 0},
                    '12h': {'v1': 0, 'v2': 0, 'total': 0},
                    '1day': {'v1': 0, 'v2': 0, 'total': 0},
                    '3day': {'v1': 0, 'v2': 0, 'total': 0},
                    '7day': {'v1': 0, 'v2': 0, 'total': 0}
                }
                
                # 对每个时间范围进行统计
                for period, start_time in time_ranges.items():
                    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 统计V1和V2的次数（只统计V1和V2）
                    cursor.execute(f"""
                        SELECT level, COUNT(*) 
                        FROM {table_name} 
                        WHERE collect_time >= ? AND level IN ('V1', 'V2')
                        GROUP BY level
                    """, (start_time_str,))
                    
                    counts = dict(cursor.fetchall())
                    v1_count = counts.get('V1', 0)
                    v2_count = counts.get('V2', 0)
                    
                    coin_stats[period]['v1'] = v1_count
                    coin_stats[period]['v2'] = v2_count
                    coin_stats[period]['total'] = v1_count + v2_count
                
                statistics.append(coin_stats)
                
            except sqlite3.OperationalError:
                # 表不存在或出错，跳过
                continue
        
        conn.close()
        
        # 按7天总信号数排序
        statistics.sort(key=lambda x: x['7day']['total'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'statistics': statistics,
                'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'total_coins': len(statistics)
            }
        })
        
    except Exception as e:
        import traceback
        print(f"❌ V1V2统计API错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

@app.route('/price-speed-monitor')
def price_speed_monitor():
    """1分钟涨跌速监控页面"""
    return render_template('price_speed_monitor.html')

@app.route('/api/price-speed/latest')
def api_price_speed_latest():
    """获取所有币种的最新涨跌速数据"""
    try:
        import sqlite3
        from datetime import datetime
        import pytz
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        conn = sqlite3.connect('price_speed_data.db')
        cursor = conn.cursor()
        
        # 获取所有币种的最新数据
        cursor.execute('''
            SELECT symbol, current_price, previous_price, change_percent, 
                   alert_level, alert_type, timestamp
            FROM latest_price_speed
            ORDER BY symbol
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'symbol': row[0],
                'current_price': row[1],
                'previous_price': row[2],
                'change_percent': row[3],
                'alert_level': row[4],
                'alert_type': row[5],
                'timestamp': row[6]
            })
        
        return jsonify({
            'success': True,
            'count': len(data),
            'data': data,
            'update_time': datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取涨跌速数据失败: {str(e)}',
            'data': []
        })

@app.route('/api/price-speed/history/<symbol>')
def api_price_speed_history(symbol):
    """获取指定币种的历史涨跌速数据"""
    try:
        import sqlite3
        
        # 获取查询参数
        limit = request.args.get('limit', 100, type=int)
        
        conn = sqlite3.connect('price_speed_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT current_price, previous_price, change_percent, 
                   alert_level, alert_type, timestamp
            FROM price_speed_alerts
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'current_price': row[0],
                'previous_price': row[1],
                'change_percent': row[2],
                'alert_level': row[3],
                'alert_type': row[4],
                'timestamp': row[5]
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史数据失败: {str(e)}',
            'data': []
        })

# ============================================================================
# Google Drive TXT检测器 API
# ============================================================================

@app.route('/gdrive-detector')
def gdrive_detector_page():
    """Google Drive检测器页面"""
    return render_template('gdrive_detector.html')

@app.route('/test-gdrive-status')
def test_gdrive_status():
    """Google Drive状态测试页面"""
    return render_template('test_gdrive_status.html')

@app.route('/gdrive-detector-fresh')
def gdrive_detector_fresh():
    """Google Drive检测器页面（无缓存版本）"""
    import time
    return render_template('gdrive_detector_fresh.html', timestamp=int(time.time()))

@app.route('/opening-logic')
def opening_logic_page():
    """开仓逻辑系统页面"""
    from flask import make_response
    response = make_response(render_template('opening_logic.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/opening-logic/suggestion')
def opening_logic_suggestion():
    """获取开仓建议API"""
    try:
        from opening_logic import get_opening_suggestion
        result = get_opening_suggestion()
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/gdrive-detector/status')
def gdrive_detector_status():
    """获取Google Drive检测器状态"""
    try:
        import subprocess
        import re
        import requests
        from datetime import datetime
        import pytz
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        # 检查检测器进程是否运行
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        detector_running = ('gdrive_txt_detector.py' in result.stdout or 
                          'gdrive_final_detector.py' in result.stdout or
                          'gdrive_smart_detector.py' in result.stdout)
        
        # 从数据库读取最新数据时间戳
        file_timestamp = None
        delay_minutes = None
        
        try:
            import sqlite3
            db_path = '/home/user/webapp/crypto_data.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT snapshot_time FROM crypto_snapshots ORDER BY created_at DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                file_timestamp = result[0]
                # 计算延迟 - 数据库时间是北京时间
                try:
                    last_time = datetime.strptime(file_timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    last_time = datetime.strptime(file_timestamp, '%Y-%m-%d %H:%M:%S.%f')
                
                # 数据库存储的是北京时间，直接与北京时间比较
                last_time_beijing = beijing_tz.localize(last_time)
                delay_seconds = (now - last_time_beijing).total_seconds()
                delay_minutes = delay_seconds / 60
        except:
            pass
        
        # 读取日志获取检查次数
        check_count = 0
        last_check_time = None
        try:
            with open('/home/user/webapp/gdrive_final_detector.log', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if '检查 #' in line:
                        match = re.search(r'检查 #(\d+)', line)
                        if match:
                            check_count = int(match.group(1))
                    if re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
                        # 提取时间戳
                        match = re.search(r'(2025-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if match:
                            last_check_time = match.group(1)
        except:
            pass
        
        # 从配置文件读取所有文件夹ID
        root_folder_odd = "1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM"  # 默认值
        root_folder_even = "1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM"  # 默认值
        folder_id = None  # 子账号文件夹ID（今日文件夹）
        
        try:
            import json
            config_file = '/home/user/webapp/daily_folder_config.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 读取单数/双数父文件夹ID
                if 'root_folder_odd' in config:
                    root_folder_odd = config['root_folder_odd']
                if 'root_folder_even' in config:
                    root_folder_even = config['root_folder_even']
                # 🆕 读取子账号文件夹ID（今日文件夹）
                if 'folder_id' in config:
                    folder_id = config['folder_id']
        except:
            pass
        
        # 如果配置文件中没有子账号文件夹ID，尝试从日志读取
        if not folder_id:
            try:
                with open('/home/user/webapp/gdrive_final_detector.log', 'r') as f:
                    lines = f.readlines()
                    for line in reversed(lines[-100:]):  # 只看最近100行
                        # 提取文件夹ID（子账号）
                        if '今日文件夹' in line or '子文件夹' in line:
                            match = re.search(r'([A-Za-z0-9_-]{20,})', line)
                            if match and match.group(1) != root_folder_odd and match.group(1) != root_folder_even:
                                folder_id = match.group(1)
                                break
            except:
                pass
        
        return jsonify({
            'success': True,
            'data': {
                'detector_running': detector_running,
                'file_timestamp': file_timestamp,
                'delay_minutes': delay_minutes,
                'check_count': check_count,
                'last_check_time': last_check_time,
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'folder_id': folder_id,
                'root_folder_odd': root_folder_odd,
                'root_folder_even': root_folder_even,
                'today_date': now.strftime('%Y年%m月%d日')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        })

@app.route('/api/gdrive-detector/txt-files')
def gdrive_detector_txt_files():
    """获取今天的TXT文件列表"""
    try:
        import requests
        import re
        from datetime import datetime
        import pytz
        import json
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        today = datetime.now(beijing_tz).strftime('%Y-%m-%d')
        
        # 从配置文件读取今天的文件夹ID
        folder_id = "1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM"  # 默认值
        try:
            config_file = '/home/user/webapp/daily_folder_config.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if config.get('current_date') == today and 'folder_id' in config:
                    folder_id = config['folder_id']
        except:
            pass
        
        url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
        
        response = requests.get(url, timeout=10)
        content = response.text
        
        # 查找今天所有的TXT文件
        pattern = rf'>{today}_(\d{{4}})\.txt<'
        matches = re.findall(pattern, content)
        
        # 排序（从新到旧）
        times_sorted = sorted(matches, reverse=True)
        filenames = [f"{today}_{time}.txt" for time in times_sorted]
        
        return jsonify({
            'success': True,
            'files': filenames,
            'count': len(filenames),
            'date': today,
            'folder_id': folder_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'files': [],
            'count': 0
        })

@app.route('/api/gdrive-detector/logs')
def gdrive_detector_logs():
    """获取检测器日志"""
    try:
        lines = request.args.get('lines', 50, type=int)
        
        # 尝试多个日志文件
        log_files = [
            '/home/user/webapp/gdrive_final_detector.log',
            '/home/user/webapp/gdrive_txt_detector.log',
            '/home/user/webapp/gdrive_smart_detector.log'
        ]
        
        log_content = None
        total_lines = 0
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    log_content = ''.join(all_lines[-lines:] if len(all_lines) > lines else all_lines)
                    total_lines = len(all_lines)
                    break
            except FileNotFoundError:
                continue
        
        if log_content is not None:
            return jsonify({
                'success': True,
                'logs': log_content,
                'total_lines': total_lines
            })
        else:
            return jsonify({
                'success': True,
                'logs': '日志文件不存在',
                'total_lines': 0
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'logs': ''
        })

@app.route('/api/gdrive-detector/config', methods=['GET'])
def gdrive_detector_get_config():
    """获取Google Drive配置"""
    try:
        import json
        config_file = '/home/user/webapp/daily_folder_config.json'
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/gdrive-detector/config', methods=['POST'])
def gdrive_detector_update_config():
    """更新Google Drive配置（父文件夹共享链接）"""
    try:
        import json
        import re
        import requests
        from datetime import datetime
        import pytz
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        data = request.get_json()
        parent_folder_url = data.get('parent_folder_url', '')
        
        # 从URL中提取文件夹ID
        match = re.search(r'folders/([A-Za-z0-9_-]+)', parent_folder_url)
        if not match:
            return jsonify({
                'success': False,
                'message': '无效的Google Drive文件夹链接'
            })
        
        parent_folder_id = match.group(1)
        
        # 获取父文件夹内的今日文件夹
        today_str = now.strftime('%Y-%m-%d')
        url = f"https://drive.google.com/embeddedfolderview?id={parent_folder_id}"
        response = requests.get(url, timeout=10)
        content = response.text
        
        # 查找今日日期文件夹
        folder_pattern = rf'>{today_str}<'
        if today_str not in content:
            return jsonify({
                'success': False,
                'message': f'父文件夹中未找到今日文件夹: {today_str}'
            })
        
        # 提取今日文件夹ID
        # 查找包含今日日期的文件夹链接
        folder_id_pattern = rf'"([A-Za-z0-9_-]{{20,}})"[^>]*>{today_str}<'
        folder_match = re.search(folder_id_pattern, content)
        
        if not folder_match:
            # 尝试另一种模式
            folder_id_pattern = rf'https://drive\.google\.com/drive/folders/([A-Za-z0-9_-]+)[^>]*>{today_str}<'
            folder_match = re.search(folder_id_pattern, content)
        
        if not folder_match:
            return jsonify({
                'success': False,
                'message': f'无法从父文件夹中提取今日文件夹ID: {today_str}'
            })
        
        today_folder_id = folder_match.group(1)
        
        # 验证今日文件夹是否包含TXT文件
        txt_url = f"https://drive.google.com/embeddedfolderview?id={today_folder_id}"
        txt_response = requests.get(txt_url, timeout=10)
        txt_content = txt_response.text
        
        # 查找TXT文件
        txt_pattern = rf'>{today_str}_(\d{{4}})\.txt<'
        txt_matches = re.findall(txt_pattern, txt_content)
        
        if not txt_matches:
            return jsonify({
                'success': False,
                'message': f'今日文件夹中未找到TXT文件'
            })
        
        # 获取最新的TXT文件
        latest_txt_time = sorted(txt_matches, reverse=True)[0]
        latest_txt = f"{today_str}_{latest_txt_time}.txt"
        
        # 更新配置文件
        config_file = '/home/user/webapp/daily_folder_config.json'
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {}
        
        # 判断今天是单数还是双数日期
        day_of_month = now.day
        is_odd_day = day_of_month % 2 == 1
        
        # 更新配置
        config['parent_folder_url'] = parent_folder_url
        config['parent_folder_id'] = parent_folder_id
        config['current_date'] = today_str
        config['data_date'] = today_str
        config['folder_id'] = today_folder_id
        config['folder_name'] = today_str
        config['latest_txt'] = latest_txt
        config['txt_count'] = len(txt_matches)
        config['last_update'] = now.strftime('%Y-%m-%d %H:%M:%S')
        config['update_reason'] = '通过配置页面更新父文件夹'
        config['last_manual_update'] = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 根据单双数更新对应的父文件夹ID
        if is_odd_day:
            config['root_folder_odd'] = parent_folder_id
        else:
            config['root_folder_even'] = parent_folder_id
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': '配置更新成功',
            'data': {
                'parent_folder_id': parent_folder_id,
                'today_folder_id': today_folder_id,
                'today_date': today_str,
                'txt_count': len(txt_matches),
                'latest_txt': latest_txt,
                'is_odd_day': is_odd_day
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/gdrive-detector/trigger-update', methods=['POST'])
def gdrive_detector_trigger_update():
    """触发手动更新检测"""
    try:
        import subprocess
        import time
        
        # 运行检测脚本一次
        result = subprocess.run(
            ['python3', '/home/user/webapp/gdrive_final_detector.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return jsonify({
            'success': True,
            'message': '检测已执行',
            'output': result.stdout[:500] if result.stdout else '',
            'error': result.stderr[:500] if result.stderr else ''
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': '检测超时（30秒）'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/gdrive-config')
def gdrive_config_page():
    """Google Drive配置页面"""
    return render_template('gdrive_config.html')

# ==================== 统一监控页面 ====================
@app.route('/unified-monitor')
def unified_monitor():
    """统一采集监控页面"""
    return render_template('unified_monitor.html')

@app.route('/unified-monitor-enhanced')
def monitor_enhanced():
    """统一采集监控页面（增强版）- 带执行日志和开关控制"""
    return render_template('unified_monitor_enhanced.html')

# ==================== 综合采集器监控 API ====================
@app.route('/api/collectors/status')
def api_collectors_status():
    """获取所有采集器的运行状态"""
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'get_all_collectors_status.py'],
            cwd='/home/user/webapp',
            capture_output=True,
            text=True,
            timeout=10
        )
        status_list = json.loads(result.stdout)
        
        # 统计状态
        total = len(status_list)
        normal = sum(1 for s in status_list if s['status'] == 'normal')
        warning = sum(1 for s in status_list if s['status'] == 'warning')
        error = sum(1 for s in status_list if s['status'] in ['error', 'stopped', 'no_data'])
        
        return jsonify({
            'success': True,
            'collectors': status_list,
            'summary': {
                'total': total,
                'normal': normal,
                'warning': warning,
                'error': error
            },
            'timestamp': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/favicon.ico')
def favicon():
    """处理favicon请求，避免404错误"""
    return '', 204  # 返回无内容状态码

# ============================================================================
# 币种选择和评分系统
# ============================================================================

@app.route('/coin-pool')
def coin_pool_page():
    """币种池页面 - 从星星系统筛选的优质币种池"""
    response = make_response(render_template('coin_pool.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ============================================================================
# 支撑压力线系统
# ============================================================================

@app.route('/support-resistance')
def support_resistance_page():
    """支撑压力线系统页面"""
    response = make_response(render_template('support_resistance.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/trading-signals')
def trading_signals_page():
    """决策-交易信号系统页面"""
    response = make_response(render_template('trading_signals.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def track_trading_signal(symbol, buy_point_type, suggested_position):
    """跟踪交易信号的首次触发时间"""
    from datetime import datetime
    import pytz
    import sqlite3
    
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)
    
    signal_key = f"{symbol}_{buy_point_type}"
    
    # 使用独立的数据库连接
    conn_track = sqlite3.connect('databases/crypto_data.db')
    conn_track.row_factory = sqlite3.Row
    cursor_track = conn_track.cursor()
    
    try:
        # 检查该信号是否已存在
        cursor_track.execute('''
            SELECT id, first_triggered_at, suggested_position 
            FROM trading_signal_history 
            WHERE signal_key = ? AND is_active = 1
        ''', (signal_key,))
        
        existing = cursor_track.fetchone()
        
        if existing:
            # 更新最后更新时间
            cursor_track.execute('''
                UPDATE trading_signal_history 
                SET last_updated_at = ?, suggested_position = ?
                WHERE id = ?
            ''', (now.strftime('%Y-%m-%d %H:%M:%S'), suggested_position, existing['id']))
            conn_track.commit()
            return {
                'first_triggered_at': existing['first_triggered_at'],
                'initial_position': str(int(float(existing['suggested_position'].replace('%', '')) * 0.3)) + '%'
            }
        else:
            # 插入新信号
            cursor_track.execute('''
                INSERT INTO trading_signal_history 
                (signal_key, symbol, buy_point_type, suggested_position, 
                 first_triggered_at, last_updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (signal_key, symbol, buy_point_type, suggested_position,
                  now.strftime('%Y-%m-%d %H:%M:%S'), 
                  now.strftime('%Y-%m-%d %H:%M:%S')))
            conn_track.commit()
            return {
                'first_triggered_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                'initial_position': str(int(float(suggested_position.replace('%', '')) * 0.3)) + '%'
            }
    finally:
        conn_track.close()

def check_no_new_low_5min(symbol):
    """检查创新低后连续5个5分钟K线不创新低"""
    import sqlite3
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect('databases/crypto_data.db')
    cursor = conn.cursor()
    
    try:
        # 统一格式：FIL -> FIL-USDT-SWAP
        symbol_full = f"{symbol}-USDT-SWAP" if not symbol.endswith('-USDT-SWAP') else symbol
        symbol_short = symbol.replace('-USDT-SWAP', '')
        
        # 获取最近的创新低事件
        cursor.execute('''
            SELECT event_time, price
            FROM price_breakthrough_events
            WHERE symbol = ? AND event_type = 'new_low'
            ORDER BY event_time DESC
            LIMIT 1
        ''', (symbol_short,))
        
        last_new_low = cursor.fetchone()
        if not last_new_low:
            return False
        
        new_low_time = datetime.strptime(last_new_low[0], '%Y-%m-%d %H:%M:%S')
        new_low_price = last_new_low[1]
        
        # 获取创新低之后的5个5分钟K线
        cursor.execute('''
            SELECT low, timestamp
            FROM okex_kline_ohlc
            WHERE symbol = ?
              AND timeframe = '5m'
              AND datetime(timestamp/1000, 'unixepoch') > datetime(?)
            ORDER BY timestamp ASC
            LIMIT 5
        ''', (symbol_full, new_low_time.strftime('%Y-%m-%d %H:%M:%S')))
        
        klines_after = cursor.fetchall()
        
        # 需要有5根K线
        if len(klines_after) < 5:
            return False
        
        # 检查这5根K线是否都没有创新低
        for low, ts in klines_after:
            if low < new_low_price:
                return False
        
        return True
    finally:
        conn.close()

def get_1h_rsi(symbol):
    """获取1小时RSI"""
    import sqlite3
    
    conn = sqlite3.connect('databases/crypto_data.db')
    cursor = conn.cursor()
    
    try:
        # 统一格式
        symbol_full = f"{symbol}-USDT-SWAP" if not symbol.endswith('-USDT-SWAP') else symbol
        
        cursor.execute('''
            SELECT rsi_14
            FROM okex_technical_indicators
            WHERE symbol = ? AND timeframe IN ('1h', '1H')
            ORDER BY record_time DESC
            LIMIT 1
        ''', (symbol_full,))
        
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def check_consecutive_oscillation_5min(symbol):
    """检查5分钟周期连续3个震荡≤0.5% 且涨跌在0%到+0.25%之间（不包括负涨跌）"""
    import sqlite3
    
    conn = sqlite3.connect('databases/crypto_data.db')
    cursor = conn.cursor()
    
    try:
        # 统一格式
        symbol_full = f"{symbol}-USDT-SWAP" if not symbol.endswith('-USDT-SWAP') else symbol
        
        # 获取最近3根5分钟K线
        cursor.execute('''
            SELECT open, high, low, close
            FROM okex_kline_ohlc
            WHERE symbol = ?
              AND timeframe = '5m'
            ORDER BY timestamp DESC
            LIMIT 3
        ''', (symbol_full,))
        
        klines = cursor.fetchall()
        
        if len(klines) < 3:
            return False
        
        # 检查每根K线
        for open_price, high, low, close in klines:
            if open_price == 0:
                return False
            
            # 震荡幅度 = (最高-最低) / 开盘 * 100
            oscillation = ((high - low) / open_price) * 100 if open_price > 0 else 999
            
            # 涨跌幅 = (收盘-开盘) / 开盘 * 100（保留正负，不取绝对值）
            change = ((close - open_price) / open_price) * 100
            
            # 任何一根不满足条件就返回False
            # 涨跌幅必须在 0% 到 +0.25% 之间，震荡幅度 <= 0.50%
            if change < 0 or change > 0.25 or oscillation > 0.5:
                return False
        
        return True
    finally:
        conn.close()

def deactivate_missing_signals(active_signal_keys):
    """将不再满足条件的信号标记为失效"""
    from datetime import datetime
    import pytz
    import sqlite3
    
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)
    
    conn = sqlite3.connect('databases/crypto_data.db')
    cursor = conn.cursor()
    
    try:
        # 获取所有当前活跃的信号
        cursor.execute('SELECT signal_key FROM trading_signal_history WHERE is_active = 1')
        all_active = [row[0] for row in cursor.fetchall()]
        
        # 找出不在当前信号列表中的信号（即条件不再满足的信号）
        signals_to_deactivate = [sig for sig in all_active if sig not in active_signal_keys]
        
        # 标记这些信号为失效
        for signal_key in signals_to_deactivate:
            cursor.execute('''
                UPDATE trading_signal_history 
                SET is_active = 0, last_updated_at = ?
                WHERE signal_key = ? AND is_active = 1
            ''', (now.strftime('%Y-%m-%d %H:%M:%S'), signal_key))
        
        conn.commit()
        return len(signals_to_deactivate)
    finally:
        conn.close()

@app.route('/api/trading-signals/analyze')
def api_trading_signals_analyze():
    """分析交易信号 - 做多买点1/2/3"""
    try:
        from datetime import datetime, timedelta
        import pytz
        from opening_logic import get_opening_suggestion
        
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        # 0. 获取开仓逻辑建议（用于买点3仓位计算）
        try:
            opening_logic_data = get_opening_suggestion()
            opening_position = opening_logic_data.get('position_info', {})
            opening_can_long = opening_logic_data.get('can_long', False)
            opening_position_percent = opening_position.get('position_percent', 0)
        except Exception as e:
            print(f"获取开仓逻辑失败: {e}")
            opening_can_long = False
            opening_position_percent = 0
        
        # 1. 获取支撑压力线数据
        cursor.execute('''
            SELECT symbol, current_price, support_line_1, support_line_2, resistance_line_1,
                   distance_to_support_1, distance_to_support_2, distance_to_resistance_1,
                   position_s2_r1, record_time
            FROM support_resistance_levels
            WHERE id IN (
                SELECT MAX(id) 
                FROM support_resistance_levels 
                GROUP BY symbol
            )
        ''')
        sr_data = {row['symbol']: dict(row) for row in cursor.fetchall()}
        
        # 2. 获取价格突破数据(创新低统计 - 最近7天)
        seven_days_ago = now - timedelta(days=7)
        cursor.execute('''
            SELECT symbol, COUNT(*) as count
            FROM price_breakthrough_events
            WHERE event_type = 'new_low'
              AND event_time >= ?
            GROUP BY symbol
        ''', (seven_days_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        breakthrough_data = {row['symbol']: row['count'] for row in cursor.fetchall()}
        
        # 3. 获取最新快照数据(急涨急跌、计次得分)
        cursor.execute('''
            SELECT c.symbol, c.rush_up, c.rush_down, c.current_price,
                   s.count_score_display, s.count_score_type
            FROM crypto_coin_data c
            JOIN crypto_snapshots s ON c.snapshot_id = s.id
            WHERE c.id IN (
                SELECT MAX(id) 
                FROM crypto_coin_data 
                GROUP BY symbol
            )
        ''')
        coin_data = {row['symbol']: dict(row) for row in cursor.fetchall()}
        
        # 3.5 获取K线指标数据 (5分钟RSI、SAR位置、SAR象限)
        cursor.execute('''
            SELECT symbol, rsi_14, sar_position, sar_quadrant, sar_count_label
            FROM okex_technical_indicators
            WHERE timeframe = '5m'
              AND (symbol, record_time) IN (
                SELECT symbol, MAX(record_time)
                FROM okex_technical_indicators
                WHERE timeframe = '5m'
                GROUP BY symbol
            )
        ''')
        kline_indicators = {}
        for row in cursor.fetchall():
            # 统一格式：FIL-USDT-SWAP -> FIL
            symbol_short = row['symbol'].replace('-USDT-SWAP', '')
            kline_indicators[symbol_short] = {
                'rsi_5m': row['rsi_14'],
                'sar_position': row['sar_position'],  # 'bullish' 或 'bearish'
                'sar_quadrant': row['sar_quadrant'],  # 1-4象限
                'sar_count_label': row['sar_count_label']  # 例如 "多头12"
            }
        
        # 4. 获取位置系统数据（BTC/ETH的4h/12h/24h/48h周期位置）
        cursor.execute('''
            SELECT symbol, position_4h, position_12h, position_24h, position_48h
            FROM position_system
            WHERE symbol IN ('BTC', 'ETH')
              AND id IN (
                SELECT MAX(id) 
                FROM position_system 
                GROUP BY symbol
            )
        ''')
        position_data = {}
        for row in cursor.fetchall():
            symbol = row['symbol']
            positions = [
                row['position_4h'], row['position_12h'], 
                row['position_24h'], row['position_48h']
            ]
            # 统计有多少个周期位置 < 10%
            low_position_count = sum(1 for p in positions if p is not None and p < 10)
            position_data[symbol] = low_position_count
        
        conn.close()
        
        # 检查BTC和ETH是否至少有5个周期 < 10%
        # 由于只有4个周期，我们改为检查BTC和ETH加起来是否有5个以上
        btc_low = position_data.get('BTC', 0)
        eth_low = position_data.get('ETH', 0)
        total_low_positions = btc_low + eth_low
        condition6_pass = total_low_positions >= 5
        
        # 5. 统计接近支撑线的币种数量（用于买点3条件6）
        # 接近支撑1：距离支撑线1 <= 某个阈值（例如10%）
        # 接近支撑2：距离支撑线2 <= 某个阈值（例如10%）
        near_support_1_count = 0
        near_support_2_count = 0
        
        for symbol, sr in sr_data.items():
            dist_s1 = sr.get('distance_to_support_1')
            dist_s2 = sr.get('distance_to_support_2')
            
            # 统计接近支撑1的币种（距离 <= 10%）
            if dist_s1 is not None and dist_s1 <= 10:
                near_support_1_count += 1
            
            # 统计接近支撑2的币种（距离 <= 10%）
            if dist_s2 is not None and dist_s2 <= 10:
                near_support_2_count += 1
        
        # 买点3条件6：接近支撑1的币种数 >= 8 或 接近支撑2的币种数 >= 8
        condition6_support_system = near_support_1_count >= 8 or near_support_2_count >= 8
        
        # 6. 分析信号
        signals = []
        buy_point_1_count = 0
        buy_point_2_count = 0
        buy_point_3_count = 0
        
        for symbol, sr in sr_data.items():
            coin_name = symbol.replace('USDT', '')
            coin = coin_data.get(coin_name, {})
            kline = kline_indicators.get(coin_name, {})
            
            # 获取创新低次数
            new_lows = breakthrough_data.get(coin_name, 0)
            
            # 获取计次得分
            score_display = coin.get('count_score_display', '---')
            score_type = coin.get('count_score_type', '中性')
            
            # 获取急涨急跌
            rush_up = coin.get('rush_up', 0) or 0
            rush_down = coin.get('rush_down', 0) or 0
            rush_diff = rush_up - rush_down
            
            # 获取K线指标数据
            rsi_5m = kline.get('rsi_5m')
            sar_position = kline.get('sar_position')  # 'bullish' / 'bearish'
            sar_quadrant = kline.get('sar_quadrant')  # 1-4
            sar_count_label = kline.get('sar_count_label', '')
            
            # 解析空头/多头数量（从 "空头20" 或 "多头12" 中提取数字）
            sar_count = 0
            if sar_count_label:
                import re
                match = re.search(r'(\d+)', sar_count_label)
                if match:
                    sar_count = int(match.group(1))
            
            # 通用条件判断
            condition1 = new_lows < 3  # 创新低 < 3 【买点1/2/3适用】
            condition2 = '★' in score_display or '⭐' in score_display  # 计次得分是星星 【买点1/2适用】
            condition3 = rush_diff > 0  # 急涨 - 急跌 > 0 【买点1/2适用】
            condition4 = rsi_5m is not None and rsi_5m < 20  # 5分钟RSI < 20 【买点1适用】（修改为使用5分钟RSI）
            condition5 = rush_diff > -15  # 急涨 - 急跌 > -15 【买点3适用】
            condition6 = condition6_pass  # BTC/ETH至少5个周期 < 10% 【买点3适用】
            
            # 新增条件（基于K线指标）
            condition_sar_bearish = sar_position == 'bearish'  # 空头趋势
            condition_sar_count = sar_count > 20  # 空头数量>20
            condition_sar_quadrant3 = sar_quadrant == 3  # SAR第三象限
            condition_rsi_low = rsi_5m is not None and rsi_5m < 30  # 5分钟RSI<30 【买点2适用】
            
            # 买点3专用条件检查
            condition_no_new_low_5m = check_no_new_low_5min(coin_name)  # 创新低后连续5个5分钟K线不创新低
            rsi_1h = get_1h_rsi(coin_name)  # 获取1小时RSI
            condition_rsi_1h_low = rsi_1h is not None and rsi_1h < 15  # 1小时RSI<15
            condition_oscillation_3 = check_consecutive_oscillation_5min(coin_name)  # 连续3个震荡
            
            # 获取距离支撑线1的距离（用于买点1）
            distance = sr.get('distance_to_support_1')
            
            # 判断各个买点
            buy_point_1 = False
            buy_point_2 = False
            buy_point_3 = False
            
            # 买点1: 达到支撑线1 (距离 < 5%) + 条件1234
            if (distance is not None and distance <= 5 and 
                condition1 and condition2 and condition3 and condition4):
                buy_point_1 = True
                buy_point_1_count += 1
            
            # 买点2: 回调买入
            # 条件：条件123 + 空头>20 + 5分钟SAR第三象限 + 5分钟RSI<30
            if (condition1 and condition2 and condition3 and 
                condition_sar_count and condition_sar_quadrant3 and condition_rsi_low):
                buy_point_2 = True
                buy_point_2_count += 1
            
            # 买点3: 空转多买入（重新定义条件）
            # 6个必须条件：
            # 1. 创新低后连续5个5分钟K线不创新低
            # 2. 1小时RSI < 15
            # 3. 5分钟周期连续3个震荡≤0.5% 且涨跌<0.25%
            # 4. SAR空头数量 > 20
            # 5. 5分钟SAR在第三象限
            # 6. 支撑压力线系统：接近支撑1的币种数 >= 8 或 接近支撑2的币种数 >= 8
            if (condition_no_new_low_5m and 
                condition_rsi_1h_low and 
                condition_oscillation_3 and 
                condition_sar_count and 
                condition_sar_quadrant3 and 
                condition6_support_system):  # 使用全局条件
                buy_point_3 = True
                buy_point_3_count += 1
            
            # 只保留有信号的币种
            if buy_point_1 or buy_point_2 or buy_point_3:
                # 详细的条件判断结果 - 用于透明化显示
                detailed_conditions = {
                    'buy_point_1_conditions': {
                        'distance_to_support': {'value': distance, 'threshold': '≤ 5%', 'pass': distance is not None and distance <= 5, 'desc': '距离支撑线1'},
                        'condition1': {'value': new_lows, 'threshold': '< 3', 'pass': condition1, 'desc': '7天创新低次数'},
                        'condition2': {'value': score_display, 'threshold': '包含★或⭐', 'pass': condition2, 'desc': '计次得分显示'},
                        'condition3': {'value': round(rush_diff, 2), 'threshold': '> 0', 'pass': condition3, 'desc': '急涨-急跌'},
                        'condition4': {'value': round(rsi_5m, 2) if rsi_5m else None, 'threshold': '< 20', 'pass': condition4, 'desc': '5分钟RSI'}
                    },
                    'buy_point_2_conditions': {
                        'condition1': {'value': new_lows, 'threshold': '< 3', 'pass': condition1, 'desc': '7天创新低次数'},
                        'condition2': {'value': score_display, 'threshold': '包含★或⭐', 'pass': condition2, 'desc': '计次得分显示'},
                        'condition3': {'value': round(rush_diff, 2), 'threshold': '> 0', 'pass': condition3, 'desc': '急涨-急跌'},
                        'sar_count': {'value': sar_count, 'threshold': '> 20', 'pass': condition_sar_count, 'desc': 'SAR空头数量'},
                        'sar_quadrant': {'value': sar_quadrant, 'threshold': '= 3', 'pass': condition_sar_quadrant3, 'desc': 'SAR第三象限'},
                        'rsi_5m': {'value': round(rsi_5m, 2) if rsi_5m else None, 'threshold': '< 30', 'pass': condition_rsi_low, 'desc': '5分钟RSI'}
                    },
                    'buy_point_3_conditions': {
                        'no_new_low_5m': {'value': '是' if condition_no_new_low_5m else '否', 'threshold': '是', 'pass': condition_no_new_low_5m, 'desc': '创新低后连续5个5分钟K线不创新低'},
                        'rsi_1h': {'value': round(rsi_1h, 2) if rsi_1h else None, 'threshold': '< 15', 'pass': condition_rsi_1h_low, 'desc': '1小时RSI'},
                        'oscillation_3': {'value': '是' if condition_oscillation_3 else '否', 'threshold': '是', 'pass': condition_oscillation_3, 'desc': '连续3个震荡≤0.5% 且涨跌<0.25%'},
                        'sar_count': {'value': sar_count, 'threshold': '> 20', 'pass': condition_sar_count, 'desc': 'SAR空头数量'},
                        'sar_quadrant': {'value': sar_quadrant, 'threshold': '= 3', 'pass': condition_sar_quadrant3, 'desc': '5分钟SAR第三象限'},
                        'support_system': {'value': f'接近支撑1: {near_support_1_count}个, 接近支撑2: {near_support_2_count}个', 'threshold': '接近支撑1 ≥ 8个 或 接近支撑2 ≥ 8个', 'pass': condition6_support_system, 'desc': '支撑压力线系统'}
                    }
                }
                
                # 确定买点类型和建议仓位
                buy_point_type = None
                suggested_position = None
                position_calculation_note = None
                buy_times = None  # 分批买入次数
                
                if buy_point_1:
                    buy_point_type = 'buy_point_1'
                    suggested_position = '30%'
                    buy_times = 3  # 买点1分3次买入
                    position_calculation_note = '买点1固定仓位，分3次买入'
                    
                elif buy_point_3:
                    buy_point_type = 'buy_point_3'
                    buy_times = 2  # 买点3分2次买入
                    # 买点3特殊仓位逻辑
                    if opening_can_long and opening_position_percent > 0:
                        # 情况2：开仓逻辑允许开仓
                        # 买点3仓位 = 开仓逻辑建议 + 20%，最高70%
                        bp3_position = min(opening_position_percent + 20, 70)
                        suggested_position = f'{int(bp3_position)}%'
                        position_calculation_note = f'开仓逻辑{int(opening_position_percent)}% + 买点3加成20% = {int(bp3_position)}% (上限70%)，分2次买入'
                    else:
                        # 情况1：开仓逻辑不允许开仓
                        # 买点3可额外开20%
                        suggested_position = '20%'
                        position_calculation_note = '开仓逻辑不允许，买点3可额外开20%，分2次买入'
                        
                elif buy_point_2:
                    buy_point_type = 'buy_point_2'
                    suggested_position = '20%'
                    buy_times = 2  # 买点2分2次买入
                    position_calculation_note = '买点2固定仓位，分2次买入'
                
                # 跟踪信号历史，获取首次触发时间和首次开仓建议
                tracking_info = track_trading_signal(coin_name, buy_point_type, suggested_position)
                
                signals.append({
                    'symbol': coin_name,
                    'current_price': sr.get('current_price', 0),
                    'support_line_1': sr.get('support_line_1'),
                    'distance_to_support_1': distance,
                    'buy_point_1': buy_point_1,
                    'buy_point_2': buy_point_2,
                    'buy_point_3': buy_point_3,
                    'suggested_position': suggested_position,
                    'buy_times': buy_times,  # 新增：分批买入次数
                    'position_calculation_note': position_calculation_note,  # 新增：仓位计算说明
                    'opening_logic_position': f'{int(opening_position_percent)}%' if opening_can_long else '不允许',  # 新增：开仓逻辑建议
                    'first_triggered_at': tracking_info['first_triggered_at'],  # 新增：首次触发时间
                    'initial_position': tracking_info['initial_position'],  # 新增：首次开仓建议(总仓位的30%)
                    'conditions': {
                        'condition1_pass': condition1,
                        'condition2_pass': condition2,
                        'condition3_pass': condition3,
                        'new_lows': new_lows,
                        'score_display': score_display,
                        'rush_diff': round(rush_diff, 2)
                    },
                    'kline_indicators': {
                        'rsi_5m': round(rsi_5m, 2) if rsi_5m else None,
                        'sar_position': sar_position,
                        'sar_quadrant': sar_quadrant,
                        'sar_count': sar_count,
                        'sar_count_label': sar_count_label
                    },
                    'detailed_conditions': detailed_conditions  # 新增：详细条件判断结果
                })
        
        # 按买点1 > 买点3 > 买点2 优先级排序，同优先级按距支撑线距离排序
        def sort_key(x):
            priority = 0
            if x['buy_point_1']:
                priority = 3
            elif x['buy_point_3']:
                priority = 2
            elif x['buy_point_2']:
                priority = 1
            distance = x['distance_to_support_1'] if x['distance_to_support_1'] is not None else 999
            return (-priority, distance)
        
        signals.sort(key=sort_key)
        
        # 收集当前所有活跃信号的signal_key
        active_signal_keys = []
        for signal in signals:
            coin_name = signal['symbol']
            if signal['buy_point_1']:
                active_signal_keys.append(f"{coin_name}_buy_point_1")
            elif signal['buy_point_3']:
                active_signal_keys.append(f"{coin_name}_buy_point_3")
            elif signal['buy_point_2']:
                active_signal_keys.append(f"{coin_name}_buy_point_2")
        
        # 将不再满足条件的信号标记为失效
        deactivated_count = deactivate_missing_signals(active_signal_keys)
        
        # 买点规则说明 - 透明化展示
        buy_point_rules = {
            'buy_point_1': {
                'name': '买点1 - 支撑线买入',
                'suggested_position': '30%',
                'buy_times': 3,  # 分3次买入
                'conditions': [
                    {'id': '距离支撑线', 'rule': '距离支撑线1 ≤ 5%', 'priority': 'high'},
                    {'id': '创新低', 'rule': '7天创新低次数 < 3', 'priority': 'high'},
                    {'id': '计次得分', 'rule': '计次得分显示包含★或⭐', 'priority': 'medium'},
                    {'id': '急涨急跌', 'rule': '急涨 - 急跌 > 0', 'priority': 'medium'},
                    {'id': 'RSI 5m', 'rule': '5分钟RSI < 20', 'priority': 'high'}
                ],
                'description': '价格接近支撑线时的买入机会，风险较低，建议分3次买入'
            },
            'buy_point_2': {
                'name': '买点2 - 回调买入',
                'suggested_position': '20%',
                'buy_times': 2,  # 分2次买入
                'conditions': [
                    {'id': '创新低', 'rule': '7天创新低次数 < 3', 'priority': 'high'},
                    {'id': '计次得分', 'rule': '计次得分显示包含★或⭐', 'priority': 'medium'},
                    {'id': '急涨急跌', 'rule': '急涨 - 急跌 > 0', 'priority': 'medium'},
                    {'id': 'SAR空头数', 'rule': 'SAR空头数量 > 20', 'priority': 'high'},
                    {'id': 'SAR象限', 'rule': 'SAR在第三象限', 'priority': 'high'},
                    {'id': 'RSI 5m', 'rule': '5分钟RSI < 30', 'priority': 'high'}
                ],
                'description': '市场回调时的买入机会，需要技术指标确认，建议分2次买入'
            },
            'buy_point_3': {
                'name': '买点3 - 空转多买入',
                'suggested_position': '最多20% (如无开仓逻辑建议)',
                'buy_times': 2,  # 分2次买入
                'conditions': [
                    {'id': '5分钟不创新低', 'rule': '创新低后连续5个5分钟K线不创新低', 'priority': 'high'},
                    {'id': '1h RSI', 'rule': '1小时RSI < 15', 'priority': 'high'},
                    {'id': '连续震荡', 'rule': '5分钟周期连续3个震荡≤0.5% 且涨跌<0.25%', 'priority': 'high'},
                    {'id': 'SAR空头数', 'rule': 'SAR空头持续数量 > 20', 'priority': 'high'},
                    {'id': 'SAR象限', 'rule': '5分钟SAR在第三象限', 'priority': 'high'},
                    {'id': '支撑压力线', 'rule': '接近支撑1的币种数 ≥ 8个 或 接近支撑2的币种数 ≥ 8个', 'priority': 'high'}
                ],
                'description': '极度超卖后的空转多买入机会，严格条件筛选（需市场整体接近支撑线），建议分2次买入'
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'signals': signals,
                'buy_point_1_count': buy_point_1_count,
                'buy_point_2_count': buy_point_2_count,
                'buy_point_3_count': buy_point_3_count,
                'total_coins': len(sr_data),
                'update_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'buy_point_rules': buy_point_rules,  # 新增：买点规则说明
                'opening_logic_info': {  # 新增：开仓逻辑信息
                    'can_long': opening_can_long,
                    'position_percent': opening_position_percent,
                    'suggestion': f'{int(opening_position_percent)}%' if opening_can_long else '不允许开仓'
                },
                'notes': {
                    'buy_point_1': '✅ 支撑线买入 (距离<5%) + 创新低<3 + 计次得分⭐/★ + 急涨>急跌 + 5分钟RSI<20 - 已更新使用5分钟RSI',
                    'buy_point_2': '✅ 回调买入 (条件1-3 + 空头>20 + 5分钟SAR第三象限 + 5分钟RSI<30) - 已集成K线指标',
                    'buy_point_3': '✅ 空转多买入 (5个5分钟不创新低 + 1h RSI<15 + 连续3个震荡 + SAR空头>20 + SAR第3象限) - 严格条件',
                    'buy_point_3_position': '📊 买点3仓位规则：若开仓逻辑允许，则为 开仓逻辑仓位+20% (上限70%)；若开仓逻辑不允许，则额外开20%',
                    'data_integration': '✅ 已集成kline-indicators数据：5分钟RSI、SAR位置、SAR象限、SAR计数',
                    'data_limitation': '⚠️ 仍需补充：连续5个5分钟K线不创新低、连续3个震荡条件'
                }
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trading-signals/buy-points')
def api_trading_signals_buy_points():
    """获取当前所有买点信号（简化版API）"""
    try:
        import sqlite3
        from datetime import datetime
        import pytz
        
        # 调用现有的分析函数
        response = api_trading_signals_analyze()
        
        # 如果返回的是Response对象，获取其JSON数据
        if hasattr(response, 'get_json'):
            data = response.get_json()
        else:
            import json
            data = json.loads(response[0])
        
        if not data.get('success'):
            return jsonify({
                'success': False,
                'message': '获取买点数据失败',
                'error': data.get('error', 'Unknown error')
            }), 500
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        # 提取买点信号
        signals_data = data.get('data', {})
        buy_signals = signals_data.get('signals', [])
        
        # 按买点类型分组
        buy_point_1 = [s for s in buy_signals if s.get('buy_point') == 1]
        buy_point_2 = [s for s in buy_signals if s.get('buy_point') == 2]
        buy_point_3 = [s for s in buy_signals if s.get('buy_point') == 3]
        
        # 简化信号数据
        def simplify_signal(signal):
            return {
                'symbol': signal.get('symbol'),
                'buy_point': signal.get('buy_point'),
                'current_price': signal.get('current_price'),
                'suggested_position': signal.get('suggested_position'),
                'buy_times': signal.get('buy_times'),
                'distance_to_support': signal.get('distance_to_support_1'),
                'conditions_met': signal.get('conditions_met'),
                'score_display': signal.get('score_display'),
                'sar_position': signal.get('sar_position'),
                'rsi_5m': signal.get('rsi_5m'),
                'rsi_1h': signal.get('rsi_1h'),
                'recommended': signal.get('recommended', False)
            }
        
        result = {
            'success': True,
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_signals': len(buy_signals),
                'buy_point_1_count': len(buy_point_1),
                'buy_point_2_count': len(buy_point_2),
                'buy_point_3_count': len(buy_point_3)
            },
            'buy_points': {
                'buy_point_1': [simplify_signal(s) for s in buy_point_1],
                'buy_point_2': [simplify_signal(s) for s in buy_point_2],
                'buy_point_3': [simplify_signal(s) for s in buy_point_3]
            },
            'all_signals': [simplify_signal(s) for s in buy_signals],
            'rules': signals_data.get('buy_point_rules', {})
        }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"获取买点信号失败: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': '获取买点信号失败',
            'error': str(e)
        }), 500

@app.route('/api/trading-signals/history')
def api_trading_signals_history():
    """获取历史信号（已失效的信号）"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        import pytz
        
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        # 获取最近7天内失效的信号
        seven_days_ago = now - timedelta(days=7)
        
        cursor.execute('''
            SELECT signal_key, symbol, buy_point_type, suggested_position,
                   first_triggered_at, last_updated_at
            FROM trading_signal_history
            WHERE is_active = 0
              AND last_updated_at >= ?
            ORDER BY last_updated_at DESC
            LIMIT 50
        ''', (seven_days_ago.strftime('%Y-%m-%d %H:%M:%S'),))
        
        history_signals = []
        for row in cursor.fetchall():
            # 计算信号持续时间
            first_time = datetime.strptime(row['first_triggered_at'], '%Y-%m-%d %H:%M:%S')
            last_time = datetime.strptime(row['last_updated_at'], '%Y-%m-%d %H:%M:%S')
            duration_minutes = int((last_time - first_time).total_seconds() / 60)
            
            buy_point_name = {
                'buy_point_1': '买点1',
                'buy_point_2': '买点2',
                'buy_point_3': '买点3'
            }.get(row['buy_point_type'], '未知')
            
            history_signals.append({
                'symbol': row['symbol'],
                'buy_point_type': buy_point_name,
                'suggested_position': row['suggested_position'],
                'initial_position': str(int(float(row['suggested_position'].replace('%', '')) * 0.3)) + '%',
                'first_triggered_at': row['first_triggered_at'],
                'last_updated_at': row['last_updated_at'],
                'duration_minutes': duration_minutes
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'history_signals': history_signals,
                'total_count': len(history_signals),
                'update_time': now.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/support-resistance/latest')
def api_support_resistance_latest():
    """获取最新的支撑压力线数据"""
    try:
        conn = sqlite3.connect('support_resistance.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取最新的快照数据
        cursor.execute('''
            SELECT 
                snapshot_time,
                scenario_1_coins,
                scenario_2_coins,
                scenario_3_coins,
                scenario_4_coins
            FROM support_resistance_snapshots
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        snapshot_row = cursor.fetchone()
        
        import json
        
        # 获取实时数据的最新更新时间（不依赖快照）
        cursor.execute('''
            SELECT MAX(record_time) as latest_time
            FROM support_resistance_levels
        ''')
        latest_row = cursor.fetchone()
        update_time = latest_row['latest_time'] if latest_row and latest_row['latest_time'] else None
        
        if not update_time:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'No data available'
            })
        
        # 获取所有监控的币种（27个）
        MONITORED_SYMBOLS = [
            'BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'XRP-USDT-SWAP', 'BNB-USDT-SWAP',
            'SOL-USDT-SWAP', 'LTC-USDT-SWAP', 'DOGE-USDT-SWAP', 'SUI-USDT-SWAP',
            'TRX-USDT-SWAP', 'TON-USDT-SWAP', 'ETC-USDT-SWAP', 'BCH-USDT-SWAP',
            'HBAR-USDT-SWAP', 'XLM-USDT-SWAP', 'FIL-USDT-SWAP', 'LINK-USDT-SWAP',
            'CRO-USDT-SWAP', 'DOT-USDT-SWAP', 'AAVE-USDT-SWAP', 'UNI-USDT-SWAP',
            'NEAR-USDT-SWAP', 'APT-USDT-SWAP', 'CFX-USDT-SWAP', 'CRV-USDT-SWAP',
            'STX-USDT-SWAP', 'LDO-USDT-SWAP', 'TAO-USDT-SWAP'
        ]
        
        # 获取每个币种的最新价格
        placeholders = ','.join(['?' for _ in MONITORED_SYMBOLS])
        cursor.execute(f'''
            SELECT symbol, close as current_price, timestamp
            FROM okex_kline_ohlc
            WHERE timeframe = '5m'
            AND symbol IN ({placeholders})
            AND (symbol, timestamp) IN (
                SELECT symbol, MAX(timestamp)
                FROM okex_kline_ohlc
                WHERE timeframe = '5m'
                AND symbol IN ({placeholders})
                GROUP BY symbol
            )
            ORDER BY symbol
        ''', MONITORED_SYMBOLS + MONITORED_SYMBOLS)
        
        price_rows = cursor.fetchall()
        price_dict = {row['symbol']: row['current_price'] for row in price_rows}
        
        # 解析4种情况的币种数据，构建alert字典
        alert_dict = {}
        if snapshot_row:  # 只有当快照存在时才解析
            for scenario_num in range(1, 5):
                coins_json = snapshot_row[f'scenario_{scenario_num}_coins']
                if coins_json:
                    try:
                        coins = json.loads(coins_json)
                        for coin in coins:
                            symbol = coin['symbol']
                            if symbol not in alert_dict:
                                alert_dict[symbol] = {
                                    'support_1': 0,
                                    'support_2': 0,
                                    'resistance_1': 0,
                                    'resistance_2': 0,
                                    'position_s2_r1': None,
                                    'position_s1_r2': None,
                                    'position_s1_r2_upper': None,
                                    'position_s1_r1': None,
                                    'alert_scenario_1': False,
                                    'alert_scenario_2': False,
                                    'alert_scenario_3': False,
                                    'alert_scenario_4': False
                                }
                            
                            # 从当前币种数据中更新支撑/压力线值（合并所有场景的数据）
                            if 'support_1' in coin and coin['support_1']:
                                alert_dict[symbol]['support_1'] = coin['support_1']
                            if 'support_2' in coin and coin['support_2']:
                                alert_dict[symbol]['support_2'] = coin['support_2']
                            if 'resistance_1' in coin and coin['resistance_1']:
                                alert_dict[symbol]['resistance_1'] = coin['resistance_1']
                            if 'resistance_2' in coin and coin['resistance_2']:
                                alert_dict[symbol]['resistance_2'] = coin['resistance_2']
                            
                            # 设置对应情况的alert和position
                            if scenario_num == 1:
                                alert_dict[symbol]['alert_scenario_1'] = True
                                alert_dict[symbol]['position_s2_r1'] = coin.get('position', 0)
                            elif scenario_num == 2:
                                alert_dict[symbol]['alert_scenario_2'] = True
                                alert_dict[symbol]['position_s1_r2'] = coin.get('position', 0)
                            elif scenario_num == 3:
                                alert_dict[symbol]['alert_scenario_3'] = True
                                alert_dict[symbol]['position_s1_r2_upper'] = coin.get('position', 0)
                            elif scenario_num == 4:
                                alert_dict[symbol]['alert_scenario_4'] = True
                                alert_dict[symbol]['position_s1_r1'] = coin.get('position', 0)
                    except:
                        pass
        
        # 获取所有币种的支撑/压力线数据（从support_resistance_levels表）
        # 将币种格式从 'BTC-USDT-SWAP' 转换为 'BTCUSDT'
        symbols_for_levels = [s.replace('-USDT-SWAP', 'USDT') for s in MONITORED_SYMBOLS]
        placeholders_levels = ','.join(['?' for _ in symbols_for_levels])
        
        # Get the latest record for each symbol using a subquery
        cursor.execute(f'''
            SELECT srl.symbol, srl.current_price, srl.support_line_1, srl.support_line_2, 
                   srl.resistance_line_1, srl.resistance_line_2,
                   srl.position_7d, srl.position_48h,
                   srl.alert_7d_low, srl.alert_7d_high,
                   srl.alert_48h_low, srl.alert_48h_high,
                   srl.support_1_days, srl.support_2_hours,
                   srl.resistance_1_days, srl.resistance_2_hours,
                   srl.baseline_price_24h, srl.price_change_24h, srl.change_percent_24h
            FROM support_resistance_levels srl
            INNER JOIN (
                SELECT symbol, MAX(record_time) as max_time
                FROM support_resistance_levels
                WHERE symbol IN ({placeholders_levels})
                GROUP BY symbol
            ) latest ON srl.symbol = latest.symbol AND srl.record_time = latest.max_time
        ''', symbols_for_levels)
        
        sr_levels_rows = cursor.fetchall()
        sr_levels_dict = {}
        for row in sr_levels_rows:
            symbol = row['symbol']  # 已经是 BTCUSDT 格式
            sr_levels_dict[symbol] = {
                'current_price': row['current_price'] or 0,  # 从数据库读取current_price
                'support_1': row['support_line_1'] or 0,
                'support_2': row['support_line_2'] or 0,
                'resistance_1': row['resistance_line_1'] or 0,
                'resistance_2': row['resistance_line_2'] or 0,
                'position_7d': row['position_7d'] or 0,
                'position_48h': row['position_48h'] or 0,
                'alert_7d_low': row['alert_7d_low'] or False,
                'alert_7d_high': row['alert_7d_high'] or False,
                'alert_48h_low': row['alert_48h_low'] or False,
                'alert_48h_high': row['alert_48h_high'] or False,
                'support_1_days': row['support_1_days'] or 0,
                'support_2_hours': row['support_2_hours'] or 0,
                'resistance_1_days': row['resistance_1_days'] or 0,
                'resistance_2_hours': row['support_2_hours'] or 0,
                'baseline_price_24h': row['baseline_price_24h'] or 0,
                'price_change_24h': row['price_change_24h'] or 0,
                'change_percent_24h': row['change_percent_24h'] or 0
            }
        
        # 构建结果：所有27个币种
        result_data = []
        for symbol in MONITORED_SYMBOLS:
            alert_info = alert_dict.get(symbol, {})
            symbol_usdt = symbol.replace('-USDT-SWAP', 'USDT')
            
            # 优先使用alert_info中的支撑/压力线数据，如果没有则使用sr_levels_dict中的数据
            sr_data = sr_levels_dict.get(symbol_usdt, {})
            # 使用数据库中的current_price，而不是实时查询的价格（保持数据一致性）
            current_price = sr_data.get('current_price', 0) or price_dict.get(symbol, 0)
            support_1 = alert_info.get('support_1', 0) or sr_data.get('support_1', 0)
            support_2 = alert_info.get('support_2', 0) or sr_data.get('support_2', 0)
            resistance_1 = alert_info.get('resistance_1', 0) or sr_data.get('resistance_1', 0)
            resistance_2 = alert_info.get('resistance_2', 0) or sr_data.get('resistance_2', 0)
            
            # 计算距离百分比（使用实时价格）
            distance_to_support_1 = ((current_price - support_1) / support_1) * 100 if support_1 > 0 else 0
            distance_to_support_2 = ((current_price - support_2) / support_2) * 100 if support_2 > 0 else 0
            distance_to_resistance_1 = ((resistance_1 - current_price) / current_price) * 100 if current_price > 0 else 0
            distance_to_resistance_2 = ((resistance_2 - current_price) / current_price) * 100 if current_price > 0 else 0
            
            coin_data = {
                'symbol': symbol_usdt,
                'current_price': current_price,
                'support_line_1': support_1,
                'support_line_2': support_2,
                'resistance_line_1': resistance_1,
                'resistance_line_2': resistance_2,
                'distance_to_support_1': distance_to_support_1,
                'distance_to_support_2': distance_to_support_2,
                'distance_to_resistance_1': distance_to_resistance_1,
                'distance_to_resistance_2': distance_to_resistance_2,
                'position_7d': sr_data.get('position_7d', 0),  # 7天位置百分比
                'position_48h': sr_data.get('position_48h', 0),  # 48小时位置百分比
                'support_1_days': sr_data.get('support_1_days', 0),  # 7天最低价发生在N天前
                'support_2_hours': sr_data.get('support_2_hours', 0),  # 48h最低价发生在N小时前
                'resistance_1_days': sr_data.get('resistance_1_days', 0),  # 7天最高价发生在N天前
                'resistance_2_hours': sr_data.get('resistance_2_hours', 0),  # 48h最高价发生在N小时前
                'alert_7d_low': sr_data.get('alert_7d_low', False),  # 7天低位预警
                'alert_7d_high': sr_data.get('alert_7d_high', False),  # 7天高位预警
                'alert_48h_low': sr_data.get('alert_48h_low', False),  # 48h低位预警
                'alert_48h_high': sr_data.get('alert_48h_high', False),  # 48h高位预警
                'baseline_price_24h': sr_data.get('baseline_price_24h', 0),  # 今日基准价格（北京时间0点）
                'price_change_24h': sr_data.get('price_change_24h', 0),  # 24小时涨跌额
                'change_percent_24h': sr_data.get('change_percent_24h', 0),  # 24小时涨跌幅%
                'position_s2_r1': alert_info.get('position_s2_r1'),
                'position_s1_r2': alert_info.get('position_s1_r2'),
                'position_s1_r2_upper': alert_info.get('position_s1_r2_upper'),
                'position_s1_r1': alert_info.get('position_s1_r1'),
                'alert_scenario_1': alert_info.get('alert_scenario_1', False),
                'alert_scenario_2': alert_info.get('alert_scenario_2', False),
                'alert_scenario_3': alert_info.get('alert_scenario_3', False),
                'alert_scenario_4': alert_info.get('alert_scenario_4', False),
                'alert_triggered': any([
                    alert_info.get('alert_scenario_1', False),
                    alert_info.get('alert_scenario_2', False),
                    alert_info.get('alert_scenario_3', False),
                    alert_info.get('alert_scenario_4', False)
                ]),
                'record_time': update_time
            }
            result_data.append(coin_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': result_data,
            'count': len(result_data),
            'update_time': update_time
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/support-resistance/history/<symbol>')
def api_support_resistance_history(symbol):
    """获取指定币种的历史支撑压力线数据"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        conn = sqlite3.connect('support_resistance.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                symbol,
                current_price,
                support_line_1,
                support_line_2,
                resistance_line_1,
                resistance_line_2,
                distance_to_support_1,
                distance_to_support_2,
                distance_to_resistance_1,
                distance_to_resistance_2,
                record_time
            FROM support_resistance_levels
            WHERE symbol = ?
            AND datetime(record_time) >= datetime('now', '+8 hours', ? || ' hours')
            ORDER BY record_time DESC
        ''', (symbol, -hours))
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'symbol': row['symbol'],
                'current_price': row['current_price'],
                'support_line_1': row['support_line_1'],
                'support_line_2': row['support_line_2'],
                'resistance_line_1': row['resistance_line_1'],
                'resistance_line_2': row['resistance_line_2'],
                'distance_to_support_1': row['distance_to_support_1'],
                'distance_to_support_2': row['distance_to_support_2'],
                'distance_to_resistance_1': row['distance_to_resistance_1'],
                'distance_to_resistance_2': row['distance_to_resistance_2'],
                'record_time': row['record_time']
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/support-resistance/snapshots')
def api_support_resistance_snapshots():
    """获取支撑压力线快照历史数据（用于时间轴和趋势图）"""
    try:
        import json
        from datetime import datetime, timedelta
        import pytz
        
        date = request.args.get('date')  # 格式: 2025-12-13
        start_hour = request.args.get('start_hour', type=int)  # 0-23
        end_hour = request.args.get('end_hour', type=int)  # 0-23
        start_time = request.args.get('start_time')  # 格式: 2025-12-13 00:00:00
        end_time = request.args.get('end_time')  # 格式: 2025-12-13 12:00:00
        get_all = request.args.get('all', 'false').lower() == 'true'  # 获取所有历史数据
        
        conn = sqlite3.connect('support_resistance.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        if get_all:
            # 获取所有历史数据（用于全局趋势图）
            cursor.execute('''
                SELECT 
                    snapshot_time, snapshot_date,
                    scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
                    scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
                    total_coins
                FROM support_resistance_snapshots
                ORDER BY snapshot_time ASC
            ''')
        elif start_time and end_time:
            # 获取指定时间范围的数据（用于翻页查看）
            cursor.execute('''
                SELECT 
                    snapshot_time, snapshot_date,
                    scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
                    scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
                    total_coins
                FROM support_resistance_snapshots
                WHERE snapshot_time >= ? AND snapshot_time < ?
                ORDER BY snapshot_time ASC
            ''', (start_time, end_time))
        elif date and start_hour is not None and end_hour is not None:
            # 🆕 支持按小时范围查询（北京时间）
            # 注意：数据库存储的已经是北京时间，直接使用即可
            
            # 构造北京时间范围字符串
            beijing_start_str = f"{date} {start_hour:02d}:00:00"
            
            # 处理 end_hour = 24 的情况（24:00 = 次日 00:00）
            if end_hour >= 24:
                from datetime import timedelta
                beijing_start_dt = datetime.strptime(beijing_start_str, "%Y-%m-%d %H:%M:%S")
                beijing_end_dt = beijing_start_dt + timedelta(hours=(end_hour - start_hour))
                beijing_end_str = beijing_end_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                beijing_end_str = f"{date} {end_hour:02d}:00:00"
            
            cursor.execute('''
                SELECT 
                    snapshot_time, snapshot_date,
                    scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
                    scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
                    total_coins
                FROM support_resistance_snapshots
                WHERE snapshot_time >= ? AND snapshot_time < ?
                ORDER BY snapshot_time ASC
            ''', (beijing_start_str, beijing_end_str))
        elif date:
            # 获取指定日期的所有数据
            cursor.execute('''
                SELECT 
                    snapshot_time, snapshot_date,
                    scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
                    scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
                    total_coins
                FROM support_resistance_snapshots
                WHERE snapshot_date = ?
                ORDER BY snapshot_time ASC
            ''', (date,))
        else:
            # 获取最近12小时的数据
            cursor.execute('''
                SELECT 
                    snapshot_time, snapshot_date,
                    scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
                    scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
                    total_coins
                FROM support_resistance_snapshots
                WHERE snapshot_time >= datetime('now', '-12 hours')
                ORDER BY snapshot_time ASC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # 数据库中存储的已经是北京时间，直接使用
        data = []
        for row in rows:
            data.append({
                'snapshot_time': row['snapshot_time'],  # 数据库存储的是北京时间
                'snapshot_date': row['snapshot_date'],
                'scenario_1_count': row['scenario_1_count'],
                'scenario_2_count': row['scenario_2_count'],
                'scenario_3_count': row['scenario_3_count'],
                'scenario_4_count': row['scenario_4_count'],
                'scenario_1_coins': json.loads(row['scenario_1_coins']) if row['scenario_1_coins'] else [],
                'scenario_2_coins': json.loads(row['scenario_2_coins']) if row['scenario_2_coins'] else [],
                'scenario_3_coins': json.loads(row['scenario_3_coins']) if row['scenario_3_coins'] else [],
                'scenario_4_coins': json.loads(row['scenario_4_coins']) if row['scenario_4_coins'] else [],
                'total_coins': row['total_coins']
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'date': date,
            'start_time': start_time,
            'end_time': end_time
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/support-resistance/latest-signal')
def api_support_resistance_latest_signal():
    """获取最新快照数据并检测是否触发信号"""
    try:
        import json
        from datetime import datetime
        import pytz
        
        conn = sqlite3.connect('support_resistance.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取最新的实时数据时间（从support_resistance_levels表）
        cursor.execute('''
            SELECT MAX(record_time) as latest_time
            FROM support_resistance_levels
        ''')
        
        time_row = cursor.fetchone()
        latest_time = time_row['latest_time'] if time_row else None
        
        # 获取最新的快照（如果有）
        cursor.execute('''
            SELECT 
                snapshot_time, snapshot_date,
                scenario_1_count, scenario_2_count, scenario_3_count, scenario_4_count,
                scenario_1_coins, scenario_2_coins, scenario_3_coins, scenario_4_coins,
                total_coins
            FROM support_resistance_snapshots
            ORDER BY snapshot_time DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'message': '暂无快照数据'
            })
        
        # 使用实时数据的最新时间，而不是快照时间
        snapshot_time_str = latest_time if latest_time else row['snapshot_time']
        
        scenario_1 = row['scenario_1_count'] or 0
        scenario_2 = row['scenario_2_count'] or 0
        scenario_3 = row['scenario_3_count'] or 0
        scenario_4 = row['scenario_4_count'] or 0
        
        # 检测信号
        # 抄底信号：情况1 >= 8 AND 情况2 >= 8（两个条件都要满足）
        buy_signal = scenario_1 >= 8 and scenario_2 >= 8
        
        # 逃顶信号：(情况3 + 情况4) >= 8（总和满足即可）
        sell_signal = (scenario_3 + scenario_4) >= 8
        
        result = {
            'success': True,
            'snapshot_time': snapshot_time_str,  # 直接使用数据库中的北京时间
            'snapshot_date': row['snapshot_date'],
            'scenario_1_count': scenario_1,
            'scenario_2_count': scenario_2,
            'scenario_3_count': scenario_3,
            'scenario_4_count': scenario_4,
            'scenario_1_coins': json.loads(row['scenario_1_coins']) if row['scenario_1_coins'] else [],
            'scenario_2_coins': json.loads(row['scenario_2_coins']) if row['scenario_2_coins'] else [],
            'scenario_3_coins': json.loads(row['scenario_3_coins']) if row['scenario_3_coins'] else [],
            'scenario_4_coins': json.loads(row['scenario_4_coins']) if row['scenario_4_coins'] else [],
            'total_coins': row['total_coins'],
            'signals': {
                'buy': buy_signal,
                'sell': sell_signal,
                'buy_count': scenario_1 + scenario_2 if buy_signal else 0,
                'sell_count': scenario_3 + scenario_4 if sell_signal else 0
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/support-resistance/dates')
def api_support_resistance_dates():
    """获取有快照数据的所有日期列表"""
    try:
        conn = sqlite3.connect('support_resistance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT snapshot_date
            FROM support_resistance_snapshots
            ORDER BY snapshot_date DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        dates = [row[0] for row in rows]
        
        return jsonify({
            'success': True,
            'dates': dates,
            'count': len(dates)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

# =====================================================
# 逃顶信号系统 API路由
# =====================================================

@app.route('/escape-top-signals')
def escape_top_signals_page():
    """逃顶信号监控页面"""
    response = make_response(render_template('escape_top_signals.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/escape-top-signals/latest')
def api_escape_top_signals_latest():
    """获取最新的逃顶信号数据 - 直接从support_resistance_levels查询"""
    try:
        conn = sqlite3.connect('crypto_data.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 直接从support_resistance_levels表查询24小时内有逃顶倾向的数据
        cursor.execute('''
            SELECT 
                symbol,
                record_time as signal_time,
                current_price,
                resistance_line_1,
                resistance_line_2,
                distance_to_resistance_1 as distance_to_r1,
                distance_to_resistance_2 as distance_to_r2,
                alert_scenario_3 as scenario_3_count,
                alert_scenario_4 as scenario_4_count,
                (alert_scenario_3 + alert_scenario_4) as total_escape_score,
                CASE WHEN (alert_scenario_3 + alert_scenario_4) >= 8 THEN 1 ELSE 0 END as is_escape_signal,
                position_48h,
                position_7d,
                price_change_24h,
                change_percent_24h,
                alert_triggered
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', '-24 hours')
              AND (alert_scenario_3 > 0 OR alert_scenario_4 > 0)
            ORDER BY record_time DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'symbol': row['symbol'],
                'signal_time': row['signal_time'],
                'current_price': row['current_price'],
                'resistance_line_1': row['resistance_line_1'],
                'resistance_line_2': row['resistance_line_2'],
                'distance_to_r1': row['distance_to_r1'],
                'distance_to_r2': row['distance_to_r2'],
                'scenario_3_count': row['scenario_3_count'],
                'scenario_4_count': row['scenario_4_count'],
                'total_escape_score': row['total_escape_score'],
                'is_escape_signal': row['is_escape_signal'],
                'position_48h': row['position_48h'],
                'position_7d': row['position_7d'],
                'price_change_24h': row['price_change_24h'],
                'change_percent_24h': row['change_percent_24h'],
                'alert_triggered': row['alert_triggered']
            })
        
        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        })

@app.route('/api/escape-top-signals/history/<symbol>')
def api_escape_top_signals_history(symbol):
    """获取指定币种的历史逃顶信号"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                signal_time,
                current_price,
                total_escape_score,
                is_escape_signal,
                position_48h,
                position_7d
            FROM escape_top_signals_24h
            WHERE symbol = ?
              AND datetime(signal_time) >= datetime('now', ? || ' hours')
            ORDER BY signal_time ASC
        ''', (symbol, f'-{hours}'))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'signal_time': row['signal_time'],
                'current_price': row['current_price'],
                'total_escape_score': row['total_escape_score'],
                'is_escape_signal': row['is_escape_signal'],
                'position_48h': row['position_48h'],
                'position_7d': row['position_7d']
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': history,
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        })

@app.route('/api/escape-top-signals/stats')
def api_escape_top_signals_stats():
    """获取逃顶信号统计数据 - 返回真实的逃顶事件次数"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        conn = sqlite3.connect('crypto_data.db', timeout=30.0)
        cursor = conn.cursor()
        
        # 逃顶事件次数（统计不同时间点的逃顶事件数量）
        # 条件：alert_triggered=1 且 (情况3+情况4)>=8 且 情况3>=1 且 情况4>=1
        cursor.execute('''
            SELECT COUNT(DISTINCT strftime('%Y-%m-%d %H:%M', record_time)) as event_count
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', ? || ' hours')
              AND alert_triggered = 1
              AND (alert_scenario_3 + alert_scenario_4) >= 8
              AND alert_scenario_3 >= 1
              AND alert_scenario_4 >= 1
        ''', (f'-{hours}',))
        total_escape_events = cursor.fetchone()[0]
        
        # 触发信号的币种数
        cursor.execute('''
            SELECT COUNT(DISTINCT symbol) as coin_count
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', ? || ' hours')
              AND alert_triggered = 1
              AND (alert_scenario_3 + alert_scenario_4) >= 8
              AND alert_scenario_3 >= 1
              AND alert_scenario_4 >= 1
        ''', (f'-{hours}',))
        coin_count = cursor.fetchone()[0]
        
        # 平均逃顶分数
        cursor.execute('''
            SELECT AVG(alert_scenario_3 + alert_scenario_4) as avg_score
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', ? || ' hours')
              AND (alert_scenario_3 > 0 OR alert_scenario_4 > 0)
        ''', (f'-{hours}',))
        avg_score = cursor.fetchone()[0] or 0
        
        # 按币种统计
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as signal_count,
                AVG(alert_scenario_3 + alert_scenario_4) as avg_score,
                MAX(alert_scenario_3 + alert_scenario_4) as max_score
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', ? || ' hours')
              AND (alert_scenario_3 > 0 OR alert_scenario_4 > 0)
            GROUP BY symbol
            ORDER BY signal_count DESC
        ''', (f'-{hours}',))
        
        by_symbol = []
        for row in cursor.fetchall():
            by_symbol.append({
                'symbol': row[0],
                'signal_count': row[1],
                'avg_score': round(row[2], 2),
                'max_score': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_signals': total_escape_events,  # 真实的逃顶事件次数
                'active_coins': coin_count,
                'avg_escape_score': round(avg_score, 2),
                'by_symbol': by_symbol
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/escape-top-signals/history-timeseries')
def api_escape_top_signals_history_timeseries():
    """获取逃顶信号的历史时间序列数据（每5分钟统计一次）- 北京时间"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        conn = sqlite3.connect('crypto_data.db', timeout=30.0)
        cursor = conn.cursor()
        
        # 按5分钟间隔统计逃顶信号数量（UTC转北京时间+8小时）
        cursor.execute('''
            SELECT 
                datetime(
                    strftime('%Y-%m-%d %H:', datetime(record_time, '+8 hours')) || 
                    printf('%02d', (CAST(strftime('%M', datetime(record_time, '+8 hours')) AS INTEGER) / 5) * 5) ||
                    ':00'
                ) as time_slot,
                COUNT(DISTINCT symbol) as unique_symbols
            FROM support_resistance_levels
            WHERE datetime(record_time) >= datetime('now', ? || ' hours')
              AND (alert_scenario_3 > 0 OR alert_scenario_4 > 0)
            GROUP BY time_slot
            ORDER BY time_slot ASC
        ''', (f'-{hours}',))
        
        timeseries = []
        for row in cursor.fetchall():
            timeseries.append({
                'time': row[0],  # 已经包含完整时间格式
                'count': row[1]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': timeseries,
            'count': len(timeseries),
            'timezone': '北京时间 (UTC+8)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        })

@app.route('/api/escape-event-stats/timeseries')
def api_escape_event_stats_timeseries():
    """获取逃顶事件统计的时间序列数据（从JSON文件读取）"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        # 从JSON文件读取数据
        import json
        import os
        from datetime import datetime, timedelta
        
        data_file = 'escape_event_stats.json'
        timeseries = []
        
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
                
            # 过滤指定小时数的数据
            cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:00')
            timeseries = [item for item in data if item['time'] >= cutoff_time]
        
        return jsonify({
            'success': True,
            'data': timeseries,
            'count': len(timeseries),
            'timezone': '北京时间 (UTC+8)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        })

# =====================================================
# OKEx K线指标系统 API路由
# =====================================================

@app.route('/kline-indicators')
def kline_indicators_page():
    """K线指标系统监控页面"""
    return render_template('kline_indicators.html')

@app.route('/api/kline-indicators/latest')
def api_kline_indicators_latest():
    """
    获取最新的技术指标数据
    
    参数：
        - symbol: 币种（可选，如BTC-USDT-SWAP）
        - timeframe: 时间周期（可选，5m或1h）
    """
    try:
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe')
        
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if symbol:
            conditions.append('symbol = ?')
            params.append(symbol)
        if timeframe:
            conditions.append('timeframe = ?')
            params.append(timeframe)
        
        # 构建WHERE子句
        if conditions:
            where_clause = f"WHERE {' AND '.join(conditions)} AND"
        else:
            where_clause = "WHERE"
        
        # 获取每个币种+时间周期的最新数据
        cursor.execute(f'''
            SELECT 
                symbol, timeframe, current_price, rsi_14, 
                sar, sar_position, sar_quadrant, sar_count_label,
                bb_upper, bb_middle, bb_lower, record_time
            FROM okex_technical_indicators
            {where_clause} id IN (
                SELECT MAX(id)
                FROM okex_technical_indicators
                GROUP BY symbol, timeframe
            )
            ORDER BY symbol, timeframe
        ''', params)
        
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'symbol': row['symbol'],
                'timeframe': row['timeframe'],
                'current_price': row['current_price'],
                'rsi_14': row['rsi_14'],
                'sar': row['sar'],
                'sar_position': row['sar_position'],
                'sar_quadrant': row['sar_quadrant'],
                'sar_count_label': row['sar_count_label'],
                'bb_upper': row['bb_upper'],
                'bb_middle': row['bb_middle'],
                'bb_lower': row['bb_lower'],
                'record_time': row['record_time']
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'timestamp': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/kline-indicators/collector-status')
def api_kline_indicators_status():
    """获取采集器运行状态"""
    try:
        conn = sqlite3.connect('crypto_data.db', timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取最新采集时间
        cursor.execute('''
            SELECT MAX(record_time) as last_collection
            FROM okex_technical_indicators
        ''')
        row = cursor.fetchone()
        last_collection = row['last_collection'] if row else None
        
        # 统计数据量
        cursor.execute('SELECT COUNT(*) as count_indicators FROM okex_technical_indicators')
        count_indicators = cursor.fetchone()['count_indicators']
        
        # 统计不同时间周期的数量
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN timeframe = '5m' THEN 1 ELSE 0 END) as count_5m,
                SUM(CASE WHEN timeframe = '1H' THEN 1 ELSE 0 END) as count_1h
            FROM okex_technical_indicators
        ''')
        row = cursor.fetchone()
        count_5m = row['count_5m'] or 0
        count_1h = row['count_1h'] or 0
        
        conn.close()
        
        # 计算状态（数据库存储的是北京时间）
        if last_collection:
            # 数据库中的时间是北京时间，需要与北京时间比较
            import pytz
            beijing_tz = pytz.timezone('Asia/Shanghai')
            last_time = datetime.strptime(last_collection, '%Y-%m-%d %H:%M:%S')
            now_beijing = datetime.now(beijing_tz).replace(tzinfo=None)
            delta_minutes = (now_beijing - last_time).total_seconds() / 60
            status = 'running' if delta_minutes < 10 else 'stopped'
        else:
            status = 'not_started'
            delta_minutes = None
        
        return jsonify({
            'success': True,
            'status': status,
            'last_collection_time': last_collection,
            'minutes_since_last': round(delta_minutes, 1) if delta_minutes else None,
            'data_counts': {
                'kline_5m': count_5m,
                'kline_1h': count_1h,
                'indicators': count_indicators
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def cleanup_expired_signals():
    """
    清理2小时之前的过期信号
    将 is_valid 设置为 0
    """
    try:
        conn = sqlite3.connect('crypto_data.db', timeout=5.0)
        cursor = conn.cursor()
        
        from datetime import datetime, timedelta
        cutoff_time = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 清理买点4过期信号
        cursor.execute('''
            UPDATE buy_point_4_signals
            SET is_valid = 0
            WHERE is_valid = 1 AND confirm_time < ?
        ''', (cutoff_time,))
        buy_point_4_cleaned = cursor.rowcount
        
        # 清理卖点1过期信号
        cursor.execute('''
            UPDATE sell_point_1_signals
            SET is_valid = 0
            WHERE is_valid = 1 AND mark_time < ?
        ''', (cutoff_time,))
        sell_point_1_cleaned = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            'buy_point_4_cleaned': buy_point_4_cleaned,
            'sell_point_1_cleaned': sell_point_1_cleaned
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/api/kline-indicators/signals')
def api_kline_indicators_signals():
    """
    返回K线指标信号（2小时时间窗口）
    数据完全从数据库读取，不进行实时检测
    - 买点4: 从 buy_point_4_signals 表读取（RSI < 20）
    - 卖点1: 从 sell_point_1_signals 表读取（RSI >= 60）
    """
    try:
        conn = sqlite3.connect('crypto_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        from datetime import datetime, timedelta
        now = datetime.now()
        cutoff_time = (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 初始化信号容器
        signals = {
            'buy_point_4': [],      # 买点4（从数据库读取）
            'sell_point_1': []      # 卖点1（从数据库读取）
        }
        
        # 1. 读取买点4信号（不查询当前价格，使用信号时的价格）
        cursor.execute('''
            SELECT symbol, low_price, low_time, confirm_time, 
                   signal_generated_at, confirm_rsi
            FROM buy_point_4_signals
            WHERE is_valid = 1 
              AND confirm_rsi IS NOT NULL 
              AND confirm_rsi < 20
              AND confirm_time >= ?
            ORDER BY confirm_time DESC
            LIMIT 100
        ''', (cutoff_time,))
        
        for row in cursor.fetchall():
            signals['buy_point_4'].append({
                'symbol': row[0],
                'price': row[1],
                'low_7d': row[1],
                'low_time': row[2],
                'confirm_time': row[3],
                'signal_generated_at': row[4],
                'confirm_rsi': row[5],
                'current_price': row[1],  # 使用确认时的价格
                'distance': 0.0  # 信号时刻距离为0
            })
        
        # 2. 读取卖点1信号（不查询当前价格）
        cursor.execute('''
            SELECT symbol, high_price, high_time, mark_price, 
                   mark_time, mark_rsi, signal_generated_at
            FROM sell_point_1_signals
            WHERE is_valid = 1 
              AND mark_rsi IS NOT NULL 
              AND mark_rsi >= 60
              AND mark_time >= ?
            ORDER BY mark_time DESC
            LIMIT 100
        ''', (cutoff_time,))
        
        for row in cursor.fetchall():
            signals['sell_point_1'].append({
                'symbol': row[0],
                'high_price': row[1],
                'high_time': row[2],
                'mark_price': row[3],
                'mark_time': row[4],
                'mark_rsi': row[5],
                'signal_generated_at': row[6],
                'current_price': row[3],  # 使用标记时的价格
                'distance': 0.0  # 信号时刻距离为0
            })
        
        conn.close()
        
        # 统计信号数量
        signal_counts = {k: len(v) for k, v in signals.items()}
        
        # 异步清理过期信号（不阻塞响应）
        import threading
        threading.Thread(target=cleanup_expired_signals, daemon=True).start()
        
        return jsonify({
            'success': True,
            'data': {
                'signals': signals,
                'counts': signal_counts,
                'update_time': now.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/kline-indicators-tv/latest')
def api_kline_indicators_tv_latest():
    """
    获取TradingView直接获取的K线指标数据（不计算）
    支持参数: symbol, timeframe
    数据源: TradingView (OKX交易所)
    """
    try:
        symbol = request.args.get('symbol')
        timeframe = request.args.get('timeframe')
        
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if symbol:
            conditions.append('symbol = ?')
            params.append(symbol)
        if timeframe:
            conditions.append('timeframe = ?')
            params.append(timeframe)
        
        # 构建WHERE子句
        if conditions:
            where_clause = f"WHERE {' AND '.join(conditions)}"
        else:
            where_clause = ""
        
        # 获取每个币种+时间周期的最新数据
        query = f'''
            SELECT 
                symbol, timeframe, current_price, rsi_14, 
                sar, bb_upper, bb_middle, bb_lower,
                ema_10, ema_20, recommendation,
                buy_signals, sell_signals, neutral_signals,
                record_time
            FROM okex_tv_indicators
            {where_clause}
            ORDER BY symbol, timeframe
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            # Calculate SAR position
            sar_position = None
            if row['sar'] and row['current_price']:
                sar_position = 'bullish' if row['current_price'] > row['sar'] else 'bearish'
            
            # Calculate BB middle if not provided
            bb_middle = row['bb_middle']
            if not bb_middle and row['bb_upper'] and row['bb_lower']:
                bb_middle = (row['bb_upper'] + row['bb_lower']) / 2
            
            data.append({
                'symbol': row['symbol'],
                'timeframe': row['timeframe'],
                'current_price': row['current_price'],
                'rsi_14': row['rsi_14'],
                'sar': row['sar'],
                'sar_position': sar_position,
                'bb_upper': row['bb_upper'],
                'bb_middle': bb_middle,
                'bb_lower': row['bb_lower'],
                'ema_10': row['ema_10'],
                'ema_20': row['ema_20'],
                'recommendation': row['recommendation'],
                'buy_signals': row['buy_signals'],
                'sell_signals': row['sell_signals'],
                'neutral_signals': row['neutral_signals'],
                'record_time': row['record_time'],
                'data_source': 'TradingView (直接获取, 不计算)'
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'data_source': 'TradingView API (OKX Exchange)',
            'note': '所有技术指标均直接从TradingView获取，不进行本地计算',
            'timestamp': datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/kline-indicators-tv/collector-status')
def api_kline_indicators_tv_status():
    """获取TradingView指标采集器运行状态"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='okex_tv_collector_status'
        ''')
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': True,
                'status': 'not_initialized',
                'message': 'TradingView collector not initialized yet'
            })
        
        # 获取采集状态
        cursor.execute('''
            SELECT last_collect_time, total_indicators_count, status
            FROM okex_tv_collector_status
            WHERE id = 1
        ''')
        
        row = cursor.fetchone()
        
        # 统计数据量
        cursor.execute('SELECT COUNT(*) FROM okex_tv_indicators')
        count_indicators = cursor.fetchone()[0]
        
        conn.close()
        
        status = row['status'] if row else 'stopped'
        last_collection = row['last_collect_time'] if row else None
        
        return jsonify({
            'success': True,
            'status': status,
            'last_collection_time': last_collection,
            'total_indicators': count_indicators,
            'data_source': 'TradingView (直接获取)',
            'note': 'RSI, SAR, 布林带均直接从TradingView获取，不计算'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 币种详情页面 ====================

@app.route('/symbol/<symbol>')
def symbol_detail(symbol):
    """币种详情页面 - 自动重定向到v6以避开浏览器缓存"""
    from flask import redirect, url_for
    return redirect(url_for('symbol_detail_v6', symbol=symbol), code=302)

@app.route('/api/symbol/<symbol>/kline')
def api_symbol_kline(symbol):
    """获取币种K线数据（10天）- 使用okex_technical_indicators表"""
    try:
        timeframe = request.args.get('timeframe', '5m')  # 5m 或 1H
        
        # 将symbol转换为标准格式
        if not symbol.endswith('-USDT-SWAP'):
            symbol = f"{symbol}-USDT-SWAP"
        
        # 转换timeframe格式: 5m -> 5m, 1h -> 1H (数据库中使用大写H)
        db_timeframe = timeframe.upper() if timeframe == '1h' else timeframe
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 根据时间周期设置limit
        if timeframe == '5m':
            # 10天的5分钟K线 = 10 * 24 * 12 = 2880根
            limit = 2880
        else:  # 1h
            # 10天的1小时K线 = 10 * 24 = 240根
            limit = 240
        
        # 从okex_kline_ohlc表获取真实的OHLC K线数据
        # 先按时间降序取最新的N条，然后反转为升序
        cursor.execute('''
            SELECT timestamp, open, high, low, close, volume
            FROM (
                SELECT timestamp, open, high, low, close, volume
                FROM okex_kline_ohlc
                WHERE symbol = ? AND timeframe = ?
                ORDER BY timestamp DESC
                LIMIT ?
            )
            ORDER BY timestamp ASC
        ''', (symbol, db_timeframe, limit))
        
        rows = cursor.fetchall()
        
        # 如果OHLC表没有数据，回退到indicators_history表
        if not rows:
            cursor.execute('''
                SELECT timestamp, current_price
                FROM (
                    SELECT timestamp, current_price
                    FROM okex_indicators_history
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
                ORDER BY timestamp ASC
            ''', (symbol, db_timeframe, limit))
            
            rows_indicators = cursor.fetchall()
            kline_data = []
            
            for i, row in enumerate(rows_indicators):
                timestamp = int(row[0]) if row[0] else 0
                close_price = float(row[1]) if row[1] else 0
                
                # 模拟OHLC
                open_price = close_price * (1 + 0.001 * (i % 3 - 1))
                high_price = close_price * 1.002
                low_price = close_price * 0.998
                volume = close_price * 10
                
                kline_data.append({
                    'timestamp': timestamp,
                    'data': [open_price, high_price, low_price, close_price],  # 标准K线格式: OHLC
                    'volume': volume
                })
        else:
            # 使用真实OHLC数据
            kline_data = []
            for row in rows:
                timestamp = int(row[0]) if row[0] else 0
                open_price = float(row[1]) if row[1] else 0
                high_price = float(row[2]) if row[2] else 0
                low_price = float(row[3]) if row[3] else 0
                close_price = float(row[4]) if row[4] else 0
                volume = float(row[5]) if row[5] else 0
                
                kline_data.append({
                    'timestamp': timestamp,
                    'data': [open_price, high_price, low_price, close_price],  # 标准K线格式: OHLC
                    'volume': volume
                })
        
        # 查询技术标记数据（窄幅震荡、高低点、SAR、RSI、布林带等）
        cursor.execute('''
            SELECT timestamp, is_narrow_range, change_percent, range_percent, consecutive_count,
                   is_7d_high, is_7d_low, is_48h_high, is_48h_low,
                   rsi_14, sar, sar_position, sar_quadrant, sar_count_label,
                   bb_upper, bb_middle, bb_lower, is_buy_point_4
            FROM kline_technical_markers
            WHERE symbol = ? AND timeframe = ?
            ORDER BY timestamp ASC
        ''', (symbol, db_timeframe))
        
        marker_rows = cursor.fetchall()
        markers_dict = {}
        for marker_row in marker_rows:
            ts = int(marker_row[0]) if marker_row[0] else 0
            markers_dict[ts] = {
                'is_narrow_range': bool(marker_row[1]),
                'change_percent': float(marker_row[2]) if marker_row[2] else 0,
                'range_percent': float(marker_row[3]) if marker_row[3] else 0,
                'consecutive_count': int(marker_row[4]) if marker_row[4] else 0,
                'is_7d_high': bool(marker_row[5]),
                'is_7d_low': bool(marker_row[6]),
                'is_48h_high': bool(marker_row[7]),
                'is_48h_low': bool(marker_row[8]),
                'rsi_14': float(marker_row[9]) if marker_row[9] else None,
                'sar': float(marker_row[10]) if marker_row[10] else None,
                'sar_position': marker_row[11],
                'sar_quadrant': int(marker_row[12]) if marker_row[12] else None,
                'sar_count_label': marker_row[13],
                'bb_upper': float(marker_row[14]) if marker_row[14] else None,
                'bb_middle': float(marker_row[15]) if marker_row[15] else None,
                'bb_lower': float(marker_row[16]) if marker_row[16] else None,
                'is_buy_point_4': bool(marker_row[17])
            }
        
        # 将标记数据合并到K线数据中
        for item in kline_data:
            ts = item['timestamp']
            if ts in markers_dict:
                item['markers'] = markers_dict[ts]
        
        conn.close()
        
        # 创建响应对象并添加缓存头
        response = jsonify({
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'data': kline_data,
            'count': len(kline_data)
        })
        
        # 添加HTTP缓存头（缓存60秒，因为数据每60秒更新一次）
        response.headers['Cache-Control'] = 'public, max-age=60'
        response.headers['Vary'] = 'Accept-Encoding'
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/symbol/<symbol>/indicators')
def api_symbol_indicators(symbol):
    """获取币种技术指标数据 - 使用okex_technical_indicators表"""
    try:
        timeframe = request.args.get('timeframe', '5m')
        
        # 将symbol转换为标准格式
        if not symbol.endswith('-USDT-SWAP'):
            symbol = f"{symbol}-USDT-SWAP"
        
        # 转换timeframe格式: 5m -> 5m, 1h -> 1H
        db_timeframe = timeframe.upper() if timeframe == '1h' else timeframe
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 设置limit
        limit = 2880 if timeframe == '5m' else 240
        
        # 从okex_indicators_history表获取历史指标数据
        cursor.execute('''
            SELECT created_at, current_price, rsi_14, sar, sar_position, sar_count_label,
                   bb_upper, bb_middle, bb_lower, timestamp
            FROM okex_indicators_history
            WHERE symbol = ? AND timeframe = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (symbol, db_timeframe, limit))
        
        rows = cursor.fetchall()
        
        indicators = []
        for row in rows:
            # 使用数据库中的timestamp字段（毫秒）
            timestamp = int(row[9]) if row[9] else 0
            
            indicators.append({
                'timestamp': timestamp,
                'price': float(row[1]) if row[1] else None,
                'rsi': float(row[2]) if row[2] else None,
                'sar': float(row[3]) if row[3] else None,
                'sar_position': row[4],
                'sar_label': row[5],
                'bb_upper': float(row[6]) if row[6] else None,
                'bb_middle': float(row[7]) if row[7] else None,
                'bb_lower': float(row[8]) if row[8] else None,
                'time_str': row[0]  # 保留时间字符串用于调试
            })
        
        conn.close()
        
        # 创建响应对象并添加缓存头
        response = jsonify({
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'data': indicators,
            'count': len(indicators)
        })
        
        # 添加HTTP缓存头（缓存60秒，因为数据每60秒更新一次）
        response.headers['Cache-Control'] = 'public, max-age=60'
        response.headers['Vary'] = 'Accept-Encoding'
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/signals/recent')
def api_signals_recent():
    """获取最近2小时内的交易信号，按类型分类"""
    try:
        from datetime import datetime, timedelta
        import json
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 计算2小时前的时间
        two_hours_ago = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取2小时内的信号
        cursor.execute('''
            SELECT record_time, long_signals, short_signals, 
                   today_new_high, today_new_low, raw_data
            FROM trading_signals
            WHERE record_time >= ?
            ORDER BY record_time DESC
        ''', (two_hours_ago,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 分类统计
        signals_by_type = {
            'long': [],  # 做多信号
            'short': [],  # 做空信号
            'new_high': [],  # 新高信号
            'new_low': []  # 新低信号
        }
        
        for row in rows:
            record_time = row[0]
            long_count = row[1] or 0
            short_count = row[2] or 0
            new_high = row[3] or 0
            new_low = row[4] or 0
            raw_data = json.loads(row[5]) if row[5] else {}
            
            if long_count > 0:
                signals_by_type['long'].append({
                    'time': record_time,
                    'count': long_count,
                    'detail': raw_data.get('breakdown', {})
                })
            
            if short_count > 0:
                signals_by_type['short'].append({
                    'time': record_time,
                    'count': short_count,
                    'detail': raw_data.get('breakdown', {})
                })
            
            if new_high > 0:
                signals_by_type['new_high'].append({
                    'time': record_time,
                    'count': new_high
                })
            
            if new_low > 0:
                signals_by_type['new_low'].append({
                    'time': record_time,
                    'count': new_low
                })
        
        # 计算汇总
        summary = {
            'long_total': sum(s['count'] for s in signals_by_type['long']),
            'short_total': sum(s['count'] for s in signals_by_type['short']),
            'new_high_total': sum(s['count'] for s in signals_by_type['new_high']),
            'new_low_total': sum(s['count'] for s in signals_by_type['new_low']),
            'time_range': two_hours_ago
        }
        
        return jsonify({
            'success': True,
            'signals': signals_by_type,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/symbol/<symbol>/extremes')
def api_symbol_extremes(symbol):
    """获取币种的48小时和7天高低点"""
    try:
        from datetime import datetime, timedelta
        
        timeframe = request.args.get('timeframe', '5m')
        
        # 将symbol转换为标准格式
        if not symbol.endswith('-USDT-SWAP'):
            symbol = f"{symbol}-USDT-SWAP"
        
        # 转换timeframe格式
        db_timeframe = timeframe.upper() if timeframe == '1h' else timeframe
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 计算时间范围（毫秒时间戳）
        now_ms = int(datetime.now().timestamp() * 1000)
        hours_48_ago_ms = int((datetime.now() - timedelta(hours=48)).timestamp() * 1000)
        days_7_ago_ms = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        
        # 获取48小时内的高低点
        cursor.execute('''
            SELECT timestamp, open, high, low, close
            FROM okex_kline_ohlc
            WHERE symbol = ? AND timeframe = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (symbol, db_timeframe, hours_48_ago_ms))
        
        rows_48h = cursor.fetchall()
        
        # 获取7天内的高低点
        cursor.execute('''
            SELECT timestamp, open, high, low, close
            FROM okex_kline_ohlc
            WHERE symbol = ? AND timeframe = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (symbol, db_timeframe, days_7_ago_ms))
        
        rows_7d = cursor.fetchall()
        conn.close()
        
        # 计算48小时高低点
        extremes_48h = {'high': None, 'low': None, 'high_time': None, 'low_time': None}
        if rows_48h:
            max_price = max(row[2] for row in rows_48h)  # high
            min_price = min(row[3] for row in rows_48h)  # low
            
            for row in rows_48h:
                if row[2] == max_price:
                    extremes_48h['high'] = max_price
                    extremes_48h['high_time'] = row[0]
                if row[3] == min_price:
                    extremes_48h['low'] = min_price
                    extremes_48h['low_time'] = row[0]
        
        # 计算7天高低点
        extremes_7d = {'high': None, 'low': None, 'high_time': None, 'low_time': None}
        if rows_7d:
            max_price = max(row[2] for row in rows_7d)  # high
            min_price = min(row[3] for row in rows_7d)  # low
            
            for row in rows_7d:
                if row[2] == max_price:
                    extremes_7d['high'] = max_price
                    extremes_7d['high_time'] = row[0]
                if row[3] == min_price:
                    extremes_7d['low'] = min_price
                    extremes_7d['low_time'] = row[0]
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'timeframe': timeframe,
            'extremes_48h': extremes_48h,
            'extremes_7d': extremes_7d
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/test-chart')
def test_chart():
    """测试K线图渲染"""
    with open('test_chart_render.html', 'r', encoding='utf-8') as f:
        return f.read()

# ==================== 新版本路由 - 强制刷新 ====================

@app.route('/symbol/<symbol>/v6')
def symbol_detail_v6(symbol):
    """币种详情页面 v6.0 - 全新路由避开缓存"""
    from datetime import datetime
    from flask import make_response
    
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    response = make_response(render_template('symbol_detail_v6.html', symbol=symbol, cache_buster=cache_buster))
    
    # 禁用HTML页面缓存，确保每次都加载最新代码
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/symbol/<symbol>/v7')
def symbol_detail_v7(symbol):
    """币种详情页面 v7.0 - 全新路由避开缓存，简化调试"""
    from datetime import datetime
    from flask import make_response
    
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    response = make_response(render_template('symbol_detail_v7.html', symbol=symbol, cache_buster=cache_buster))
    
    # 禁用HTML页面缓存，确保每次都加载最新代码
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/symbol/<symbol>/v8')
def symbol_detail_v8(symbol):
    """币种详情页面 v8.0 - 彻底避开所有浏览器缓存"""
    from datetime import datetime
    from flask import make_response
    
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    response = make_response(render_template('symbol_detail_v8.html', symbol=symbol, cache_buster=cache_buster))
    
    # 最强缓存禁用策略
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    return response

@app.route('/kline/<symbol>')
def kline_chart(symbol):
    """全新的K线图路由 - 完全独立的地址"""
    from datetime import datetime
    from flask import make_response
    
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    response = make_response(render_template('kline_chart.html', symbol=symbol, cache_buster=cache_buster))
    
    # 强制禁用所有缓存
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    return response

@app.route('/test-xlm-data')
def test_xlm_data():
    """XLM数据诊断测试页"""
    return render_template('test_xlm_data.html')

@app.route('/chart/<symbol>')
def chart_new(symbol):
    """全新K线图 - 从零开始，简单清晰"""
    from datetime import datetime
    from flask import make_response
    
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    response = make_response(render_template('chart_new.html', symbol=symbol, cache_buster=cache_buster))
    
    # 强制禁用所有缓存
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# ==================== Google Drive 监控状态 API ====================

@app.route('/gdrive-monitor-status')
def gdrive_monitor_status_page():
    """Google Drive 监控状态页面 - 11分钟超时保险机制可视化"""
    return render_template('gdrive_monitor_status.html')

@app.route('/api/gdrive-monitor/status')
def api_gdrive_monitor_status():
    """获取 Google Drive 监控状态的实时数据"""
    import os
    import json
    from datetime import datetime
    import pytz
    import re
    import requests
    from bs4 import BeautifulSoup
    
    try:
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        
        # 读取配置文件
        config_file = '/home/user/webapp/daily_folder_config.json'
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 🆕 扫描 Google Drive 中的实际文件
        gdrive_dates = {}
        gdrive_scan_error = None
        try:
            ROOT_FOLDER_ID = "1jFGGlGP5KEVhAxpCNxFIYEFI5-cDOBjM"
            url = f"https://drive.google.com/embeddedfolderview?id={ROOT_FOLDER_ID}"
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            all_links = soup.find_all('a', href=True)
            pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(\d{4})\.txt')
            
            for link in all_links:
                text = link.get_text(strip=True)
                match = pattern.match(text)
                if match:
                    date = match.group(1)
                    if date not in gdrive_dates:
                        gdrive_dates[date] = 0
                    gdrive_dates[date] += 1
        except Exception as e:
            gdrive_scan_error = str(e)
        
        # 读取日志文件获取最新状态
        log_file = '/home/user/webapp/gdrive_final_detector.log'
        latest_file = None
        latest_file_time = None
        check_count = 0
        last_file_found_time = None
        recovery_count = 0
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 分析日志
                for line in reversed(lines[-500:]):  # 只看最近500行
                    # 查找最新文件
                    if '最新文件名 =' in line and not latest_file:
                        match = re.search(r'最新文件名 = (.+\.txt)', line)
                        if match:
                            latest_file = match.group(1)
                            # 提取时间戳
                            time_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                            if time_match:
                                latest_file_time = time_match.group(1)
                    
                    # 查找检查次数
                    if '检查 #' in line:
                        match = re.search(r'检查 #(\d+)', line)
                        if match:
                            check_count = max(check_count, int(match.group(1)))
                    
                    # 查找恢复触发
                    if '触发11分钟超时恢复机制' in line:
                        recovery_count += 1
                    
                    # 查找最后找到文件的时间
                    if '找到' in line and 'TXT文件' in line and not last_file_found_time:
                        match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
                        if match:
                            last_file_found_time = match.group(1)
        
        # 计算距上次找到文件的时间
        time_since_last_file = 0
        if last_file_found_time:
            try:
                last_time = datetime.strptime(last_file_found_time, '%Y-%m-%d %H:%M:%S')
                last_time = beijing_tz.localize(last_time)
                time_since_last_file = (now - last_time).total_seconds()
            except:
                pass
        
        # 获取数据库记录数
        db_records = 0
        try:
            import sqlite3
            conn = sqlite3.connect('databases/crypto_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crypto_snapshots WHERE snapshot_date = ?", (now.strftime('%Y-%m-%d'),))
            db_records = cursor.fetchone()[0]
            conn.close()
        except:
            pass
        
        # 计算系统运行时长 (从最早的日志时间戳开始)
        uptime_seconds = 0
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', first_line)
                if match:
                    start_time = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                    start_time = beijing_tz.localize(start_time)
                    uptime_seconds = (now - start_time).total_seconds()
        
        # 🆕 判断数据源状态
        today_str = now.strftime('%Y-%m-%d')
        data_source_status = 'unknown'
        data_source_message = ''
        
        if gdrive_dates:
            latest_gdrive_date = max(gdrive_dates.keys())
            if latest_gdrive_date == today_str:
                data_source_status = 'active'
                data_source_message = f'✅ 数据源正常，今天有 {gdrive_dates[today_str]} 个文件'
            else:
                days_old = (datetime.strptime(today_str, '%Y-%m-%d') - datetime.strptime(latest_gdrive_date, '%Y-%m-%d')).days
                data_source_status = 'stale'
                data_source_message = f'⚠️  数据源已停更 {days_old} 天，最新数据：{latest_gdrive_date}'
        elif gdrive_scan_error:
            data_source_status = 'error'
            data_source_message = f'❌ 无法访问 Google Drive: {gdrive_scan_error}'
        else:
            data_source_status = 'empty'
            data_source_message = '❌ Google Drive 中没有任何数据文件'
        
        return jsonify({
            'success': True,
            'time_since_last_file': time_since_last_file,
            'current_folder_id': config.get('folder_id', 'N/A'),
            'folder_date': config.get('current_date', '--'),
            'latest_file': latest_file or '--',
            'file_time': latest_file_time or '--',
            'gdrive_dates': gdrive_dates,  # 🆕 Google Drive 中的日期分布
            'data_source_status': data_source_status,  # 🆕 数据源状态
            'data_source_message': data_source_message,  # 🆕 数据源状态消息
            'today_date': today_str,  # 🆕 当前日期
            'root_folder_odd': config.get('root_folder_odd', 'N/A'),  # 🆕 单数日期父文件夹
            'root_folder_even': config.get('root_folder_even', 'N/A'),  # 🆕 双数日期父文件夹
            'recovery_count': recovery_count,
            'check_count': check_count,
            'files_found': check_count,  # 简化处理
            'db_records': db_records,
            'last_update': now.strftime('%H:%M:%S'),
            'uptime_seconds': uptime_seconds,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 每日00:10任务状态 API ====================

@app.route('/daily-tasks-status')
def daily_tasks_status_page():
    """每日00:10任务执行状态页面"""
    return render_template('daily_tasks_status.html')

@app.route('/api/daily-tasks/status')
def api_daily_tasks_status():
    """获取每日00:10任务的执行状态"""
    import os
    import json
    from datetime import datetime
    import pytz
    
    try:
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        today_str = now.strftime('%Y-%m-%d')
        
        # 读取配置文件
        config_file = '/home/user/webapp/daily_folder_config.json'
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # 父文件夹更新任务状态
        parent_folder_update = {
            'status': config.get('auto_update_status', 'pending'),
            'last_update': config.get('last_auto_update', '--'),
            'parent_folder_id': config.get('root_folder_odd') or config.get('root_folder_even', '--'),
            'child_folder_id': config.get('folder_id', '--'),
            'url': config.get('parent_folder_url', '--')
        }
        
        # 清理任务状态
        cleanup = {
            'last_cleanup': config.get('last_cleanup', None),
            'cleanup_reason': config.get('cleanup_reason', '--'),
            'root_folder_odd': config.get('root_folder_odd'),
            'root_folder_even': config.get('root_folder_even')
        }
        
        return jsonify({
            'success': True,
            'today_date': today_str,
            'parent_folder_update': parent_folder_update,
            'cleanup': cleanup
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/daily-tasks/logs')
def api_daily_tasks_logs():
    """获取每日任务的执行日志"""
    import os
    
    try:
        log_file = '/home/user/webapp/parent_folder_update.log'
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 只返回最近100行
                logs = [line.rstrip() for line in lines[-100:]]
        
        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 文件夹更新监控 API ====================

@app.route('/folder-update-monitor')
def folder_update_monitor():
    """文件夹更新监控页面"""
    return render_template('folder_update_monitor.html')

@app.route('/api/folder-update-status')
def api_folder_update_status():
    """获取文件夹更新状态"""
    import os
    import json
    
    try:
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(beijing_tz)
        today_str = now.strftime('%Y-%m-%d')
        
        # 读取配置文件
        config_file = '/home/user/webapp/daily_folder_config.json'
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        config_date = config.get('current_date', 'unknown')
        need_update = config_date != today_str
        
        return jsonify({
            'success': True,
            'data': {
                'config_date': config_date,
                'today_date': today_str,
                'folder_id': config.get('folder_id', 'N/A'),
                'latest_txt': config.get('latest_txt', 'N/A'),
                'txt_count': config.get('txt_count', 0),
                'last_updated': config.get('last_updated', 'N/A'),
                'need_update': need_update,
                'message': '配置日期与今天不匹配' if need_update else '配置正常'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/trigger-folder-update', methods=['POST'])
def api_trigger_folder_update():
    """触发文件夹更新"""
    import subprocess
    import os
    
    try:
        script_path = '/home/user/webapp/auto_update_today_folder.py'
        
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'message': '更新脚本不存在'
            }), 404
        
        # 执行更新脚本
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # 读取更新后的配置
            config_file = '/home/user/webapp/daily_folder_config.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return jsonify({
                'success': True,
                'data': {
                    'folder_id': config.get('folder_id'),
                    'date': config.get('current_date'),
                    'latest_txt': config.get('latest_txt'),
                    'txt_count': config.get('txt_count', 0)
                },
                'message': '更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'更新失败: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': '更新超时（60秒）'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/list-recent-folders')
def api_list_recent_folders():
    """列出最近的文件夹"""
    import requests
    from bs4 import BeautifulSoup
    import re
    
    try:
        parent_folder_id = "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV"
        url = f"https://drive.google.com/embeddedfolderview?id={parent_folder_id}"
        
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        folders = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if '/folders/' in href:
                match = re.search(r'/folders/([a-zA-Z0-9_-]+)', href)
                if match:
                    folder_id = match.group(1)
                    # 检查是否是日期文件夹
                    if re.search(r'\d{4}-\d{2}-\d{2}', text):
                        folders.append({
                            'name': text,
                            'id': folder_id
                        })
        
        # 排序（最新的在前）
        folders.sort(key=lambda x: x['name'], reverse=True)
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        today = datetime.now(beijing_tz).strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'data': {
                'folders': folders[:10],  # 只返回最近10个
                'today': today
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/get-update-log')
def api_get_update_log():
    """获取更新日志"""
    import os
    
    try:
        log_file = '/home/user/webapp/auto_update_folder.log'
        log_content = ''
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 只返回最近200行
                log_content = ''.join(lines[-200:])
        
        return jsonify({
            'success': True,
            'data': {
                'log': log_content or '暂无日志'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 旧的telegram-dashboard路由已废弃，使用下方新版本
# @app.route('/telegram-dashboard')
# def telegram_dashboard():
#     """Telegram信号推送系统监控面板"""
#     import time
#     cache_buster = int(time.time())
#     return render_template('telegram_dashboard.html', cache_buster=cache_buster)

@app.route('/api/telegram/status')
def telegram_status():
    """获取Telegram监控系统状态"""
    try:
        import subprocess
        import os
        
        # 检查进程是否运行（检查telegram_signal_system.py而不是tg_signal_monitor.py）
        result = subprocess.run(
            ['pgrep', '-f', 'telegram_signal_system.py'],
            capture_output=True,
            text=True
        )
        
        is_running = bool(result.stdout.strip())
        pid = result.stdout.strip() if is_running else None
        
        # 获取数据库统计
        db_stats = {}
        if os.path.exists('tg_signals.db'):
            conn = sqlite3.connect('tg_signals.db', timeout=5.0)
            cursor = conn.cursor()
            
            # 获取总发送数
            cursor.execute("SELECT COUNT(*) FROM signal_history")
            total_sent = cursor.fetchone()[0]
            
            # 获取最近1小时发送数
            cursor.execute("""
                SELECT COUNT(*) FROM signal_history 
                WHERE sent_time >= datetime('now', '-1 hour', 'localtime')
            """)
            sent_1h = cursor.fetchone()[0]
            
            # 获取今天发送数
            cursor.execute("""
                SELECT COUNT(*) FROM signal_history 
                WHERE date(sent_time) = date('now', 'localtime')
            """)
            sent_today = cursor.fetchone()[0]
            
            # 获取各类信号统计
            cursor.execute("""
                SELECT signal_type, COUNT(*) as count
                FROM signal_history
                GROUP BY signal_type
            """)
            signal_counts = dict(cursor.fetchall())
            
            # 获取最新发送时间
            cursor.execute("""
                SELECT sent_time FROM signal_history 
                ORDER BY created_at DESC LIMIT 1
            """)
            last_sent = cursor.fetchone()
            last_sent_time = last_sent[0] if last_sent else None
            
            conn.close()
            
            db_stats = {
                'total_sent': total_sent,
                'sent_1h': sent_1h,
                'sent_today': sent_today,
                'signal_counts': signal_counts,
                'last_sent_time': last_sent_time
            }
        
        # 返回扁平化的数据结构，符合前端期待的格式
        return jsonify({
            'success': True,
            'is_running': is_running,
            'pid': pid,
            'status': '运行中' if is_running else '未运行',
            'total_sent': db_stats.get('total_sent', 0),
            'sent_1h': db_stats.get('sent_1h', 0),
            'sent_today': db_stats.get('sent_today', 0),
            'last_sent_time': db_stats.get('last_sent_time'),
            'last_update': db_stats.get('last_sent_time', '未知'),
            'signal_counts': signal_counts,
            'last_messages': [],  # 前端需要的字段
            # 同时保留嵌套格式以兼容其他可能的调用
            'data': {
                'is_running': is_running,
                'pid': pid,
                'database_stats': db_stats
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/telegram/history')
def telegram_history():
    """获取Telegram信号发送历史"""
    try:
        import os
        
        if not os.path.exists('tg_signals.db'):
            return jsonify({
                'success': False,
                'error': '数据库不存在'
            }), 404
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        signal_type = request.args.get('type', '')
        
        conn = sqlite3.connect('tg_signals.db', timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询
        where_clause = ""
        params = []
        if signal_type:
            where_clause = "WHERE signal_type = ?"
            params.append(signal_type)
        
        # 获取总数
        cursor.execute(f"SELECT COUNT(*) FROM signal_history {where_clause}", params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * limit
        cursor.execute(f"""
            SELECT id, signal_type, symbol, signal_name, signal_data, sent_time, created_at
            FROM signal_history
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row['id'],
                'signal_type': row['signal_type'],
                'symbol': row['symbol'],
                'signal_name': row['signal_name'],
                'signal_data': row['signal_data'],
                'sent_time': row['sent_time'],
                'created_at': row['created_at']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'records': records,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/coins/realtime-status')
def api_coins_realtime_status():
    """
    获取所有币种的实时状态
    包括：当前价格（来自最新K线）、7天高低点、涨跌幅、交易信号及发生时间
    """
    try:
        import pytz
        conn = sqlite3.connect('crypto_data.db', timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        beijing_tz = pytz.timezone('Asia/Shanghai')
        
        # 定义27个币种
        symbols = [
            'AAVE', 'APT', 'BCH', 'BNB', 'BTC', 'CRV', 'DOGE', 'DOT', 'ETC', 'ETH', 'FIL',
            'HBAR', 'LDO', 'LINK', 'LTC', 'NEAR', 'SOL', 'SUI', 'TAO', 'TON', 'TRX',
            'XLM', 'XRP', 'CFX', 'CRO', 'STX', 'UNI'
        ]
        
        results = []
        
        for symbol_short in symbols:
            symbol = f"{symbol_short}-USDT-SWAP"
            
            # 1. 获取最新K线数据（当前价格）
            cursor.execute('''
                SELECT timestamp, close, open
                FROM okex_kline_ohlc
                WHERE symbol = ? AND timeframe = '5m'
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (symbol,))
            latest_kline = cursor.fetchone()
            
            if not latest_kline:
                continue
            
            current_price = latest_kline['close']
            open_price = latest_kline['open']
            latest_time = datetime.fromtimestamp(latest_kline['timestamp'] / 1000, tz=beijing_tz)
            
            # 计算涨跌幅
            change_pct = ((current_price - open_price) / open_price * 100) if open_price > 0 else 0
            
            # 2. 获取7天高低点
            cursor.execute('''
                SELECT MAX(high) as high_7d, MIN(low) as low_7d
                FROM okex_kline_ohlc
                WHERE symbol = ? AND timeframe = '5m'
                AND timestamp >= ?
            ''', (symbol, int((datetime.now() - timedelta(days=7)).timestamp() * 1000)))
            extremes = cursor.fetchone()
            
            high_7d = extremes['high_7d'] if extremes and extremes['high_7d'] else current_price
            low_7d = extremes['low_7d'] if extremes and extremes['low_7d'] else current_price
            
            # 3. 检查最近2小时的交易信号
            two_hours_ago = datetime.now(beijing_tz) - timedelta(hours=2)
            
            cursor.execute('''
                SELECT record_time, long_signals, short_signals, today_new_high, today_new_low
                FROM trading_signals
                WHERE record_time >= ?
                ORDER BY record_time DESC
                LIMIT 1
            ''', (two_hours_ago.strftime('%Y-%m-%d %H:%M:%S'),))
            signal_row = cursor.fetchone()
            
            signal_type = None
            signal_time = None
            
            if signal_row:
                signal_time_dt = datetime.strptime(signal_row['record_time'], '%Y-%m-%d %H:%M:%S')
                signal_time_dt = beijing_tz.localize(signal_time_dt)
                signal_time = signal_time_dt.strftime('%m-%d %H:%M')
                
                # 判断信号类型
                if signal_row['long_signals'] > 0 or signal_row['today_new_low'] > 0:
                    signal_type = 'buy'
                elif signal_row['short_signals'] > 0 or signal_row['today_new_high'] > 0:
                    signal_type = 'sell'
            
            results.append({
                'symbol': symbol_short,
                'current_price': current_price,
                'high_7d': high_7d,
                'low_7d': low_7d,
                'change_pct': change_pct,
                'signal_type': signal_type,  # 'buy' or 'sell' or None
                'signal_time': signal_time,  # K线时间，格式：'MM-DD HH:MM'
                'latest_update': latest_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results),
            'timestamp': datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sell-point-1/save', methods=['POST'])
def api_sell_point_1_save():
    """
    保存卖点1信号到数据库
    
    请求体格式:
    {
        "symbol": "BTC",
        "high_price": 90000.0,
        "high_time": "2025-12-15 14:30:00",
        "high_index": 1000,
        "mark_price": 89500.0,
        "mark_time": "2025-12-15 15:00:00",
        "mark_index": 1006,
        "mark_rsi": 65.5
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        # 验证必需字段
        required_fields = ['symbol', 'high_price', 'high_time', 'high_index', 
                          'mark_price', 'mark_time', 'mark_index', 'mark_rsi']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 检查是否已存在相同的信号（避免重复插入）
        cursor.execute('''
            SELECT id FROM sell_point_1_signals
            WHERE symbol = ? AND mark_time = ? AND is_valid = 1
        ''', (data['symbol'], data['mark_time']))
        
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({
                'success': True,
                'message': '信号已存在',
                'signal_id': existing[0]
            })
        
        # 插入新信号
        now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO sell_point_1_signals (
                symbol, high_price, high_time, high_index,
                mark_price, mark_time, mark_index, mark_rsi,
                signal_generated_at, is_valid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            data['symbol'],
            data['high_price'],
            data['high_time'],
            data['high_index'],
            data['mark_price'],
            data['mark_time'],
            data['mark_index'],
            data['mark_rsi'],
            now
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '卖点1信号保存成功',
            'signal_id': signal_id
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sell-point-1/latest')
def api_sell_point_1_latest():
    """
    获取最新的卖点1信号
    
    参数:
        - symbol: 币种（可选，如BTC）
        - hours: 时间范围（可选，默认24小时）
    """
    try:
        symbol = request.args.get('symbol')
        hours = int(request.args.get('hours', 24))
        
        conn = sqlite3.connect('databases/crypto_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 构建查询
        beijing_tz = pytz.timezone('Asia/Shanghai')
        cutoff_time = (datetime.now(beijing_tz) - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        if symbol:
            cursor.execute('''
                SELECT * FROM sell_point_1_signals
                WHERE symbol = ? AND mark_time >= ? AND is_valid = 1
                ORDER BY mark_time DESC
            ''', (symbol, cutoff_time))
        else:
            cursor.execute('''
                SELECT * FROM sell_point_1_signals
                WHERE mark_time >= ? AND is_valid = 1
                ORDER BY mark_time DESC
            ''', (cutoff_time,))
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'high_price': row['high_price'],
                'high_time': row['high_time'],
                'high_index': row['high_index'],
                'mark_price': row['mark_price'],
                'mark_time': row['mark_time'],
                'mark_index': row['mark_index'],
                'mark_rsi': row['mark_rsi'],
                'signal_generated_at': row['signal_generated_at'],
                'created_at': row['created_at']
            })
        
        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals),
            'timestamp': datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/telegram-dashboard')
def telegram_dashboard():
    """Telegram信号推送系统仪表板"""
    return render_template('telegram_signal_dashboard.html')

@app.route('/cache-help')
def cache_help():
    """缓存清除帮助页面"""
    return render_template('cache_clear_guide.html')

@app.route('/api/telegram/signals/support-resistance')
def api_telegram_support_resistance():
    """获取支撑压力线信号（2小时内）"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('telegram_signals.db')
        cursor = conn.cursor()
        
        # 获取2小时内的信号
        two_hours_ago = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT signal_type, symbol, price, signal_time, sent_at
            FROM support_resistance_signals
            WHERE sent_at >= ?
            ORDER BY sent_at DESC
        ''', (two_hours_ago,))
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'signal_type': row[0],
                'symbol': row[1],
                'price': row[2],
                'signal_time': row[3],
                'sent_at': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'signals': signals,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram/signals/count-alerts')
def api_telegram_count_alerts():
    """获取计次预警（2小时内）"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('telegram_signals.db')
        cursor = conn.cursor()
        
        two_hours_ago = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT record_time, count_value, threshold, full_data, sent_at
            FROM count_alerts
            WHERE sent_at >= ?
            ORDER BY sent_at DESC
        ''', (two_hours_ago,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'record_time': row[0],
                'count_value': row[1],
                'threshold': row[2],
                'full_data': row[3],
                'sent_at': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram/signals/trading')
def api_telegram_trading():
    """获取交易信号（2小时内）"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('telegram_signals.db')
        cursor = conn.cursor()
        
        two_hours_ago = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            SELECT signal_type, symbol, price, signal_time, rsi, sent_at
            FROM trading_signals
            WHERE sent_at >= ?
            ORDER BY sent_at DESC
        ''', (two_hours_ago,))
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'signal_type': row[0],
                'symbol': row[1],
                'price': row[2],
                'signal_time': row[3],
                'rsi': row[4],
                'sent_at': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'signals': signals,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram/signals/stats')
def api_telegram_stats():
    """获取发送统计"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('telegram_signals.db')
        cursor = conn.cursor()
        
        # 总发送数
        cursor.execute('SELECT COUNT(*) FROM support_resistance_signals')
        support_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM count_alerts')
        alert_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM trading_signals')
        trade_count = cursor.fetchone()[0]
        total = support_count + alert_count + trade_count
        
        # 最近1小时
        one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT COUNT(*) FROM support_resistance_signals WHERE sent_at >= ?', (one_hour_ago,))
        support_1h = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM count_alerts WHERE sent_at >= ?', (one_hour_ago,))
        alert_1h = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM trading_signals WHERE sent_at >= ?', (one_hour_ago,))
        trade_1h = cursor.fetchone()[0]
        last_hour = support_1h + alert_1h + trade_1h
        
        # 今日发送
        today_start = datetime.now().strftime('%Y-%m-%d 00:00:00')
        cursor.execute('SELECT COUNT(*) FROM support_resistance_signals WHERE sent_at >= ?', (today_start,))
        support_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM count_alerts WHERE sent_at >= ?', (today_start,))
        alert_today = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM trading_signals WHERE sent_at >= ?', (today_start,))
        trade_today = cursor.fetchone()[0]
        today = support_today + alert_today + trade_today
        
        # 最后推送时间
        cursor.execute('''
            SELECT MAX(sent_at) FROM (
                SELECT sent_at FROM support_resistance_signals
                UNION ALL
                SELECT sent_at FROM count_alerts
                UNION ALL
                SELECT sent_at FROM trading_signals
            )
        ''')
        last_time = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': total,
            'last_hour': last_hour,
            'today': today,
            'last_time': last_time
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram/system/status')
def api_telegram_system_status():
    """获取Telegram推送系统状态"""
    try:
        import subprocess
        # 检查进程是否运行
        result = subprocess.run(['pgrep', '-f', 'telegram_signal_system.py'], 
                               capture_output=True, text=True)
        is_running = bool(result.stdout.strip())
        pid = result.stdout.strip() if is_running else None
        
        return jsonify({
            'success': True,
            'running': is_running,
            'pid': pid,
            'message': '系统运行中' if is_running else '系统未运行'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram/start', methods=['POST'])
def api_telegram_start():
    """启动Telegram推送系统"""
    try:
        import subprocess
        result = subprocess.run(['./start_telegram_signal_system.sh'], 
                               capture_output=True, text=True, cwd='/home/user/webapp')
        return jsonify({
            'success': True,
            'message': '系统已启动',
            'output': result.stdout
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram/stop', methods=['POST'])
def api_telegram_stop():
    """停止Telegram推送系统"""
    try:
        import subprocess
        result = subprocess.run(['./stop_telegram_signal_system.sh'], 
                               capture_output=True, text=True, cwd='/home/user/webapp')
        return jsonify({
            'success': True,
            'message': '系统已停止',
            'output': result.stdout
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/query/latest')
def api_query_latest():
    """获取最新查询数据API（用于计次预警）"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                snapshot_time, rush_up, rush_down, diff, count, ratio, status,
                round_rush_up, round_rush_down, price_lowest, price_newhigh,
                count_score_display, rise_24h_count, fall_24h_count
            FROM crypto_snapshots
            ORDER BY snapshot_date DESC, snapshot_time DESC
            LIMIT 1
        """)
        
        snapshot = cursor.fetchone()
        conn.close()
        
        if not snapshot:
            return jsonify({'success': False, 'error': '暂无数据'})
        
        return jsonify({
            'success': True,
            'data': {
                '运算时间': snapshot[0],
                '急涨': snapshot[1],
                '急跌': snapshot[2],
                '差值': snapshot[3],
                '计次': snapshot[4],
                '比值': snapshot[5],
                '状态': snapshot[6],
                '本轮急涨': snapshot[7],
                '本轮急跌': snapshot[8],
                '比价最低': snapshot[9],
                '比价创新高': snapshot[10],
                '计次得分': snapshot[11],
                '24h涨≥10%': snapshot[12],
                '24h跌≤-10%': snapshot[13]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/support-resistance/export', methods=['POST'])
def api_support_resistance_export():
    """导出支撑阻力位数据"""
    try:
        import subprocess
        import os
        
        script_path = '/home/user/webapp/export_support_resistance_data.py'
        
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': '导出脚本不存在'
            })
        
        # 执行导出脚本
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': '导出失败',
                'output': result.stderr
            })
        
        # 从输出中提取导出文件路径
        export_file = None
        for line in result.stdout.split('\n'):
            if '导出文件:' in line:
                export_file = line.split('导出文件:')[-1].strip()
                break
        
        if not export_file or not os.path.exists(export_file):
            return jsonify({
                'success': False,
                'error': '找不到导出文件'
            })
        
        # 获取文件信息
        file_size = os.path.getsize(export_file)
        file_size_mb = file_size / (1024 * 1024)
        filename = os.path.basename(export_file)
        
        return jsonify({
            'success': True,
            'message': '导出成功',
            'file_path': export_file,
            'filename': filename,
            'file_size': file_size,
            'file_size_mb': round(file_size_mb, 2),
            'download_url': f'/api/support-resistance/download/{filename}'
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': '导出超时'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/support-resistance/download/<filename>')
def api_support_resistance_download(filename):
    """下载导出的数据文件"""
    try:
        export_dir = '/home/user/webapp/exports'
        file_path = os.path.join(export_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
        
        return send_from_directory(export_dir, filename, as_attachment=True)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/support-resistance/import', methods=['POST'])
def api_support_resistance_import():
    """导入支撑阻力位数据"""
    try:
        import subprocess
        import os
        from werkzeug.utils import secure_filename
        
        # 检查是否有上传的文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            })
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            })
        
        # 检查是否清空现有数据
        clear_existing = request.form.get('clear_existing', 'false').lower() == 'true'
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        upload_dir = '/home/user/webapp/uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # 执行导入脚本
        script_path = '/home/user/webapp/import_support_resistance_data.py'
        
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': '导入脚本不存在'
            })
        
        # 构建命令
        cmd = ['python3', script_path, file_path]
        if clear_existing:
            cmd.append('--clear')
        
        # 执行导入
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 删除上传的临时文件
        try:
            os.remove(file_path)
        except:
            pass
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': '导入失败',
                'output': result.stderr or result.stdout
            })
        
        # 从输出中提取统计信息
        stats = {
            'tables': 0,
            'records': 0
        }
        
        for line in result.stdout.split('\n'):
            if '表数量:' in line:
                try:
                    stats['tables'] = int(line.split(':')[-1].strip())
                except:
                    pass
            elif '总记录数:' in line:
                try:
                    stats['records'] = int(line.split(':')[-1].strip().replace(',', ''))
                except:
                    pass
        
        return jsonify({
            'success': True,
            'message': '导入成功',
            'stats': stats,
            'output': result.stdout
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': '导入超时'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/query/batch-import', methods=['POST'])
def api_query_batch_import():
    """批量导入当天所有TXT文件数据"""
    try:
        import subprocess
        import os
        
        # 执行批量导入脚本
        script_path = '/home/user/webapp/batch_import_daily_txt.py'
        
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': '批量导入脚本不存在'
            })
        
        # 使用subprocess运行脚本
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 解析输出结果
        output_lines = result.stdout.split('\n')
        
        # 提取统计信息
        stats = {
            'total': 0,
            'success': 0,
            'exists': 0,
            'invalid': 0,
            'error': 0
        }
        
        for line in output_lines:
            if '总文件数:' in line:
                stats['total'] = int(line.split(':')[-1].strip())
            elif '成功导入:' in line:
                stats['success'] = int(line.split(':')[-1].strip())
            elif '已存在:' in line:
                stats['exists'] = int(line.split(':')[-1].strip())
            elif '无效数据:' in line:
                stats['invalid'] = int(line.split(':')[-1].strip())
            elif '失败:' in line and '❌' in line:
                stats['error'] = int(line.split(':')[-1].strip())
        
        return jsonify({
            'success': True,
            'message': '批量导入完成',
            'stats': stats,
            'output': result.stdout
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': '批量导入超时（超过5分钟）'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/test-simple')
def test_simple():
    """简单测试页面 - 验证window.onload和ECharts基础功能"""
    return render_template('test_simple.html')

@app.route('/api/chart-config')
def chart_config():
    """获取K线图配置URL"""
    return jsonify({
        'success': True,
        'chart_base_url': CHART_BASE_URL,
        'example': f"{CHART_BASE_URL}/chart/BTC"
    })

@app.route('/gdrive-config')
def gdrive_config():
    """Google Drive配置管理页面"""
    return render_template('gdrive_config.html')

@app.route('/api/gdrive-config/get')
def gdrive_config_get():
    """获取当前Google Drive配置"""
    try:
        import json
        config_file = '/home/user/webapp/daily_folder_config.json'
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/gdrive-config/update', methods=['POST'])
def gdrive_config_update():
    """更新Google Drive文件夹配置"""
    try:
        import json
        from datetime import datetime
        
        data = request.get_json()
        parent_folder_url = data.get('parent_folder_url', '')
        
        if not parent_folder_url:
            return jsonify({
                'success': False,
                'error': '请提供Google Drive文件夹链接'
            }), 400
        
        # 提取文件夹ID
        import re
        folder_id_match = re.search(r'/folders/([a-zA-Z0-9_-]+)', parent_folder_url)
        if not folder_id_match:
            return jsonify({
                'success': False,
                'error': '无法从链接中提取文件夹ID，请检查链接格式'
            }), 400
        
        root_folder_id = folder_id_match.group(1)
        
        # 读取现有配置
        config_file = '/home/user/webapp/daily_folder_config.json'
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            config = {}
        
        # 更新配置
        beijing_time = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        
        # 根据日期判断是单数还是双数
        day_of_month = datetime.now(BEIJING_TZ).day
        is_odd_day = day_of_month % 2 == 1
        
        if is_odd_day:
            config['root_folder_odd'] = root_folder_id
        else:
            config['root_folder_even'] = root_folder_id
        
        config['parent_folder_url'] = parent_folder_url
        config['last_manual_update'] = beijing_time
        config['last_updated'] = beijing_time
        config['update_reason'] = f'手动更新{"单数" if is_odd_day else "双数"}日期父文件夹'
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': f'配置已更新 ({"单数" if is_odd_day else "双数"}日期父文件夹)',
            'config': config
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/gdrive-config/manual-trigger', methods=['POST'])
def gdrive_manual_trigger():
    """手动触发数据采集"""
    try:
        import subprocess
        import os
        
        # 运行gdrive_final_detector.py一次
        script_path = '/home/user/webapp/gdrive_final_detector.py'
        
        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': f'脚本不存在: {script_path}'
            }), 404
        
        # 在后台运行一次检测
        process = subprocess.Popen(
            ['python3', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/home/user/webapp'
        )
        
        # 等待最多5秒
        try:
            stdout, stderr = process.communicate(timeout=5)
            return jsonify({
                'success': True,
                'message': '手动触发成功，数据采集已开始',
                'output': stdout.decode('utf-8', errors='ignore')[:500]
            })
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': True,
                'message': '手动触发成功，数据采集正在后台运行'
            })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/gdrive-config/latest-data')
def gdrive_latest_data():
    """获取最新数据时间和状态"""
    try:
        import sqlite3
        from datetime import datetime
        
        db_path = '/home/user/webapp/crypto_data.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取最新数据
        cursor.execute("""
            SELECT snapshot_time, rush_up, rush_down, count, status, created_at
            FROM crypto_snapshots
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                'success': True,
                'has_data': False,
                'message': '暂无数据'
            })
        
        snapshot_time = result[0]
        created_at = result[5]
        
        # 计算延迟（分钟）
        now = datetime.now(BEIJING_TZ)
        try:
            snapshot_dt = datetime.strptime(snapshot_time, '%Y-%m-%d %H:%M:%S')
            snapshot_dt = BEIJING_TZ.localize(snapshot_dt)
        except:
            snapshot_dt = datetime.strptime(snapshot_time, '%Y-%m-%d %H:%M:%S.%f')
            snapshot_dt = BEIJING_TZ.localize(snapshot_dt)
        
        delay_minutes = (now - snapshot_dt).total_seconds() / 60
        
        return jsonify({
            'success': True,
            'has_data': True,
            'data': {
                'snapshot_time': snapshot_time,
                'rush_up': result[1],
                'rush_down': result[2],
                'count': result[3],
                'status': result[4],
                'created_at': created_at,
                'delay_minutes': round(delay_minutes, 1)
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ==================== SAR斜率系统 API ====================

@app.route('/sar-slope')
def sar_slope_page():
    """SAR斜率系统页面"""
    return render_template('sar_slope.html')

@app.route('/api/sar-slope/latest')
def api_sar_slope_latest():
    """获取所有币种的最新SAR斜率数据"""
    try:
        symbol_filter = request.args.get('symbol', '').upper()
        position_filter = request.args.get('position', '')  # bullish/bearish
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取每个币种的最新记录
        query = """
            SELECT 
                s.symbol,
                s.datetime_beijing,
                s.sar_value,
                s.sar_position,
                s.sar_quadrant,
                s.position_duration,
                s.slope_value,
                s.slope_direction,
                s.price_close,
                s.timestamp
            FROM sar_slope_data s
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM sar_slope_data
                GROUP BY symbol
            ) latest ON s.symbol = latest.symbol AND s.timestamp = latest.max_timestamp
        """
        
        conditions = []
        params = []
        
        if symbol_filter:
            conditions.append("s.symbol LIKE ?")
            params.append(f"%{symbol_filter}%")
        
        if position_filter:
            conditions.append("s.sar_position = ?")
            params.append(position_filter)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY s.symbol"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'symbol': row[0],
                'datetime': row[1],
                'sar_value': round(row[2], 6) if row[2] else None,
                'sar_position': row[3],
                'sar_quadrant': row[4],
                'position_duration': row[5],
                'slope_value': round(row[6], 4) if row[6] else None,
                'slope_direction': row[7],
                'price': round(row[8], 6) if row[8] else None,
                'timestamp': row[9]
            })
        
        # 获取统计信息
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN current_position = 'bullish' THEN 1 ELSE 0 END) as bullish_count,
                SUM(CASE WHEN current_position = 'bearish' THEN 1 ELSE 0 END) as bearish_count,
                AVG(position_duration) as avg_duration
            FROM sar_position_stats
        """)
        
        stats_row = cursor.fetchone()
        stats = {
            'total_symbols': stats_row[0],
            'bullish_count': stats_row[1],
            'bearish_count': stats_row[2],
            'avg_duration': round(stats_row[3], 1) if stats_row[3] else 0
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'stats': stats,
            'timestamp': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/sar-slope/history/<symbol>')
def api_sar_slope_history(symbol):
    """获取指定币种的SAR斜率历史数据（默认48小时）"""
    try:
        days = int(request.args.get('days', 2))
        limit = int(request.args.get('limit', 600))
        
        # 计算起始时间戳
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                timestamp,
                datetime_beijing,
                sar_value,
                sar_position,
                sar_quadrant,
                position_duration,
                slope_value,
                slope_direction,
                price_open,
                price_close
            FROM sar_slope_data
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, start_time, limit))
        
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'timestamp': row[0],
                'datetime': row[1],
                'sar_value': round(row[2], 6) if row[2] else None,
                'sar_position': row[3],
                'sar_quadrant': row[4],
                'position_duration': row[5],
                'slope_value': round(row[6], 4) if row[6] else None,
                'slope_direction': row[7],
                'price_open': round(row[8], 6) if row[8] else None,
                'price': round(row[9], 6) if row[9] else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'days': days,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/sar-slope/position-changes/<symbol>')
def api_sar_slope_position_changes(symbol):
    """获取指定币种的SAR位置变化历史"""
    try:
        days = int(request.args.get('days', 7))
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 查找位置变化点
        cursor.execute("""
            WITH position_changes AS (
                SELECT 
                    timestamp,
                    datetime_beijing,
                    sar_value,
                    sar_position,
                    position_duration,
                    price_close,
                    LAG(sar_position) OVER (ORDER BY timestamp) as prev_position
                FROM sar_slope_data
                WHERE symbol = ? AND timestamp >= ?
            )
            SELECT 
                timestamp,
                datetime_beijing,
                sar_value,
                sar_position,
                position_duration,
                price_close
            FROM position_changes
            WHERE prev_position IS NULL OR sar_position != prev_position
            ORDER BY timestamp DESC
            LIMIT 100
        """, (symbol, start_time))
        
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'timestamp': row[0],
                'datetime': row[1],
                'sar_value': round(row[2], 6) if row[2] else None,
                'position': row[3],
                'duration': row[4],
                'price': round(row[5], 6) if row[5] else None
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'days': days,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/sar-slope/collector-status')
def api_sar_slope_collector_status():
    """获取SAR斜率采集器状态"""
    try:
        conn = sqlite3.connect('databases/crypto_data.db')
        cursor = conn.cursor()
        
        # 获取最新数据时间
        cursor.execute("""
            SELECT MAX(timestamp) FROM sar_slope_data
        """)
        
        latest_timestamp = cursor.fetchone()[0]
        
        if latest_timestamp:
            latest_dt = datetime.utcfromtimestamp(latest_timestamp / 1000)
            latest_dt_beijing = latest_dt.replace(tzinfo=pytz.UTC).astimezone(BEIJING_TZ)
            latest_time = latest_dt_beijing.strftime('%Y-%m-%d %H:%M:%S')
            
            # 计算延迟
            now = datetime.now(BEIJING_TZ)
            delay_minutes = (now - latest_dt_beijing).total_seconds() / 60
        else:
            latest_time = None
            delay_minutes = None
        
        # 获取数据统计
        cursor.execute("""
            SELECT COUNT(*) FROM sar_slope_data
        """)
        total_records = cursor.fetchone()[0]
        
        # 获取各币种数据量
        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM sar_slope_data
            GROUP BY symbol
            ORDER BY count DESC
        """)
        
        symbol_counts = [{'symbol': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'status': {
                'latest_time': latest_time,
                'delay_minutes': round(delay_minutes, 1) if delay_minutes else None,
                'is_delayed': delay_minutes > 10 if delay_minutes else True,
                'total_records': total_records,
                'symbol_counts': symbol_counts
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ==================== Telegram 配置管理 API ====================

@app.route('/api/telegram/config', methods=['GET', 'POST'])
def telegram_config_api():
    """
    获取或更新 Telegram 配置
    GET: 返回当前配置
    POST: 更新配置
    """
    config_file = 'telegram_config.json'
    
    try:
        if request.method == 'GET':
            # 读取当前配置
            if not os.path.exists(config_file):
                return jsonify({
                    'success': False,
                    'error': '配置文件不存在'
                }), 404
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            # 更新配置
            data = request.json
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': '请提供配置数据'
                }), 400
            
            # 读取现有配置
            if not os.path.exists(config_file):
                return jsonify({
                    'success': False,
                    'error': '配置文件不存在'
                }), 404
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新信号类型的启用状态
            if 'buy' in data:
                config['signal_types']['buy']['enabled'] = data['buy']
            if 'sell' in data:
                config['signal_types']['sell']['enabled'] = data['sell']
            if 'double_buy' in data:
                config['signal_types']['double_buy']['enabled'] = data['double_buy']
            if 'double_sell' in data:
                config['signal_types']['double_sell']['enabled'] = data['double_sell']
            
            # 备份原配置
            backup_file = f'telegram_config_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 保存新配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'message': '配置已更新',
                'config': config,
                'backup_file': backup_file
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ==================== 资金监控系统 API ====================

@app.route('/api/fund-monitor/latest', methods=['GET'])
def fund_monitor_latest():
    """获取最新的资金监控数据（所有币种，所有时间周期）"""
    try:
        conn = sqlite3.connect('fund_monitor.db')
        cursor = conn.cursor()
        
        # 获取每个币种、每个时间周期的最新数据
        cursor.execute('''
            SELECT symbol, interval_type, timestamp, collect_time, volume, 
                   avg_3day, deviation_percent, is_abnormal
            FROM fund_monitor_aggregated
            WHERE (symbol, interval_type, timestamp) IN (
                SELECT symbol, interval_type, MAX(timestamp)
                FROM fund_monitor_aggregated
                GROUP BY symbol, interval_type
            )
            ORDER BY symbol, interval_type
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # 按币种组织数据
        data_by_symbol = {}
        for row in rows:
            symbol = row[0]
            if symbol not in data_by_symbol:
                data_by_symbol[symbol] = {
                    '15min': None,
                    '30min': None,
                    '60min': None
                }
            
            interval_type = row[1]
            data_by_symbol[symbol][interval_type] = {
                'timestamp': row[2],
                'collect_time': row[3],
                'volume': round(row[4], 2),
                'avg_3day': round(row[5], 2) if row[5] is not None else None,
                'deviation_percent': round(row[6], 2) if row[6] is not None else None,
                'is_abnormal': bool(row[7])
            }
        
        return jsonify({
            'success': True,
            'data': data_by_symbol,
            'update_time': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/fund-monitor/history/<symbol>', methods=['GET'])
def fund_monitor_history(symbol):
    """获取指定币种的历史数据"""
    try:
        interval_type = request.args.get('interval', '15min')  # 默认15分钟
        hours = int(request.args.get('hours', 24))  # 默认24小时
        
        conn = sqlite3.connect('fund_monitor.db')
        cursor = conn.cursor()
        
        # 计算时间范围
        end_time = int(datetime.now(BEIJING_TZ).timestamp() * 1000)
        start_time = end_time - (hours * 60 * 60 * 1000)
        
        cursor.execute('''
            SELECT timestamp, collect_time, volume, avg_3day, 
                   deviation_percent, is_abnormal
            FROM fund_monitor_aggregated
            WHERE symbol = ?
            AND interval_type = ?
            AND timestamp >= ?
            ORDER BY timestamp ASC
        ''', (symbol.upper(), interval_type, start_time))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'timestamp': row[0],
                'collect_time': row[1],
                'volume': round(row[2], 2),
                'avg_3day': round(row[3], 2) if row[3] is not None else None,
                'deviation_percent': round(row[4], 2) if row[4] is not None else None,
                'is_abnormal': bool(row[5])
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'interval_type': interval_type,
            'hours': hours,
            'data': history
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/fund-monitor/abnormal', methods=['GET'])
def fund_monitor_abnormal():
    """获取当前所有异常数据"""
    try:
        conn = sqlite3.connect('fund_monitor.db')
        cursor = conn.cursor()
        
        # 获取最新异常数据
        cursor.execute('''
            SELECT symbol, interval_type, timestamp, collect_time, 
                   volume, avg_3day, deviation_percent
            FROM fund_monitor_aggregated
            WHERE is_abnormal = 1
            AND (symbol, interval_type, timestamp) IN (
                SELECT symbol, interval_type, MAX(timestamp)
                FROM fund_monitor_aggregated
                WHERE is_abnormal = 1
                GROUP BY symbol, interval_type
            )
            ORDER BY ABS(deviation_percent) DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        abnormal_list = []
        for row in rows:
            abnormal_list.append({
                'symbol': row[0],
                'interval_type': row[1],
                'timestamp': row[2],
                'collect_time': row[3],
                'volume': round(row[4], 2),
                'avg_3day': round(row[5], 2) if row[5] is not None else None,
                'deviation_percent': round(row[6], 2)
            })
        
        return jsonify({
            'success': True,
            'count': len(abnormal_list),
            'data': abnormal_list,
            'update_time': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/fund-monitor/config', methods=['GET', 'POST'])
def fund_monitor_config():
    """获取或更新资金监控配置"""
    config_file = 'fund_monitor_config.json'
    
    try:
        if request.method == 'GET':
            # 读取配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {
                    'threshold_percentage': 20.0,
                    'lookback_days': 3,
                    'collection_interval': 300
                }
            
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            # 更新配置
            data = request.json
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': '请提供配置数据'
                }), 400
            
            # 读取现有配置或使用默认值
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {
                    'threshold_percentage': 20.0,
                    'lookback_days': 3,
                    'collection_interval': 300
                }
            
            # 更新配置
            if 'threshold_percentage' in data:
                config['threshold_percentage'] = float(data['threshold_percentage'])
            if 'lookback_days' in data:
                config['lookback_days'] = int(data['lookback_days'])
            if 'collection_interval' in data:
                config['collection_interval'] = int(data['collection_interval'])
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'message': '配置已更新',
                'config': config
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/fund-monitor/abnormal-history', methods=['GET'])
def fund_monitor_abnormal_history():
    """查询异常数据历史记录"""
    try:
        # 获取查询参数
        date = request.args.get('date')  # 格式：YYYY-MM-DD
        start_date = request.args.get('start_date')  # 格式：YYYY-MM-DD
        end_date = request.args.get('end_date')  # 格式：YYYY-MM-DD
        symbol = request.args.get('symbol')  # 币种
        interval = request.args.get('interval')  # 时间周期
        severity = request.args.get('severity')  # 严重程度
        deviation_type = request.args.get('type')  # surge或drop
        limit = int(request.args.get('limit', 100))  # 返回记录数
        
        conn = sqlite3.connect('fund_monitor.db')
        cursor = conn.cursor()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if date:
            conditions.append('collect_date = ?')
            params.append(date)
        elif start_date and end_date:
            conditions.append('collect_date BETWEEN ? AND ?')
            params.extend([start_date, end_date])
        elif start_date:
            conditions.append('collect_date >= ?')
            params.append(start_date)
        elif end_date:
            conditions.append('collect_date <= ?')
            params.append(end_date)
        
        if symbol:
            conditions.append('symbol = ?')
            params.append(symbol.upper())
        
        if interval:
            conditions.append('interval_type = ?')
            params.append(interval)
        
        if severity:
            conditions.append('severity = ?')
            params.append(severity)
        
        if deviation_type:
            conditions.append('deviation_type = ?')
            params.append(deviation_type)
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        # 执行查询
        query = f'''
            SELECT id, symbol, interval_type, timestamp, collect_time, collect_date,
                   volume, avg_3day, deviation_percent, deviation_type, severity
            FROM fund_monitor_abnormal_history
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 格式化结果
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'symbol': row[1],
                'interval_type': row[2],
                'timestamp': row[3],
                'collect_time': row[4],
                'collect_date': row[5],
                'volume': round(row[6], 2),
                'avg_3day': round(row[7], 2),
                'deviation_percent': round(row[8], 2),
                'deviation_type': row[9],
                'severity': row[10]
            })
        
        # 统计信息
        cursor.execute(f'''
            SELECT COUNT(*) FROM fund_monitor_abnormal_history
            WHERE {where_clause}
        ''', params[:-1])  # 去掉limit参数
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_count': total_count,
            'returned_count': len(history),
            'data': history
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/fund-monitor/abnormal-dates', methods=['GET'])
def fund_monitor_abnormal_dates():
    """获取有异常数据的日期列表"""
    try:
        conn = sqlite3.connect('fund_monitor.db')
        cursor = conn.cursor()
        
        # 查询所有有异常数据的日期及其统计
        cursor.execute('''
            SELECT collect_date, 
                   COUNT(*) as count,
                   COUNT(DISTINCT symbol) as affected_coins,
                   AVG(ABS(deviation_percent)) as avg_deviation
            FROM fund_monitor_abnormal_history
            GROUP BY collect_date
            ORDER BY collect_date DESC
        ''')
        
        rows = cursor.fetchall()
        
        dates = []
        for row in rows:
            dates.append({
                'date': row[0],
                'count': row[1],
                'affected_coins': row[2],
                'avg_deviation': round(row[3], 2)
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'dates': dates
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/fund-monitor/abnormal-timeline', methods=['GET'])
def fund_monitor_abnormal_timeline():
    """获取异常数据时间轴（按小时聚合）"""
    try:
        date = request.args.get('date')  # YYYY-MM-DD
        
        if not date:
            return jsonify({
                'success': False,
                'error': '请提供date参数'
            }), 400
        
        conn = sqlite3.connect('fund_monitor.db')
        cursor = conn.cursor()
        
        # 查询指定日期的所有异常数据
        cursor.execute('''
            SELECT symbol, interval_type, collect_time, volume, 
                   avg_3day, deviation_percent, deviation_type, severity
            FROM fund_monitor_abnormal_history
            WHERE collect_date = ?
            ORDER BY collect_time ASC
        ''', (date,))
        
        rows = cursor.fetchall()
        
        # 按小时分组
        timeline = {}
        for row in rows:
            collect_time = row[2]
            hour = collect_time[:13]  # YYYY-MM-DD HH
            
            if hour not in timeline:
                timeline[hour] = []
            
            timeline[hour].append({
                'symbol': row[0],
                'interval_type': row[1],
                'time': collect_time,
                'volume': round(row[3], 2),
                'avg_3day': round(row[4], 2),
                'deviation_percent': round(row[5], 2),
                'deviation_type': row[6],
                'severity': row[7]
            })
        
        # 转换为列表格式
        timeline_list = []
        for hour, events in sorted(timeline.items()):
            timeline_list.append({
                'hour': hour,
                'count': len(events),
                'events': events
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'date': date,
            'timeline': timeline_list
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/fund-monitor', methods=['GET'])
def fund_monitor_page():
    """资金监控系统前端页面"""
    return render_template('fund_monitor.html')

@app.route('/fund-monitor-history', methods=['GET'])
def fund_monitor_history_page():
    """资金监控异常历史查询页面"""
    return render_template('fund_monitor_history.html')

# ==================== SAR斜率系统路由 ====================
@app.route('/sar-slope')
def sar_slope():
    """SAR斜率系统主页面"""
    return render_template('sar_slope.html')

@app.route('/sar-slope/<symbol>')
def sar_slope_detail(symbol):
    """SAR斜率单币详细追踪页面"""
    return render_template('sar_slope_detail.html', symbol=symbol.upper())

@app.route('/api/sar-slope/status')
def sar_slope_status():
    """获取所有币种的SAR状态"""
    # 检查服务器端缓存
    cache_key = "sar_slope_status:all"
    cached_data = server_cache.get(cache_key, max_age=30)
    if cached_data:
        cached_data['_from_server_cache'] = True
        cached_data['_cache_age'] = int(time.time() - server_cache.timestamps.get(cache_key, 0))
        return jsonify(cached_data)
    
    try:
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, last_kline_time, total_klines,
                   current_position, current_sequence, updated_at
            FROM system_status
            ORDER BY symbol
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        status_list = []
        for row in rows:
            status_list.append({
                'symbol': row[0],
                'last_kline_time': row[1],
                'total_klines': row[2],
                'current_position': row[3],
                'current_sequence': row[4],
                'updated_at': row[5]
            })
        
        result = {
            'success': True,
            'data': status_list,
            'count': len(status_list)
        }
        
        # 保存到服务器端缓存
        server_cache.set(cache_key, result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sar-slope/symbol/<symbol>')
def sar_slope_symbol_data(symbol):
    """获取单个币种的详细SAR数据"""
    try:
        limit = request.args.get('limit', 500, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        # 获取原始SAR数据
        cursor.execute('''
            SELECT timestamp, kline_time, open_price, high_price, low_price, 
                   close_price, sar_value, position, position_sequence, duration_minutes
            FROM sar_raw_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol, limit))
        
        sar_data = []
        for row in cursor.fetchall():
            sar_data.append({
                'timestamp': row[0],
                'kline_time': row[1],
                'open': row[2],
                'high': row[3],
                'low': row[4],
                'close': row[5],
                'sar': row[6],
                'position': row[7],
                'sequence': row[8],
                'duration': row[9]
            })
        
        # 获取变化率数据
        cursor.execute('''
            SELECT sequence_num, prev_sar, current_sar, change_value, 
                   change_percent, kline_time, position
            FROM sar_consecutive_changes
            WHERE symbol = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (symbol, limit))
        
        changes = []
        for row in cursor.fetchall():
            changes.append({
                'sequence': row[0],
                'prev_sar': row[1],
                'current_sar': row[2],
                'change_value': row[3],
                'change_percent': row[4],
                'time': row[5],
                'position': row[6]
            })
        
        # 获取平均值
        cursor.execute('''
            SELECT position, period_type, avg_change_percent, sample_count
            FROM sar_period_averages
            WHERE symbol = ?
        ''', (symbol,))
        
        averages = {}
        for row in cursor.fetchall():
            pos = row[0]
            if pos not in averages:
                averages[pos] = {}
            averages[pos][row[1]] = {
                'avg': row[2],
                'samples': row[3]
            }
        
        # 获取最近异常
        cursor.execute('''
            SELECT position, sequence_num, sar_value, change_percent,
                   deviation_percent, alert_level, is_extreme_point, kline_time
            FROM sar_anomaly_alerts
            WHERE symbol = ?
            ORDER BY created_at DESC
            LIMIT 100
        ''', (symbol,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'position': row[0],
                'sequence': row[1],
                'sar': row[2],
                'change_percent': row[3],
                'deviation': row[4],
                'level': row[5],
                'is_extreme': row[6],
                'time': row[7]
            })
        
        # 获取转换点
        cursor.execute('''
            SELECT timestamp, kline_time, from_position, to_position,
                   conversion_sar, conversion_price, previous_duration
            FROM sar_conversion_points
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (symbol,))
        
        conversions = []
        for row in cursor.fetchall():
            conversions.append({
                'timestamp': row[0],
                'time': row[1],
                'from_position': row[2],
                'to_position': row[3],
                'sar': row[4],
                'price': row[5],
                'prev_duration': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'sar_data': sar_data,
            'changes': changes,
            'averages': averages,
            'alerts': alerts,
            'conversions': conversions
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sar-slope/alerts')
def sar_slope_alerts():
    """获取所有异常告警"""
    try:
        limit = request.args.get('limit', 50, type=int)
        symbol = request.args.get('symbol', None)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('''
                SELECT symbol, position, sequence_num, sar_value,
                       change_percent, deviation_percent, alert_level,
                       is_extreme_point, extreme_type, kline_time
                FROM sar_anomaly_alerts
                WHERE symbol = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (symbol, limit))
        else:
            cursor.execute('''
                SELECT symbol, position, sequence_num, sar_value,
                       change_percent, deviation_percent, alert_level,
                       is_extreme_point, extreme_type, kline_time
                FROM sar_anomaly_alerts
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'symbol': row[0],
                'position': row[1],
                'sequence': row[2],
                'sar': row[3],
                'change_percent': row[4],
                'deviation': row[5],
                'level': row[6],
                'is_extreme': row[7],
                'extreme_type': row[8],
                'time': row[9]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sar-slope/conversions')
def sar_slope_conversions():
    """获取多空转换点"""
    try:
        limit = request.args.get('limit', 50, type=int)
        symbol = request.args.get('symbol', None)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute('''
                SELECT symbol, timestamp, kline_time, from_position, to_position,
                       conversion_sar, conversion_price, previous_duration
                FROM sar_conversion_points
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (symbol, limit))
        else:
            cursor.execute('''
                SELECT symbol, timestamp, kline_time, from_position, to_position,
                       conversion_sar, conversion_price, previous_duration
                FROM sar_conversion_points
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
        
        conversions = []
        for row in cursor.fetchall():
            conversions.append({
                'symbol': row[0],
                'timestamp': row[1],
                'time': row[2],
                'from_position': row[3],
                'to_position': row[4],
                'sar': row[5],
                'price': row[6],
                'prev_duration': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': conversions,
            'count': len(conversions)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sar-slope/query/<symbol>')
def sar_slope_query_symbol(symbol):
    """
    完整的单币查询接口
    查询参数:
    - start_time: 开始时间 (格式: YYYY-MM-DD HH:MM:SS)
    - end_time: 结束时间 (格式: YYYY-MM-DD HH:MM:SS)
    - limit: 返回数量限制 (默认: 1000)
    - position: 筛选多空状态 (long/short)
    - include_changes: 是否包含变化率 (true/false, 默认: true)
    - include_alerts: 是否包含异常告警 (true/false, 默认: true)
    - include_conversions: 是否包含多空转换 (true/false, 默认: true)
    - include_averages: 是否包含周期平均值 (true/false, 默认: true)
    """
    try:
        # 获取查询参数
        start_time = request.args.get('start_time', None)
        end_time = request.args.get('end_time', None)
        limit = request.args.get('limit', 1000, type=int)
        position = request.args.get('position', None)  # long/short
        
        include_changes = request.args.get('include_changes', 'true').lower() == 'true'
        include_alerts = request.args.get('include_alerts', 'true').lower() == 'true'
        include_conversions = request.args.get('include_conversions', 'true').lower() == 'true'
        include_averages = request.args.get('include_averages', 'true').lower() == 'true'
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        result = {
            'success': True,
            'symbol': symbol.upper(),
            'query_params': {
                'start_time': start_time,
                'end_time': end_time,
                'limit': limit,
                'position': position
            }
        }
        
        # 1. 获取系统状态
        cursor.execute('''
            SELECT last_update_time, last_kline_time, total_klines,
                   current_position, current_sequence, status, updated_at
            FROM system_status
            WHERE symbol = ?
        ''', (symbol.upper(),))
        
        status_row = cursor.fetchone()
        if status_row:
            result['system_status'] = {
                'last_update_time': status_row[0],
                'last_kline_time': status_row[1],
                'total_klines': status_row[2],
                'current_position': status_row[3],
                'current_sequence': status_row[4],
                'status': status_row[5],
                'updated_at': status_row[6]
            }
        else:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol.upper()} not found in system'
            })
        
        # 2. 构建原始数据查询SQL
        sql_conditions = ["symbol = ?"]
        sql_params = [symbol.upper()]
        
        if start_time:
            # 转换时间字符串为时间戳
            from datetime import datetime
            import pytz
            beijing_tz = pytz.timezone('Asia/Shanghai')
            dt = beijing_tz.localize(datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
            timestamp = int(dt.timestamp() * 1000)
            sql_conditions.append("timestamp >= ?")
            sql_params.append(timestamp)
        
        if end_time:
            from datetime import datetime
            import pytz
            beijing_tz = pytz.timezone('Asia/Shanghai')
            dt = beijing_tz.localize(datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S'))
            timestamp = int(dt.timestamp() * 1000)
            sql_conditions.append("timestamp <= ?")
            sql_params.append(timestamp)
        
        if position:
            sql_conditions.append("position = ?")
            sql_params.append(position)
        
        # 获取原始SAR数据
        cursor.execute(f'''
            SELECT timestamp, kline_time, open_price, high_price, low_price,
                   close_price, sar_value, position, position_sequence, duration_minutes
            FROM sar_raw_data
            WHERE {' AND '.join(sql_conditions)}
            ORDER BY timestamp DESC
            LIMIT ?
        ''', sql_params + [limit])
        
        sar_data = []
        for row in cursor.fetchall():
            sar_data.append({
                'timestamp': row[0],
                'kline_time': row[1],
                'open': row[2],
                'high': row[3],
                'low': row[4],
                'close': row[5],
                'sar': row[6],
                'position': row[7],
                'sequence': row[8],
                'duration': row[9]
            })
        
        result['sar_data'] = {
            'count': len(sar_data),
            'data': sar_data
        }
        
        # 3. 获取变化率数据（如果需要）
        if include_changes:
            change_conditions = ["symbol = ?"]
            change_params = [symbol.upper()]
            
            if position:
                change_conditions.append("position = ?")
                change_params.append(position)
            
            cursor.execute(f'''
                SELECT sequence_num, prev_sar, current_sar, change_value,
                       change_percent, kline_time, position
                FROM sar_consecutive_changes
                WHERE {' AND '.join(change_conditions)}
                ORDER BY id DESC
                LIMIT ?
            ''', change_params + [limit])
            
            changes = []
            for row in cursor.fetchall():
                changes.append({
                    'sequence': row[0],
                    'prev_sar': row[1],
                    'current_sar': row[2],
                    'change_value': row[3],
                    'change_percent': row[4],
                    'time': row[5],
                    'position': row[6]
                })
            
            result['changes'] = {
                'count': len(changes),
                'data': changes
            }
        
        # 4. 获取周期平均值（如果需要）
        if include_averages:
            cursor.execute('''
                SELECT position, period_type, avg_change_percent, 
                       sample_count, calculated_at
                FROM sar_period_averages
                WHERE symbol = ?
                ORDER BY position, period_type
            ''', (symbol.upper(),))
            
            averages = {
                'long': {},
                'short': {}
            }
            
            for row in cursor.fetchall():
                pos = row[0]
                period = row[1]
                averages[pos][period] = {
                    'avg_change_percent': row[2],
                    'sample_count': row[3],
                    'calculated_at': row[4]
                }
            
            result['averages'] = averages
        
        # 5. 获取异常告警（如果需要）
        if include_alerts:
            alert_conditions = ["symbol = ?"]
            alert_params = [symbol.upper()]
            
            if position:
                alert_conditions.append("position = ?")
                alert_params.append(position)
            
            cursor.execute(f'''
                SELECT position, sequence_num, sar_value, change_percent,
                       period_avg, deviation_percent, alert_level,
                       is_extreme_point, extreme_type, kline_time, created_at
                FROM sar_anomaly_alerts
                WHERE {' AND '.join(alert_conditions)}
                ORDER BY created_at DESC
                LIMIT ?
            ''', alert_params + [min(limit, 200)])
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'position': row[0],
                    'sequence': row[1],
                    'sar': row[2],
                    'change_percent': row[3],
                    'period_avg': row[4],
                    'deviation': row[5],
                    'level': row[6],
                    'is_extreme': row[7],
                    'extreme_type': row[8],
                    'time': row[9],
                    'created_at': row[10]
                })
            
            result['alerts'] = {
                'count': len(alerts),
                'data': alerts
            }
        
        # 6. 获取多空转换点（如果需要）
        if include_conversions:
            cursor.execute('''
                SELECT timestamp, kline_time, from_position, to_position,
                       conversion_sar, conversion_price, previous_duration, created_at
                FROM sar_conversion_points
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (symbol.upper(), min(limit, 100)))
            
            conversions = []
            for row in cursor.fetchall():
                conversions.append({
                    'timestamp': row[0],
                    'time': row[1],
                    'from_position': row[2],
                    'to_position': row[3],
                    'sar': row[4],
                    'price': row[5],
                    'prev_duration': row[6],
                    'created_at': row[7]
                })
            
            result['conversions'] = {
                'count': len(conversions),
                'data': conversions
            }
        
        # 7. 统计信息
        result['statistics'] = {
            'total_records': len(sar_data),
            'date_range': {
                'earliest': sar_data[-1]['kline_time'] if sar_data else None,
                'latest': sar_data[0]['kline_time'] if sar_data else None
            }
        }
        
        # 计算多空分布
        if sar_data:
            long_count = sum(1 for d in sar_data if d['position'] == 'long')
            short_count = sum(1 for d in sar_data if d['position'] == 'short')
            result['statistics']['position_distribution'] = {
                'long': long_count,
                'short': short_count,
                'long_percent': round(long_count / len(sar_data) * 100, 2),
                'short_percent': round(short_count / len(sar_data) * 100, 2)
            }
        
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/sar-slope/sequence-compare/<symbol>')
def sar_slope_sequence_compare(symbol):
    """
    序列号对比接口 - 用户需求
    对比当前序列号的变化率与该序列号的历史平均值
    
    例如：当前是空头02→空头03，变化率是0.05%
    查询所有历史上"空头02→空头03"这一步的平均变化率是0.04%
    得出结论：当前比平均值增加了0.01%
    
    参数:
    - position: long/short (可选，不填则返回两个方向)
    - sequence: 序列号 (可选，不填则返回所有序列号)
    """
    try:
        position_filter = request.args.get('position', None)
        sequence_filter = request.args.get('sequence', None, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        result = {
            'success': True,
            'symbol': symbol.upper(),
            'comparisons': []
        }
        
        # 获取当前状态
        cursor.execute('''
            SELECT current_position, current_sequence
            FROM system_status
            WHERE symbol = ?
        ''', (symbol.upper(),))
        
        status = cursor.fetchone()
        if not status:
            return jsonify({'success': False, 'error': 'Symbol not found'})
        
        result['current_status'] = {
            'position': status[0],
            'sequence': status[1]
        }
        
        # 获取当前最新的变化率
        cursor.execute('''
            SELECT sequence_num, change_percent, kline_time, position
            FROM sar_consecutive_changes
            WHERE symbol = ?
            ORDER BY id DESC
            LIMIT 50
        ''', (symbol.upper(),))
        
        recent_changes = cursor.fetchall()
        
        # 获取序列号平均值
        cursor.execute('''
            SELECT position, period_type, avg_change_percent, sample_count
            FROM sar_period_averages
            WHERE symbol = ? AND period_type LIKE 'seq_%'
            ORDER BY position, period_type
        ''', (symbol.upper(),))
        
        seq_averages = {}
        for row in cursor.fetchall():
            pos = row[0]
            period = row[1]  # 格式: seq_01, seq_02, seq_03
            seq_num = int(period.split('_')[1])
            
            if pos not in seq_averages:
                seq_averages[pos] = {}
            
            seq_averages[pos][seq_num] = {
                'avg': row[2],
                'samples': row[3]
            }
        
        # 对比分析
        for change in recent_changes:
            seq_num = change[0]
            current_change = change[1]
            kline_time = change[2]
            pos = change[3]
            
            # 过滤条件
            if position_filter and pos != position_filter:
                continue
            if sequence_filter and seq_num != sequence_filter:
                continue
            
            # 获取该序列号的历史平均值
            if pos in seq_averages and seq_num in seq_averages[pos]:
                avg_data = seq_averages[pos][seq_num]
                avg_change = avg_data['avg']
                samples = avg_data['samples']
                
                # 计算差异
                difference = current_change - avg_change
                difference_percent = (difference / avg_change * 100) if avg_change != 0 else 0
                
                # 判断增加还是减小
                trend = 'increase' if difference > 0 else 'decrease' if difference < 0 else 'equal'
                
                result['comparisons'].append({
                    'position': pos,
                    'sequence': seq_num,
                    'time': kline_time,
                    'current_change': round(current_change, 6),
                    'average_change': round(avg_change, 6),
                    'difference': round(difference, 6),
                    'difference_percent': round(difference_percent, 2),
                    'trend': trend,
                    'sample_count': samples,
                    'description': f'{"多头" if pos == "long" else "空头"}{seq_num:02d}→{seq_num+1:02d}'
                })
        
        result['total_comparisons'] = len(result['comparisons'])
        
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/sar-slope/duration-signal/<symbol>')
def sar_slope_duration_signal(symbol):
    """
    按持续时间段分析信号 - 用户最新需求
    
    对比逻辑：
    - 多头区间：
      * 1天平均 < 3天平均（比值减小）→ 强势多头信号（偏多）
      * 1天平均 > 3天平均（比值增大）→ 加速赶顶信号（偏空）
    - 空头区间：
      * 1天平均 < 3天平均（比值减小）→ 强势空头信号（偏空）
      * 1天平均 > 3天平均（比值增大）→ 加速赶底信号（偏多）
    
    参数:
    - position: long/short (可选，不填则返回两个方向)
    - duration: 持续时间（分钟，可选）
    """
    try:
        position_filter = request.args.get('position', None)
        duration_filter = request.args.get('duration', None, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        result = {
            'success': True,
            'symbol': symbol.upper(),
            'signals': []
        }
        
        # 获取当前状态
        cursor.execute('''
            SELECT current_position, current_sequence
            FROM system_status
            WHERE symbol = ?
        ''', (symbol.upper(),))
        
        status = cursor.fetchone()
        if not status:
            return jsonify({'success': False, 'error': 'Symbol not found'})
        
        result['current_status'] = {
            'position': status[0],
            'sequence': status[1]
        }
        
        # 构建查询条件
        conditions = ["symbol = ?", "period_type LIKE 'dur_%'"]
        params = [symbol.upper()]
        
        if position_filter:
            conditions.append("position = ?")
            params.append(position_filter)
        
        # 获取所有 duration 的平均值数据
        cursor.execute(f'''
            SELECT position, period_type, avg_change_percent, sample_count
            FROM sar_period_averages
            WHERE {' AND '.join(conditions)}
            ORDER BY position, period_type
        ''', params)
        
        # 组织数据结构: {position: {duration: {period: avg}}}
        duration_data = {}
        for row in cursor.fetchall():
            pos = row[0]
            period_type = row[1]  # 格式: dur_15_1day
            avg_pct = row[2]
            sample_count = row[3]
            
            # 解析 period_type
            parts = period_type.split('_')
            if len(parts) != 3:
                continue
            
            duration = int(parts[1])
            period = parts[2]  # 1day, 3day, 7day, 15day
            
            # 过滤 duration
            if duration_filter and duration != duration_filter:
                continue
            
            if pos not in duration_data:
                duration_data[pos] = {}
            if duration not in duration_data[pos]:
                duration_data[pos][duration] = {}
            
            duration_data[pos][duration][period] = {
                'avg': avg_pct,
                'samples': sample_count
            }
        
        # 分析每个 position 和 duration 的信号
        for pos in duration_data:
            for duration in sorted(duration_data[pos].keys()):
                periods = duration_data[pos][duration]
                
                # 必须有 1day 和 3day 数据才能对比
                if '1day' not in periods or '3day' not in periods:
                    continue
                
                avg_1day = periods['1day']['avg']
                avg_3day = periods['3day']['avg']
                avg_7day = periods.get('7day', {}).get('avg', None)
                avg_15day = periods.get('15day', {}).get('avg', None)
                
                # 计算比值
                ratio = (avg_1day / avg_3day) if avg_3day != 0 else 1.0
                ratio_change = avg_1day - avg_3day
                ratio_change_percent = ((avg_1day - avg_3day) / avg_3day * 100) if avg_3day != 0 else 0
                
                # 根据用户逻辑判断信号
                if pos == 'long':
                    if avg_1day < avg_3day:  # 比值减小
                        signal_type = 'strong_long'
                        signal_desc = '强势多头'
                        bias = 'bullish'  # 偏多
                        interpretation = '当天平均 < 3天平均，变化率减小，趋势强劲'
                    else:  # 比值增大
                        signal_type = 'top_acceleration'
                        signal_desc = '加速赶顶'
                        bias = 'bearish'  # 偏空
                        interpretation = '当天平均 > 3天平均，变化率增大，可能见顶'
                else:  # short
                    if avg_1day < avg_3day:  # 比值减小
                        signal_type = 'strong_short'
                        signal_desc = '强势空头'
                        bias = 'bearish'  # 偏空
                        interpretation = '当天平均 < 3天平均，变化率减小，趋势强劲'
                    else:  # 比值增大
                        signal_type = 'bottom_acceleration'
                        signal_desc = '加速赶底'
                        bias = 'bullish'  # 偏多
                        interpretation = '当天平均 > 3天平均，变化率增大，可能见底'
                
                signal = {
                    'position': pos,
                    'duration_minutes': duration,
                    'averages': {
                        '1day': round(avg_1day, 6),
                        '3day': round(avg_3day, 6),
                        '7day': round(avg_7day, 6) if avg_7day else None,
                        '15day': round(avg_15day, 6) if avg_15day else None
                    },
                    'comparison': {
                        'ratio': round(ratio, 4),
                        'change': round(ratio_change, 6),
                        'change_percent': round(ratio_change_percent, 2)
                    },
                    'signal': {
                        'type': signal_type,
                        'description': signal_desc,
                        'bias': bias,
                        'interpretation': interpretation
                    },
                    'sample_counts': {
                        '1day': periods['1day']['samples'],
                        '3day': periods['3day']['samples'],
                        '7day': periods.get('7day', {}).get('samples', None),
                        '15day': periods.get('15day', {}).get('samples', None)
                    }
                }
                
                result['signals'].append(signal)
        
        result['total_signals'] = len(result['signals'])
        
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/sar-slope/transition-analysis/<symbol>')
def sar_slope_transition_analysis(symbol):
    """
    多空转换分析接口 - 用户最新需求
    
    核心逻辑:
    1. 记录每个5分钟的多空转换点（保留16天数据）
    2. 多头关注 sequence_num=2 (01→02，相当于03→02的变化)
    3. 空头关注 sequence_num=2 (01→02，相当于02→03的变化)
    4. 计算 当天/3天/7天/15天 平均值
    5. 对比当前值与平均值的差值百分比
    6. 判断偏多/偏空状态
    
    参数:
    - position: long/short (可选)
    """
    try:
        position_filter = request.args.get('position', None)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        result = {
            'success': True,
            'symbol': symbol.upper(),
            'analysis': {}
        }
        
        # 获取当前状态
        cursor.execute('''
            SELECT current_position, current_sequence, last_kline_time
            FROM system_status
            WHERE symbol = ?
        ''', (symbol.upper(),))
        
        status = cursor.fetchone()
        if not status:
            return jsonify({'success': False, 'error': 'Symbol not found'})
        
        # 获取当前价格和持续时间
        cursor.execute('''
            SELECT close_price, duration_minutes
            FROM sar_raw_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (symbol.upper(),))
        
        price_data = cursor.fetchone()
        current_price = price_data[0] if price_data else None
        current_duration = price_data[1] if price_data else None
        
        result['current_status'] = {
            'position': status[0],
            'sequence': status[1],
            'last_update': status[2],
            'current_price': round(current_price, 2) if current_price else None,
            'duration_minutes': current_duration
        }
        
        # 对每个方向进行分析
        positions = [position_filter] if position_filter else ['long', 'short']
        
        for pos in positions:
            # 获取该方向 sequence_num=2 的所有变化率数据（按时间降序）
            cursor.execute('''
                SELECT change_percent, kline_time, id
                FROM sar_consecutive_changes
                WHERE symbol = ? AND position = ? AND sequence_num = 2
                ORDER BY id DESC
            ''', (symbol.upper(), pos))
            
            changes = cursor.fetchall()
            
            if not changes:
                continue
            
            # 当前最新值
            current_value = changes[0][0]
            current_time = changes[0][1]
            
            # 提取所有变化率（从旧到新）
            all_changes = [c[0] for c in reversed(changes)]
            
            # 计算各周期平均值
            periods = {
                '1day': 288,   # 24小时 * 12个5分钟
                '3day': 864,   # 3 * 24 * 12
                '7day': 2016,  # 7 * 24 * 12
                '15day': 4320  # 15 * 24 * 12
            }
            
            period_averages = {}
            for period_name, period_count in periods.items():
                if len(all_changes) >= period_count:
                    period_changes = all_changes[-period_count:]
                else:
                    period_changes = all_changes
                
                if period_changes:
                    avg = sum(period_changes) / len(period_changes)
                    period_averages[period_name] = {
                        'average': avg,
                        'sample_count': len(period_changes)
                    }
            
            # 对比当前值与各周期平均值
            comparisons = {}
            for period_name, period_data in period_averages.items():
                avg = period_data['average']
                diff = current_value - avg
                diff_percent = (diff / avg * 100) if avg != 0 else 0
                
                # 判断趋势
                if diff > 0:
                    trend = 'increased'  # 增加
                    trend_cn = '增加'
                elif diff < 0:
                    trend = 'decreased'  # 减少
                    trend_cn = '减少'
                else:
                    trend = 'unchanged'
                    trend_cn = '持平'
                
                comparisons[period_name] = {
                    'period_average': round(avg, 6),
                    'current_value': round(current_value, 6),
                    'difference': round(diff, 6),
                    'difference_percent': round(diff_percent, 2),
                    'trend': trend,
                    'trend_cn': trend_cn,
                    'sample_count': period_data['sample_count']
                }
            
            # 综合判断偏多/偏空状态
            # 使用 1天 和 3天 的对比结果
            bias = None
            bias_reason = []
            
            if '1day' in comparisons and '3day' in comparisons:
                day1_diff = comparisons['1day']['difference_percent']
                day3_diff = comparisons['3day']['difference_percent']
                
                # 如果当前值高于平均值，说明变化率在增大
                # 如果当前值低于平均值，说明变化率在减小
                
                if pos == 'long':
                    # 多头区间：变化率增大 → 偏空（可能赶顶）
                    #          变化率减小 → 偏多（趋势稳健）
                    if day1_diff > 0 and day3_diff > 0:
                        bias = 'bearish'
                        bias_cn = '偏空'
                        bias_reason.append('多头变化率增大，可能加速赶顶')
                    elif day1_diff < 0 and day3_diff < 0:
                        bias = 'bullish'
                        bias_cn = '偏多'
                        bias_reason.append('多头变化率减小，趋势稳健')
                    else:
                        bias = 'neutral'
                        bias_cn = '中性'
                        bias_reason.append('多头信号不明确')
                else:  # short
                    # 空头区间：变化率增大 → 偏多（可能赶底）
                    #          变化率减小 → 偏空（趋势稳健）
                    if day1_diff > 0 and day3_diff > 0:
                        bias = 'bullish'
                        bias_cn = '偏多'
                        bias_reason.append('空头变化率增大，可能加速赶底')
                    elif day1_diff < 0 and day3_diff < 0:
                        bias = 'bearish'
                        bias_cn = '偏空'
                        bias_reason.append('空头变化率减小，趋势稳健')
                    else:
                        bias = 'neutral'
                        bias_cn = '中性'
                        bias_reason.append('空头信号不明确')
            
            result['analysis'][pos] = {
                'position': pos,
                'position_cn': '多头' if pos == 'long' else '空头',
                'sequence_info': '01→02 (序列2)',
                'current_value': round(current_value, 6),
                'current_time': current_time,
                'total_samples': len(all_changes),
                'period_comparisons': comparisons,
                'bias': {
                    'type': bias,
                    'type_cn': bias_cn,
                    'reason': bias_reason
                }
            }
        
        conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/sar-slope/current-cycle/<symbol>')
def sar_slope_current_cycle(symbol):
    """
    获取当前完整周期的所有序列数据
    
    用户需求:
    - 空头01开始显示，一直到空头转多头
    - 多头01开始显示，一直到多头转空头
    - 不显示持续时间字段
    
    返回当前周期从序列01到当前序列的完整数据
    """
    # 检查服务器端缓存
    cache_key = f"sar_slope_current_cycle:{symbol.upper()}"
    cached_data = server_cache.get(cache_key, max_age=30)
    if cached_data:
        cached_data['_from_server_cache'] = True
        cached_data['_cache_age'] = int(time.time() - server_cache.timestamps.get(cache_key, 0))
        response = jsonify(cached_data)
        # 添加防缓存头
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    try:
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        # 获取当前状态
        cursor.execute('''
            SELECT current_position, current_sequence, last_kline_time
            FROM system_status
            WHERE symbol = ?
        ''', (symbol.upper(),))
        
        status = cursor.fetchone()
        if not status:
            return jsonify({'success': False, 'error': 'Symbol not found'})
        
        current_position = status[0]
        current_sequence = status[1]
        last_update = status[2]
        
        # 获取所有可用的连续数据（不限制周期，显示16天或所有可用数据）
        # 计算16天需要的记录数：16天 * 288条/天 = 4608条
        max_records = 4608  # 16天的数据
        cursor.execute('''
            SELECT position_sequence, close_price, kline_time, 
                   open_price, high_price, low_price, sar_value, position
            FROM sar_raw_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol.upper(), max_records))
        
        raw_sequences = []
        rows = cursor.fetchall()  # 从新到旧
        for row in rows:  # 不反转，保持最新的在前
            seq, close, kline_time, open_p, high, low, sar, pos = row
            raw_sequences.append({
                'sequence': seq,
                'price': round(close, 2),
                'time': kline_time,
                'open': round(open_p, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'sar': sar,  # 保留完整精度用于计算
                'position': pos  # 记录该条数据的position（long/short）
            })
        
        # 【性能优化】一次性批量查询所有历史数据，避免在循环中重复查询
        # 获取所有需要的历史平均数据
        cursor.execute('''
            SELECT position, sequence_num, change_percent
            FROM sar_consecutive_changes
            WHERE symbol = ?
            ORDER BY id DESC
            LIMIT 4320
        ''', (symbol.upper(),))
        
        # 构建历史数据字典：{(position, seq_num): [change_percent, ...]}
        historical_data_dict = {}
        for row in cursor.fetchall():
            pos, seq_num, change_pct = row
            key = (pos, seq_num)
            if key not in historical_data_dict:
                historical_data_dict[key] = []
            historical_data_dict[key].append(change_pct)
        
        # 计算每个序列相对于前一个序列的变化率
        # 注意：现在raw_sequences[0]是最新的，raw_sequences[-1]是最早的
        sequences_with_changes = []
        for i, seq_data in enumerate(raw_sequences):
            seq_num = seq_data['sequence']
            
            # 获取当前行的position
            row_position = seq_data['position']
            
            # 添加基础数据
            result_data = {
                'sequence': seq_num,
                'price': seq_data['price'],
                'time': seq_data['time'],
                'open': seq_data['open'],
                'high': seq_data['high'],
                'low': seq_data['low'],
                'sar': round(seq_data['sar'], 4),
                'position': row_position,  # 添加position字段用于前端判断
                'position_cn': '多头' if row_position == 'long' else '空头'
            }
            
            # 如果有下一个序列（时间更早的），且position相同才计算变化率
            if i < len(raw_sequences) - 1:
                next_position = raw_sequences[i+1]['position']
                
                # 只有当前后两条数据的position相同时才计算变化率
                # 如果position不同，说明发生了多空转换，跳过计算
                if row_position == next_position:
                    next_sar = raw_sequences[i+1]['sar']  # 下一个（时间更早）
                    curr_sar = seq_data['sar']  # 当前（时间更新）
                    
                    # 用户需求的计算公式:
                    # 当前是较新的序列号，next是较旧的序列号
                    # 例如：curr=空03, next=空02
                    # 多头: (当前SAR - 前一个SAR) / 当前SAR
                    # 空头: (前一个SAR - 当前SAR) / 前一个SAR
                    if row_position == 'long':
                        # 多头: (curr - next) / curr
                        seq_change_percent = ((curr_sar - next_sar) / curr_sar) * 100 if curr_sar != 0 else 0
                        sar_absolute_diff = curr_sar - next_sar  # SAR绝对差值
                    else:  # short
                        # 空头: (next - curr) / next
                        # 注意：这里next是旧序列（序列号小），curr是新序列（序列号大）
                        # 但SAR值计算时，next的SAR应该比curr的SAR大
                        seq_change_percent = ((next_sar - curr_sar) / next_sar) * 100 if next_sar != 0 else 0
                        sar_absolute_diff = next_sar - curr_sar  # SAR绝对差值
                    
                    result_data['sequence_change_percent'] = round(seq_change_percent, 4)
                    result_data['sar_diff'] = round(sar_absolute_diff, 4)  # SAR值的绝对差值
                    
                    # 【性能优化】从预加载的字典中获取历史数据，而不是重复查询数据库
                    lookup_key = (row_position, seq_num)
                    historical_changes = historical_data_dict.get(lookup_key, [])[:288]  # 最多取288条（1天）
                    if historical_changes:
                        avg_1day = sum(historical_changes) / len(historical_changes)
                        avg_3day = sum(historical_changes[:min(864, len(historical_changes))]) / min(864, len(historical_changes)) if len(historical_changes) >= 1 else avg_1day
                        avg_7day = sum(historical_changes[:min(2016, len(historical_changes))]) / min(2016, len(historical_changes)) if len(historical_changes) >= 1 else avg_1day
                        avg_15day = sum(historical_changes[:min(4320, len(historical_changes))]) / min(4320, len(historical_changes)) if len(historical_changes) >= 1 else avg_1day
                        
                        result_data['avg_1day'] = round(avg_1day, 6)
                        result_data['avg_3day'] = round(avg_3day, 6)
                        result_data['avg_7day'] = round(avg_7day, 6)
                        result_data['avg_15day'] = round(avg_15day, 6)
                        
                        # 计算相对变化百分比：(当前 - 平均) / 平均 × 100
                        # 例: 当前0.0613%, 平均0.083284%, 变化 = (0.0613-0.083284)/0.083284*100 = -26.40%
                        if avg_1day != 0:
                            change_1day_percent = ((seq_change_percent - avg_1day) / avg_1day) * 100
                        else:
                            change_1day_percent = 0
                        
                        if avg_3day != 0:
                            change_3day_percent = ((seq_change_percent - avg_3day) / avg_3day) * 100
                        else:
                            change_3day_percent = 0
                        
                        if avg_7day != 0:
                            change_7day_percent = ((seq_change_percent - avg_7day) / avg_7day) * 100
                        else:
                            change_7day_percent = 0
                        
                        if avg_15day != 0:
                            change_15day_percent = ((seq_change_percent - avg_15day) / avg_15day) * 100
                        else:
                            change_15day_percent = 0
                        
                        # 同时保留绝对差值（用于偏向判断）
                        diff_1day = seq_change_percent - avg_1day
                        
                        result_data['change_1day_percent'] = round(change_1day_percent, 2)
                        result_data['change_3day_percent'] = round(change_3day_percent, 2)
                        result_data['change_7day_percent'] = round(change_7day_percent, 2)
                        result_data['change_15day_percent'] = round(change_15day_percent, 2)
                        
                        # 判断偏向（使用当前行的position）
                        if row_position == 'long':
                            bias = '偏多' if diff_1day < 0 else '偏空'
                        else:
                            bias = '偏空' if diff_1day < 0 else '偏多'
                        
                        result_data['bias'] = bias
            
            sequences_with_changes.append(result_data)
        
        # 计算最近2小时的偏多/偏空比例
        # 2小时 = 24条数据（每5分钟一条）
        recent_2hours = sequences_with_changes[:24]  # 取最新的24条数据
        
        bias_bullish_count = 0  # 偏多数量
        bias_bearish_count = 0  # 偏空数量
        bias_neutral_count = 0  # 中性（无偏向或"-"）
        
        for seq in recent_2hours:
            if 'bias' in seq and seq['bias']:
                if seq['bias'] == '偏多':
                    bias_bullish_count += 1
                elif seq['bias'] == '偏空':
                    bias_bearish_count += 1
                else:
                    bias_neutral_count += 1
            else:
                bias_neutral_count += 1
        
        total_with_bias = bias_bullish_count + bias_bearish_count
        bias_stats = {
            'period': '2小时',
            'total_records': len(recent_2hours),
            'bullish_count': bias_bullish_count,
            'bearish_count': bias_bearish_count,
            'neutral_count': bias_neutral_count,
            'bullish_ratio': round((bias_bullish_count / total_with_bias * 100), 2) if total_with_bias > 0 else 0,
            'bearish_ratio': round((bias_bearish_count / total_with_bias * 100), 2) if total_with_bias > 0 else 0
        }
        
        result = {
            'success': True,
            'symbol': symbol.upper(),
            'current_status': {
                'position': current_position,
                'position_cn': '多头' if current_position == 'long' else '空头',
                'current_sequence': current_sequence,
                'last_update': last_update,
                'cycle_info': f"{current_position}01 → {current_position}{current_sequence:02d}"
            },
            'bias_statistics': bias_stats,  # 新增：2小时偏向统计
            'sequences': sequences_with_changes,
            'total_sequences': len(sequences_with_changes)
        }
        
        # 保存到服务器端缓存
        server_cache.set(cache_key, result)
        
        conn.close()
        response = jsonify(result)
        # 添加防缓存头，避免外部代理缓存旧的500错误
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# ============================================
# SAR偏向趋势API
# ============================================
@app.route('/sar-bias-trend')
def sar_bias_trend_page():
    """SAR偏向趋势图页面"""
    return render_template('sar_bias_trend.html')

@app.route('/api/sar-slope/bias-trend')
def sar_slope_bias_trend():
    """获取SAR偏向趋势数据（12小时分页）"""
    try:
        from datetime import datetime, timezone, timedelta
        import json
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/sar_slope_data.db', timeout=10.0)
        cursor = conn.cursor()
        
        # 北京时区
        beijing_tz = timezone(timedelta(hours=8))
        
        # 计算时间范围（每页12小时）
        # page=1: 最近12小时
        # page=2: 12-24小时前
        # page=3: 24-36小时前
        hours_end = (page - 1) * 12
        hours_start = page * 12
        
        # 获取指定页的12小时数据（数据库存储的是北京时间，需要+8小时来匹配）
        cursor.execute('''
        SELECT 
            timestamp,
            bullish_count,
            bearish_count,
            total_symbols,
            bullish_symbols,
            bearish_symbols
        FROM sar_bias_trend
        WHERE datetime(timestamp) >= datetime('now', '+8 hours', '-' || ? || ' hours')
          AND datetime(timestamp) < datetime('now', '+8 hours', '-' || ? || ' hours')
        ORDER BY timestamp ASC
        ''', (hours_start, hours_end))
        
        rows = cursor.fetchall()
        
        # 获取总页数（基于所有数据）
        cursor.execute('SELECT MIN(timestamp) FROM sar_bias_trend')
        min_timestamp = cursor.fetchone()[0]
        
        total_pages = 1
        if min_timestamp:
            # 计算最早数据距今的小时数（使用北京时间）
            cursor.execute("SELECT (julianday('now', '+8 hours') - julianday(?)) * 24", (min_timestamp,))
            hours_diff = cursor.fetchone()[0]
            total_pages = max(1, int(hours_diff / 12) + 1)
        
        conn.close()
        
        data = []
        for row in rows:
            # 将时间戳转换为北京时间（如果需要）
            timestamp_str = row[0]
            data.append({
                'timestamp': timestamp_str,
                'bullish_count': row[1],
                'bearish_count': row[2],
                'total_symbols': row[3],
                'bullish_symbols': json.loads(row[4]) if row[4] else [],
                'bearish_symbols': json.loads(row[5]) if row[5] else []
            })
        
        # 获取当前页的时间范围（用于显示）
        time_range = {
            'start': '',
            'end': ''
        }
        if data:
            time_range['start'] = data[0]['timestamp']
            time_range['end'] = data[-1]['timestamp']
        
        return jsonify({
            'success': True,
            'data': data,
            'total': len(data),
            'page': page,
            'total_pages': total_pages,
            'time_range': time_range,
            'has_prev': page < total_pages,
            'has_next': page > 1
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ============================================
# 缓存管理API
# ============================================
@app.route('/api/cache/stats')
def cache_stats():
    """获取缓存统计信息"""
    stats = server_cache.get_stats()
    return jsonify({
        'success': True,
        'cache_stats': stats,
        'message': '服务器端缓存统计信息'
    })

@app.route('/api/cache/clear', methods=['POST'])
def cache_clear():
    """清除服务器端缓存"""
    try:
        key = request.json.get('key') if request.json else None
        server_cache.clear(key)
        return jsonify({
            'success': True,
            'message': f'缓存已清除{"（键: " + key + "）" if key else "（全部）"}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ========== 锚点系统（OKEx持仓监控） ==========

@app.route('/warning-test')
def warning_test():
    """预警模块测试页面"""
    return render_template('warning_test.html')

@app.route('/anchor-system')
def anchor_system():
    """锚点系统主页 - 重定向到实盘"""
    return redirect('/anchor-system-real')

@app.route('/anchor-system-real')
def anchor_system_real():
    """实盘锚点系统"""
    response = make_response(render_template('anchor_system_real.html'))
    # 禁用所有缓存
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/anchor-snapshots')
def anchor_snapshots():
    """锚点系统历史快照查看"""
    response = make_response(render_template('anchor_snapshots.html'))
    # 禁用所有缓存
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


@app.route('/api/anchor-system/real/hourly-extreme-stats')
def get_real_hourly_extreme_stats():
    """获取实盘锚点系统最近1小时的极值统计（只统计每个币种的最新极值）"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        db_path = '/home/user/webapp/anchor_system.db'
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # 使用北京时区
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now_beijing = datetime.now(beijing_tz)
        one_hour_ago_beijing = now_beijing - timedelta(hours=1)
        
        # 转换为字符串（数据库中存储的是北京时间）
        one_hour_ago_str = one_hour_ago_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取所有记录
        cursor.execute("""
            SELECT inst_id, pos_side, record_type, profit_rate, timestamp
            FROM anchor_real_profit_records
            ORDER BY timestamp DESC
        """)
        
        all_records = cursor.fetchall()
        
        # 按币种、方向、类型分组，只保留最新的记录
        latest_records = {}
        for record in all_records:
            inst_id, pos_side, record_type, profit_rate, timestamp = record
            key = (inst_id, pos_side, record_type)
            if key not in latest_records:
                latest_records[key] = record
        
        # 统计最近1小时内的最新极值
        stats = {
            'short_max_profit': 0,  # 空单利润创新高
            'short_max_loss': 0,    # 空单亏损创新高
            'long_max_profit': 0,   # 多单利润创新高
            'long_max_loss': 0      # 多单亏损创新高
        }
        
        for key, record in latest_records.items():
            inst_id, pos_side, record_type, profit_rate, timestamp = record
            if timestamp >= one_hour_ago_str:
                if pos_side == 'short' and record_type == 'max_profit':
                    stats['short_max_profit'] += 1
                elif pos_side == 'short' and record_type == 'max_loss':
                    stats['short_max_loss'] += 1
                elif pos_side == 'long' and record_type == 'max_profit':
                    stats['long_max_profit'] += 1
                elif pos_side == 'long' and record_type == 'max_loss':
                    stats['long_max_loss'] += 1
        
        conn.close()
        
        return jsonify({
            'success': True,
            'time_range': f'最近1小时 (>{one_hour_ago_str})',
            'current_time': now_beijing.strftime('%Y-%m-%d %H:%M:%S'),
            'stats': stats,
            'note': '只统计每个币种的最新极值记录（北京时间）'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/anchor-system-paper')
def anchor_system_paper():
    """模拟盘锚点系统"""
    response = make_response(render_template('anchor_system_paper.html'))
    # 禁用所有缓存
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


@app.route('/anchor-system-v2')
def anchor_system_v2():
    """锚点系统主页 v2 (新URL避免缓存)"""
    response = make_response(render_template('anchor_system.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/api/anchor-system/monitors')
def get_anchor_monitors():
    """获取持仓监控记录"""
    try:
        limit = request.args.get('limit', 100, type=int)
        db_path = '/home/user/webapp/anchor_system.db'
        
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM anchor_monitors 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        monitors = []
        for row in rows:
            monitors.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'inst_id': row['inst_id'],
                'pos_side': row['pos_side'],
                'pos_size': row['pos_size'],
                'avg_price': row['avg_price'],
                'mark_price': row['mark_price'],
                'upl': row['upl'],
                'upl_ratio': row['upl_ratio'],
                'margin': row['margin'],
                'leverage': row['leverage'],
                'profit_rate': row['profit_rate'],
                'alert_type': row['alert_type'],
                'alert_sent': row['alert_sent']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': monitors,
            'total': len(monitors)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor-system/alerts')
def get_anchor_alerts():
    """获取告警历史"""
    try:
        limit = request.args.get('limit', 50, type=int)
        db_path = '/home/user/webapp/anchor_system.db'
        
        conn = sqlite3.connect(db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM anchor_alerts 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        alerts = []
        for row in rows:
            alerts.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'inst_id': row['inst_id'],
                'pos_side': row['pos_side'],
                'profit_rate': row['profit_rate'],
                'alert_type': row['alert_type'],
                'message': row['message'],
                'sent_status': row['sent_status']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'total': len(alerts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor-system/status')
def get_anchor_status():
    """获取系统状态"""
    try:
        import json
        
        # 读取配置
        config_path = '/home/user/webapp/anchor_config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 获取最新监控记录
        db_path = '/home/user/webapp/anchor_system.db'
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM anchor_monitors')
        total_monitors = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM anchor_alerts')
        total_alerts = cursor.fetchone()[0]
        
        cursor.execute('''
        SELECT * FROM anchor_monitors 
        ORDER BY timestamp DESC 
        LIMIT 1
        ''')
        latest = cursor.fetchone()
        
        conn.close()
        
        # 使用默认配置值（因为 anchor_config.json 没有 monitor 键）
        return jsonify({
            'success': True,
            'status': {
                'total_monitors': total_monitors,
                'total_alerts': total_alerts,
                'latest_check': latest[1] if latest else None,
                'config': {
                    'profit_target': 40.0,  # 默认盈利目标 40%
                    'loss_limit': -10.0,     # 默认止损限制 -10%
                    'check_interval': 30,    # 默认检查间隔 30秒
                    'only_short': False      # 默认支持多空
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor-system/profit-records')
def get_anchor_profit_records():
    """获取历史极值记录 - 实盘和模拟盘使用不同的表"""
    try:
        inst_id = request.args.get('inst_id')
        pos_side = request.args.get('pos_side')
        trade_mode = request.args.get('trade_mode', 'real')  # 默认实盘
        
        # 根据 trade_mode 选择不同的表
        table_name = 'anchor_real_profit_records' if trade_mode == 'real' else 'anchor_paper_profit_records'
        
        db_path = '/home/user/webapp/anchor_system.db'
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        if inst_id and pos_side:
            # 查询特定币种的记录
            cursor.execute(f'''
            SELECT record_type, profit_rate, timestamp, pos_size, avg_price, mark_price, upl, margin, leverage
            FROM {table_name}
            WHERE inst_id = ? AND pos_side = ?
            ORDER BY record_type
            ''', (inst_id, pos_side))
        else:
            # 查询所有记录
            cursor.execute(f'''
            SELECT inst_id, pos_side, record_type, profit_rate, timestamp, pos_size, avg_price, mark_price
            FROM {table_name}
            ORDER BY inst_id, pos_side, record_type
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        if inst_id and pos_side:
            for row in rows:
                records.append({
                    'record_type': row[0],
                    'profit_rate': row[1],
                    'timestamp': row[2],
                    'pos_size': row[3],
                    'avg_price': row[4],
                    'mark_price': row[5],
                    'upl': row[6],
                    'margin': row[7],
                    'leverage': row[8]
                })
        else:
            for row in rows:
                records.append({
                    'inst_id': row[0],
                    'pos_side': row[1],
                    'record_type': row[2],
                    'profit_rate': row[3],
                    'timestamp': row[4],
                    'pos_size': row[5],
                    'avg_price': row[6],
                    'mark_price': row[7]
                })
        
        return jsonify({
            'success': True,
            'records': records,
            'total': len(records),
            'trade_mode': trade_mode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor-system/cleanup-extremes', methods=['POST'])
def cleanup_extreme_records():
    """清理错误的极值记录（删除所有亏损记录）"""
    try:
        import sys
        sys.path.insert(0, '/home/user/webapp')
        from extreme_correction_system import (
            init_correction_system, backup_current_data,
            detect_error_records, delete_error_records, get_statistics
        )
        
        # 初始化
        from anchor_system import init_database
        init_database()
        init_correction_system()
        
        # 备份
        backup_count = backup_current_data()
        
        # 检测错误记录
        error_records = detect_error_records()
        
        if not error_records:
            return jsonify({
                'success': True,
                'message': '没有发现错误记录',
                'backup_count': backup_count,
                'deleted_count': 0
            })
        
        # 删除错误记录
        deleted_count = delete_error_records(error_records, "Web端手动清理")
        
        # 获取统计
        stats = get_statistics()
        
        return jsonify({
            'success': True,
            'message': f'已清理 {deleted_count} 条错误记录',
            'backup_count': backup_count,
            'deleted_count': deleted_count,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })


@app.route('/api/anchor-system/extreme-stats')
def get_extreme_stats():
    """获取极值记录统计信息"""
    try:
        import sys
        sys.path.insert(0, '/home/user/webapp')
        from extreme_correction_system import get_statistics, detect_error_records
        
        # 获取统计
        stats = get_statistics()
        
        # 检测错误记录
        error_records = detect_error_records()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'error_count': len(error_records),
            'has_errors': len(error_records) > 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })


@app.route('/api/anchor-system/correction-log')
def get_correction_log():
    """获取纠错日志"""
    try:
        limit = int(request.args.get('limit', 20))
        
        db_path = '/home/user/webapp/anchor_system.db'
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, correction_type, inst_id, pos_side, record_type,
               old_profit_rate, new_profit_rate, reason, created_at
        FROM extreme_corrections_log
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row[0],
                'correction_type': row[1],
                'inst_id': row[2],
                'pos_side': row[3],
                'record_type': row[4],
                'old_profit_rate': row[5],
                'new_profit_rate': row[6],
                'reason': row[7],
                'created_at': row[8]
            })
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })


@app.route('/api/anchor-system/current-positions')
def get_current_positions():
    """获取当前持仓情况 - 模拟盘直接读取数据库，实盘从 OKEx API 实时获取"""
    try:
        import sys
        import sqlite3
        from datetime import datetime
        sys.path.append('/home/user/webapp')
        from anchor_system import get_positions, calculate_profit_rate
        
        # 获取交易模式（默认为 paper 模拟盘）
        trade_mode = request.args.get('trade_mode', 'paper')
        
        # 连接数据库，获取维护后的开仓价格
        DB_PATH = '/home/user/webapp/trading_decision.db'
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 从数据库读取模拟盘数据 - 联合查询维护价格表
        cursor.execute('''
            SELECT 
                p.inst_id, 
                p.pos_side, 
                COALESCE(amp.maintenance_price, p.open_price) as open_price,
                p.open_size, 
                p.updated_time, 
                p.mark_price, 
                p.profit_rate, 
                p.upl, 
                p.lever, 
                p.margin,
                amp.original_open_price,
                amp.maintenance_count,
                p.is_anchor
            FROM position_opens p
            LEFT JOIN anchor_maintenance_prices amp 
                ON p.inst_id = amp.inst_id 
                AND p.pos_side = amp.pos_side 
                AND p.trade_mode = amp.trade_mode
            WHERE p.trade_mode = ?
        ''', (trade_mode,))
        
        db_positions = cursor.fetchall()
        conn.close()
        
        # 如果是模拟盘，直接使用数据库数据
        if trade_mode == 'paper':
            position_list = []
            for row in db_positions:
                profit_rate = row['profit_rate'] if row['profit_rate'] is not None else 0.0
                
                # 判断状态
                status = '监控中'
                status_class = 'normal'
                if profit_rate >= 40:
                    status = '接近盈利目标'
                    status_class = 'profit'
                elif profit_rate <= -10:
                    status = '接近止损'
                    status_class = 'loss'
                
                position_list.append({
                    'inst_id': row['inst_id'],
                    'pos_side': row['pos_side'],
                    'pos_size': abs(float(row['open_size'])),
                    'avg_price': float(row['open_price']),  # 现在使用维护价格
                    'mark_price': float(row['mark_price']) if row['mark_price'] else 0.0,
                    'lever': int(row['lever']) if row['lever'] else 10,
                    'upl': float(row['upl']) if row['upl'] else 0.0,
                    'margin': float(row['margin']) if row['margin'] else 0.0,
                    'profit_rate': profit_rate,
                    'status': status,
                    'status_class': status_class,
                    'is_anchor': int(row['is_anchor']) if row['is_anchor'] else 0
                })
            
            return jsonify({
                'success': True,
                'positions': position_list,
                'total': len(position_list),
                'trade_mode': trade_mode
            })
        
        # 如果是实盘，从 OKEx API 获取实时持仓
        okex_positions = get_positions()
        
        if not okex_positions or len(okex_positions) == 0:
            return jsonify({
                'success': True,
                'positions': [],
                'total': 0,
                'trade_mode': trade_mode
            })
        
        # 将数据库记录转换为字典
        db_positions_dict = {(row['inst_id'], row['pos_side']): row for row in db_positions}
        
        # 获取维护次数统计（不再限制今日，统计所有维护次数）
        import json as json_lib
        from datetime import datetime
        from collections import defaultdict
        
        maintenance_file = 'maintenance_orders.json'
        maintenance_counts = defaultdict(int)
        
        if os.path.exists(maintenance_file):
            try:
                with open(maintenance_file, 'r', encoding='utf-8') as f:
                    maintenance_records = json_lib.load(f)
                
                # 不再按日期过滤，统计所有维护次数
                for record in maintenance_records:
                    inst_id = record.get('inst_id', '')
                    pos_side = record.get('pos_side', '')
                    # 使用 (inst_id, pos_side) 作为key，区分多单和空单
                    key = (inst_id, pos_side)
                    maintenance_counts[key] += 1
            except Exception as e:
                print(f"读取维护记录失败: {e}")
        
        position_list = []
        for pos in okex_positions:
            inst_id = pos.get('instId')
            pos_side = pos.get('posSide')
            pos_value = float(pos.get('pos', 0))
            
            # 跳过持仓量为0的
            if pos_value == 0:
                continue
            
            # 查找数据库记录（可能是锚点单，也可能不是）
            db_record = db_positions_dict.get((inst_id, pos_side))
            
            # 安全转换函数
            def safe_float(value, default=0):
                try:
                    if value == '' or value is None:
                        return default
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            def safe_int(value, default=10):
                try:
                    if value == '' or value is None:
                        return default
                    return int(value)
                except (ValueError, TypeError):
                    return default
            
            # 计算数据
            okex_avg_price = safe_float(pos.get('avgPx', 0))
            mark_price = safe_float(pos.get('markPx', 0))
            lever = safe_int(pos.get('lever', 10))
            upl = safe_float(pos.get('upl', 0))
            # 使用理论保证金：持仓价值 / 杠杆
            # 这与OKEx Web界面显示的"保证金"一致
            pos_value_abs = abs(pos_value)  # 持仓数量（绝对值）
            margin = (pos_value_abs * mark_price) / lever if lever > 0 and mark_price > 0 else 0.01
            
            # 直接使用OKEx的收益率（uplRatio），转换为百分比
            okex_profit_ratio = safe_float(pos.get('uplRatio', 0))
            profit_rate = okex_profit_ratio * 100  # 转换为百分比
            
            # 如果数据库中有记录，使用数据库的开仓价格
            if db_record:
                avg_price = float(db_record['open_price'])
                is_anchor = int(db_record['is_anchor']) if db_record['is_anchor'] else 0
            else:
                # 如果数据库中没有，使用 OKEx 的价格，标记为非锚点单
                avg_price = okex_avg_price
                is_anchor = 0
            
            # 判断状态
            status = '监控中'
            status_class = 'normal'
            if profit_rate >= 40:
                status = '接近盈利目标'
                status_class = 'profit'
            elif profit_rate <= -10:
                status = '接近止损'
                status_class = 'loss'
            
            position_list.append({
                'inst_id': inst_id,
                'pos_side': pos_side,
                'pos_size': abs(pos_value),
                'avg_price': avg_price,
                'mark_price': mark_price,
                'lever': lever,
                'upl': upl,
                'margin': margin,
                'profit_rate': profit_rate,
                'status': status,
                'status_class': status_class,
                'is_anchor': is_anchor,
                'maintenance_count_today': maintenance_counts.get((inst_id, pos_side), 0),  # 总维护次数（不再限制今日）
                'total_maintenance_count': maintenance_counts.get((inst_id, pos_side), 0)  # 新增字段，明确是总次数
            })
        
        return jsonify({
            'success': True,
            'positions': position_list,
            'total': len(position_list),
            'trade_mode': trade_mode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor-system/today-statistics')
def get_today_statistics():
    """获取今日统计数据"""
    try:
        import sqlite3
        import requests
        from datetime import datetime
        
        trade_mode = request.args.get('trade_mode', 'real')
        
        # 获取维护次数统计
        maintenance_stats_response = requests.get('http://localhost:5000/api/anchor/maintenance-stats', timeout=5)
        maintenance_stats = {}
        if maintenance_stats_response.status_code == 200:
            maintenance_data = maintenance_stats_response.json()
            if maintenance_data.get('success'):
                maintenance_stats = maintenance_data.get('stats', {})
        
        # 统计今日维护次数（按类型分类）
        maintenance_file = 'maintenance_orders.json'
        auto_maintain_long = 0
        auto_maintain_short = 0
        super_maintain_long = 0
        super_maintain_short = 0
        
        try:
            import json as json_lib
            import os
            if os.path.exists(maintenance_file):
                with open(maintenance_file, 'r', encoding='utf-8') as f:
                    records = json_lib.load(f)
                
                today = get_china_today()
                for record in records:
                    if record.get('created_at', '').startswith(today):
                        pos_side = record.get('pos_side')
                        maintenance_type = record.get('maintenance_type', 'normal')
                        
                        if maintenance_type == 'super_maintain':
                            if pos_side == 'long':
                                super_maintain_long += 1
                            else:
                                super_maintain_short += 1
                        else:
                            if pos_side == 'long':
                                auto_maintain_long += 1
                            else:
                                auto_maintain_short += 1
        except Exception as e:
            print(f"统计维护次数失败: {e}")
        
        # 获取当前持仓统计
        positions_response = requests.get(
            f'http://localhost:5000/api/anchor-system/current-positions?trade_mode={trade_mode}',
            timeout=10
        )
        
        total_positions = 0
        anchor_positions = 0
        warning_positions = 0
        
        if positions_response.status_code == 200:
            positions_data = positions_response.json()
            if positions_data.get('success'):
                positions = positions_data.get('positions', [])
                total_positions = len(positions)
                
                for pos in positions:
                    if pos.get('is_anchor'):
                        anchor_positions += 1
                    if pos.get('profit_rate', 0) <= -8:
                        warning_positions += 1
        
        return jsonify({
            'success': True,
            'statistics': {
                'auto_maintain_long': auto_maintain_long,
                'auto_maintain_short': auto_maintain_short,
                'super_maintain_long': super_maintain_long,
                'super_maintain_short': super_maintain_short,
                'total_positions': total_positions,
                'anchor_positions': anchor_positions,
                'warning_positions': warning_positions
            },
            'trade_mode': trade_mode,
            'date': get_china_today()
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/anchor-system/sub-account-positions')
def get_sub_account_positions():
    """获取子账号持仓"""
    try:
        import json as json_lib
        import requests
        import hmac
        import base64
        import hashlib
        from datetime import datetime
        
        # 加载子账号配置
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json_lib.load(f)
        
        all_positions = []
        
        # 遍历所有子账号
        for sub_account in config.get('sub_accounts', []):
            if not sub_account.get('enabled'):
                continue
            
            account_name = sub_account['account_name']
            api_key = sub_account['api_key']
            secret_key = sub_account['secret_key']
            passphrase = sub_account['passphrase']
            
            api_success = False
            
            try:
                # 生成OKEx签名 - GET请求需要在签名中包含查询参数
                request_path = '/api/v5/account/positions'
                query_string = 'instType=SWAP'
                timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                message = timestamp + 'GET' + request_path + '?' + query_string
                mac = hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                )
                signature = base64.b64encode(mac.digest()).decode('utf-8')
                
                headers = {
                    'OK-ACCESS-KEY': api_key,
                    'OK-ACCESS-SIGN': signature,
                    'OK-ACCESS-TIMESTAMP': timestamp,
                    'OK-ACCESS-PASSPHRASE': passphrase,
                    'Content-Type': 'application/json'
                }
                
                # 获取持仓
                url = f"https://www.okx.com{request_path}"
                params = {'instType': 'SWAP'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"⚠️ 子账号 {account_name} API响应: code={data.get('code')}, 持仓数={len(data.get('data', []))}")
                    if data.get('code') == '0':
                        api_success = True
                        # 处理持仓数据
                        for pos in data.get('data', []):
                            # 安全转换float，处理空字符串
                            try:
                                pos_size = float(pos.get('pos') or 0)
                            except:
                                pos_size = 0
                            
                            if pos_size == 0:
                                continue
                            
                            try:
                                avg_px = float(pos.get('avgPx') or 0)
                                mark_px = float(pos.get('markPx') or 0)
                                upl = float(pos.get('upl') or 0)
                                notional_usd = float(pos.get('notionalUsd') or 0)
                                # 打印原始字段值
                                print(f"🔍 原始数据 - imr: {pos.get('imr')}, margin: {pos.get('margin')}, mgnRatio: {pos.get('mgnRatio')}")
                                # 优先使用 margin（占用保证金），而不是 imr（初始保证金）
                                margin = float(pos.get('margin') or pos.get('imr') or 0)
                                print(f"💰 最终使用的保证金: {margin}")
                            except Exception as e:
                                print(f"⚠️ 数据转换失败: {e}, pos={pos}")
                                continue
                            
                            leverage = float(pos.get('lever') or 10)  # 确保leverage是float类型
                            pos_side = pos.get('posSide')
                            
                            # ✅ 使用实时价格计算收益率（与前端一致）
                            if avg_px > 0 and mark_px > 0:
                                if pos_side == 'long':
                                    # 多单：(当前价 - 开仓价) / 开仓价 * 杠杆 * 100
                                    profit_rate = (mark_px - avg_px) / avg_px * leverage * 100
                                else:  # short
                                    # 空单：(开仓价 - 当前价) / 开仓价 * 杠杆 * 100
                                    profit_rate = (avg_px - mark_px) / avg_px * leverage * 100
                                print(f"📊 收益率计算: {pos['instId']} {pos_side}, 开仓价={avg_px:.4f}, 标记价={mark_px:.4f}, 杠杆={leverage}x, 收益率={profit_rate:.2f}%")
                            else:
                                profit_rate = 0
                                print(f"⚠️ {pos['instId']} 价格数据异常，收益率设为0")
                            
                            # 获取维护次数
                            maintenance_count = 0
                            try:
                                with open('sub_account_maintenance.json', 'r', encoding='utf-8') as f:
                                    maintenance_data = json.load(f)
                                today = get_china_today()
                                # Key格式: Wu666666_CRV-USDT-SWAP_long
                                key = f"{account_name}_{pos['instId']}_{pos['posSide']}"
                                if key in maintenance_data:
                                    record = maintenance_data[key]
                                    # 检查日期是否是今天
                                    if record.get('date') == today:
                                        maintenance_count = record.get('count', 0)
                            except Exception as e:
                                print(f"读取维护次数失败: {e}")
                                pass
                            
                            all_positions.append({
                                'account_name': account_name,
                                'inst_id': pos['instId'],
                                'pos_side': pos['posSide'],
                                'pos_size': abs(pos_size),
                                'avg_price': avg_px,
                                'mark_price': mark_px,
                                'leverage': leverage,
                                'margin': margin,
                                'upl': upl,
                                'profit_rate': profit_rate,
                                'notional_usd': abs(notional_usd),
                                'maintenance_count': maintenance_count,
                                'status': '正常',
                                'is_sub_account': True
                            })
            
            except Exception as e:
                print(f"获取子账号 {account_name} 持仓失败: {e}")
            
            # 如果API失败，使用本地记录
            if not api_success:
                print(f"⚠️ 子账号 {account_name} API失败，使用本地记录")
                try:
                    with open('sub_account_opened_positions.json', 'r', encoding='utf-8') as f:
                        opened_positions = json_lib.load(f)
                    
                    for key, pos_info in opened_positions.items():
                        if pos_info['account_name'] == account_name:
                            # 获取维护次数
                            maintenance_count = 0
                            try:
                                with open('sub_account_maintenance_count.json', 'r', encoding='utf-8') as f:
                                    counts = json_lib.load(f)
                                today = get_china_today()
                                count_key = f"{account_name}:{pos_info['inst_id']}:{pos_info['pos_side']}:{today}"
                                maintenance_count = counts.get(count_key, 0)
                            except:
                                pass
                            
                            # 添加基于本地记录的持仓（没有实时价格数据）
                            all_positions.append({
                                'account_name': account_name,
                                'inst_id': pos_info['inst_id'],
                                'pos_side': pos_info['pos_side'],
                                'pos_size': 0,  # 未知
                                'avg_price': 0,  # 未知
                                'mark_price': 0,  # 未知
                                'leverage': '10',
                                'margin': 10,  # 估算
                                'upl': 0,  # 未知
                                'profit_rate': 0,  # 未知
                                'notional_usd': 10,  # 估算
                                'maintenance_count': maintenance_count,
                                'status': '⚠️ 数据来自本地记录',
                                'is_sub_account': True,
                                'from_local': True
                            })
                except Exception as e:
                    print(f"读取本地持仓记录失败: {e}")
        
        # 合并同一账户、同一币种、同一方向的持仓（逐仓模式）
        merged_positions = {}
        for pos in all_positions:
            # 创建合并键：账户名_币种_方向
            merge_key = f"{pos['account_name']}_{pos['inst_id']}_{pos['pos_side']}"
            
            if merge_key in merged_positions:
                # 已存在，合并数据
                existing = merged_positions[merge_key]
                
                # 计算加权平均开仓价
                total_value = existing['avg_price'] * existing['pos_size'] + pos['avg_price'] * pos['pos_size']
                total_size = existing['pos_size'] + pos['pos_size']
                if total_size > 0:
                    weighted_avg_price = total_value / total_size
                else:
                    weighted_avg_price = existing['avg_price']
                
                # 合并数据
                existing['pos_size'] += pos['pos_size']
                existing['avg_price'] = weighted_avg_price
                existing['margin'] += pos['margin']
                existing['upl'] += pos['upl']
                existing['notional_usd'] += pos['notional_usd']
                
                # 重新计算收益率（基于总保证金）
                if existing['margin'] > 0:
                    existing['profit_rate'] = (existing['upl'] / existing['margin']) * 100
                else:
                    existing['profit_rate'] = 0
                
                # 维护次数取最大值
                existing['maintenance_count'] = max(existing['maintenance_count'], pos['maintenance_count'])
                
                # 标记价格使用最新的（假设最后一个是最新的）
                existing['mark_price'] = pos['mark_price']
            else:
                # 新持仓，直接添加
                merged_positions[merge_key] = pos.copy()
        
        # 转换为列表
        final_positions = list(merged_positions.values())
        
        return jsonify({
            'success': True,
            'positions': final_positions,
            'total': len(final_positions)
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/sub-account-config', methods=['GET', 'POST'])
def sub_account_config():
    """子账户配置管理"""
    try:
        import json as json_lib
        import os
        
        config_file = 'sub_account_config.json'
        
        if request.method == 'GET':
            # 读取配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json_lib.load(f)
            else:
                config = {
                    'sub_accounts': [],
                    'main_account': {'account_name': 'JAMESYI', 'enabled': True}
                }
            
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            # 更新配置
            data = request.json
            
            # 读取现有配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json_lib.load(f)
            else:
                config = {
                    'sub_accounts': [],
                    'main_account': {'account_name': 'JAMESYI', 'enabled': True}
                }
            
            # 更新所有子账户的超级维护开关
            if 'super_maintain_long_enabled' in data:
                for sub_account in config.get('sub_accounts', []):
                    sub_account['super_maintain_long_enabled'] = data['super_maintain_long_enabled']
            
            if 'super_maintain_short_enabled' in data:
                for sub_account in config.get('sub_accounts', []):
                    sub_account['super_maintain_short_enabled'] = data['super_maintain_short_enabled']
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json_lib.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '配置已更新',
                'config': config
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

# ====================交易决策系统路由 ====================

@app.route('/trading-decision')
def trading_decision_page():
    """交易决策系统管理页面 - 重定向到统一管理页面"""
    return redirect('/trading-manager')

@app.route('/api/trading/anchor-maintenance/logs')
def anchor_maintenance_logs_api():
    """获取锚点单维护日志"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/trading_decision.db', timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, inst_id, pos_side, original_size, original_price, 
               original_margin, current_price, profit_rate, step, action,
               trade_size, trade_price, remaining_size, remaining_margin,
               trigger_reason, decision_log, status, executed_at, created_at
        FROM anchor_maintenance_logs
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'original_size': float(row[3]),
                'original_price': float(row[4]),
                'original_margin': float(row[5]),
                'current_price': float(row[6]),
                'profit_rate': float(row[7]),
                'step': row[8],
                'action': row[9],
                'trade_size': float(row[10]),
                'trade_price': float(row[11]),
                'remaining_size': float(row[12]),
                'remaining_margin': float(row[13]),
                'trigger_reason': row[14],
                'decision_log': row[15],
                'status': row[16],
                'executed_at': row[17],
                'created_at': row[18]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/trading/config', methods=['GET', 'POST'])
def trading_config_api():
    """交易配置API"""
    config_file = '/home/user/webapp/trading_config.json'
    
    if request.method == 'GET':
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return jsonify({'success': True, 'config': config})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            new_config = request.json
            
            # 更新数据库中的配置
            conn = sqlite3.connect('/home/user/webapp/trading_decision.db', timeout=10.0)
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE market_config SET
                market_mode = ?,
                market_trend = ?,
                total_capital = ?,
                position_limit_percent = ?,
                anchor_capital_limit = ?,
                allow_long = ?,
                enabled = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            ''', (
                new_config.get('market_mode'),
                new_config.get('market_trend'),
                new_config.get('total_capital'),
                new_config.get('position_limit_percent'),
                new_config.get('anchor_capital_limit'),
                1 if new_config.get('allow_long') else 0,
                1 if new_config.get('enabled') else 0
            ))
            conn.commit()
            conn.close()
            
            # 更新JSON文件
            with open(config_file, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            return jsonify({'success': True, 'message': '配置更新成功'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/decisions')
def trading_decisions_api():
    """获取交易决策记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/trading_decision.db', timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(f'''
        SELECT id, inst_id, pos_side, action, decision_type, current_size,
               target_size, close_size, close_percent, profit_rate,
               current_price, reason, executed, timestamp
        FROM trading_decisions
        ORDER BY id DESC
        LIMIT {limit}
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        decisions = []
        for row in rows:
            decisions.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'action': row[3],
                'decision_type': row[4],
                'current_size': row[5],
                'target_size': row[6],
                'close_size': row[7],
                'close_percent': row[8],
                'profit_rate': row[9],
                'current_price': row[10],
                'reason': row[11],
                'executed': bool(row[12]),
                'timestamp': row[13]
            })
        
        return jsonify({'success': True, 'decisions': decisions, 'total': len(decisions)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/signals')
def trading_signals_api():
    """获取交易信号（供其他账号使用）"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/trading_decision.db', timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(f'''
        SELECT id, inst_id, signal_type, action, price, size,
               profit_rate, reason, timestamp
        FROM trading_signals
        ORDER BY id DESC
        LIMIT {limit}
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'inst_id': row[1],
                'signal_type': row[2],
                'action': row[3],
                'price': row[4],
                'size': row[5],
                'profit_rate': row[6],
                'reason': row[7],
                'timestamp': row[8]
            })
        
        return jsonify({'success': True, 'signals': signals, 'total': len(signals)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trading/maintenance')
def trading_maintenance_api():
    """获取锚点单维护记录"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect('/home/user/webapp/trading_decision.db', timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(f'''
        SELECT id, inst_id, pos_side, original_size, original_price,
               maintenance_price, maintenance_size, profit_rate,
               action, status, timestamp
        FROM anchor_maintenance
        ORDER BY id DESC
        LIMIT {limit}
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append({
                'id': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'original_size': row[3],
                'original_price': row[4],
                'maintenance_price': row[5],
                'maintenance_size': row[6],
                'profit_rate': row[7],
                'action': row[8],
                'status': row[9],
                'timestamp': row[10]
            })
        
        return jsonify({'success': True, 'records': records, 'total': len(records)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """实时监控仪表板 - 重定向到统一管理页面"""
    return redirect('/trading-manager')

@app.route('/trading-manager')
def trading_manager():
    """交易管理界面 - 模拟交易系统"""
    try:
        with open('/home/user/webapp/templates/trading_manager.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加缓存控制头，强制浏览器刷新
        response = make_response(content)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except FileNotFoundError:
        return "Trading manager template not found", 404
    except Exception as e:
        return f"Error loading trading manager: {str(e)}", 500

@app.route('/simulated-trades')
def simulated_trades():
    """模拟交易详情界面"""
    try:
        with open('/home/user/webapp/templates/simulated_trades.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Simulated trades template not found", 404
    except Exception as e:
        return f"Error loading simulated trades: {str(e)}", 500

@app.route('/api/anchor-system/warnings')
def get_anchor_warnings():
    """获取当前活跃的锚点预警"""
    try:
        import sqlite3
        
        # 获取交易模式
        trade_mode = request.args.get('trade_mode', 'paper')
        
        DB_PATH = '/home/user/webapp/trading_decision.db'
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询活跃预警
        cursor.execute('''
            SELECT inst_id, pos_side, open_price, current_price, profit_rate, 
                   open_size, warning_level, alert_message, status, created_at, trade_mode
            FROM anchor_warning_monitor
            WHERE status = 'active' AND trade_mode = ?
            ORDER BY profit_rate ASC
        ''', (trade_mode,))
        
        warnings = cursor.fetchall()
        conn.close()
        
        warning_list = []
        for row in warnings:
            warning_list.append({
                'inst_id': row['inst_id'],
                'pos_side': row['pos_side'],
                'open_price': float(row['open_price']),
                'current_price': float(row['current_price']) if row['current_price'] else 0.0,
                'profit_rate': float(row['profit_rate']),
                'open_size': float(row['open_size']),
                'warning_level': row['warning_level'],
                'alert_message': row['alert_message'],
                'status': row['status'],
                'created_at': row['created_at'],
                'trade_mode': row['trade_mode']
            })
        
        return jsonify({
            'success': True,
            'warnings': warning_list,
            'total': len(warning_list),
            'trade_mode': trade_mode
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/super-maintain-anchor', methods=['POST'])
def super_maintain_anchor_order():
    """超级维护锚点单：买入100U，保留10U，卖出剩余"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE, OKEX_REST_URL
        
        data = request.json
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        current_pos_size = float(data.get('current_pos_size', 0))
        maintenance_amount = float(data.get('maintenance_amount', 100))  # 默认100U
        target_margin = float(data.get('target_margin', 10))  # 默认保留10U
        
        print(f"🚀 开始超级维护: {inst_id} {pos_side} 当前持仓={current_pos_size}")
        print(f"   维护金额: {maintenance_amount}U, 目标保证金: {target_margin}U")
        
        # 生成签名函数
        def generate_signature(timestamp, method, request_path, body=''):
            if body:
                body = json.dumps(body)
            message = timestamp + method + request_path + body
            mac = hmac.new(
                bytes(OKEX_SECRET_KEY, encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod=hashlib.sha256
            )
            return base64.b64encode(mac.digest()).decode()
        
        def get_headers(method, request_path, body=''):
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            sign = generate_signature(timestamp, method, request_path, body)
            return {
                'OK-ACCESS-KEY': OKEX_API_KEY,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': OKEX_PASSPHRASE,
                'Content-Type': 'application/json'
            }
        
        # 获取当前标记价格和杠杆
        position_path = f'/api/v5/account/positions?instType=SWAP&instId={inst_id}'
        headers = get_headers('GET', position_path)
        pos_response = requests.get(OKEX_REST_URL + position_path, headers=headers, timeout=10)
        pos_data = pos_response.json()
        
        mark_price = 0
        lever = 10
        if pos_data.get('code') == '0' and pos_data.get('data'):
            for position in pos_data['data']:
                if position.get('posSide') == pos_side:
                    mark_price = float(position.get('markPx', 0))
                    lever = int(position.get('lever', 10))
                    break
        
        if mark_price == 0:
            return jsonify({
                'success': False,
                'message': f'无法获取标记价格，检查持仓和行情数据'
            })
        
        print(f"📊 标记价格: ${mark_price}, 杠杆: {lever}x")
        
        # 计算买入数量：maintenance_amount × 杠杆 / 标记价格
        buy_size_raw = (maintenance_amount * lever) / mark_price
        
        # 获取合约面值
        inst_path = f'/api/v5/public/instruments?instType=SWAP&instId={inst_id}'
        inst_resp = requests.get(OKEX_REST_URL + inst_path, timeout=10)
        inst_data = inst_resp.json()
        lot_size = 1
        if inst_data.get('code') == '0' and inst_data.get('data'):
            lot_size = float(inst_data['data'][0].get('ctVal', 1))
        
        # 向下取整到lot_size的整数倍
        buy_size = int(buy_size_raw / lot_size) * lot_size
        
        print(f"💰 新开仓数量: {buy_size} (原始: {buy_size_raw:.2f}, lot_size: {lot_size})")
        
        # 计算保留目标：target_margin × 杠杆 / 标记价格
        keep_size_raw = (target_margin * lever) / mark_price
        keep_size = int(keep_size_raw / lot_size) * lot_size
        
        # 计算需要平仓的数量 = 旧持仓 + 新开仓 - 最终保留
        total_pos_size = current_pos_size + buy_size
        close_size_raw = total_pos_size - keep_size
        close_size = int(close_size_raw / lot_size) * lot_size if close_size_raw > 0 else 0
        
        print(f"📊 仓位计算:")
        print(f"   当前持仓: {current_pos_size} 张")
        print(f"   新开仓: {buy_size} 张")
        print(f"   总持仓: {total_pos_size} 张")
        print(f"   最终保留: {keep_size} 张 (目标保证金 {target_margin}U)")
        print(f"   需要平仓: {close_size} 张")
        
        # 🔄 优化后的流程：先开仓再平仓（更省手续费）
        order_path = '/api/v5/trade/order'
        
        # 第一步：开仓新持仓（维护金额对应的仓位）
        print(f"📊 第1步：开仓新持仓 {buy_size} 张（{maintenance_amount}U）")
        buy_side = 'sell' if pos_side == 'short' else 'buy'
        
        buy_order_body = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式：每个持仓独立保证金
            'side': buy_side,
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(buy_size),
            'lever': str(lever)
        }
        
        headers = get_headers('POST', order_path, buy_order_body)
        buy_response = requests.post(
            OKEX_REST_URL + order_path,
            headers=headers,
            json=buy_order_body,
            timeout=10
        )
        buy_data = buy_response.json()
        
        if buy_data.get('code') != '0':
            return jsonify({
                'success': False,
                'message': f'开仓失败: {buy_data.get("msg")}',
                'error_code': buy_data.get('code')
            })
        
        buy_order_id = buy_data['data'][0]['ordId']
        print(f"✅ 开仓订单提交成功: {buy_order_id}")
        
        # 等待3秒让订单成交
        import time
        time.sleep(3)
        
        # 第二步：平仓多余持仓，保留目标保证金
        if close_size <= 0:
            print(f"⚠️  无需平仓，当前持仓已达到目标")
            return jsonify({
                'success': True,
                'message': '超级维护完成（无需平仓）',
                'data': {
                    'buy_order_id': buy_order_id,
                    'buy_size': buy_size,
                    'close_size': 0,
                    'keep_size': keep_size
                }
            })
        
        print(f"📊 第2步：平仓多余持仓 {close_size} 张（保留: {keep_size} 张 = {target_margin}U）")
        close_side = 'buy' if pos_side == 'short' else 'sell'
        
        close_order_body = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式：每个持仓独立保证金
            'side': close_side,
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(close_size)
        }
        
        headers = get_headers('POST', order_path, close_order_body)
        close_response = requests.post(
            OKEX_REST_URL + order_path,
            headers=headers,
            json=close_order_body,
            timeout=10
        )
        close_data = close_response.json()
        
        if close_data.get('code') != '0':
            return jsonify({
                'success': False,
                'message': f'平仓失败: {close_data.get("msg")}',
                'buy_order_id': buy_order_id,
                'error_code': close_data.get('code')
            })
        
        close_order_id = close_data['data'][0]['ordId']
        print(f"✅ 第2步平仓订单提交成功: {close_order_id}")
        
        # 保存超级维护记录（计数+1）
        try:
            import os
            maintenance_file = 'maintenance_orders.json'
            
            if os.path.exists(maintenance_file):
                with open(maintenance_file, 'r', encoding='utf-8') as f:
                    records = json_lib.load(f)
            else:
                records = []
            
            # 添加超级维护记录（优化后流程：平仓→开仓→再平仓）
            new_record = {
                'id': len(records) + 1,
                'inst_id': inst_id,
                'pos_side': pos_side,
                'type': 'super_maintain',  # 标记为超级维护
                'close_old_order_id': close_order_id,  # 平掉旧持仓
                'buy_order_id': buy_order_id,
                'buy_size': buy_size,
                'sell_order_id': sell_order_id,  # 卖出到目标
                'sell_size': sell_size,
                'keep_size': keep_size,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success',
                'maintenance_count': 1  # 超级维护也是计数+1
            }
            
            records.insert(0, new_record)
            
            if len(records) > 100:
                records = records[:100]
            
            with open(maintenance_file, 'w', encoding='utf-8') as f:
                json_lib.dump(records, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 超级维护记录已保存")
        except Exception as save_error:
            print(f"⚠️  保存超级维护记录失败: {save_error}")
        
        print(f"🎉 超级维护完成！流程：平仓旧持仓({current_pos_size}张) → 开仓新持仓({new_pos_size}张) → 平到目标({keep_size}张)")
        
        return jsonify({
            'success': True,
            'message': '超级维护执行成功（优化流程：先平仓再开仓）',
            'data': {
                'close_old_order_id': close_order_id,
                'buy_order_id': buy_order_id,
                'buy_size': buy_size,
                'sell_order_id': sell_order_id,
                'sell_size': sell_size,
                'keep_size': keep_size,
                'new_pos_size': new_pos_size
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'超级维护失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/maintain-anchor', methods=['POST'])
def maintain_anchor_order():
    """维护锚点单：以市价买入10倍底仓数量（10倍杠杆），然后立即平掉92%"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE, OKEX_REST_URL
        
        data = request.json
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')  # 'short' or 'long'
        pos_size = float(data.get('pos_size'))
        auto_adjust = data.get('auto_adjust', False)  # 是否自动调整保证金（只用于自动维护-10%）
        
        # 计算10倍数量
        order_size = pos_size * 10
        
        # 检查维护次数（不再限制每日次数）
        # 注释掉原有的今日维护次数限制逻辑
        # import json as json_lib_check
        # import os
        # from collections import defaultdict
        
        # maintenance_file = 'maintenance_orders.json'
        # today = get_china_today()
        
        # # 统计今天的维护次数
        # today_count = 0
        # if os.path.exists(maintenance_file):
        #     try:
        #         with open(maintenance_file, 'r', encoding='utf-8') as f:
        #             records = json_lib_check.load(f)
        #         
        #         for record in records:
        #             created_at = record.get('created_at', '')
        #             if created_at.startswith(today):
        #                 if record.get('inst_id') == inst_id and record.get('pos_side') == pos_side:
        #                     today_count += 1
        #     except Exception as e:
        #         print(f"读取维护记录失败: {e}")
        
        # print(f"📊 {inst_id} {pos_side} 今日已维护次数: {today_count}/3")
        
        # # 检查是否超过每日上限
        # if today_count >= 3:
        #     return jsonify({
        #         'success': False,
        #         'message': f'今日维护次数已达上限(3次)，请明天再试',
        #         'today_count': today_count,
        #         'max_count': 3
        #     })
        
        # 🔄 优化后的流程：先开仓再平仓（节省手续费）
        # 第一步：开仓新持仓
        print(f"📊 第1步：开仓新持仓 {order_size} 张（10倍底仓数量）")
        
        # 生成签名
        def generate_signature(timestamp, method, request_path, body=''):
            if body:
                body = json.dumps(body)
            message = timestamp + method + request_path + body
            mac = hmac.new(
                bytes(OKEX_SECRET_KEY, encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod=hashlib.sha256
            )
            return base64.b64encode(mac.digest()).decode()
        
        def get_headers(method, request_path, body=''):
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            sign = generate_signature(timestamp, method, request_path, body)
            return {
                'OK-ACCESS-KEY': OKEX_API_KEY,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': OKEX_PASSPHRASE,
                'Content-Type': 'application/json'
            }
        
        order_path = '/api/v5/trade/order'
        
        # 设置杠杆为10倍
        leverage_path = '/api/v5/account/set-leverage'
        leverage_body = {
            'instId': inst_id,
            'lever': '10',
            'mgnMode': 'isolated',
            'posSide': pos_side
        }
        headers = get_headers('POST', leverage_path, leverage_body)
        leverage_response = requests.post(
            OKEX_REST_URL + leverage_path,
            headers=headers,
            json=leverage_body,
            timeout=10
        )
        leverage_result = leverage_response.json()
        if leverage_result.get('code') == '0':
            print(f"✅ 杠杆设置成功: {lever}x")
        else:
            print(f"⚠️ 杠杆设置失败: {leverage_result}")
        
        import time
        
        # 确定开仓方向
        open_side = 'sell' if pos_side == 'short' else 'buy'
        
        open_order_body = {
            'instId': inst_id,
            'tdMode': 'isolated',
            'side': open_side,
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(order_size),
            'lever': str(lever)
        }
        
        headers = get_headers('POST', order_path, open_order_body)
        open_response = requests.post(
            OKEX_REST_URL + order_path,
            headers=headers,
            json=open_order_body,
            timeout=10
        )
        
        open_result = open_response.json()
        
        # 记录详细的响应日志
        print(f"📝 OKEx开仓响应: {open_result}")
        
        if open_result.get('code') != '0':
            error_msg = open_result.get('msg', '未知错误')
            error_code = open_result.get('code', '未知代码')
            print(f"❌ OKEx API错误 - Code: {error_code}, Message: {error_msg}")
            
            # 提供更友好的错误提示
            if 'permission' in error_msg.lower():
                error_msg = f"{error_msg}\n\n💡 解决方案：\n1. 登录OKEx后台 (www.okx.com)\n2. 进入API管理页面\n3. 确认API密钥已勾选「交易」权限\n4. 如未勾选，需要重新创建API密钥"
            
            return jsonify({
                'success': False,
                'message': f"开仓失败: {error_msg}",
                'error_code': error_code,
                'full_response': open_result
            })
        
        open_order_id = open_result['data'][0]['ordId']
        print(f"✅ 开仓订单提交成功，订单ID: {open_order_id}")
        
        # 等待订单成交（增加等待时间到3秒）
        print(f"⏳ 等待3秒确保订单成交...")
        time.sleep(3)
        
        # 查询订单状态
        order_detail_path = f'/api/v5/trade/order?instId={inst_id}&ordId={open_order_id}'
        headers = get_headers('GET', order_detail_path)
        order_detail_response = requests.get(
            OKEX_REST_URL + order_detail_path,
            headers=headers,
            timeout=10
        )
        order_detail = order_detail_response.json()
        print(f"📝 开仓订单状态: {order_detail}")
        
        # 检查订单是否完全成交
        if order_detail.get('code') == '0' and order_detail.get('data'):
            order_state = order_detail['data'][0].get('state', '')
            if order_state != 'filled':
                print(f"⚠️ 订单未完全成交，状态: {order_state}")
                # 继续尝试平仓
        
        
        # 第二步：平掉多余持仓，保留target_margin对应的数量
        print(f"📊 第2步：平到目标保证金 {target_margin}U（平掉多余持仓）")
        
        import math
        
        # 计算应该保留的数量
        keep_size_raw = (target_margin * lever) / mark_price
        keep_size = math.floor(keep_size_raw)
        
        # 确保至少保留0.6U的保证金
        MIN_MARGIN = 0.6
        min_keep_size = math.ceil((MIN_MARGIN * lever) / mark_price)
        if keep_size < min_keep_size:
            print(f"⚠️ 保留数量 {keep_size} 张小于最小要求 {min_keep_size} 张（最小保证金 {MIN_MARGIN}U），强制设置为 {min_keep_size} 张")
            keep_size = min_keep_size
        
        # 计算总持仓：原持仓 + 新开仓
        total_pos_size = pos_size + order_size
        
        # 计算需要平掉的数量
        close_size = max(0, total_pos_size - keep_size)
        
        print(f"📊 仓位计算:")
        print(f"   当前持仓: {pos_size} 张")
        print(f"   新开仓: {order_size} 张")
        print(f"   总持仓: {total_pos_size} 张")
        print(f"   最终保留: {keep_size} 张 = {target_margin}U")
        print(f"   需要平仓: {close_size} 张")
        
        if close_size <= 0:
            print(f"✅ 跳过第2步：不需要平仓（close_size={close_size}）")
            close_order_id = 'SKIPPED'
        else:
            # 平仓方向与开仓相反
            close_side = 'buy' if pos_side == 'short' else 'sell'
            
            close_order_body = {
                'instId': inst_id,
                'tdMode': 'isolated',
                'side': close_side,
                'posSide': pos_side,
                'ordType': 'market',
                'sz': str(close_size)
            }
            
            print(f"📝 平仓请求参数: {close_order_body}")
            
            headers = get_headers('POST', order_path, close_order_body)
            close_response = requests.post(
                OKEX_REST_URL + order_path,
                headers=headers,
                json=close_order_body,
                timeout=10
            )
            
            close_result = close_response.json()
            print(f"📝 OKEx平仓响应: {close_result}")
            
            if close_result.get('code') != '0':
                error_msg = close_result.get('msg', '未知错误')
                error_code = close_result.get('code', '未知代码')
                print(f"❌ 平仓失败 - Code: {error_code}, Message: {error_msg}")
                
                return jsonify({
                    'success': False,
                    'message': f"平仓失败: {error_msg} (开仓订单ID: {open_order_id})",
                    'error_code': error_code,
                    'open_order_id': open_order_id,
                    'full_response': close_result
                })
            
            close_order_id = close_result['data'][0]['ordId']
            print(f"✅ 第2步平仓订单提交成功: {close_order_id}")
            
            # 等待平仓订单成交
            print(f"⏳ 等待3秒确保平仓订单成交...")
            time.sleep(3)
        
        # 查询开仓订单的成交明细（fills）
        fills_path = f'/api/v5/trade/fills?instId={inst_id}&ordId={open_order_id}'
        headers = get_headers('GET', fills_path)
        open_fills_response = requests.get(
            OKEX_REST_URL + fills_path,
            headers=headers,
            timeout=10
        )
        open_fills_data = open_fills_response.json()
        
        # 查询平仓订单的成交明细
        close_fills_path = f'/api/v5/trade/fills?instId={inst_id}&ordId={close_order_id}'
        headers = get_headers('GET', close_fills_path)
        close_fills_response = requests.get(
            OKEX_REST_URL + close_fills_path,
            headers=headers,
            timeout=10
        )
        close_fills_data = close_fills_response.json()
        
        # 处理开仓成交明细
        open_fills = []
        open_total_fee = 0
        open_total_qty = 0
        open_total_value = 0
        if open_fills_data.get('code') == '0' and open_fills_data.get('data'):
            for fill in open_fills_data['data']:
                qty = float(fill.get('fillSz', 0))
                price = float(fill.get('fillPx', 0))
                fee = float(fill.get('fee', 0))
                value = qty * price  # 这笔交易的价值
                open_fills.append({
                    'trade_id': fill.get('tradeId'),
                    'qty': qty,
                    'price': price,
                    'value': value,  # 交易价值
                    'fee': abs(fee),  # 费用取绝对值
                    'fee_currency': fill.get('feeCcy', 'USDT')
                })
                open_total_fee += abs(fee)
                open_total_qty += qty
                open_total_value += value
        
        # 处理平仓成交明细
        close_fills = []
        close_total_fee = 0
        close_total_qty = 0
        close_total_value = 0
        if close_fills_data.get('code') == '0' and close_fills_data.get('data'):
            for fill in close_fills_data['data']:
                qty = float(fill.get('fillSz', 0))
                price = float(fill.get('fillPx', 0))
                fee = float(fill.get('fee', 0))
                value = qty * price  # 这笔交易的价值
                close_fills.append({
                    'trade_id': fill.get('tradeId'),
                    'qty': qty,
                    'price': price,
                    'value': value,  # 交易价值
                    'fee': abs(fee),
                    'fee_currency': fill.get('feeCcy', 'USDT')
                })
                close_total_fee += abs(fee)
                close_total_qty += qty
                close_total_value += value
        
        # 计算总费用和费率
        total_fee = open_total_fee + close_total_fee
        
        # 计算平均开仓价格
        avg_open_price = 0
        if open_total_qty > 0:
            avg_open_price = open_total_value / open_total_qty
        
        # 计算平均平仓价格
        avg_close_price = 0
        if close_total_qty > 0:
            avg_close_price = close_total_value / close_total_qty
        
        # 计算交易金额（以USDT计）
        trade_value = open_total_qty * avg_open_price
        
        # 计算总盈亏
        total_profit = 0
        if pos_side == 'long':
            total_profit = (avg_close_price - avg_open_price) * close_total_qty
        else:
            total_profit = (avg_open_price - avg_close_price) * close_total_qty
        
        # 净盈亏（扣除手续费）
        net_profit = total_profit - total_fee
        
        # 计算总成本：手续费 + 亏损（如果盈利则不算）
        total_cost = total_fee
        if total_profit < 0:
            total_cost += abs(total_profit)  # 亏损也是成本
        
        # 计算费率（总成本/交易金额）
        fee_rate = (total_cost / trade_value * 100) if trade_value > 0 else 0
        
        # 计算每笔订单的盈亏
        # 对于每笔开仓，计算对应的平仓盈亏
        # 盈亏 = (平仓价格 - 开仓价格) * 数量 (多单)
        # 盈亏 = (开仓价格 - 平仓价格) * 数量 (空单)
        for i, open_fill in enumerate(open_fills):
            if i < len(close_fills):
                close_fill = close_fills[i]
                qty = min(open_fill['qty'], close_fill['qty'])
                
                if pos_side == 'long':
                    # 多单：平仓价格 - 开仓价格
                    profit = (close_fill['price'] - open_fill['price']) * qty
                else:
                    # 空单：开仓价格 - 平仓价格
                    profit = (open_fill['price'] - close_fill['price']) * qty
                
                # 减去这笔交易的手续费
                net_profit = profit - open_fill['fee'] - close_fill['fee']
                
                open_fill['profit'] = profit
                open_fill['net_profit'] = net_profit
                close_fill['profit'] = profit
                close_fill['net_profit'] = net_profit
        
        print(f"📊 开仓成交: {len(open_fills)}笔, 总量{open_total_qty}, 均价${avg_open_price:.4f}, 费用${open_total_fee:.4f}")
        print(f"📊 平仓成交: {len(close_fills)}笔, 总量{close_total_qty}, 均价${avg_close_price:.4f}, 费用${close_total_fee:.4f}")
        print(f"💰 总费用: ${total_fee:.4f}, 总成本: ${total_cost:.4f}, 费率: {fee_rate:.4f}%")
        print(f"💵 盈亏: ${total_profit:.4f}, 净盈亏: ${net_profit:.4f}")
        
        # 保存维护记录到JSON文件
        try:
            import json as json_lib
            import os
            from datetime import datetime
            
            maintenance_file = 'maintenance_orders.json'
            
            # 读取现有记录
            if os.path.exists(maintenance_file):
                with open(maintenance_file, 'r', encoding='utf-8') as f:
                    records = json_lib.load(f)
            else:
                records = []
            
            # 添加新记录（优化后流程：先开新仓→平到目标保证金）
            new_record = {
                'id': len(records) + 1,
                'account_name': 'JAMESYI',  # 账户名称（后续可从配置读取）
                'inst_id': inst_id,
                'pos_side': pos_side,
                'original_size': pos_size,
                'open_order_id': open_order_id,
                'open_size': order_size,
                'open_fills': open_fills,
                'open_total_qty': open_total_qty,
                'open_avg_price': avg_open_price,
                'open_total_fee': open_total_fee,
                'close_order_id': close_order_id,
                'close_size': close_size,
                'close_fills': close_fills,
                'close_total_qty': close_total_qty,
                'close_avg_price': avg_close_price,
                'close_total_fee': close_total_fee,
                'remaining_size': order_size - close_size,
                'total_fee': total_fee,
                'total_cost': total_cost,  # 总成本（手续费+亏损）
                'fee_rate': fee_rate,
                'total_profit': total_profit,  # 总盈亏
                'net_profit': net_profit,  # 净盈亏（扣除手续费）
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success',
                'flow_type': 'optimized'  # 标记为优化流程
            }
            
            records.insert(0, new_record)  # 最新的记录放在前面
            
            # 只保留最近100条记录
            if len(records) > 100:
                records = records[:100]
            
            # 保存到文件
            with open(maintenance_file, 'w', encoding='utf-8') as f:
                json_lib.dump(records, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 维护记录已保存: ID {new_record['id']}")
            
            # 发送TG通知
            try:
                from telegram_notifier import TelegramNotifier
                
                notifier = TelegramNotifier()
                
                # 构建通知消息（优化流程：先平旧仓→开新仓→平到92%）
                tg_message = f"""🔧 **锚点单维护通知**（优化流程）

📍 **币种**: {inst_id}
📊 **方向**: {'做空' if pos_side == 'short' else '做多'}
💼 **原始仓位**: {pos_size}

**🔵 第1步-平掉旧持仓**:
• 订单ID: `{old_close_order_id}`
• 数量: {pos_size}
• 目的: 释放保证金

**🟢 第2步-开仓详情**:
• 订单ID: `{open_order_id}`
• 开仓数量: {open_total_qty}
• 平均价格: ${avg_open_price:.4f}
• 成交笔数: {len(open_fills)}笔
• 开仓费用: ${open_total_fee:.4f} USDT

**🔴 第3步-平仓到92%**:
• 订单ID: `{close_order_id}`
• 平仓数量: {close_total_qty}
• 平均价格: ${avg_close_price:.4f}
• 成交笔数: {len(close_fills)}笔
• 平仓费用: ${close_total_fee:.4f} USDT

**💰 盈亏统计**:
• 总盈亏: ${total_profit:.4f} USDT {'📈' if total_profit > 0 else '📉' if total_profit < 0 else '➖'}
• 手续费: ${total_fee:.4f} USDT
• 总成本: ${total_cost:.4f} USDT (手续费{'+ 亏损' if total_profit < 0 else ''})
• 净盈亏: ${net_profit:.4f} USDT {'✅' if net_profit > 0 else '❌' if net_profit < 0 else '➖'}
• 费率: {fee_rate:.4f}%
• 剩余仓位: {order_size - close_size}

⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                notifier.send_message(tg_message)
                print(f"✅ TG通知已发送")
            except Exception as tg_error:
                print(f"⚠️  发送TG通知失败: {tg_error}")
                import traceback
                print(traceback.format_exc())
                # 不影响主流程
        except Exception as save_error:
            print(f"⚠️  保存维护记录失败: {save_error}")
            # 不影响主流程，继续返回成功
        
        # 检查剩余持仓的保证金，如果大于2U则继续平仓到0.6-1U之间
        # 注意：只在自动维护（auto_adjust=True）时才执行此检查
        # 超级维护不做此限制
        adjustment_order_id = None
        adjustment_size = 0
        
        if auto_adjust:  # 只有自动维护才调整保证金
            try:
                print(f"🔍 检查剩余持仓保证金...")
                
                # 等待3秒让持仓数据更新
                import time
                time.sleep(3)
                
                # 查询当前持仓
                position_path = f'/api/v5/account/positions?instType=SWAP&instId={inst_id}'
                headers = get_headers('GET', position_path)
                pos_response = requests.get(
                    OKEX_REST_URL + position_path,
                    headers=headers,
                    timeout=10
                )
                pos_data = pos_response.json()
                
                if pos_data.get('code') == '0' and pos_data.get('data'):
                    for position in pos_data['data']:
                        if position.get('posSide') == pos_side:
                            current_pos_size = abs(float(position.get('pos', 0)))
                            current_margin = float(position.get('margin', 0))
                            mark_price = float(position.get('markPx', 0))
                            lever = int(position.get('lever', 10))
                            
                            print(f"📊 当前持仓: 数量={current_pos_size}, 保证金={current_margin:.4f}u, 标记价格={mark_price}")
                            
                            if current_margin > 2.0 and current_pos_size > 0:
                                print(f"⚠️  保证金 {current_margin:.4f}u > 2u，需要调整")
                                
                                # 目标保证金设为0.8U（在0.6-1U之间）
                                target_margin = 0.8
                                
                                # 计算需要的持仓量：margin = pos_size * mark_price / lever
                                # target_pos_size = target_margin * lever / mark_price
                                target_pos_size = (target_margin * lever) / mark_price
                                
                                # 计算需要平仓的数量
                                adjustment_size_raw = current_pos_size - target_pos_size
                                
                                # 获取合约面值
                                inst_path = f'/api/v5/public/instruments?instType=SWAP&instId={inst_id}'
                                inst_resp = requests.get(OKEX_REST_URL + inst_path, timeout=10)
                                inst_data = inst_resp.json()
                                lot_size = 1
                                if inst_data.get('code') == '0' and inst_data.get('data'):
                                    lot_size = float(inst_data['data'][0].get('ctVal', 1))
                                
                                # 向下取整到lot_size的整数倍
                                adjustment_size = int(adjustment_size_raw / lot_size) * lot_size
                                
                                if adjustment_size > 0:
                                    print(f"📉 计划平仓: {adjustment_size} (目标保证金: {target_margin}u)")
                                    
                                    # 执行平仓
                                    close_side = 'buy' if pos_side == 'short' else 'sell'
                                    adjustment_body = {
                                        'instId': inst_id,
                                        'tdMode': 'isolated',  # 逐仓模式：每个持仓独立保证金
                                        'side': close_side,
                                        'posSide': pos_side,
                                        'ordType': 'market',
                                        'sz': str(adjustment_size)
                                    }
                                    
                                    headers = get_headers('POST', order_path, adjustment_body)
                                    adj_response = requests.post(
                                        OKEX_REST_URL + order_path,
                                        headers=headers,
                                        json=adjustment_body,
                                        timeout=10
                                    )
                                    adj_data = adj_response.json()
                                    
                                    if adj_data.get('code') == '0':
                                        adjustment_order_id = adj_data['data'][0]['ordId']
                                        print(f"✅ 调整平仓成功: 订单ID {adjustment_order_id}, 平仓数量 {adjustment_size}")
                                    else:
                                        print(f"❌ 调整平仓失败: {adj_data.get('msg')}")
                                else:
                                    print(f"⚠️  计算的平仓数量 <= 0，跳过调整")
                            else:
                                print(f"✅ 保证金 {current_margin:.4f}u <= 2u，无需调整")
                            break
            except Exception as adj_error:
                print(f"⚠️  保证金调整失败: {adj_error}")
                import traceback
                print(traceback.format_exc())
        else:
            print(f"ℹ️  手动维护/超级维护模式，跳过保证金自动调整")
        
        response_data = {
            'open_order_id': open_order_id,
            'close_order_id': close_order_id,
            'open_size': order_size,
            'close_size': close_size,
            'remaining_size': order_size - close_size,
            'open_fills': open_fills,
            'close_fills': close_fills,
            'open_total_fee': open_total_fee,
            'close_total_fee': close_total_fee,
            'total_fee': total_fee,
            'fee_rate': fee_rate
        }
        
        if adjustment_order_id:
            response_data['adjustment_order_id'] = adjustment_order_id
            response_data['adjustment_size'] = adjustment_size
        
        return jsonify({
            'success': True,
            'message': '维护锚点单执行成功' + (f'，已调整保证金（平仓{adjustment_size}）' if adjustment_order_id else ''),
            'data': response_data
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'执行失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/maintenance-orders', methods=['GET'])
def get_maintenance_orders():
    """查询维护锚点单记录"""
    try:
        import json as json_lib
        import os
        
        maintenance_file = 'maintenance_orders.json'
        
        # 读取记录
        if os.path.exists(maintenance_file):
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                records = json_lib.load(f)
        else:
            records = []
        
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        inst_id = request.args.get('inst_id', None)
        
        # 过滤
        if inst_id:
            records = [r for r in records if r['inst_id'] == inst_id]
        
        # 限制数量
        records = records[:limit]
        
        return jsonify({
            'success': True,
            'data': records,
            'total': len(records)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/test-api-permission', methods=['GET'])
def test_api_permission():
    """测试API密钥权限"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        from okex_api_config import OKEX_API_KEY, OKEX_SECRET_KEY, OKEX_PASSPHRASE, OKEX_REST_URL
        
        # 生成签名
        def generate_signature(timestamp, method, request_path, body=''):
            if body:
                body = json.dumps(body)
            message = timestamp + method + request_path + body
            mac = hmac.new(
                bytes(OKEX_SECRET_KEY, encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod=hashlib.sha256
            )
            return base64.b64encode(mac.digest()).decode()
        
        def get_headers(method, request_path, body=''):
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            sign = generate_signature(timestamp, method, request_path, body)
            return {
                'OK-ACCESS-KEY': OKEX_API_KEY,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': OKEX_PASSPHRASE,
                'Content-Type': 'application/json'
            }
        
        # 测试1：读取账户余额
        balance_path = '/api/v5/account/balance'
        headers = get_headers('GET', balance_path)
        balance_response = requests.get(
            OKEX_REST_URL + balance_path,
            headers=headers,
            timeout=10
        )
        balance_result = balance_response.json()
        
        # 测试2：读取持仓信息
        position_path = '/api/v5/account/positions'
        headers = get_headers('GET', position_path)
        position_response = requests.get(
            OKEX_REST_URL + position_path,
            headers=headers,
            timeout=10
        )
        position_result = position_response.json()
        
        return jsonify({
            'success': True,
            'api_key': OKEX_API_KEY[:10] + '...',
            'tests': {
                'balance': {
                    'code': balance_result.get('code'),
                    'msg': balance_result.get('msg'),
                    'has_permission': balance_result.get('code') == '0'
                },
                'positions': {
                    'code': position_result.get('code'),
                    'msg': position_result.get('msg'),
                    'has_permission': position_result.get('code') == '0'
                }
            },
            'message': '如果has_permission都是True，说明API密钥可以读取数据。如果交易失败，需要在OKEx后台勾选「交易」权限。'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/auto-maintenance-config', methods=['GET', 'POST'])
def auto_maintenance_config():
    """获取或设置自动维护配置"""
    try:
        import json as json_lib
        import os
        
        config_file = 'auto_maintenance_config.json'
        
        if request.method == 'GET':
            # 读取配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json_lib.load(f)
            else:
                # 默认配置
                config = {
                    'auto_maintain_long_enabled': False,
                    'auto_maintain_short_enabled': False,
                    'super_maintain_long_enabled': False,
                    'super_maintain_short_enabled': False,
                    'loss_threshold': -10,
                    'margin_min': 0.6,
                    'margin_max': 1.0,
                    'last_check_time': None
                }
                # 保存默认配置
                with open(config_file, 'w', encoding='utf-8') as f:
                    json_lib.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            # 更新配置
            data = request.get_json()
            
            # 读取现有配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json_lib.load(f)
            else:
                config = {
                    'auto_maintain_long_enabled': False,
                    'auto_maintain_short_enabled': False,
                    'super_maintain_long_enabled': False,
                    'super_maintain_short_enabled': False,
                    'loss_threshold': -10,
                    'margin_min': 0.6,
                    'margin_max': 1.0,
                    'last_check_time': None
                }
            
            # 更新指定的字段
            if 'auto_maintain_long_enabled' in data:
                config['auto_maintain_long_enabled'] = data['auto_maintain_long_enabled']
            if 'auto_maintain_short_enabled' in data:
                config['auto_maintain_short_enabled'] = data['auto_maintain_short_enabled']
            if 'super_maintain_long_enabled' in data:
                config['super_maintain_long_enabled'] = data['super_maintain_long_enabled']
            if 'super_maintain_short_enabled' in data:
                config['super_maintain_short_enabled'] = data['super_maintain_short_enabled']
            if 'loss_threshold' in data:
                config['loss_threshold'] = data['loss_threshold']
            if 'margin_min' in data:
                config['margin_min'] = data['margin_min']
            if 'margin_max' in data:
                config['margin_max'] = data['margin_max']
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json_lib.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '配置已更新',
                'config': config
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/sub-account/config', methods=['GET', 'POST'])
def sub_account_config_v2():
    """获取或设置子账户配置"""
    try:
        import json as json_lib
        import os
        
        config_file = 'sub_account_config.json'
        
        if request.method == 'GET':
            # 读取配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json_lib.load(f)
            else:
                return jsonify({
                    'success': False,
                    'message': '子账户配置文件不存在'
                })
            
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            # 更新配置
            data = request.get_json()
            
            # 读取现有配置
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json_lib.load(f)
            else:
                return jsonify({
                    'success': False,
                    'message': '子账户配置文件不存在'
                })
            
            # 更新指定的字段
            if 'super_maintain_long_enabled' in data:
                config['super_maintain_long_enabled'] = data['super_maintain_long_enabled']
            if 'super_maintain_short_enabled' in data:
                config['super_maintain_short_enabled'] = data['super_maintain_short_enabled']
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json_lib.dump(config, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'message': '子账户配置已更新',
                'config': config
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/maintenance-stats', methods=['GET'])
def get_maintenance_stats():
    """获取维护次数统计（按自然日、币种和方向）"""
    try:
        import json as json_lib
        import os
        from datetime import datetime
        from collections import defaultdict
        
        maintenance_file = 'maintenance_orders.json'
        
        if not os.path.exists(maintenance_file):
            return jsonify({
                'success': True,
                'stats': {},
                'today_date': get_china_today()
            })
        
        # 读取维护记录
        with open(maintenance_file, 'r', encoding='utf-8') as f:
            records = json_lib.load(f)
        
        # 今天的日期
        today = get_china_today()
        
        # 统计今天每个币种+方向的维护次数（普通维护和超级维护都是+1）
        stats = defaultdict(int)
        
        for record in records:
            created_at = record.get('created_at', '')
            if created_at.startswith(today):
                inst_id = record.get('inst_id', '')
                pos_side = record.get('pos_side', '')
                key = f"{inst_id}:{pos_side}"
                
                # 无论是普通维护还是超级维护，都计数+1
                stats[key] += 1
        
        return jsonify({
            'success': True,
            'stats': dict(stats),
            'today_date': today
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

# ==================== 历史快照API ====================

@app.route('/api/anchor/snapshots/positions', methods=['GET'])
def get_position_snapshots():
    """获取持仓历史快照"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        # 获取参数
        start_time = request.args.get('start_time')  # 2025-12-30 00:00:00
        end_time = request.args.get('end_time')      # 2025-12-30 23:59:59
        inst_id = request.args.get('inst_id')        # 可选：筛选币种
        pos_side = request.args.get('pos_side')      # 可选：筛选方向
        limit = int(request.args.get('limit', 100))  # 默认100条
        
        # 默认查询最近24小时
        if not end_time:
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not start_time:
            start_dt = datetime.now() - timedelta(hours=24)
            start_time = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 查询数据库
        conn = sqlite3.connect('/home/user/webapp/anchor_snapshots.db')
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
        SELECT snapshot_time, inst_id, pos_side, pos_size, avg_price,
               mark_price, leverage, margin, profit_rate, upl,
               maintenance_count, is_anchor, status
        FROM position_snapshots
        WHERE snapshot_time BETWEEN ? AND ?
        '''
        params = [start_time, end_time]
        
        if inst_id:
            query += ' AND inst_id = ?'
            params.append(inst_id)
        
        if pos_side:
            query += ' AND pos_side = ?'
            params.append(pos_side)
        
        query += ' ORDER BY snapshot_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典列表
        snapshots = []
        for row in rows:
            snapshots.append({
                'snapshot_time': row[0],
                'inst_id': row[1],
                'pos_side': row[2],
                'pos_size': row[3],
                'avg_price': row[4],
                'mark_price': row[5],
                'leverage': row[6],
                'margin': row[7],
                'profit_rate': row[8],
                'upl': row[9],
                'maintenance_count': row[10],
                'is_anchor': row[11],
                'status': row[12]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'snapshots': snapshots,
            'count': len(snapshots),
            'start_time': start_time,
            'end_time': end_time
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/anchor/snapshots/statistics', methods=['GET'])
def get_statistics_snapshots():
    """获取统计历史快照"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        # 获取参数
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        stat_type = request.args.get('stat_type')  # 可选：筛选统计类型
        limit = int(request.args.get('limit', 100))
        
        # 默认查询最近24小时
        if not end_time:
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not start_time:
            start_dt = datetime.now() - timedelta(hours=24)
            start_time = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 查询数据库
        conn = sqlite3.connect('/home/user/webapp/anchor_snapshots.db')
        cursor = conn.cursor()
        
        # 构建查询
        query = '''
        SELECT snapshot_time, stat_type, stat_value, stat_label
        FROM statistics_snapshots
        WHERE snapshot_time BETWEEN ? AND ?
        '''
        params = [start_time, end_time]
        
        if stat_type:
            query += ' AND stat_type = ?'
            params.append(stat_type)
        
        query += ' ORDER BY snapshot_time DESC, stat_type LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 转换为字典列表
        snapshots = []
        for row in rows:
            snapshots.append({
                'snapshot_time': row[0],
                'stat_type': row[1],
                'stat_value': row[2],
                'stat_label': row[3]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'snapshots': snapshots,
            'count': len(snapshots),
            'start_time': start_time,
            'end_time': end_time
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/anchor/snapshots/times', methods=['GET'])
def get_snapshot_times():
    """获取可用的快照时间点列表"""
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        # 获取参数
        date = request.args.get('date')  # 格式：2025-12-30
        
        if not date:
            date = get_china_today()
        
        # 查询数据库
        conn = sqlite3.connect('/home/user/webapp/anchor_snapshots.db')
        cursor = conn.cursor()
        
        # 查询当天的所有快照时间
        cursor.execute('''
        SELECT DISTINCT snapshot_time
        FROM position_snapshots
        WHERE snapshot_time LIKE ?
        ORDER BY snapshot_time DESC
        ''', (f"{date}%",))
        
        rows = cursor.fetchall()
        times = [row[0] for row in rows]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'times': times,
            'count': len(times),
            'date': date
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/trading/positions/opens')
def get_trading_positions_opens():
    """获取开仓持仓 - Trading Manager专用，支持维护价格表"""
    try:
        import sqlite3
        
        # 获取参数
        is_anchor = request.args.get('is_anchor', type=int)
        limit = request.args.get('limit', 50, type=int)
        trade_mode = request.args.get('trade_mode', 'paper')
        
        DB_PATH = '/home/user/webapp/trading_decision.db'
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 如果是锚点单，使用维护价格表
        if is_anchor == 1:
            # 联合查询：position_opens 和 anchor_maintenance_prices
            cursor.execute('''
                SELECT 
                    p.id,
                    p.inst_id,
                    p.pos_side,
                    p.open_size,
                    p.mark_price,
                    p.profit_rate,
                    p.lever,
                    p.upl,
                    p.margin,
                    p.created_at,
                    p.updated_time,
                    p.trade_mode,
                    p.is_anchor,
                    p.granularity,
                    p.open_percent,
                    p.total_adds,
                    p.total_positions,
                    COALESCE(amp.maintenance_price, p.open_price) as open_price,
                    amp.original_open_price,
                    amp.maintenance_count,
                    amp.last_maintenance_time,
                    p.mark_price as current_price
                FROM position_opens p
                LEFT JOIN anchor_maintenance_prices amp 
                    ON p.inst_id = amp.inst_id 
                    AND p.pos_side = amp.pos_side 
                    AND p.trade_mode = amp.trade_mode
                WHERE p.is_anchor = 1 AND p.trade_mode = ?
                ORDER BY p.id DESC
                LIMIT ?
            ''', (trade_mode, limit))
            
            rows = cursor.fetchall()
            
            # 获取最新价格更新时间
            cursor.execute('''
                SELECT MAX(updated_time) FROM position_opens WHERE is_anchor = 1 AND trade_mode = ?
            ''', (trade_mode,))
            
            price_update_time = cursor.fetchone()[0] or ''
            
            records = []
            for row in rows:
                records.append({
                    'id': row['id'],
                    'inst_id': row['inst_id'],
                    'pos_side': row['pos_side'],
                    'open_price': float(row['open_price']),  # 使用维护价格
                    'original_open_price': float(row['original_open_price']) if row['original_open_price'] else None,
                    'open_size': float(row['open_size']),
                    'current_price': float(row['current_price']) if row['current_price'] else 0.0,
                    'mark_price': float(row['mark_price']) if row['mark_price'] else 0.0,
                    'profit_rate': float(row['profit_rate']) if row['profit_rate'] else 0.0,
                    'lever': int(row['lever']) if row['lever'] else 10,
                    'upl': float(row['upl']) if row['upl'] else 0.0,
                    'margin': float(row['margin']) if row['margin'] else 0.0,
                    'is_anchor': bool(row['is_anchor']),
                    'granularity': float(row['granularity']) if row['granularity'] else 0.0,
                    'open_percent': float(row['open_percent']) if row['open_percent'] else 0.0,
                    'total_adds': int(row['total_adds']) if row['total_adds'] else 0,
                    'total_positions': int(row['total_positions']) if row['total_positions'] else 0,
                    'maintenance_count': int(row['maintenance_count']) if row['maintenance_count'] else 0,
                    'last_maintenance_time': row['last_maintenance_time'] or '',
                    'created_at': row['created_at'],
                    'price_update_time': row['updated_time'] or '',
                    'trade_mode': row['trade_mode']
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'records': records,
                'total': len(records),
                'price_update_time': price_update_time,
                'trade_mode': trade_mode
            })
        
        # 非锚点单，直接查询
        else:
            cursor.execute('''
                SELECT 
                    id, inst_id, pos_side, open_price, open_size, mark_price, 
                    profit_rate, lever, upl, margin, created_at, updated_time,
                    trade_mode, is_anchor, granularity, open_percent, 
                    total_adds, total_positions
                FROM position_opens
                WHERE (? IS NULL OR is_anchor = ?) AND trade_mode = ?
                ORDER BY id DESC
                LIMIT ?
            ''', (is_anchor, is_anchor, trade_mode, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append({
                    'id': row['id'],
                    'inst_id': row['inst_id'],
                    'pos_side': row['pos_side'],
                    'open_price': float(row['open_price']),
                    'open_size': float(row['open_size']),
                    'current_price': float(row['mark_price']) if row['mark_price'] else 0.0,
                    'mark_price': float(row['mark_price']) if row['mark_price'] else 0.0,
                    'profit_rate': float(row['profit_rate']) if row['profit_rate'] else 0.0,
                    'lever': int(row['lever']) if row['lever'] else 10,
                    'upl': float(row['upl']) if row['upl'] else 0.0,
                    'margin': float(row['margin']) if row['margin'] else 0.0,
                    'is_anchor': bool(row['is_anchor']),
                    'granularity': float(row['granularity']) if row['granularity'] else 0.0,
                    'open_percent': float(row['open_percent']) if row['open_percent'] else 0.0,
                    'total_adds': int(row['total_adds']) if row['total_adds'] else 0,
                    'total_positions': int(row['total_positions']) if row['total_positions'] else 0,
                    'created_at': row['created_at'],
                    'price_update_time': row['updated_time'] or '',
                    'trade_mode': row['trade_mode']
                })
            
            return jsonify({
                'success': True,
                'records': records,
                'total': len(records),
                'trade_mode': trade_mode
            })
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/reset-maintenance-count', methods=['POST'])
def reset_maintenance_count():
    """清零子账户今日维护次数"""
    try:
        from datetime import datetime
        import pytz
        
        data = request.json
        account_name = data.get('account_name')
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        
        if not all([account_name, inst_id, pos_side]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 读取维护记录文件
        maintenance_file = 'sub_account_maintenance.json'
        try:
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                maintenance_data = json.load(f)
        except FileNotFoundError:
            maintenance_data = {}
        
        # 构建记录键
        record_key = f"{account_name}_{inst_id}_{pos_side}"
        
        # 获取当前北京时间的日期
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now_beijing = datetime.now(beijing_tz)
        today_date = now_beijing.strftime('%Y-%m-%d')
        
        # 检查是否存在今日记录
        if record_key not in maintenance_data:
            return jsonify({
                'success': False,
                'message': '该持仓没有维护记录'
            })
        
        record = maintenance_data[record_key]
        
        # 清零今日维护次数
        old_count = record.get('count', 0)
        old_date = record.get('date', '')
        
        # 重置记录
        record['count'] = 0
        record['date'] = today_date
        record['last_reset'] = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存更新后的数据
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            json.dump(maintenance_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'清零成功！原维护次数: {old_count}次',
            'data': {
                'account_name': account_name,
                'inst_id': inst_id,
                'pos_side': pos_side,
                'old_count': old_count,
                'old_date': old_date,
                'new_count': 0,
                'reset_time': record['last_reset']
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'清零失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/maintain-sub-account', methods=['POST'])
def maintain_sub_account():
    """子账户维护锚点单：买入100U并立即平掉"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        import pytz
        import os
        import math
        import time
        
        data = request.json
        account_name = data.get('account_name')
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        pos_size = float(data.get('pos_size', 0))
        
        # 新增参数：支持动态维护金额和目标保证金
        maintenance_amount = float(data.get('amount', 100))  # 维护金额，默认100U
        target_margin = float(data.get('target_margin', 10))  # 目标保证金，默认10U
        maintenance_count = int(data.get('maintenance_count', 0))  # 当前维护次数
        
        if not all([account_name, inst_id, pos_side]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 读取子账户配置
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json_lib.load(f)
        
        # 查找对应的子账户
        sub_account = None
        for acc in config.get('sub_accounts', []):
            if acc['account_name'] == account_name:
                sub_account = acc
                break
        
        if not sub_account:
            return jsonify({
                'success': False,
                'message': f'未找到子账户: {account_name}'
            })
        
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        # 检查今日维护次数
        maintenance_file = 'sub_account_maintenance.json'
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now_beijing = datetime.now(beijing_tz)
        today_date = now_beijing.strftime('%Y-%m-%d')
        
        # 读取维护记录
        if os.path.exists(maintenance_file):
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                maintenance_data = json.load(f)
        else:
            maintenance_data = {}
        
        record_key = f"{account_name}_{inst_id}_{pos_side}"
        record = maintenance_data.get(record_key, {})
        
        # 检查15分钟维护间隔
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
            except Exception as e:
                print(f"解析上次维护时间失败: {e}")
        
        # 获取当前维护次数（不再按日期重置）
        current_count = record.get('count', 0)
        
        max_count = sub_account.get('max_maintenance_count', 3)
        if current_count >= max_count:
            return jsonify({
                'success': False,
                'message': f'维护次数已达上限({max_count}次)，请手动清零',
                'current_count': current_count,
                'max_count': max_count
            })
        
        # OKEx API签名函数
        def generate_signature(timestamp, method, request_path, body=''):
            if body:
                body = json.dumps(body)
            message = timestamp + method + request_path + body
            mac = hmac.new(
                bytes(secret_key, encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod=hashlib.sha256
            )
            return base64.b64encode(mac.digest()).decode()
        
        def get_headers(method, request_path, body=''):
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            sign = generate_signature(timestamp, method, request_path, body)
            return {
                'OK-ACCESS-KEY': api_key,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': passphrase,
                'Content-Type': 'application/json'
            }
        
        OKEX_REST_URL = 'https://www.okx.com'
        
        # 维护操作：买入100U并立即平掉
        # 计算买入数量：100U / 标记价格 * 杠杆
        # 先获取当前标记价格
        position_path = f'/api/v5/account/positions?instType=SWAP&instId={inst_id}'
        headers = get_headers('GET', position_path)
        pos_response = requests.get(
            OKEX_REST_URL + position_path,
            headers=headers,
            timeout=10
        )
        pos_data = pos_response.json()
        
        mark_price = 0
        for position in pos_data.get('data', []):
            if position.get('posSide') == pos_side:
                # 安全转换：处理空字符串和None
                mark_px_str = position.get('markPx', '0')
                try:
                    mark_price = float(mark_px_str) if mark_px_str and mark_px_str != '' else 0
                except (ValueError, TypeError):
                    mark_price = 0
                break
        
        if mark_price == 0:
            # 如果没有持仓，查询行情获取价格
            ticker_path = f'/api/v5/market/ticker?instId={inst_id}'
            ticker_response = requests.get(
                OKEX_REST_URL + ticker_path,
                timeout=10
            )
            ticker_data = ticker_response.json()
            if ticker_data.get('code') == '0' and ticker_data.get('data'):
                # 安全转换：处理空字符串和None
                last_price_str = ticker_data['data'][0].get('last', '0')
                try:
                    mark_price = float(last_price_str) if last_price_str and last_price_str != '' else 0
                except (ValueError, TypeError):
                    mark_price = 0
        
        if mark_price == 0:
            return jsonify({
                'success': False,
                'message': f'无法获取标记价格，检查持仓和行情数据'
            })
        
        print(f"🎯 子账户维护: {account_name} {inst_id} {pos_side}")
        print(f"   标记价格: {mark_price}")
        print(f"   维护金额: {maintenance_amount}U")
        print(f"   目标保证金: {target_margin}U")
        print(f"   杠杆: {sub_account.get('leverage', 10)}x")
        
        # ========== 计算开仓和平仓数量（先开再平逻辑）==========
        import math
        lever = int(sub_account.get('leverage', 10))
        
        # 新开仓的数量：使用动态维护金额
        new_order_size_raw = (maintenance_amount * lever) / mark_price
        new_order_size = math.floor(new_order_size_raw)
        
        # 重要：如果new_order_size计算为0，说明维护金额太小，至少开1张
        if new_order_size == 0 and new_order_size_raw > 0:
            new_order_size = 1
            print(f"⚠️  new_order_size计算为 {new_order_size_raw:.2f}，向下取整为0，强制开仓1张")
        
        # 如果new_order_size仍然是0，返回错误
        if new_order_size == 0:
            return jsonify({
                'success': False,
                'message': f'维护金额太小，无法开仓。当前价格 {mark_price}，建议增加维护金额至少到 {math.ceil(mark_price / lever)}U'
            })
        
        # 计算最终保留的仓位：target_margin对应的仓位
        keep_size_raw = (target_margin * lever) / mark_price
        keep_size = math.floor(keep_size_raw)
        
        # 🔴 重要：确保保留的仓位对应的保证金不小于0.6U（OKEx最小保证金要求）
        MIN_MARGIN = 0.6  # 最小保证金0.6U
        min_keep_size = math.ceil((MIN_MARGIN * lever) / mark_price)
        
        if keep_size < min_keep_size:
            old_keep_size = keep_size
            keep_size = min_keep_size
            print(f"⚠️  keep_size计算为 {keep_size_raw:.2f}（{old_keep_size} 张），但为满足最小保证金0.6U要求，强制保留 {keep_size} 张")
        
        # 计算需要平掉的数量 = 旧持仓 + 新开仓 - 最终保留
        # 例如：旧持仓10U(100张) + 新开100U(1000张) - 保留10U(100张) = 平掉1000张
        total_pos_size = pos_size + new_order_size
        close_size = total_pos_size - keep_size
        
        # 确保close_size不为负数
        if close_size < 0:
            close_size = 0
            print(f"⚠️  计算出的close_size为负数，设为0（无需平仓）")
        
        print(f"📊 仓位计算:")
        print(f"   当前持仓: {pos_size} 张")
        print(f"   新开仓: {new_order_size} 张")
        print(f"   总持仓: {total_pos_size} 张")
        print(f"   最终保留: {keep_size} 张")
        print(f"   需要平仓: {close_size} 张")
        
        # ========== 第1步：设置逐仓杠杆 ==========
        print(f"📊 第1步：设置逐仓杠杆 {lever}x")
        leverage_path = '/api/v5/account/set-leverage'
        leverage_body = {
            'instId': inst_id,
            'lever': str(lever),
            'mgnMode': 'isolated',  # 逐仓模式
            'posSide': pos_side
        }
        leverage_headers = get_headers('POST', leverage_path, leverage_body)
        leverage_response = requests.post(
            OKEX_REST_URL + leverage_path,
            headers=leverage_headers,
            json=leverage_body,
            timeout=10
        )
        leverage_result = leverage_response.json()
        print(f"📥 设置杠杆响应: code={leverage_result.get('code')}, msg={leverage_result.get('msg')}")
        if leverage_result.get('code') != '0':
            print(f"⚠️  设置杠杆失败（可能已设置）: {leverage_result.get('msg')}")
        time.sleep(0.5)
        
        # ========== 第2步：开仓新持仓（维护金额对应的仓位）==========
        print(f"📊 第2步：开仓新持仓 {new_order_size} 张（维护金额 {maintenance_amount}U）")
        order_path = '/api/v5/trade/order'
        side = 'sell' if pos_side == 'short' else 'buy'
        
        open_order_body = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式
            'side': side,
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(new_order_size)
        }
        
        headers = get_headers('POST', order_path, open_order_body)
        open_response = requests.post(
            OKEX_REST_URL + order_path,
            headers=headers,
            json=open_order_body,
            timeout=10
        )
        
        open_result = open_response.json()
        
        # 详细日志：打印OKEx响应
        print(f"📤 开仓请求: {open_order_body}")
        print(f"📥 OKEx响应: code={open_result.get('code')}, msg={open_result.get('msg')}")
        if open_result.get('code') != '0':
            print(f"❌ 完整响应: {open_result}")
        
        if open_result.get('code') != '0':
            return jsonify({
                'success': False,
                'message': f"开仓失败: {open_result.get('msg', '未知错误')}",
                'error_code': open_result.get('code'),
                'full_response': str(open_result)
            })
        
        open_order_id = open_result['data'][0]['ordId']
        print(f"✅ 开仓订单ID: {open_order_id}")
        
        # 等待开仓完成
        time.sleep(2)
        open_order_id = open_result['data'][0]['ordId']
        
        # 等待订单成交
        import time
        time.sleep(2)
        
        # ========== 第3步：平掉多余仓位，保留target_margin对应的数量 ==========
        close_order_id = None
        if close_size > 0:
            print(f"📊 第3步：平到目标保证金，平掉 {close_size} 张")
            # close_size已经在前面计算好了
            close_side = 'buy' if pos_side == 'short' else 'sell'
            
            close_order_body = {
                'instId': inst_id,
                'tdMode': 'isolated',  # 逐仓模式
                'side': close_side,
                'posSide': pos_side,
                'ordType': 'market',
                'sz': str(close_size)
            }
            
            headers = get_headers('POST', order_path, close_order_body)
            close_response = requests.post(
                OKEX_REST_URL + order_path,
                headers=headers,
                json=close_order_body,
                timeout=10
            )
            
            close_result = close_response.json()
            
            if close_result.get('code') != '0':
                return jsonify({
                    'success': False,
                    'message': f"平仓失败: {close_result.get('msg', '未知错误')} (开仓订单ID: {open_order_id})",
                    'error_code': close_result.get('code'),
                    'open_order_id': open_order_id
                })
            
            close_order_id = close_result['data'][0]['ordId']
        else:
            print(f"📊 第3步：跳过（close_size={close_size}，无需平仓）")
            close_order_id = "SKIPPED"
        
        # 维护成功，更新维护次数（不再按日期重置）
        if not record:
            # 第一次维护，创建记录
            record = {
                'count': 1,
                'last_maintenance': now_beijing.strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            # 增加次数（不再检查日期）
            record['count'] = record.get('count', 0) + 1
            record['last_maintenance'] = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        maintenance_data[record_key] = record
        
        # 保存更新后的数据
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            json.dump(maintenance_data, f, ensure_ascii=False, indent=2)
        
        # 🔍 维护后自动验证和纠错
        print(f"\n{'='*60}")
        print(f"🔍 启动维护后自动验证...")
        try:
            from maintenance_verifier import verify_and_correct
            verify_result = verify_and_correct(
                account_name=account_name,
                inst_id=inst_id,
                pos_side=pos_side,
                target_margin=target_margin,
                maintenance_count=record['count']
            )
            print(f"✅ 验证完成: {verify_result.get('message')}")
            if verify_result.get('corrected'):
                print(f"⚠️ 已执行自动纠错")
        except Exception as e:
            print(f"❌ 验证过程出错: {e}")
            import traceback
            traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'message': f'维护成功！第{record["count"]}次维护',
            'data': {
                'account_name': account_name,
                'inst_id': inst_id,
                'pos_side': pos_side,
                'open_order_id': open_order_id,
                'close_order_id': close_order_id,
                'order_size': new_order_size,  # 新开仓的数量
                'close_size': close_size,  # 平仓的数量
                'total_count': record['count'],
                'max_count': max_count
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'维护失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/sub-account/close-all-positions', methods=['POST'])
def close_all_sub_account_positions():
    """一键全部平仓：关闭所有子账户的所有持仓"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        
        print("🚨 开始执行一键全部平仓...")
        
        # OKEx API配置
        OKEX_REST_URL = 'https://www.okx.com'
        
        # 直接读取子账户配置并获取持仓
        all_positions = []
        
        try:
            with open('sub_account_config.json', 'r', encoding='utf-8') as f:
                config_data = json_lib.load(f)
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'message': '子账户配置文件不存在'
            })
        
        # 遍历所有子账号获取持仓
        print(f"📋 配置中的子账号数量: {len(config_data.get('sub_accounts', []))}")
        
        for sub_account in config_data.get('sub_accounts', []):
            account_name = sub_account.get('account_name', 'Unknown')
            enabled = sub_account.get('enabled', False)
            print(f"  - {account_name}: enabled={enabled}")
            
            if not enabled:
                continue
            
            api_key = sub_account.get('api_key', '')
            secret_key = sub_account.get('secret_key', '')
            passphrase = sub_account.get('passphrase', '')
            
            try:
                # 生成OKEx签名
                request_path = '/api/v5/account/positions'
                query_string = 'instType=SWAP'
                timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                message = timestamp + 'GET' + request_path + '?' + query_string
                mac = hmac.new(
                    secret_key.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                )
                signature = base64.b64encode(mac.digest()).decode('utf-8')
                
                headers = {
                    'OK-ACCESS-KEY': api_key,
                    'OK-ACCESS-SIGN': signature,
                    'OK-ACCESS-TIMESTAMP': timestamp,
                    'OK-ACCESS-PASSPHRASE': passphrase,
                    'Content-Type': 'application/json'
                }
                
                # 获取持仓
                print(f"  🔍 正在获取 {account_name} 的持仓...")
                response = requests.get(
                    f'{OKEX_REST_URL}{request_path}?{query_string}',
                    headers=headers,
                    timeout=10
                )
                
                result = response.json()
                print(f"  📊 API响应: code={result.get('code')}, data_count={len(result.get('data', []))}")
                
                if result.get('code') == '0' and result.get('data'):
                    pos_count = 0
                    for pos_data in result['data']:
                        pos_size = float(pos_data.get('pos', 0) or 0)
                        if pos_size != 0:
                            inst_id = pos_data.get('instId', '')
                            pos_side = pos_data.get('posSide', '')
                            mgn_mode = pos_data.get('mgnMode', 'isolated')  # 获取持仓模式
                            margin_str = pos_data.get('margin', '0')
                            mark_px_str = pos_data.get('markPx', '0')
                            
                            # 处理空字符串
                            margin = float(margin_str or 0)
                            mark_price = float(mark_px_str or 0)
                            
                            all_positions.append({
                                'account_name': account_name,
                                'inst_id': inst_id,
                                'pos_side': pos_side,
                                'pos_size': pos_size,
                                'margin': margin,
                                'mark_price': mark_price,
                                'mgn_mode': mgn_mode  # 保存持仓模式
                            })
                            pos_count += 1
                            print(f"    ✅ {inst_id} {pos_side}: {pos_size}张 (模式: {mgn_mode})")
                    print(f"  📈 {account_name} 共找到 {pos_count} 个持仓")
                else:
                    error_msg = result.get('msg', 'Unknown error')
                    print(f"  ❌ API错误: {error_msg}")
            except Exception as e:
                print(f"  ⚠️ 获取 {account_name} 持仓失败: {str(e)}")
                import traceback
                print(f"  Stack trace: {traceback.format_exc()}")
                continue
        
        positions = all_positions
        
        if not positions:
            return jsonify({
                'success': True,
                'message': '没有持仓需要平仓',
                'success_count': 0,
                'fail_count': 0,
                'results': []
            })
        
        print(f"📊 找到 {len(positions)} 个持仓，开始逐个平仓...")
        
        success_count = 0
        fail_count = 0
        results = []
        
        # OKEx API签名和请求头函数
        def generate_signature(timestamp, method, request_path, body='', secret_key=''):
            if body:
                body = json_lib.dumps(body)
            message = timestamp + method + request_path + body
            mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
            return base64.b64encode(mac.digest()).decode()
        
        def get_headers(api_key, secret_key, passphrase, timestamp, method, request_path, body=''):
            return {
                'OK-ACCESS-KEY': api_key,
                'OK-ACCESS-SIGN': generate_signature(timestamp, method, request_path, body, secret_key),
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': passphrase,
                'Content-Type': 'application/json'
            }
        
        # 逐个平仓
        for pos in positions:
            account_name = pos.get('account_name')
            inst_id = pos.get('inst_id')
            pos_side = pos.get('pos_side')
            pos_size = abs(float(pos.get('pos_size', 0)))
            mgn_mode = pos.get('mgn_mode', 'isolated')  # 获取持仓模式，默认逐仓
            
            if pos_size == 0:
                continue
            
            print(f"\n🔧 开始平仓: {account_name} {inst_id} {pos_side} ({pos_size}张, 模式:{mgn_mode})")
            
            try:
                # 查找对应的子账户
                sub_account = None
                for acc in config_data.get('sub_accounts', []):
                    if acc['account_name'] == account_name:
                        sub_account = acc
                        break
                
                if not sub_account:
                    fail_count += 1
                    results.append({
                        'account_name': account_name,
                        'inst_id': inst_id,
                        'pos_side': pos_side,
                        'success': False,
                        'message': f'未找到子账户配置'
                    })
                    continue
                
                api_key = sub_account['api_key']
                secret_key = sub_account['secret_key']
                passphrase = sub_account['passphrase']
                
                # 多策略平仓：尝试3种方法确保成功
                close_success = False
                order_id = None
                error_details = []
                
                # 策略1: 使用快捷平仓接口（最可靠）
                print(f"  🎯 策略1: 快捷平仓接口 - {inst_id} {pos_side}")
                try:
                    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    request_path = '/api/v5/trade/close-position'
                    
                    close_body = {
                        'instId': inst_id,
                        'mgnMode': mgn_mode,  # 使用实际的持仓模式
                        'posSide': pos_side,
                        'ccy': 'USDT'
                    }
                    
                    headers = get_headers(api_key, secret_key, passphrase, timestamp, 'POST', request_path, close_body)
                    
                    response = requests.post(
                        f'{OKEX_REST_URL}{request_path}',
                        headers=headers,
                        json=close_body,
                        timeout=10
                    )
                    
                    result = response.json()
                    print(f"     响应: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
                    
                    if result.get('code') == '0' and result.get('data'):
                        order_id = result['data'][0].get('ordId', '--')
                        close_success = True
                        print(f"     ✅ 策略1成功")
                    else:
                        error_details.append(f"策略1失败: {result.get('msg', '未知错误')}")
                except Exception as e:
                    error_details.append(f"策略1异常: {str(e)}")
                    print(f"     ❌ 策略1异常: {str(e)}")
                
                # 策略2: 标准下单接口 + reduceOnly（如果策略1失败）
                if not close_success:
                    print(f"  🎯 策略2: 标准下单接口 + reduceOnly")
                    try:
                        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        request_path = '/api/v5/trade/order'
                        
                        close_side = 'sell' if pos_side == 'long' else 'buy'
                        
                        order_body = {
                            'instId': inst_id,
                            'tdMode': mgn_mode,  # 使用实际的持仓模式
                            'side': close_side,
                            'posSide': pos_side,
                            'ordType': 'market',
                            'sz': str(int(pos_size)),
                            'reduceOnly': True  # 关键参数
                        }
                        
                        headers = get_headers(api_key, secret_key, passphrase, timestamp, 'POST', request_path, order_body)
                        
                        response = requests.post(
                            f'{OKEX_REST_URL}{request_path}',
                            headers=headers,
                            json=order_body,
                            timeout=10
                        )
                        
                        result = response.json()
                        print(f"     响应: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
                        
                        if result.get('code') == '0' and result.get('data'):
                            order_id = result['data'][0].get('ordId', '--')
                            close_success = True
                            print(f"     ✅ 策略2成功")
                        else:
                            error_details.append(f"策略2失败: {result.get('msg', '未知错误')}")
                    except Exception as e:
                        error_details.append(f"策略2异常: {str(e)}")
                        print(f"     ❌ 策略2异常: {str(e)}")
                
                # 策略3: 不带reduceOnly的标准下单（最后的尝试）
                if not close_success:
                    print(f"  🎯 策略3: 标准下单接口（无reduceOnly）")
                    try:
                        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        request_path = '/api/v5/trade/order'
                        
                        close_side = 'sell' if pos_side == 'long' else 'buy'
                        
                        order_body = {
                            'instId': inst_id,
                            'tdMode': mgn_mode,  # 使用实际的持仓模式
                            'side': close_side,
                            'posSide': pos_side,
                            'ordType': 'market',
                            'sz': str(int(pos_size))
                        }
                        
                        headers = get_headers(api_key, secret_key, passphrase, timestamp, 'POST', request_path, order_body)
                        
                        response = requests.post(
                            f'{OKEX_REST_URL}{request_path}',
                            headers=headers,
                            json=order_body,
                            timeout=10
                        )
                        
                        result = response.json()
                        print(f"     响应: code={result.get('code')}, msg={result.get('msg', 'N/A')}")
                        
                        if result.get('code') == '0' and result.get('data'):
                            order_id = result['data'][0].get('ordId', '--')
                            close_success = True
                            print(f"     ✅ 策略3成功")
                        else:
                            error_details.append(f"策略3失败: {result.get('msg', '未知错误')}")
                    except Exception as e:
                        error_details.append(f"策略3异常: {str(e)}")
                        print(f"     ❌ 策略3异常: {str(e)}")
                
                # 汇总结果
                if close_success:
                    print(f"  ✅ {account_name} {inst_id} {pos_side}: 平仓成功 (订单ID: {order_id})")
                    success_count += 1
                    results.append({
                        'account_name': account_name,
                        'inst_id': inst_id,
                        'pos_side': pos_side,
                        'success': True,
                        'order_id': order_id,
                        'size': pos_size
                    })
                else:
                    print(f"  ❌ {account_name} {inst_id} {pos_side}: 所有策略均失败")
                    print(f"     失败详情: {'; '.join(error_details)}")
                    fail_count += 1
                    results.append({
                        'account_name': account_name,
                        'inst_id': inst_id,
                        'pos_side': pos_side,
                        'success': False,
                        'message': '; '.join(error_details) if error_details else '所有策略均失败'
                    })
                
            except Exception as e:
                print(f"  ❌ {account_name} {inst_id} {pos_side}: 平仓异常 - {str(e)}")
                fail_count += 1
                results.append({
                    'account_name': account_name,
                    'inst_id': inst_id,
                    'pos_side': pos_side,
                    'success': False,
                    'message': str(e)
                })
        
        print(f"🎯 一键全部平仓完成！成功: {success_count}个，失败: {fail_count}个")
        
        return jsonify({
            'success': True,
            'message': f'平仓完成',
            'success_count': success_count,
            'fail_count': fail_count,
            'total': len(positions),
            'results': results
        })
        
    except Exception as e:
        import traceback
        print(f"❌ 一键全部平仓失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'一键平仓失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/close-sub-account-position', methods=['POST'])
def close_sub_account_position():
    """子账户平仓：部分或全部平仓"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        from position_close_guard import validate_close_request, MIN_KEEP_MARGIN
        
        data = request.json
        account_name = data.get('account_name')
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        close_size = float(data.get('close_size', 0))
        reason = data.get('reason', '手动平仓')
        
        if not all([account_name, inst_id, pos_side, close_size]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 读取子账户配置
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json_lib.load(f)
        
        # 查找对应的子账户
        sub_account = None
        for acc in config.get('sub_accounts', []):
            if acc['account_name'] == account_name:
                sub_account = acc
                break
        
        if not sub_account:
            return jsonify({
                'success': False,
                'message': f'未找到子账户: {account_name}'
            })
        
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        # OKEx API签名函数
        def generate_signature(timestamp, method, request_path, body=''):
            if body:
                body = json.dumps(body)
            message = timestamp + method + request_path + body
            mac = hmac.new(
                bytes(secret_key, encoding='utf8'),
                bytes(message, encoding='utf-8'),
                digestmod=hashlib.sha256
            )
            return base64.b64encode(mac.digest()).decode()
        
        def get_headers(method, request_path, body=''):
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            sign = generate_signature(timestamp, method, request_path, body)
            return {
                'OK-ACCESS-KEY': api_key,
                'OK-ACCESS-SIGN': sign,
                'OK-ACCESS-TIMESTAMP': timestamp,
                'OK-ACCESS-PASSPHRASE': passphrase,
                'Content-Type': 'application/json'
            }
        
        # OKEx API URL
        OKEX_REST_URL = 'https://www.okx.com'
        
        # 🛡️ 底仓保护：获取当前持仓信息
        positions_path = '/api/v5/account/positions'
        positions_params = f'?instType=SWAP&instId={inst_id}'
        positions_headers = get_headers('GET', positions_path + positions_params)
        positions_response = requests.get(
            OKEX_REST_URL + positions_path + positions_params,
            headers=positions_headers,
            timeout=10
        )
        positions_data = positions_response.json()
        
        if positions_data.get('code') != '0':
            return jsonify({
                'success': False,
                'message': f'获取持仓信息失败: {positions_data.get("msg")}'
            })
        
        # 查找对应的持仓
        current_position = None
        for pos in positions_data.get('data', []):
            if pos['instId'] == inst_id and pos['posSide'] == pos_side:
                current_position = pos
                break
        
        if not current_position:
            return jsonify({
                'success': False,
                'message': f'未找到持仓: {inst_id} {pos_side}'
            })
        
        # 提取持仓信息（安全转换，处理空字符串）
        pos_size = abs(float(current_position['pos']) if current_position['pos'] else 0)
        
        # 如果 markPx 为空，尝试从行情API获取
        mark_price_str = current_position.get('markPx', '')
        if mark_price_str and mark_price_str.strip():
            mark_price = float(mark_price_str)
        else:
            # 从ticker获取价格
            ticker_path = f'/api/v5/market/ticker?instId={inst_id}'
            ticker_headers = get_headers('GET', ticker_path)
            ticker_response = requests.get(
                OKEX_REST_URL + ticker_path,
                headers=ticker_headers,
                timeout=10
            )
            ticker_data = ticker_response.json()
            if ticker_data.get('code') == '0' and ticker_data.get('data'):
                mark_price = float(ticker_data['data'][0].get('last', 0))
            else:
                return jsonify({
                    'success': False,
                    'message': '无法获取标记价格'
                })
        
        leverage_str = current_position.get('lever', '10')
        leverage = float(leverage_str) if leverage_str and leverage_str.strip() else 10.0
        
        # 🛡️ 底仓保护验证
        is_safe, adjusted_close_size, warning_msg = validate_close_request(
            pos_size, close_size, mark_price, leverage, MIN_KEEP_MARGIN
        )
        
        if not is_safe:
            print(f"⚠️  {warning_msg}")
            close_size = adjusted_close_size
            reason = f"{reason} (底仓保护自动调整)"
        
        # 执行平仓
        order_path = '/api/v5/trade/order'
        
        # 确定平仓方向
        close_side = 'buy' if pos_side == 'short' else 'sell'
        
        close_order_body = {
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式：每个持仓独立保证金
            'side': close_side,
            'posSide': pos_side,
            'ordType': 'market',
            'sz': str(int(close_size))
        }
        
        print(f"🎯 子账户平仓: {account_name} {inst_id} {pos_side} {close_size}")
        print(f"   原因: {reason}")
        
        headers = get_headers('POST', order_path, close_order_body)
        close_response = requests.post(
            OKEX_REST_URL + order_path,
            headers=headers,
            json=close_order_body,
            timeout=10
        )
        close_data = close_response.json()
        
        if close_data.get('code') != '0':
            return jsonify({
                'success': False,
                'message': f'平仓失败: {close_data.get("msg")}',
                'error_code': close_data.get('code')
            })
        
        order_id = close_data['data'][0]['ordId']
        print(f"✅ 平仓订单提交成功: {order_id}")
        
        return jsonify({
            'success': True,
            'message': '平仓成功',
            'order_id': order_id,
            'close_size': int(close_size),
            'reason': reason
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'平仓失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/anchor/open-sub-account-position', methods=['POST'])
def open_sub_account_position():
    """子账户开仓：按指定金额开仓"""
    try:
        import requests
        import hmac
        import base64
        import hashlib
        import json as json_lib
        from datetime import datetime, timezone
        import pytz
        import os
        import math
        import time
        
        data = request.json
        account_name = data.get('account_name')
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')  # 'long' or 'short'
        amount = float(data.get('amount', 10))  # 默认10U
        
        if not all([account_name, inst_id, pos_side]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 读取子账户配置
        with open('sub_account_config.json', 'r', encoding='utf-8') as f:
            config = json_lib.load(f)
        
        # 查找对应的子账户
        sub_account = None
        for acc in config.get('sub_accounts', []):
            if acc['account_name'] == account_name:
                sub_account = acc
                break
        
        if not sub_account:
            return jsonify({
                'success': False,
                'message': f'未找到子账户: {account_name}'
            })
        
        api_key = sub_account['api_key']
        secret_key = sub_account['secret_key']
        passphrase = sub_account['passphrase']
        
        print(f"\n{'='*80}")
        print(f"🚀 子账户开仓")
        print(f"账户: {account_name}")
        print(f"币种: {inst_id}")
        print(f"方向: {pos_side}")
        print(f"金额: {amount} USDT")
        print(f"{'='*80}\n")
        
        # 1. 获取当前标记价格
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        request_path = f'/api/v5/public/mark-price?instType=SWAP&instId={inst_id}'
        message = timestamp + 'GET' + request_path
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        signature = base64.b64encode(mac.digest()).decode()
        
        headers = {
            'OK-ACCESS-KEY': api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': passphrase,
            'Content-Type': 'application/json'
        }
        
        mark_price_url = f'https://www.okx.com{request_path}'
        mark_response = requests.get(mark_price_url, headers=headers, timeout=10)
        mark_result = mark_response.json()
        
        if mark_result['code'] != '0' or not mark_result['data']:
            return jsonify({
                'success': False,
                'message': f'获取标记价格失败: {mark_result.get("msg")}'
            })
        
        mark_price = float(mark_result['data'][0]['markPx'])
        print(f"📊 当前标记价格: {mark_price}")
        
        # 2. 获取合约信息（张数和面值）
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        request_path = f'/api/v5/public/instruments?instType=SWAP&instId={inst_id}'
        message = timestamp + 'GET' + request_path
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        signature = base64.b64encode(mac.digest()).decode()
        
        headers['OK-ACCESS-SIGN'] = signature
        headers['OK-ACCESS-TIMESTAMP'] = timestamp
        
        instruments_url = f'https://www.okx.com{request_path}'
        instruments_response = requests.get(instruments_url, headers=headers, timeout=10)
        instruments_result = instruments_response.json()
        
        if instruments_result['code'] != '0' or not instruments_result['data']:
            return jsonify({
                'success': False,
                'message': f'获取合约信息失败: {instruments_result.get("msg")}'
            })
        
        ct_val = float(instruments_result['data'][0]['ctVal'])
        lot_sz = float(instruments_result['data'][0]['lotSz'])
        print(f"📊 合约面值: {ct_val}, 最小张数: {lot_sz}")
        
        # 3. 计算开仓张数（10倍杠杆）
        leverage = 10
        # amount USDT * 杠杆 / 标记价格 = 可开张数
        raw_size = (amount * leverage) / (mark_price * ct_val)
        # 向下取整到最小张数的倍数
        open_size = math.floor(raw_size / lot_sz) * lot_sz
        
        if open_size < lot_sz:
            return jsonify({
                'success': False,
                'message': f'开仓金额太小，无法开仓（最少需要 {lot_sz} 张）'
            })
        
        print(f"📊 计算开仓张数: {open_size}")
        
        # 4. 设置杠杆
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        request_path = '/api/v5/account/set-leverage'
        body = json_lib.dumps({
            'instId': inst_id,
            'lever': str(leverage),
            'mgnMode': 'isolated',
            'posSide': pos_side if pos_side in ['long', 'short'] else 'net'
        })
        message = timestamp + 'POST' + request_path + body
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        signature = base64.b64encode(mac.digest()).decode()
        
        headers['OK-ACCESS-SIGN'] = signature
        headers['OK-ACCESS-TIMESTAMP'] = timestamp
        
        leverage_url = f'https://www.okx.com{request_path}'
        leverage_response = requests.post(leverage_url, headers=headers, data=body, timeout=10)
        leverage_result = leverage_response.json()
        print(f"📊 设置杠杆结果: {leverage_result}")
        
        # 5. 提交开仓订单
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        request_path = '/api/v5/trade/order'
        
        # 判断订单方向
        if pos_side == 'long':
            side = 'buy'
        elif pos_side == 'short':
            side = 'sell'
        else:
            side = 'buy'  # 默认买入
        
        body = json_lib.dumps({
            'instId': inst_id,
            'tdMode': 'isolated',  # 逐仓模式：每个持仓独立保证金
            'side': side,
            'ordType': 'market',
            'sz': str(int(open_size)),
            'posSide': pos_side if pos_side in ['long', 'short'] else 'net'
        })
        
        message = timestamp + 'POST' + request_path + body
        mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod=hashlib.sha256)
        signature = base64.b64encode(mac.digest()).decode()
        
        headers['OK-ACCESS-SIGN'] = signature
        headers['OK-ACCESS-TIMESTAMP'] = timestamp
        
        order_url = f'https://www.okx.com{request_path}'
        order_response = requests.post(order_url, headers=headers, data=body, timeout=10)
        order_result = order_response.json()
        
        print(f"📊 开仓订单结果: {order_result}")
        
        if order_result['code'] != '0':
            return jsonify({
                'success': False,
                'message': f'开仓失败: {order_result.get("msg", "未知错误")}'
            })
        
        order_id = order_result['data'][0]['ordId']
        print(f"✅ 开仓订单ID: {order_id}")
        
        # 6. 保存开仓记录
        opened_positions = {}
        try:
            if os.path.exists('sub_account_opened_positions.json'):
                with open('sub_account_opened_positions.json', 'r', encoding='utf-8') as f:
                    opened_positions = json_lib.load(f)
        except:
            pass
        
        position_key = f"{account_name}_{inst_id}_{pos_side}"
        opened_positions[position_key] = {
            'account_name': account_name,
            'inst_id': inst_id,
            'pos_side': pos_side,
            'order_id': order_id,
            'open_size': open_size,
            'open_price': mark_price,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open('sub_account_opened_positions.json', 'w', encoding='utf-8') as f:
            json_lib.dump(opened_positions, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': '开仓成功',
            'data': {
                'account_name': account_name,
                'inst_id': inst_id,
                'pos_side': pos_side,
                'order_id': order_id,
                'open_size': open_size,
                'open_price': mark_price,
                'amount': amount
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'开仓失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/sub-account/reset-maintenance-count', methods=['POST'])
def reset_sub_account_maintenance_count():
    """清零子账户今日维护次数"""
    try:
        import json as json_lib
        from datetime import datetime
        import pytz
        
        data = request.json
        account_name = data.get('account_name')
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        
        if not all([account_name, inst_id, pos_side]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 读取维护记录文件
        maintenance_file = 'sub_account_maintenance.json'
        try:
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                maintenance_data = json.load(f)
        except FileNotFoundError:
            maintenance_data = {}
        
        # 构建记录键
        record_key = f"{account_name}_{inst_id}_{pos_side}"
        
        # 获取当前北京时间的日期
        beijing_tz = pytz.timezone('Asia/Shanghai')
        now_beijing = datetime.now(beijing_tz)
        today_date = now_beijing.strftime('%Y-%m-%d')
        
        # 检查是否存在今日记录
        if record_key not in maintenance_data:
            return jsonify({
                'success': False,
                'message': '该持仓没有维护记录'
            })
        
        record = maintenance_data[record_key]
        
        # 清零今日维护次数
        old_count = record.get('count', 0)
        
        # 重置记录
        record['count'] = 0
        record['date'] = today_date
        record['last_reset'] = now_beijing.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存更新后的数据
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            json.dump(maintenance_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'清零成功！原维护次数: {old_count}次',
            'account_name': account_name,
            'inst_id': inst_id,
            'pos_side': pos_side,
            'old_count': old_count,
            'new_count': 0,
            'reset_time': now_beijing.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'清零失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/main-account/reset-maintenance-count', methods=['POST'])
def reset_main_account_maintenance_count():
    """清零主账户今日超级维护次数"""
    try:
        import json as json_lib
        from datetime import datetime
        
        data = request.json
        inst_id = data.get('inst_id')
        pos_side = data.get('pos_side')
        
        if not all([inst_id, pos_side]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            })
        
        # 读取维护记录文件
        maintenance_file = 'main_account_maintenance.json'
        try:
            with open(maintenance_file, 'r', encoding='utf-8') as f:
                maintenance_data = json.load(f)
        except FileNotFoundError:
            maintenance_data = {}
        
        # 构建记录键
        record_key = f"{inst_id}_{pos_side}"
        
        # 获取当前日期
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        # 检查是否存在今日记录
        if record_key not in maintenance_data:
            return jsonify({
                'success': False,
                'message': '该持仓没有维护记录'
            })
        
        record = maintenance_data[record_key]
        
        # 清零今日维护次数
        old_count = record.get('count', 0)
        
        # 重置记录
        record['count'] = 0
        record['date'] = today_date
        record['last_reset'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存更新后的数据
        with open(maintenance_file, 'w', encoding='utf-8') as f:
            json.dump(maintenance_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'清零成功！原超级维护次数: {old_count}次',
            'inst_id': inst_id,
            'pos_side': pos_side,
            'old_count': old_count,
            'new_count': 0,
            'reset_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'清零失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/api/sub-account/take-profit-records', methods=['GET'])
def get_sub_account_take_profit_records():
    """获取子账户止盈记录"""
    try:
        import json as json_lib
        from datetime import datetime, timedelta
        
        # 获取查询参数
        account_name = request.args.get('account_name')
        days = int(request.args.get('days', 7))  # 默认查询最近7天
        
        # 读取止盈记录文件
        records_file = 'sub_account_take_profit_records.json'
        try:
            with open(records_file, 'r', encoding='utf-8') as f:
                all_records = json_lib.load(f)
        except FileNotFoundError:
            all_records = []
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 过滤记录
        filtered_records = []
        total_profit = 0
        total_closed_amount = 0
        
        for record in all_records:
            # 按账户名过滤
            if account_name and record.get('account_name') != account_name:
                continue
            
            # 按时间范围过滤
            record_time = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
            if record_time < start_date or record_time > end_date:
                continue
            
            filtered_records.append(record)
            
            # 统计数据
            if 'estimated_profit' in record:
                total_profit += record['estimated_profit']
            if 'close_amount' in record:
                total_closed_amount += record['close_amount']
        
        # 按时间倒序排序
        filtered_records.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 统计信息
        stats = {
            'total_records': len(filtered_records),
            'total_profit': round(total_profit, 2),
            'total_closed_amount': round(total_closed_amount, 2),
            'avg_profit_per_trade': round(total_profit / len(filtered_records), 2) if len(filtered_records) > 0 else 0,
            'rule1_count': len([r for r in filtered_records if r.get('rule') == 'rule1']),
            'rule2_count': len([r for r in filtered_records if r.get('rule') == 'rule2']),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        return jsonify({
            'success': True,
            'records': filtered_records,
            'stats': stats
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'获取记录失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

# 测试页面路由
@app.route('/api/anchor/decline-strength', methods=['GET'])
def get_decline_strength():
    """
    获取下跌强度分类
    根据空单盈利情况判断市场下跌强度
    """
    try:
        import sys
        sys.path.append('/home/user/webapp')
        from anchor_system import get_positions_from_okex
        
        # 获取实盘持仓
        raw_positions = get_positions_from_okex()
        
        # 统计空单盈利情况
        short_profits = []
        for pos in raw_positions:
            if pos.get('posSide') == 'short':  # OKEx API 使用 posSide
                profit_rate = float(pos.get('uplRatio', 0)) * 100  # 转换为百分比
                short_profits.append({
                    'inst_id': pos.get('instId'),
                    'profit_rate': profit_rate,
                    'margin': float(pos.get('margin', 0)),
                    'upl': float(pos.get('upl', 0))
                })
        
        # 计算各盈利区间的空单数量（新增100%、90%、80%统计）
        count_100 = len([p for p in short_profits if p['profit_rate'] >= 100])
        count_90 = len([p for p in short_profits if p['profit_rate'] >= 90])
        count_80 = len([p for p in short_profits if p['profit_rate'] >= 80])
        count_70 = len([p for p in short_profits if p['profit_rate'] >= 70])
        count_60 = len([p for p in short_profits if p['profit_rate'] >= 60])
        count_50 = len([p for p in short_profits if p['profit_rate'] >= 50])
        count_40 = len([p for p in short_profits if p['profit_rate'] >= 40])
        
        # 判断下跌等级（新的5级规则）
        strength_level = 0
        strength_name = ''
        buy_suggestion = ''
        color_class = ''
        
        # 没有空单的情况
        if len(short_profits) == 0:
            strength_level = 0
            strength_name = '市场正常'
            buy_suggestion = '暂无明显下跌信号'
            color_class = 'strength-0'
        # 下跌等级5：极端下跌
        elif count_100 >= 1:
            strength_level = 5
            strength_name = '下跌等级5 - 极端下跌'
            buy_suggestion = '交易对的空仓盈利要大于100%'
            color_class = 'strength-5'
        # 下跌等级4：超高强度下跌
        elif count_100 == 0 and count_90 >= 1 and count_80 >= 1:
            strength_level = 4
            strength_name = '下跌等级4 - 超高强度下跌'
            buy_suggestion = '交易对的空仓盈利要大于90%'
            color_class = 'strength-4'
        # 下跌等级3：高强度下跌
        elif count_100 == 0 and count_90 == 0 and count_80 == 0 and count_70 >= 1 and count_60 >= 2:
            strength_level = 3
            strength_name = '下跌等级3 - 高强度下跌'
            buy_suggestion = '交易对的空仓盈利要大于70%'
            color_class = 'strength-3'
        # 下跌等级2：中等强度下跌
        elif count_100 == 0 and count_90 == 0 and count_80 == 0 and count_70 == 0 and count_60 >= 2:
            strength_level = 2
            strength_name = '下跌等级2 - 中等强度下跌'
            buy_suggestion = '交易对的空仓盈利要大于60%'
            color_class = 'strength-2'
        # 下跌等级1：轻微下跌
        elif count_100 == 0 and count_90 == 0 and count_80 == 0 and count_70 == 0 and count_60 == 0 and count_50 == 0 and count_40 >= 3:
            strength_level = 1
            strength_name = '下跌等级1 - 轻微下跌'
            buy_suggestion = '交易对的空仓盈利要大于40%'
            color_class = 'strength-1'
        # 不满足任何条件
        else:
            strength_level = 0
            strength_name = '市场正常'
            buy_suggestion = '暂无明显下跌信号'
            color_class = 'strength-0'
        
        return jsonify({
            'success': True,
            'data': {
                'strength_level': strength_level,
                'strength_name': strength_name,
                'buy_suggestion': buy_suggestion,
                'color_class': color_class,
                'statistics': {
                    'total_shorts': len(short_profits),
                    'profit_100': count_100,
                    'profit_90': count_90,
                    'profit_80': count_80,
                    'profit_70': count_70,
                    'profit_60': count_60,
                    'profit_50': count_50,
                    'profit_40': count_40
                },
                'short_positions': short_profits
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'获取下跌强度失败: {str(e)}',
            'traceback': traceback.format_exc()
        })

@app.route('/test-positions')
def test_positions_page():
    """持仓数据测试页面"""
    return render_template('test_positions.html')

@app.route('/sub-account-trades')
def sub_account_trades_page():
    """子账户交易详情页面"""
    return render_template('sub_account_trades.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
