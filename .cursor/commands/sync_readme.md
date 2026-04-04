1. 读取 `static/locales/registry.json` 中的 `locales` 列表；排除带 `source_of_truth: true` 的项（即 zh-CN，对应主 `README.md`）。
2. 对每个需同步的 locale，目标文件为 `docs/readme/{CODE}_README.md`。`CODE` 规则：locale code 全大写并保留连字符（如 `zh-TW`→`ZH-TW`、`vi-VN`→`VI-VN`）；`en-US` 特殊为 `EN`。可参考 `docs/readme/` 下已有文件名。
3. 读取主 `README.md` (简体中文) 的内容，对比各目标文件的内容差异。
4. 将 `README.md` 中新增或修改的内容，分别准确地翻译并更新到各目标文件中。
5. 保持原有目标文件的排版格式和 Markdown 语法（如标题、列表、代码块等），注意图片等静态资源的引用路径也要保持各文件本身的正确性。
6. 翻译要符合对应语言开发者的阅读习惯，专业且自然；繁体中文需符合港台用语习惯；越南语需符合越南语表达习惯；日语需符合日本开发者的自然表达习惯，语气克制、清晰，不要直译成生硬的中文句式。
7. 仅更新对应的多语言 README 文件，不要修改主 `README.md` 文件。
8. qq群的入群答案不翻译，保持 literal 相同。
