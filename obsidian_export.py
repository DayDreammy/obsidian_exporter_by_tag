#!/usr/bin/env python3
"""
Obsidian标签化导出脚本
优化版：自动层级目录生成，支持Tag和Category两种模式
"""

from pathlib import Path
import sys
import re
import subprocess
import json
from datetime import datetime
from collections import defaultdict

# =============================================================================
# 配置
# =============================================================================

# Obsidian vault路径
VAULT_PATH = Path("./Sth-Matters")

# 标签前缀
TAG_PREFIX = "> Tag:"
CATEGORY_PREFIX = "> Category:"

# 输出文件配置
OUTPUT_FILENAME = "Obsidian_导出_合集.epub"
OUTPUT_DIRECTORY = Path("./output")
INDEX_FILENAME = "chapter_index.json"

# =============================================================================
# 核心函数
# =============================================================================


def find_all_md_files(vault_path):
    """
    递归查找vault中的所有.md文件

    Args:
        vault_path (Path): Obsidian vault的路径

    Returns:
        list: 所有.md文件的路径列表
    """
    if not vault_path.exists():
        print(f"错误：路径 {vault_path} 不存在")
        return []

    if not vault_path.is_dir():
        print(f"错误：路径 {vault_path} 不是目录")
        return []

    md_files = []

    # 使用递归glob模式查找所有.md文件
    for md_file in vault_path.rglob("*.md"):
        # 跳过.obsidian目录中的文件
        if ".obsidian" not in str(md_file):
            md_files.append(md_file)

    return sorted(md_files)


