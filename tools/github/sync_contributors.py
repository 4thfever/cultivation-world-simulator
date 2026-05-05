from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib import error, parse, request


DEFAULT_REPO = "4thfever/cultivation-world-simulator"
DEFAULT_OUTPUT = Path("CONTRIBUTORS.md")
DEFAULT_README = Path("README.md")
API_BASE_URL = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch GitHub contributors and regenerate CONTRIBUTORS.md and update README.md."
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub repository in owner/name format. Default: {DEFAULT_REPO}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output Markdown path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=DEFAULT_README,
        help=f"README path to update. Default: {DEFAULT_README}",
    )
    return parser.parse_args()


def build_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "cultivation-world-simulator-contributor-sync",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None

    for part in link_header.split(","):
        match = re.match(r'\s*<([^>]+)>;\s*rel="([^"]+)"', part.strip())
        if match and match.group(2) == "next":
            return match.group(1)
    return None


def fetch_all_contributors(repo: str) -> list[dict[str, Any]]:
    headers = build_headers()
    url = f"{API_BASE_URL}/repos/{repo}/contributors?per_page=100"
    contributors: list[dict[str, Any]] = []

    while url:
        req = request.Request(url, headers=headers)
        try:
            with request.urlopen(req) as resp:
                payload = json.load(resp)
                if not isinstance(payload, list):
                    raise RuntimeError(f"Unexpected GitHub API payload: {payload!r}")
                contributors.extend(payload)
                url = parse_next_link(resp.headers.get("Link"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitHub API request failed with status {exc.code}: {body}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"Failed to connect to GitHub API: {exc}") from exc

    return contributors


def render_markdown(repo: str, contributors: list[dict[str, Any]]) -> str:
    lines = [
        "# Contributors",
        "",
        "感谢每一位为这个开源项目贡献代码、创意、反馈与时间的朋友。",
        "每一个 Pull Request、Issue、讨论和评审，都在帮助 `Cultivation World Simulator` 变得更完整、更有生命力。",
        "",
        "Thanks to everyone who has contributed code, ideas, feedback, and time to this open source project.",
        "Every pull request, issue, discussion, and review helps `Cultivation World Simulator` grow into something better.",
        "",
        "| Name | Avatar | GitHub |",
        "| --- | --- | --- |",
    ]

    for contributor in contributors:
        login = contributor.get("login") or "unknown"
        avatar_url = contributor.get("avatar_url") or ""
        profile_url = (
            contributor.get("html_url") or f"https://github.com/{parse.quote(login)}"
        )
        name = contributor.get("login") or "unknown"
        avatar = f'<img src="{avatar_url}" alt="{login} avatar" width="64" height="64" />'
        github = f"[@{login}]({profile_url})"
        lines.append(f"| {name} | {avatar} | {github} |")

    lines.append("")
    return "\n".join(lines)


def render_readme_contributors_section(
    repo: str, contributors: list[dict[str, Any]]
) -> str:
    contributor_cells: list[str] = []
    for contributor in contributors:
        login = contributor.get("login") or "unknown"
        avatar_url = contributor.get("avatar_url") or ""
        profile_url = (
            contributor.get("html_url") or f"https://github.com/{parse.quote(login)}"
        )
        safe_login = html.escape(login)
        contributor_cells.append(
            f'<td align="center"><a href="{profile_url}"><img src="{avatar_url}" width="56" height="56" alt="{safe_login}" /><br /><sub><b>{safe_login}</b></sub></a></td>'
        )

    lines = [
        "## 👥 贡献者",
        "",
        "<table>",
    ]
    for start in range(0, len(contributor_cells), 7):
        lines.append("  <tr>")
        lines.append("    " + "\n    ".join(contributor_cells[start : start + 7]))
        lines.append("  </tr>")
    lines.extend(
        [
            "</table>",
            "",
            "更多贡献细节请查看 [CONTRIBUTORS.md](CONTRIBUTORS.md)。",
            "",
        ]
    )
    return "\n".join(lines)


def update_readme(readme_path: Path, repo: str, contributors: list[dict[str, Any]]) -> bool:
    if not readme_path.exists():
        print(f"Warning: {readme_path} not found, skipping README update.")
        return False

    content = readme_path.read_text(encoding="utf-8")
    
    pattern = re.compile(r"## 👥 贡献者\s*\n.*?(?=\n## |\Z)", re.DOTALL)
    section = render_readme_contributors_section(repo, contributors)
    new_content, count = pattern.subn(section, content, count=1)

    if count == 0:
        print(f"Warning: Could not find contributors section in {readme_path} to update.")
        return False

    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")
        print(f"Updated {readme_path} contributors section.")
    else:
        print(f"{readme_path} contributors section already up to date.")
    return True


def main() -> int:
    args = parse_args()
    contributors = fetch_all_contributors(args.repo)
    markdown = render_markdown(args.repo, contributors)

    args.output.write_text(markdown, encoding="utf-8")
    print(
        f"Updated {args.output} with {len(contributors)} contributors from {args.repo}."
    )
    
    update_readme(args.readme, args.repo, contributors)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
