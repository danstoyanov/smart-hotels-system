"""Check relative links and #anchors in the repository's Markdown files."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", ".local", ".claude", "node_modules"}
LINK = re.compile(r"\]\(<?([^)\s>]+)>?\)")
HEADING = re.compile(r"^#{1,6} (.+)$", re.MULTILINE)
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def anchor(heading: str) -> str:
    # GitHub style: lower case, drop punctuation, spaces become dashes.
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def markdown_files():
    for path in ROOT.rglob("*.md"):
        if not SKIP.intersection(path.relative_to(ROOT).parts):
            yield path


def main() -> int:
    broken = []
    for page in markdown_files():
        text = FENCE.sub("", page.read_text(encoding="utf-8"))
        for link in LINK.findall(text):
            if re.match(r"^[a-z]+:", link):
                continue
            path, _, fragment = link.partition("#")
            target = (page.parent / path).resolve() if path else page
            ok = target.exists()
            if ok and fragment and target.suffix == ".md":
                body = FENCE.sub("", target.read_text(encoding="utf-8"))
                ok = fragment in {anchor(h) for h in HEADING.findall(body)}
            if not ok:
                broken.append(f"{page.relative_to(ROOT)}: {link}")
    for line in broken:
        print(f"Broken link: {line}")
    print(f"Link check: {len(broken)} broken.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
