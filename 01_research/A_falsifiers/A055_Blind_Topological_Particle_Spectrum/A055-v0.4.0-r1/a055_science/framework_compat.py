from __future__ import annotations
from pathlib import PurePosixPath

RUNTIME_EXCLUDE_PARTS = frozenset({
    '.venv','venv','env','__pycache__','.pytest_cache','build','dist',
    '.git','.mypy_cache','.ruff_cache','node_modules'
})


def install_runtime_safe_blind_scan():
    """Exclude runtime/build/vendor trees from the framework source blindness scan.

    Framework v1.0.4 scans the entire instance root. A local virtual environment is
    not part of the falsifier source or blind artifact, yet third-party packages can
    contain forbidden tokens such as particle names or knot labels. Filtering only
    these runtime-owned path components preserves strict scanning of all actual
    instance source and output files.
    """
    import sst_falsifier.blind as blind
    current=blind.scan_tree
    if getattr(current,'_a055_runtime_safe',False):
        return

    def runtime_safe_scan_tree(root, forbidden, suffixes=blind.DEFAULT_SUFFIXES):
        hits=current(root,forbidden,suffixes)
        out=[]
        for hit in hits:
            parts={p.casefold() for p in PurePosixPath(hit['path']).parts}
            if parts & RUNTIME_EXCLUDE_PARTS:
                continue
            out.append(hit)
        return out

    runtime_safe_scan_tree._a055_runtime_safe=True
    runtime_safe_scan_tree._a055_original=current
    blind.scan_tree=runtime_safe_scan_tree
