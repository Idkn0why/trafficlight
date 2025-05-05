# 方法1：
# 1. 筛选出16:00-17:00之间的数据
# 2. 筛去等待时间小于1或大于300的数据
# 3. 筛去next_nds_id为0的数据
# 4. 筛去stop_time等于travel_time的数据

# 方法2：
# 1. 筛选出16:00-17:00之间的数据
# 2. 筛去next_nds_id为0的数据
# 3. 筛去stop_time等于travel_time的数据

import pandas as pd
from datetime import datetime, timedelta
import os

def parse_time(time_str):
    """将UFC格式的时间字符串转换为datetime对象"""
    return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')

def is_time_in_range(enter_time, travel_time):
    """检查离开时间是否严格在16:00-17:00之间"""
    end_time = enter_time + timedelta(seconds=travel_time)
    # 检查是否在16:00:00到17:00:00之间
    return (end_time.hour == 16 and end_time.minute >= 0 and end_time.second >= 0) or \
           (end_time.hour == 17 and end_time.minute == 0 and end_time.second == 0)

# 读取文件
chunk_size = 100000  # 每次读取的行数
output_file = 'data/filtered_trajectory_16_17_method1.txt'
#output_file = 'data/filtered_trajectory_16_17.txt'

# 如果输出文件已存在，先删除
if os.path.exists(output_file):
    os.remove(output_file)

# 定义列名
column_names = ['adcode', 'nds_id', 'enter_time', 'exit_turn', 'travel_time', 'stop_time', 
                'link_length', 'road_class', 'cover_percent', 'no_stop_speed', 'avg_speed',
                'traffic_kmph', 'stop_length', 'next_nds_id', 'ds_code', 'user_id', 'device_id',
                'start_time', 'intersection_time', 'new_route_flag', 'offset_info', 'stop_info',
                'match_points_info', 'pre_nds_id', 'link_width', 'formway', 'ownership_type',
                'navi_info', 'flag', 'province', 'ds']

# 先写入表头
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\t'.join(column_names) + '\n')

# 使用pandas的chunk读取大文件
for chunk in pd.read_csv('data/trajectory_20250329.txt', 
                        sep='\t',  # 使用制表符分隔
                        chunksize=chunk_size,
                        header=0,  # 第一行是表头
                        names=column_names,
                        dtype={'enter_time': 'int64'},  # 指定enter_time为整数类型
                        low_memory=False):  # 避免混合类型警告
    
    # 转换时间格式 - 将UTC时间戳转换为datetime
    chunk['enter_time'] = pd.to_datetime(chunk['enter_time'], unit='s', utc=True).dt.tz_convert('Asia/Shanghai')
    
    # 筛选条件：
    # 1. next_nds_id不为空
    # 2. 离开时间严格在16:00:00到17:00:00之间
    # 3. 通过时间不能等于等待时间
    # 5. 筛去等待时间小于1或大于600的数据
    filtered_chunk = chunk[
        (chunk['next_nds_id']!=0) & (chunk['stop_time'] != chunk['travel_time']) &
        chunk.apply(lambda x: is_time_in_range(x['enter_time'], x['travel_time']), axis=1) &
        (chunk['stop_time'] > 1) & (chunk['stop_time'] < 600)
    ]
    
    # 将筛选后的数据追加到输出文件
    filtered_chunk.to_csv(output_file, 
                         mode='a', 
                         header=False, 
                         index=False, 
                         sep='\t')
    
    print(f"已处理 {len(chunk)} 行数据，找到 {len(filtered_chunk)} 条符合条件的记录")

print("数据处理完成！") 