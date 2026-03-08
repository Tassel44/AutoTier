import pandas as pd
import numpy as np
import time
import random


def generate_mock_data(filename='mock_file_data.csv', num_files=5000):
    print(f"正在生成 {num_files} 条模拟数据...")

    current_time = time.time()
    data = []

    # === 场景设计：我们需要制造几类典型数据 ===

    # 1.【近期热数据 - 视频/大文件】
    # 特征：访问时间 < 7天, 大小 100MB - 10GB
    for i in range(int(num_files * 0.1)):  # 占比 10%
        days_ago = random.uniform(0, 7)
        size_bytes = random.randint(100 * 1024 ** 2, 10 * 1024 ** 3)
        data.append([f"E:\\Mock\\Hot_Video_{i}.mp4", size_bytes, current_time - days_ago * 86400])

    # 2.【近期热数据 - 图片/文档】
    # 特征：访问时间 < 7天, 大小 10KB - 5MB
    for i in range(int(num_files * 0.2)):  # 占比 20%
        days_ago = random.uniform(0, 7)
        size_bytes = random.randint(10 * 1024, 5 * 1024 ** 2)
        data.append([f"E:\\Mock\\Hot_Doc_{i}.jpg", size_bytes, current_time - days_ago * 86400])

    # 3.【中期温数据 - 项目文件】
    # 特征：访问时间 30 - 90天, 大小随机
    for i in range(int(num_files * 0.3)):  # 占比 30%
        days_ago = random.uniform(30, 90)
        size_bytes = random.randint(1 * 1024 ** 2, 500 * 1024 ** 2)
        data.append([f"E:\\Mock\\Warm_Project_{i}.zip", size_bytes, current_time - days_ago * 86400])

    # 4.【远期冷数据 - 备份归档】
    # 特征：访问时间 > 180天, 大小随机
    for i in range(int(num_files * 0.4)):  # 占比 40%
        days_ago = random.uniform(180, 1000)  # 半年到三年
        size_bytes = random.randint(1 * 1024, 2 * 1024 ** 3)
        data.append([f"E:\\Mock\\Cold_Backup_{i}.bak", size_bytes, current_time - days_ago * 86400])

    # 转为 DataFrame 并打乱顺序
    df = pd.DataFrame(data, columns=['filepath', 'size_bytes', 'atime'])
    df = df.sample(frac=1).reset_index(drop=True)

    # 保存
    df.to_csv(filename, index=False)
    print(f"模拟数据已保存至: {filename}")

if __name__ == "__main__":
    generate_mock_data()