def extract_metadata_from_file(file_path, metadata_type="tag"):
    """
    从markdown文件中提取元数据（标签或分类）

    Args:
        file_path (Path): markdown文件路径
        metadata_type (str): "tag" 或 "category"

    Returns:
        list: 提取到的元数据列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 根据类型选择前缀
        if metadata_type.lower() == "tag":
            prefix = TAG_PREFIX
            field_name = "标签"
        elif metadata_type.lower() == "category":
            prefix = CATEGORY_PREFIX
            field_name = "分类"
        else:
            raise ValueError(f"不支持的元数据类型: {metadata_type}")

        # 查找元数据行
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(prefix):
                # 提取内容（去掉前缀）
                content_text = line[len(prefix):].strip()

                # 使用正则表达式提取所有以#开头的项目
                items = re.findall(r'#[^\s#]+(?:/[^\s#]+)*', content_text)

                return items

        # 如果没有找到对应行，返回空列表
        return []

    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return []


def parse_hierarchy(item):
    """
    解析项目的层级结构

    Args:
        item (str): 项目字符串，如 "#1-个人成长/1-内在建设/1C-自强"

    Returns:
        tuple: (完整项目, 层级列表, 排序键)
    """
    # 去掉开头的#
    clean_item = item[1:] if item.startswith('#') else item

    # 按/分割获取层级
    levels = clean_item.split('/')

    # 生成排序键（用于自然排序）
    # 提取每个层级中的数字和字母部分进行排序
    sort_key = []
    for level in levels:
        # 提取数字部分和文字部分分别处理
        import re
        # 匹配开头的数字、字母、中文等
        match = re.match(r'^(\d*)([A-Za-z]*)(.*)$', level)
        if match:
            num_part, alpha_part, text_part = match.groups()
            # 构建排序键：(数字部分, 字母部分, 文字部分)
            sort_key.append((
                int(num_part) if num_part else 999999,  # 没有数字的排到后面
                alpha_part,
                text_part
            ))
        else:
            sort_key.append((999999, '', level))

    return item, levels, tuple(sort_key)


def collect_all_metadata(files_with_metadata):
    """
    收集所有元数据并进行层级解析和排序

    Args:
        files_with_metadata (list): 包含(文件路径, 元数据列表)的元组列表

    Returns:
        tuple: (排序后的元数据列表, 元数据层级字典, 文件元数据映射)
    """
    all_items = set()
    item_hierarchy = {}
    file_item_mapping = {}

    # 收集所有元数据项目
    for file_path, items in files_with_metadata:
        if items:
            file_item_mapping[file_path] = items
            for item in items:
                all_items.add(item)

    print(f"总共发现 {len(all_items)} 个不同的项目")

    # 解析层级
    item_info = []
    for item in all_items:
        full_item, levels, sort_key = parse_hierarchy(item)
        item_info.append((full_item, levels, sort_key))
        item_hierarchy[full_item] = levels

    # 按排序键排序
    item_info.sort(key=lambda x: x[2])
    sorted_items = [info[0] for info in item_info]

    return sorted_items, item_hierarchy, file_item_mapping


def generate_chapter_structure(sorted_items, item_hierarchy, file_item_mapping, metadata_type):
    """
    生成章节结构

    Args:
        sorted_items (list): 排序后的元数据列表
        item_hierarchy (dict): 元数据层级字典
        file_item_mapping (dict): 文件元数据映射
        metadata_type (str): "tag" 或 "category"

    Returns:
        dict: 章节结构字典
    """
    chapter_structure = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "metadata_type": metadata_type,
            "total_items": len(sorted_items),
            "total_files": len(file_item_mapping)
        },
        "chapters": []
    }

    # 按元数据组织文件
    for item in sorted_items:
        levels = item_hierarchy[item]

        # 查找使用此元数据的文件
        files_with_item = []
        for file_path, file_items in file_item_mapping.items():
            if item in file_items:
                files_with_item.append(str(file_path))

        if files_with_item:  # 只包含有文件的项目
            chapter_info = {
                "item": item,
                "levels": levels,
                "level_1": levels[0] if len(levels) > 0 else "",
                "level_2": levels[1] if len(levels) > 1 else "",
                "level_3": levels[2] if len(levels) > 2 else "",
                "level_4": levels[3] if len(levels) > 3 else "",
                "files": files_with_item,
                "file_count": len(files_with_item)
            }
            chapter_structure["chapters"].append(chapter_info)

    return chapter_structure


def save_chapter_index(chapter_structure, output_dir, metadata_type):
    """
    保存章节索引到JSON文件

    Args:
        chapter_structure (dict): 章节结构
        output_dir (Path): 输出目录
        metadata_type (str): "tag" 或 "category"

    Returns:
        Path: 索引文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    index_filename = f"chapter_index_{metadata_type}.json"
    index_path = output_dir / index_filename

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(chapter_structure, f, ensure_ascii=False, indent=2)

    print(f"✅ 章节索引已保存到: {index_path}")
    return index_path


def print_chapter_summary(chapter_structure, metadata_type):
    """
    打印章节结构摘要

    Args:
        chapter_structure (dict): 章节结构
        metadata_type (str): "tag" 或 "category"
    """
    print("\n" + "=" * 80)
    print(f"章节结构预览 (按{metadata_type.upper()}分组)")
    print("=" * 80)

    # 按层级分组显示
    level1_groups = defaultdict(list)

    for chapter in chapter_structure["chapters"]:
        level1 = chapter["level_1"]
        level1_groups[level1].append(chapter)

    for level1, chapters in level1_groups.items():
        print(f"\n📁 {level1} ({sum(ch['file_count'] for ch in chapters)} 个文件)")

        # 按二级目录分组
        level2_groups = defaultdict(list)
        for chapter in chapters:
            level2 = chapter["level_2"]
            level2_groups[level2].append(chapter)

        for level2, level2_chapters in level2_groups.items():
            if level2:
                print(
                    f"  📂 {level2} ({sum(ch['file_count'] for ch in level2_chapters)} 个文件)")

                for chapter in level2_chapters:
                    level3 = chapter["level_3"]
                    if level3:
                        print(f"    📄 {level3} ({chapter['file_count']} 个文件)")
            else:
                # 没有二级目录的直接显示
                for chapter in level2_chapters:
                    print(f"  📄 直接文件 ({chapter['file_count']} 个文件)")


