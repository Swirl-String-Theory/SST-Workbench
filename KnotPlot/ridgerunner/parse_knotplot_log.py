#!/usr/bin/env python3
"""Parse KnotPlot build logs into per-checkpoint *.knotplot.json sidecars."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CHECKPOINT_RE = re.compile(
    r"^(?:KnotPlot>\s*)?CHECKPOINT\s+(\S+)\s*$",
    re.IGNORECASE,
)
SAFE_RE = re.compile(r"safe|Current position is safe|NOT safe|unsafe", re.I)
DOWKER_RE = re.compile(
    r"(?:Dowker|dowker).*?([+\-]?\d+(?:\s+[+\-]?\d+)+)",
    re.I,
)
KNOT_TYPE_RE = re.compile(
    r"(?:knot type|knot_type|identified as|is the knot)\s*[:=]?\s*([0-9]+[_]?[0-9a-zA-Z.]*)",
    re.I,
)
# Rolfsen-style 3.1 / 3_1 / 10.123
KNOT_ID_RE = re.compile(r"\b(\d{1,2}[._]\d{1,3}[a-zA-Z]?)\b")
LNKNUM_MATRIX_RE = re.compile(
    r"linking.*?matrix|lnknum|Linking numbers",
    re.I,
)


def _parse_safe(block: str) -> bool | None:
    lower = block.lower()
    if "not safe" in lower or "unsafe" in lower:
        return False
    if "is safe" in lower or re.search(r"\bsafe\b", lower):
        # Heuristic: KnotPlot prints "Current position is safe."
        if "current position is safe" in lower:
            return True
        if "safe" in lower and "not" not in lower.split("safe")[0][-10:]:
            return True
    return None


def _parse_dowker(block: str) -> str | None:
    m = DOWKER_RE.search(block)
    if m:
        return " ".join(m.group(1).split())
    # Fallback: line with many signed integers after "dowker"
    for line in block.splitlines():
        if "dowker" in line.lower():
            nums = re.findall(r"[+\-]?\d+", line)
            if len(nums) >= 4:
                return " ".join(nums)
    return None


def _parse_knot_type(block: str, folder_hint: str | None) -> str | None:
    m = KNOT_TYPE_RE.search(block)
    if m:
        return m.group(1).replace(".", "_")
    # Prefer folder name knot_X.Y → X_Y as expected type hint (not from log)
    if folder_hint and folder_hint.startswith("knot_"):
        return folder_hint[len("knot_") :].replace(".", "_")
    m2 = KNOT_ID_RE.search(block)
    if m2:
        return m2.group(1).replace(".", "_")
    return None


def _parse_linking_matrix(block: str) -> list[list[int]] | None:
    # Collect integer rows that look like a square matrix
    rows: list[list[int]] = []
    for line in block.splitlines():
        if not re.search(r"\d", line):
            continue
        if re.search(r"[a-df-zA-DF-Z]", line) and "link" not in line.lower():
            # skip non-matrix prose unless only ints
            ints = re.findall(r"[+\-]?\d+", line)
            if len(ints) < 2:
                continue
        ints = [int(x) for x in re.findall(r"[+\-]?\d+", line)]
        if len(ints) >= 2:
            rows.append(ints)
    if not rows:
        return None
    # Keep trailing square block
    n = len(rows[-1])
    square = [r for r in rows if len(r) == n]
    if len(square) >= n:
        square = square[-n:]
        if all(len(r) == n for r in square):
            return square
    return None


def parse_log_blocks(log_text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in log_text.splitlines():
        m = CHECKPOINT_RE.match(line.strip())
        if m:
            current = m.group(1)
            blocks.setdefault(current, [])
            continue
        if current is not None:
            blocks[current].append(line)
    return {k: "\n".join(v) for k, v in blocks.items()}


def sidecar_from_block(
    label: str,
    block: str,
    *,
    folder_hint: str | None,
    vertices_from_txt: list[int] | None,
) -> dict[str, Any]:
    safe = _parse_safe(block)
    dowker = _parse_dowker(block)
    knot_type = _parse_knot_type(block, folder_hint)
    linking = _parse_linking_matrix(block)
    ncomp = len(vertices_from_txt) if vertices_from_txt else None
    if ncomp == 1:
        linking = None
    elif ncomp is not None and ncomp > 1:
        knot_type = None  # primary gate is linking for multilinks
    return {
        "checkpoint": label,
        "safe": safe,
        "component_count": ncomp,
        "vertices_per_component": vertices_from_txt,
        "knot_type": knot_type,
        "dowker_code": dowker,
        "linking_matrix": linking,
        "raw_block_chars": len(block),
    }


def find_txt_for_checkpoint(outdir: Path, label: str) -> Path | None:
    if label == "analytic_D1":
        matches = list(outdir.glob("*_analytic_D1.txt"))
        return matches[0] if matches else None
    if label.startswith("trial_"):
        matches = list(outdir.glob(f"*_{label}.txt"))
        matches = [p for p in matches if "_rr_" not in p.name]
        return matches[0] if matches else None
    return None


def count_vertices(txt: Path) -> list[int]:
    from run_knotplot_txt import parse_xyz_txt  # type: ignore

    comps = parse_xyz_txt(txt)
    return [len(c) for c in comps]


def write_sidecars(outdir: Path, log_path: Path) -> list[Path]:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    blocks = parse_log_blocks(text)
    folder_hint = outdir.name
    written: list[Path] = []
    for label, block in blocks.items():
        txt = find_txt_for_checkpoint(outdir, label)
        verts = None
        if txt is not None:
            try:
                verts = count_vertices(txt)
            except Exception:
                verts = None
        data = sidecar_from_block(
            label, block, folder_hint=folder_hint, vertices_from_txt=verts
        )
        if txt is not None:
            out = txt.with_suffix(".knotplot.json")
        else:
            out = outdir / f"{label}.knotplot.json"
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        written.append(out)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("outdir", type=Path, help="folder with trial_*.txt exports")
    ap.add_argument(
        "--log",
        type=Path,
        default=None,
        help="KnotPlot log (default: outdir/build_knotplot.log)",
    )
    args = ap.parse_args()
    outdir = args.outdir.resolve()
    log_path = (args.log or (outdir / "build_knotplot.log")).resolve()
    if not log_path.is_file():
        raise SystemExit(f"log not found: {log_path}")
    # Ensure import path for run_knotplot_txt
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    paths = write_sidecars(outdir, log_path)
    print(f"Wrote {len(paths)} sidecars from {log_path}")
    for p in paths:
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
