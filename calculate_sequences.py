def calculate_sequences(data_points):
    """计算SAR连续序列和统计"""
    if not data_points: return []
    sequences = []
    current_seq = {'position': data_points[0]['sar_position'], 'data': [data_points[0]]}
    
    for i in range(1, len(data_points)):
        if data_points[i]['sar_position'] == current_seq['position']:
            current_seq['data'].append(data_points[i])
        else:
            sequences.append(build_sequence(current_seq))
            current_seq = {'position': data_points[i]['sar_position'], 'data': [data_points[i]]}
    sequences.append(build_sequence(current_seq))
    return sequences

def build_sequence(seq):
    data = seq['data']
    return {
        'sequence': len(data),
        'position': seq['position'],
        'start_time': data[0]['datetime_beijing'],
        'end_time': data[-1]['datetime_beijing'],
        'start_price': data[0]['price_close'],
        'end_price': data[-1]['price_close'],
        'start_sar': data[0]['sar_value'],
        'end_sar': data[-1]['sar_value'],
        'sar_diff': data[-1]['sar_value'] - data[0]['sar_value'],
        'price_change_percent': ((data[-1]['price_close'] - data[0]['price_close']) / data[0]['price_close'] * 100) if data[0]['price_close'] else 0
    }