def analyze_files_with_metadata(md_files, metadata_type):
    """
    分析所有文件并提取元数据

    Args:
        md_files (list): markdown文件路径列表
        metadata_type (str): "tag" 或 "category"

    Returns:
        list: 包含(文件路径, 元数据列表)的元组列表
    """
    files_with_metadata = []
    field_name = "标签" if metadata_type == "tag" else "分类"

    print(f"正在分析 {len(md_files)} 个文件的{field_name}...")

    for i, file_path in enumerate(md_files, 1):
        # 显示进度
        if i % 500 == 0 or i == len(md_files):
            print(f"进度: {i}/{len(md_files)}")

        metadata = extract_metadata_from_file(file_path, metadata_type)
        files_with_metadata.append((file_path, metadata))

    return files_with_metadata


def generate_sorted_file_list(chapter_structure):
    """
    根据章节结构生成排序后的文件列表

    Args:
        chapter_structure (dict): 章节结构

    Returns:
        list: 排序后的文件路径列表
    """
    sorted_files = []

    for chapter in chapter_structure["chapters"]:
        for file_path in chapter["files"]:
            sorted_files.append(
                (Path(file_path), [chapter["item"]], [chapter["item"]]))

    return sorted_files


def generate_epub(sorted_files, output_path, metadata_type):
    """
    使用Pandoc生成EPUB文件

    Args:
        sorted_files (list): 排序后的文件列表
        output_path (Path): 输出文件路径
        metadata_type (str): "tag" 或 "category"

    Returns:
        bool: 是否成功生成
    """
    if not sorted_files:
        print("错误：没有文件需要导出")
        return False

    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 准备Pandoc命令
        file_paths = [str(file_path) for file_path, _, _ in sorted_files]

        field_name = "标签" if metadata_type == "tag" else "分类"
        title = f"Obsidian导出合集（按{field_name}自动层级版）"

        pandoc_cmd = [
            "pandoc",
            # 输入文件
            *file_paths,
            # 输出格式和文件
            "-o", str(output_path),
            # EPUB相关选项
            "--to=epub3",
            "--epub-metadata=metadata.xml" if Path(
                "metadata.xml").exists() else None,
            # 目录选项
            "--toc",
            "--toc-depth=3",  # 增加目录深度以适应层级结构
            # 跳过YAML frontmatter解析，避免格式错误
            "--from=markdown-yaml_metadata_block",
            # 资源路径（让Pandoc能找到图片等资源）
            f"--resource-path={VAULT_PATH.absolute()}",
            # 标题和作者信息
            f"--metadata=title:{title}",
            "--metadata=author:知识整理者",
            f"--metadata=date:{datetime.now().strftime('%Y-%m-%d')}",
            # 中文支持
            "--variable=lang:zh-CN",
        ]

        # 过滤掉None值
        pandoc_cmd = [arg for arg in pandoc_cmd if arg is not None]

        print(f"\n正在生成EPUB文件...")
        print(f"输出路径: {output_path.absolute()}")
        print(f"处理文件数: {len(file_paths)}")

        # 执行Pandoc命令
        result = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15分钟超时
        )

        if result.returncode == 0:
            print("✅ EPUB文件生成成功!")
            return True
        else:
            print("❌ EPUB文件生成失败!")
            print(f"错误信息: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ EPUB生成超时!")
        return False
    except Exception as e:
        print(f"❌ 生成EPUB时出错: {e}")
        return False


