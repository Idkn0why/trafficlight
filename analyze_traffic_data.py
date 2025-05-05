import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 读取数据，所有列都以字符串形式读取
df = pd.read_csv('data/filtered_DATA0329.txt', sep='\t', dtype=str)

# 统计总共有多少不同的inter_id
unique_inter_id = df['inter_id'].nunique()
print(f"总共有{unique_inter_id}个不同的inter_id")

# 统计总共有多少不同的nds_id
unique_nds_id = df['nds_id'].nunique()
print(f"总共有{unique_nds_id}个不同的nds_id")

# 统计每个小时的数据数量
hour_counts = df['hour'].value_counts()
# 将小时转换为整数并排序
hour_counts.index = hour_counts.index.astype(int)
hour_counts = hour_counts.sort_index()
most_common_hour = hour_counts.idxmax()
print(f"\n数据最多的hour是: {most_common_hour}点，共有{hour_counts[most_common_hour]}条数据")

# 把16时数据保存到traffic_light_16.txt
df_16 = df[df['hour'] == '16']
df_16.to_csv('traffic_light_16.txt', index=False, sep='\t')

# 统计每个小时对应的不同inter_id数量
unique_inter_per_hour = df.groupby('hour')['inter_id'].nunique()
# 将小时转换为整数并排序
unique_inter_per_hour.index = unique_inter_per_hour.index.astype(int)
unique_inter_per_hour = unique_inter_per_hour.sort_index()
most_inter_hour = unique_inter_per_hour.idxmax()
print(f"\n{most_inter_hour}点对应的不同inter_id数量最多，共有{unique_inter_per_hour[most_inter_hour]}个不同的inter_id")

# 统计每个小时对应的不同nds_id数量
unique_nds_per_hour = df.groupby('hour')['nds_id'].nunique()
# 将小时转换为整数并排序
unique_nds_per_hour.index = unique_nds_per_hour.index.astype(int)
unique_nds_per_hour = unique_nds_per_hour.sort_index()
most_nds_hour = unique_nds_per_hour.idxmax()
print(f"\n{most_nds_hour}点对应的不同nds_id数量最多，共有{unique_nds_per_hour[most_nds_hour]}个不同的nds_id")

# 绘制小时分布图
plt.figure(figsize=(10, 6))
hour_counts.plot(kind='bar')
plt.title('各小时数据分布')
plt.xlabel('小时')
plt.ylabel('数据数量')
plt.tight_layout()
plt.savefig('data/hour_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 绘制每个小时对应的不同inter_id数量图
plt.figure(figsize=(10, 6))
unique_inter_per_hour.plot(kind='bar', color='orange')
plt.title('各小时对应的不同inter_id数量')
plt.xlabel('小时')
plt.ylabel('不同inter_id数量')
plt.tight_layout()
plt.savefig('data/unique_inter_per_hour.png', dpi=300, bbox_inches='tight')
plt.close()

# 绘制每个小时对应的不同nds_id数量图
plt.figure(figsize=(10, 6))
unique_nds_per_hour.plot(kind='bar', color='green')
plt.title('各小时对应的不同nds_id数量')
plt.xlabel('小时')
plt.ylabel('不同nds_id数量')
plt.tight_layout()
plt.savefig('data/unique_nds_per_hour.png', dpi=300, bbox_inches='tight')
plt.close()

# 保存统计结果
with open('data/analysis_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"总共有{unique_inter_id}个不同的inter_id\n")
    f.write(f"数据最多的hour: {most_common_hour}点\n")
    f.write(f"数据数量: {hour_counts[most_common_hour]}条\n\n")
    f.write(f"{most_nds_hour}点对应的不同nds_id数量最多\n")
    f.write(f"不同nds_id数量: {unique_nds_per_hour[most_nds_hour]}个\n\n")
    f.write(f"{most_inter_hour}点对应的不同inter_id数量最多\n")
    f.write(f"不同inter_id数量: {unique_inter_per_hour[most_inter_hour]}个") 