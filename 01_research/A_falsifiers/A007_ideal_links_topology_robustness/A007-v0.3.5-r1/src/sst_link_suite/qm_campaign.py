from __future__ import annotations

from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import traceback

from . import __version__
from .parser import parse_ideal_links, select_links
from .models import jsonable
from .native_ext import BackendOptions, backend_status
from .qm_readiness import analyze_qm_readiness
from .spectral import spectral_qm_preflight
from .qm_report import write_qm_tables, write_qm_plots, write_qm_markdown_report


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024*1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _signature(payload: dict) -> str:
    raw = json.dumps(jsonable(payload), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def _write_noncritical_reports(results: list[dict], summary, outdir: Path, metadata: dict, cfg: dict) -> list[dict]:
    """
    Numerical CSV/per-link ledgers are primary outputs. Plots and Markdown are
    presentation artifacts and may warn, but must not turn a completed campaign
    into a failed scientific run.
    """
    warnings = []
    if cfg.get("plots", True):
        try:
            write_qm_plots(summary, outdir)
        except Exception as exc:
            warnings.append({
                "stage": "plots",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            })
    try:
        write_qm_markdown_report(results, summary, outdir, metadata)
    except Exception as exc:
        warnings.append({
            "stage": "markdown_report",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        })
    if warnings:
        (outdir / "reporting_warnings.json").write_text(
            json.dumps(jsonable(warnings), indent=2), encoding="utf-8"
        )
    return warnings




def rebuild_qm_outputs(
    input_path: str | Path,
    output_dir: str | Path,
    cfg: dict,
    ids=None,
    all_database: bool = False,
) -> dict:
    input_path = Path(input_path)
    outdir = Path(output_dir)
    per_link = outdir / "per_link"
    links = select_links(parse_ideal_links(input_path), ids, all_database)
    results, failures = [], []
    signatures = set()
    for link in links:
        path = per_link / f"{link.link_id}.json"
        if not path.exists():
            failures.append({"link_id": link.link_id, "error": "missing per-link QM ledger"})
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        results.append(result)
        if result.get("run_signature"):
            signatures.add(result["run_signature"])
    if len(signatures) > 1:
        raise RuntimeError(f"Mixed QM run signatures in {per_link}: {sorted(signatures)}")
    backend = results[0].get("backend", {}) if results else {}
    metadata = {
        "suite_version": __version__,
        "run_signature": next(iter(signatures), None),
        "preset": cfg.get("name", "custom"),
        "input": str(input_path),
        "input_sha256": _sha256(input_path),
        "requested_ids": [link.link_id for link in links],
        "completed_ids": [result["link_id"] for result in results],
        "failures": failures,
        "elapsed_s": 0.0,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "backend": backend,
        "config": cfg,
        "rebuild_only": True,
    }
    (outdir / "qm_run_metadata.json").write_text(json.dumps(jsonable(metadata), indent=2), encoding="utf-8")
    if results:
        summary = write_qm_tables(results, outdir)
        reporting_warnings = _write_noncritical_reports(results, summary, outdir, metadata, cfg)
        metadata["reporting_warnings"] = reporting_warnings
        (outdir / "qm_run_metadata.json").write_text(
            json.dumps(jsonable(metadata), indent=2), encoding="utf-8"
        )
    return metadata


def run_qm_campaign(
    input_path: str | Path,
    output_dir: str | Path,
    cfg: dict,
    ids=None,
    all_database: bool = False,
    resume: bool = True,
    backend_options: BackendOptions | None = None,
) -> dict:
    backend_options = backend_options or BackendOptions()
    input_path = Path(input_path)
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    per_link = outdir / "per_link"
    per_link.mkdir(exist_ok=True)
    links = select_links(parse_ideal_links(input_path), ids, all_database)

    # v0.3.5: reject an inconsistent raw/configured bandwidth before native O(N^2) or Hessian work.
    preflight_rows = [spectral_qm_preflight(link, cfg) for link in links]
    preflight_payload = {
        "suite_version": __version__,
        "preset": cfg.get("name", "custom"),
        "input": str(input_path),
        "rows": preflight_rows,
        "blocked_ids": [row["link_id"] for row in preflight_rows if not row.get("pass", False)],
        "status": "[NUMERICAL] fail-fast QM spectral preflight; no Hessian is evaluated for a blocked campaign.",
    }
    (outdir / "qm_spectral_preflight.json").write_text(
        json.dumps(jsonable(preflight_payload), indent=2), encoding="utf-8"
    )
    abort_on_preflight = bool(cfg.get("abort_on_spectral_preflight_failure", True))
    if preflight_payload["blocked_ids"] and abort_on_preflight:
        failures = []
        by_id = {row["link_id"]: row for row in preflight_rows}
        for link_id in preflight_payload["blocked_ids"]:
            row = by_id[link_id]
            failures.append({
                "link_id": link_id,
                "stage": "spectral_preflight",
                "error": row.get("guard_error") or row.get("error") or "working geometry is spectrally under-resolved",
            })
        metadata = {
            "suite_version": __version__,
            "run_signature": None,
            "preset": cfg.get("name", "custom"),
            "input": str(input_path),
            "input_sha256": _sha256(input_path),
            "requested_ids": [link.link_id for link in links],
            "completed_ids": [],
            "failures": failures,
            "spectral_preflight": preflight_payload,
            "elapsed_s": 0.0,
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "backend": None,
            "config": cfg,
            "aborted_before_native_qm": True,
        }
        (outdir / "qm_run_metadata.json").write_text(json.dumps(jsonable(metadata), indent=2), encoding="utf-8")
        print(
            "QM spectral preflight aborted campaign before Hessian work. Blocked: "
            + ", ".join(preflight_payload["blocked_ids"]),
            flush=True,
        )
        return metadata

    backend = backend_status(backend_options)
    input_digest = _sha256(input_path)
    run_signature = _signature({
        "suite_version": __version__,
        "input_sha256": input_digest,
        "config": cfg,
        "backend_source_hash": backend.get("source_hash"),
        "backend": backend.get("backend"),
    })
    started = time.time()
    results, failures = [], []
    for number, link in enumerate(links, 1):
        path = per_link / f"{link.link_id}.json"
        if resume and path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            if previous.get("run_signature") == run_signature:
                print(f"[{number}/{len(links)}] resume {link.link_id}", flush=True)
                results.append(previous)
                continue
        print(f"[{number}/{len(links)}] QM-readiness {link.link_id}", flush=True)
        try:
            result = analyze_qm_readiness(link, cfg, backend_options, backend)
            result["run_signature"] = run_signature
            result = jsonable(result)
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
        "suite_version": __version__,
        "run_signature": run_signature,
        "preset": cfg.get("name", "custom"),
        "input": str(input_path),
        "input_sha256": input_digest,
        "requested_ids": [link.link_id for link in links],
        "completed_ids": [result["link_id"] for result in results],
        "failures": failures,
        "elapsed_s": time.time()-started,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "backend": backend,
        "config": cfg,
        "spectral_preflight": preflight_payload,
    }
    (outdir / "qm_run_metadata.json").write_text(json.dumps(jsonable(metadata), indent=2), encoding="utf-8")
    if results:
        summary = write_qm_tables(results, outdir)
        reporting_warnings = _write_noncritical_reports(results, summary, outdir, metadata, cfg)
        metadata["reporting_warnings"] = reporting_warnings
        (outdir / "qm_run_metadata.json").write_text(
            json.dumps(jsonable(metadata), indent=2), encoding="utf-8"
        )
    return metadata
