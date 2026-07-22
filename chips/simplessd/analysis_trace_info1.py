import pandas as pd
import numpy as np
import os
from collections import defaultdict, Counter, deque
import sys
from datetime import datetime

# 控制输出详细程度的变量
OUTPUT_DETAIL = True  # True: 输出完整分析, False: 只输出连续性结果

# 缓存相关参数 - 可调整
CACHE_WL_SIZE = 5      # 缓存中可保存的WL数量
MAX_GAP_THRESHOLD = 10 # 允许的最大WL跳跃间隔
MIN_SEQUENTIAL_RATIO = 0.6  # 判定为顺序读取的最小连续性比例

# 文件输出设置
OUTPUT_TO_FILE = True  # 是否输出到文件
OUTPUT_DIR = "analysis_results"  # 输出目录

# 分析模式选择
ANALYSIS_MODE = "both"  # "block": 只分析block级别, "file": 只分析文件级别, "both": 两者都分析

def setup_output_directory(trace_file):
    """设置输出目录"""
    if not OUTPUT_TO_FILE:
        return None
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"analysis_result_{trace_file}_{timestamp}.txt")
    return output_file

class DualOutput:
    """同时输出到终端和文件的类"""
    def __init__(self, terminal, file):
        self.terminal = terminal
        self.file = file
    
    def write(self, message):
        self.terminal.write(message)
        if self.file:
            self.file.write(message)
    
    def flush(self):
        self.terminal.flush()
        if self.file:
            self.file.flush()

def get_trace_files_count(data_path, trace_file):
    """
    自动获取目录中的文件数量
    """
    trace_dir = os.path.join(data_path, trace_file)
    if not os.path.exists(trace_dir):
        print(f"错误: 目录不存在: {trace_dir}")
        return 0
    
    # 查找所有 read_info*.csv 文件
    files = [f for f in os.listdir(trace_dir) 
             if f.startswith('read_info') and f.endswith('.csv')]
    
    # 提取文件编号并排序
    file_numbers = []
    for f in files:
        try:
            num_str = f.replace('read_info', '').replace('.csv', '')
            if num_str.isdigit():
                file_numbers.append(int(num_str))
        except:
            continue
    
    if file_numbers:
        max_file_num = max(file_numbers)
        if OUTPUT_DETAIL:
            print(f"在目录 {trace_dir} 中找到 {len(file_numbers)} 个数据文件")
            print(f"文件编号范围: {min(file_numbers)} - {max_file_num}")
        return max_file_num
    else:
        print(f"在目录 {trace_dir} 中未找到数据文件")
        return 0

