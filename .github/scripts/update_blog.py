import html
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

BLOG_URL = "https://www.richardorilla.website/blog.html"
README_PATH = Path("README.md")
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"
MAX_POSTS = 5


def fetch_recent_posts() -> list[str]:
    """Fetch the latest blog posts from the #blog-articles table."""
    req = urllib.request.Request(
        BLOG_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GitHubActions-ReadmeUpdater/1.0)"},
    )
    raw = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")

    table_match = re.search(
        r'<table[^>]*id=["\']blog-articles["\'][^>]*>(.*?)</table>', raw, re.S | re.I
    )
    if not table_match:
        raise RuntimeError("Could not find #blog-articles table")

    tbody_match = re.search(r"<tbody>(.*?)</tbody>", table_match.group(1), re.S | re.I)
    if not tbody_match:
        raise RuntimeError("Could not find <tbody> in #blog-articles")

    rows = re.findall(r"<tr>(.*?)</tr>", tbody_match.group(1), re.S | re.I)[:MAX_POSTS]
    posts = []
    for row in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        if len(tds) < 2:
            continue
        date = re.sub(r"<[^>]+>", "", tds[0]).strip()
        link_match = re.search(
            r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', tds[1], re.S | re.I
        )
        if not link_match:
            continue
        href = urljoin(BLOG_URL, link_match.group(1).strip())
        title = html.unescape(
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", link_match.group(2))).strip()
        )
        posts.append(f"- **{date}** — [{title}]({href})")

    return posts


def main() -> None:
    """Update README.md with the latest blog posts if they have changed."""
    posts = fetch_recent_posts()
    if not posts:
        raise RuntimeError("No posts parsed from blog.html")

    readme = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"({re.escape(START_MARKER)}\n)(.*?)(\n{re.escape(END_MARKER)})",
        re.S,
    )
    replacement = rf"\g<1>{chr(10).join(posts)}\g<3>"
    updated, count = pattern.subn(replacement, readme, count=1)
    if count == 0:
        raise RuntimeError("Blog post markers not found in README.md")

    if updated != readme:
        README_PATH.write_text(updated, encoding="utf-8")
        print(f"Updated README.md with {len(posts)} posts.")
    else:
        print("README.md is already up to date.")


if __name__ == "__main__":
    main()
