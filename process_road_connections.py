import pandas as pd
import numpy as np
import json
from collections import defaultdict

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

# 用于存储结果的字典
result_dict = defaultdict(lambda: {'exit_turns': [], 'count': 0})

# 定义数据类型
dtype_dict = {
    'nds_id': 'str',
    'next_nds_id': 'str',
    'exit_turn': 'float64'
}

# 分块读取数据
chunk_size = 1000000  # 每次读取100万行
total_rows = 0
for chunk in pd.read_csv('data/trajectory_20250329.txt', 
                        sep='\t', 
                        chunksize=chunk_size,
                        dtype=dtype_dict,
                        low_memory=False):
    total_rows += len(chunk)
    print(f"处理第 {total_rows} 行")
    # 对每个chunk进行处理
    for _, row in chunk.iterrows():
        # 去除next_nds_id为0的行
        if row['next_nds_id'] != '0':
            key = (row['nds_id'], row['next_nds_id'])
            result_dict[key]['exit_turns'].append(float(row['exit_turn']))  # 确保转换为float
            result_dict[key]['count'] += 1

# 将结果转换为字典格式
results = {}
for (from_road, next_road), data in result_dict.items():
    exit_turns = np.array(data['exit_turns'])  # 转换为numpy数组
    avg_turn = np.mean(exit_turns)
    turn_std = np.std(exit_turns, ddof=1)  # 使用无偏估计
    dir_value = map_exit_turn_to_dir(avg_turn)
    
    # 创建路口连接关系
    connection = {
        'from_road': from_road,
        'next_road': next_road,
        'avg_turn_angle': float(avg_turn),  # 确保是Python原生类型
        'turn_count': int(data['count']),
        'dir': int(dir_value) if dir_value is not None else None
    }
    
    # 如果有多个样本，添加标准差和极值
    if len(exit_turns) > 1:
        connection.update({
            'turn_std': float(turn_std),
            'min_turn': float(np.min(exit_turns)),
            'max_turn': float(np.max(exit_turns))
        })
    
    # 使用from_road作为主键
    if from_road not in results:
        results[from_road] = []
    results[from_road].append(connection)

# 保存为JSON文件
with open('data/intersection_turns.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 打印处理完成的信息
print(f"\n处理完成，共处理了 {len(results)} 个路口的连接关系")
print(f"结果已保存到 data/intersection_turns.json")

