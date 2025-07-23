#!/usr/bin/env python3
"""
Obsidian标签化导出脚本
第四步：整合导出 - 调用Pandoc生成EPUB文件
"""

from pathlib import Path
import sys
import re
import subprocess
from datetime import datetime

# =============================================================================
# 配置
# =============================================================================

# Obsidian vault路径
VAULT_PATH = Path("./Sth-Matters")

# 标签前缀
TAG_PREFIX = "> Tag:"

# 输出文件配置
OUTPUT_FILENAME = "Obsidian_导出_合集.epub"
OUTPUT_DIRECTORY = Path("./output")

# 标签排序顺序（用户可以根据需要修改这个列表）
# 这里是一个示例排序，基于标签使用频率和逻辑分组
TAG_ORDER = [
    # 致读者 - 开篇
    "#0-致读者",
    
    # 个人成长系列
    "#1-个人成长/1-内在建设/1C-自强",
    "#1-个人成长/3-处世之道/3e-礼节规范", 
    "#1-个人成长/4-心理与疗愈/4a-情绪与心态",
    "#1-个人成长/5-核心能力/5a-核心能力总论/读书与行路",
    "#1-个人成长/5-核心能力/5b-学逻辑/逻辑总论",
    "#1-个人成长/5-核心能力/5c-学哲学/哲学总论",
    
    # 亲密关系系列
    "#2-亲密关系/1-交往准则/1a-爱的原理",
    "#2-亲密关系/1-交往准则/1b-爱的禁忌",
    "#2-亲密关系/1-交往准则/1f-银子弹",
    "#2-亲密关系/2-交往案例/2a-论恋爱",
    
    # 家庭伦理系列
    "#3-家庭伦理/2-亲子关系/2b-家庭教育",
    "#3-家庭伦理/3-家族传承/论传承",
    
    # 职业发展系列  
    "#4-职业发展/1-态度与伦理",
    "#4-职业发展/2-选择与规划",
    "#4-职业发展/4-管理者素质",
    "#4-职业发展/6-经营案例",
    
    # 专题合集
    "#_专题合集/合集1-概念与定义",
    "#_专题合集/合集2-一些推荐", 
    "#_专题合集/合集4-俄乌战争",
    "#_专题合集/合集6-个人信仰/A-Caritas/1-爱",
]

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


