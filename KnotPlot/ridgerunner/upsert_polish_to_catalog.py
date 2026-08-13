#!/usr/bin/env python3
"""
Resample a Ridgerunner polish → VortexLab uniform N=300 and upsert knotplot_knots_data.js.

Same curve as the polish (arc-length reparameterization only; no RR re-optimize).
Does not change the RR pipeline outputs beyond writing/updating the uniform sibling.

Examples:
  upsert_polish_to_catalog.py --polish path/to/…_polish.txt --outdir knots/knot_3.1
  upsert_polish_to_catalog.py --polish … --outdir … --final path/to/build_*_final_*.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BUNDLE = Path(__file__).resolve().parent
KNOTPLOT_ROOT = BUNDLE.parent
DEFAULT_JS = KNOTPLOT_ROOT / "knotplot_knots_data.js"
RESAMPLE = KNOTPLOT_ROOT / "resample_closed_knot_txt.py"
BUILD_JS = KNOTPLOT_ROOT / "build_knotplot_knots_data.py"


def _metrics_for_polish(polish: Path) -> Path:
    return Path(str(polish).removesuffix(".txt") + ".metrics.json")


def uniform_path_for_polish(polish: Path, *, points: int | None = 300) -> Path:
    """Default resample naming next to polish.

    When points is None, use VortexLab default (300 or preserve Ni).
    """
    polish = Path(polish)
    if points is None:
        if str(KNOTPLOT_ROOT) not in sys.path:
            sys.path.insert(0, str(KNOTPLOT_ROOT))
        import resample_closed_knot_txt as resample_mod

        return resample_mod.vortexlab_uniform_path(polish)
    return polish.with_name(f"{polish.stem}_uniform_N{points}.txt")


def resample_polish_uniform(
    polish: Path,
    *,
    points: int | None = None,
    method: str = "linear",
    preserve_counts: bool = False,
) -> Path:
    """Run resample_closed_knot_txt; return uniform TXT path."""
    polish = polish.resolve()
    if not polish.is_file():
        raise FileNotFoundError(f"polish not found: {polish}")
    if not RESAMPLE.is_file():
        raise FileNotFoundError(f"missing {RESAMPLE}")

    # Import sibling module from KnotPlot root
    if str(KNOTPLOT_ROOT) not in sys.path:
        sys.path.insert(0, str(KNOTPLOT_ROOT))
    import resample_closed_knot_txt as resample_mod

    argv = [str(polish), "--method", method, "--no-strict"]
    if preserve_counts:
        out = uniform_path_for_polish(polish, points=None)
        # force preserve even for 1-comp
        argv.extend(["--preserve-counts", "--output", str(out)])
    elif points is not None:
        out = uniform_path_for_polish(polish, points=points)
        argv.extend(["--points", str(points), "--output", str(out)])
    else:
        out = resample_mod.vortexlab_uniform_path(polish)
        argv.extend(["--output", str(out)])
    rc = resample_mod.main(argv)
    if rc != 0:
        raise RuntimeError(f"resample failed (exit {rc}) for {polish}")
    if not out.is_file():
        raise FileNotFoundError(f"uniform output missing: {out}")
    return out


def classify_outdir(outdir: Path) -> dict[str, Any]:
    from classify_catalog_status import classify

    outdir = outdir.resolve()
    result = classify(outdir)
    path = outdir / "catalog_status.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def find_latest_final_for_polish(outdir: Path, polish: Path) -> Path | None:
    """Newest build_*_final_*.txt whose alias polish_path matches this polish."""
    outdir = outdir.resolve()
    polish = polish.resolve()
    best: Path | None = None
    best_mtime = -1.0
    for alias_path in outdir.glob("*_final_*.alias.json"):
        try:
            data = json.loads(alias_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        src = data.get("polish_path")
        if not src:
            continue
        try:
            if Path(src).resolve() != polish:
                continue
        except OSError:
            continue
        final = data.get("final_txt")
        if not final:
            continue
        fin = Path(final)
        if not fin.is_file():
            continue
        mtime = alias_path.stat().st_mtime
        if mtime >= best_mtime:
            best_mtime = mtime
            best = fin
    return best


def prefer_polish_in_catalog_status(
    outdir: Path,
    polish: Path,
    *,
    final_txt: Path | None = None,
) -> dict[str, Any]:
    """Ensure catalog_status.json points primary_polish at this polish (audit)."""
    outdir = outdir.resolve()
    polish = polish.resolve()
    status_path = outdir / "catalog_status.json"
    if status_path.is_file():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            status = {}
    else:
        status = {}
    met = _metrics_for_polish(polish)
    status["primary_polish"] = str(met if met.is_file() else polish)
    resolved_final = final_txt
    if resolved_final is None:
        resolved_final = find_latest_final_for_polish(outdir, polish)
    if resolved_final is not None and resolved_final.is_file():
        status["final_snapshot"] = str(resolved_final.resolve())
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return status


def polish_from_outdir(outdir: Path) -> tuple[Path, Path | None]:
    """Pick best polish in a KnotPlot knots/<id> folder; optional latest final."""
    from write_final_snapshot import pick_best_polish_in_folder

    polish, _rop, _info = pick_best_polish_in_folder(outdir)
    final = find_latest_final_for_polish(outdir, polish)
    return polish, final


def upsert_js_from_outdir(
    outdir: Path,
    *,
    js_output: Path | None = None,
    force: bool = True,
) -> int:
    """Call build_knotplot_knots_data.py --from-rr-outdir."""
    if str(KNOTPLOT_ROOT) not in sys.path:
        sys.path.insert(0, str(KNOTPLOT_ROOT))
    import build_knotplot_knots_data as build_mod

    js = (js_output or DEFAULT_JS).resolve()
    argv = [
        "--from-rr-outdir",
        str(outdir.resolve()),
        "--output",
        str(js),
    ]
    if force:
        argv.append("--force")
    # build_mod.main uses sys.argv — call carefully
    old = sys.argv
    try:
        sys.argv = [str(BUILD_JS), *argv]
        return int(build_mod.main())
    finally:
        sys.argv = old


def upsert_polish_to_catalog(
    polish: Path,
    outdir: Path,
    *,
    final_txt: Path | None = None,
    js_output: Path | None = None,
    points: int | None = None,
    skip_classify: bool = False,
) -> dict[str, Any]:
    """
    Full path: resample polish → classify → prefer polish → upsert JS.
    Returns dict with paths and status.
    """
    polish = polish.resolve()
    outdir = outdir.resolve()
    uniform = resample_polish_uniform(polish, points=points, method="linear")
    if not skip_classify:
        classify_outdir(outdir)
    prefer_polish_in_catalog_status(outdir, polish, final_txt=final_txt)
    # polishAudit in JS comes from uniform sibling strip; also pass via status final
    rc = upsert_js_from_outdir(outdir, js_output=js_output, force=True)
    if rc != 0:
        raise RuntimeError(f"catalog upsert failed (exit {rc})")
    return {
        "polish": str(polish),
        "uniform": str(uniform),
        "outdir": str(outdir),
        "final_txt": str(final_txt) if final_txt else None,
        "js": str((js_output or DEFAULT_JS).resolve()),
    }


def try_upsert_polish_to_catalog(
    polish: Path,
    outdir: Path,
    *,
    final_txt: Path | None = None,
    js_output: Path | None = None,
) -> dict[str, Any] | None:
    """Best-effort wrapper; prints WARNING and returns None on failure."""
    try:
        result = upsert_polish_to_catalog(
            polish,
            outdir,
            final_txt=final_txt,
            js_output=js_output,
        )
        print(f"Catalog upsert: {result['js']}  (uniform {result['uniform']})", flush=True)
        return result
    except (OSError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"WARNING: catalog upsert failed: {exc}", flush=True)
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Resample polish → uniform N300 and upsert knotplot_knots_data.js "
            "(same shape as polish; VortexLab mesh). KnotPlot knots/ only."
        )
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--polish", type=Path, help="Ridgerunner polish TXT")
    src.add_argument(
        "--from-outdir",
        type=Path,
        help="knots/<id> folder: pick best polish (same as final snapshot)",
    )
    ap.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="catalog upsert root (default: polish parent or --from-outdir)",
    )
    ap.add_argument(
        "--final",
        type=Path,
        default=None,
        help="optional build_*_final_*.txt path (recorded in catalog_status)",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"JS catalog path (default: {DEFAULT_JS})",
    )
    ap.add_argument(
        "--points",
        type=int,
        default=None,
        help="force uniform bead count per component (default: VortexLab policy)",
    )
    args = ap.parse_args(argv)

    try:
        final_txt = args.final
        if args.from_outdir is not None:
            outdir = (args.outdir or args.from_outdir).resolve()
            polish, discovered_final = polish_from_outdir(outdir)
            if final_txt is None:
                final_txt = discovered_final
        else:
            assert args.polish is not None
            polish = args.polish
            outdir = (args.outdir or polish.parent).resolve()
        result = upsert_polish_to_catalog(
            polish,
            outdir,
            final_txt=final_txt,
            js_output=args.output,
            points=args.points,
        )
    except (OSError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
