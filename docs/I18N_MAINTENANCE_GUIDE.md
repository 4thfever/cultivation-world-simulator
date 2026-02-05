# 国际化资源文件 (messages.po) 维护与增补指南

## 1. 核心问题警示 (CRITICAL WARNING)

**严禁在 Windows PowerShell 环境下直接使用重定向符号 (`>>`) 追加内容到 PO 文件！**

### 现象
`messages.po` 文件末尾出现大量 `NULL` (`\x00`) 字符或乱码，导致文件损坏，IDE 打开后显示为空白或包含红色方块。

### 原因
*   项目中的 PO 文件使用标准的 **UTF-8** 编码。
*   Windows PowerShell 的默认输出编码（尤其是在使用 `>>` 时）通常是 **UTF-16LE** (Windows Unicode)。
*   当 UTF-16LE 的内容被追加到 UTF-8 文件末尾时，文件会包含两种不兼容的编码，且 UTF-16 中的 `\x00` 字节会被视为乱码。

---

## 2. 正确的增补方式 (Source Split, Build Merge)

项目现已采用 **"Source Split, Build Merge"** 策略，将庞大的 `messages.po` 拆分为多个模块文件。

**请勿直接修改 `LC_MESSAGES/messages.po`！该文件现由构建脚本自动生成。**

### 方法 A：修改模块文件 (推荐)

所有源文件位于 `static/locales/{lang}/modules/` 目录下。请根据内容分类修改对应的 `.po` 文件：

*   `static/locales/zh-CN/modules/battle.po` - 战斗相关
*   `static/locales/zh-CN/modules/action.po` - 动作相关
*   `static/locales/zh-CN/modules/fortune.po` - 奇遇相关
*   `static/locales/zh-CN/modules/ui.po` - 界面相关
*   ... (以及其他分类)

直接使用编辑器打开相应的模块文件进行修改或追加。

### 方法 B：构建与合并

修改完成后，必须运行构建脚本将模块合并并编译为 MO 文件：

```bash
# 在项目根目录下运行
python tools/i18n/build_mo.py
```

该脚本会：
1.  合并 `modules/*.po` 到 `LC_MESSAGES/messages.po`
2.  编译生成 `LC_MESSAGES/messages.mo`
3.  编译其他独立文件 (如 `game_configs.po`)

### 方法 C：添加新模块

如果需要添加新的分类：
1.  在 `static/locales/{lang}/modules/` 下新建 `{category}.po`。
2.  确保包含标准 Header (参考其他模块)。
3.  运行 `build_mo.py` 即可自动识别并合并。

---

## 3. 文件格式规范

在增补 PO 文件时，请遵守以下格式规则，否则可能导致解析错误：

1.  **不要重复 Header**：
    *   PO 文件的开头已经包含了元数据（`Project-Id-Version`, `Content-Type` 等）。
    *   **不要**在追加的内容中再次包含这些 Header 信息。追加内容应仅包含 `msgid` 和 `msgstr`。

2.  **保持空行分隔**：
    *   每个 `msgid`/`msgstr` 对之间应保留一个空行，以提高可读性。

3.  **UTF-8 无 BOM**：
    *   始终确保文件保存为 UTF-8 编码且不带 BOM 头。

## 4. 紧急修复指南

如果不慎损坏了文件（出现了 NULL 字节），请按以下步骤修复：

1.  **立即停止写入**。
2.  使用支持二进制查看的编辑器（或 Python）读取文件。
3.  去除所有的 `\x00` 字节。
4.  检查并删除文件中段出现的重复 Header。
5.  重新保存为 UTF-8。

**Python 修复脚本示例：**

```python
def fix_po_file(path):
    with open(path, 'rb') as f:
        content = f.read()
    
    # 替换掉 null 字节
    content = content.replace(b'\x00', b'')
    
    # 重新写入为 UTF-8
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.decode('utf-8')) # 假设剩余内容是合法的 utf-8
```
