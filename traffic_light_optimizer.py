import json
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Phase:
    inter_id: str
    nds_id: str
    next_nds_id: str
    dir: int
    cycle_length: float
    green_start: float
    green_time: float
    vehicle_count: int
    covered_vehicles: int
    coverage_rate: float
    way: int
    data_source: str

class TrafficLightOptimizer:
    def __init__(self, phases: List[Phase]):
        self.phases = phases

         # 如果周期长度不同取最长
        self.cycle_length = max(phase.cycle_length for phase in phases)
        # 并修改所有相位的周期长度
        for phase in self.phases:
            phase.cycle_length = self.cycle_length
        
        # 定义二维冲突关系 (way, dir) -> Set[(way, dir)]
        self.conflicting_combinations = {
            # way 0 的冲突关系
            (0, 0): {  # 直行
                (0, 1), (0, 7),  # 同向的左转、掉头
                (1, 0), (1, 1),  (1, 7)  # 正交道路的所有方向
            },
            (0, 1): {  # 左转
                (0, 0), (0, 7),  # 同向的直行、掉头
                (1, 0), (1, 1),  (1, 7)  # 正交道路的所有方向
            },
            (0, 2): {  # 右转   
            },
            (0, 7): {  # 掉头
                (0, 0), (0, 1),  # 同向的直行、左转
                (1, 0), (1, 1),  (1, 7)  # 正交道路的直行、左转、右转、掉头
            },
            
            # way 1 的冲突关系
            (1, 0): {  # 直行
                (1, 1), (1, 7),  # 同向的左转、掉头
                (0, 0), (0, 1),  (0, 7)  # 正交道路的所有方向
            },
            (1, 1): {  # 左转
                (1, 0), (1, 7),  # 同向的直行、掉头
                (0, 0), (0, 1),  (0, 7)  # 正交道路的所有方向
            },
            (1, 2): {  # 右转
            },
            (1, 7): {  # 掉头
                (1, 0), (1, 1),  # 同向的直行、左转
                (0, 0), (0, 1), (0, 7)  # 正交道路的直行、左转、右转、掉头
            }
        }

    def detect_conflicts(self) -> List[Tuple[Phase, Phase]]:
        """检测相位冲突"""
        conflicts = []
        for i, phase1 in enumerate(self.phases):
            for phase2 in self.phases[i+1:]:
                if self._is_conflicting(phase1, phase2):
                    conflicts.append((phase1, phase2))
        return conflicts

    def _is_conflicting(self, phase1: Phase, phase2: Phase) -> bool:
        """判断两个相位是否冲突"""
        # 获取两个相位的way和dir组合
        combo1 = (phase1.way, phase1.dir)
        combo2 = (phase2.way, phase2.dir)
        
        # 检查是否存在冲突关系
        if combo1 in self.conflicting_combinations and combo2 in self.conflicting_combinations[combo1]:
            # 计算两个相位的绿灯结束时间
            end1 = phase1.green_start + phase1.green_time
            end2 = phase2.green_start + phase2.green_time

            # 考虑周期循环
            if end1 > self.cycle_length:
                end1 -= self.cycle_length
            if end2 > self.cycle_length:
                end2 -= self.cycle_length

            # 检查时间重叠
            if phase1.green_start <= phase2.green_start < end1:
                return True
            if phase2.green_start <= phase1.green_start < end2:
                return True
        return False

    def optimize_phases(self) -> List[Phase]:
        """优化相位时间安排"""
        # 按方向和way分组
        phases_by_dir_way = {}
        for phase in self.phases:
            key = (phase.dir, phase.way)
            if key not in phases_by_dir_way:
                phases_by_dir_way[key] = []
            phases_by_dir_way[key].append(phase)

        # 合并相同方向的相位
        optimized_phases = []
        for dir_way_phases in phases_by_dir_way.values():
            if len(dir_way_phases) > 1:
                # 合并相同方向的相位
                merged_phases = self._merge_phases(dir_way_phases)
                optimized_phases.extend(merged_phases)  # 使用extend而不是append
            else:
                optimized_phases.append(dir_way_phases[0])

        # 重新安排相位时间
        self._reschedule_phases(optimized_phases)
        return optimized_phases

    def _merge_phases(self, phases: List[Phase]) -> List[Phase]:
        """合并相同方向的相位，保留所有数据并同步配时"""
        # 使用交通流量最大的相位作为基础
        base_phase = max(phases, key=lambda x: x.vehicle_count)

        for phase in phases:
            phase.green_start = base_phase.green_start
            phase.green_time = base_phase.green_time

        return phases

    def _reschedule_phases(self, phases: List[Phase]):
        """重新安排相位时间，以way0直行为基准相位，同时处理相同way和dir的相位"""
        # 按way分组，不处理右转相位，按照dir排序
        phases_by_way = {}
        for phase in phases:
            if phase.way not in phases_by_way:
                phases_by_way[phase.way] = {}
            if phase.dir not in phases_by_way[phase.way] and phase.dir != 2:
                phases_by_way[phase.way][phase.dir] = []
            if phase.dir != 2:
                phases_by_way[phase.way][phase.dir].append(phase)
        
        # 找到基准相位（way0的直行相位）
        base_phase = None
        for phase in phases:
            if phase.way == 0 and phase.dir == 0:
                base_phase = phase
                break
        
        # 定义相位顺序：直行(0)、左转(1)、掉头(7)
        dir_order = {0: 0, 1: 1, 7: 2}

        if base_phase is None:
            # 如果没有找到way0直行相位，按照相位顺序寻找
            for dir in sorted(phases_by_way.get(0, {}).keys(), key=lambda x: dir_order.get(x, 3)):
                base_phase = max(phases_by_way[0][dir], key=lambda x: x.vehicle_count)
                break
        if base_phase is None:
            for dir in sorted(phases_by_way.get(1, {}).keys(), key=lambda x: dir_order.get(x, 3)):
                base_phase = max(phases_by_way[1][dir], key=lambda x: x.vehicle_count)
                break

        if base_phase is None:
            raise ValueError("没有找到基准相位，请检查")

        # 根据基准相位调整其他相位的绿灯开始时间
        current_time = base_phase.green_start
        
        # 处理之前先计算相位总时间是否超过一个周期
        total_time = 0
        for phase_by_way in phases_by_way.values():
            for dir_phases in phase_by_way.values():
                total_time += max(dir_phases, key=lambda x: x.green_time).green_time + 1
        if total_time > self.cycle_length:
            # 如果总时间超过一个周期，则需要调整相位时间
            # 先尝试将左转和掉头合并
            if 1 in phases_by_way and 7 in phases_by_way[1]:
                if 1 in phases_by_way[1]:
                    phases_by_way[1][1].extend(phases_by_way[1][7])
                else:
                    # 如果没有左转相位，则将掉头相位作为左转相位
                    phases_by_way[1][1] = phases_by_way[1][7]
                # 删除掉头相位
                del phases_by_way[1][7]
            if 0 in phases_by_way and 7 in phases_by_way[0]:
                if 1 in phases_by_way[0]:
                    phases_by_way[0][1].extend(phases_by_way[0][7])
                else:
                    # 如果没有左转相位，则将掉头相位作为左转相位
                    phases_by_way[0][1] = phases_by_way[0][7]
                # 删除掉头相位
                del phases_by_way[0][7]
            # 重新计算总时间
            total_time = 0
            for phase_by_way in phases_by_way.values():
                for dir_phases in phase_by_way.values():
                    total_time += max(dir_phases, key=lambda x: x.green_time).green_time + 1
            if total_time > self.cycle_length:
                # 如果总时间仍然超过一个周期，则需要调整相位时间
                # 将左转和直行进一步合并
                if 1 in phases_by_way and 1 in phases_by_way[1]:
                    if 0 in phases_by_way[1]:
                        phases_by_way[1][0].extend(phases_by_way[1][1])
                    else:
                        # 如果没有直行相位，则将左转相位作为直行相位
                        phases_by_way[1][0] = phases_by_way[1][1]
                    # 删除左转相位
                    del phases_by_way[1][1]
                if 0 in phases_by_way and 1 in phases_by_way[0]:
                    if 0 in phases_by_way[0]:
                        phases_by_way[0][0].extend(phases_by_way[0][1])
                    else:
                        # 如果没有直行相位，则将左转相位作为直行相位
                        phases_by_way[0][0] = phases_by_way[0][1]
                    # 删除左转相位
                    del phases_by_way[0][1]
                # 重新计算总时间
                total_time = 0
                for phase_by_way in phases_by_way.values():
                    for dir_phases in phase_by_way.values():
                        total_time += max(dir_phases, key=lambda x: x.green_time).green_time + 1
            if total_time > self.cycle_length:
                # 输出详细信息
                phases_info = {}
                for way, dir_phases in phases_by_way.items():
                    phases_info[way] = {}
                    for dir, phase_list in dir_phases.items():
                        phases_info[way][dir] = [p.__dict__ for p in phase_list]
                # 输出到特定json文件
                with open('infos.json', 'w') as f:
                    json.dump(phases_info, f, indent=2)
                raise ValueError("合并后，总时间仍然超过一个周期，请检查")


        # 处理way0的其他相位
        for dir in sorted(phases_by_way.get(0, {}).keys(), key=lambda x: dir_order.get(x, 3)):
            # 同时处理相同way和dir的所有相位
            for phase in phases_by_way[0][dir]:
                phase.green_start = current_time % self.cycle_length
            current_time += max(phases_by_way[0][dir], key=lambda x: x.green_time).green_time + 1  # 绿灯时间 + 黄灯时间
            # 如果配时超过一个周期，报错
            if current_time - base_phase.green_start > self.cycle_length:
                print(current_time, base_phase.green_start, self.cycle_length)
                # 将phases_by_way转换为可序列化的格式
                phases_info = {}
                for way, dir_phases in phases_by_way.items():
                    phases_info[way] = {}
                    for dir, phase_list in dir_phases.items():
                        phases_info[way][dir] = [p.__dict__ for p in phase_list]
                with open('infos.json', 'w') as f:
                    json.dump(phases_info, f, indent=2)
                raise ValueError(f"相位{phase.inter_id}的配时超过一个周期，请检查")
        

        # 处理way1的相位
        for dir in sorted(phases_by_way.get(1, {}).keys(), key=lambda x: dir_order.get(x, 3)):
            # 同时处理相同way和dir的所有相位
            for phase in phases_by_way[1][dir]:
                phase.green_start = current_time % self.cycle_length
            current_time += max(phases_by_way[1][dir], key=lambda x: x.green_time).green_time + 1  # 绿灯时间 + 黄灯时间
            # 如果配时超过一个周期，报错
            if current_time - base_phase.green_start > self.cycle_length:
                print(current_time, base_phase.green_start, self.cycle_length)
                # 将phases_by_way转换为可序列化的格式
                phases_info = {}
                for way, dir_phases in phases_by_way.items():
                    phases_info[way] = {}
                    for dir, phase_list in dir_phases.items():
                        phases_info[way][dir] = [p.__dict__ for p in phase_list]
                with open('infos.json', 'w') as f:
                    json.dump(phases_info, f, indent=2)
                raise ValueError(f"相位{phase.inter_id}的配时超过一个周期，请检查")