def analyze_block_wl_sequentiality(df):
    """
    分析每个block内部的WL顺序读取模式（考虑缓存）
    """
    if OUTPUT_DETAIL:
        print("每个Block内部的WL顺序读取分析（考虑缓存）")
        print(f"缓存参数: WL缓存大小={CACHE_WL_SIZE}, 最大允许间隔={MAX_GAP_THRESHOLD}")
        print("=" * 60)
    
    # 按block分组分析
    block_groups = df.groupby('block')
    block_analysis_results = {}
    
    total_blocks = len(block_groups)
    sequential_blocks = 0
    mixed_blocks = 0
    random_blocks = 0
    
    # 存储所有block的连续性信息
    block_continuity_info = []
    
    if OUTPUT_DETAIL:
        print(f"总共有 {total_blocks} 个block被访问")
        print("\n各Block的WL访问模式分析:")
        print("-" * 50)
    
    for block_id, block_data in block_groups:
        if len(block_data) < 3:  # 太小的block跳过
            continue
            
        # 分析该block内的WL访问顺序（考虑缓存）
        wl_sequence = block_data['wl'].values
        access_count = len(wl_sequence)
        
        # 分析WL连续性（考虑缓存）
        wl_sequential_info = analyze_wl_sequence_with_cache(block_id, wl_sequence)
        block_analysis_results[block_id] = wl_sequential_info
        
        # 存储block连续性信息
        block_continuity_info.append({
            'block_id': block_id,
            'sequential_ratio': wl_sequential_info['sequential_ratio'],
            'access_count': access_count,
            'wl_range': wl_sequential_info['wl_range'],
            'avg_gap': wl_sequential_info['avg_gap'],
            'access_pattern': wl_sequential_info['access_pattern']
        })
        
        # 分类统计（使用更宽松的标准）
        if wl_sequential_info['sequential_ratio'] >= MIN_SEQUENTIAL_RATIO:
            sequential_blocks += 1
            block_type = "顺序读取"
        elif wl_sequential_info['sequential_ratio'] >= 0.3:
            mixed_blocks += 1
            block_type = "混合读取"
        else:
            random_blocks += 1
            block_type = "随机读取"
        
        # 只在详细输出时显示每个block的分析结果
        if OUTPUT_DETAIL:
            print(f"Block {block_id:3d}: 访问{access_count:3d}次, "
                  f"WL范围[{wl_sequential_info['wl_min']:3d}-{wl_sequential_info['wl_max']:3d}], "
                  f"连续性{wl_sequential_info['sequential_ratio']:6.1%}, "
                  f"类型: {block_type}")
            
            if wl_sequential_info['sequential_segments']:
                longest_seg = max(wl_sequential_info['sequential_segments'], key=len)
                print(f"       最长顺序段: {len(longest_seg)}次, WL{longest_seg[0]}→{longest_seg[-1]}")
    
    # 显示block连续性统计
    if OUTPUT_DETAIL and block_continuity_info:
        print_block_continuity_statistics(block_continuity_info)
    
    # 总体统计（总是输出）
    print(f"📊 Block访问模式统计 (缓存大小={CACHE_WL_SIZE}, 阈值={MIN_SEQUENTIAL_RATIO:.0%}):")
    print(f"顺序读取block: {sequential_blocks}/{total_blocks} ({sequential_blocks/max(1,total_blocks):.1%})")
    print(f"混合读取block: {mixed_blocks}/{total_blocks} ({mixed_blocks/max(1,total_blocks):.1%})")
    print(f"随机读取block: {random_blocks}/{total_blocks} ({random_blocks/max(1,total_blocks):.1%})")
    
    return block_analysis_results, (sequential_blocks, mixed_blocks, random_blocks, total_blocks), block_continuity_info

def analyze_file_sequentiality(df, file_index):
    """
    分析整个文件的WL顺序读取模式（文件级别的连续性）
    """
    if OUTPUT_DETAIL:
        print(f"\n📊 分析文件 {file_index} 的整体顺序性")
        print("=" * 60)
    
    # 获取所有WL访问序列
    wl_sequence = df['wl'].values
    total_accesses = len(wl_sequence)
    
    if total_accesses < 2:
        return {
            'file_index': file_index,
            'total_accesses': total_accesses,
            'sequential_ratio': 0,
            'avg_gap': 0,
            'sequential_segments': [],
            'access_pattern': "数据不足",
            'max_segment_length': 0,
            'avg_segment_length': 0,
            'segment_count': 0
        }
    
    # 分析整个文件的WL连续性
    sequential_count = 0
    gaps = []
    sequential_segments = []
    current_segment = []
    
    # 模拟WL缓存
    wl_cache = deque(maxlen=CACHE_WL_SIZE)
    
    for i in range(total_accesses - 1):
        current_wl = wl_sequence[i]
        next_wl = wl_sequence[i + 1]
        gap = next_wl - current_wl
        
        gaps.append(gap)
        
        # 更新缓存
        wl_cache.append(current_wl)
        
        # 检查WL连续性（考虑缓存机制）
        is_sequential = False
        
        # 情况1: 严格连续
        if gap == 1:
            is_sequential = True
        # 情况2: 小跳跃，但在缓存范围内
        elif 1 < gap <= MAX_GAP_THRESHOLD:
            # 检查跳跃的WL是否在缓存中
            missing_wls = list(range(current_wl + 1, next_wl))
            cached_missing = any(wl in wl_cache for wl in missing_wls)
            if cached_missing:
                is_sequential = True
        # 情况3: 大跳跃，但方向一致
        elif gap > MAX_GAP_THRESHOLD:
            # 检查整体趋势是否单调
            if i > 0 and i < total_accesses - 2:
                prev_gap = wl_sequence[i] - wl_sequence[i-1]
                next_gap = wl_sequence[i+2] - wl_sequence[i+1] if i < total_accesses - 2 else gap
                if gap > 0 and prev_gap > 0 and next_gap > 0:
                    is_sequential = True
        
        if is_sequential:
            sequential_count += 1
            if not current_segment:
                current_segment = [current_wl]
            current_segment.append(next_wl)
        else:
            if len(current_segment) >= 2:
                sequential_segments.append(current_segment.copy())
            current_segment = []
    
    # 处理最后一个段
    if len(current_segment) >= 2:
        sequential_segments.append(current_segment)
    
    # 计算统计量
    sequential_ratio = sequential_count / (total_accesses - 1)
    avg_gap = np.mean(gaps) if gaps else 0
    
    # 分析访问模式
    access_pattern = analyze_wl_access_pattern(wl_sequence)
    
    # 分析连续性分布
    segment_lengths = [len(seg) for seg in sequential_segments]
    max_segment_length = max(segment_lengths) if segment_lengths else 0
    avg_segment_length = np.mean(segment_lengths) if segment_lengths else 0
    
    if OUTPUT_DETAIL:
        print(f"文件 {file_index} 顺序性分析结果:")
        print(f"  总访问次数: {total_accesses}")
        print(f"  连续性比例: {sequential_ratio:.2%}")
        print(f"  平均WL间隔: {avg_gap:.2f}")
        print(f"  最长连续段: {max_segment_length} 次访问")
        print(f"  平均连续段: {avg_segment_length:.1f} 次访问")
        print(f"  连续段数量: {len(sequential_segments)}")
        print(f"  访问模式: {access_pattern}")
    
    return {
        'file_index': file_index,
        'total_accesses': total_accesses,
        'sequential_ratio': sequential_ratio,
        'avg_gap': avg_gap,
        'sequential_segments': sequential_segments,
        'access_pattern': access_pattern,
        'max_segment_length': max_segment_length,
        'avg_segment_length': avg_segment_length,
        'segment_count': len(sequential_segments)
    }

