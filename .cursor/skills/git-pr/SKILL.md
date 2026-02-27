---
name: git-pr
description: 创建包含正确远程处理的 Pull Request
---

## 飞行前检查

```bash
git remote -v
# 如果 origin URL 过期，请修复它：
# git remote set-url origin https://github.com/AI-Cultivation/cultivation-world-simulator.git
```

## 命令

```bash
git checkout main && git pull origin main
git checkout -b <github-username>/<branch-name>
git add <files>
git commit -m "<type>: <description>"
git push -u origin <github-username>/<branch-name>
gh pr create --head <github-username>/<branch-name> --base main --title "<type>: <description>" --body "<body>"
```

## 注意事项

- 始终从 `main` 分支拉取新分支，而不是从当前分支
- 遵循 `.github/PULL_REQUEST_TEMPLATE.md` 中的 PR 模板
- `<github-username>`：例如 `xzhseh`
- `<type>`：`feat` | `fix` | `refactor` | `test` | `docs`
