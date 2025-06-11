## 项目结构

```
.
├── README.md
├── xxx.py
├── visualizations           # 信号灯可视化文件（不在git）
└── data/                    # 数据文件夹（不包含在git中）
    ├── trajectory_20250329.txt
    └── DATA0329.txt
```

## 数据说明

- `trajectory_20250329.txt`: 原始轨迹数据文件
- `DATA0329.txt`: 原始信号灯数据文件

## 使用方法

1. 将数据文件放在 `data` 文件夹下
2. 信号灯数据分析：
```bash
python filter_data_by_link.py
python analyze_traffic_data.py
```
选取16h数据并补全
```bash
python complete_16h_data.py
python merge_timing_data.py
```
3. 轨迹数据处理：
注意方法1和方法2在filter_trajectory_by_time.py有所不同，需要更改条件
```bash
python filter_trajectory_by_time.py
python filter_trajectory_by_link.py
python filter_trajectory_by_light.py
```
4. 相位推测方法1：
```bash
python infer_traffic_light_method1.py
python traffic_light_reconstruction.py
```
5. 相位推测方法2：
```bash
python process_trajectory.py
python infer_traffic_light.py
```

6. 合并相位数据：
```bash
python merge_traffic_data.py
python inter_id_group.py
```
8. 信号灯冲突处理：
```bash
python traffic_light_optimizer.py
python visualize_traffic_lights.py
```

9. 推测道路连接关系：
```bash
python process_road_connections.py
```

10. 相位推测方法3：
直接按照简单4相位配时
```bash
python filter_inters_full_info_by_signal_info.py
python visualize_signal_info.py
```



## 输出说明

输出的`intersection_turns.txt`文件包含以下字段：
- from_road: 起始道路ID
- next_road: 目标道路ID
- avg_turn_angle: 平均转向角度
- turn_count: 样本数量
- turn_std: 转向角度标准差（仅当样本数>1时计算）
- dir: 转向方向（0-直行, 1-左转, 2-右转, 7-掉头）
- min_turn: 最小转向角度
- max_turn: 最大转向角度 