def print_file_continuity_ranking(all_file_results):
    """按文件连续性排序显示"""
    if not all_file_results:
        return
    
    print(f"\n🏆 文件连续性排序 (基于整体顺序性):")
    print("=" * 80)
    print(f"{'排名':<4} {'文件':<8} {'连续性':<10} {'访问次数':<10} {'最长段':<8} {'平均间隔':<10} {'模式':<12}")
    print("-" * 80)
    
    # 按连续性从高到低排序
    sorted_files = sorted(all_file_results, key=lambda x: x['sequential_ratio'], reverse=True)
    
    for i, result in enumerate(sorted_files):
        rank = i + 1
        file_index = result['file_index']
        continuity = result['sequential_ratio']
        total_accesses = result['total_accesses']
        max_segment = result['max_segment_length']
        avg_gap = result['avg_gap']
        pattern = result['access_pattern']
        
        print(f"{rank:<4} {file_index:<8} {continuity:9.2%} {total_accesses:<10} "
              f"{max_segment:<8} {avg_gap:<10.2f} {pattern:<12}")
    
    # 显示统计信息
    if len(sorted_files) > 0:
        continuities = [r['sequential_ratio'] for r in sorted_files]
        avg_continuity = np.mean(continuities)
        max_continuity = sorted_files[0]['sequential_ratio']
        min_continuity = sorted_files[-1]['sequential_ratio']
        
        print(f"\n📈 文件连续性统计:")
        print(f"平均连续性: {avg_continuity:.2%}")
        print(f"最高连续性: {max_continuity:.2%} (文件 {sorted_files[0]['file_index']})")
        print(f"最低连续性: {min_continuity:.2%} (文件 {sorted_files[-1]['file_index']})")
        print(f"连续性范围: {min_continuity:.2%} - {max_continuity:.2%}")
        
        # 分类统计
        sequential_files = len([r for r in sorted_files if r['sequential_ratio'] >= MIN_SEQUENTIAL_RATIO])
        mixed_files = len([r for r in sorted_files if 0.3 <= r['sequential_ratio'] < MIN_SEQUENTIAL_RATIO])
        random_files = len([r for r in sorted_files if r['sequential_ratio'] < 0.3])
        
        print(f"\n📊 文件访问模式分类:")
        print(f"顺序读取文件: {sequential_files}/{len(sorted_files)} ({sequential_files/len(sorted_files):.1%})")
        print(f"混合读取文件: {mixed_files}/{len(sorted_files)} ({mixed_files/len(sorted_files):.1%})")
        print(f"随机读取文件: {random_files}/{len(sorted_files)} ({random_files/len(sorted_files):.1%})")

