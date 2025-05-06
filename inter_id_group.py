import json

# 读取原始数据
with open('data/merged_traffic_light_info.json', 'r') as f:
    data = json.load(f)

# 创建新的数据结构
grouped_data = {}

# 按照inter_id进行分组
for key, value in data.items():
    inter_id = value['inter_id']
    if inter_id not in grouped_data:
        grouped_data[inter_id] = []
    grouped_data[inter_id].append(value)

# 将重组后的数据写入新文件
with open('data/grouped_traffic_light_info.json', 'w') as f:
    json.dump(grouped_data, f, indent=2) 