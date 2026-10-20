"""Non-overwriting, run-scoped publication and archival for SST falsifier outputs.

No change to scientific gates, protocol hashes or backend kernels. Existing pipelines
continue to write into their canonical <name>_<version>-outputs working directory.
Previous working trees are renamed (not deleted) before a fresh blind run begins.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import secrets

from .util import write_json

_RUN_RE = re.compile(r"^[0-9]{8}T[0-9]{12}Z-[0-9a-f]{8}$")


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)


def assert_run_id(value: str) -> str:
    if not _RUN_RE.fullmatch(str(value)):
        raise ValueError(f"invalid immutable SST run ID: {value!r}")
    return value


def read_run_id(out: Path) -> str:
    payload = json.loads((Path(out) / "RUN_ID.json").read_text(encoding="utf-8"))
    return assert_run_id(payload["run_id"])


def reserve_blind_output(root: Path, out: Path, cfg: dict, mode: str) -> tuple[str, Path | None]:
    """Archive previous canonical tree without deleting or overwriting any run.

    Exclusive lock must be held by caller. A newly created canonical working tree
    is returned, and no old tree is ever recursively deleted.
    """
    root, out = Path(root), Path(out)
    prior = None
    if out.exists():
        if not out.is_dir() or out.is_symlink():
            raise FileExistsError(f"refusing to replace non-directory or symlink: {out}")
        try:
            prior_id = read_run_id(out)
        except FileNotFoundError:
            prior_id = "LEGACY-" + new_run_id()
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid existing RUN_ID.json; refusing destructive replacement: {out}: {exc}") from exc
        prior = out.parent / f"{out.name}__{prior_id}"
        if prior.exists():
            raise FileExistsError(f"archive name exists; refusing replacement: {prior}")
        out.rename(prior)
    run_id = new_run_id()
    out.mkdir(exist_ok=False)
    write_json(out / "RUN_ID.json", {
        "schema": "SST-RUN-IDENTITY-1", "run_id": run_id,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode, "instance": root.name,
        "project_name": cfg["project"]["name"],
        "project_version": cfg["project"]["version"],
        "framework_version": "1.0.9", "archived_previous": str(prior) if prior else None,
    })
    return run_id, prior


def package_path(root: Path, cfg: dict, run_id: str, phase: str) -> Path:
    assert_run_id(run_id)
    if phase not in {"BLIND", "REVEALED"}:
        raise ValueError(f"invalid phase: {phase!r}")
    p = cfg["project"]
    return Path(root).parent / f"{p['name']}_{p['version']}-outputs__{run_id}_{phase}.zip"


def report_path(root: Path, run_id: str, phase: str) -> Path:
    assert_run_id(run_id)
    if phase not in {"BLIND", "REVEALED"}:
        raise ValueError(f"invalid phase: {phase!r}")
    root = Path(root)
    return root.parent / f"{root.name}__{run_id}_{phase}_FALSIFIER_REPORT.pdf"


def report_revision_path(root: Path, run_id: str, phase: str) -> Path:
    """Create a distinct report-only publication identity, never modify prior PDFs."""
    assert_run_id(run_id)
    if phase not in {"BLIND", "REVEALED"}:
        raise ValueError(f"invalid phase: {phase!r}")
    return Path(root).parent / (f"{Path(root).name}__{run_id}_{phase}_RERENDER_"
                                f"{new_run_id()}_FALSIFIER_REPORT.pdf")


@contextmanager
def instance_lock(root: Path):
    """Fail-closed process lock across a blind or reveal transaction."""
    root = Path(root)
    lock = root.parent / f".{root.name}.sst-run.lock"
    try:
        with lock.open("x", encoding="utf-8") as fh:
            fh.write(f"pid={os.getpid()}\ncreated_utc={datetime.now(timezone.utc).isoformat()}\n")
    except FileExistsError:
        raise RuntimeError(f"another run is active (or a stale lock remains): {lock}") from None
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)