def print_block_continuity_statistics(block_continuity_info):
    """显示各个block的连续性统计"""
    if not block_continuity_info:
        return
    
    print(f"\n📈 各个Block的连续性统计:")
    print("=" * 60)
    
    # 计算统计信息
    continuities = [info['sequential_ratio'] for info in block_continuity_info]
    avg_continuity = np.mean(continuities)
    max_continuity = max(continuities)
    min_continuity = min(continuities)
    std_continuity = np.std(continuities)
    
    # 找到最高和最低连续性的block
    max_block = max(block_continuity_info, key=lambda x: x['sequential_ratio'])
    min_block = min(block_continuity_info, key=lambda x: x['sequential_ratio'])
    
    print(f"平均连续性: {avg_continuity:.1%}")
    print(f"最高连续性: {max_continuity:.1%} (Block {max_block['block_id']})")
    print(f"最低连续性: {min_continuity:.1%} (Block {min_block['block_id']})")
    print(f"连续性标准差: {std_continuity:.3f}")
    print(f"连续性范围: {min_continuity:.1%} - {max_continuity:.1%}")
    
    # 连续性分布
    continuity_bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    bin_counts = [0] * (len(continuity_bins) - 1)
    
    for continuity in continuities:
        for i in range(len(continuity_bins) - 1):
            if continuity_bins[i] <= continuity < continuity_bins[i + 1]:
                bin_counts[i] += 1
                break
    
    print(f"\n📊 连续性分布:")
    for i in range(len(continuity_bins) - 1):
        if bin_counts[i] > 0:
            range_str = f"{continuity_bins[i]:.0%}-{continuity_bins[i+1]:.0%}"
            print(f"  {range_str}: {bin_counts[i]}个block ({bin_counts[i]/len(continuities):.1%})")

def analyze_wl_sequence_with_cache(block_id, wl_sequence):
    """
    分析单个block内的WL序列（考虑缓存机制）
    """
    access_count = len(wl_sequence)
    
    # 模拟WL缓存
    wl_cache = deque(maxlen=CACHE_WL_SIZE)
    sequential_count = 0
    gaps = []
    sequential_segments = []
    current_segment = []
    
    for i in range(access_count - 1):
        current_wl = wl_sequence[i]
        next_wl = wl_sequence[i + 1]
        gap = next_wl - current_wl
        
        gaps.append(gap)
        
        # 更新缓存
        wl_cache.append(current_wl)
        
        # 检查WL连续性（考虑缓存机制）
        is_sequential = False
        
        # 情况1: 严格连续
        if gap == 1:
            is_sequential = True
        # 情况2: 小跳跃，但在缓存范围内
        elif 1 < gap <= MAX_GAP_THRESHOLD:
            # 检查跳跃的WL是否在缓存中（表示可能被预取或之前访问过）
            missing_wls = list(range(current_wl + 1, next_wl))
            cached_missing = any(wl in wl_cache for wl in missing_wls)
            if cached_missing:
                is_sequential = True
        # 情况3: 大跳跃，但方向一致（单调递增/递减）
        elif gap > MAX_GAP_THRESHOLD:
            # 检查整体趋势是否单调
            if i > 0 and i < access_count - 2:
                prev_gap = wl_sequence[i] - wl_sequence[i-1]
                next_gap = wl_sequence[i+2] - wl_sequence[i+1] if i < access_count - 2 else gap
                # 如果前后都是正向，且当前也是正向，认为是顺序访问（可能有大的预取跳跃）
                if gap > 0 and prev_gap > 0 and next_gap > 0:
                    is_sequential = True
        
        if is_sequential:
            sequential_count += 1
            if not current_segment:
                current_segment = [current_wl]
            current_segment.append(next_wl)
        else:
            if len(current_segment) >= 2:
                sequential_segments.append(current_segment.copy())
            current_segment = []
    
    # 处理最后一个段
    if len(current_segment) >= 2:
        sequential_segments.append(current_segment)
    
    # 计算统计量
    sequential_ratio = sequential_count / (access_count - 1) if access_count > 1 else 0
    
    # 分析访问模式
    access_pattern = analyze_wl_access_pattern(wl_sequence)
    
    return {
        'block_id': block_id,
        'access_count': access_count,
        'wl_min': min(wl_sequence) if access_count > 0 else 0,
        'wl_max': max(wl_sequence) if access_count > 0 else 0,
        'wl_range': max(wl_sequence) - min(wl_sequence) if access_count > 0 else 0,
        'sequential_ratio': sequential_ratio,
        'sequential_segments': sequential_segments,
        'avg_gap': np.mean(gaps) if gaps else 0,
        'access_pattern': access_pattern,
        'cache_hit_simulated': sequential_count  # 模拟的缓存命中次数
    }

