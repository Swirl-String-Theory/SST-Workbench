"""Record the catalog-audit findings as SP08 todos.

catalog_audit.py found three duplicate catalog ids on disk and three catalog rows with
no matching directory. Both have to be settled before FAMILY.yaml is generated, or the
metadata will encode the wrong identity.
"""
from __future__ import annotations

from pathlib import Path

PLAN = (
    Path(__file__).resolve().parents[1]
    / ".cursor" / "plans" / "restructure"
    / "SP08_catalog_metadata_and_registry.plan.md"
)

FRONTMATTER = """  - id: t05
    content: "Fix 3 duplicate catalog ids on disk: B003, B004, C006"
    status: pending
  - id: t06
    content: "Resolve 3 catalog rows with no directory: B002, research D001, E007"
    status: pending
"""

CHECKBOXES = [
    "- [ ] Fix 3 duplicate catalog ids on disk: B003, B004, C006\n",
    "- [ ] Resolve 3 catalog rows with no directory: B002, research D001, E007\n",
]


def main() -> None:
    text = PLAN.read_text(encoding="utf-8")

    if "id: t05" not in text:
        end = text.find("\n---", 3)
        text = text[:end] + "\n" + FRONTMATTER.rstrip("\n") + text[end:]

    lines = text.splitlines(keepends=True)
    already = any(line.startswith("- [") and "duplicate catalog ids" in line for line in lines)
    if not already:
        # Insert after the last checkbox in the Todos list.
        last = max(
            (i for i, line in enumerate(lines) if line.startswith("- [")),
            default=None,
        )
        if last is not None:
            lines[last + 1 : last + 1] = CHECKBOXES
            text = "".join(lines)

    PLAN.write_text(text, encoding="utf-8")
    print("SP08 todos updated")


if __name__ == "__main__":
    main()
