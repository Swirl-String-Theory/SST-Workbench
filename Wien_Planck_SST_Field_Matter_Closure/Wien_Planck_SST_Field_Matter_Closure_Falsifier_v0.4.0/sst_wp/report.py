from __future__ import annotations
import argparse, json
from .common import load_json

def main():
    p = argparse.ArgumentParser()
    p.add_argument("json")
    p.add_argument("--out", required=True)
    p.add_argument("--title", default="SST Wien–Planck report")
    a = p.parse_args()
    d = load_json(a.json)
    lines = [f"# {a.title}", "", f"Format: `{d.get('format')}`", ""]
    if "gates" in d:
        lines += ["## Gates", ""] + [
            f"- **{k}**: `{v}`" for k, v in d["gates"].items()
        ] + [""]
    if "summary" in d:
        lines += [
            "## Summary", "", "```json",
            json.dumps(d["summary"], indent=2), "```", ""
        ]
    if "dimensionless_discovery" in d:
        lines += [
            "## Dimensionless discovery", "", "```json",
            json.dumps(d["dimensionless_discovery"], indent=2), "```", ""
        ]
    if "absolute_normalization_audit" in d:
        lines += [
            "## Absolute normalization audit", "", "```json",
            json.dumps(d["absolute_normalization_audit"], indent=2), "```", ""
        ]
    if "interpretation" in d:
        lines += ["## Interpretation", "", d["interpretation"], ""]
    if "warning" in d:
        lines += ["## Warning", "", d["warning"], ""]
    open(a.out, "w", encoding="utf-8").write("\n".join(lines))

if __name__ == "__main__":
    main()