def analyze_wl_access_pattern(wl_sequence):
    """
    分析WL访问模式
    """
    if len(wl_sequence) < 3:
        return "数据不足"
    
    # 计算方向变化
    direction_changes = 0
    positive_directions = 0
    negative_directions = 0
    
    for i in range(len(wl_sequence) - 1):
        gap = wl_sequence[i + 1] - wl_sequence[i]
        if gap > 0:
            positive_directions += 1
        elif gap < 0:
            negative_directions += 1
        
        if i > 0:
            prev_gap = wl_sequence[i] - wl_sequence[i-1]
            current_gap = gap
            if (prev_gap > 0 and current_gap < 0) or (prev_gap < 0 and current_gap > 0):
                direction_changes += 1
    
    total_directions = positive_directions + negative_directions
    if total_directions == 0:
        return "稳定"
    
    positive_ratio = positive_directions / total_directions
    change_ratio = direction_changes / (len(wl_sequence) - 2) if len(wl_sequence) > 2 else 0
    
    if change_ratio < 0.1:  # 方向变化少于10%
        if positive_ratio > 0.8:
            return "强递增"
        elif positive_ratio < 0.2:
            return "强递减"
        else:
            return "基本单调"
    elif change_ratio < 0.3:
        return "轻度振荡"
    else:
        return "剧烈振荡"

def analyze_wl_locality(df):
    """分析WL访问的局部性特征"""
    if not OUTPUT_DETAIL:
        return
    
    print(f"\n🔍 WL访问局部性分析 (缓存大小={CACHE_WL_SIZE}):")
    print("=" * 50)
    
    wl_access_sequence = []
    for _, row in df.iterrows():
        wl_access_sequence.append((row['block'], row['wl']))
    
    # 模拟缓存分析
    cache_size = CACHE_WL_SIZE
    cache_hits = 0
    cache = deque(maxlen=cache_size)
    
    for access in wl_access_sequence:
        if access in cache:
            cache_hits += 1
            # 更新缓存位置（LRU）
            cache.remove(access)
            cache.append(access)
        else:
            cache.append(access)
    
    cache_hit_ratio = cache_hits / len(wl_access_sequence) if wl_access_sequence else 0
    
    print(f"模拟缓存命中率: {cache_hit_ratio:.2%} (缓存大小: {cache_size} WL)")
    print(f"缓存命中次数: {cache_hits}/{len(wl_access_sequence)}")

def print_detailed_sequential_blocks(block_analysis):
    """显示顺序性较好的block的详细信息"""
    if not OUTPUT_DETAIL:
        return
    
    sequential_blocks = {k: v for k, v in block_analysis.items() 
                        if v['sequential_ratio'] >= MIN_SEQUENTIAL_RATIO}
    
    if sequential_blocks:
        print(f"\n🎯 顺序性较好的Block (连续性≥{MIN_SEQUENTIAL_RATIO:.0%}):")
        print("=" * 60)
        for block_id, info in sorted(sequential_blocks.items(), 
                                   key=lambda x: x[1]['sequential_ratio'], reverse=True):
            print(f"Block {block_id}: 访问{info['access_count']}次, "
                  f"连续性{info['sequential_ratio']:.1%}, 模式: {info['access_pattern']}")

