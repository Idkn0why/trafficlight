import pandas as pd
import json

# 读取json文件
with open('filtered_links_cleaned.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# 提取所有link_id
nds_ids = set()
for item in json_data:
    if 'nds_id' in item:
        nds_ids.add(str(item['nds_id']))  # 转换为字符串以匹配数据文件中的格式

print(f"从json中提取到{len(nds_ids)}个不同的nds_id")

# 读取数据文件
df = pd.read_csv('DATA0329.txt', sep='\t', dtype=str)

# 统计原始数据中的nds_id数量
original_nds_count = df['nds_id'].nunique()
print(f"原始数据中有{original_nds_count}个不同的nds_id")

# 筛选出nds_id在link_ids中的数据
filtered_df = df[df['nds_id'].isin(nds_ids)]

# 统计筛选后的数据
filtered_nds_count = filtered_df['nds_id'].nunique()
print(f"筛选后数据中有{filtered_nds_count}个不同的nds_id")
print(f"被筛除的nds_id数量: {original_nds_count - filtered_nds_count}")

# 保存筛选后的数据
filtered_df.to_csv('data/filtered_DATA0329.txt', sep='\t', index=False)

# 保存被筛除的nds_id列表
removed_nds = set(df['nds_id'].unique()) - set(filtered_df['nds_id'].unique())
with open('removed_nds_ids.txt', 'w', encoding='utf-8') as f:
    for nds_id in removed_nds:
        f.write(f"{nds_id}\n")

print("\n处理完成！")
print(f"筛选后的数据已保存到 filtered_DATA0329.txt")
print(f"被筛除的nds_id列表已保存到 removed_nds_ids.txt") 