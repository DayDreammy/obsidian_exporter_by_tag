#!/usr/bin/env python3
"""
EPUB合并脚本
直接合并现有的EPUB文件，避免重新从markdown生成
"""

from pathlib import Path
import subprocess
import sys
from datetime import datetime

# =============================================================================
# 配置
# =============================================================================

# 输入目录（包含要合并的EPUB文件）
INPUT_DIRECTORY = Path("./output")

# 输出文件配置
OUTPUT_FILENAME = "Obsidian_完整合集_合并版.epub"
OUTPUT_DIRECTORY = Path("./output")

# 要合并的EPUB文件顺序（按逻辑顺序排列）
EPUB_FILES_ORDER = [
    "Obsidian_0-致读者.epub",
    "Obsidian_1-个人成长.epub",
    "Obsidian_2-亲密关系.epub",
    "Obsidian_3-家庭伦理.epub",
    "Obsidian_4-职业发展.epub",
    "Obsidian_5-社会科学.epub",
    "Obsidian_6-文化艺术.epub",
    "Obsidian_7-科学与技术.epub",
    "Obsidian_8-世界史地.epub",
    "Obsidian__专题合集.epub",
    "Obsidian__其它.epub",
    "Obsidian_【答集】.epub",
]

# =============================================================================
# 核心函数
# =============================================================================


def find_existing_epub_files(input_dir):
    """
    查找现有的EPUB文件

    Args:
        input_dir (Path): 输入目录

    Returns:
        list: 找到的EPUB文件路径列表
    """
    found_files = []
    missing_files = []

    print(f"正在检查目录: {input_dir.absolute()}")

    for filename in EPUB_FILES_ORDER:
        file_path = input_dir / filename
        if file_path.exists():
            found_files.append(file_path)
            file_size = file_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"✅ 找到: {filename} ({size_mb:.2f} MB)")
        else:
            missing_files.append(filename)
            print(f"❌ 缺失: {filename}")

    return found_files, missing_files


def merge_epub_files(epub_files, output_path):
    """
    使用Pandoc合并EPUB文件

    Args:
        epub_files (list): 要合并的EPUB文件路径列表
        output_path (Path): 输出文件路径

    Returns:
        bool: 是否成功合并
    """
    if not epub_files:
        print("错误：没有找到要合并的EPUB文件")
        return False

    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n正在合并 {len(epub_files)} 个EPUB文件...")

        # 准备Pandoc命令
        file_paths = [str(file_path) for file_path in epub_files]

        pandoc_cmd = [
            "pandoc",
            # 输入文件（EPUB格式）
            *file_paths,
            # 输出格式和文件
            "-o", str(output_path),
            # EPUB相关选项
            "--to=epub3",
            # 目录选项
            "--toc",
            "--toc-depth=3",
            # 标题和作者信息
            "--metadata=title:Obsidian完整知识合集（合并版）",
            "--metadata=author:知识整理者",
            f"--metadata=date:{datetime.now().strftime('%Y-%m-%d')}",
            # 中文支持
            "--variable=lang:zh-CN",
        ]

        print(f"输出路径: {output_path.absolute()}")
        print(
            f"合并命令: pandoc {' '.join(file_paths[0:2])}... -> {output_path.name}")

        # 执行Pandoc命令
        print(f"正在执行合并（预计需要1-3分钟）...")
        result = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时，合并EPUB应该比较快
        )

        if result.returncode == 0:
            print("✅ EPUB文件合并成功!")

            # 显示文件大小
            if output_path.exists():
                file_size = output_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                print(f"📏 合并后文件大小: {size_mb:.2f} MB")

            return True
        else:
            print("❌ EPUB文件合并失败!")
            print(f"错误信息: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ EPUB合并超时!")
        return False
    except Exception as e:
        print(f"❌ 合并EPUB时出错: {e}")
        return False


def calculate_total_size(epub_files):
    """
    计算总文件大小

    Args:
        epub_files (list): EPUB文件路径列表

    Returns:
        float: 总大小（MB）
    """
    total_size = 0
    for file_path in epub_files:
        if file_path.exists():
            total_size += file_path.stat().st_size

    return total_size / (1024 * 1024)


# =============================================================================
# 主程序
# =============================================================================

def main():
    """主程序"""
    print("=" * 80)
    print("EPUB合并脚本 - 快速合并现有EPUB文件")
    print("=" * 80)

    # 检查现有EPUB文件
    found_files, missing_files = find_existing_epub_files(INPUT_DIRECTORY)

    if not found_files:
        print("\n❌ 没有找到任何EPUB文件！")
        print("请先运行 obsidian_export.py 生成分章节的EPUB文件。")
        return

    # 显示统计信息
    print(f"\n" + "=" * 60)
    print("合并统计:")
    print("=" * 60)
    print(f"找到的文件: {len(found_files)} 个")
    print(f"缺失的文件: {len(missing_files)} 个")

    if missing_files:
        print(f"\n⚠️  缺失的文件:")
        for filename in missing_files:
            print(f"   - {filename}")
        print(f"\n将只合并找到的文件。")

    total_size = calculate_total_size(found_files)
    print(f"预计合并后大小: ~{total_size:.2f} MB")

    # 询问是否继续
    print(f"\n是否继续合并？")
    response = input("按 Enter 继续，或输入 'n' 取消: ").strip().lower()

    if response == 'n':
        print("取消合并。")
        return

    # 执行合并
    output_path = OUTPUT_DIRECTORY / OUTPUT_FILENAME
    success = merge_epub_files(found_files, output_path)

    if success:
        print(f"\n🎉 合并完成!")
        print(f"📁 合并文件: {output_path.absolute()}")
        print(f"📊 合并了 {len(found_files)} 个EPUB文件")

        # 对比原始大小和合并后大小
        if output_path.exists():
            merged_size = output_path.stat().st_size / (1024 * 1024)
            print(f"📏 原始总大小: {total_size:.2f} MB")
            print(f"📏 合并后大小: {merged_size:.2f} MB")

            # 计算压缩比例
            if total_size > 0:
                compression_ratio = (1 - merged_size / total_size) * 100
                if compression_ratio > 0:
                    print(f"💾 压缩了 {compression_ratio:.1f}%")
                else:
                    print(f"📈 大小增加了 {abs(compression_ratio):.1f}%")
    else:
        print(f"\n❌ 合并失败")


if __name__ == "__main__":
    main()
