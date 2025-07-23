# Obsidian Exporter by Tag/Category

一个强大的Obsidian笔记导出工具，支持按标签(Tag)或分类(Category)自动组织并生成EPUB电子书。

## ✨ 主要特性

- 🏷️ **双模式支持**: 支持按Tag或Category两种方式组织导出
- 📁 **自动层级识别**: 智能解析`#一级/二级/三级`层级结构
- 📚 **EPUB生成**: 使用Pandoc生成高质量EPUB3格式电子书
- ⚡ **批量处理**: 支持大规模文件处理（测试过4000+文件）
- 🔄 **分章节导出**: 避免超时，按一级目录分别生成多个EPUB
- 📋 **索引生成**: 自动生成JSON格式的章节索引文件
- 🎯 **智能排序**: 基于数字和字母的自然排序算法

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Pandoc 3.0+（用于EPUB生成）

### 安装依赖

```bash
# 安装Pandoc (Ubuntu/Debian)
sudo apt update
sudo apt install pandoc

# 或者下载最新版本
wget https://github.com/jgm/pandoc/releases/download/3.7/pandoc-3.7-1-amd64.deb
sudo dpkg -i pandoc-3.7-1-amd64.deb
```

### 使用方法

1. **克隆项目**
```bash
git clone https://github.com/DayDreammy/obsidian_exporter_by_tag.git
cd obsidian_exporter_by_tag
```

2. **配置路径**
编辑`obsidian_export.py`中的路径配置：
```python
# Obsidian vault路径
VAULT_PATH = Path("./Sth-Matters")  # 修改为你的Obsidian vault路径
```

3. **运行脚本**
```bash
python obsidian_export.py
```

4. **选择模式**
- 选择1：按标签(Tag)处理
- 选择2：按分类(Category)处理

5. **选择导出方式**
- 选择1：分章节生成（推荐，避免超时）
- 选择2：单文件生成
- 选择3：合并生成
- 选择4：仅生成索引

## 📝 支持的元数据格式

### Tag模式
在Markdown文件中使用以下格式：
```markdown
> Tag: #1-个人成长/1-内在建设/1C-自强 #6-文化艺术/1-艺术总论
```

### Category模式
在Markdown文件中使用以下格式：
```markdown
> Category: #【答集】/08-文艺答集 #0-致读者
```

## 📂 层级结构解析

脚本会自动解析层级结构：
- `#1-个人成长/1-内在建设/1C-自强`
  - 一级：`1-个人成长`
  - 二级：`1-内在建设`
  - 三级：`1C-自强`

## 📊 输出文件

### EPUB文件
- Tag模式：`Obsidian_tag_[章节名].epub`
- Category模式：`Obsidian_category_[章节名].epub`

### 索引文件
- Tag模式：`chapter_index_tag.json`
- Category模式：`chapter_index_category.json`

### 文件结构
```
output/
├── chapter_index_tag.json          # Tag模式索引
├── chapter_index_category.json     # Category模式索引
├── Obsidian_tag_1-个人成长.epub     # Tag模式EPUB
├── Obsidian_category_【答集】.epub  # Category模式EPUB
└── ...
```

## ⚙️ 配置选项

在`obsidian_export.py`中可以修改以下配置：

```python
# 路径配置
VAULT_PATH = Path("./Sth-Matters")      # Obsidian vault路径
OUTPUT_DIRECTORY = Path("./output")      # 输出目录

# 元数据前缀
TAG_PREFIX = "> Tag:"                    # Tag前缀
CATEGORY_PREFIX = "> Category:"          # Category前缀

# 输出文件名
OUTPUT_FILENAME = "Obsidian_导出_合集.epub"
INDEX_FILENAME = "chapter_index.json"
```

## 🛠️ 技术实现

### 核心组件
- **文件扫描**: 使用`pathlib`递归扫描Markdown文件
- **元数据解析**: 正则表达式提取Tag/Category信息
- **层级排序**: 基于数字优先的自然排序算法
- **EPUB生成**: 集成Pandoc进行格式转换

### 处理流程
1. 扫描Obsidian vault中的所有`.md`文件
2. 提取每个文件的Tag或Category信息
3. 解析层级结构并自动排序
4. 生成章节索引JSON文件
5. 按章节分组生成EPUB文件

## 📈 性能表现

测试环境下的性能数据：
- ✅ 处理文件：4811个Markdown文件
- ✅ 识别标签：206个不同标签（Tag模式）
- ✅ 识别分类：20个不同分类（Category模式）
- ✅ 生成时间：约6分钟（包含4000+文件的EPUB生成）
- ✅ 输出大小：100-200MB（取决于内容量）

## 🔧 故障排除

### 常见问题

1. **Pandoc版本兼容性**
   - 推荐使用Pandoc 3.0+
   - 如遇YAML解析错误，脚本已自动添加`--from=markdown-yaml_metadata_block`参数

2. **超时问题**
   - 建议选择"分章节生成"模式
   - 大文件集合会自动拆分为多个EPUB

3. **编码问题**
   - 脚本已设置UTF-8编码
   - 支持中文路径和文件名

4. **路径配置**
   - 确保`VAULT_PATH`指向正确的Obsidian vault目录
   - 相对路径和绝对路径都支持

## 🤝 贡献指南

欢迎提交Issues和Pull Requests！

1. Fork本项目
2. 创建feature分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

## 🙏 致谢

- [Pandoc](https://pandoc.org/) - 强大的文档转换工具
- [Obsidian](https://obsidian.md/) - 优秀的知识管理工具

## 📞 联系方式

如有问题或建议，欢迎：
- 提交Issue
- 发起讨论
- 贡献代码

---

**让知识管理更高效！** 🚀 