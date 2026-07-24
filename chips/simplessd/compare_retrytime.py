import pandas as pd
import numpy as np
import os


def ensure_dir_exists(path):
    # 确保输出目录存在
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建输出目录: {path}")
    else:
        print(f"输出目录已存在: {path}")

def compare_readTime(file1_path, file2_path, output_file=None):
    """
    读取两个CSV文件，对比readTime这一列值不同的数据，并记录下来
    
    Args:
        file1_path: 第一个CSV文件路径
        file2_path: 第二个CSV文件路径
        output_file: 输出文件路径（可选），如果不指定则打印到控制台
    """

    # 读取两个CSV文件
    try:
        df1 = pd.read_csv(file1_path)
        df2 = pd.read_csv(file2_path)
        print(f"成功读取文件1: {file1_path}, 共 {len(df1)} 行")
        print(f"成功读取文件2: {file2_path}, 共 {len(df2)} 行")
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return
    
    # 检查是否存在readTime列
    if 'readTime' not in df1.columns:
        print(f"错误: 文件1中不存在 'readTime' 列")
        print(f"文件1的列名: {list(df1.columns)}")
        return
    
    if 'readTime' not in df2.columns:
        print(f"错误: 文件2中不存在 'readTime' 列")
        print(f"文件2的列名: {list(df2.columns)}")
        return
    
    # 确定用于匹配的列（假设用索引或所有列来匹配行）
    # 如果两个文件的索引可以作为匹配键，使用索引
    # 否则，尝试找到共同的列作为匹配键
    common_cols = set(df1.columns) & set(df2.columns)
    common_cols.discard('readTime')  # 排除readTime列
    
    # 如果行数相同，按索引匹配；否则尝试用其他列匹配
    if len(df1) == len(df2):
        # 按索引匹配
        df1_matched = df1.copy()
        df2_matched = df2.copy()
        df1_matched['_match_key'] = df1_matched.index
        df2_matched['_match_key'] = df2_matched.index
    elif common_cols:
        # 使用共同列作为匹配键
        match_key = list(common_cols)[0]  # 使用第一个共同列
        print(f"使用 '{match_key}' 列作为匹配键")
        df1_matched = df1.copy()
        df2_matched = df2.copy()
        df1_matched['_match_key'] = df1[match_key]
        df2_matched['_match_key'] = df2[match_key]
    else:
        print("警告: 无法确定匹配方式，将按行号匹配")
        df1_matched = df1.copy()
        df2_matched = df2.copy()
        df1_matched['_match_key'] = range(len(df1))
        df2_matched['_match_key'] = range(len(df2))
    
    # 合并数据以比较readTime列
    merged = pd.merge(
        df1_matched[['_match_key', 'readTime']], 
        df2_matched[['_match_key', 'readTime']], 
        on='_match_key', 
        suffixes=('_file1', '_file2'),
        how='outer'
    )
    
    # 找出readTime值不同的行
    # 处理NaN值：如果两个都是NaN，认为相同；否则不同
    # 先创建临时列用于比较
    merged['readTime_file1_temp'] = merged['readTime_file1'].fillna('NaN')
    merged['readTime_file2_temp'] = merged['readTime_file2'].fillna('NaN')
    
    different_mask = merged['readTime_file1_temp'] != merged['readTime_file2_temp']
    different_rows = merged[different_mask].copy()
    
    # 创建只包含两列的结果
    if len(different_rows) > 0:
        # 只保留两列：not_group_readTime 和 NPC_readTime，并计算差值
        result_df = pd.DataFrame({
            'not_group_readTime': different_rows['readTime_file1'],
            'NPC_readTime': different_rows['readTime_file2']
        })
        # 计算差值：file1 - file2
        result_df['difference'] = result_df['not_group_readTime'] - result_df['NPC_readTime']
        
        # 记录过滤前的行数
        total_different = len(result_df)
        
        # 只保留差值大于{threshold}的行
        result_df = result_df[result_df['difference'] > threshold]
        
        print(f"\n找到 {total_different} 行readTime值不同的数据")
        print(f"过滤后保留 {len(result_df)} 行（差值大于{threshold}）")
        print("\n差异统计:")
        print(f"  文件1独有的行: {len(merged[merged['readTime_file1_temp'] == 'NaN'])}")
        print(f"  文件2独有的行: {len(merged[merged['readTime_file2_temp'] == 'NaN'])}")
        print(f"  值不同的行（总数）: {total_different}")
        print(f"  差值大于{threshold}的行: {len(result_df)}")
        
        # 如果过滤后没有数据，输出提示
        if len(result_df) == 0:
            print(f"\n警告: 过滤后没有差值大于{threshold}的数据")
        
        # 输出结果并写出到 CSV（确保写入目录存在）
        if output_file:
            ensure_dir_exists(os.path.dirname(output_file))
            result_df = result_df.astype({
                'not_group_readTime': 'float64',
                'NPC_readTime': 'float64',
                'difference': 'float64'
            }, errors='ignore')
            result_df.to_csv(output_file, index=False, encoding='utf-8-sig', float_format='%.6f')
            print(f"\n结果已保存到: {output_file}")
        else:
            print("\n差异数据详情:")
            print(result_df.to_string())
            # 也保存一个默认文件名
            default_output = "readTime_differences.csv"
            result_df = result_df.astype({
                'not_group_readTime': 'float64',
                'NPC_readTime': 'float64',
                'difference': 'float64'
            }, errors='ignore')
            result_df.to_csv(default_output, index=False, encoding='utf-8-sig', float_format='%.6f')
            print(f"\n结果也已保存到: {default_output}")
    else:
        print("\n两个文件的readTime列值完全相同，没有差异数据")
        if output_file:
            ensure_dir_exists(os.path.dirname(output_file))
            empty_df = pd.DataFrame(columns=['not_group_readTime', 'NPC_readTime', 'difference'])
            empty_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"空结果已保存到: {output_file}")


