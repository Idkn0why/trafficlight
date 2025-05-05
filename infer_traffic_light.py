import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

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

def analyze_light_cycle(trajectory_data, cycle_data):
    """
    分析轨迹数据在信号周期内的分布
    trajectory_data: 处理后的轨迹数据
    cycle_data: 信号灯周期数据
    """
    # 将离开时间转换为秒数（相对于周期）
    def get_relative_time(exit_times_str, cycle_length):
        # 使用ISO8601格式解析时间
        exit_times = pd.to_datetime(exit_times_str.split(','), format='ISO8601')
        # 计算相对于周期的秒数
        seconds = [(t.hour * 3600 + t.minute * 60 + t.second) % cycle_length for t in exit_times]
        return seconds
    
    results = []
    for _, row in trajectory_data.iterrows():
        nds_id = row['nds_id']
        next_nds_id = row['next_nds_id']
        dir_val = map_exit_turn_to_dir(row['exit_turn'])
        
        # 获取对应的信号灯周期数据
        cycle_info = cycle_data[(cycle_data['nds_id'] == nds_id) & 
                              (cycle_data['dir'] == dir_val)]
        
        if not cycle_info.empty:
            cycle_length = cycle_info['cycle_time'].iloc[0]
            green_time = cycle_info['green_time'].iloc[0]
            
            # 计算相对时间
            relative_times = get_relative_time(row['exit_time'], cycle_length)
            
            # 在周期内滑动窗口，寻找最佳绿灯开始时间
            best_start = 0
            max_covered = 0
            
            # 以0.1秒为步长滑动窗口
            for start in np.arange(0, cycle_length, 1):
                # 计算窗口结束时间（考虑周期循环）
                end = (start + green_time) % cycle_length
                
                # 计算在窗口内的车辆数量
                if end > start:
                    # 正常情况：窗口不跨越周期
                    covered = sum(1 for t in relative_times if start <= t <= end)
                else:
                    # 窗口跨越周期的情况
                    covered = sum(1 for t in relative_times if t >= start or t <= end)
                
                if covered > max_covered:
                    max_covered = covered
                    best_start = start
            
            # 计算覆盖率
            coverage_rate = max_covered / len(relative_times)
            
            results.append({
                'nds_id': nds_id,
                'next_nds_id': next_nds_id,
                'dir': dir_val,
                'cycle_length': cycle_length,
                'inferred_green_start': best_start,
                'green_time': green_time,
                'vehicle_count': len(relative_times),
                'covered_vehicles': max_covered,
                'coverage_rate': coverage_rate
            })
    
    return pd.DataFrame(results)

def main():
    # 读取已聚类的轨迹数据
    trajectory_data = pd.read_csv('data/clustered_trajectory.txt', sep='\t')
    
    # 读取信号灯周期数据
    cycle_data = pd.read_csv('data/merged_16h_timing_data.txt', sep='\t')
    
    # 分析信号灯信息
    light_analysis = analyze_light_cycle(trajectory_data, cycle_data)
    
    # 保存结果
    light_analysis.to_csv('data/inferred_traffic_light_info.txt', sep='\t', index=False)
    print("信号灯信息推测完成，结果已保存到 data/inferred_traffic_light_info.txt")
    
    # 统计路口数量
    print(f'信号灯数据数量: {len(cycle_data)}')
    print(f"轨迹数据数量: {len(trajectory_data)}")
    print(f"信号灯推测数量: {len(light_analysis)}")

    # 统计覆盖度分析
    print("\n=== 覆盖度统计分析 ===")
    
    # 排除只有1条车辆数据的情况
    valid_analysis = light_analysis[light_analysis['vehicle_count'] > 1]
    print(f"\n有效样本数量: {len(valid_analysis)} (排除{len(light_analysis) - len(valid_analysis)}个只有1条车辆数据的样本)")
    
    # 1. 总体覆盖度统计
    print(f"\n总体覆盖度统计:")
    print(f"平均覆盖度: {valid_analysis['coverage_rate'].mean():.2%}")
    print(f"中位数覆盖度: {valid_analysis['coverage_rate'].median():.2%}")
    print(f"最小覆盖度: {valid_analysis['coverage_rate'].min():.2%}")
    print(f"最大覆盖度: {valid_analysis['coverage_rate'].max():.2%}")
    
    # 3. 覆盖度分布直方图
    plt.figure(figsize=(10, 6))
    plt.hist(valid_analysis['coverage_rate'], bins=20, edgecolor='black')
    plt.title('信号灯推测覆盖度分布 (排除单车辆样本)')
    plt.xlabel('覆盖度')
    plt.ylabel('频数')
    plt.grid(True, alpha=0.3)
    plt.savefig('data/coverage_distribution.png')
    print("\n覆盖度分布直方图已保存到 data/coverage_distribution.png")
    
    # 4. 高覆盖度路口分析
    high_coverage = valid_analysis[valid_analysis['coverage_rate'] > 0.8]
    print(f"\n高覆盖度路口分析 (覆盖度>80%):")
    print(f"高覆盖度路口数量: {len(high_coverage)}")
    print(f"高覆盖度路口占比: {len(high_coverage)/len(valid_analysis):.2%}")
    
    # 5. 低覆盖度路口分析
    low_coverage = valid_analysis[valid_analysis['coverage_rate'] < 0.5]
    print(f"\n低覆盖度路口分析 (覆盖度<50%):")
    print(f"低覆盖度路口数量: {len(low_coverage)}")
    print(f"低覆盖度路口占比: {len(low_coverage)/len(valid_analysis):.2%}")
    
    # 保存详细统计结果
    stats_summary = pd.DataFrame({
        '统计指标': ['有效样本数', '平均覆盖度', '中位数覆盖度', '最小覆盖度', '最大覆盖度', 
                   '高覆盖度路口数', '高覆盖度占比', '低覆盖度路口数', '低覆盖度占比'],
        '数值': [len(valid_analysis),
                valid_analysis['coverage_rate'].mean(), 
                valid_analysis['coverage_rate'].median(),
                valid_analysis['coverage_rate'].min(),
                valid_analysis['coverage_rate'].max(),
                len(high_coverage),
                len(high_coverage)/len(valid_analysis),
                len(low_coverage),
                len(low_coverage)/len(valid_analysis)]
    })
    stats_summary.to_csv('data/coverage_statistics.txt', sep='\t', index=False)
    print("\n详细统计结果已保存到 data/coverage_statistics.txt")

if __name__ == "__main__":
    main() 