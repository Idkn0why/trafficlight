import json
from collections import defaultdict

def filter_signal_info()->list:
    # 读取JSON文件
    with open('data/inters_full_info.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 筛选signal_info不为空的记录
    filtered_data = [item for item in data if item.get('signal_info')]

    normal_data = [item for item in filtered_data if len(item.get('in_links')) <=4 and len(item.get('out_links')) <=4]

    special_data = [item for item in filtered_data if len(item.get('in_links')) >4 or len(item.get('out_links')) >4]
    
    # 将结果写入新文件
    with open('data/filter_inters_full_info_by_signal_info_normal.json', 'w', encoding='utf-8') as f:
        json.dump(normal_data, f, ensure_ascii=False, indent=4)
    
    with open('data/filter_inters_full_info_by_signal_info_special.json', 'w', encoding='utf-8') as f:  
        json.dump(special_data, f, ensure_ascii=False, indent=4)

    print(f'总共找到 {len(filtered_data)} 条包含signal_info的记录')
    print(f'正常记录有 {len(normal_data)} 条')
    print(f'特殊记录有 {len(special_data)} 条')

    return normal_data

def merge_signal_info(signal_info_list: list) -> dict:
    """合并同一way的信号灯数据，只计算指定字段的平均值"""
    if not signal_info_list:
        return {}
    
    # 需要计算平均值的字段
    avg_fields = ['red_time', 'green_time', 'cycle_time', 'start_time', 'end_time']
    
    # 使用第一条记录作为基础
    result = signal_info_list[0].copy()
    
    # 计算指定字段的平均值
    for field in avg_fields:
        if field in result:
            values = [float(info[field]) for info in signal_info_list if field in info]
            if values:
                result[field] = sum(values) / len(values)
    
    return result

def find_way_by_nds_id(nds_id: int, in_links: dict) -> str:
    """根据nds_id找到对应的way"""
    for way, links in in_links.items():
        if str(nds_id) in [str(link) for link in links]:
            return way
    return None

def process_intersection(item: dict) -> dict:
    """处理单个路口的信号灯数据"""
    signal_info = item.get('signal_info', {})
    if not signal_info:
        return item
    
    # 按way分组
    way_groups = defaultdict(lambda: defaultdict(list))
    for nds_id, signal_list in signal_info.items():
        for signal in signal_list:
            way = find_way_by_nds_id(int(nds_id), item['in_links'])
            if way is not None:
                dir = signal.get('dir')
                # 修改signal中的way字段
                signal['way'] = int(way)
                way_groups[way][dir].append(signal)
            else:
                print(f"未找到way，nds_id: {nds_id}")
    
    # 处理每个way组
    processed_signal_info = defaultdict(dict)
    for way, dir_groups in way_groups.items():
        for dir, group in dir_groups.items():
            if len(group) > 1:
                # 合并同一way同一方向的信号灯数据
                processed_signal_info[way][dir] = merge_signal_info(group)
            else:
                # 单个way的数据直接保留
                processed_signal_info[way][dir] = group[0]
    
    # 更新item的signal_info
    result = item.copy()
    result['signal_info'] = dict(processed_signal_info)  # 转换为普通字典
    return result

def set_signal_phase(data: list) -> list:
    """设置信号灯相位,根据信号灯相位设置一套合理的相位方案，way0直行->way0左右->way1直行->way1左右"""
    result = []
    for item in data:
        signal_info = item.get('signal_info', {})
        if not signal_info:
            result.append(item)
            continue
        
        # 获取所有way
        ways = sorted(signal_info.keys())
        if not ways:
            result.append(item)
            continue
        
        # 计算每个相位的初始时间
        total_time = 0
        formatted_signals = []
        # 作一次检查如果周期时间不同则选择最长的周期时间
        cycle_time = 0
        for way in ways:
            for dir in signal_info[way]:
                if signal_info[way][dir]['cycle_time'] > cycle_time:
                    cycle_time = signal_info[way][dir]['cycle_time']

        # 在分配前作一次时间检查，如果各个相位时间之和大于cycle_time，则将cycle_time设置为各个相位时间之和
        for way in ways:
            if 0 in signal_info[way]:
                signal = signal_info[way][0]
                total_time += signal['green_time']
            # 在1,2,7三个方向中选绿灯时间最长的方向
            max_green_time = 0
            if 1 in signal_info[way]:
                signal = signal_info[way][1]
                if signal['green_time'] > max_green_time:
                    max_green_time = signal['green_time']
            if 2 in signal_info[way]:
                signal = signal_info[way][2]
                if signal['green_time'] > max_green_time:
                    max_green_time = signal['green_time']
            if 7 in signal_info[way]:
                signal = signal_info[way][7]
                if signal['green_time'] > max_green_time:
                    max_green_time = signal['green_time']
            total_time += max_green_time
        if total_time > cycle_time:
            cycle_time = total_time
        # 简单配置一下黄灯时间
        yellow_time_total = cycle_time - total_time
        #识别一下有几组信号灯
        signal_count = 0
        for way in ways:
            if 0 in signal_info[way]:
                signal_count += 1
            if 1 in signal_info[way] or 2 in signal_info[way] or 7 in signal_info[way]:
                signal_count += 1
        if signal_count == 0:
            raise Exception("没有信号灯")
        yellow_time_per_signal = yellow_time_total / signal_count
        
        total_time = 0
        for way in ways:
            # 直行相位
            if 0 in signal_info[way]:
                signal = signal_info[way][0]
                for link in item['in_links'][way]:
                    formatted_signal = {
                        "nds_id": link,
                        "period": cycle_time,
                        "green_time": signal.get('green_time'),
                        "initial_phase": (cycle_time - total_time)%cycle_time,
                        "dir": 0  # 直行
                    }
                    formatted_signals.append(formatted_signal)
                total_time += signal['green_time'] + yellow_time_per_signal
            signal_left = {
                "green_time": 0,
            }
            signal_right = {
                "green_time": 0,
            }
            signal_around = {
                "green_time": 0,
            }
            # 左转相位
            if 1 in signal_info[way]:
                signal_left = signal_info[way][1]
                for link in item['in_links'][way]:
                    formatted_signal = {
                        "nds_id": link,
                        "period": cycle_time,
                        "green_time": signal_left.get('green_time'),
                        "initial_phase": cycle_time - total_time,
                        "dir": 1  # 左转
                    }
                    formatted_signals.append(formatted_signal)
                # 右转相位
            if 2 in signal_info[way]:
                signal_right = signal_info[way][2]
                for link in item['in_links'][way]:
                    formatted_signal = {
                        "nds_id": link,
                        "period": cycle_time,
                        "green_time": signal_right.get('green_time'),
                        "initial_phase": cycle_time - total_time,
                        "dir": 2  # 右转
                    }
                    formatted_signals.append(formatted_signal)
            # 掉头相位
            if 7 in signal_info[way]:
                signal_around = signal_info[way][7]
                for link in item['in_links'][way]:
                    formatted_signal = {
                        "nds_id": link,
                        "period": cycle_time,
                        "green_time": signal_around.get('green_time'),
                        "initial_phase": cycle_time - total_time,
                        "dir": 7  # 掉头
                    }
                    formatted_signals.append(formatted_signal)
            max_green_time = max(signal_left.get('green_time'), signal_right.get('green_time'), signal_around.get('green_time'))
            if max_green_time > 0:
                total_time += max_green_time + yellow_time_per_signal
        # 此时total_time应该等于cycle_time
        if abs(total_time - cycle_time)>1e-6:
            print(f"total_time: {total_time}, cycle_time: {cycle_time}")
            raise Exception("total_time != cycle_time")
        # 更新item的signal_info
        new_item = item.copy()
        new_item['signal_info'] = formatted_signals
        result.append(new_item)
    
    print(f'处理了 {len(result)} 个路口的相位方案')
    return result

def process_all_intersections(data: list) -> list:
    """处理所有路口的信号灯数据"""
    result = []
    for item in data:
        processed_item = process_intersection(item)
        result.append(processed_item)
    
    print(f'处理了 {len(result)} 个路口的信号灯数据')
    return result

def format_final_output(data: list) -> list:
    """将数据转换为最终格式"""
    result = []
    for item in data:
        signal_info = item.get('signal_info', [])
        if not signal_info:
            continue
            
        # 按nds_id分组信号灯数据
        nds_groups = defaultdict(list)
        for signal in signal_info:
            nds_id = signal['nds_id']
            nds_groups[nds_id].append({
                "dir": signal['dir'],
                "period": signal['period'],
                "green_time": signal['green_time'],
                "initial_phase": signal['initial_phase']
            })
        
        # 构建最终格式
        link_info = item.get('link_info', {})
        for nds_id, lights in nds_groups.items():
            # 获取对应的out_links
            if str(nds_id) not in link_info:
                raise Exception(f"nds_id: {nds_id} not in link_info")
            
            # 获取该nds_id对应的所有out_links及其方向
            out_top = set()  # 使用集合去重
            lights_info = []
            for out_nds_id, dir_value in link_info[str(nds_id)]['dir'].items():
                # 检查是否有对应方向的信号灯
                for light in lights:
                    if light['dir'] == dir_value:
                        lights_info.append({
                            "out_nds_id": out_nds_id,
                            "period": light['period'],
                            "green_time": light['green_time'],
                            "initial_phase": light['initial_phase']
                        })
                out_top.add(out_nds_id)  # 添加到out_top集合中
            
            formatted_item = {
                "nds_id": nds_id,
                "out_top": ",".join(map(str, sorted(out_top))),  # 排序并转换为字符串
                "lights": lights_info
            }
            result.append(formatted_item)
    
    return result

if __name__ == '__main__':
    normal_data = filter_signal_info()
    processed_data = process_all_intersections(normal_data)
    phased_data = set_signal_phase(processed_data)
    with open('data/processed_signal_info.json', 'w', encoding='utf-8') as f:
        json.dump(phased_data, f, ensure_ascii=False, indent=4)
    final_data = format_final_output(phased_data)
    
    # 保存处理后的数据
    with open('data/final_signal_info.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4) 