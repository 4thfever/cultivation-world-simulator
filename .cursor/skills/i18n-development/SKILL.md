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
