"""Blind-safe, structured progress events and long-running phase checkpoints.

Events are machine-readable and console-visible; only measured progress (completed/total)
is printed. An external Windows supervisor can heartbeat through long GIL-holding C++ calls.
Never emit blind/reveal secrets, datasets, raw numerical observations, or private paths.
"""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json, os, sys, tempfile, threading, time
from pathlib import Path

_ACTIVE: ContextVar["ProgressSession | None"] = ContextVar("sst_progress", default=None)
_ALLOWED = {"backend", "level", "resolution", "dt", "final_time", "phase_kind"}


def _heartbeat_seconds():
    try:
        value = float(os.environ.get("SST_PROGRESS_HEARTBEAT_SECONDS", "15"))
        return value if 0.02 <= value <= 3600 else 15.0
    except (TypeError, ValueError):
        return 15.0


class ProgressSession:
    def __init__(self, mode: str, *, stream=None, status_file=None, heartbeat_seconds=None):
        self.mode = mode.upper()
        self.stream = stream if stream is not None else sys.stdout
        self.status_file = Path(status_file) if status_file else (Path(os.environ["SST_PROGRESS_STATUS_FILE"]) if os.environ.get("SST_PROGRESS_STATUS_FILE") else None)
        self.heartbeat_seconds = heartbeat_seconds if heartbeat_seconds is not None else _heartbeat_seconds()
        self.start = time.monotonic()
        self.stage_start = self.start
        self.last_update = self.start
        self.current = "INITIALIZING"
        self.completed = None
        self.total = None
        self._log = None
        self._log_frozen = False
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread = None
        self._token = None

    def __enter__(self):
        self._token = _ACTIVE.set(self)
        self.event("RUN", "START")
        # A separate supervisor owns reliable heartbeat while C++ holds the GIL.
        if os.environ.get("SST_PROGRESS_SUPERVISED") != "1":
            self._thread = threading.Thread(target=self._heartbeat_loop, name="sst-progress", daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.event("RUN", "ERROR" if exc_type else "FINISHED")
        finally:
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=1.0)
            self.freeze_log()
            if self._token is not None:
                _ACTIVE.reset(self._token)
        return False

    def _heartbeat_loop(self):
        while not self._stop.wait(self.heartbeat_seconds):
            with self._lock:
                age = time.monotonic() - self.last_update
                elapsed = time.monotonic() - self.start
                suffix = f" {self.completed}/{self.total}" if self.completed is not None and self.total else ""
                print(f"[SST][HEARTBEAT] RUNNING phase={self.current}{suffix} elapsed={elapsed:.1f}s no_update={age:.1f}s", file=self.stream, flush=True)

    def bind_log(self, path):
        """Bind the run-local journal before creating immutable evidence manifests."""
        with self._lock:
            if self._log is not None or self._log_frozen:
                raise RuntimeError("Progress journal already bound/frozen")
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            self._log = target.open("x", encoding="utf-8", newline="\n")

    def freeze_log(self):
        """Close journal before science/output manifest hashing; console stays alive."""
        with self._lock:
            if self._log is not None:
                self._log.close()
                self._log = None
            self._log_frozen = True

    def _write_status(self, payload):
        if self.status_file is None:
            return
        try:
            # Supervisor's status file is out-of-band and never included in frozen artifacts.
            tmp = self.status_file.with_name(self.status_file.name + '.tmp')
            tmp.write_text(json.dumps(payload,sort_keys=True), encoding='utf-8')
            os.replace(tmp,self.status_file)
        except OSError:
            pass  # Console progress must not alter scientific execution status.

    def event(self, phase: str, state: str="UPDATE", *, completed=None, total=None, **details):
        """Emit a phase transition; never invent a completion percentage."""
        if (completed is None) != (total is None):
            raise ValueError("completed and total must be provided together")
        if completed is not None:
            if not (isinstance(completed,int) and isinstance(total,int) and 0 <= completed <= total and total > 0):
                raise ValueError("Invalid measured progress counter")
        phase = str(phase).upper().replace(' ', '_')[:64]
        state = str(state).upper()[:24]
        now = time.monotonic()
        # Whitelist *values* as well as keys: never copy arbitrary exception text,
        # private source paths, opaque target labels or reveal metadata to the blind log.
        clean = {}
        for k,v in details.items():
            if k not in _ALLOWED or v is None:continue
            if k=='backend' and v in ('py','cpp','gpu','intel','cuda'):
                clean[k]=v
            elif k=='phase_kind' and v in ('spatial','temporal'):
                clean[k]=v
            elif k in ('level','resolution') and type(v) is int and 0<=v<=10**12:
                clean[k]=v
            elif k in ('dt','final_time') and type(v) in (float,int):
                import math
                if math.isfinite(v):clean[k]=v
        with self._lock:
            if phase != self.current:
                self.stage_start = now
            self.current, self.completed, self.total, self.last_update = phase, completed, total, now
            record = {"schema":"SST-RUN-PROGRESS-1", "utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "mode":self.mode,"phase":phase,"state":state,"elapsed_s":round(now-self.start,3),
                      "phase_elapsed_s":round(now-self.stage_start,3), **clean}
            if completed is not None:
                record.update(completed=completed,total=total)
            counter = f" {completed}/{total}" if completed is not None else ""
            backend = f" backend={clean['backend']}" if 'backend' in clean else ''
            label = f" level={clean['level']}" if 'level' in clean else ''
            print(f"[SST][PROGRESS] {phase} {state}{counter}{backend}{label} elapsed={record['elapsed_s']:.1f}s",file=self.stream,flush=True)
            if self._log is not None:
                self._log.write(json.dumps(record,sort_keys=True,allow_nan=False)+'\n')
                self._log.flush()
            self._write_status(record)
            return record


def current():
    return _ACTIVE.get()


def event(phase: str, state: str="UPDATE", **kwargs):
    session = current()
    if session is not None:
        return session.event(phase,state,**kwargs)
    return None


@contextmanager
def phase(name: str, *, completed=None, total=None, **details):
    """Wrap long-running work with measured start/done/error transitions."""
    event(name,'START',completed=completed,total=total,**details)
    try:
        yield
    except BaseException:
        event(name,'ERROR',completed=completed,total=total,**details)
        raise
    else:
        # Preserve an exact current/total counter only if the caller supplied it.
        event(name,'DONE',completed=(completed+1 if completed is not None else None),total=total,**details)


def refinement(kind, *, level, total, resolution=None, dt=None, final_time=None):
    """Context manager for a single measured spatial/temporal refinement level.

    Example: with refinement('spatial',level=i+1,total=len(levels),resolution=N): solve(N)
    Each level emits START/DONE; heartbeat reports the active level even mid-kernel.
    """
    if kind not in ('spatial','temporal'):
        raise ValueError('refinement kind must be spatial or temporal')
    if not isinstance(level,int) or not isinstance(total,int) or not (1<=level<=total):
        raise ValueError('invalid refinement level')
    return phase(kind.upper()+'_REFINEMENT',completed=level-1,total=total,level=level,
                 resolution=resolution,dt=dt,final_time=final_time)
