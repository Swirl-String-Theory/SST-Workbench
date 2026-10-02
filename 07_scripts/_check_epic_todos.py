"""Tick the epic/plan checkboxes that SP00-SP07 have now satisfied."""
from __future__ import annotations

from pathlib import Path

PLANS = Path(__file__).resolve().parents[1] / ".cursor" / "plans" / "restructure"

# file -> substrings identifying items that are now complete
COMPLETED = {
    "RESTRUCTURE_EPIC.plan.md": [
        "SP01 path resolver implemented",
        "SP02 junction layer live",
        "SP03 catalog skeleton + hygiene",
        "SP04-SP07 physical",
    ],
    "RESTRUCTURE_PLAN_v0.1.plan.md": [
        "SP04: 18 simple moves executed",
        "SP05: clean family moves executed",
        "SP06: container splits executed",
        "SP07: KnotPlot tool/data/campaign/result split executed",
    ],
}


def main() -> None:
    for name, needles in COMPLETED.items():
        path = PLANS / name
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        hits = 0
        for i, line in enumerate(lines):
            if not line.startswith("- [ ]"):
                continue
            if any(n in line for n in needles):
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                hits += 1
        path.write_text("".join(lines), encoding="utf-8")
        print(f"{name}: {hits} items ticked")


if __name__ == "__main__":
    main()