def load_phases_from_json(file_path: str) -> Dict[str, List[Phase]]:
    """从JSON文件加载相位数据
    Returns:
        Dict[str, List[Phase]]: 路口ID到相位列表的映射
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    phases_by_intersection = {}
    for inter_id, phase_list in data.items():
        phases = []
        for phase_data in phase_list:
            phase = Phase(**phase_data)
            phases.append(phase)
        phases_by_intersection[inter_id] = phases
    
    return phases_by_intersection

def save_phases_to_json(phases_by_intersection: Dict[str, List[Phase]], file_path: str):
    """将优化后的相位数据保存到JSON文件"""
    data = {}
    for inter_id, phases in phases_by_intersection.items():
        data[inter_id] = [phase.__dict__ for phase in phases]
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    # 加载数据
    phases_by_intersection = load_phases_from_json('data/grouped_traffic_light_info.json')
    
    # 处理每个路口
    for inter_id, phases in phases_by_intersection.items():
        print(f"处理路口 {inter_id}")
        # 创建优化器
        optimizer = TrafficLightOptimizer(phases)
        
        # 检测冲突
        conflicts = optimizer.detect_conflicts()
        print(f"检测到 {len(conflicts)} 个相位冲突")
        
        if len(conflicts) > 0:
            # 优化相位
            optimized_phases = optimizer.optimize_phases()
            # 更新该路口的相位数据
            phases_by_intersection[inter_id] = optimized_phases
    
    # 保存优化后的数据
    save_phases_to_json(phases_by_intersection, 'data/optimized_traffic_light_info.json')
    print("相位优化完成，结果已保存到 optimized_traffic_light_info.json")

if __name__ == "__main__":
    main() 