import numpy as np
import random
from collections import Counter
from scipy import stats
from scipy.optimize import minimize
import pandas as pd

def calculate_optimal_distribution(total_count, target_values=[1, 3, 6, 12], target_mean=5.5):
    """
    计算最优分布，使得离散分布尽可能接近正态分布
    
    参数:
    - total_count: 变量总数
    - target_values: 目标值列表
    - target_mean: 目标均值
    
    返回:
    - 每个值对应的数量字典
    """
    # 定义优化目标函数：最小化与正态分布的差异
    def objective(probs):
        # 确保概率和为1
        probs = np.abs(probs)  # 避免负概率
        probs = probs / np.sum(probs)
        
        # 计算离散分布的均值和方差
        mean = np.sum(np.array(target_values) * probs)
        variance = np.sum((np.array(target_values) - mean)**2 * probs)
        
        # 计算与目标正态分布的差异
        # 使用KL散度作为差异度量
        # 这里简化为均值和方差的差异
        mean_diff = (mean - target_mean)**2
        # 假设目标方差为1.5^2=2.25 (可以根据需要调整)
        target_variance = 2.25
        var_diff = (variance - target_variance)**2
        
        return mean_diff + 0.5 * var_diff
    
    # 初始概率分布（均匀分布）
    initial_probs = np.ones(len(target_values)) / len(target_values)
    
    # 约束条件：概率和为1
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    
    # 边界条件：概率非负
    bounds = [(0.001, 1) for _ in range(len(target_values))]
    
    # 优化
    result = minimize(objective, initial_probs, method='SLSQP', 
                     bounds=bounds, constraints=constraints)
    
    if result.success:
        optimal_probs = result.x
        optimal_probs = optimal_probs / np.sum(optimal_probs)  # 确保和为1
        
        # 计算每个值对应的数量
        counts = {}
        for i, value in enumerate(target_values):
            count = round(optimal_probs[i] * total_count)
            counts[value] = max(1, count)  # 确保每个值至少有一个
        
        # 调整总数以确保总和为total_count
        current_total = sum(counts.values())
        if current_total != total_count:
            # 找到概率最大的值，调整其数量
            max_prob_value = max(zip(optimal_probs, target_values), key=lambda x: x[0])[1]
            counts[max_prob_value] += total_count - current_total
        
        return counts
    else:
        # 如果优化失败，使用默认分布
        print("优化失败，使用默认分布")
        return {1: 2, 3: 82, 6: 427, 12: 1}

def assign_values_with_distribution(total_count, target_values=[1, 3, 6, 12], target_mean=5.5):
    """
    根据计算出的分布对变量进行赋值
    
    参数:
    - total_count: 变量总数
    - target_values: 目标值列表
    - target_mean: 目标均值
    
    返回:
    - 赋值后的变量列表
    """
    # 计算最优分布
    distribution = calculate_optimal_distribution(total_count, target_values, target_mean)
    
    print("计算出的分布:")
    for value, count in sorted(distribution.items()):
        percentage = (count / total_count) * 100
        print(f"  值 {value}: {count} 个 ({percentage:.2f}%)")
    
    # 创建变量列表
    variables = []
    for value, count in distribution.items():
        variables.extend([value] * count)
    
    # 随机打乱顺序
    random.shuffle(variables)
    
    return variables

def analyze_distribution(variables, title="分布分析"):
    """
    分析分布情况（不包含可视化）
    """
    # 统计各值出现次数
    counter = Counter(variables)
    total = len(variables)
    
    print(f"\n{title}:")
    print(f"总变量数: {total}")
    print("值分布:")
    for value in sorted(counter.keys()):
        count = counter[value]
        percentage = (count / total) * 100
        print(f"  值 {value}: {count} 个 ({percentage:.2f}%)")
    
    # 计算统计量
    mean = np.mean(variables)
    std = np.std(variables)
    print(f"均值: {mean:.3f}")
    print(f"标准差: {std:.3f}")
    
    return mean, std

def test_subsets(variables, num_subsets=5, subset_size=50):
    """
    测试随机子集的分布（不包含可视化）
    """
    print(f"\n{'='*50}")
    print(f"测试 {num_subsets} 个大小为 {subset_size} 的随机子集:")
    print('='*50)
    
    subset_means = []
    subset_stds = []
    
    for i in range(num_subsets):
        # 随机选择子集
        subset = random.sample(variables, subset_size)
        
        # 分析子集分布
        mean, std = analyze_distribution(subset, f"随机子集 {i+1}")
        subset_means.append(mean)
        subset_stds.append(std)
    
    # 分析子集统计量的分布
    print(f"\n子集统计量分析:")
    print(f"子集均值范围: {min(subset_means):.3f} - {max(subset_means):.3f}")
    print(f"子集标准差范围: {min(subset_stds):.3f} - {max(subset_stds):.3f}")
    
    return subset_means, subset_stds

def save_to_csv(variables, filename="block_rt_assignment.csv"):
    """
    将变量分配结果保存为CSV文件（包含行索引）
    
    参数:
    - variables: 变量值列表
    - filename: 输出文件名
    """
    # 创建DataFrame，包含行索引
    df = pd.DataFrame({
        'blockid': range(1, len(variables) + 1),
        'rt': variables
    })
    
    # 保存为CSV，包含行索引
    df.to_csv(filename, index=True, index_label='')
    print(f"\n结果已保存到 {filename}")
    
    # 显示文件前几行（包含行索引）
    print("\nCSV文件前10行预览 (包含行索引):")
    print(df.head(10))
    
    return df

def main():
    # 设置随机种子以便结果可重现
    random.seed(42)
    np.random.seed(42)
    
    # 参数设置
    total_count = 512
    target_values = [1, 3, 6, 12]
    target_mean = float(np.mean(target_values))
    # target_mean = 5.5
    
    print(f"\n开始对{total_count}个变量进行正态分布赋值...")
    print(f"目标值: {target_values}")
    print(f"目标均值: {target_mean}")
    
    # 1. 生成变量赋值
    variables = assign_values_with_distribution(total_count, target_values, target_mean)
    
    # 2. 分析整体分布
    overall_mean, overall_std = analyze_distribution(variables, f"整体分布 ({total_count}个变量)")
    
    # 3. 测试不同大小的子集
    # subset_sizes = [min(50, total_count//10), min(100, total_count//5), min(200, total_count//2)]
    # subset_sizes = [size for size in subset_sizes if size >= 10]  # 确保子集大小合理
    
    # for size in subset_sizes:
    #     if size <= len(variables):
    #         test_subsets(variables, num_subsets=3, subset_size=size)
    
    # 4. 正态性检验
    print(f"\n正态性检验 (Shapiro-Wilk检验):")
    if len(variables) <= 5000:  # Shapiro-Wilk适用于小样本
        stat, p_value = stats.shapiro(variables)
        print(f"统计量: {stat:.4f}, p值: {p_value:.4f}")
        if p_value > 0.05:
            print("不能拒绝正态分布的原假设 (p > 0.05)")
        else:
            print("拒绝正态分布的原假设 (p <= 0.05)")
    
    # 5. 保存结果到CSV文件
    df = save_to_csv(variables, "E:/code/vsc/chips/simplessd/block_rt_assignment.csv")
    
    return variables, df

# 运行主程序
if __name__ == "__main__":
    assigned_variables, df = main()
    
    # 显示前20个变量的值作为示例
    print(f"\n前20个变量的值:")
    for i, value in enumerate(assigned_variables[:20]):
        print(f"变量{i+1}: {value}", end=" | ")
        if (i + 1) % 5 == 0:
            print()