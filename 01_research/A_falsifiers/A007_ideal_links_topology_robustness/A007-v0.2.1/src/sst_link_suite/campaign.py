from __future__ import annotations
from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import traceback

from .parser import parse_ideal_links, select_links
from .analysis import analyze_link
from .fourier import sample_component
from .biot_savart import sign_matrix
from .models import jsonable
from .report import write_tables, write_plots, write_markdown_report
from .native_ext import BackendOptions, NativeBackendError, backend_status
from .native_ext.audit import run_native_parity_audit


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stable_hash(value: dict) -> str:
    payload = json.dumps(jsonable(value), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _representative_links(links):
    representatives = []
    two_component = next((link for link in links if len(link.components) == 2), None)
    three_component = next((link for link in links if len(link.components) == 3), None)
    if two_component is not None:
        representatives.append(two_component)
    if three_component is not None and three_component not in representatives:
        representatives.append(three_component)
    if not representatives and links:
        representatives.append(links[0])
    return representatives


def _native_parity_ledger(links, cfg: dict, options: BackendOptions, status: dict) -> dict:
    if status["backend"] != "cpp":
        return {
            "status": "skipped",
            "reason": "native backend unavailable or Python explicitly selected",
            "ok": not options.require_native,
            "representatives": [],
        }
    if not cfg.get("native_parity", True):
        return {
            "status": "disabled",
            "reason": "native_parity=false in configuration",
            "ok": True,
            "representatives": [],
        }
    n = int(cfg.get("parity_sample_n", 128))
    epsilons = [float(value) for value in cfg.get("parity_epsilons_D", [0.05, 0.1])]
    reports = []
    for link in _representative_links(links):
        curves = [sample_component(component, n).r for component in link.components]
        report = run_native_parity_audit(
            curves,
            sign_matrix(len(curves)),
            epsilons,
            options,
            abs_tolerance=float(cfg.get("native_abs_tolerance", 2e-11)),
            relative_tolerance=float(cfg.get("native_relative_tolerance", 2e-11)),
            local_skip_velocity=int(cfg.get("local_skip_velocity", 3)),
            local_skip_energy=int(cfg.get("local_skip_energy", 2)),
        )
        reports.append({"link_id": link.link_id, "sample_n": n, **report})
    return {
        "status": "completed",
        "ok": all(report["ok"] for report in reports),
        "representatives": reports,
    }


def run_campaign(
    input_path: str | Path,
    output_dir: str | Path,
    cfg: dict,
    ids=None,
    all_database: bool = False,
    resume: bool = True,
    backend_options: BackendOptions | None = None,
) -> dict:
    backend_options = backend_options or BackendOptions()
    input_path, outdir = Path(input_path), Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    per_link_dir = outdir / "per_link"
    per_link_dir.mkdir(exist_ok=True)

    all_links = parse_ideal_links(input_path)
    links = select_links(all_links, ids, all_database)
    started = time.time()
    input_digest = sha256(input_path)
    status = backend_status(backend_options)
    parity = _native_parity_ledger(links, cfg, backend_options, status)
    (outdir / "native_audit.json").write_text(
        json.dumps(jsonable(parity), indent=2), encoding="utf-8"
    )
    if not parity["ok"] and (backend_options.require_native or cfg.get("enforce_native_parity", True)):
        raise NativeBackendError(
            "Native/Python parity gate failed. Inspect native_audit.json; campaign was not started."
        )

    signature_payload = {
        "suite_version": "0.2.1",
        "input_sha256": input_digest,
        "config": cfg,
        "backend": status,
    }
    run_signature = _stable_hash(signature_payload)
    results, failures = [], []

    for number, link in enumerate(links, 1):
        path = per_link_dir / f"{link.link_id}.json"
        if resume and path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            if previous.get("run_signature") == run_signature:
                results.append(previous)
                print(f"[{number}/{len(links)}] resume {link.link_id}", flush=True)
                continue
            print(f"[{number}/{len(links)}] stale result -> recompute {link.link_id}", flush=True)
        else:
            print(f"[{number}/{len(links)}] analyze {link.link_id}", flush=True)
        try:
            result = jsonable(analyze_link(
                link, cfg, backend_options, status, run_signature
            ))
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            results.append(result)
        except Exception as exc:
            failures.append({
                "link_id": link.link_id,
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            })
            print(f"FAILED {link.link_id}: {exc}", flush=True)

    metadata = {
        "suite_version": "0.2.1",
        "run_signature": run_signature,
        "preset": cfg.get("name", "custom"),
        "input": str(input_path),
        "input_sha256": input_digest,
        "requested_ids": [link.link_id for link in links],
        "completed_ids": [result["link_id"] for result in results],
        "failures": failures,
        "elapsed_s": time.time() - started,
        "python": sys.version,
        "platform": platform.platform(),
        "backend": status,
        "native_audit": parity,
        "config": cfg,
    }
    (outdir / "run_metadata.json").write_text(
        json.dumps(jsonable(metadata), indent=2), encoding="utf-8"
    )
    if results:
        summary = write_tables(results, outdir)
        if cfg.get("plots", True):
            write_plots(summary, outdir)
        write_markdown_report(results, summary, outdir, metadata)
    return metadata
