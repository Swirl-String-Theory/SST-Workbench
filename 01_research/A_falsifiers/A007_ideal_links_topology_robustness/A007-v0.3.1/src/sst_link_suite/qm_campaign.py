from __future__ import annotations

from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import traceback

from .parser import parse_ideal_links, select_links
from .models import jsonable
from .native_ext import BackendOptions, backend_status
from .qm_readiness import analyze_qm_readiness
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
        "suite_version": "0.3.0",
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
        if cfg.get("plots", True):
            write_qm_plots(summary, outdir)
        write_qm_markdown_report(results, summary, outdir, metadata)
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
    backend = backend_status(backend_options)
    input_digest = _sha256(input_path)
    run_signature = _signature({
        "suite_version": "0.3.0",
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
        "suite_version": "0.3.0",
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
    }
    (outdir / "qm_run_metadata.json").write_text(json.dumps(jsonable(metadata), indent=2), encoding="utf-8")
    if results:
        summary = write_qm_tables(results, outdir)
        if cfg.get("plots", True):
            write_qm_plots(summary, outdir)
        write_qm_markdown_report(results, summary, outdir, metadata)
    return metadata
