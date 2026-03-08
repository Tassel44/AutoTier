import pandas as pd
import numpy as np
import shutil
import os
import time
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ==========================================
# 🛠️ 用户配置区
# ==========================================
CSV_FILE_PATH = 'real_file_data.csv'

TARGET_DIRS = {
    'Hot': r'E:\Storage_Pool\01_Hot_SSD',
    'Warm': r'E:\Storage_Pool\02_Warm_HDD',
    'Cold': r'E:\Storage_Pool\03_Cold_Archive'
}

# True = 模拟运行 (推荐); False = 正式移动
DRY_RUN = True
# ==========================================

# --- 全局绘图风格设置  ---
sns.set(style="whitegrid")
plt.rcParams['axes.unicode_minus'] = False
# 优先尝试中文字体，如果系统没有则回退到通用字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']


class AutoFileOrganizer:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.optimal_weight = 1.0

    def _find_optimal_weight(self, df, X_scaled_base):
        """[内部] 自动寻找最佳权重"""
        print("   >>> 正在自动校准算法参数...")

        # 定义我们的目标 (KPI)：希望 30 天以内的文件都被认为是"近期文件"
        recent_mask = df['days_since_access'] <=30
        total_recent = recent_mask.sum()

        # 如果数据里压根没有30天内的文件，直接返回默认权重 5.0
        if total_recent == 0: return 5.0

        for w in np.arange(1.0, 15.5, 1.0):
            X_test = X_scaled_base.copy()
            X_test[:, 0] *= w
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=5)
            labels = kmeans.fit_predict(X_test)

            # 找Hot层 逻辑：计算每个簇的平均“未访问天数”，天数最小的那个簇就是 Hot
            cluster_days_mean = pd.DataFrame({'c': labels, 'd': df['days_since_access']}).groupby('c')['d'].mean()
            hot_cluster_id = cluster_days_mean.idxmin()

            # 算命中率 看看实际上有多少"30天内的文件"被成功分到了这个 Hot 簇里
            recall = (labels[recent_mask] == hot_cluster_id).sum() / total_recent
            # 如果命中率超过 99%，说明这个权重足够好，停止尝试
            if recall >= 0.99:
                print(f"   ✅ 校准完成！最佳时间权重: {w:.1f}")
                return w
        return 15.0

    def analyze_and_classify(self):
        print("-" * 60)
        print("1. 正在加载数据并智能分析...")
        try:
            df = pd.read_csv(self.csv_file)
            df = df[df['size_bytes'] > 0].copy()

            current_time = max(time.time(), df['atime'].max()) + 100
            df['days_since_access'] = (current_time - df['atime']) / (3600 * 24)
            df['log_size'] = np.log10(df['size_bytes'])

            # 数据标准化
            X = df[['days_since_access', 'log_size']].values
            scaler = StandardScaler()
            X_scaled_base = scaler.fit_transform(X)

            # 寻找并应用权重
            self.optimal_weight = self._find_optimal_weight(df, X_scaled_base)
            X_final = X_scaled_base.copy()
            X_final[:, 0] *= self.optimal_weight

            print(f"   执行最终聚类 (Time Weight x {self.optimal_weight})...")
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(X_final)

            # 打标签
            cluster_means = df.groupby('cluster')['days_since_access'].mean().sort_values()
            sorted_clusters = cluster_means.index.tolist()
            tier_map = {sorted_clusters[0]: 'Hot', sorted_clusters[1]: 'Warm', sorted_clusters[2]: 'Cold'}
            df['target_tier'] = df['cluster'].map(tier_map)

            # 输出简报
            print("\n📊 智能分层结果:")
            for tier in ['Hot', 'Warm', 'Cold']:
                subset = df[df['target_tier'] == tier]
                if not subset.empty:
                    print(
                        f"   [{tier:<4}] 文件数: {len(subset):<5} | 范围: {subset['days_since_access'].min():.1f} - {subset['days_since_access'].max():.1f} 天")
            print("-" * 60)
            return df

        except Exception as e:
            print(f"❌ 分析失败: {e}")
            return None

    def visualize_results(self, df):
        """
        🎨 [可视化模块]
        """
        print("\n2. 生成可视化图表...")
        try:
            # 1. 采样 (避免点太多卡顿)
            sample_size = min(5000, len(df))
            plot_data = df.sample(n=sample_size, random_state=42).copy()

            # 2. 标签映射 (为了图例更好看，模仿 Analyzer 的命名)
            # 注意：这里的映射仅用于画图，不影响 target_tier 的逻辑
            display_label_map = {
                'Hot': 'Hot (SSD)',
                'Warm': 'Warm (HDD)',
                'Cold': 'Cold (Archive/Tape)'
            }
            plot_data['Display_Tier'] = plot_data['target_tier'].map(display_label_map)

            # 3. 定义颜色映射 (完全一致的红/橙/蓝)
            palette = {
                'Hot (SSD)': '#ff4d4d',  # 红
                'Warm (HDD)': '#ffad33',  # 橙
                'Cold (Archive/Tape)': '#3399ff'  # 蓝
            }

            # 4. 绘图
            plt.figure(figsize=(12, 7))
            sns.scatterplot(
                data=plot_data,
                x='days_since_access',
                y='log_size',
                hue='Display_Tier',
                palette=palette,
                hue_order=['Hot (SSD)', 'Warm (HDD)', 'Cold (Archive/Tape)'],  # 强制图例排序
                alpha=0.6,
                edgecolor=None
            )

            # 5. 设置标题和标签
            plt.title(f'文件生命周期分层分析 (自适应权重: {self.optimal_weight})', fontsize=14)
            plt.xlabel('距离最后一次访问的天数 (Recency)', fontsize=12)
            plt.ylabel('文件大小 Log10(Bytes)', fontsize=12)

            # 6. 添加参考线和网格
            plt.grid(True, linestyle='--', alpha=0.3)
            plt.tight_layout()

            # 7. 保存图片
            save_name = 'storage_analysis_result.png'
            plt.savefig(save_name, dpi=150)
            print(f"   ✅ 图表已保存为: {save_name}")

        except Exception as e:
            print(f"   ⚠️ 绘图失败: {e}")

    def get_safe_dest_path(self, dest_path):
        if not os.path.exists(dest_path): return dest_path
        base, ext = os.path.splitext(dest_path)
        counter = 1
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path): return new_path
            counter += 1

    def execute_move(self, df):
        mode_str = "🛑 模拟运行 (DRY RUN)" if DRY_RUN else "🚀 正式执行 (REAL RUN)"
        print(f"\n3. 开始文件整理... 当前模式: {mode_str}")

        stats = {'Success': 0, 'Fail': 0, 'Skipped': 0}

        if not DRY_RUN:
            for path in TARGET_DIRS.values():
                if not os.path.exists(path): os.makedirs(path)

        for index, row in df.iterrows():
            src_path = row['filepath']
            tier = row['target_tier']
            dest_root = TARGET_DIRS.get(tier)

            if not os.path.exists(src_path) or os.path.dirname(src_path) == dest_root:
                stats['Skipped'] += 1
                continue

            filename = os.path.basename(src_path)

            try:
                if DRY_RUN:
                    if stats['Success'] < 5 or stats['Success'] % 200 == 0:
                        print(f"   [模拟] {filename} -> {tier}")
                    stats['Success'] += 1
                else:
                    final_dest = self.get_safe_dest_path(os.path.join(dest_root, filename))
                    shutil.move(src_path, final_dest)
                    stats['Success'] += 1
                    if stats['Success'] % 100 == 0: print(f"   已处理 {stats['Success']} 个...")
            except:
                stats['Fail'] += 1

        print(f"\n📋 总结: 成功 {stats['Success']} | 失败 {stats['Fail']} | 跳过 {stats['Skipped']}")
        if DRY_RUN: print("💡 满意请将代码中 DRY_RUN 改为 False。")


if __name__ == "__main__":
    organizer = AutoFileOrganizer(CSV_FILE_PATH)
    df_result = organizer.analyze_and_classify()

    if df_result is not None:
        # 画图
        organizer.visualize_results(df_result)
        # 执行移动
        organizer.execute_move(df_result)