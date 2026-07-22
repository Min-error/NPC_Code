import os
import glob
import pandas as pd
from io import StringIO

# 你的数据
data_path = r"E:/VMware/windows share folders/trace_info"
trace_file = "msr"

# 根据目录中匹配的文件决定 trace 数量，按文件名排序
file_dir = os.path.join(data_path, trace_file)
file_pattern = os.path.join(file_dir, "read_info*.csv")
file_list = sorted(glob.glob(file_pattern))

if not file_list:
    print(f"在路径 {file_dir} 未找到匹配的文件: {file_pattern}")
else:
    print(f"找到 {len(file_list)} 个文件用于分析。")

for i, input_data_path in enumerate(file_list, start=1):
    print("=" * 80)
    print(f"第 {i} 组数据分析，文件路径: {input_data_path}")

    # 读取数据
    df = pd.read_csv(input_data_path)
    if df.empty:
        print("数据文件为空，跳过分析。")
        continue

    # print("原始数据预览:")
    # print(df.head(10))
    print(f"\n总记录数: {len(df)}")
    print("=" * 60)

    def analyze_sequential_read(df):
        """
        分析SSD读取是否为顺序读 - 基于pageindexs进行连续性判断
        """
        sequential_issues = []
        block_pageindex_sequence = []
        
        print("按时间顺序分析读取模式 (基于pageindexs):")
        print("-" * 50)
        
        for i in range(len(df) - 1):
            current = df.iloc[i]
            next_row = df.iloc[i + 1]
            
            current_block = current['block']
            current_pageindex = current['pageindexs']
            next_block = next_row['block']
            next_pageindex = next_row['pageindexs']
            
            block_pageindex_sequence.append((current_block, current_pageindex))
            
            # 检查pageindex是否连续递增
            if next_pageindex == current_pageindex + 1:
                pass
            else:
                gap_size = next_pageindex - current_pageindex
                if gap_size <= 0:
                    issue_type = "pageindex回退或不变"
                else:
                    issue_type = "pageindex跳跃"
                
                sequential_issues.append({
                    'type': issue_type,
                    '位置': f"第{i+1}-{i+2}行",
                    '当前': f"block {current_block}, pageindex {current_pageindex}",
                    '下一个': f"block {next_block}, pageindex {next_pageindex}",
                    '跳跃大小': gap_size,
                    '是否跨block': current_block != next_block
                })
        
        block_pageindex_sequence.append((df.iloc[-1]['block'], df.iloc[-1]['pageindexs']))
        
        return sequential_issues, block_pageindex_sequence

    def analyze_by_block(df):
        """
        按block分组分析每个block内的pageindex读取模式
        """
        # print("\n按block分组分析 (基于pageindexs):")
        # print("-" * 50)
        
        block_groups = df.groupby('block')
        block_analysis = []
        
        for block, group in block_groups:
            pageindexs = group['pageindexs'].sort_values().values
            total_access = len(pageindexs)
            
            if total_access == 0:
                continue
                
            gaps = []
            continuous_segments = []
            current_segment = [pageindexs[0]]
            
            for i in range(len(pageindexs) - 1):
                gap = pageindexs[i + 1] - pageindexs[i]
                if gap == 1:
                    current_segment.append(pageindexs[i + 1])
                else:
                    if gap > 1:
                        gaps.append(gap)
                    if len(current_segment) > 1:
                        continuous_segments.append(current_segment)
                    current_segment = [pageindexs[i + 1]]
            
            if len(current_segment) > 1:
                continuous_segments.append(current_segment)
            elif len(current_segment) == 1 and total_access == 1:
                continuous_segments.append(current_segment)
            
            continuous_ratio = (total_access - len(gaps)) / total_access if total_access > 1 else 0
            max_segment_length = max([len(seg) for seg in continuous_segments]) if continuous_segments else 1
            
            block_analysis.append({
                'block': block,
                '访问次数': total_access,
                'pageindex范围': f"{min(pageindexs)}-{max(pageindexs)}",
                '总跨度': max(pageindexs) - min(pageindexs),
                '不连续间隙数': len(gaps),
                '连续段数量': len(continuous_segments),
                '最大连续段长度': max_segment_length,
                '连续性比例': f"{continuous_ratio:.1%}",
                '最大间隙': max(gaps) if gaps else 0
            })
            
            # print(f"Block {block}: 访问{total_access}次, pageindex范围 {min(pageindexs)}-{max(pageindexs)}")
            # print(f"  连续段: {len(continuous_segments)}段, 最大连续段: {max_segment_length}次")
            # print(f"  连续性: {continuous_ratio:.1%}, 间隙数: {len(gaps)}")
            
            # if len(continuous_segments) <= 5:
            #     for j, seg in enumerate(continuous_segments):
            #         if len(seg) > 1:
            #             print(f"    段{j+1}: {seg[0]}→{seg[-1]} (长度{len(seg)})")
        
        return block_analysis

    def analyze_global_sequence(df):
        """
        分析全局pageindex序列的连续性
        """
        # print("\n全局pageindex序列分析:")
        # print("-" * 40)
        
        global_sequence = df['pageindexs'].values
        total_access = len(global_sequence)
        
        gaps = []
        continuous_count = 0
        current_run = 1
        
        for i in range(total_access - 1):
            if global_sequence[i + 1] == global_sequence[i] + 1:
                continuous_count += 1
                current_run += 1
            else:
                gap_size = global_sequence[i + 1] - global_sequence[i]
                gaps.append({
                    'position': f"{i+1}-{i+2}",
                    'from': global_sequence[i],
                    'to': global_sequence[i + 1],
                    'gap': gap_size
                })
                current_run = 1
        
        global_continuous_ratio = continuous_count / (total_access - 1) if total_access > 1 else 0
        
        # print(f"全局连续访问次数: {continuous_count}/{total_access-1} ({global_continuous_ratio:.1%})")
        # print(f"总间隙数: {len(gaps)}")
        
        # if gaps:
        #     avg_gap = sum(g['gap'] for g in gaps) / len(gaps)
        #     max_gap = max(g['gap'] for g in gaps)
        #     print(f"平均间隙大小: {avg_gap:.1f}, 最大间隙: {max_gap}")
            
        #     large_gaps = sorted(gaps, key=lambda x: x['gap'], reverse=True)[:5]
        #     print("前5大间隙:")
        #     for gap in large_gaps:
        #         print(f"  位置{gap['position']}: {gap['from']} → {gap['to']} (跳跃{gap['gap']})")
        
        return global_continuous_ratio, gaps

    sequential_issues, sequence = analyze_sequential_read(df)
    block_analysis = analyze_by_block(df)
    global_ratio, global_gaps = analyze_global_sequence(df)

    print("\n" + "=" * 60)
    print("分析结果汇总 (基于pageindexs):")
    print("=" * 60)

    if not sequential_issues:
        print("✅ 这是完美顺序读取！所有pageindex都是连续的。")
    else:
        jump_issues = [issue for issue in sequential_issues if issue['type'] == 'pageindex跳跃']
        backtrack_issues = [issue for issue in sequential_issues if issue['type'] == 'pageindex回退或不变']
        cross_block_issues = [issue for issue in sequential_issues if issue['是否跨block']]
        
        print("❌ 这不是完美顺序读取！发现不连续问题:")
        print(f"总不连续点: {len(sequential_issues)} 个")
        print(f"  - pageindex跳跃: {len(jump_issues)} 个")
        print(f"  - pageindex回退: {len(backtrack_issues)} 个")
        print(f"  - 其中跨block不连续: {len(cross_block_issues)} 个")
        
        # if sequential_issues:
        #     print("\n前5个不连续问题示例:")
        #     for i, issue in enumerate(sequential_issues[:5]):
        #         block_info = "跨block" if issue['是否跨block'] else "同block内"
        #         print(f"{i+1}. {issue['type']} ({block_info})")
        #         print(f"   位置: {issue['位置']}")
        #         print(f"   当前: {issue['当前']}")
        #         print(f"   下一个: {issue['下一个']}")
        #         print(f"   跳跃大小: {issue['跳跃大小']}")
        #         print()

    total_sequential_ratio = 1 - len(sequential_issues) / (len(df) - 1) if len(df) > 1 else 0
    print(f"整体连续性比例: {total_sequential_ratio:.1%}")
    print(f"全局连续性比例: {global_ratio:.1%}")

    print("\n读取类型判断:")
    if total_sequential_ratio > 0.9:
        print("✅ 基本为顺序读取 (连续性 > 90%)")
    elif total_sequential_ratio > 0.7:
        print("⚠️  大部分顺序读取，但有部分跳跃 (连续性 70%-90%)")
    elif total_sequential_ratio > 0.5:
        print("⚠️  混合读取模式 (连续性 50%-70%)")
    else:
        print("❌ 随机读取模式 (连续性 < 50%)")

    # print("\n访问模式可视化 (前20个记录, 格式: block(pageindex)):")
    # vis_sequence = [f"{b}({p})" for b, p in sequence[:20]]
    # print(" -> ".join(vis_sequence))
    
    print("\n" + "=" * 80)
