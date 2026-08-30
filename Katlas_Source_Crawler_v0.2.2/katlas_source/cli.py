from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from .builder import build_catalog
from .downloader import download, write_manifest
from .page_fetch import fetch_profile, fetch_page_snapshots, rendered_page_url
from .page_enrich import enrich_one, sync_alias_enrichment
from .validate import validate
from .aliases import sync_alias_page_snapshots


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_download(args, config, root):
    out_root = (root / config["output_root"]).resolve()
    source_dir = out_root / "_source"
    results = []
    for ds in config["datasets"]:
        print(f"[download] {ds['name']}: {ds['url']}")
        results.append(download(ds["url"], source_dir / ds["filename"], ds["name"]))
    write_manifest(results, source_dir / "SOURCE_MANIFEST.json")
    print(json.dumps([r.__dict__ for r in results], indent=2))


def cmd_build(args, config, root):
    print(json.dumps(build_catalog(config, root), indent=2))


def cmd_validate(args, config, root):
    report = validate(config, root)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 2)


def _resolve(con: sqlite3.Connection, user_id: str):
    try:
        ar = con.execute(
            "SELECT alias,target_id,crossings,relpath,canonical_relpath,reason FROM aliases WHERE alias=?",
            (user_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        ar = None
    return (ar[1] if ar else user_id), ar


def cmd_lookup(args, config, root):
    out_root = (root / config["output_root"]).resolve()
    db = out_root / "_catalog" / "catalog.sqlite3"
    con = sqlite3.connect(db)
    resolved_id, alias_row = _resolve(con, args.id)
    row = con.execute("SELECT * FROM objects WHERE id=?", (resolved_id,)).fetchone()
    if row is None:
        con.close(); print(f"Not found: {args.id}", file=sys.stderr); raise SystemExit(1)
    cols = [x[0] for x in con.execute("SELECT * FROM objects LIMIT 0").description]
    data = dict(zip(cols, row))
    if alias_row:
        data["lookup_alias"] = {
            "alias": alias_row[0], "target_id": alias_row[1], "crossings": alias_row[2],
            "relpath": alias_row[3], "canonical_relpath": alias_row[4], "reason": alias_row[5],
        }
    data["invariants"] = [{"predicate": p, "value": v} for p, v in con.execute(
        "SELECT predicate,value FROM invariants WHERE object_id=? ORDER BY predicate", (resolved_id,)
    )]
    con.close(); print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_fetch_page(args, config, root):
    out_root = (root / config["output_root"]).resolve()
    db = out_root / "_catalog" / "catalog.sqlite3"
    con = sqlite3.connect(db)
    resolved_id, alias_row = _resolve(con, args.id)
    row = con.execute("SELECT relpath,page_url FROM objects WHERE id=?", (resolved_id,)).fetchone()
    con.close()
    if row is None:
        print(f"Not found in local catalog: {args.id}", file=sys.stderr); raise SystemExit(1)
    obj_dir = out_root / row[0]
    raw_url, page_url, attempts, raw_sha, html_sha = fetch_page_snapshots(
        resolved_id, obj_dir, delay_seconds=args.delay
    )
    enrichment = enrich_one(katlas_id=resolved_id, obj_dir=obj_dir, page_url=page_url)
    sync_alias_page_snapshots(db, out_root, resolved_id)
    copied = sync_alias_enrichment(db, out_root, resolved_id)
    print(json.dumps({
        "id": args.id, "resolved_id": resolved_id, "raw_url": raw_url, "page_url": page_url,
        "attempts": attempts, "wikitext_sha256": raw_sha, "html_sha256": html_sha,
        "arc_presentations": len(enrichment["arc_presentations"]),
        "semantic_notes": len(enrichment["semantic_notes"]),
        "media_references": len(enrichment["media_references"]),
        "alias_duplicates_updated": copied,
    }, indent=2))


def cmd_fetch_profile(args, config, root):
    profiles = config.get("page_fetch_profiles", {})
    if args.profile not in profiles:
        print(f"Unknown fetch profile: {args.profile}", file=sys.stderr)
        print("Available: " + ", ".join(sorted(profiles)), file=sys.stderr); raise SystemExit(2)
    out_root = (root / config["output_root"]).resolve()
    db = out_root / "_catalog" / "catalog.sqlite3"
    if not db.exists():
        print("Local catalog not built yet. Run run_all_rdf_only.cmd first.", file=sys.stderr); raise SystemExit(2)
    report = fetch_profile(
        db_path=db, out_root=out_root, profile_name=args.profile, profile=profiles[args.profile],
        force=args.force, delay_seconds=args.delay,
    )
    print(json.dumps({k: report[k] for k in (
        "profile", "target_count", "fetched", "skipped_existing", "failed",
        "objects_with_arc", "objects_with_notes", "objects_with_media", "extra_ids_missing_from_catalog"
    )}, indent=2))
    raise SystemExit(0 if report["failed"] == 0 else 3)


def main(argv=None):
    p = argparse.ArgumentParser(description="Katlas RDF importer and offline catalog builder")
    p.add_argument("--config", default="config.json")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download"); sub.add_parser("build"); sub.add_parser("validate")
    lookup = sub.add_parser("lookup"); lookup.add_argument("id")
    fetch = sub.add_parser("fetch-page"); fetch.add_argument("id"); fetch.add_argument("--delay", type=float, default=0.8)
    batch = sub.add_parser("fetch-profile"); batch.add_argument("profile", nargs="?", default="sst_curated")
    batch.add_argument("--delay", type=float, default=None); batch.add_argument("--force", action="store_true")
    args = p.parse_args(argv)
    config_path = Path(args.config).resolve(); root = config_path.parent; config = load_config(config_path)
    {"download": cmd_download, "build": cmd_build, "validate": cmd_validate, "lookup": cmd_lookup,
     "fetch-page": cmd_fetch_page, "fetch-profile": cmd_fetch_profile}[args.cmd](args, config, root)

if __name__ == "__main__":
    main()
