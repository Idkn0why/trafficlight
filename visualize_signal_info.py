import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class SignalLight:
    nds_id: int
    period: float
    green_time: float
    initial_phase: float
    dir: int

def load_signal_info(file_path: str) -> Dict[str, List[SignalLight]]:
    """加载信号灯数据"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    signal_by_intersection = {}
    for item in data:
        inter_id = item['inter_id']
        lights = []
        for signal_data in item['signal_info']:
            light = SignalLight(**signal_data)
            lights.append(light)
        signal_by_intersection[inter_id] = lights
    
    return signal_by_intersection

def plot_signals(signals: List[SignalLight], inter_id: str):
    """绘制信号灯时间轴"""
    if not signals:
        print(f"路口 {inter_id} 没有信号灯数据")
        return None
        
    # 设置颜色映射
    dir_colors = {
        0: 'green',    # 直行
        1: 'blue',     # 左转
        2: 'orange',   # 右转
        7: 'purple'    # 掉头
    }
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # 按方向分组信号灯
    dir_groups = {0: [], 1: [], 2: [], 7: []}
    for signal in signals:
        dir_groups[signal.dir].append(signal)
    
    # 为每个方向创建不同的y轴位置
    y_positions = {}
    current_pos = 1
    for dir_value in [0, 1, 2, 7]:
        if dir_groups[dir_value]:
            for signal in dir_groups[dir_value]:
                y_positions[signal.nds_id] = current_pos
                current_pos += 1
            current_pos += 1  # 添加一个空行分隔不同方向
    
    # 绘制每个信号灯
    for signal in signals:
        y_pos = y_positions[signal.nds_id]
        color = dir_colors.get(signal.dir, 'gray')
        
        # 计算相位结束时间
        signal.initial_phase = signal.period - signal.initial_phase
        end_time = signal.initial_phase + signal.green_time
        cycle_length = signal.period
        
        if end_time > cycle_length:
            # 如果相位跨越周期，分成两部分绘制
            # 第一部分：从开始到周期结束
            first_part_time = cycle_length - signal.initial_phase
            ax.barh(y_pos, first_part_time, 
                    left=signal.initial_phase,
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
            label = f"Dir:{signal.dir}\nTime:{signal.green_time:.1f}s"
            ax.text(10, y_pos,
                    label,
                    ha='center', va='center',
                    color='black', fontweight='bold')
        else:
            # 如果相位在周期内，正常绘制
            ax.barh(y_pos, signal.green_time, 
                    left=signal.initial_phase,
                    height=0.5,
                    color=color,
                    alpha=0.7)
            
            # 添加标签
            label = f"Dir:{signal.dir}\nTime:{signal.green_time:.1f}s"
            ax.text(signal.initial_phase + signal.green_time/2, y_pos,
                    label,
                    ha='center', va='center',
                    color='black', fontweight='bold')
    
    # 设置图形属性
    ax.set_yticks(list(y_positions.values()))
    ax.set_yticklabels([f'Signal {nds_id}' for nds_id in y_positions.keys()])
    ax.set_xlabel('Time (s)')
    ax.set_title(f'Traffic Light Signals - Intersection {inter_id}')
    
    # 设置x轴范围
    cycle_length = signals[0].period
    ax.set_xlim(0, cycle_length)
    
    # 添加网格
    ax.grid(True, alpha=0.3)
    
    # 添加图例
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.7)
                      for color in dir_colors.values()]
    ax.legend(legend_elements, ['Straight', 'Left Turn', 'Right Turn', 'U-turn'],
              loc='upper right')
    
    # 调整图形大小以适应所有标签
    plt.tight_layout()
    
    return fig

def visualize_conflicts(signals: List[SignalLight], inter_id: str):
    """可视化信号灯冲突"""
    # 绘制信号灯时间轴
    fig = plot_signals(signals, inter_id)
    if fig is None:
        return None
        
    ax = fig.axes[0]
    
    # 使用不同的颜色来区分不同的冲突
    conflict_colors = ['#ff9999', '#99ff99', '#9999ff', '#ffff99', '#ff99ff', '#99ffff']
    
    # 记录已经标记的冲突区域
    marked_conflicts = set()
    
    # 检测冲突
    for i, signal1 in enumerate(signals):
        for j, signal2 in enumerate(signals[i+1:], i+1):
            # 计算冲突时间范围
            start1 = signal1.initial_phase
            end1 = start1 + signal1.green_time
            start2 = signal2.initial_phase
            end2 = start2 + signal2.green_time
            
            # 找出重叠的时间范围
            conflict_start = max(start1, start2)
            conflict_end = min(end1, end2)
            
            if conflict_start < conflict_end:
                # 检查是否已经标记过这个冲突区域
                conflict_key = (conflict_start, conflict_end)
                if conflict_key in marked_conflicts:
                    continue
                marked_conflicts.add(conflict_key)
                
                # 在冲突区域添加半透明阴影
                color = conflict_colors[len(marked_conflicts) % len(conflict_colors)]
                ax.axvspan(conflict_start, conflict_end,
                          ymin=0, ymax=1,
                          color=color, alpha=0.3)
                
                # 添加冲突标记
                ax.text((conflict_start + conflict_end)/2, 0.5,
                        f"Conflict {len(marked_conflicts)}: Dir{signal1.dir} vs Dir{signal2.dir}",
                        ha='center', va='center',
                        color='black', fontweight='bold',
                        transform=ax.transAxes)
    
    return fig

def main():
    # 加载数据
    signal_by_intersection = load_signal_info('data/processed_signal_info.json')
    
    # 为每个路口创建可视化
    for inter_id, signals in signal_by_intersection.items():
        print(f"处理路口 {inter_id}")
        
        # 创建冲突可视化
        fig = visualize_conflicts(signals, inter_id)
        if fig is not None:
            # 保存图形
            fig.savefig(f'visualizations/{inter_id}_signals.png')
            plt.close(fig)

if __name__ == "__main__":
    main() 