def extract_tags_from_file(file_path):
    """
    从markdown文件中提取标签
    
    Args:
        file_path (Path): markdown文件路径
        
    Returns:
        list: 提取到的标签列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找标签行
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(TAG_PREFIX):
                # 提取标签内容（去掉前缀）
                tag_content = line[len(TAG_PREFIX):].strip()
                
                # 使用正则表达式提取所有以#开头的标签
                tags = re.findall(r'#[^\s#]+(?:/[^\s#]+)*', tag_content)
                
                return tags
        
        # 如果没有找到标签行，返回空列表
        return []
        
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return []


def analyze_files_with_tags(md_files):
    """
    分析所有文件并提取标签
    
    Args:
        md_files (list): markdown文件路径列表
        
    Returns:
        list: 包含(文件路径, 标签列表)的元组列表
    """
    files_with_tags = []
    
    print(f"正在分析 {len(md_files)} 个文件的标签...")
    
    for i, file_path in enumerate(md_files, 1):
        # 显示进度
        if i % 500 == 0 or i == len(md_files):
            print(f"进度: {i}/{len(md_files)}")
        
        tags = extract_tags_from_file(file_path)
        files_with_tags.append((file_path, tags))
    
    return files_with_tags


def filter_and_sort_by_tags(files_with_tags, tag_order):
    """
    根据标签顺序筛选和排序文件
    
    Args:
        files_with_tags (list): 包含(文件路径, 标签列表)的元组列表
        tag_order (list): 预设的标签排序列表
        
    Returns:
        list: 排序后的文件路径列表
    """
    # 为标签创建优先级映射
    tag_priority = {tag: i for i, tag in enumerate(tag_order)}
    
    # 筛选：只保留包含在tag_order中的文件
    filtered_files = []
    
    for file_path, tags in files_with_tags:
        # 检查文件是否包含任何目标标签
        matching_tags = []
        for tag in tags:
            if tag in tag_priority:
                matching_tags.append(tag)
        
        if matching_tags:
            # 文件的优先级由其最高优先级的标签决定
            min_priority = min(tag_priority[tag] for tag in matching_tags)
            filtered_files.append((file_path, tags, min_priority, matching_tags))
    
    # 按优先级排序
    filtered_files.sort(key=lambda x: x[2])
    
    # 返回排序后的文件路径列表
    return [(file_path, tags, matching_tags) for file_path, tags, _, matching_tags in filtered_files]


def generate_epub(sorted_files, output_path):
    """
    使用Pandoc生成EPUB文件
    
    Args:
        sorted_files (list): 排序后的文件列表
        output_path (Path): 输出文件路径
        
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
        
        pandoc_cmd = [
            "pandoc",
            # 输入文件
            *file_paths,
            # 输出格式和文件
            "-o", str(output_path),
            # EPUB相关选项
            "--to=epub3",
            "--epub-metadata=metadata.xml" if Path("metadata.xml").exists() else None,
            # 目录选项
            "--toc",
            "--toc-depth=2",
            # 资源路径（让Pandoc能找到图片等资源）
            f"--resource-path={VAULT_PATH.absolute()}",
            # 标题和作者信息
            "--metadata=title:Obsidian导出合集",
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
            timeout=300  # 5分钟超时
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


# =============================================================================
# 主程序
# =============================================================================

def main():
    """主程序"""
    print("=" * 60)
    print("Obsidian标签化导出脚本 - 第四步：生成EPUB")
    print("=" * 60)
    
    print(f"正在扫描目录: {VAULT_PATH.absolute()}")
    
    # 查找所有.md文件
    md_files = find_all_md_files(VAULT_PATH)
    print(f"找到 {len(md_files)} 个markdown文件")
    
    # 提取标签
    files_with_tags = analyze_files_with_tags(md_files)
    
    # 按标签排序
    print(f"\n正在根据预设标签顺序进行筛选和排序...")
    sorted_files = filter_and_sort_by_tags(files_with_tags, TAG_ORDER)
    
    if not sorted_files:
        print("没有找到包含目标标签的文件!")
        return
    
    # 显示筛选统计
    print("\n" + "=" * 60)
    print("筛选统计:")
    print("=" * 60)
    print(f"原始文件总数: {len(md_files)}")
    print(f"有标签的文件: {len([f for f in files_with_tags if f[1]])}")
    print(f"匹配目标标签的文件: {len(sorted_files)}")
    
    # 显示使用的标签统计
    used_tags = {}
    for _, _, matching_tags in sorted_files:
        for tag in matching_tags:
            used_tags[tag] = used_tags.get(tag, 0) + 1
    
    if used_tags:
        print(f"\n使用的标签统计:")
        print("-" * 40)
        for tag in TAG_ORDER:
            if tag in used_tags:
                print(f"{used_tags[tag]:3d} 次: {tag}")
    
    # 生成EPUB文件
    output_path = OUTPUT_DIRECTORY / OUTPUT_FILENAME
    success = generate_epub(sorted_files, output_path)
    
    if success:
        print(f"\n🎉 导出成功完成!")
        print(f"📁 输出文件: {output_path.absolute()}")
        print(f"📊 包含文件数: {len(sorted_files)}")
        
        # 显示文件大小
        if output_path.exists():
            file_size = output_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            print(f"📏 文件大小: {size_mb:.2f} MB")
    else:
        print(f"\n❌ 导出失败，请检查错误信息")

if __name__ == "__main__":
    main() 