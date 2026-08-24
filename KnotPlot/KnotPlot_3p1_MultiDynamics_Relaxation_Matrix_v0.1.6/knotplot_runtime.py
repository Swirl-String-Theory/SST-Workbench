from __future__ import annotations
import os, re, subprocess
from dataclasses import dataclass
from pathlib import Path

WINDOWS_PATH_RE = re.compile(r'(?i)([A-Z]:[\\/][^\r\n<>"]+)')

def kp_path(p: Path) -> str:
    return str(p.resolve()).replace("\\", "/")

def run_knotplot(exe: Path, cwd: Path, script_text: str, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("wb") as fout:
        cp = subprocess.run(
            [str(exe), "-nographics", "-stdin"],
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
    out, seen = [], set()
    for m in WINDOWS_PATH_RE.finditer(text):
        raw = m.group(1).strip().rstrip(" .;,:")
        p = Path(raw)
        for q in ([p] if p.is_dir() else [p.parent]):
            if not q.is_dir():
                continue
            key = os.path.normcase(str(q.resolve()))
            if key not in seen:
                seen.add(key); out.append(q)
    return out

def candidate_distribution_roots(exe: Path, shortcut_cwd: Path, info_text: str = "") -> list[Path]:
    seeds = [exe.parent, shortcut_cwd, *_existing_dirs_from_text(info_text)]
    for p in list(seeds):
        seeds += list(p.parents)[:3]
    out, seen = [], set()
    for p in seeds:
        if not p.is_dir():
            continue
        key = os.path.normcase(str(p.resolve()))
        if key not in seen:
            seen.add(key); out.append(p)
    return out

def find_basic_dirs(exe: Path, shortcut_cwd: Path, info_text: str = "") -> list[Path]:
    roots = candidate_distribution_roots(exe, shortcut_cwd, info_text)
    found, seen = [], set()
    def add(p: Path):
        if p.is_dir():
            key = os.path.normcase(str(p.resolve()))
            if key not in seen:
                seen.add(key); found.append(p.resolve())
    for root in roots:
        for p in (root/"basic", root/"kpdist"/"basic", root/"distribution"/"basic", root/"dist"/"basic"):
            add(p)
        if root.name.lower() == "basic":
            add(root)
    for root in roots:
        try:
            for base, dirs, _ in os.walk(root):
                rel = Path(base).relative_to(root)
                dirs[:] = [d for d in dirs if d.lower() not in {
                    ".git",".venv","node_modules","archive","out","logs","analysis",
                    "catalog_logs","runtime_scripts","catalog_runtime"
                }]
                if len(rel.parts) >= 4:
                    dirs[:] = []
                    continue
                if Path(base).name.lower() == "basic":
                    add(Path(base)); dirs[:] = []
        except (OSError, ValueError):
            pass
    return found

def find_catalogue_file(catalog_id: str, basic_dirs: list[Path]) -> Path | None:
    names = [catalog_id, catalog_id+".k", catalog_id+".txt"]
    lows = {x.lower() for x in names}
    for basic in basic_dirs:
        for n in names:
            p = basic/n
            if p.is_file() and p.stat().st_size:
                return p.resolve()
        try:
            for p in basic.iterdir():
                if p.is_file() and p.name.lower() in lows and p.stat().st_size:
                    return p.resolve()
        except OSError:
            pass
    return None

@dataclass(frozen=True)
class LoadStrategy:
    name: str
    process_cwd: Path
    basic_dir: Path
    prefix: str
    load_template: str

    def load_line(self, catalog_id: str) -> str:
        return self.load_template.format(id=catalog_id)

def candidate_load_strategies(shortcut_cwd: Path, basic: Path) -> list[LoadStrategy]:
    b = kp_path(basic)
    return [
        LoadStrategy("default_read_path", shortcut_cwd, basic, "", "load {id}"),
        LoadStrategy("path_then_catalog_id", shortcut_cwd, basic, f"path {b}\n", "load {id}"),
        LoadStrategy("basic_as_cwd", basic, basic, "", "load {id}"),
        LoadStrategy("basic_as_cwd_dot", basic, basic, "", "load ./{id}"),
    ]

def render_catalogue_loads(text: str, strategy: LoadStrategy) -> tuple[str, dict[str, str]]:
    resolved = {}
    pat = re.compile(r'(?mi)^(?P<indent>\s*)load\s+(?P<kind>combine\s+|sum\s+)?(?P<id>[^\s%]+)\s*$')
    def repl(m):
        cid = m.group("id")
        kind = (m.group("kind") or "").strip()
        if "/" in cid or "\\" in cid or ":" in cid:
            return m.group(0)
        # For combine/sum, preserve the modifier while using catalogue id under the selected read strategy.
        if kind:
            line = strategy.load_line(cid)
            if not line.lower().startswith("load "):
                return m.group(0)
            arg = line[5:]
            line = f"load {kind} {arg}"
        else:
            line = strategy.load_line(cid)
        resolved[cid] = line
        return m.group("indent") + line
    body = pat.sub(repl, text)
    return strategy.prefix + body, resolved
