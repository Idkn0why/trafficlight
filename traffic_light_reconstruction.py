import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

def load_data():
    # 读取信号灯周期数据
    cycle_data = pd.read_csv('data/merged_16h_timing_data.txt', sep='\t')
    
    # 读取信号灯推测绿灯开始时间数据
    phase_data = pd.read_csv('data/inferred_traffic_light_method1.txt', sep='\t')
    
    return cycle_data, phase_data

def find_best_cycle_start(phase_times, cycle_time):
    """
    用模周期下的单位圆均值方法，寻找最优周期起点。
    """
    if not phase_times:
        return None

    # 转为秒值（从午夜开始）
    seconds_list = [(t - datetime.combine(t.date(), datetime.min.time())).total_seconds() for t in phase_times]
    
    # 映射到单位圆（单位周期为2π）
    angles = [2 * np.pi * (s % cycle_time) / cycle_time for s in seconds_list]
    
    # 求单位向量平均方向
    sin_sum = np.sum(np.sin(angles))
    cos_sum = np.sum(np.cos(angles))
    
    mean_angle = np.arctan2(sin_sum, cos_sum)  # 返回值范围 [-π, π]
    if mean_angle < 0:
        mean_angle += 2 * np.pi  # 映射到 [0, 2π]

    # 反推回起点在周期内的偏移秒数
    offset_in_cycle = (cycle_time * mean_angle) / (2 * np.pi)

    return offset_in_cycle

def reconstruct_traffic_light(cycle_data, phase_data):
    # 创建结果DataFrame
    result = []
    
    # 用于统计未使用的数据
    used_cycle_keys = set()  # 记录已使用的cycle_data的键
    used_phase_keys = set()  # 记录已使用的phase_data的键
    
    # 遍历每个路口
    for inter_id in cycle_data['inter_id'].unique():
        # 获取该路口的cycle_data和phase_data
        inter_cycle_data = cycle_data[cycle_data['inter_id'] == inter_id]
        inter_phase_data = phase_data[phase_data['nds_id'].isin(inter_cycle_data['nds_id'])]
        
        # 遍历每个方向
        for _, cycle_row in inter_cycle_data.iterrows():
            nds_id = cycle_row['nds_id']
            dir_value = cycle_row['dir']
            cycle_time = cycle_row['cycle_time']
            green_time = cycle_row['green_time']
            red_time = cycle_row['red_time']
            
            # 记录cycle_data的键
            cycle_key = (inter_id, nds_id, dir_value)

            # 获取这个方向相关的phase_data
            phase_data_dir = inter_phase_data[
                (inter_phase_data['nds_id'] == nds_id) & 
                (inter_phase_data['dir'] == dir_value)
            ]
            
            # 获取该方向的绿灯开始时间
            phase_times = phase_data_dir['green_start_time'].tolist()

            if not phase_times:
                # 跳过数据
                
                continue
                
            next_nds_id = str(phase_data_dir['next_nds_id'].iloc[0])
            
            # 记录phase_data的键
            phase_key = (nds_id, next_nds_id, phase_data_dir['exit_turn'].iloc[0])
            used_phase_keys.add(phase_key)
            
            # 将时间字符串转换为datetime对象
            phase_times = [datetime.strptime(t, '%H:%M:%S') for t in phase_times]
            
            # 找出最合理的周期起始点
            cycle_start = find_best_cycle_start(phase_times, cycle_time)
            if not cycle_start:
                continue
            
            first_cycle_start = cycle_start%cycle_time
            
            # 储存结果，只需要周期起始时间和周期时长
            result.append({
                'inter_id': inter_id,
                'nds_id': nds_id,
                'next_nds_id': next_nds_id,
                'dir': dir_value,
                'cycle_start': first_cycle_start,
                'cycle_time': cycle_time,
                'green_time': green_time,
                'red_time': red_time
            })
            used_cycle_keys.add(cycle_key)
    
    # 统计未使用的数据
    unused_cycle_data = []
    for _, row in cycle_data.iterrows():
        key = (row['inter_id'], row['nds_id'], row['dir'])
        if key not in used_cycle_keys:
            unused_cycle_data.append(row)
    
    unused_phase_data = []
    for _, row in phase_data.iterrows():
        key = (row['nds_id'], str(row['next_nds_id']), row['exit_turn'])
        if key not in used_phase_keys:
            unused_phase_data.append(row)
    
    return pd.DataFrame(result), pd.DataFrame(unused_cycle_data), pd.DataFrame(unused_phase_data)

def main():
    # 加载数据
    cycle_data, phase_data = load_data()
    
    # 还原信号灯信号并获取未使用的数据
    reconstructed_signals, unused_cycle_data, unused_phase_data = reconstruct_traffic_light(cycle_data, phase_data)
    
    # 保存结果
    reconstructed_signals.to_csv('data/reconstructed_method1.txt', sep='\t', index=False)
    unused_cycle_data.to_csv('data/unused_cycle_data.txt', sep='\t', index=False)
    unused_phase_data.to_csv('data/unused_phase_data.txt', sep='\t', index=False)
    
    # 打印统计信息
    print(f"总周期数据条数: {len(cycle_data)}")
    print(f"未使用的周期数据条数: {len(unused_cycle_data)}")
    print(f"周期数据利用率: {(len(cycle_data) - len(unused_cycle_data)) / len(cycle_data) * 100:.2f}%")
    print()
    print(f"总相位数据条数: {len(phase_data)}")
    print(f"未使用的相位数据条数: {len(unused_phase_data)}")
    print(f"相位数据利用率: {(len(phase_data) - len(unused_phase_data)) / len(phase_data) * 100:.2f}%")

if __name__ == "__main__":
    main() 