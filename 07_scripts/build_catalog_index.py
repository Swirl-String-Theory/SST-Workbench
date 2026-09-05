"""SP08: build 10_docs/registry/catalog_index.json from the FAMILY.yaml files.

`resolve_family()` should read one file rather than walk the tree. The index is derived,
never hand-edited: regenerate it whenever families move or versions are added.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
INDEX = WB / "10_docs" / "registry" / "catalog_index.json"


def family_files() -> list[Path]:
    found = list(WB.glob("0*/*/*/FAMILY.yaml")) + list(WB.glob("05_apps/*/FAMILY.yaml"))
    return sorted(set(found))


def parse_family(path: Path) -> dict:
    """Read the flat subset of FAMILY.yaml we need without a YAML dependency."""
    scalars: dict[str, str] = {}
    versions: list[dict] = []
    legacy: list[str] = []
    variants: list[str] = []
    section = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        if not raw.startswith((" ", "-")):
            key, _, value = raw.partition(":")
            key, value = key.strip(), value.strip()
            if value in ("", "[]"):
                section = key if value == "" else None
                if value == "[]":
                    section = None
                continue
            section = None
            scalars[key] = value.strip('"')
            continue

        stripped = raw.strip()
        if section == "versions":
            if stripped.startswith("- id:"):
                versions.append({"id": stripped.split(":", 1)[1].strip()})
            elif versions and ":" in stripped:
                k, _, v = stripped.partition(":")
                versions[-1][k.strip()] = v.strip().strip('"')
        elif section == "legacy_paths" and stripped.startswith("- "):
            legacy.append(stripped[2:].strip().strip('"'))
        elif section == "variants" and stripped.startswith("- "):
            variants.append(stripped[2:].strip().strip('"'))

    return {
        "catalog_id": scalars.get("catalog_id", ""),
        "slug": scalars.get("slug", ""),
        "name": scalars.get("name", ""),
        "domain": scalars.get("domain", ""),
        "letter": scalars.get("letter", ""),
        "kind": scalars.get("kind", ""),
        "status": scalars.get("status", ""),
        "latest": scalars.get("latest", ""),
        "output_prefix": scalars.get("output_prefix", ""),
        "path": path.parent.relative_to(WB).as_posix(),
        "versions": versions,
        "variants": variants,
        "legacy_paths": legacy,
    }


def build() -> dict:
    entries = [parse_family(p) for p in family_files()]
    by_domain: dict[str, dict[str, dict]] = {}
    legacy_lookup: dict[str, str] = {}
    for e in entries:
        by_domain.setdefault(e["domain"], {})[e["catalog_id"]] = e
        for old in e["legacy_paths"]:
            legacy_lookup[old] = f"{e['domain']}/{e['catalog_id']}"
    return {
        "schema": 1,
        "families": len(entries),
        "versions": sum(len(e["versions"]) for e in entries),
        "by_domain": by_domain,
        "legacy_lookup": legacy_lookup,
    }


def main() -> int:
    index = build()
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"families        : {index['families']}")
    print(f"versions        : {index['versions']}")
    print(f"legacy lookups  : {len(index['legacy_lookup'])}")
    print(f"wrote {INDEX.relative_to(WB).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
