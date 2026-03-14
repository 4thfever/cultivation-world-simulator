# 新增语言流程

本文档沉淀“如何为仓库新增一门语言”的推荐顺序。本文只描述流程，不代表仓库当前已经启用新的语言。

## 1. 先更新语言注册表

单一真相源位于：

- `tools/i18n/locales.json`

先在 `locales` 数组中新增一项，再考虑目录和资源。

建议字段：

```json
{
  "code": "vi-VN",
  "label": "Tiếng Việt",
  "html_lang": "vi",
  "enabled": true
}
```

说明：

- `code`: 语言目录名和运行时语言码
- `label`: 菜单显示名称
- `html_lang`: 写入前端 `<html lang>` 的值
- `enabled`: 是否启用

## 2. 再创建资源骨架

新增语言时，后续需要为该语言补齐以下目录：

- `web/src/locales/<locale>/`
- `static/locales/<locale>/modules/`
- `static/locales/<locale>/game_configs_modules/`
- `static/locales/<locale>/LC_MESSAGES/`
- `static/locales/<locale>/templates/`

当前推荐做法是先复制结构，再补内容；不要先零散改前端菜单、单个测试或运行时代码。

## 3. Python 侧工具和校验

以下 Python 侧工具/测试已经改为从 `tools/i18n/locales.json` 读取语言列表：

- `tools/i18n/generate_missing_report.py`
- `tools/i18n/compare_msgids_across_locales.py`
- `tools/i18n/align_po_files.py`
- `tools/i18n/align_po_files_preview.py`
- `tests/test_frontend_locales.py`
- `tests/test_backend_locales.py`
- `tests/test_i18n_modules.py`

如果后续新增新的 Python 侧 i18n 工具，也应优先复用：

- `tools/i18n/locale_registry.py`

## 4. 完成后建议验证

```bash
python tools/i18n/build_mo.py
pytest tests/test_frontend_locales.py tests/test_backend_locales.py tests/test_i18n_modules.py
```

## 5. 当前边界

本文档只沉淀流程，不会自动新增任何语言，也不替代未来可能引入的脚手架脚本。