if __name__ == '__main__':
    threshold = 1E3  # 设定阈值，只有当差值大于此值时才记录
    chip_name_group = ["3DV7", "X3_9070"]
    workload_index_group = [28, 11, 4]
    time_group = ["1m"]
    pe_group = [3000, 4000, 5000, 6000]

    # chip_name_group = ["X3_9070"]
    # workload_index_group = [28, 11, 4]
    # time_group = ["3m"]
    # pe_group = [3000]

    # 定义转换因子：除以10^6 将ps改为us
    CONVERSION_FACTOR = 1e6

    # 示例用法
    # 请修改这两个文件路径为你要比较的实际文件路径
    for chip_name in chip_name_group:
    # for chip_name in ["X3_9070"]:
        summary_rows = []  # 每个chip独立一个汇总列表

        for pe in pe_group:
            for workload_index in workload_index_group:
                for time in time_group:
                    # file1 = f"D:/disk/result/ATC/data_msr/{chip_name}/read_time_not_group_PE{pe}_{workload_index}.csv"
                    file1 = f"D:/disk/result/ATC/data_msr/{chip_name}/read_time_drrm_PE{pe}_{workload_index}.csv"
                    file2 = f"D:/disk/result/ATC/data_msr/{chip_name}/read_time_PE{pe}_{workload_index}.csv"
                    output = f"D:/disk/result/ATC/data_msr/{chip_name}_analysis/readTime_differences_PE{pe}_{workload_index}.csv"
                    output_dir = os.path.dirname(output)
                    ensure_dir_exists(output_dir)
                    compare_readTime(file1, file2, output)
                    
                    # 读取生成的output文件，计算统计值
                    if os.path.exists(output):
                        try:
                            result_df = pd.read_csv(output)
                            if len(result_df) > 0 and 'not_group_readTime' in result_df.columns:
                                # 计算sum和mean
                                not_group_sum = result_df['not_group_readTime'].sum() / CONVERSION_FACTOR
                                NPC_sum = result_df['NPC_readTime'].sum() / CONVERSION_FACTOR
                                difference_sum = result_df['difference'].sum() / CONVERSION_FACTOR
                                
                                not_group_mean = result_df['not_group_readTime'].mean() / CONVERSION_FACTOR
                                NPC_mean = result_df['NPC_readTime'].mean() / CONVERSION_FACTOR
                                difference_mean = result_df['difference'].mean() / CONVERSION_FACTOR

                                # 计算improve_rate = sum(difference) / sum(not_group_readTime)
                                improve_rate = difference_sum / not_group_sum if not_group_sum > 0 else 0
                                
                                # 创建汇总行
                                row_name = f"PE{pe}_{time}_{workload_index}"
                                summary_rows.append({
                                    'row_name': row_name,
                                    'not_group_readTime_sum': not_group_sum,
                                    'NPC_readTime_sum': NPC_sum,
                                    'difference_sum': difference_sum,
                                    'not_group_readTime_mean': not_group_mean,
                                    'NPC_readTime_mean': NPC_mean,
                                    'difference_mean': difference_mean,
                                    'improve_rate': improve_rate
                                })
                        except Exception as e:
                            print(f"读取或处理文件 {output} 时出错: {e}")
        
        # 为当前chip创建汇总表格
        if summary_rows:
            summary_df = pd.DataFrame(summary_rows)
            summary_df.set_index('row_name', inplace=True)
            
            # 确保数值列是正确的数值类型，避免WPS中显示单引号
            numeric_cols = ['not_group_readTime_sum', 'NPC_readTime_sum', 'difference_sum',
                           'not_group_readTime_mean', 'NPC_readTime_mean', 'difference_mean', 'improve_rate']
            for col in numeric_cols:
                if col in summary_df.columns:
                    summary_df[col] = pd.to_numeric(summary_df[col], errors='coerce')
            
            # 保存汇总结果，文件名包含chip_name
            summary_output = f"D:/disk/result/ATC/data_msr/{chip_name}_summary_readTime_statistics_pe.csv"
            ensure_dir_exists(os.path.dirname(summary_output))
            summary_df.to_csv(summary_output, encoding='utf-8-sig', float_format='%.6f')
            print(f"\n[{chip_name}] 汇总统计结果已保存到: {summary_output}")
            # print(f"\n[{chip_name}] 汇总统计预览:")
            # print(summary_df.to_string())
        else:
            print(f"\n[{chip_name}] 没有找到有效数据，未生成汇总文件")


