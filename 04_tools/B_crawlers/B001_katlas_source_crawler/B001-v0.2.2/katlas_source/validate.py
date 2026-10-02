from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from .naming import parse_identity
from .rdf_parser import parse_dataset
from .page_fetch import select_profile_targets


def _expected_dataset_counts(config: dict, out_root: Path) -> dict[str, int]:
    source_dir = out_root / "_source"
    expected: dict[str, int] = {}
    for ds in config["datasets"]:
        p = source_dir / ds["filename"]
        if not p.exists():
            continue
        objects, _ = parse_dataset(p)
        n = 0
        for (_, _), obj in objects.items():
            ident = parse_identity(obj.subject_type, obj.katlas_id)
            if ident is not None and ident.crossings <= int(config["max_crossings"]):
                n += 1
        expected[ds["name"]] = n
    return expected


def validate(config: dict, project_root: Path) -> dict:
    out_root = (project_root / config["output_root"]).resolve()
    db = out_root / "_catalog" / "catalog.sqlite3"
    issues: list[dict] = []
    counts = Counter()
    if not db.exists():
        raise FileNotFoundError(f"Missing catalog: {db}")

    con = sqlite3.connect(db)
    rows = con.execute(
        "SELECT id,kind,crossings,family,relpath,dataset FROM objects ORDER BY kind,crossings,ordinal"
    ).fetchall()
    actual_by_dataset = Counter()
    for katlas_id, kind, crossings, family, relpath, dataset in rows:
        counts[f"{kind}:{crossings}"] += 1
        actual_by_dataset[dataset] += 1
        p = out_root / relpath / "katlas.json"
        if not p.exists():
            issues.append({"id": katlas_id, "issue": "missing-katlas-json", "path": str(p)})
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append({"id": katlas_id, "issue": "invalid-json", "error": str(exc)})
            continue
        ident = data.get("identity", {})
        if ident.get("katlas_id") != katlas_id:
            issues.append({"id": katlas_id, "issue": "id-mismatch"})
        if ident.get("kind") != kind:
            issues.append({"id": katlas_id, "issue": "kind-mismatch", "db": kind, "json": ident.get("kind")})
        if int(ident.get("crossings", -1)) != crossings:
            issues.append({"id": katlas_id, "issue": "crossing-mismatch"})
        if crossings > int(config["max_crossings"]):
            issues.append({"id": katlas_id, "issue": "above-max-crossings"})

    expected = _expected_dataset_counts(config, out_root)
    for ds_name, expected_n in expected.items():
        actual_n = actual_by_dataset.get(ds_name, 0)
        if actual_n != expected_n:
            issues.append({
                "dataset": ds_name,
                "issue": "dataset-export-count-mismatch",
                "expected_parseable_objects": expected_n,
                "actual_exported_objects": actual_n,
            })

    if expected.get("Links", 0) > 0 and sum(v for k, v in counts.items() if k.startswith("link:")) == 0:
        issues.append({"dataset": "Links", "issue": "links-source-present-but-zero-links-exported"})

    alias_rows = con.execute(
        "SELECT alias,target_id,crossings,relpath,canonical_relpath FROM aliases ORDER BY alias"
    ).fetchall()
    for alias, target_id, crossings, relpath, canonical_relpath in alias_rows:
        alias_dir = out_root / relpath
        canonical_dir = out_root / canonical_relpath
        for filename in ("katlas.json", "ALIAS.json"):
            if not (alias_dir / filename).exists():
                issues.append({"alias": alias, "target_id": target_id, "issue": f"missing-alias-{filename}", "path": str(alias_dir / filename)})
        if not canonical_dir.exists():
            issues.append({"alias": alias, "target_id": target_id, "issue": "missing-canonical-directory", "path": str(canonical_dir)})
        try:
            alias_meta = json.loads((alias_dir / "ALIAS.json").read_text(encoding="utf-8"))
            if alias_meta.get("alias") != alias or alias_meta.get("target_id") != target_id:
                issues.append({"alias": alias, "target_id": target_id, "issue": "alias-metadata-mismatch"})
        except Exception as exc:
            issues.append({"alias": alias, "target_id": target_id, "issue": "invalid-alias-json", "error": str(exc)})

    # When run_all has fetched a profile, require all selected targets to have the enrichment files.
    profile_name = config.get("validation", {}).get("require_page_profile")
    profile_report_exists = False
    if profile_name:
        report_path = out_root / "_catalog" / f"PAGE_FETCH_{profile_name}_REPORT.json"
        profile_report_exists = report_path.exists()
        if profile_report_exists:
            profile = config.get("page_fetch_profiles", {}).get(profile_name, {})
            targets = select_profile_targets(
                db, int(profile.get("max_auto_crossings", 7)), list(profile.get("extra_ids", []))
            )
            for katlas_id, relpath in targets:
                obj_dir = out_root / relpath
                for fn in ("page.wikitext", "page.html", "page_enrichment.json"):
                    if not (obj_dir / fn).exists():
                        issues.append({"id": katlas_id, "issue": f"missing-curated-{fn}", "path": str(obj_dir / fn)})
                kj = obj_dir / "katlas.json"
                if kj.exists():
                    try:
                        kd = json.loads(kj.read_text(encoding="utf-8"))
                        if "page_enrichment" not in kd:
                            issues.append({"id": katlas_id, "issue": "missing-page-enrichment-in-katlas-json"})
                    except Exception:
                        pass
    con.close()

    report = {
        "schema": "SST-KATLAS-VALIDATION-1.1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not issues else "FAIL",
        "objects_total": len(rows),
        "friendly_aliases_total": len(alias_rows),
        "counts": dict(sorted(counts.items())),
        "dataset_counts": {
            name: {"expected_from_source": expected.get(name, 0), "exported": actual_by_dataset.get(name, 0)}
            for name in sorted(set(expected) | set(actual_by_dataset))
        },
        "page_profile_required": profile_name,
        "page_profile_report_present": profile_report_exists,
        "issues": issues,
        "notes": [
            "Identifier syntax is authoritative for links because official Links.rdf.gz uses knot: subjects for L... IDs.",
            "Dataset counts are recomputed from the downloaded RDF and must exactly match exported parseable objects.",
            "Missing individual presentation fields are not failures because Katlas coverage varies by object.",
            "12-crossing links are exported only if actually present in Links.rdf.gz; no IDs are fabricated.",
            "Friendly aliases are portable duplicates, not replacements for canonical Katlas identities."
        ]
    }
    path = out_root / "_catalog" / "VALIDATION_REPORT.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