def check_file_validity(file_path):
    """检查文件是否有效"""
    if not os.path.exists(file_path):
        return False, "文件不存在"
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "文件为空"
    
    try:
        df_sample = pd.read_csv(file_path, nrows=5)
        if len(df_sample) == 0:
            return False, "文件无数据"
        if 'block' not in df_sample.columns or 'wl' not in df_sample.columns:
            return False, "文件格式错误（缺少必要列）"
    except Exception as e:
        return False, f"文件读取错误: {str(e)}"
    
    return True, "文件有效"

# 主分析函数
def analyze_single_file(df, file_index):
    """分析单个文件的WL顺序读取模式"""
    if OUTPUT_DETAIL:
        print("=" * 80)
        print(f"第 {file_index} 组数据分析")
        print(f"总记录数: {len(df)}")
        print(f"缓存参数: WL缓存大小={CACHE_WL_SIZE}, 连续性阈值={MIN_SEQUENTIAL_RATIO:.0%}")
        print("=" * 70)
    
    results = {}
    
    # Block级别分析
    if ANALYSIS_MODE in ["block", "both"]:
        if OUTPUT_DETAIL:
            print("开始分析每个Block的WL顺序读取模式...")
        block_results, block_stats, block_continuity_info = analyze_block_wl_sequentiality(df)
        results['block_analysis'] = {
            'block_results': block_results,
            'block_stats': block_stats,
            'block_continuity_info': block_continuity_info
        }
    
    # 文件级别分析
    if ANALYSIS_MODE in ["file", "both"]:
        if OUTPUT_DETAIL:
            print("\n开始分析文件整体顺序性...")
        file_result = analyze_file_sequentiality(df, file_index)
        results['file_analysis'] = file_result
    
    # 只在详细模式输出额外分析
    if OUTPUT_DETAIL:
        analyze_wl_locality(df)
        if ANALYSIS_MODE in ["block", "both"]:
            print_detailed_sequential_blocks(block_results)
    
    # 返回统计结果
    if ANALYSIS_MODE in ["block", "both"]:
        sequential, mixed, random, total = block_stats
        results['summary'] = {
            'file_index': file_index,
            'total_blocks': total,
            'sequential_blocks': sequential,
            'sequential_ratio': sequential / max(1, total),
            'mixed_blocks': mixed,
            'mixed_ratio': mixed / max(1, total),
            'random_blocks': random,
            'random_ratio': random / max(1, total),
            'total_records': len(df),
            'cache_size_used': CACHE_WL_SIZE,
            'sequential_threshold': MIN_SEQUENTIAL_RATIO
        }
    else:
        results['summary'] = results['file_analysis']
    
    return results

