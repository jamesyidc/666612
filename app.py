#!/usr/bin/env python3
"""
加密货币数据分析系统 - 统一Web应用
使用路径后缀区分不同页面，而非端口号
"""
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from flask_compress import Compress
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)
Compress(app)  # 启用gzip压缩

# 首页HTML
HOME_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>加密货币数据分析系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 60px;
            text-align: center;
        }
        h1 {
            color: #667eea;
            font-size: 3em;
            margin-bottom: 20px;
        }
        .subtitle {
            color: #666;
            font-size: 1.3em;
            margin-bottom: 50px;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 50px;
        }
        .feature-card {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        .feature-card h3 {
            color: #764ba2;
            font-size: 1.5em;
            margin-bottom: 15px;
        }
        .feature-card p {
            color: #666;
            line-height: 1.6;
        }
        .buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 40px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 1.2em;
            font-weight: bold;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .links {
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 15px;
            font-size: 1.1em;
        }
        .links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 加密货币数据分析系统</h1>
        <p class="subtitle">专业的历史数据查询、趋势分析和优先级计算平台</p>
        
        <div class="features">
            <div class="feature-card">
                <h3>📊 数据查询</h3>
                <p>按日期+时间快速查询历史数据，支持多种格式，无需设置时间范围</p>
            </div>
            <div class="feature-card">
                <h3>📈 趋势图表</h3>
                <p>4指标曲线图：急涨、急跌、差值、计次，清晰展示市场趋势</p>
            </div>
            <div class="feature-card">
                <h3>🎯 优先级计算</h3>
                <p>基于最高占比和最低占比自动计算6级优先级，颜色标记清晰</p>
            </div>
        </div>

        <div class="buttons">
            <a href="/dashboard" class="btn">📊 进入数据看板</a>
            <a href="/query" class="btn">🔍 历史数据查询</a>
            <a href="/api/docs" class="btn">📖 API文档</a>
        </div>

        <div class="links">
            <a href="https://github.com/jamesyidc/6666" target="_blank">📦 GitHub仓库</a>
            <a href="https://github.com/jamesyidc/6666/pull/1" target="_blank">🔀 Pull Request</a>
            <a href="/about">ℹ️ 关于系统</a>
        </div>
    </div>
</body>
</html>
"""

# 数据看板HTML（仿照用户截图）
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据看板 - 加密货币分析系统</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: #1a1d2e;
            color: #fff;
            padding: 20px;
        }
        .container {
            max-width: 1800px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            font-size: 24px;
        }
        .header .nav a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
            padding: 8px 15px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .header .nav a:hover {
            background: rgba(255,255,255,0.2);
        }
        .status-bar {
            background: #252b3f;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 30px;
            align-items: center;
            flex-wrap: wrap;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-label {
            color: #8b93a7;
        }
        .status-value {
            font-weight: bold;
            font-size: 18px;
        }
        .status-value.rise {
            color: #00d4aa;
        }
        .status-value.fall {
            color: #ff4d4f;
        }
        .datetime-selector {
            background: #252b3f;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .datetime-selector label {
            color: #8b93a7;
        }
        .datetime-selector input {
            background: #1a1d2e;
            border: 1px solid #404654;
            color: #fff;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 14px;
        }
        .datetime-selector button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 8px 25px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }
        .datetime-selector button:hover {
            opacity: 0.9;
        }
        .data-table {
            background: #252b3f;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #1a1d2e;
            padding: 12px 8px;
            text-align: center;
            font-size: 13px;
            color: #8b93a7;
            border-bottom: 2px solid #404654;
            white-space: nowrap;
        }
        td {
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid #323649;
            font-size: 13px;
            white-space: nowrap;
        }
        tr:hover {
            background: #2a3147;
        }
        .symbol-cell {
            font-weight: bold;
            font-size: 14px;
        }
        .rise-tag {
            background: #ff4d4f;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
        }
        .fall-tag {
            background: #00d4aa;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
        }
        .positive {
            color: #ff4d4f;
        }
        .negative {
            color: #00d4aa;
        }
        .priority-1 { color: #ff0000; font-weight: bold; }
        .priority-2 { color: #ff6600; font-weight: bold; }
        .priority-3 { color: #ff9900; }
        .priority-4 { color: #ffcc00; }
        .priority-5 { color: #99cc00; }
        .priority-6 { color: #8b93a7; }
        .chart-section {
            background: #252b3f;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .chart-title {
            font-size: 18px;
            margin-bottom: 15px;
            color: #fff;
        }
        #trendChart {
            width: 100%;
            height: 400px;
        }
        .legend {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 30px;
            height: 3px;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>🚀 加密货币数据看板</h1>
            <div class="nav">
                <a href="/">🏠 首页</a>
                <a href="/query">🔍 查询</a>
                <a href="/dashboard">📊 看板</a>
            </div>
        </div>

        <!-- 状态栏 -->
        <div class="status-bar">
            <div class="status-item">
                <span class="status-label">运算时间:</span>
                <span class="status-value" id="calcTime">--</span>
            </div>
            <div class="status-item">
                <span class="status-label">急涨:</span>
                <span class="status-value rise" id="rushUp">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">急跌:</span>
                <span class="status-value fall" id="rushDown">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">状态:</span>
                <span class="status-value" id="status">--</span>
            </div>
            <div class="status-item">
                <span class="status-label">比值:</span>
                <span class="status-value" id="ratio">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">差值:</span>
                <span class="status-value" id="diff">0</span>
            </div>
            <div class="status-item">
                <span class="status-label">计次:</span>
                <span class="status-value" id="count">0</span>
            </div>
        </div>

        <!-- 日期时间选择器 -->
        <div class="datetime-selector">
            <label>选择日期:</label>
            <input type="date" id="queryDate" value="">
            <label>时间:</label>
            <input type="time" id="queryTime" value="">
            <button onclick="queryData()">🔍 查询</button>
            <button onclick="loadLatest()">📊 最新数据</button>
        </div>

        <!-- 币种数据表格 -->
        <div class="data-table">
            <table>
                <thead>
                    <tr>
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
                        <th>优先级</th>
                    </tr>
                </thead>
                <tbody id="dataTable">
                    <tr><td colspan="15" style="padding:30px;color:#8b93a7;">正在加载数据...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 趋势图 -->
        <div class="chart-section">
            <div class="chart-title">急涨/急跌历史趋势图</div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background:#ff4d4f;"></div>
                    <span>急涨</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background:#00d4aa;"></div>
                    <span>急跌</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background:#ffa940; border: 2px dashed #ffa940;"></div>
                    <span>差值(急涨-急跌)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background:#1890ff;"></div>
                    <span>计次</span>
                </div>
            </div>
            <div id="trendChart"></div>
        </div>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>
"""

# JavaScript代码
DASHBOARD_JS = """
// 初始化图表
const chart = echarts.init(document.getElementById('trendChart'));

// 初始化日期时间选择器
const now = new Date();
document.getElementById('queryDate').valueAsDate = now;
document.getElementById('queryTime').value = now.toTimeString().substr(0, 5);

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
            loadChartData(date);
        })
        .catch(error => {
            alert('查询失败: ' + error);
        });
}

// 加载最新数据
function loadLatest() {
    fetch('/api/latest')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('❌ ' + data.error);
                return;
            }
            updateUI(data);
            const date = data.snapshot_time.split(' ')[0];
            loadChartData(date);
        })
        .catch(error => {
            alert('加载失败: ' + error);
        });
}

// 更新UI
function updateUI(data) {
    document.getElementById('calcTime').textContent = data.snapshot_time;
    document.getElementById('rushUp').textContent = data.rush_up;
    document.getElementById('rushDown').textContent = data.rush_down;
    document.getElementById('status').textContent = data.status;
    document.getElementById('ratio').textContent = data.ratio;
    document.getElementById('diff').textContent = data.diff;
    document.getElementById('count').textContent = data.count;
    
    // 更新表格
    const tbody = document.getElementById('dataTable');
    if (data.coins && data.coins.length > 0) {
        let html = '';
        data.coins.forEach((coin, idx) => {
            const changeClass = coin.change > 0 ? 'positive' : (coin.change < 0 ? 'negative' : '');
            const change24Class = coin.change_24h > 0 ? 'positive' : (coin.change_24h < 0 ? 'negative' : '');
            const priorityClass = 'priority-' + coin.priority.replace('等级', '');
            
            html += '<tr>';
            html += '<td>' + (idx + 1) + '</td>';
            html += '<td class="symbol-cell">' + coin.symbol + '</td>';
            html += '<td class="' + changeClass + '">' + coin.change.toFixed(2) + '</td>';
            html += '<td>' + coin.rush_up + '</td>';
            html += '<td>' + coin.rush_down + '</td>';
            html += '<td>' + coin.update_time + '</td>';
            html += '<td>' + coin.high_price.toFixed(2) + '</td>';
            html += '<td>' + coin.high_time + '</td>';
            html += '<td class="negative">' + coin.decline.toFixed(2) + '</td>';
            html += '<td class="' + change24Class + '">' + coin.change_24h.toFixed(2) + '</td>';
            html += '<td>' + coin.rank + '</td>';
            html += '<td>' + coin.current_price.toFixed(4) + '</td>';
            html += '<td>' + coin.ratio1 + '</td>';
            html += '<td>' + coin.ratio2 + '</td>';
            html += '<td class="' + priorityClass + '">' + coin.priority + '</td>';
            html += '</tr>';
        });
        tbody.innerHTML = html;
    } else {
        tbody.innerHTML = '<tr><td colspan="15" style="padding:30px;color:#8b93a7;">暂无数据</td></tr>';
    }
}

// 加载图表数据
function loadChartData(date) {
    fetch('/api/chart?date=' + encodeURIComponent(date))
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }
            
            const option = {
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    borderColor: '#404654',
                    textStyle: { color: '#fff' }
                },
                grid: {
                    left: '3%',
                    right: '5%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: data.times,
                    axisLine: { lineStyle: { color: '#404654' } },
                    axisLabel: { color: '#8b93a7', rotate: 45 }
                },
                yAxis: [
                    {
                        type: 'value',
                        name: '数量',
                        nameTextStyle: { color: '#8b93a7' },
                        axisLine: { lineStyle: { color: '#404654' } },
                        axisLabel: { color: '#8b93a7' },
                        splitLine: { lineStyle: { color: '#323649' } }
                    },
                    {
                        type: 'value',
                        name: '计次',
                        nameTextStyle: { color: '#8b93a7' },
                        axisLine: { lineStyle: { color: '#404654' } },
                        axisLabel: { color: '#8b93a7' },
                        splitLine: { show: false }
                    }
                ],
                series: [
                    {
                        name: '急涨',
                        type: 'line',
                        data: data.rush_up,
                        smooth: true,
                        itemStyle: { color: '#ff4d4f' },
                        lineStyle: { width: 3 }
                    },
                    {
                        name: '急跌',
                        type: 'line',
                        data: data.rush_down,
                        smooth: true,
                        itemStyle: { color: '#00d4aa' },
                        lineStyle: { width: 3 }
                    },
                    {
                        name: '差值',
                        type: 'line',
                        data: data.diff,
                        smooth: true,
                        itemStyle: { color: '#ffa940' },
                        lineStyle: { width: 2, type: 'dashed' }
                    },
                    {
                        name: '计次',
                        type: 'line',
                        yAxisIndex: 1,
                        data: data.count,
                        smooth: true,
                        itemStyle: { color: '#1890ff' },
                        lineStyle: { width: 2 }
                    }
                ]
            };
            
            chart.setOption(option);
        })
        .catch(error => {
            console.error('图表加载失败:', error);
        });
}

// 页面加载时获取最新数据
window.onload = function() {
    loadLatest();
};

// 响应式调整
window.addEventListener('resize', function() {
    chart.resize();
});
"""

# 路由定义
@app.route('/')
def index():
    """首页"""
    return render_template_string(HOME_HTML)

# 旧的数据看板路由已弃用，改用交易监控仪表板
# @app.route('/dashboard')
# def dashboard_old():
#     """数据看板"""
#     return render_template_string(DASHBOARD_HTML)

@app.route('/static/dashboard.js')
def dashboard_js():
    """看板JS文件"""
    return DASHBOARD_JS, 200, {'Content-Type': 'application/javascript'}

@app.route('/query')
def query_page():
    """查询页面 - 重定向到看板"""
    return redirect('/dashboard')

@app.route('/api/query')
def api_query():
    """查询API"""
    query_time = request.args.get('time', '')
    if not query_time:
        return jsonify({'error': '请提供查询时间'})
    
    try:
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                snapshot_time, rush_up, rush_down, diff, count, ratio, status
            FROM crypto_snapshots
            WHERE snapshot_time LIKE ?
            ORDER BY snapshot_time DESC
            LIMIT 1
        """, (f"{query_time}%",))
        
        snapshot = cursor.fetchone()
        
        if not snapshot:
            conn.close()
            return jsonify({'error': f'未找到 {query_time} 的数据'})
        
        snapshot_time, rush_up, rush_down, diff, count, ratio, status = snapshot
        
        cursor.execute("""
            SELECT 
                symbol, change, rush_up, rush_down, update_time,
                high_price, high_time, decline, change_24h, rank,
                current_price, ratio1, ratio2, priority_level
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
                'ratio1': row[11],
                'ratio2': row[12],
                'priority': row[13]
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
            'coins': coins
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/latest')
def api_latest():
    """获取最新数据API"""
    try:
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                snapshot_time, rush_up, rush_down, diff, count, ratio, status
            FROM crypto_snapshots
            ORDER BY snapshot_time DESC
            LIMIT 1
        """)
        
        snapshot = cursor.fetchone()
        
        if not snapshot:
            conn.close()
            return jsonify({'error': '数据库中暂无数据'})
        
        snapshot_time, rush_up, rush_down, diff, count, ratio, status = snapshot
        
        cursor.execute("""
            SELECT 
                symbol, change, rush_up, rush_down, update_time,
                high_price, high_time, decline, change_24h, rank,
                current_price, ratio1, ratio2, priority_level
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
                'ratio1': row[11],
                'ratio2': row[12],
                'priority': row[13]
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
            'coins': coins
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/chart')
def api_chart():
    """图表数据API"""
    date = request.args.get('date', '')
    if not date:
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT snapshot_time FROM crypto_snapshots ORDER BY snapshot_time DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        if result:
            date = result[0].split(' ')[0]
        else:
            return jsonify({'error': '无数据'})
    
    try:
        conn = sqlite3.connect('crypto_data.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                snapshot_time, rush_up, rush_down, diff, count
            FROM crypto_snapshots
            WHERE snapshot_time LIKE ?
            ORDER BY snapshot_time ASC
        """, (f"{date}%",))
        
        data = cursor.fetchall()
        conn.close()
        
        times = [row[0].split(' ')[1][:5] for row in data]
        rush_up = [row[1] for row in data]
        rush_down = [row[2] for row in data]
        diff = [row[3] for row in data]
        count = [row[4] for row in data]
        
        return jsonify({
            'times': times,
            'rush_up': rush_up,
            'rush_down': rush_down,
            'diff': diff,
            'count': count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/about')
def about():
    """关于页面"""
    about_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>关于系统</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
            }
            h1 { color: #667eea; margin-bottom: 20px; }
            h2 { color: #764ba2; margin-top: 30px; margin-bottom: 15px; }
            p { line-height: 1.8; color: #333; margin-bottom: 15px; }
            .back-btn {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 25px;
                border-radius: 8px;
                text-decoration: none;
                margin-top: 20px;
            }
            ul { margin: 15px 0; padding-left: 25px; }
            li { margin: 8px 0; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📖 关于加密货币数据分析系统</h1>
            
            <h2>🎯 系统功能</h2>
            <ul>
                <li><strong>历史数据查询：</strong>按日期+时间快速查询历史数据，支持多种格式</li>
                <li><strong>趋势图表：</strong>4指标曲线图（急涨、急跌、差值、计次）清晰展示市场趋势</li>
                <li><strong>优先级计算：</strong>基于最高占比和最低占比自动计算6级优先级</li>
                <li><strong>实时更新：</strong>支持定时采集，保持数据新鲜度</li>
            </ul>

            <h2>🔗 相关链接</h2>
            <ul>
                <li>GitHub仓库: <a href="https://github.com/jamesyidc/6666" target="_blank">jamesyidc/6666</a></li>
                <li>Pull Request: <a href="https://github.com/jamesyidc/6666/pull/1" target="_blank">#1</a></li>
            </ul>

            <h2>📝 技术栈</h2>
            <ul>
                <li>后端: Python + Flask</li>
                <li>数据库: SQLite</li>
                <li>前端: HTML5 + CSS3 + JavaScript</li>
                <li>图表: ECharts</li>
                <li>数据采集: Playwright</li>
            </ul>

            <a href="/" class="back-btn">← 返回首页</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(about_html)

@app.route('/api/docs')
def api_docs():
    """API文档"""
    docs_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API文档</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                background: #1a1d2e;
                color: #fff;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: #252b3f;
                border-radius: 15px;
                padding: 40px;
            }
            h1 { color: #667eea; margin-bottom: 30px; }
            h2 { color: #00d4aa; margin-top: 40px; margin-bottom: 20px; }
            .endpoint {
                background: #1a1d2e;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 25px;
                border-left: 4px solid #667eea;
            }
            .method {
                display: inline-block;
                background: #00d4aa;
                color: #1a1d2e;
                padding: 5px 12px;
                border-radius: 5px;
                font-weight: bold;
                margin-right: 10px;
            }
            .path {
                color: #ffa940;
                font-family: 'Courier New', monospace;
                font-size: 16px;
            }
            .params {
                margin-top: 15px;
                color: #8b93a7;
            }
            code {
                background: #1a1d2e;
                padding: 3px 8px;
                border-radius: 4px;
                color: #00d4aa;
                font-family: 'Courier New', monospace;
            }
            pre {
                background: #1a1d2e;
                padding: 15px;
                border-radius: 8px;
                overflow-x: auto;
                margin-top: 10px;
            }
            .back-btn {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 30px;
                border-radius: 8px;
                text-decoration: none;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 API 文档</h1>

            <h2>🔍 查询接口</h2>
            
            <div class="endpoint">
                <div>
                    <span class="method">GET</span>
                    <span class="path">/api/query</span>
                </div>
                <div class="params">
                    <p><strong>参数:</strong> <code>time</code> - 查询时间 (格式: YYYY-MM-DD HH:MM)</p>
                    <p><strong>返回:</strong> 指定时间点的完整数据（急涨、急跌、差值、计次、币种列表等）</p>
                </div>
                <pre>示例: /api/query?time=2025-12-06 13:42</pre>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method">GET</span>
                    <span class="path">/api/latest</span>
                </div>
                <div class="params">
                    <p><strong>参数:</strong> 无</p>
                    <p><strong>返回:</strong> 最新的完整数据</p>
                </div>
                <pre>示例: /api/latest</pre>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method">GET</span>
                    <span class="path">/api/chart</span>
                </div>
                <div class="params">
                    <p><strong>参数:</strong> <code>date</code> - 日期 (格式: YYYY-MM-DD, 可选)</p>
                    <p><strong>返回:</strong> 指定日期的图表数据（时间点、急涨、急跌、差值、计次）</p>
                </div>
                <pre>示例: /api/chart?date=2025-12-06</pre>
            </div>

            <h2>📊 页面路由</h2>
            
            <div class="endpoint">
                <div>
                    <span class="method">GET</span>
                    <span class="path">/</span>
                </div>
                <div class="params">
                    <p><strong>说明:</strong> 系统首页</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method">GET</span>
                    <span class="path">/dashboard</span>
                </div>
                <div class="params">
                    <p><strong>说明:</strong> 数据看板（主界面）</p>
                </div>
            </div>

            <div class="endpoint">
                <div>
                    <span class="method">GET</span>
                    <span class="path">/about</span>
                </div>
                <div class="params">
                    <p><strong>说明:</strong> 关于系统</p>
                </div>
            </div>

            <a href="/" class="back-btn">← 返回首页</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(docs_html)

# ==================== 交易决策系统路由 ====================

@app.route('/trading-decision')
def trading_decision_page():
    """交易决策系统管理页面"""
    return render_template_string(TRADING_DECISION_HTML)

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


# 交易决策系统HTML模板
TRADING_DECISION_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自动交易决策系统</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .config-group {
            margin-bottom: 20px;
        }
        .config-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        .config-group select,
        .config-group input {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .config-group select:focus,
        .config-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .switch-group {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #4CAF50;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
            width: 100%;
            margin-top: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn:active {
            transform: translateY(0);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-on {
            background: #4CAF50;
            box-shadow: 0 0 10px #4CAF50;
        }
        .status-off {
            background: #f44336;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: #f8f9fa;
            color: #667eea;
            font-weight: 600;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .badge-long { background: #e3f2fd; color: #1976d2; }
        .badge-short { background: #fce4ec; color: #c2185b; }
        .badge-close { background: #fff3e0; color: #f57c00; }
        .badge-add { background: #e8f5e9; color: #388e3c; }
        .badge-profit { background: #4CAF50; color: white; }
        .badge-loss { background: #f44336; color: white; }
        .badge-anchor { background: #764ba2; color: white; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background: #f8f9fa;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .tab.active {
            background: #667eea;
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 自动交易决策系统</h1>
            <p>第一阶段：核心决策逻辑 - 止盈规则 + 锚点单维护</p>
        </div>

        <div class="grid">
            <!-- 左侧：配置面板 -->
            <div>
                <div class="card">
                    <h2>⚙️ 系统配置</h2>
                    
                    <div class="switch-group">
                        <span><strong>🔒 安全闸门（总开关）</strong></span>
                        <label class="switch">
                            <input type="checkbox" id="enabled-switch">
                            <span class="slider"></span>
                        </label>
                    </div>

                    <div class="config-group">
                        <label>📊 市场模式</label>
                        <select id="market-mode">
                            <option value="manual">手动</option>
                            <option value="auto">自动</option>
                        </select>
                    </div>

                    <div class="config-group">
                        <label>📈 市场趋势</label>
                        <select id="market-trend">
                            <option value="neutral">中性</option>
                            <option value="bullish">多头主导</option>
                            <option value="bearish">空头主导</option>
                        </select>
                    </div>

                    <div class="config-group">
                        <label>💰 总本金（USDT）</label>
                        <input type="number" id="total-capital" min="0" step="100">
                    </div>

                    <div class="config-group">
                        <label>📊 可开仓额度（%）</label>
                        <input type="number" id="position-limit" min="0" max="100" step="5">
                    </div>

                    <div class="config-group">
                        <label>⚓ 锚点单上限（USDT）</label>
                        <input type="number" id="anchor-limit" min="0" step="10">
                    </div>

                    <div class="switch-group">
                        <span><strong>允许开多单</strong></span>
                        <label class="switch">
                            <input type="checkbox" id="allow-long-switch">
                            <span class="slider"></span>
                        </label>
                    </div>

                    <button class="btn" onclick="saveConfig()">💾 保存配置</button>
                    <button class="btn" onclick="loadConfig()" style="background: #666; margin-top: 5px;">🔄 刷新配置</button>
                </div>
            </div>

            <!-- 右侧：状态和记录 -->
            <div>
                <div class="card">
                    <h2>📊 系统状态</h2>
                    <div id="system-status"></div>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <div class="tabs">
                        <button class="tab active" onclick="switchTab('decisions')">交易决策</button>
                        <button class="tab" onclick="switchTab('signals')">交易信号</button>
                        <button class="tab" onclick="switchTab('maintenance')">锚点维护</button>
                    </div>

                    <div id="decisions-tab" class="tab-content active">
                        <h2>📝 交易决策记录</h2>
                        <div id="decisions-list"></div>
                    </div>

                    <div id="signals-tab" class="tab-content">
                        <h2>📡 交易信号（API）</h2>
                        <div id="signals-list"></div>
                    </div>

                    <div id="maintenance-tab" class="tab-content">
                        <h2>🔧 锚点单维护记录</h2>
                        <div id="maintenance-list"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentConfig = {};

        // 加载配置
        async function loadConfig() {
            try {
                const response = await fetch('/api/trading/config');
                const data = await response.json();
                
                if (data.success) {
                    currentConfig = data.config;
                    
                    document.getElementById('enabled-switch').checked = currentConfig.enabled || false;
                    document.getElementById('market-mode').value = currentConfig.market_mode || 'manual';
                    document.getElementById('market-trend').value = currentConfig.market_trend || 'neutral';
                    document.getElementById('total-capital').value = currentConfig.total_capital || 1000;
                    document.getElementById('position-limit').value = currentConfig.position_limit_percent || 60;
                    document.getElementById('anchor-limit').value = currentConfig.anchor_capital_limit || 200;
                    document.getElementById('allow-long-switch').checked = currentConfig.allow_long || false;
                    
                    updateSystemStatus();
                }
            } catch (error) {
                console.error('加载配置失败:', error);
            }
        }

        // 保存配置
        async function saveConfig() {
            const newConfig = {
                enabled: document.getElementById('enabled-switch').checked,
                market_mode: document.getElementById('market-mode').value,
                market_trend: document.getElementById('market-trend').value,
                total_capital: parseFloat(document.getElementById('total-capital').value),
                position_limit_percent: parseFloat(document.getElementById('position-limit').value),
                anchor_capital_limit: parseFloat(document.getElementById('anchor-limit').value),
                allow_long: document.getElementById('allow-long-switch').checked,
                position_limit_mode: 'manual',
                anchor_capital_percent: 10,
                min_granularity: 1,
                long_granularity: 10
            };

            try {
                const response = await fetch('/api/trading/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newConfig)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ 配置保存成功！');
                    loadConfig();
                } else {
                    alert('❌ 保存失败: ' + data.error);
                }
            } catch (error) {
                alert('❌ 保存失败: ' + error.message);
            }
        }

        // 更新系统状态
        function updateSystemStatus() {
            const enabled = currentConfig.enabled;
            const statusHtml = `
                <div style="padding: 20px; background: ${enabled ? '#e8f5e9' : '#ffebee'}; border-radius: 8px;">
                    <p style="font-size: 1.2em; margin-bottom: 15px;">
                        <span class="status-indicator ${enabled ? 'status-on' : 'status-off'}"></span>
                        系统状态: <strong>${enabled ? '🟢 运行中' : '🔴 已停止'}</strong>
                    </p>
                    <p><strong>市场模式:</strong> ${currentConfig.market_mode || 'manual'}</p>
                    <p><strong>市场趋势:</strong> ${currentConfig.market_trend || 'neutral'}</p>
                    <p><strong>总本金:</strong> ${currentConfig.total_capital || 1000} USDT</p>
                    <p><strong>可开仓额度:</strong> ${currentConfig.position_limit_percent || 60}%</p>
                    <p><strong>允许开多:</strong> ${currentConfig.allow_long ? '是' : '否'}</p>
                </div>
            `;
            document.getElementById('system-status').innerHTML = statusHtml;
        }

        // 加载交易决策
        async function loadDecisions() {
            try {
                const response = await fetch('/api/trading/decisions?limit=50');
                const data = await response.json();
                
                if (data.success && data.decisions.length > 0) {
                    let html = '<table><thead><tr><th>时间</th><th>币种</th><th>方向</th><th>动作</th><th>类型</th><th>收益率</th><th>平仓量</th><th>原因</th></tr></thead><tbody>';
                    
                    data.decisions.forEach(d => {
                        html += `<tr>
                            <td>${d.timestamp}</td>
                            <td>${d.inst_id}</td>
                            <td><span class="badge badge-${d.pos_side}">${d.pos_side}</span></td>
                            <td><span class="badge badge-${d.action}">${d.action}</span></td>
                            <td><span class="badge badge-${d.decision_type === 'take_profit' ? 'profit' : 'anchor'}">${d.decision_type}</span></td>
                            <td style="color: ${d.profit_rate >= 0 ? 'green' : 'red'}">${d.profit_rate.toFixed(2)}%</td>
                            <td>${d.close_size.toFixed(4)}</td>
                            <td>${d.reason}</td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('decisions-list').innerHTML = html;
                } else {
                    document.getElementById('decisions-list').innerHTML = '<p style="text-align:center;color:#999;padding:20px;">暂无交易决策记录</p>';
                }
            } catch (error) {
                console.error('加载决策失败:', error);
            }
        }

        // 加载交易信号
        async function loadSignals() {
            try {
                const response = await fetch('/api/trading/signals?limit=50');
                const data = await response.json();
                
                if (data.success && data.signals.length > 0) {
                    let html = '<table><thead><tr><th>时间</th><th>币种</th><th>信号类型</th><th>动作</th><th>价格</th><th>数量</th><th>收益率</th><th>原因</th></tr></thead><tbody>';
                    
                    data.signals.forEach(s => {
                        html += `<tr>
                            <td>${s.timestamp}</td>
                            <td>${s.inst_id}</td>
                            <td><span class="badge badge-${s.signal_type === 'take_profit' ? 'profit' : 'anchor'}">${s.signal_type}</span></td>
                            <td><span class="badge badge-${s.action}">${s.action}</span></td>
                            <td>${s.price.toFixed(4)}</td>
                            <td>${s.size.toFixed(4)}</td>
                            <td style="color: ${s.profit_rate >= 0 ? 'green' : 'red'}">${s.profit_rate.toFixed(2)}%</td>
                            <td>${s.reason}</td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('signals-list').innerHTML = html;
                } else {
                    document.getElementById('signals-list').innerHTML = '<p style="text-align:center;color:#999;padding:20px;">暂无交易信号</p>';
                }
            } catch (error) {
                console.error('加载信号失败:', error);
            }
        }

        // 加载维护记录
        async function loadMaintenance() {
            try {
                const response = await fetch('/api/trading/maintenance?limit=50');
                const data = await response.json();
                
                if (data.success && data.records.length > 0) {
                    let html = '<table><thead><tr><th>时间</th><th>币种</th><th>方向</th><th>原始仓位</th><th>维护仓位</th><th>维护价格</th><th>收益率</th><th>动作</th><th>状态</th></tr></thead><tbody>';
                    
                    data.records.forEach(r => {
                        html += `<tr>
                            <td>${r.timestamp}</td>
                            <td>${r.inst_id}</td>
                            <td><span class="badge badge-${r.pos_side}">${r.pos_side}</span></td>
                            <td>${r.original_size.toFixed(4)}</td>
                            <td>${r.maintenance_size.toFixed(4)}</td>
                            <td>${r.maintenance_price.toFixed(4)}</td>
                            <td style="color: ${r.profit_rate >= 0 ? 'green' : 'red'}">${r.profit_rate.toFixed(2)}%</td>
                            <td>${r.action}</td>
                            <td>${r.status}</td>
                        </tr>`;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('maintenance-list').innerHTML = html;
                } else {
                    document.getElementById('maintenance-list').innerHTML = '<p style="text-align:center;color:#999;padding:20px;">暂无维护记录</p>';
                }
            } catch (error) {
                console.error('加载维护记录失败:', error);
            }
        }

        // 切换标签
        function switchTab(tabName) {
            // 更新标签按钮
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            // 更新内容
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // 加载对应数据
            if (tabName === 'decisions') loadDecisions();
            else if (tabName === 'signals') loadSignals();
            else if (tabName === 'maintenance') loadMaintenance();
        }

        // 初始化
        window.onload = function() {
            loadConfig();
            loadDecisions();
            
            // 自动刷新（每60秒）
            setInterval(() => {
                loadConfig();
                const activeTab = document.querySelector('.tab.active').textContent;
                if (activeTab.includes('交易决策')) loadDecisions();
                else if (activeTab.includes('交易信号')) loadSignals();
                else if (activeTab.includes('锚点维护')) loadMaintenance();
            }, 60000);
        };
    </script>
</body>
</html>
"""


# 导入交易管理API
from trading_api import trading_bp

# 注册交易管理Blueprint
app.register_blueprint(trading_bp)


@app.route('/trading-manager')
def trading_manager():
    """交易管理界面"""
    with open('/home/user/webapp/templates/trading_manager.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/dashboard')
def dashboard():
    """实时监控仪表板"""
    with open('/home/user/webapp/templates/dashboard.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/anchor-auto-monitor')
def anchor_auto_monitor():
    """锚点单自动开仓监控"""
    with open('/home/user/webapp/templates/anchor_auto_monitor.html', 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
