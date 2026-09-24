from __future__ import annotations
from pathlib import Path
import hashlib
import os
from .selection import canonical_topology_from_text

GEOMETRY_SUFFIXES={'.txt','.xyz','.vect','.locd','.locf','.fseries','.short','.qhp','.kp','.knot','.npz','.npy'}
SKIP={'.git','.venv','venv','__pycache__','.pytest_cache','node_modules','build','dist'}


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _safe_walk(base: Path, diagnostics: list[dict] | None = None):
    """os.walk wrapper that never aborts the atlas because one unrelated directory is inaccessible."""
    def onerror(exc: OSError):
        if diagnostics is not None:
            diagnostics.append({'kind':'walk_error','path':getattr(exc,'filename',None),'error':f'{type(exc).__name__}: {exc}'})
    try:
        for cur, dirs, files in os.walk(base, topdown=True, onerror=onerror, followlinks=False):
            dirs[:] = [d for d in dirs if d.lower() not in SKIP and not d.startswith('.')]
            yield Path(cur), dirs, files
    except OSError as exc:
        onerror(exc)
        return


def candidate_knotplot_roots(workbench: Path, diagnostics: list[dict] | None = None) -> list[Path]:
    """Locate KnotPlot source trees without pathlib.rglob/stat failures on unrelated junctions."""
    candidates=[]
    preferred=[workbench/'03_data', workbench/'02_libraries']
    bases=[b for b in preferred if b.is_dir()]
    # Only fall back to a repository-wide search when canonical data/library roots yield nothing.
    for base in bases:
        for p, _dirs, _files in _safe_walk(base, diagnostics):
            s=str(p).replace('\\','/').lower()
            name=p.name.lower()
            if 'knotplot' in s and any(k in name for k in ('knot','qhp','fourier','final','relax')):
                candidates.append(p)
    if not candidates:
        for p, _dirs, _files in _safe_walk(workbench, diagnostics):
            s=str(p).replace('\\','/').lower()
            name=p.name.lower()
            if 'knotplot' in s and any(k in name for k in ('knot','qhp','fourier','final','relax')):
                candidates.append(p)
    # Keep shallow/non-nested roots so the same file is not re-scanned many times.
    uniq=[]
    for p in sorted(set(candidates), key=lambda x:(len(x.parts),str(x).lower())):
        try:
            nested=any(p==q or p.is_relative_to(q) for q in uniq)
        except (OSError, ValueError):
            nested=False
        if not nested:
            uniq.append(p)
    return uniq


def scan_knotplot(workbench: Path, selected: set[str], diagnostics: list[dict] | None = None) -> list[dict]:
    records=[]; seen=set()
    for root in candidate_knotplot_roots(workbench, diagnostics):
        for cur, _dirs, files in _safe_walk(root, diagnostics):
            for fn in files:
                p=cur/fn
                if p.suffix.lower() not in GEOMETRY_SUFFIXES:
                    continue
                topo=canonical_topology_from_text(str(p))
                if topo not in selected:
                    continue
                # absolute() is lexical; unlike resolve()/stat(), it does not dereference inaccessible junctions.
                rp=str(p.absolute())
                key=os.path.normcase(rp)
                if key in seen:
                    continue
                try:
                    st=p.stat()
                    digest=sha256_file(p)
                except OSError as exc:
                    if diagnostics is not None:
                        diagnostics.append({'kind':'file_error','path':rp,'error':f'{type(exc).__name__}: {exc}'})
                    continue
                seen.add(key)
                records.append({
                    'topology_id':topo,
                    'path':rp,
                    'source_root':str(root.absolute()),
                    'suffix':p.suffix.lower(),
                    'size':st.st_size,
                    'sha256':digest,
                    'source_family':'knotplot',
                    'status':'DISCOVERED_NOT_YET_SEED_QUALIFIED'
                })
    return sorted(records,key=lambda r:(r['topology_id'],r['path'].lower()))
