"""Mark SP08 complete in its plan file and the README status table."""
from __future__ import annotations

import re
from pathlib import Path

PLANS = Path(__file__).resolve().parents[1] / ".cursor" / "plans" / "restructure"
BACKTICK = chr(96)

NEXT = (
    "**Next:** Done. 87 FAMILY.yaml, 246 project.json, 46 registry entries carrying "
    "catalog_id, catalog_index.json with 229 legacy lookups."
)


def main() -> None:
    plan = PLANS / "SP08_catalog_metadata_and_registry.plan.md"
    text = plan.read_text(encoding="utf-8")
    text = re.sub(r"^(\s+)status: pending$", r"\1status: completed", text, flags=re.M)
    text = text.replace("- [ ]", "- [x]")
    text = re.sub(
        rf"^(Status: ){BACKTICK}\w[\w ]*{BACKTICK}",
        rf"\1{BACKTICK}DONE{BACKTICK}",
        text, count=1, flags=re.M,
    )
    text = re.sub(r"^\*\*Next:\*\* .*$", NEXT, text, count=1, flags=re.M)
    plan.write_text(text, encoding="utf-8")

    readme = PLANS / "README.md"
    rt = readme.read_text(encoding="utf-8")
    rt = rt.replace(
        f"| Catalog metadata and registry | {BACKTICK}PLANNED{BACKTICK} | 0/7 |",
        f"| Catalog metadata and registry | {BACKTICK}DONE{BACKTICK} | 7/7 |",
    )
    readme.write_text(rt, encoding="utf-8")
    print("SP08 marked done in the plan and the README")


if __name__ == "__main__":
    main()
