当用户调用此命令时，请同步并更新仓库根目录 `CONTRIBUTORS.md`，来源为 GitHub 仓库贡献者列表。

请严格执行以下流程：

1. **确认目标仓库**：
   - 默认仓库为 `4thfever/cultivation-world-simulator`
   - 若用户明确指定其他仓库，再按用户要求覆盖
2. **执行同步脚本**：
   - 运行 `python tools/github/sync_contributors.py`
   - 若需指定仓库，使用 `python tools/github/sync_contributors.py --repo owner/name`
3. **生成文档要求**：
   - 输出目标为仓库根目录 `CONTRIBUTORS.md`
   - 文档顶部保留感谢开源贡献者的说明文字
   - 贡献者列表使用 Markdown 表格
   - 表格仅保留三列：`Name`、`Avatar`、`GitHub`
   - 不要补充“每个人做了什么”的说明
   - 表格数据以 GitHub contributors API 返回结果为准
4. **失败处理**：
   - 若 GitHub API 请求失败，明确说明失败原因
   - 不要在请求失败时写入伪造或手填的贡献者数据
5. **完成后自检**：
   - 检查 `CONTRIBUTORS.md` 是否已更新
   - 检查表格是否可读、链接是否指向正确 GitHub 主页
   - 输出本次同步的贡献者总数

注意：

- 仅更新 `CONTRIBUTORS.md` 与必要脚本，不要顺带修改其他业务文件。
- 若新增或修改了 `.cursor/commands`，建议随后执行一次 `/sync_agents`，保持 `AGENTS.md` 索引同步。
