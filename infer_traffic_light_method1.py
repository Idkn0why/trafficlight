import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime

def map_exit_turn_to_dir(exit_turn):
    """
    将exit_turn映射到dir值
    exit_turn: 离开此link的角度，向左为正向右为负，取值范围在[-180,180]
    dir: 由此link驶入下一个link的行驶方式
        0-直行, 1-左转, 2-右转, 7-掉头
    """
    if abs(exit_turn) < 30:  # 直行
        return 0
    elif exit_turn > 30 and exit_turn < 150:  # 左转
        return 1
    elif exit_turn < -30 and exit_turn > -150:  # 右转
        return 2
    elif abs(exit_turn) > 150:  # 掉头
        return 7
    else:
        return None

# 读取数据
df = pd.read_csv('data/filtered_trajectory_16_17_by_light_method1.txt', sep='\t', dtype=str)
# 读取信号灯周期数据
cycle_data = pd.read_csv('data/merged_16h_timing_data.txt', sep='\t', dtype=str)

# 将时间转换为秒数，方便计算
def time_to_seconds(time_str):
    # 解析完整的时间字符串
    dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S%z')
    # 只返回当天的时间（秒数）
    return dt.hour * 3600 + dt.minute * 60 + dt.second

# 将秒数转换回时间字符串
def seconds_to_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# 创建一个字典来存储每个信号灯的推测时间
inferred_times = defaultdict(list)
removed_data = []

# 保存所有next_nds_id为0的数据
removed_data.append(df[df['next_nds_id'] == '0'])

# 对每个nds_id和next_nds_id的组合进行处理
for nds_id in df['nds_id'].unique():
    # 获取该nds_id的所有数据
    nds_data = df[df['nds_id'] == nds_id].copy()
    
    # 对每个next_nds_id分别处理
    for next_id in nds_data['next_nds_id'].unique():
        # 获取特定next_nds_id的数据
        light_data = nds_data[nds_data['next_nds_id'] == next_id].copy()
        
        # 获取该组合的exit_turn的平均值
        # 先将exit_turn转换为数值类型
        light_data['exit_turn'] = pd.to_numeric(light_data['exit_turn'], errors='coerce')
        # 计算平均值，忽略NaN值
        exit_turn = light_data['exit_turn'].mean()
        # 如果所有值都是NaN，则使用0
        if pd.isna(exit_turn):
            exit_turn = 0
        
        # 将exit_turn映射到dir值
        dir = map_exit_turn_to_dir(exit_turn)

        # 根据nds_id和dir值获取对应的cycle_data
        cycle_data_dir = cycle_data[(cycle_data['nds_id'] == nds_id) & (cycle_data['dir'] == str(dir))]

        # 将enter_time转换为秒
        light_data['enter_time_seconds'] = light_data['enter_time'].apply(time_to_seconds)
        
        # 离开时间通过enter_time和travel_time计算
        light_data['end_time_seconds'] = light_data['enter_time_seconds'] + pd.to_numeric(light_data['travel_time'])
        
        # 按时间排序
        light_data = light_data.sort_values('end_time_seconds')
        
        # 计算相邻车辆离开的时间差
        time_diffs = np.diff(light_data['end_time_seconds'])
        
        # 找出时间差较大的点（可能是红灯变绿灯的点）
        # 这里假设时间差大于0.9周期的点可能是红灯变绿灯的点
        if len(cycle_data_dir) > 0:
            # 将cycle_time转换为数值类型
            cycle_time = pd.to_numeric(cycle_data_dir['cycle_time'], errors='coerce')
            threshold = 0.9 * cycle_time.mean()
        else:
            threshold = 30
        potential_green_starts = []
        
        for i in range(len(time_diffs)):
            if time_diffs[i] > threshold:
                # 记录这个时间点
                potential_green_starts.append(light_data.iloc[i + 1]['end_time_seconds'])
        
        # 如果potential为空
        if len(potential_green_starts) == 0 and len(light_data) > 0:
            # 直接记录第一个点
            inferred_times[(nds_id, next_id, exit_turn,dir)].append(seconds_to_time(int(light_data.iloc[0]['end_time_seconds'])))
            continue

        if len(potential_green_starts) > 1:
            for time in potential_green_starts:
                inferred_times[(nds_id, next_id, exit_turn,dir)].append(seconds_to_time(int(time)))
        elif len(potential_green_starts) == 1:
            # 如果只有一个时间点，直接保存
            inferred_times[(nds_id, next_id, exit_turn,dir)].append(seconds_to_time(int(potential_green_starts[0])))

# 将结果转换为DataFrame
results = []
for (nds_id, next_id, exit_turn,dir), times in inferred_times.items():
    for i, time in enumerate(times):
        results.append({
            'nds_id': nds_id,
            'next_nds_id': next_id,
            'exit_turn': exit_turn,
            'dir': dir,
            'phase_index': i + 1,
            'green_start_time': time
        })

# 创建DataFrame并保存
results_df = pd.DataFrame(results)
results_df.to_csv('data/inferred_traffic_light_method1.txt', sep='\t', index=False, encoding='utf-8')

# 处理被移除的数据
removed_data_df = pd.concat(removed_data)
# 找出在removed_data中但不在results_df中的nds_id
unique_removed_nds_ids = set(removed_data_df['nds_id'].unique()) - set(results_df['nds_id'].unique())
removed_data_df = removed_data_df[removed_data_df['nds_id'].isin(unique_removed_nds_ids)]

# 打印统计信息
print(f"总共处理了 {len(df['nds_id'].unique())} 个nds_id")
print(f"成功推测出时间的信号灯数量: {len(results_df['nds_id'].unique())}")