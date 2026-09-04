from __future__ import annotations
from pathlib import Path
import re

ALLOWED_TARGET_FILES={"unblind.py","unblind_target.json","README.md","research_basis.md"}
FORBIDDEN_PATTERNS=[r"1093845\.63",r"1\.09384563e6",r"1\.09384563\s*[x×*]\s*10\^?6"]


def audit_blindness(root):
    root=Path(root)
    hits=[]
    for path in root.rglob("*"):
        if not path.is_file() or path.name in ALLOWED_TARGET_FILES or ".venv" in path.parts:
            continue
        if path.suffix.lower() not in {".py",".json",".toml",".txt",".md",".cmd",".cpp",".h"}:
            continue
        txt=path.read_text(encoding="utf-8",errors="ignore")
        for pat in FORBIDDEN_PATTERNS:
            if re.search(pat,txt,re.I):
                hits.append((str(path.relative_to(root)),pat))
    return hits
