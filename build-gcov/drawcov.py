#! /usr/bin/env python3

import sys
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from collections import defaultdict

col_names = ["timestamp", "lines_hit", "lines_total", "functions_hit", "functions_total", "branches_hit", "branches_total"]

parser = argparse.ArgumentParser()

parser.add_argument("-f", "--file", action="append", required=True, help="CSV file to read")
parser.add_argument("-n", "--name", action="append", required=True, help="Name of the coverage")
parser.add_argument("-o", "--output", required=True, help="Output file name")
parser.add_argument("--title", default="Coverage Analysis", help="Title of the plot")

def load_data(file):
    """
    读取并处理单个CSV文件，返回处理后的 time_minutes 和 branches_hit 数据。
    """
    try:
        data = pd.read_csv(file, header=0, names=col_names)
        # 去掉最后一行
        data = data.iloc[:-1]
        
        # 时间戳处理
        data["timestamp"] = data["timestamp"].str.replace("_", " ")
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        
        # 计算相对时间（分钟）
        start_time = data["timestamp"].iloc[0]
        data["time_minutes"] = (data["timestamp"] - start_time) / pd.Timedelta(minutes=1)
        
        return data[["time_minutes", "branches_hit"]]
    except Exception as e:
        # print(f"Error reading file {file}: {e}", file=sys.stderr)
        return None

def main():
    args = parser.parse_args()
    files = args.file
    names = args.name
    output = args.output
    
    if len(files) != len(names):
        parser.error("Number of files and names must be the same")
        
    # --- 1. 数据加载、分组，并确定统一的时间轴长度 ---
    groups = defaultdict(list)
    max_total_time = 0.0
    
    for file, name in zip(files, names):
        df = load_data(file)
        if df is not None and not df.empty:
            groups[name].append(df)
            max_total_time = max(max_total_time, df["time_minutes"].max())

    if not groups:
        print("No valid data files were loaded. Exiting.")
        sys.exit(1)
        
    # 创建一个统一的、高密度的公共时间轴 (500个插值点)
    global_common_time = np.linspace(0, max_total_time, 500)
    # 用于存储插值后的均值曲线，供分析使用
    analysis_results = {}

    # --- 2. 准备画布、绘图 (含高分辨率) ---
    # **设置 dpi=300 提高分辨率**
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300) 
    ax.set_title(args.title)
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Branches Hit (Mean)")
    
    # --- 3. 遍历分组，计算均值/方差并绘图 ---
    for name, dfs in groups.items():
        interpolated_y = []
        
        # 将该组所有运行结果插值到公共时间轴上
        for df in dfs:
            # np.interp 会使用该运行的最后已知值来填充超出其最大时间后的区域
            y_interp = np.interp(global_common_time, df["time_minutes"], df["branches_hit"])
            interpolated_y.append(y_interp)
        
        y_matrix = np.array(interpolated_y)
        
        # 计算均值和标准差
        y_mean = np.mean(y_matrix, axis=0)
        y_std = np.std(y_matrix, axis=0)
        
        # 存储均值曲线
        analysis_results[name] = y_mean
        
        # 绘图
        line, = ax.plot(global_common_time, y_mean, label=name)
        
        # 绘制阴影区域 (均值 ± 标准差)
        if len(dfs) > 1:
            ax.fill_between(global_common_time, 
                            y_mean - y_std, 
                            y_mean + y_std, 
                            color=line.get_color(), 
                            alpha=0.2)
        
    ax.legend()
    plt.savefig(output)
    plt.close()
    print(f"Plot saved to {output}")
    
    # # --- 4. 两组数据性能分析 (仅限两组) ---
    
    # group_names = list(analysis_results.keys())
    
    # if len(group_names) == 2:
    #     name_A, name_B = group_names[0], group_names[1]
    #     mean_A = analysis_results[name_A]
    #     mean_B = analysis_results[name_B]
        
    #     print("\n--- 两组数据性能分析 ---")
    #     print(f"对比组 1: **{name_A}** (基于 {len(groups[name_A])} 次运行的平均值)")
    #     print(f"对比组 2: **{name_B}** (基于 {len(groups[name_B])} 次运行的平均值)")
    #     print("------------------------")
        
    #     # 1. 最终数值
    #     final_A = mean_A[-1]
    #     final_B = mean_B[-1]
        
    #     print("🚀 最终分支命中数 (Final Branches Hit):")
    #     print(f"  - **{name_A}**: {final_A:.2f}")
    #     print(f"  - **{name_B}**: {final_B:.2f}")
        
    #     # 2. 最大差距及前五分析
        
    #     # 计算绝对差距
    #     diff = np.abs(mean_A - mean_B)
        
    #     # 获取排序后的索引 (降序)
    #     sorted_indices = np.argsort(diff)[::-1]
        
    #     # 限制为前五个点
    #     top_N = 5
    #     top_indices = sorted_indices[:top_N]
        
    #     print(f"\n📈 **前 {top_N} 大差距分析** (基于平均曲线的绝对差):")
        
    #     # 打印表头
    #     print(" | 差距排名 | 差异值 (分支数) | 时间 (分钟) | 领先组 |")
    #     print(" | :------: | :-------------: | :---------: | :----: |")
        
    #     # 遍历前 N 个最大差距点
    #     for rank, index in enumerate(top_indices, 1):
    #         diff_value = diff[index]
    #         time_value = global_common_time[index]
            
    #         value_at_point_A = mean_A[index]
    #         value_at_point_B = mean_B[index]
            
    #         leading_group = name_A if value_at_point_A > value_at_point_B else name_B
            
    #         # 打印表格行
    #         print(f" |    {rank}     |     {diff_value:.2f}      |   {time_value:.2f}    |  {leading_group} |")
            
    # elif len(group_names) > 2:
    #     print("\n📢 注意: 检测到超过两组数据。已绘制所有曲线，但未执行两组对比分析。")
        
    # else:
    #     print("\n📢 注意: 只有一组或没有有效数据，跳过两组对比分析。")

if __name__ == "__main__":
    main()