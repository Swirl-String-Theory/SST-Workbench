from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3


def friendly_alias_relpath(alias: str, crossings: int) -> Path:
    """Direct, unsharded convenience path for a friendly knot alias."""
    return Path("knots") / f"{crossings:02d}" / alias


def build_friendly_aliases(config: dict, out_root: Path, con: sqlite3.Connection) -> list[dict]:
    aliases = list(config.get("friendly_knot_aliases", []))
    results: list[dict] = []
    for spec in aliases:
        alias = str(spec["alias"])
        target_id = str(spec["target_id"])
        reason = str(spec.get("reason", "Convenience alias."))
        row = con.execute(
            "SELECT id,kind,crossings,relpath,page_url FROM objects WHERE id=?",
            (target_id,),
        ).fetchone()
        if row is None:
            results.append({"alias": alias, "target_id": target_id, "status": "TARGET_MISSING"})
            continue
        _, kind, crossings, canonical_relpath, page_url = row
        if kind != "knot":
            results.append({"alias": alias, "target_id": target_id, "status": "NOT_A_KNOT"})
            continue

        alias_rel = friendly_alias_relpath(alias, int(crossings))
        canonical_dir = out_root / canonical_relpath
        alias_dir = out_root / alias_rel
        alias_dir.mkdir(parents=True, exist_ok=True)

        # Explicit duplicate, rather than symlink/hardlink, for Windows portability.
        for filename in ("katlas.json", "source.rdf.nt", "page.wikitext", "page.html", "page_enrichment.json"):
            src = canonical_dir / filename
            if src.exists():
                shutil.copy2(src, alias_dir / filename)

        alias_record = {
            "schema": "SST-KATLAS-FRIENDLY-ALIAS-1.0",
            "alias": alias,
            "target_id": target_id,
            "crossings": int(crossings),
            "alias_relpath": alias_rel.as_posix(),
            "canonical_relpath": str(canonical_relpath),
            "canonical_page_url": page_url,
            "reason": reason,
            "storage_mode": "duplicate",
            "identity_rule": "katlas.json keeps the canonical Katlas identity; ALIAS.json records the friendly name.",
        }
        (alias_dir / "ALIAS.json").write_text(
            json.dumps(alias_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        con.execute(
            "INSERT OR REPLACE INTO aliases(alias,target_id,crossings,relpath,canonical_relpath,reason) VALUES(?,?,?,?,?,?)",
            (alias, target_id, int(crossings), alias_rel.as_posix(), str(canonical_relpath), reason),
        )
        results.append({**alias_record, "status": "CREATED"})
    return results


def sync_alias_page_snapshots(db_path: Path, out_root: Path, target_id: str | None = None) -> int:
    """Copy fetched canonical page.wikitext into every friendly duplicate that resolves to it."""
    con = sqlite3.connect(db_path)
    try:
        try:
            if target_id is None:
                rows = con.execute(
                    "SELECT alias,target_id,relpath,canonical_relpath FROM aliases ORDER BY alias"
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT alias,target_id,relpath,canonical_relpath FROM aliases WHERE target_id=? ORDER BY alias",
                    (target_id,),
                ).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table: aliases" in str(exc):
                return 0
            raise
    finally:
        con.close()

    copied = 0
    for alias, resolved_id, alias_relpath, canonical_relpath in rows:
        src = out_root / canonical_relpath / "page.wikitext"
        if not src.exists():
            continue
        dest_dir = out_root / alias_relpath
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_dir / "page.wikitext")
        copied += 1
    return copied
