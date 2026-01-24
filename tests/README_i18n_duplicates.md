# i18n PO 文件重复项检查

## 概述

本测试用于检查项目中的 i18n PO 文件（中文和英文）是否存在重复的 `msgid` 条目，以及确保中英文翻译文件的一致性。

## 测试内容

1. **检查中文 po 文件没有重复的 msgid**
   - 扫描 `src/i18n/locales/zh_CN/LC_MESSAGES/messages.po`
   - 确保没有重复的翻译键

2. **检查英文 po 文件没有重复的 msgid**
   - 扫描 `src/i18n/locales/en_US/LC_MESSAGES/messages.po`
   - 确保没有重复的翻译键

3. **检查中英文 msgid 数量一致**
   - 确保两个语言文件的条目数量相同

4. **检查中英文 msgid 键完全匹配**
   - 确保两个文件中的所有 msgid 键完全一致
   - 防止某个语言缺少翻译或多出翻译

## 使用方法

### 方法一：直接运行测试文件

```bash
python tests/test_i18n_duplicates.py
```

这个测试文件是独立的，不依赖 `conftest.py`，可以直接运行。

### 方法二：使用工具脚本

```bash
python tools/i18n/check_po_duplicates.py
```

这个工具脚本提供了更详细的输出和检查结果。

## 输出示例

### 成功时的输出

```
============================================================
i18n PO 文件重复项检查
============================================================

检查中文 po 文件没有重复...
[PASS] 中文 po 文件没有重复的 msgid (共 519 个)

检查英文 po 文件没有重复...
[PASS] 英文 po 文件没有重复的 msgid (共 519 个)

检查中英文 msgid 数量一致...
[PASS] 中英文 po 文件的 msgid 数量一致: 519 个

检查中英文 msgid 键完全匹配...
[PASS] 中英文 po 文件的 msgid 键完全匹配

============================================================
[OK] 所有测试通过 (4/4)
```

### 失败时的输出

```
============================================================
i18n PO 文件重复项检查
============================================================

检查中文 po 文件没有重复...
[FAIL] 中文 po 文件中发现 2 个重复的 msgid:
  - 'Encountered fortune ({theme}), {result}' 出现了 2 次
  - 'New {label}: {info}' 出现了 2 次

...

============================================================
[FAIL] 部分测试失败 (1/4)
```

## 常见问题

### 如果发现重复的 msgid 怎么办？

1. 使用工具定位重复的位置
2. 检查两个重复条目的上下文，确定哪个是正确的
3. 删除多余的重复条目
4. 重新运行测试确认修复

### 如何在 CI/CD 中集成？

在 GitHub Actions 或其他 CI 系统中添加：

```yaml
- name: Check i18n PO duplicates
  run: python tests/test_i18n_duplicates.py
```

脚本会返回退出码：
- `0`: 所有测试通过
- `1`: 有测试失败

## 相关文件

- `tests/test_i18n_duplicates.py` - 独立测试脚本
- `tools/i18n/check_po_duplicates.py` - 检查工具脚本
- `src/i18n/locales/zh_CN/LC_MESSAGES/messages.po` - 中文翻译文件
- `src/i18n/locales/en_US/LC_MESSAGES/messages.po` - 英文翻译文件

## 维护说明

当添加新的翻译条目时：

1. 确保在两个语言文件中同时添加
2. 确保 `msgid` 完全一致
3. 运行此测试确保没有引入重复或不一致

## 技术细节

- 使用正则表达式 `msgid\s+"([^"]*)"` 提取 msgid
- 使用 `collections.Counter` 统计重复
- 使用 `set` 操作检查键的差异
