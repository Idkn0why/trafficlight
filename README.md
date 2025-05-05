# 路口转向关系分析

这个项目用于分析轨迹数据中的路口转向关系，计算路口之间的平均转向角度和标准差。

## 项目结构

```
.
├── README.md
├── process_road_connections.py
└── data/                    # 数据文件夹（不包含在git中）
    ├── trajectory_20250329.txt
    └── intersection_turns.txt
```

## 数据说明

- `trajectory_20250329.txt`: 原始轨迹数据文件
- `intersection_turns.txt`: 处理后的路口转向关系数据

## 使用方法

1. 将轨迹数据文件放在 `data` 文件夹下
2. 运行处理脚本：
```bash
python process_road_connections.py
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