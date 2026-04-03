---
name: i18n-development
description: 国际化 (i18n) 开发指南。在添加新文本、创建物品/事件、修改翻译或管理 PO/MO 文件时使用。
---

# I18n 国际化开发指南

## ⭐ 核心日常操作 (最重要)

### 1. 如何添加新消息
将新条目追加到 `static/locales/{lang}/modules/` 或 `game_configs_modules/` 中相应的 `.po` 文件里。

**格式要求:**
- 条目之间保持 **一个空行**。
- `msgid` 必须是准确的英文字符串。
- `msgstr` 是翻译内容。

```po
msgid "Found {amount} spirit stone"
msgstr "发现了 {amount} 块灵石"
```

### 2. 如何添加新的 PO 文件
如果正在开发新功能，请创建一个新的 `.po` 文件（例如，`modules/new_feature.po`）。
- **规则**: **不要**向这些拆分的模块文件添加 PO 头部信息（如 `Project-Id-Version`）。构建脚本会处理头部信息。直接开始编写 `msgid` 即可。

### 2.1 语言注册表
仓库中的语言列表单一真相源位于 `static/locales/registry.json`。

- Python 侧 i18n 工具、校验脚本和新增语言流程应优先读取该文件。
- 如果未来需要新增语言，请先更新该文件，再补目录和资源骨架。
- 不要在新脚本里重新写死 `zh-CN / zh-TW / en-US / vi-VN / ja-JP`。

### 3. ⚠️ 关键: 始终重新构建
`.po` 或 `.csv` 文件中的更改在编译为 `.mo` 文件之前 **不会** 在游戏中生效。
**在任何翻译更改后，始终运行构建脚本:**
```bash
python tools/i18n/build_mo.py
```

---

## 🔴 关键规则 (简述)

- **绝对不要**在 Windows PowerShell 中使用重定向 (`>>`) 追加内容到 PO 文件（这会导致 UTF-16LE 编码和 `\x00` 损坏）。
- **编码**: 必须使用无 BOM 的 UTF-8。
- **不要直接编辑** `LC_MESSAGES/messages.po`。请编辑 `modules/` 或 `game_configs_modules/` 中拆分的 `.po` 文件。
- **语言列表**: 优先从 `static/locales/registry.json` 读取，不要在工具或测试里重新维护一份手写语言列表。
- **设置页语言入口**: `web/src/components/SystemMenu.vue` 中的语言设置项，对非英语 UI 必须保留可见的 `Language` 英文提示（例如 `语言 / Language`、`言語 / Language`），不要在后续润色或本地化时去掉这个 `Language`。

## 🧩 工作流与模式 (简述)

### Python 动态文本
使用 `src.i18n` 中的 `t()`。
```python
from src.i18n import t
msg = t("{actor} performs action", actor=self.avatar.name)
```

### CSV 游戏配置
1. 编辑 CSV（添加 `name_id` 和 `desc_id`）。
2. 提取 POT: `python tools/i18n/extract_csv.py`
3. 在 `game_configs_modules/{category}.po` 中进行翻译。
4. 重新构建: `python tools/i18n/build_mo.py`

### 效果 (JSON) & 角色信息
- **JSON**: 使用 `_desc` 和 `when_desc` 通过翻译键覆盖描述。
- **字典**: 直接翻译键（例如，`t("Name"): self.name`）。
