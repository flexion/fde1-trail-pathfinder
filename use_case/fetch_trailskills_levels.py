"""Fetch each competency's definition and level descriptions from trailskills.org.

Run from the repository root:
    uv run python use_case/fetch_trailskills_levels.py

Reads the competency ids and urls from
01_Product_Engineering/challenge/data/framework.json and writes
use_case/data/trailskills_levels.json (git-ignored: the text is American Trails'
content and this repository is a public fork):

    {"source", "fetched_at", "skills": {"<competency id>": {
        "name", "url", "definition",
        "levels": {"Entry": [...], "Full Performance": [...], "Expert": [...]}}}}

Level names match schema.SkillLevel.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = ROOT / "01_Product_Engineering/challenge/data/framework.json"
OUT = ROOT / "use_case/data/trailskills_levels.json"

HEADINGS = {
    "Skill Definition": "definition",
    "Entry Level Performance": "Entry",
    "Full Performance Level": "Full Performance",
    "Expert Level Performance": "Expert",
}
LEVELS = ("Entry", "Full Performance", "Expert")
USER_AGENT = "fde1-trail-pathfinder (American Trails project; one request per skill)"


class SkillPage(HTMLParser):
    """Collects the definition paragraph and the bullets under each level heading."""

    def __init__(self) -> None:
        super().__init__()
        self.definition = ""
        self.levels: dict[str, list[str]] = {level: [] for level in LEVELS}
        self._section: str | None = None
        self._in_heading = False
        self._heading = ""
        self._capture: str | None = None
        self._text = ""

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2"):
            self._in_heading, self._heading = True, ""
        elif tag == "p" and self._section == "definition" and not self.definition:
            self._capture, self._text = "p", ""
        elif tag == "li" and self._section in LEVELS:
            self._capture, self._text = "li", ""

    def handle_endtag(self, tag):
        if tag in ("h1", "h2") and self._in_heading:
            self._in_heading = False
            self._section = HEADINGS.get(" ".join(self._heading.split()))
        elif tag == self._capture:
            text = " ".join(self._text.split())
            if tag == "p":
                self.definition = text
            elif text and self._section is not None:
                self.levels[self._section].append(text)
            self._capture = None
        elif tag == "ul" and self._section in LEVELS:
            self._section = None

    def handle_data(self, data):
        if self._in_heading:
            self._heading += data
        elif self._capture:
            self._text += data


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main() -> int:
    competencies = json.loads(FRAMEWORK.read_text())["competencies"]
    skills, problems = {}, []
    for i, comp in enumerate(competencies, 1):
        try:
            page = SkillPage()
            page.feed(fetch(comp["url"]))
        except OSError as err:
            problems.append(f"{comp['id']}: {err}")
            continue
        missing = [level for level in LEVELS if not page.levels[level]]
        if not page.definition or missing:
            problems.append(f"{comp['id']}: missing {'definition ' if not page.definition else ''}{missing}")
        skills[comp["id"]] = {
            "name": comp["name"],
            "url": comp["url"],
            "definition": page.definition,
            "levels": page.levels,
        }
        print(f"[{i}/{len(competencies)}] {comp['id']}")
        time.sleep(0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "https://www.trailskills.org/skills/ (American Trails)",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skills": skills,
    }, indent=1) + "\n")
    print(f"wrote {len(skills)} skills to {OUT.relative_to(ROOT)}")
    for problem in problems:
        print("PROBLEM", problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