def generate_epub_by_chapters(chapter_structure, output_dir, metadata_type):
    """
    按一级目录分别生成多个EPUB文件

    Args:
        chapter_structure (dict): 章节结构
        output_dir (Path): 输出目录
        metadata_type (str): "tag" 或 "category"

    Returns:
        list: 生成的EPUB文件路径列表
    """
    # 按一级目录分组
    level1_groups = defaultdict(list)

    for chapter in chapter_structure["chapters"]:
        level1 = chapter["level_1"]
        level1_groups[level1].append(chapter)

    generated_files = []
    field_name = "标签" if metadata_type == "tag" else "分类"

    print(f"\n将按 {len(level1_groups)} 个一级目录分别生成EPUB文件:")

    for level1, chapters in level1_groups.items():
        # 计算文件总数
        total_files = sum(len(chapter["files"]) for chapter in chapters)

        print(f"\n📁 正在处理: {level1} ({total_files} 个文件)")

        # 生成该分组的文件列表
        group_files = []
        for chapter in chapters:
            for file_path in chapter["files"]:
                group_files.append(
                    (Path(file_path), [chapter["item"]], [chapter["item"]]))

        # 生成文件名（去掉特殊字符）
        safe_name = level1.replace(
            "/", "_").replace("\\", "_").replace(":", "_")
        output_filename = f"Obsidian_{metadata_type}_{safe_name}.epub"
        output_path = output_dir / output_filename

        # 生成EPUB
        success = generate_single_epub(
            group_files, output_path, level1, metadata_type)

        if success:
            generated_files.append(output_path)
            print(f"✅ 已生成: {output_filename}")
        else:
            print(f"❌ 生成失败: {output_filename}")

    return generated_files


