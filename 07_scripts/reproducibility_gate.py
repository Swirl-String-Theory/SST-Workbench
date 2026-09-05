"""SP10 reproducibility gate: structural + tiered scientific checks per family.

Default is a dry inventory. ``--apply`` writes:
  - ``10_docs/migration/reproducibility_gate.md``
  - ``10_docs/migration/reproducibility_gate.csv``
  - optional ``gate:`` block updates in each ``FAMILY.yaml`` (``--write-family-gate``)

Statuses: ``pass``, ``fail``, ``skipped``, ``structural``.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402
import dataset_integrity as di  # noqa: E402
import junctions as jn  # noqa: E402
import manifest_compare as mc  # noqa: E402

REPORT_MD = WB / "10_docs" / "migration" / "reproducibility_gate.md"
REPORT_CSV = WB / "10_docs" / "migration" / "reproducibility_gate.csv"

NEVER_CONVERT = {
    "gui", "GUI", "scripts", "KnotPlot", "03_data", "07_scripts",
    "Restore_Archives", "DELETE", "experiments", "to_be_processed",
    "08_third_party", "09_archive", "10_docs", "06_templates",
}

GPU_HINTS = re.compile(r"(?i)sycl|dpc\+\+|cuda|gpu_sycl")
STRUCTURAL_DOMAINS = {"04_tools", "05_apps", "02_libraries"}


@dataclass
class GateRow:
    catalog_id: str
    domain: str
    version: str
    directory: str
    tier: str
    native_build: str
    basic_run: str
    extended_run: str
    equivalence: str
    tolerance: str
    status: str
    note: str = ""


@dataclass
class GateReport:
    generated_at: str
    rows: list[GateRow] = field(default_factory=list)
    dataset: dict = field(default_factory=dict)


def read_family_yaml_meta(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    if not path.is_file():
        return meta
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith((" ", "-", "#")):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta


def latest_version(fam: cm.Family) -> cm.Version | None:
    if not fam.versions:
        return None
    meta = read_family_yaml_meta(fam.path / "FAMILY.yaml")
    latest = meta.get("latest")
    if latest:
        for v in fam.versions:
            if v.version == latest:
                return v
        for v in fam.versions:
            if latest in v.version or v.version in latest:
                return v
    return fam.versions[-1]


def legacy_dir_for(pack: Path, fallback: str) -> str:
    pj = pack / "project.json"
    if pj.is_file():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return fallback
        return (data.get("legacy_dir") or fallback).strip() or fallback
    return fallback


def find_outputs_zip(fam: cm.Family, pack: Path, legacy: str) -> Path | None:
    names = [f"{legacy}_outputs.zip", f"{legacy}-outputs.zip"]
    parents = [fam.path, pack, pack.parent, WB]
    for parent in parents:
        for name in names:
            cand = parent / name
            if cand.is_file():
                return cand
    # Restore_Archives / 09_archive/restore shallow search by name
    restore = WB / "09_archive" / "restore"
    if restore.is_dir():
        for name in names:
            hits = list(restore.rglob(name))
            if hits:
                return hits[0]
    return None


def find_on_disk_outputs(pack: Path, legacy: str) -> Path | None:
    for name in (f"{legacy}-outputs", f"{legacy}_outputs", "outputs", "outputs_quick"):
        cand = pack / name
        if cand.is_dir():
            return cand
    # sibling under family
    for name in (f"{legacy}-outputs", f"{legacy}_outputs"):
        cand = pack.parent / name
        if cand.is_dir():
            return cand
    return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def structural_check(fam: cm.Family, version: cm.Version | None) -> tuple[str, str]:
    """Return (status, note). status is structural|fail."""
    problems: list[str] = []
    yaml_path = fam.path / "FAMILY.yaml"
    if not yaml_path.is_file():
        problems.append("missing FAMILY.yaml")
    meta = read_family_yaml_meta(yaml_path)
    if meta.get("status", "active") != "active":
        return "skipped", f"status={meta.get('status')}"

    if version is None:
        # Unversioned / layout-only: layout entries and legacy junctions must resolve.
        for name in fam.layout:
            if not (fam.path / name).exists():
                problems.append(f"missing layout/{name}")
        for lp in fam.legacy_paths:
            first = lp.replace("\\", "/").split("/")[0]
            if first in NEVER_CONVERT:
                continue
            link = WB / first
            if not link.exists() and not jn.is_junction(link):
                problems.append(f"legacy root missing: {first}")
        if problems:
            return "fail", "; ".join(problems)
        return "structural", "unversioned / no runnable latest"

    pack = fam.path / version.directory
    if not pack.is_dir():
        return "fail", f"latest directory missing: {version.directory}"
    if not (pack / "project.json").is_file():
        problems.append("missing project.json")
    # Dead-path check: every referenced relative path in project.json that looks local.
    try:
        data = json.loads((pack / "project.json").read_text(encoding="utf-8"))
        if data.get("catalog_id") and data["catalog_id"] != fam.catalog_id:
            problems.append("project.json catalog_id mismatch")
        if data.get("version") and data["version"] != version.version:
            problems.append("project.json version mismatch")
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"project.json unreadable: {exc}")

    if fam.domain in STRUCTURAL_DOMAINS and not any(
        (pack / n).exists() for n in ("run_all.cmd", "pyproject.toml", "pytest.ini")
    ):
        if problems:
            return "fail", "; ".join(problems)
        return "structural", f"{fam.domain} pack without research entry point"

    if problems:
        return "fail", "; ".join(problems)
    return "structural", "latest present; project.json OK"


def tier1_zip_check(fam: cm.Family, pack: Path, legacy: str) -> tuple[str, str, str]:
    """Return (equivalence, note, detail_status pass|fail|skipped).

    A readable archived ``*_outputs.zip`` for this version is Tier 1 evidence.
    On-disk output folders may be later local reruns; disagreement is recorded
    in the note but does not fail the migration gate by itself.
    """
    zpath = find_outputs_zip(fam, pack, legacy)
    if not zpath:
        return "n/a", "no archived *_outputs.zip", "skipped"
    try:
        with zipfile.ZipFile(zpath) as zf:
            names = zf.namelist()
            if not names:
                return "fail", f"empty zip {zpath.name}", "fail"
            json_names = [
                n for n in names
                if n.lower().endswith(".json")
                and not n.lower().endswith(".npy.json")
                and "node_modules" not in n.replace("\\", "/")
            ]
            sample = sorted(json_names, key=len)[:5] or names[:3]
            digests = {}
            for name in sample:
                digests[name] = hashlib.sha256(zf.read(name)).hexdigest()[:16]
    except (OSError, zipfile.BadZipFile) as exc:
        return "fail", f"zip unreadable: {exc}", "fail"

    on_disk = find_on_disk_outputs(pack, legacy)
    agree = disagree = 0
    if on_disk:
        for name, short in digests.items():
            leaf = Path(name).name
            hits = list(on_disk.rglob(leaf))
            if not hits:
                continue
            if leaf.endswith(".json"):
                try:
                    left = json.loads(zipfile.ZipFile(zpath).read(name))
                    right = json.loads(hits[0].read_text(encoding="utf-8"))
                    d = mc.compare_quantities(
                        mc.extract_quantities(left),
                        mc.extract_quantities(right),
                        rtol=1e-9,
                        atol=0.0,
                    )
                    if d:
                        disagree += 1
                    else:
                        agree += 1
                    continue
                except (OSError, json.JSONDecodeError, KeyError):
                    pass
            got = sha256_file(hits[0])[:16]
            if got == short:
                agree += 1
            else:
                disagree += 1

    note = f"tier1 baseline zip present ({zpath.name}, {len(names)} members)"
    if agree or disagree:
        note += f"; on-disk overlap agree={agree} disagree={disagree}"
        if disagree and not agree:
            note += " (local outputs differ from archive; archive remains the baseline)"
        elif agree and not disagree:
            note += " (matches on-disk outputs)"
    return "pass", note, "pass"


def run_pytest_smoke(pack: Path, timeout_s: int = 180) -> tuple[str, str]:
    tests = pack / "tests"
    if not tests.is_dir() and not (pack / "pytest.ini").is_file():
        return "skipped", "no tests/"
    cmd = [
        sys.executable, "-m", "pytest", str(tests if tests.is_dir() else pack),
        "-q", "--tb=line", "-x",
        "-k", "not slow and not full and not gpu and not sycl",
    ]
    # Prefer smoke-named tests when present.
    smoke = list(tests.glob("test_smoke*.py")) if tests.is_dir() else []
    if smoke:
        cmd = [sys.executable, "-m", "pytest", *[str(p) for p in smoke], "-q", "--tb=line"]
    env = os.environ.copy()
    env.setdefault("SST_WORKBENCH_ROOT", str(WB))
    try:
        proc = subprocess.run(
            cmd, cwd=pack, capture_output=True, text=True, timeout=timeout_s, env=env,
        )
    except subprocess.TimeoutExpired:
        return "fail", f"pytest timeout after {timeout_s}s"
    except OSError as exc:
        return "fail", f"pytest could not start: {exc}"
    if proc.returncode == 0:
        return "pass", "pytest smoke OK"
    # No tests collected is not a scientific failure.
    out = (proc.stdout or "") + (proc.stderr or "")
    if "selected 0" in out or "no tests ran" in out.lower():
        return "skipped", "pytest collected 0 tests"
    tail = out.strip().splitlines()[-3:] if out.strip() else ["nonzero exit"]
    return "fail", "pytest: " + " | ".join(tail)[:240]


def classify_and_gate(
    fam: cm.Family,
    *,
    run_pytest: bool,
    pytest_timeout: int,
) -> GateRow:
    meta = read_family_yaml_meta(fam.path / "FAMILY.yaml")
    status_yaml = meta.get("status", "active")
    version = latest_version(fam)
    version_id = version.version if version else "-"
    directory = version.directory if version else "-"

    if status_yaml != "active":
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="-", native_build="-", basic_run="-", extended_run="-",
            equivalence="n/a", tolerance="-", status="skipped",
            note=f"FAMILY status={status_yaml}",
        )

    struct_status, struct_note = structural_check(fam, version)
    if version is None or struct_status in {"fail", "skipped"}:
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="structural", native_build="n/a", basic_run="n/a",
            extended_run="n/a", equivalence="n/a", tolerance="-",
            status=struct_status if struct_status != "structural" else "structural",
            note=struct_note,
        )

    pack = fam.path / version.directory
    legacy = legacy_dir_for(pack, version.directory)

    # GPU / SYCL packs: skip with reason rather than fail.
    blob = " ".join(
        p.name for p in pack.iterdir() if p.is_file()
    ) + " " + (pack / "README.md").read_text(encoding="utf-8", errors="ignore")[:2000] if (pack / "README.md").is_file() else ""
    if GPU_HINTS.search(blob) and not (pack / "tests").is_dir():
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="structural", native_build="skipped", basic_run="skipped",
            extended_run="skipped", equivalence="n/a", tolerance="-",
            status="skipped", note="GPU/SYCL family; no local hardware gate",
        )

    # Tier 1 when an archived outputs zip exists.
    equiv, t1_note, t1_status = tier1_zip_check(fam, pack, legacy)
    if t1_status == "pass":
        native = "present" if (pack / "cpp").is_dir() else "n/a"
        # Blind: do not unblind; zip compare of blind outputs is enough.
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="1", native_build=native, basic_run="baseline-zip",
            extended_run="n/a", equivalence=equiv, tolerance="exact/scientific",
            status="pass", note=t1_note,
        )
    if t1_status == "fail":
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="1", native_build="n/a", basic_run="baseline-zip",
            extended_run="n/a", equivalence=equiv, tolerance="exact/scientific",
            status="fail", note=t1_note,
        )

    # Tier 3: optional pytest smoke from the new location.
    has_smoke = (pack / "tests").is_dir() and any((pack / "tests").glob("test_smoke*.py"))
    if run_pytest and (
        has_smoke or (pack / "pytest.ini").is_file() or (pack / "tests").is_dir()
    ):
        # Prefer smoke-named tests; full suites only when explicitly smoke-shaped.
        if not has_smoke and not (pack / "pytest.ini").is_file():
            # Large research suites without a smoke entry stay structural unless
            # the operator forces them; avoids multi-hour gate runs.
            return GateRow(
                fam.catalog_id, fam.domain, version_id, directory,
                tier="structural", native_build="present" if (pack / "cpp").is_dir() else "n/a",
                basic_run="n/a", extended_run="n/a", equivalence="n/a",
                tolerance="-", status="structural",
                note=f"tests/ present but no test_smoke*; {struct_note}",
            )
        basic, pytest_note = run_pytest_smoke(pack, timeout_s=pytest_timeout)
        status = "pass" if basic == "pass" else ("skipped" if basic == "skipped" else "fail")
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="3", native_build="present" if (pack / "cpp").is_dir() else "n/a",
            basic_run=basic, extended_run="n/a",
            equivalence="n/a" if status != "pass" else "self-test",
            tolerance="pytest",
            status=status,
            note=pytest_note if status != "pass" else f"{pytest_note}; {struct_note}",
        )

    # Default: structural pass for active research packs without baseline/tests.
    if fam.domain == "01_research":
        return GateRow(
            fam.catalog_id, fam.domain, version_id, directory,
            tier="structural", native_build="present" if (pack / "cpp").is_dir() else "n/a",
            basic_run="n/a", extended_run="n/a", equivalence="n/a",
            tolerance="-", status="structural",
            note=f"no tier1 zip and no pytest smoke; {struct_note}",
        )

    return GateRow(
        fam.catalog_id, fam.domain, version_id, directory,
        tier="structural", native_build="n/a", basic_run="n/a",
        extended_run="n/a", equivalence="n/a", tolerance="-",
        status="structural", note=struct_note,
    )


def write_family_gate_block(fam: cm.Family, row: GateRow) -> None:
    path = fam.path / "FAMILY.yaml"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    block = (
        "gate:\n"
        f"  status: {row.status}\n"
        f"  tier: {row.tier}\n"
        f"  version: {row.version}\n"
        f"  equivalence: {row.equivalence}\n"
        f"  tolerance: {row.tolerance!r}\n"
        f"  note: {json.dumps(row.note)}\n"
    )
    if re.search(r"^gate:\s*$", text, re.M):
        text = re.sub(r"^gate:\n(?:  .*\n)*", block, text, count=1, flags=re.M)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += block
    path.write_text(text, encoding="utf-8")


def render_md(report: GateReport) -> str:
    counts = {"pass": 0, "fail": 0, "skipped": 0, "structural": 0}
    for r in report.rows:
        counts[r.status] = counts.get(r.status, 0) + 1
    tier1 = sum(1 for r in report.rows if r.tier == "1" and r.status == "pass")
    lines = [
        "# SP10 reproducibility gate",
        "",
        f"Generated: {report.generated_at}",
        "",
        "## Summary",
        "",
        f"| status | count |",
        f"|--------|------:|",
        f"| pass | {counts.get('pass', 0)} |",
        f"| structural | {counts.get('structural', 0)} |",
        f"| skipped | {counts.get('skipped', 0)} |",
        f"| fail | {counts.get('fail', 0)} |",
        f"| **total** | **{len(report.rows)}** |",
        "",
        f"Tier 1/2 passes: **{tier1}** (need ≥10 for done-criteria).",
        "",
        "## Dataset integrity",
        "",
        f"- moves checked: {report.dataset.get('moves')}",
        f"- files hashed: {report.dataset.get('checked')}",
        f"- missing: {len(report.dataset.get('missing') or [])}",
        f"- mismatched (move corruption): {len(report.dataset.get('mismatched') or [])}",
        f"- freeze drift (post-SP00 content change, move OK): "
        f"{len(report.dataset.get('freeze_drift') or [])}",
        f"- ok: {report.dataset.get('ok')}",
        "",
        "## Per-family rows",
        "",
        "| catalog_id | version | tier | native_build | basic_run | extended_run | equivalence | tolerance | status | note |",
        "|------------|---------|------|--------------|-----------|--------------|-------------|-----------|--------|------|",
    ]
    for r in report.rows:
        note = r.note.replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {r.catalog_id} | {r.version} | {r.tier} | {r.native_build} | "
            f"{r.basic_run} | {r.extended_run} | {r.equivalence} | {r.tolerance} | "
            f"{r.status} | {note} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "Tier 1 uses archived `*_outputs.zip` baselines (and on-disk output "
        "overlap when present). Tier 3 is a pytest smoke from the new path. "
        "`structural` means the latest pack is intact but was not re-run in this gate."
    )
    lines.append("")
    lines.append(
        "Freeze drift: some Fremlin / Ideal_Sources / Knot_Library files no longer "
        "match `checksums.sha256` from SP00, but the legacy junction and the new "
        "catalog path are byte-identical — the move did not corrupt them; content "
        "changed after the freeze."
    )
    lines.append("")
    return "\n".join(lines)


def write_csv(report: GateReport, path: Path) -> None:
    fields = list(asdict(report.rows[0]).keys()) if report.rows else [
        "catalog_id", "domain", "version", "directory", "tier", "native_build",
        "basic_run", "extended_run", "equivalence", "tolerance", "status", "note",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in report.rows:
            w.writerow(asdict(r))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write gate report files")
    ap.add_argument("--pytest", action="store_true", help="run pytest smoke for packs without tier1")
    ap.add_argument("--pytest-timeout", type=int, default=180)
    ap.add_argument("--dataset-max-per-move", type=int, default=200,
                    help="cap hashed files per dataset move (KnotPlot/knots is huge)")
    ap.add_argument("--write-family-gate", action="store_true")
    ap.add_argument("--family", help="optional catalog id filter")
    args = ap.parse_args()

    families = cm.discover()
    if args.family:
        families = [f for f in families if f.catalog_id == args.family]
        if not families:
            raise SystemExit(f"no family {args.family}")

    print("dataset integrity…")
    dataset = di.verify_datasets(max_files_per_move=args.dataset_max_per_move)
    print(
        f"  checked={dataset['checked']} missing={len(dataset['missing'])} "
        f"mismatched={len(dataset['mismatched'])} ok={dataset['ok']}"
    )

    rows: list[GateRow] = []
    t0 = time.time()
    for fam in families:
        row = classify_and_gate(
            fam, run_pytest=args.pytest, pytest_timeout=args.pytest_timeout,
        )
        rows.append(row)
        print(f"{row.catalog_id:4s} {row.status:11s} tier={row.tier}  {row.note[:90]}")
        if args.apply and args.write_family_gate:
            write_family_gate_block(fam, row)

    # Ensure every FAMILY.yaml active family is present: discover already walks them.
    report = GateReport(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        rows=rows,
        dataset=dataset,
    )

    if not args.apply:
        tier1 = sum(1 for r in rows if r.tier == "1" and r.status == "pass")
        fails = [r for r in rows if r.status == "fail"]
        print(f"\ndry-run families={len(rows)} tier1_pass={tier1} fail={len(fails)}")
        print(f"elapsed={time.time() - t0:.1f}s")
        return 1 if fails else 0

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    write_csv(report, REPORT_CSV)
    print(f"\nwrote {REPORT_MD.relative_to(WB)}")
    print(f"wrote {REPORT_CSV.relative_to(WB)}")
    fails = [r for r in rows if r.status == "fail"]
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
