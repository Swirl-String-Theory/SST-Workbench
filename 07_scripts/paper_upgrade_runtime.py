"""Resume-able stage runner + heartbeat logging for paper-upgrade campaigns.

Usage (from a family directory)::

    python %WB%\\07_scripts\\paper_upgrade_runtime.py init --family A034 --tier basic --out outputs\\basic
    python %WB%\\07_scripts\\paper_upgrade_runtime.py stage --out outputs\\basic --family A034 --id setup -- run_setup.cmd

Env:
    SST_RESUME=1          treat as resume (skip stages with .done)
    SST_FRESH=1           ignore prior markers (force full rerun)
    SST_FORCE_STAGE=id    delete that stage marker before run
    SST_HEARTBEAT_SEC=60  ALIVE interval (seconds); use 1 in tests
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _out_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    (p / "stages").mkdir(parents=True, exist_ok=True)
    return p


def _state_path(out: Path) -> Path:
    return out / "run_state.json"


def _heartbeat_path(out: Path) -> Path:
    return out / "heartbeat.log"


def _done_path(out: Path, stage_id: str) -> Path:
    safe = stage_id.replace("/", "_").replace("\\", "_")
    return out / "stages" / f"{safe}.done"


def heartbeat_line(
    family: str,
    tier: str,
    stage: str,
    event: str,
    *,
    elapsed_s: float | None = None,
    detail: str = "",
) -> str:
    parts = [
        _utc_now(),
        "HEARTBEAT",
        f"family={family}",
        f"tier={tier}",
        f"stage={stage}",
        f"event={event}",
    ]
    if elapsed_s is not None:
        parts.append(f"elapsed_s={int(elapsed_s)}")
    if detail:
        parts.append(f"detail={detail}")
    return " ".join(parts)


def append_heartbeat(out: Path, line: str) -> None:
    path = _heartbeat_path(out)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line, flush=True)


def load_state(out: Path) -> dict[str, Any]:
    sp = _state_path(out)
    if not sp.is_file():
        return {}
    return json.loads(sp.read_text(encoding="utf-8"))


def save_state(out: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = _utc_now()
    _state_path(out).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init_run(*, family: str, tier: str, out: str | Path, resume: bool | None = None) -> dict[str, Any]:
    out_p = _out_dir(out)
    if resume is None:
        resume = os.environ.get("SST_RESUME", "").strip() not in ("", "0", "false", "False")
    if os.environ.get("SST_FRESH", "").strip() in ("1", "true", "True"):
        resume = False
        # wipe markers
        for p in (out_p / "stages").glob("*.done"):
            p.unlink(missing_ok=True)
        if _heartbeat_path(out_p).is_file() and not resume:
            # keep history but mark fresh section
            append_heartbeat(
                out_p,
                heartbeat_line(family, tier, "-", "START", detail="fresh_run"),
            )

    force = os.environ.get("SST_FORCE_STAGE", "").strip()
    if force:
        _done_path(out_p, force).unlink(missing_ok=True)

    state = {
        "family": family,
        "tier": tier,
        "status": "RUNNING",
        "resume": bool(resume),
        "stages": [],
        "started_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    prev = load_state(out_p)
    if resume and prev.get("stages"):
        # carry forward DONE stages
        state["stages"] = [s for s in prev["stages"] if s.get("status") == "DONE"]
        state["started_at"] = prev.get("started_at", state["started_at"])
    save_state(out_p, state)
    append_heartbeat(
        out_p,
        heartbeat_line(family, tier, "-", "START", detail="resume" if resume else "new"),
    )
    return state


def _upsert_stage(state: dict[str, Any], stage_id: str, status: str) -> None:
    stages = list(state.get("stages") or [])
    found = False
    for s in stages:
        if s.get("id") == stage_id:
            s["status"] = status
            if status == "RUNNING":
                s["started_at"] = _utc_now()
            if status in ("DONE", "FAILED", "SKIP"):
                s["ended_at"] = _utc_now()
            found = True
            break
    if not found:
        entry: dict[str, Any] = {"id": stage_id, "status": status}
        if status == "RUNNING":
            entry["started_at"] = _utc_now()
        if status in ("DONE", "FAILED", "SKIP"):
            entry["ended_at"] = _utc_now()
        stages.append(entry)
    state["stages"] = stages


class _HeartbeatThread(threading.Thread):
    def __init__(self, out: Path, family: str, tier: str, stage: str, interval: float):
        super().__init__(daemon=True)
        self._stop = threading.Event()
        self.out = out
        self.family = family
        self.tier = tier
        self.stage = stage
        self.interval = max(0.1, float(interval))
        self.t0 = time.monotonic()

    def run(self) -> None:
        while not self._stop.wait(self.interval):
            append_heartbeat(
                self.out,
                heartbeat_line(
                    self.family,
                    self.tier,
                    self.stage,
                    "ALIVE",
                    elapsed_s=time.monotonic() - self.t0,
                ),
            )

    def stop(self) -> None:
        self._stop.set()


def run_stage(
    *,
    family: str,
    tier: str,
    out: str | Path,
    stage_id: str,
    argv: list[str],
    cwd: str | Path | None = None,
    resume: bool | None = None,
    heartbeat_sec: float | None = None,
) -> int:
    out_p = _out_dir(out)
    if resume is None:
        resume = os.environ.get("SST_RESUME", "").strip() not in ("", "0", "false", "False")
        if os.environ.get("SST_FRESH", "").strip() in ("1", "true", "True"):
            resume = False
    if heartbeat_sec is None:
        heartbeat_sec = float(os.environ.get("SST_HEARTBEAT_SEC", "60") or "60")

    state = load_state(out_p) or {
        "family": family,
        "tier": tier,
        "status": "RUNNING",
        "resume": bool(resume),
        "stages": [],
        "started_at": _utc_now(),
    }
    state["family"] = family
    state["tier"] = tier

    done = _done_path(out_p, stage_id)
    if resume and done.is_file():
        append_heartbeat(
            out_p,
            heartbeat_line(family, tier, stage_id, "SKIP", detail="done_marker"),
        )
        _upsert_stage(state, stage_id, "SKIP")
        # normalize SKIP of already-done as still DONE in ledger
        _upsert_stage(state, stage_id, "DONE")
        save_state(out_p, state)
        return 0

    append_heartbeat(out_p, heartbeat_line(family, tier, stage_id, "START"))
    _upsert_stage(state, stage_id, "RUNNING")
    state["status"] = "RUNNING"
    save_state(out_p, state)

    hb = _HeartbeatThread(out_p, family, tier, stage_id, heartbeat_sec)
    hb.start()
    t0 = time.monotonic()
    try:
        if not argv:
            raise SystemExit("stage requires a command after --")
        # On Windows, .cmd/.bat need shell
        use_shell = os.name == "nt" and (
            argv[0].lower().endswith((".cmd", ".bat")) or argv[0].lower() in ("call", "cmd")
        )
        if use_shell and argv[0].lower() != "cmd":
            # run via cmd /c
            cmd = subprocess.list2cmdline(argv)
            proc = subprocess.run(cmd, shell=True, cwd=cwd)
        else:
            proc = subprocess.run(argv, cwd=cwd)
        rc = int(proc.returncode)
    except Exception as exc:  # noqa: BLE001 — surface to heartbeat then re-raise path via rc
        append_heartbeat(
            out_p,
            heartbeat_line(family, tier, stage_id, "FAIL", elapsed_s=time.monotonic() - t0, detail=str(exc)),
        )
        _upsert_stage(state, stage_id, "FAILED")
        state["status"] = "FAILED"
        save_state(out_p, state)
        hb.stop()
        hb.join(timeout=2)
        return 1
    finally:
        hb.stop()
        hb.join(timeout=2)

    elapsed = time.monotonic() - t0
    if rc == 0:
        done.write_text(_utc_now() + "\n", encoding="utf-8")
        append_heartbeat(
            out_p,
            heartbeat_line(family, tier, stage_id, "DONE", elapsed_s=elapsed),
        )
        _upsert_stage(state, stage_id, "DONE")
        save_state(out_p, state)
        return 0

    append_heartbeat(
        out_p,
        heartbeat_line(family, tier, stage_id, "FAIL", elapsed_s=elapsed, detail=f"rc={rc}"),
    )
    _upsert_stage(state, stage_id, "FAILED")
    state["status"] = "FAILED"
    save_state(out_p, state)
    return rc


def finish_run(*, family: str, tier: str, out: str | Path, status: str = "DONE") -> None:
    out_p = _out_dir(out)
    state = load_state(out_p) or {"family": family, "tier": tier, "stages": []}
    state["status"] = status
    state["family"] = family
    state["tier"] = tier
    save_state(out_p, state)
    append_heartbeat(out_p, heartbeat_line(family, tier, "-", status))


def _split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" in argv:
        i = argv.index("--")
        return argv[:i], argv[i + 1 :]
    return argv, []


def find_workbench(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "07_scripts" / "paper_upgrade_runtime.py").is_file():
            return candidate
    raise FileNotFoundError("07_scripts/paper_upgrade_runtime.py not found from " + str(p))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pre, post = _split_argv(argv)
    ap = argparse.ArgumentParser(prog="paper_upgrade_runtime")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("which-wb")

    p_init = sub.add_parser("init")
    p_init.add_argument("--family", required=True)
    p_init.add_argument("--tier", required=True)
    p_init.add_argument("--out", required=True)
    p_init.add_argument("--resume", action="store_true")

    p_stage = sub.add_parser("stage")
    p_stage.add_argument("--family", required=True)
    p_stage.add_argument("--tier", required=True)
    p_stage.add_argument("--out", required=True)
    p_stage.add_argument("--id", required=True, dest="stage_id")
    p_stage.add_argument("--cwd", default=None)
    p_stage.add_argument("--resume", action="store_true")
    p_stage.add_argument("--heartbeat-sec", type=float, default=None)

    p_fin = sub.add_parser("finish")
    p_fin.add_argument("--family", required=True)
    p_fin.add_argument("--tier", required=True)
    p_fin.add_argument("--out", required=True)
    p_fin.add_argument("--status", default="DONE")

    ns = ap.parse_args(pre)
    if ns.cmd == "which-wb":
        print(find_workbench())
        return 0
    if ns.cmd == "init":
        init_run(family=ns.family, tier=ns.tier, out=ns.out, resume=True if ns.resume else None)
        return 0
    if ns.cmd == "finish":
        finish_run(family=ns.family, tier=ns.tier, out=ns.out, status=ns.status)
        return 0
    if ns.cmd == "stage":
        return run_stage(
            family=ns.family,
            tier=ns.tier,
            out=ns.out,
            stage_id=ns.stage_id,
            argv=post,
            cwd=ns.cwd,
            resume=True if ns.resume else None,
            heartbeat_sec=ns.heartbeat_sec,
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
