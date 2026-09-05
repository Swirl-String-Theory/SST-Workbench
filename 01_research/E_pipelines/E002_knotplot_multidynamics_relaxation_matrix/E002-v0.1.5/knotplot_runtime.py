from __future__ import annotations
import os, re, subprocess
from pathlib import Path

WINDOWS_PATH_RE = re.compile(r'(?i)([A-Z]:[\\/][^\r\n<>"]+)')

def kp_path(p: Path) -> str:
    return str(p.resolve()).replace("\\", "/")

def run_knotplot(exe: Path, cwd: Path, script_text: str, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Current KnotPlot manual documents -nographics and -stdin for batch research.
    argv = [str(exe), "-nographics", "-stdin"]
    with log_path.open("wb") as fout:
        cp = subprocess.run(
            argv,
            cwd=str(cwd),
            input=script_text.encode("utf-8"),
            stdout=fout,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return int(cp.returncode)

def runtime_info(exe: Path, cwd: Path, out_dir: Path) -> tuple[int, str]:
    log = out_dir / "00_runtime_info.log"
    rc = run_knotplot(exe, cwd, "version\npath\nstop\n", log)
    text = log.read_text(encoding="utf-8", errors="replace")
    return rc, text

def _existing_dirs_from_text(text: str) -> list[Path]:
    out = []
    seen = set()
    for m in WINDOWS_PATH_RE.finditer(text):
        raw = m.group(1).strip().rstrip(" .;,:")
        p = Path(raw)
        # If a file-like path is printed, search its parent too.
        qs = [p] if p.is_dir() else [p.parent]
        for q in qs:
            try:
                key = os.path.normcase(str(q.resolve()))
            except Exception:
                key = os.path.normcase(str(q))
            if q.exists() and q.is_dir() and key not in seen:
                seen.add(key)
                out.append(q)
    return out

def candidate_distribution_roots(exe: Path, shortcut_cwd: Path, info_text: str = "") -> list[Path]:
    seeds = [exe.parent, shortcut_cwd]
    seeds += _existing_dirs_from_text(info_text)
    # Add a few parents because installers often place distribution beside bin/.
    for p in list(seeds):
        seeds += list(p.parents)[:3]

    out, seen = [], set()
    for p in seeds:
        if not p.exists() or not p.is_dir():
            continue
        try:
            key = os.path.normcase(str(p.resolve()))
        except Exception:
            key = os.path.normcase(str(p))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def find_basic_dirs(exe: Path, shortcut_cwd: Path, info_text: str = "") -> list[Path]:
    roots = candidate_distribution_roots(exe, shortcut_cwd, info_text)
    found, seen = [], set()

    def add(p: Path):
        if p.is_dir():
            try:
                key = os.path.normcase(str(p.resolve()))
            except Exception:
                key = os.path.normcase(str(p))
            if key not in seen:
                seen.add(key)
                found.append(p)

    # Fast common layouts.
    for root in roots:
        add(root / "basic")
        add(root / "kpdist" / "basic")
        add(root / "distribution" / "basic")
        add(root / "dist" / "basic")
        if root.name.lower() == "basic":
            add(root)

    # Bounded recursive search. Avoid crawling entire drives/users.
    for root in roots:
        # Only recurse near the executable/runtime paths.
        try:
            for base, dirs, files in os.walk(root):
                rel = Path(base).relative_to(root)
                # Skip enormous/developer trees and cap depth.
                dirs[:] = [d for d in dirs if d.lower() not in {
                    ".git", ".venv", "node_modules", "archive", "out", "logs",
                    "analysis", "catalog_logs", "runtime_scripts"
                }]
                if len(rel.parts) >= 4:
                    dirs[:] = []
                    continue
                if Path(base).name.lower() == "basic":
                    add(Path(base))
                    dirs[:] = []
        except (OSError, ValueError):
            pass
    return found

def find_catalogue_file(catalog_id: str, basic_dirs: list[Path]) -> Path | None:
    names = [catalog_id, catalog_id + ".k", catalog_id + ".txt"]
    low_names = {n.lower() for n in names}
    for basic in basic_dirs:
        # Exact direct filenames first.
        for n in names:
            p = basic / n
            if p.is_file() and p.stat().st_size > 0:
                return p.resolve()
        # Case-insensitive direct match.
        try:
            for p in basic.iterdir():
                if p.is_file() and p.name.lower() in low_names and p.stat().st_size > 0:
                    return p.resolve()
        except OSError:
            pass
    return None

def render_catalogue_loads(text: str, basic_dirs: list[Path]) -> tuple[str, dict[str, str]]:
    resolved: dict[str, str] = {}
    missing: set[str] = set()

    # Only plain `load ID` lines are rewritten. load combine/sum remain untouched.
    pat = re.compile(r'(?mi)^(?P<indent>\s*)load\s+(?P<id>[^\s%]+)\s*$')

    def repl(m):
        cid = m.group("id")
        # Already a path/file: leave it alone.
        if "/" in cid or "\\" in cid or ":" in cid:
            return m.group(0)
        f = find_catalogue_file(cid, basic_dirs)
        if f is None:
            missing.add(cid)
            return m.group(0)
        resolved[cid] = str(f)
        return f'{m.group("indent")}load {kp_path(f)}'

    out = pat.sub(repl, text)
    if missing:
        raise FileNotFoundError(
            "KnotPlot catalogue file(s) not found in resolved basic directories: "
            + ", ".join(sorted(missing))
        )
    return out, resolved
