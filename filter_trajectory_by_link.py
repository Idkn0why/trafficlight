import json
import pandas as pd

# 读取filtered_links_cleaned.json文件
with open('data/filtered_links_cleaned.json', 'r', encoding='utf-8') as f:
    links_data = json.load(f)

# 提取所有nds_id
valid_nds_ids = set()
for link in links_data:
    valid_nds_ids.add(str(link['nds_id']))

# 输出valid_nds_ids的数量
print(f"valid_nds_ids的数量: {len(valid_nds_ids)}")
# 读取轨迹文件
trajectory_df = pd.read_csv('data/filtered_trajectory_16_17_method1.txt', sep='\t')

# 输出trajectory_df的行数
print(f"trajectory_df的行数: {len(trajectory_df)}")

# 筛选数据
filtered_df = trajectory_df[trajectory_df['nds_id'].astype(str).isin(valid_nds_ids)]

# 输出filtered_df的行数
print(f"filtered_df的行数: {len(filtered_df)}")

# 保存结果
filtered_df.to_csv('data/filtered_trajectory_matched_16_17_method1.txt', sep='\t', index=False) 