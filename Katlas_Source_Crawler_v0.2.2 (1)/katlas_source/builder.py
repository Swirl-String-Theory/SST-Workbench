from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
from urllib.parse import quote

from .naming import parse_identity, object_relpath
from .rdf_parser import parse_dataset, extract_presentations
from .aliases import build_friendly_aliases

SCHEMA = "SST-KATLAS-SOURCE-1.0"


def _page_url(katlas_id: str) -> str:
    return "https://katlas.org/wiki/" + quote(katlas_id, safe="_")


def build_catalog(config: dict, project_root: Path) -> dict:
    out_root = (project_root / config["output_root"]).resolve()
    source_dir = out_root / "_source"
    catalog_dir = out_root / "_catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = catalog_dir / "catalog.jsonl"
    csv_path = catalog_dir / "catalog.csv"
    db_path = catalog_dir / "catalog.sqlite3"
    if db_path.exists():
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE objects(
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            crossings INTEGER NOT NULL,
            family TEXT,
            ordinal INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            dataset TEXT NOT NULL,
            relpath TEXT NOT NULL,
            page_url TEXT NOT NULL,
            pd TEXT,
            gauss TEXT,
            dt TEXT,
            conway TEXT,
            braid TEXT
        );
        CREATE TABLE invariants(
            object_id TEXT NOT NULL,
            predicate TEXT NOT NULL,
            value TEXT NOT NULL,
            FOREIGN KEY(object_id) REFERENCES objects(id)
        );
        CREATE INDEX idx_objects_crossings ON objects(kind, crossings, family, ordinal);
        CREATE INDEX idx_invariants_predicate ON invariants(predicate);
        CREATE INDEX idx_invariants_object ON invariants(object_id);
        CREATE TABLE aliases(
            alias TEXT PRIMARY KEY,
            target_id TEXT NOT NULL,
            crossings INTEGER NOT NULL,
            relpath TEXT NOT NULL,
            canonical_relpath TEXT NOT NULL,
            reason TEXT NOT NULL,
            FOREIGN KEY(target_id) REFERENCES objects(id)
        );
        CREATE INDEX idx_aliases_target ON aliases(target_id);
    """)

    rows_for_csv: list[dict] = []
    counts: dict[str, int] = {}
    skipped: list[dict] = []
    rejected_lines: dict[str, int] = {}

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as jsonl:
        for dataset in config["datasets"]:
            dataset_path = source_dir / dataset["filename"]
            if not dataset_path.exists():
                raise FileNotFoundError(
                    f"Missing {dataset_path}. Run the download command first."
                )
            objects, rejected = parse_dataset(dataset_path)
            rejected_lines[dataset["name"]] = len(rejected)
            for (_, _), obj in sorted(objects.items(), key=lambda kv: kv[0][1]):
                identity = parse_identity(obj.subject_type, obj.katlas_id)
                if identity is None:
                    skipped.append({"dataset": dataset["name"], "id": obj.katlas_id, "reason": "unrecognized-id"})
                    continue
                if identity.crossings > int(config["max_crossings"]):
                    continue

                rel = object_relpath(identity, int(config["shard_from_crossings"]), int(config["shard_size"]))
                obj_dir = out_root / rel
                obj_dir.mkdir(parents=True, exist_ok=True)
                presentations = extract_presentations(obj.invariants)
                record = {
                    "schema": SCHEMA,
                    "source": {
                        "name": "Knot Atlas",
                        "dataset": dataset["name"],
                        "archive": dataset["filename"],
                        "page_url": _page_url(identity.katlas_id),
                    },
                    "identity": {
                        "katlas_id": identity.katlas_id,
                        "kind": identity.kind,
                        "crossings": identity.crossings,
                        "ordinal": identity.ordinal,
                        "family": identity.family,
                        "table": identity.table_name,
                    },
                    "presentations": presentations,
                    "invariants": obj.invariants,
                }
                (obj_dir / "katlas.json").write_text(
                    json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                if config.get("keep_raw_object_rdf", True):
                    (obj_dir / "source.rdf.nt").write_text("\n".join(obj.raw_lines) + "\n", encoding="utf-8")

                jsonl.write(json.dumps({
                    "id": identity.katlas_id,
                    "kind": identity.kind,
                    "crossings": identity.crossings,
                    "family": identity.family,
                    "ordinal": identity.ordinal,
                    "table": identity.table_name,
                    "dataset": dataset["name"],
                    "relpath": rel.as_posix(),
                    "page_url": _page_url(identity.katlas_id),
                    "presentations": presentations,
                }, ensure_ascii=False) + "\n")

                first = lambda key: (presentations.get(key) or [None])[0]
                row = {
                    "id": identity.katlas_id, "kind": identity.kind,
                    "crossings": identity.crossings, "family": identity.family or "",
                    "ordinal": identity.ordinal, "table": identity.table_name,
                    "dataset": dataset["name"], "relpath": rel.as_posix(),
                    "page_url": _page_url(identity.katlas_id),
                    "pd": first("pd"), "gauss": first("gauss"), "dt": first("dt"),
                    "conway": first("conway"), "braid": first("braid"),
                }
                rows_for_csv.append(row)
                con.execute(
                    "INSERT OR REPLACE INTO objects VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (row["id"], row["kind"], row["crossings"], row["family"] or None,
                     row["ordinal"], row["table"], row["dataset"], row["relpath"], row["page_url"],
                     row["pd"], row["gauss"], row["dt"], row["conway"], row["braid"]),
                )
                con.executemany(
                    "INSERT INTO invariants(object_id,predicate,value) VALUES(?,?,?)",
                    [(identity.katlas_id, pred, value) for pred, values in obj.invariants.items() for value in values]
                )
                counts[dataset["name"]] = counts.get(dataset["name"], 0) + 1

    fieldnames = ["id","kind","crossings","family","ordinal","table","dataset","relpath","page_url","pd","gauss","dt","conway","braid"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows_for_csv)

    alias_results = build_friendly_aliases(config, out_root, con)
    aliases_path = catalog_dir / "aliases.json"
    aliases_path.write_text(json.dumps(alias_results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Compact capability summary for fast offline inspection.
    summary_rows = con.execute("SELECT kind,crossings,pd,gauss,dt,conway,braid FROM objects").fetchall()
    from collections import Counter
    by_kind = Counter(); by_crossing = Counter(); coverage = Counter()
    for kind,crossings,pd,gauss,dt,conway,braid in summary_rows:
        by_kind[kind] += 1; by_crossing[f"{kind}:{crossings}"] += 1
        for name,val in (("pd",pd),("gauss",gauss),("dt",dt),("conway",conway),("braid",braid)):
            if val not in (None, ""):
                coverage[f"{kind}:{crossings}:{name}"] += 1
    summary = {
        "schema": "SST-KATLAS-CATALOG-SUMMARY-1.0",
        "objects_total": len(summary_rows),
        "objects_by_kind": dict(sorted(by_kind.items())),
        "objects_by_kind_crossings": dict(sorted(by_crossing.items())),
        "presentation_coverage": dict(sorted(coverage.items())),
        "web_enrichment": {
            "scope": "curated profile after fetch-profile",
            "fields": ["ArcPresentation", "semantic notes", "diagram/image references"],
            "files": ["page.wikitext", "page.html", "page_enrichment.json"]
        }
    }
    (catalog_dir / "CATALOG_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    con.commit(); con.close()

    report = {
        "schema": "SST-KATLAS-BUILD-REPORT-1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "output_root": str(out_root),
        "objects_total": sum(counts.values()),
        "objects_by_dataset": counts,
        "rejected_rdf_lines": rejected_lines,
        "skipped": skipped,
        "friendly_aliases": {
            "requested": len(config.get("friendly_knot_aliases", [])),
            "created": sum(x.get("status") == "CREATED" for x in alias_results),
            "results": alias_results,
        },
        "catalogs": {
            "jsonl": str(jsonl_path), "csv": str(csv_path), "sqlite3": str(db_path)
        }
    }
    (catalog_dir / "BUILD_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
