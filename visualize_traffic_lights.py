import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from traffic_light_optimizer import Phase, TrafficLightOptimizer

def load_phases(file_path: str) -> Dict[str, List[Phase]]:
    """加载相位数据"""
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

def plot_phases(phases: List[Phase], inter_id: str):
    """绘制相位时间轴"""
    # 设置颜色映射
    dir_colors = {
        0: 'green',    # 直行
        1: 'blue',     # 左转
        2: 'orange',   # 右转
        7: 'purple'    # 掉头
    }
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # 为每个way和dir创建不同的y轴位置
    # way 0: 位置 1-4
    # way 1: 位置 5-8
    way_dir_positions = {
        0: {0: 1, 1: 2, 2: 3, 7: 4},  # way 0
        1: {0: 5, 1: 6, 2: 7, 7: 8}   # way 1
    }
    
    # 绘制每个相位
    for phase in phases:
        y_pos = way_dir_positions[phase.way][phase.dir]
        color = dir_colors.get(phase.dir, 'gray')
        
        # 计算相位结束时间
        end_time = phase.green_start + phase.green_time
        cycle_length = phase.cycle_length
        
        if end_time > cycle_length:
            # 如果相位跨越周期，分成两部分绘制
            # 第一部分：从开始到周期结束
            first_part_time = cycle_length - phase.green_start
            ax.barh(y_pos, first_part_time, 
                    left=phase.green_start,
                    height=0.5,
                    color=color,
                    alpha=0.7)
            
            # 第二部分：从周期开始到结束
            second_part_time = end_time - cycle_length
            ax.barh(y_pos, second_part_time, 
                    left=0,
                    height=0.5,
                    color=color,
                    alpha=0.7)
            
            # 添加标签（在两部分中间）
            label = f"Dir:{phase.dir}\nTime:{phase.green_time:.1f}s"
            ax.text(10, y_pos,
                    label,
                    ha='center', va='center',
                    color='black', fontweight='bold')
        else:
            # 如果相位在周期内，正常绘制
            ax.barh(y_pos, phase.green_time, 
                    left=phase.green_start,
                    height=0.5,
                    color=color,
                    alpha=0.7)
            
            # 添加标签
            label = f"Dir:{phase.dir}\nTime:{phase.green_time:.1f}s"
            ax.text(phase.green_start + phase.green_time/2, y_pos,
                    label,
                    ha='center', va='center',
                    color='black', fontweight='bold')
    
    # 设置图形属性
    ax.set_yticks([1, 2, 3, 4, 5, 6, 7, 8])
    ax.set_yticklabels([
        'Way0-Straight', 'Way0-Left', 'Way0-Right', 'Way0-U-turn',
        'Way1-Straight', 'Way1-Left', 'Way1-Right', 'Way1-U-turn'
    ])
    ax.set_xlabel('Time (s)')
    ax.set_title(f'Traffic Light Phases - Intersection {inter_id}')
    
    # 添加图例
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7)
                      for color in dir_colors.values()]
    ax.legend(legend_elements, ['Straight', 'Left Turn', 'Right Turn', 'U-turn'],
              loc='upper right')
    
    # 设置x轴范围
    cycle_length = phases[0].cycle_length
    ax.set_xlim(0, cycle_length)
    
    # 添加网格
    ax.grid(True, alpha=0.3)
    
    # 调整图形大小以适应所有标签
    plt.tight_layout()
    
    return fig

def visualize_conflicts(phases: List[Phase], inter_id: str):
    """可视化相位冲突"""
    # 创建优化器实例来检测冲突
    optimizer = TrafficLightOptimizer(phases)
    conflicts = optimizer.detect_conflicts()
    
    # 绘制相位时间轴
    fig = plot_phases(phases, inter_id)
    ax = fig.axes[0]
    
    # 使用不同的颜色来区分不同的冲突
    conflict_colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ff99ff', '#99ffff']
    
    # 记录已经标记的冲突区域
    marked_conflicts = set()
    
    # 标记冲突
    for i, (phase1, phase2) in enumerate(conflicts):
        # 计算冲突时间范围
        start1 = phase1.green_start
        end1 = start1 + phase1.green_time
        start2 = phase2.green_start
        end2 = start2 + phase2.green_time
        
        # 找出重叠的时间范围
        conflict_start = max(start1, start2)
        conflict_end = min(end1, end2)
        
        # 检查是否已经标记过这个冲突区域
        conflict_key = (conflict_start, conflict_end)
        if conflict_key in marked_conflicts:
            continue
        marked_conflicts.add(conflict_key)
        
        # 在冲突区域添加半透明阴影
        color = conflict_colors[i % len(conflict_colors)]
        ax.axvspan(conflict_start, conflict_end,
                  ymin=0, ymax=1,
                  color=color, alpha=0.3)
        
        # 添加冲突标记
        ax.text((conflict_start + conflict_end)/2, 0.5,
                f"Conflict {i+1}: {phase1.dir} vs {phase2.dir}",
                ha='center', va='center',
                color='black', fontweight='bold',
                transform=ax.transAxes)
    
    return fig

def main():
    # 加载数据
    phases_by_intersection = load_phases('data/optimized_traffic_light_info.json')
    
    # 为每个路口创建可视化
    for inter_id, phases in phases_by_intersection.items():
        print(f"处理路口 {inter_id}")
        
        # 创建冲突可视化
        fig = visualize_conflicts(phases, inter_id)
        
        # 保存图形
        fig.savefig(f'visualizations/{inter_id}_phases.png')
        plt.close(fig)

if __name__ == "__main__":
    main() 