# 文件循环分析
def analyze_all_files(data_path, trace_file):
    """分析所有文件的主函数"""
    # 自动获取文件数量
    trace_num = get_trace_files_count(data_path, trace_file)
    if trace_num == 0:
        print("未找到有效的数据文件，退出分析")
        return []
    
    print(f"找到 {trace_num} 个数据文件，开始分析...")
    print(f"分析参数: 缓存大小={CACHE_WL_SIZE} WL, 连续性阈值={MIN_SEQUENTIAL_RATIO:.0%}")
    print(f"分析模式: {ANALYSIS_MODE}")
    
    all_results = []
    all_file_results = []
    valid_files = 0
    skipped_files = 0
    
    for i in range(1, trace_num + 1):
        input_data_path = f"{data_path}/{trace_file}/read_info{i}.csv"
        print(f"\n🔍 分析文件 {i}: {input_data_path}")
        
        # 检查文件有效性
        is_valid, message = check_file_validity(input_data_path)
        
        if not is_valid:
            if OUTPUT_DETAIL:
                print(f"⚠️  跳过文件 {i}: {message}")
            skipped_files += 1
            continue
        
        # 读取数据
        try:
            df = pd.read_csv(input_data_path)
            
            if len(df) == 0:
                if OUTPUT_DETAIL:
                    print(f"⚠️  文件 {i} 数据为空，跳过分析")
                skipped_files += 1
                continue
            
            # 执行分析
            result = analyze_single_file(df, i)
            all_results.append(result)
            valid_files += 1
            
            # 收集文件级别结果用于排序
            if ANALYSIS_MODE in ["file", "both"] and 'file_analysis' in result:
                all_file_results.append(result['file_analysis'])
            
            # 简洁输出模式
            if not OUTPUT_DETAIL:
                if ANALYSIS_MODE in ["block", "both"]:
                    summary = result['summary']
                    seq_ratio = summary['sequential_ratio']
                    mix_ratio = summary['mixed_ratio']
                    rand_ratio = summary['random_ratio']
                    print(f"文件{i:2d}: 顺序{seq_ratio:5.1%} 混合{mix_ratio:5.1%} 随机{rand_ratio:5.1%} "
                          f"(block数: {summary['total_blocks']})")
                else:
                    file_result = result['file_analysis']
                    seq_ratio = file_result['sequential_ratio']
                    pattern = file_result['access_pattern']
                    print(f"文件{i:2d}: 连续性{seq_ratio:6.1%} 模式:{pattern:<8} "
                          f"访问次数:{file_result['total_accesses']}")
                
        except Exception as e:
            print(f"❌ 分析文件 {i} 时出错: {str(e)}")
            skipped_files += 1
            continue
    
    # 显示文件连续性排序（文件级别分析）
    if ANALYSIS_MODE in ["file", "both"] and all_file_results:
        print_file_continuity_ranking(all_file_results)
    
    # 显示分析总结
    print(f"\n分析完成！")
    print(f"有效文件: {valid_files} 个, 跳过文件: {skipped_files} 个")
    print(f"分析参数: 缓存大小={CACHE_WL_SIZE}, 连续性阈值={MIN_SEQUENTIAL_RATIO:.0%}")
    print(f"分析模式: {ANALYSIS_MODE}")
    
    # 显示总体统计（block级别分析）
    if not OUTPUT_DETAIL and all_results and ANALYSIS_MODE in ["block", "both"]:
        print("\n" + "=" * 60)
        print("总体统计:")
        print("=" * 60)
        
        total_sequential = sum(r['summary']['sequential_blocks'] for r in all_results)
        total_mixed = sum(r['summary']['mixed_blocks'] for r in all_results)
        total_random = sum(r['summary']['random_blocks'] for r in all_results)
        total_blocks = sum(r['summary']['total_blocks'] for r in all_results)
        
        if total_blocks > 0:
            print(f"顺序读取block: {total_sequential}/{total_blocks} ({total_sequential/total_blocks:.1%})")
            print(f"混合读取block: {total_mixed}/{total_blocks} ({total_mixed/total_blocks:.1%})")
            print(f"随机读取block: {total_random}/{total_blocks} ({total_random/total_blocks:.1%})")
    
    return all_results

# 使用示例
if __name__ == "__main__":
    # 设置参数
    data_path = "E:/VMware/windows share folders/trace_info"
    # trace_file = "msr"
    trace_file = "trace1"
    
    # 设置输出模式
    OUTPUT_DETAIL = True
    
    # 设置分析模式
    ANALYSIS_MODE = "both"  # "block", "file", "both"
    
    # 调整缓存参数
    CACHE_WL_SIZE = 8
    MAX_GAP_THRESHOLD = 15
    MIN_SEQUENTIAL_RATIO = 0.5
    
    # 设置文件输出
    output_file_path = None
    original_stdout = sys.stdout
    
    if OUTPUT_TO_FILE:
        output_file_path = setup_output_directory(trace_file)
        if output_file_path:
            print(f"输出将保存到: {output_file_path}")
            output_file = open(output_file_path, 'w', encoding='utf-8')
            dual_output = DualOutput(original_stdout, output_file)
            sys.stdout = dual_output
    
    try:
        print("=" * 80)
        print("SSD WL顺序读取分析工具 - 多模式分析")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"数据路径: {data_path}/{trace_file}")
        print(f"分析参数: 缓存大小={CACHE_WL_SIZE}, 最大间隔={MAX_GAP_THRESHOLD}, 阈值={MIN_SEQUENTIAL_RATIO:.0%}")
        print(f"分析模式: {ANALYSIS_MODE}")
        print("=" * 80)
        
        # 执行分析
        results = analyze_all_files(data_path, trace_file)
        
        print(f"\n分析完成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    finally:
        # 恢复标准输出
        if OUTPUT_TO_FILE and output_file_path:
            sys.stdout = original_stdout
            output_file.close()
            print(f"分析结果已保存到: {output_file_path}")