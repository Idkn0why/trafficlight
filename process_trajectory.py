import pandas as pd
from datetime import datetime, timedelta

# 读取数据
df = pd.read_csv('data/filtered_trajectory_16_17_by_light.txt', sep='\t')

# 计算离开时间
df['exit_time'] = pd.to_datetime(df['enter_time']) + pd.to_timedelta(df['travel_time'], unit='s')

# 按nds_id和next_nds_id分组
grouped = df.groupby(['nds_id', 'next_nds_id'])

# 计算每个组的统计信息
result = grouped.agg({
    'exit_time': lambda x: ','.join(x.astype(str)),  # 保留所有离开时间
    'exit_turn': 'mean',   # 计算平均转向角度
    'travel_time': 'mean', # 计算平均行驶时间
    'stop_time': 'mean',   # 计算平均停车时间
    'link_length': 'mean', # 计算平均路段长度
    'avg_speed': 'mean'    # 计算平均速度
}).reset_index()

# 保存结果
result.to_csv('data/clustered_trajectory.txt', sep='\t', index=False)
print("处理完成，结果已保存到 clustered_trajectory.txt") 