def generate_single_epub(sorted_files, output_path, category_name, metadata_type):
    """
    生成单个EPUB文件

    Args:
        sorted_files (list): 排序后的文件列表
        output_path (Path): 输出文件路径
        category_name (str): 分类名称
        metadata_type (str): "tag" 或 "category"

    Returns:
        bool: 是否成功生成
    """
    if not sorted_files:
        print("错误：没有文件需要导出")
        return False

    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 准备Pandoc命令
        file_paths = [str(file_path) for file_path, _, _ in sorted_files]

        field_name = "标签" if metadata_type == "tag" else "分类"
        title = f"Obsidian导出 - {category_name} (按{field_name})"

        pandoc_cmd = [
            "pandoc",
            # 输入文件
            *file_paths,
            # 输出格式和文件
            "-o", str(output_path),
            # EPUB相关选项
            "--to=epub3",
            "--epub-metadata=metadata.xml" if Path(
                "metadata.xml").exists() else None,
            # 目录选项
            "--toc",
            "--toc-depth=3",
            # 跳过YAML frontmatter解析，避免格式错误
            "--from=markdown-yaml_metadata_block",
            # 资源路径（让Pandoc能找到图片等资源）
            f"--resource-path={VAULT_PATH.absolute()}",
            # 标题和作者信息
            f"--metadata=title:{title}",
            "--metadata=author:知识整理者",
            f"--metadata=date:{datetime.now().strftime('%Y-%m-%d')}",
            # 中文支持
            "--variable=lang:zh-CN",
        ]

        # 过滤掉None值
        pandoc_cmd = [arg for arg in pandoc_cmd if arg is not None]

        # 执行Pandoc命令
        result = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时，单个分类应该不会太大
        )

        if result.returncode == 0:
            return True
        else:
            print(f"生成失败，错误信息: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("生成超时!")
        return False
    except Exception as e:
        print(f"生成时出错: {e}")
        return False


def generate_merged_epub(chapter_structure, output_dir, metadata_type):
    """
    合并所有章节生成一个大的EPUB文件

    Args:
        chapter_structure (dict): 章节结构
        output_dir (Path): 输出目录
        metadata_type (str): "tag" 或 "category"

    Returns:
        bool: 是否成功生成
    """
    field_name = "标签" if metadata_type == "tag" else "分类"
    print(f"\n正在生成合并的EPUB文件（按{field_name}）...")

    # 收集所有文件，按章节顺序
    all_files = []
    total_files = 0

    # 按一级目录分组
    level1_groups = defaultdict(list)
    for chapter in chapter_structure["chapters"]:
        level1 = chapter["level_1"]
        level1_groups[level1].append(chapter)

    # 按顺序处理每个一级目录
    for level1 in sorted(level1_groups.keys()):
        chapters = level1_groups[level1]
        print(f"📁 添加章节: {level1}")

        # 按章节顺序添加文件
        for chapter in chapters:
            for file_path in chapter["files"]:
                all_files.append(str(file_path))
                total_files += 1

    print(f"总共将处理 {total_files} 个文件")

    # 生成合并的EPUB
    output_filename = f"Obsidian_完整合集_{metadata_type}.epub"
    output_path = output_dir / output_filename

    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        title = f"Obsidian完整知识合集（按{field_name}）"

        pandoc_cmd = [
            "pandoc",
            # 输入文件
            *all_files,
            # 输出格式和文件
            "-o", str(output_path),
            # EPUB相关选项
            "--to=epub3",
            "--epub-metadata=metadata.xml" if Path(
                "metadata.xml").exists() else None,
            # 目录选项
            "--toc",
            "--toc-depth=3",
            # 跳过YAML frontmatter解析，避免格式错误
            "--from=markdown-yaml_metadata_block",
            # 资源路径（让Pandoc能找到图片等资源）
            f"--resource-path={VAULT_PATH.absolute()}",
            # 标题和作者信息
            f"--metadata=title:{title}",
            "--metadata=author:知识整理者",
            f"--metadata=date:{datetime.now().strftime('%Y-%m-%d')}",
            # 中文支持
            "--variable=lang:zh-CN",
        ]

        # 过滤掉None值
        pandoc_cmd = [arg for arg in pandoc_cmd if arg is not None]

        print(f"正在生成合并EPUB文件（这可能需要较长时间）...")
        print(f"输出路径: {output_path.absolute()}")

        # 执行Pandoc命令，使用更长的超时时间
        result = subprocess.run(
            pandoc_cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )

        if result.returncode == 0:
            print("✅ 合并EPUB文件生成成功!")

            # 显示文件大小
            if output_path.exists():
                file_size = output_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                print(f"📏 合并文件大小: {size_mb:.2f} MB")
                print(f"📊 包含文件数: {total_files}")

            return True
        else:
            print("❌ 合并EPUB文件生成失败!")
            print(f"错误信息: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 合并EPUB生成超时!")
        return False
    except Exception as e:
        print(f"❌ 生成合并EPUB时出错: {e}")
        return False


# =============================================================================
# 主程序
# =============================================================================

def main():
    """主程序"""
    print("=" * 80)
    print("Obsidian标签化导出脚本 - 自动层级目录生成版（支持Tag/Category）")
    print("=" * 80)

    print(f"正在扫描目录: {VAULT_PATH.absolute()}")

    # 第一步：查找所有.md文件
    md_files = find_all_md_files(VAULT_PATH)
    print(f"找到 {len(md_files)} 个markdown文件")

    # 第二步：选择处理模式
    print(f"\n请选择处理模式:")
    print(f"1. 按标签 (Tag) 处理")
    print(f"2. 按分类 (Category) 处理")

    while True:
        mode_choice = input("请选择 (1/2): ").strip()
        if mode_choice in ['1', '2']:
            break
        print("请输入有效选择: 1 或 2")

    metadata_type = "tag" if mode_choice == '1' else "category"
    field_name = "标签" if metadata_type == "tag" else "分类"

    print(f"\n已选择: 按{field_name}处理")

    # 第三步：提取元数据
    files_with_metadata = analyze_files_with_metadata(md_files, metadata_type)

    # 第四步：收集并排序所有元数据
    print(f"\n正在收集和分析{field_name}...")
    sorted_items, item_hierarchy, file_item_mapping = collect_all_metadata(
        files_with_metadata)

    # 第五步：生成章节结构
    print(f"\n正在生成章节结构...")
    chapter_structure = generate_chapter_structure(
        sorted_items, item_hierarchy, file_item_mapping, metadata_type)

    # 第六步：保存索引文件
    index_path = save_chapter_index(
        chapter_structure, OUTPUT_DIRECTORY, metadata_type)

    # 第七步：显示章节结构预览
    print_chapter_summary(chapter_structure, metadata_type)

    # 第八步：生成排序文件列表
    sorted_files = generate_sorted_file_list(chapter_structure)

    # 显示统计信息
    print("\n" + "=" * 80)
    print("导出统计:")
    print("=" * 80)
    print(f"原始文件总数: {len(md_files)}")
    print(f"有{field_name}的文件: {len(file_item_mapping)}")
    print(f"包含的{field_name}数: {len(sorted_items)}")
    print(f"将导出的文件: {len(sorted_files)}")

    # 询问EPUB生成方式
    print(f"\n选择EPUB生成方式:")
    print(f"1. 按一级目录分别生成多个EPUB文件（推荐，避免超时）")
    print(f"2. 生成单个完整EPUB文件（可能超时）")
    print(f"3. 合并所有章节生成一个大的EPUB文件")
    print(f"4. 跳过EPUB生成")

    while True:
        choice = input("请选择 (1/2/3/4): ").strip()
        if choice in ['1', '2', '3', '4']:
            break
        print("请输入有效选择: 1、2、3 或 4")

    if choice == '1':
        # 按章节分别生成EPUB
        print(f"\n正在按一级目录分别生成EPUB文件...")
        generated_files = generate_epub_by_chapters(
            chapter_structure, OUTPUT_DIRECTORY, metadata_type)

        if generated_files:
            print(f"\n🎉 分章节导出成功完成!")
            print(f"📁 输出目录: {OUTPUT_DIRECTORY.absolute()}")
            print(f"📁 索引文件: {index_path.absolute()}")
            print(f"📊 生成的EPUB文件: {len(generated_files)} 个")

            total_size = 0
            for epub_file in generated_files:
                if epub_file.exists():
                    file_size = epub_file.stat().st_size
                    size_mb = file_size / (1024 * 1024)
                    total_size += file_size
                    print(f"   📄 {epub_file.name}: {size_mb:.2f} MB")

            total_size_mb = total_size / (1024 * 1024)
            print(f"📏 总大小: {total_size_mb:.2f} MB")
        else:
            print(f"\n❌ 分章节导出失败")

    elif choice == '2':
        # 生成单个完整EPUB
        print(f"\n正在生成完整EPUB文件...")
        output_filename = f"Obsidian_导出_合集_{metadata_type}.epub"
        output_path = OUTPUT_DIRECTORY / output_filename
        success = generate_epub(sorted_files, output_path, metadata_type)

        if success:
            print(f"\n🎉 完整导出成功完成!")
            print(f"📁 EPUB文件: {output_path.absolute()}")
            print(f"📁 索引文件: {index_path.absolute()}")
            print(f"📊 包含文件数: {len(sorted_files)}")

            # 显示文件大小
            if output_path.exists():
                file_size = output_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                print(f"📏 EPUB大小: {size_mb:.2f} MB")
        else:
            print(f"\n❌ 完整导出失败，建议尝试分章节生成")
    elif choice == '3':
        # 合并所有章节生成一个大的EPUB
        success = generate_merged_epub(
            chapter_structure, OUTPUT_DIRECTORY, metadata_type)
        if success:
            print(f"\n📁 索引文件: {index_path.absolute()}")
        else:
            print(f"\n❌ 合并导出失败")
    else:
        print(f"\n✅ 章节索引生成完成，EPUB生成已跳过")
        print(f"📁 索引文件: {index_path.absolute()}")


if __name__ == "__main__":
    main()
