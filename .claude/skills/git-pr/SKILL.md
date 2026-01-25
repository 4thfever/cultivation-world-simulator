---
name: git-pr
description: Create a pull request with proper remote handling
---

## Pre-flight

```bash
git remote -v
# If origin URL is outdated, fix it:
# git remote set-url origin https://github.com/AI-Cultivation/cultivation-world-simulator.git
```

## Commands

```bash
git checkout main && git pull origin main
git checkout -b <github-username>/<branch-name>
git add <files>
git commit -m "<type>: <description>"
git push -u origin <github-username>/<branch-name>
gh pr create --head <github-username>/<branch-name> --base main --title "<type>: <description>" --body "<body>"
```

## Notes

- Always branch off from `main`, not from current branch
- Follow PR template in `.github/PULL_REQUEST_TEMPLATE.md`
- `<github-username>`: e.g., `xzhseh`
- `<type>`: `feat` | `fix` | `refactor` | `test` | `docs`
