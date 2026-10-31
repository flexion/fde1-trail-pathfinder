"""Render the trailskills.org level descriptions as a markdown wiki.

Run from the repository root, after fetch_trailskills_levels.py:
    uv run python use_case/build_wiki.py

Reads use_case/data/trailskills_levels.json and the categories in
01_Product_Engineering/challenge/data/framework.json. Writes
use_case/data/wiki/: one page per competency, named <competency id>.md, with a
`## <level>` heading per level, plus index.md listing the pages by category.
The wiki is generated, never edited by hand: change the source and re-run.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = ROOT / "01_Product_Engineering/challenge/data/framework.json"
LEVELS_FILE = ROOT / "use_case/data/trailskills_levels.json"
WIKI = ROOT / "use_case/data/wiki"


def page(comp: dict, skill: dict) -> str:
    lines = [
        f"# {comp['name']}",
        "",
        f"Category: {comp['category']} · id: {comp['id']} · source: {skill['url']}",
        "",
        "## Definition",
        "",
        skill["definition"],
    ]
    for level, bullets in skill["levels"].items():
        lines += ["", f"## {level}", ""] + [f"- {bullet}" for bullet in bullets]
    return "\n".join(lines) + "\n"


def index(framework: dict) -> str:
    lines = ["# Trail skills", "", "One page per competency, grouped by category.", ""]
    for category in framework["categories"]:
        lines += [f"## {category['name']}", ""]
        for comp in framework["competencies"]:
            if comp["category_id"] == category["id"]:
                lines.append(f"- [{comp['name']}]({comp['id']}.md) — {comp['definition']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    framework = json.loads(FRAMEWORK.read_text())
    skills = json.loads(LEVELS_FILE.read_text())["skills"]
    if WIKI.exists():
        shutil.rmtree(WIKI)
    WIKI.mkdir(parents=True)
    for comp in framework["competencies"]:
        (WIKI / f"{comp['id']}.md").write_text(page(comp, skills[comp["id"]]))
    (WIKI / "index.md").write_text(index(framework))
    print(f"wrote {len(framework['competencies'])} pages + index.md to {WIKI.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
