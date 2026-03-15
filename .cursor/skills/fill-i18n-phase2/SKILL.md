---
name: fill-i18n-phase2
description: 运行 Phase 2 工作流。执行脚本扫描缺失的多语言词条，并通过 Vibe coding 补全 en-US 和 zh-TW，最后修复所有测试。
---

# 多语言补全：Phase 2 工作流

当你被要求执行此技能时，说明我们现在进入了 **Phase 2**，你可以暂时忽略 "Phase 1" 的限制规则。你的目标是补齐所有缺失的翻译，并让测试变绿。

请严格执行以下步骤：

1. **生成缺失报告**：运行 `python tools/i18n/generate_missing_report.py`（该脚本会对比 zh-CN 和其他语言，输出 Markdown 报告到根目录）。
2. **阅读报告**：读取生成的 `i18n_missing_report.md` 报告文件。
3. **Vibe Coding 补全**：
   - 遍历报告中的文件路径和缺失项。
   - 运用你对“修仙(Cultivation)”背景的理解，将中文原意翻译为高质量的英文 (en-US) 和繁体中文 (zh-TW，请注意符合台湾用语习惯)。
   - 使用文件编辑工具，将对应的键值对或 msgid/msgstr 正确地插入到目标文件中。保持现有格式和缩进。对于 JSON 文件要确保逗号正确，不要破坏语法。对于 PO 文件要在 msgstr 中填入正确的翻译，并且条目之间保持一个空行。
4. **编译与验证**：
   - 如果修改了后端 `.po` 文件，必须运行 `python tools/i18n/build_mo.py`。但是不要去修改messages.po文件，这个是通过python tools/i18n/build_mo.p生成出来的，你不需要修改也不需要去阅读任何语言的messages.po文件。
   - 运行 `pytest tests/test_frontend_locales.py tests/test_backend_locales.py` 进行终检。如果有缺失，重复步骤 3 直到全部通过。
   - 全部ok后，删除生成的i18n_missing_report.md文件
