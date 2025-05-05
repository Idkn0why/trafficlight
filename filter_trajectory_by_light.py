import pandas as pd

# 读取DATA0329数据
data0329 = pd.read_csv('data/merged_16h_timing_data.txt', sep='\t')
nds_ids = set(data0329['nds_id'].unique())
print(f"DATA0329数据包含 {len(nds_ids)} 个唯一的nds_id")

# 读取轨迹数据
trajectory_data = pd.read_csv('data/filtered_trajectory_matched_16_17_method1.txt', sep='\t')
print(f"轨迹数据包含 {len(trajectory_data)} 条记录")
trajectory_data_nds_ids = set(trajectory_data['nds_id'].unique())
print(f"轨迹数据包含 {len(trajectory_data_nds_ids)} 个唯一的nds_id")

# 筛选数据
filtered_trajectory = trajectory_data[trajectory_data['nds_id'].isin(nds_ids)]
# 保存被筛除的数据
filtered_trajectory_removed = trajectory_data[~trajectory_data['nds_id'].isin(nds_ids)]
# 保存结果
filtered_trajectory.to_csv('data/filtered_trajectory_16_17_by_light_method1.txt', sep='\t', index=False)
filtered_trajectory_removed.to_csv('data/filtered_trajectory_16_17_removed_by_light_method1.txt', sep='\t', index=False)
print(f"处理完成！筛选后的数据包含 {len(filtered_trajectory)} 条记录")
filtered_nds_ids = set(filtered_trajectory['nds_id'].unique())
print(f"筛选后的数据包含 {len(filtered_nds_ids)} 个唯一的nds_id")



