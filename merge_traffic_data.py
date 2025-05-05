import pandas as pd
import numpy as np
import json

# 读取数据文件，指定nds_id和next_nds_id为字符串类型
inferred_df = pd.read_csv('data/inferred_traffic_light_info.txt', sep='\t', 
                         dtype={'nds_id': str, 'next_nds_id': str})
reconstructed_df = pd.read_csv('data/reconstructed_method1.txt', sep='\t',
                              dtype={'nds_id': str, 'next_nds_id': str})

# 重命名列以匹配
reconstructed_df = reconstructed_df.rename(columns={
    'cycle_time': 'cycle_length',
    'cycle_start': 'inferred_green_start'
})

def compare_data_sources(inferred_df, reconstructed_df):
    """比较两个数据源的差异，只比较覆盖率大于0.8的记录"""
    # 找到两个数据源中都存在的记录
    common_records = []
    for _, row in inferred_df.iterrows():
        # 只处理覆盖率大于0.8的记录
        if row['coverage_rate'] > 0.8:
            reconstructed_row = reconstructed_df[
                (reconstructed_df['nds_id'] == row['nds_id']) & 
                (reconstructed_df['next_nds_id'] == row['next_nds_id']) & 
                (reconstructed_df['dir'] == row['dir'])
            ]
            if not reconstructed_row.empty:
                common_records.append({
                    'nds_id': row['nds_id'],
                    'next_nds_id': row['next_nds_id'],
                    'dir': int(row['dir']),
                    'inferred_green_start': float(row['inferred_green_start']),
                    'reconstructed_green_start': float(reconstructed_row.iloc[0]['inferred_green_start']),
                })
    
    # 转换为DataFrame
    comparison_df = pd.DataFrame(common_records)
    
    # 计算差异
    comparison_df['green_start_diff'] = comparison_df['reconstructed_green_start'] - comparison_df['inferred_green_start']
    
    # 计算绝对差异
    comparison_df['green_start_abs_diff'] = np.abs(comparison_df['green_start_diff'])
    
    return comparison_df

# 比较数据源
comparison_df = compare_data_sources(inferred_df, reconstructed_df)

# 打印比较结果
print("\n数据源比较结果（仅覆盖率>0.8的记录）：")
print(f"共有 {len(comparison_df)} 条记录在两个数据源中都存在")

print("\n绿灯开始时间差异统计：")
print(f"平均差异: {comparison_df['green_start_diff'].mean():.2f}")
print(f"平均绝对差异: {comparison_df['green_start_abs_diff'].mean():.2f}")
print(f"最大绝对差异: {comparison_df['green_start_abs_diff'].max():.2f}")
print(f"差异标准差: {comparison_df['green_start_diff'].std():.2f}")

# 输出最大绝对差异的记录
max_diff_idx = comparison_df['green_start_abs_diff'].idxmax()
max_diff_record = comparison_df.loc[max_diff_idx]
print("\n最大绝对差异的记录详情：")
print(f"nds_id: {max_diff_record['nds_id']}")
print(f"next_nds_id: {max_diff_record['next_nds_id']}")
print(f"方向: {max_diff_record['dir']}")
print(f"推断绿灯开始时间: {max_diff_record['inferred_green_start']}")
print(f"重构绿灯开始时间: {max_diff_record['reconstructed_green_start']}")

# 创建合并后的数据字典
merged_data = {}

# 统计变量
total_records = len(inferred_df)
replaced_records = 0
low_coverage_records = 0
single_vehicle_records = 0
found_in_reconstructed = 0

# 处理inferred数据
for _, row in inferred_df.iterrows():
    key = f"{row['nds_id']}_{row['next_nds_id']}_{row['dir']}"
    
    if row['coverage_rate'] < 0.8 or row['covered_vehicles'] == 1:
        if row['coverage_rate'] < 0.8:
            low_coverage_records += 1
        if row['covered_vehicles'] == 1:
            single_vehicle_records += 1
            
        # 查找reconstructed中对应的数据
        reconstructed_row = reconstructed_df[
            (reconstructed_df['nds_id'] == row['nds_id']) & 
            (reconstructed_df['next_nds_id'] == row['next_nds_id']) & 
            (reconstructed_df['dir'] == row['dir'])
        ]
        
        if not reconstructed_row.empty:
            found_in_reconstructed += 1
            replaced_records += 1
            # 使用reconstructed的数据
            merged_data[key] = {
                'nds_id': str(row['nds_id']),
                'next_nds_id': str(row['next_nds_id']),
                'dir': int(row['dir']),
                'cycle_length': float(reconstructed_row.iloc[0]['cycle_length']),
                'green_start': float(reconstructed_row.iloc[0]['inferred_green_start']),
                'green_time': float(reconstructed_row.iloc[0]['green_time']),
                'vehicle_count': int(row['vehicle_count']),
                'covered_vehicles': int(row['covered_vehicles']),
                'coverage_rate': float(row['coverage_rate']),
                'data_source': 'method1'
            }
        else:
            # 如果没有找到对应的reconstructed数据，保留inferred数据
            merged_data[key] = {
                'nds_id': str(row['nds_id']),
                'next_nds_id': str(row['next_nds_id']),
                'dir': int(row['dir']),
                'cycle_length': float(row['cycle_length']),
                'green_start': float(row['inferred_green_start']),
                'green_time': float(row['green_time']),
                'vehicle_count': int(row['vehicle_count']),
                'covered_vehicles': int(row['covered_vehicles']),
                'coverage_rate': float(row['coverage_rate']),
                'data_source': 'method2'
            }
    else:
        # 使用inferred数据
        merged_data[key] = {
            'nds_id': str(row['nds_id']),
            'next_nds_id': str(row['next_nds_id']),
            'dir': int(row['dir']),
            'cycle_length': float(row['cycle_length']),
            'green_start': float(row['inferred_green_start']),
            'green_time': float(row['green_time']),
            'vehicle_count': int(row['vehicle_count']),
            'covered_vehicles': int(row['covered_vehicles']),
            'coverage_rate': float(row['coverage_rate']),
            'data_source': 'method2'
        }

# 保存为JSON文件
with open('data/merged_traffic_light_info.json', 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

# 打印统计信息
print("\n数据合并统计信息：")
print(f"总记录数: {total_records}")
print(f"低覆盖率记录数（<0.8）: {low_coverage_records} ({low_coverage_records/total_records*100:.2f}%)")
print(f"单车辆记录数: {single_vehicle_records} ({single_vehicle_records/total_records*100:.2f}%)")
print(f"需要替换的记录数: {low_coverage_records + single_vehicle_records} ({(low_coverage_records + single_vehicle_records)/total_records*100:.2f}%)")
print(f"在reconstructed中找到的记录数: {found_in_reconstructed} ({found_in_reconstructed/total_records*100:.2f}%)")
print(f"实际替换的记录数: {replaced_records} ({replaced_records/total_records*100:.2f}%)")

print("数据合并完成！") 