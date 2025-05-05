import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv('data/filtered_DATA0329.txt', sep='\t', dtype=str)

# 输出不同的nds_id数量
print(f"原始数据中的不同的nds_id数量: {df['nds_id'].nunique()}")

# 获取16时的数据作为基准
df_16 = df[df['hour'] == '16'].copy()

# 获取其他时间的数据
df_other = df[df['hour'] != '16'].copy()

# 将hour转换为整数，处理可能的NaN值
df_other['hour'] = pd.to_numeric(df_other['hour'], errors='coerce')
df_other = df_other.dropna(subset=['hour'])  # 删除hour为NaN的行
df_other['hour'] = df_other['hour'].astype(int)
# 输出删除hour为NaN的行后的nds_id数量
print(f"删除hour为NaN的行后的nds_id数量: {df_other['nds_id'].nunique()}")

# 创建一个唯一标识符，用于匹配数据
df_16['unique_key'] = df_16['nds_id'] + '_' + df_16['dir']
df_other['unique_key'] = df_other['nds_id'] + '_' + df_other['dir']

# 获取16时数据中所有唯一的标识符
unique_keys_16 = set(df_16['unique_key'])

# 获取其他时间数据中所有唯一的标识符
unique_keys_other = set(df_other['unique_key'])

# 找出16时缺失的标识符
missing_keys = unique_keys_other - unique_keys_16

# 创建一个新的DataFrame来存储补充的数据
supplemental_data = []

# 对于每个缺失的标识符，找到最接近16时的数据
for key in missing_keys:
    # 获取包含这个标识符的所有数据
    matching_data = df_other[df_other['unique_key'] == key].copy()
    
    if len(matching_data) > 0:
        # 计算每个时间点与16时和17时的差距
        time_diff_16 = abs(matching_data['hour'] - 16)
        time_diff_17 = abs(matching_data['hour'] - 17)
        
        # 取最小值作为时间差
        matching_data['time_diff'] = pd.DataFrame({'diff16': time_diff_16, 'diff17': time_diff_17}).min(axis=1)
        
        # 找到最接近16时或17时的数据
        closest_data = matching_data.loc[matching_data['time_diff'].idxmin()]
        
        # 添加到补充数据中
        supplemental_data.append(closest_data)

# 将补充数据转换为DataFrame
if supplemental_data:
    df_supplement = pd.DataFrame(supplemental_data)
    # 合并原始16时数据和补充数据
    df_complete = pd.concat([df_16, df_supplement], ignore_index=True)
else:
    df_complete = df_16

# 输出不同的nds_id数量
print(f"原始16时数据中的不同的nds_id数量: {df_16['nds_id'].nunique()}")
print(f"补充数据中的不同的nds_id数量: {df_supplement['nds_id'].nunique()}")
print(f"完整数据中的不同的nds_id数量: {df_complete['nds_id'].nunique()}")

# 删除临时列
df_complete = df_complete.drop(['unique_key'], axis=1)

# 将nds_id转换为数值类型以便正确排序
df_complete['nds_id'] = pd.to_numeric(df_complete['nds_id'], errors='coerce')
df_complete = df_complete.dropna(subset=['nds_id'])  # 删除nds_id为NaN的行

# 按照inter_id和nds_id排序
df_complete = df_complete.sort_values(['inter_id', 'nds_id'])

# 将nds_id转回字符串类型
df_complete['nds_id'] = df_complete['nds_id'].astype(str)

# 保存完整的数据
df_complete.to_csv('data/complete_16h_data.txt', sep='\t', index=False)

# 打印统计信息
print(f"原始16时数据条数: {len(df_16)}")
print(f"补充的数据条数: {len(supplemental_data)}")
print(f"完整数据总条数: {len(df_complete)}")