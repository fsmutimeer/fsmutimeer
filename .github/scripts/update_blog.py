"""Rewrite the "Latest articles" list in README.md from the migrax.org RSS feed.

Only the lines between the BLOG-POST-LIST markers change. Uses the standard library only.
"""

import email.utils
import html
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEED = "https://migrax.org/feed_rss_created.xml"
README = pathlib.Path(__file__).resolve().parents[2] / "README.md"
MAX_POSTS = 5
START = "<!-- BLOG-POST-LIST:START -->"
END = "<!-- BLOG-POST-LIST:END -->"


def fetch_posts():
    request = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme-updater"})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    posts = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = email.utils.parsedate_to_datetime(item.findtext("pubDate"))
        if title and link.startswith("https://migrax.org/"):
            posts.append((published, title, link))
    posts.sort(reverse=True)
    return posts[:MAX_POSTS]


def render(posts):
    lines = []
    for published, title, link in posts:
        # Titles may contain `code`; keep it, but escape anything that could break the table.
        safe = html.escape(title, quote=False).replace("|", "\\|")
        lines.append(f"| [{safe}]({link}) | {published:%b %d, %Y} |")
    return "\n".join(["| Article | Published |", "| :-- | --: |", *lines])


def main():
    posts = fetch_posts()
    if not posts:
        sys.exit("The feed has no articles; leaving README.md unchanged.")
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        sys.exit("Markers not found in README.md.")
    updated = pattern.sub(lambda _: f"{START}\n{render(posts)}\n{END}", text)
    if updated != text:
        README.write_text(updated, encoding="utf-8", newline="\n")
        print(f"Updated README.md with {len(posts)} articles.")
    else:
        print("README.md is already up to date.")


if __name__ == "__main__":
    main()
