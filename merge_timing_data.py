import pandas as pd

# 读取数据
df = pd.read_csv('data/complete_16h_data.txt', sep='\t')

# 定义需要分组的列
group_columns = ['inter_id', 'f_rid', 'nds_id', 'node_id', 'dir', 'way', 'hour']

# 定义需要计算平均值的列
agg_columns = ['red_time', 'green_time', 'cycle_time']

# 按指定列分组并计算平均值
df_merged = df.groupby(group_columns)[agg_columns].mean().reset_index()

# 保留其他列的第一个值
other_columns = [col for col in df.columns if col not in group_columns + agg_columns]
df_other = df.groupby(group_columns)[other_columns].first().reset_index()

# 合并结果
df_final = pd.merge(df_merged, df_other, on=group_columns)

# 保存结果
df_final.to_csv('merged_16h_timing_data.txt', sep='\t', index=False)

# 打印统计信息
print(f"原始数据条数: {len(df)}")
print(f"合并后数据条数: {len(df_final)}")
print(f"合并减少的数据条数: {len(df) - len(df_final)}") 