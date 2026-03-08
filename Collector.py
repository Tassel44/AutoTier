import os
import time
import csv
import pathlib


class FileScanner:
    def __init__(self, save_path='real_file_data.csv', batch_size=10000):
        self.save_path = save_path
        self.batch_size = batch_size
        self.buffer = []
        self.total_scanned = 0
        self.start_time = 0

        # 初始化 CSV 文件头
        self._init_csv()

    def _init_csv(self):
        """初始化CSV文件，写入表头"""
        headers = ['filepath', 'size_bytes', 'atime', 'mtime', 'ctime', 'extension']
        try:
            with open(self.save_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        except PermissionError:
            print(f"错误：无法写入 {self.save_path}，请关闭该文件后重试。")
            exit()

    def flush_buffer(self):
        """将缓冲区数据批量写入CSV"""
        if not self.buffer:
            return

        try:
            with open(self.save_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerows(self.buffer)
        except Exception as e:
            print(f"写入错误: {e}")
            return

        self.total_scanned += len(self.buffer)
        print(f"\r--> 已扫描并保存: {self.total_scanned} 个文件...", end="")
        self.buffer.clear()  # 清空列表，释放内存

    def scan_directory(self, root_dir):
        print(f"开始扫描目录: {root_dir}")
        self.start_time = time.time()

        # 使用栈实现非递归遍历，防止目录过深爆栈
        # stack 存储待扫描的目录路径
        stack = [root_dir]

        while stack:
            current_dir = stack.pop()

            try:
                # os.scandir 上下文管理器，自动关闭句柄
                with os.scandir(current_dir) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            try:
                                # entry.stat() 在 Windows 上利用了缓存，比 os.stat(path) 快得多
                                stats = entry.stat()

                                # 构造轻量级元组 (Tuple) 比 字典 (Dict) 更省内存
                                row = (
                                    entry.path,
                                    stats.st_size,
                                    stats.st_atime,
                                    stats.st_mtime,
                                    stats.st_ctime,
                                    pathlib.Path(entry.name).suffix.lower()
                                )
                                self.buffer.append(row)

                                if len(self.buffer) >= self.batch_size:
                                    self.flush_buffer()
                            except (PermissionError, FileNotFoundError):
                                continue
            except (PermissionError, FileNotFoundError):
                continue
            except Exception as e:
                print(f"\n扫描目录出错 {current_dir}: {e}")

        # 处理剩余数据
        self.flush_buffer()
        self._print_summary()

    def _print_summary(self):
        end_time = time.time()
        duration = end_time - self.start_time
        print(f"\n\n{'=' * 30}")
        print(f"扫描完成！")
        print(f"总耗时: {duration:.2f} 秒")
        print(f"总文件数: {self.total_scanned}")
        if duration > 0:
            print(f"扫描速度: {self.total_scanned / duration:.0f} 文件/秒")
        print(f"数据已保存至: {os.path.abspath(self.save_path)}")
        print(f"{'=' * 30}")


if __name__ == "__main__":
    # 使用 raw string (r"...") 避免路径转义问题
    target_dir = r"E:\code\.vscode"

    if os.path.exists(target_dir):
        scanner = FileScanner()
        scanner.scan_directory(target_dir)
    else:
        print("错误：目标目录不存在，请检查路径。")