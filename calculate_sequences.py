def calculate_sequences(data_points):
    """计算SAR连续序列和统计
    
    每个序列会展开成多个数据点，每个点都带有该点在序列中的位置编号
    例如：空头序列有3个数据点，会返回3条记录，分别标记为空头01、空头02、空头03
    """
    if not data_points: return []
    sequences = []
    current_seq = {'position': data_points[0]['sar_position'], 'data': [data_points[0]]}
    
    for i in range(1, len(data_points)):
        if data_points[i]['sar_position'] == current_seq['position']:
            current_seq['data'].append(data_points[i])
        else:
            # 将当前序列的每个数据点作为独立记录
            sequences.extend(build_sequence_points(current_seq, len(sequences) + 1))
            current_seq = {'position': data_points[i]['sar_position'], 'data': [data_points[i]]}
    
    # 添加最后一个序列的所有数据点
    sequences.extend(build_sequence_points(current_seq, len(sequences) + 1))
    return sequences

def build_sequence_points(seq, seq_number):
    """构建序列中的每个数据点记录"""
    data = seq['data']
    total_points = len(data)
    result = []
    
    for point_index, point_data in enumerate(data, 1):
        # 计算该点相对于序列起点的变化
        sar_diff = point_data['sar_value'] - data[0]['sar_value']
        price_change = ((point_data['price_close'] - data[0]['price_close']) / data[0]['price_close'] * 100) if data[0]['price_close'] else 0
        
        result.append({
            'seq_number': seq_number,
            'point_number': point_index,  # 该点在序列中的位置（1-based）
            'total_points': total_points,  # 序列总数据点数
            'sequence': point_index,  # 为了兼容前端，保持这个字段
            'position': seq['position'],
            'time': point_data['datetime_beijing'],
            'start_time': data[0]['datetime_beijing'],
            'end_time': point_data['datetime_beijing'],
            'price': point_data['price_close'],
            'start_price': data[0]['price_close'],
            'end_price': point_data['price_close'],
            'sar': point_data['sar_value'],
            'sar_value': point_data['sar_value'],
            'start_sar': data[0]['sar_value'],
            'end_sar': point_data['sar_value'],
            'sar_diff': sar_diff,
            'sequence_change_percent': price_change,
            'change_1day_percent': price_change,
            'avg_1day': abs(price_change) / point_index if point_index > 0 else 0,
            'change_3day_percent': price_change,
            'avg_3day': abs(price_change) / point_index if point_index > 0 else 0,
            'change_7day_percent': price_change,
            'avg_7day': abs(price_change) / point_index if point_index > 0 else 0,
            'change_15day_percent': price_change,
            'avg_15day': abs(price_change) / point_index if point_index > 0 else 0
        })
    
    return result

def build_sequence(seq, seq_number):
    data = seq['data']
    sar_diff = data[-1]['sar_value'] - data[0]['sar_value']
    price_change = ((data[-1]['price_close'] - data[0]['price_close']) / data[0]['price_close'] * 100) if data[0]['price_close'] else 0
    avg_change = abs(price_change) / len(data) if len(data) > 0 else 0
    return {
        'seq_number': seq_number,
        'sequence': len(data),
        'position': seq['position'],
        'time': data[-1]['datetime_beijing'],
        'start_time': data[0]['datetime_beijing'],
        'end_time': data[-1]['datetime_beijing'],
        'price': data[-1]['price_close'],
        'start_price': data[0]['price_close'],
        'end_price': data[-1]['price_close'],
        'sar': data[-1]['sar_value'],
        'sar_value': data[-1]['sar_value'],
        'start_sar': data[0]['sar_value'],
        'end_sar': data[-1]['sar_value'],
        'sar_diff': sar_diff,
        'sequence_change_percent': price_change,
        'change_1day_percent': price_change,
        'avg_1day': avg_change,
        'change_3day_percent': price_change,
        'avg_3day': avg_change,
        'change_7day_percent': price_change,
        'avg_7day': avg_change,
        'change_15day_percent': price_change,
        'avg_15day': avg_change
    }
