# AutoTier: Adaptive Tiered Storage System

## 📖 项目简介 (About)
AutoTier 是一个基于机器学习的智能文件分级与自动化迁移引擎。针对工作站中“海量碎片文件”与“巨型媒体素材”共存的混合负载场景，本项目通过参数自适应的加权 K-Means 聚类算法，有效消除了传统算法中的“大文件偏见”，实现冷热数据的自动化分层与物理迁移。

## ✨ 核心特性 (Features)
* **🚀 高性能数据采集**：采用显式栈非递归 DFS 遍历与 `os.scandir`，消除深层目录栈溢出风险；结合双缓冲写入机制，大幅提升百万级文件元数据的 I/O 吞吐量。
* **🧠 自适应 K-Means 聚类**：引入时间特征权重动态寻优机制，基于基准热数据的召回率反馈（Recall ≥ 0.99）自动修正聚类边界，精准分离高频文件与低频冷备。
* **📊 鲁棒的特征工程**：利用 Log10 对数变换与 Z-Score 标准化，统一文件大小与时间戳量纲，跨越数据形态学鸿沟。
* **🛡️ 安全的物理迁移**：内置 `Dry-Run` 预演模式支持人工审计，并提供基于增量后缀的防冲突重命名策略，确保迁移过程数据零丢失。

## 🛠️ 技术栈 (Tech Stack)
* **语言**: Python 3.12+
* **核心算法**: `scikit-learn` (K-Means), `numpy`, `pandas`
* **可视化**: `matplotlib`, `seaborn`

## 🚀 快速开始 (Getting Started)

### 1. 安装依赖
pip install pandas numpy scikit-learn matplotlib seaborn

### 2. 配置存储策略
在 AutoFileOrganizer.py 中修改你本地的目标存储路径：
TARGET_DIRS = {
    'Hot': r'E:\Storage_Pool\01_Hot_SSD',
    'Warm': r'E:\Storage_Pool\02_Warm_HDD',
    'Cold': r'E:\Storage_Pool\03_Cold_Archive'
}

### 3. 运行模式配置
建议首次运行时开启预演模式，确认分类无误后再执行真实物理移动：
# True = 模拟运行 (仅输出日志不移动文件); False = 执行物理迁移
DRY_RUN = True 

### 4. 执行全链路梳理
先运行采集器生成元数据，再运行核心引擎进行聚类与迁移：
python Collector.py
python AutoFileOrganizer.py

## 📈 算法效果对比
系统通过参数自适应扫描（Adaptive Parameter Scanning），将标准 K-Means 受“文件大小”主导的水平决策边界，强行修正为受“访问时间”主导的垂直边界。有效解决了近期修改的轻量级配置文件被误判为冷数据的问题。
