#!/usr/bin/env python3
"""
Copy a Ridgerunner polish to a unique final snapshot (additive; never overwrites).

Examples:
  write_final_snapshot.py --polish path/to/..._polish.txt --stem build_knot_3.1 --tag min
  write_final_snapshot.py --from-outdir out/3_1 --stem 3_1 --tag N900 --suffix scout
  write_final_snapshot.py --from-outdir knots/knot_3.1 --stem build_knot_3.1 --tag finalize
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

BUNDLE = Path(__file__).resolve().parent
KNOTPLOT_ROOT = BUNDLE.parent
DEFAULT_KNOTS_ROOT = KNOTPLOT_ROOT / "knots"
DEFAULT_SHARED_FINALS = DEFAULT_KNOTS_ROOT / "final"

_TN_RE = re.compile(r"^t\d+$", re.IGNORECASE)
_RN_RE = re.compile(r"^r_?.+$", re.IGNORECASE)
_SHORT_POLISH_RE = re.compile(r"^n(\d+)p\.txt$", re.IGNORECASE)
_N_FROM_METRICS = re.compile(r"^n(\d+)p\.metrics\.json$", re.IGNORECASE)


def sanitize_token(text: str) -> str:
    """Keep filename-safe tokens."""
    t = text.strip().replace(" ", "_")
    t = re.sub(r"[^\w.\-]+", "_", t, flags=re.UNICODE)
    t = re.sub(r"_+", "_", t).strip("._")
    if not t:
        raise ValueError("empty token after sanitize")
    return t


def final_basename(
    stem: str,
    tag: str,
    *,
    suffix: str | None = None,
    when: datetime | None = None,
) -> str:
    """Return basename without extension: stem_final_tag[_suffix]_YYYYMMDD_HHMMSS."""
    parts = [sanitize_token(stem), "final", sanitize_token(tag)]
    if suffix:
        parts.append(sanitize_token(suffix))
    stamp = (when or datetime.now()).strftime("%Y%m%d_%H%M%S")
    parts.append(stamp)
    return "_".join(parts)


def unique_path(dest_dir: Path, basename: str, *, ext: str = ".txt") -> Path:
    """Avoid overwrite: basename.ext, basename_2.ext, …"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    candidate = dest_dir / f"{basename}{ext}"
    if not candidate.exists():
        return candidate
    n = 2
    while True:
        candidate = dest_dir / f"{basename}_{n}{ext}"
        if not candidate.exists():
            return candidate
        n += 1


def is_excluded_polish_name(name: str) -> bool:
    lower = name.lower()
    if "uniform" in lower:
        return True
    if "n600" in lower or "n1200" in lower:
        return True
    if "_final_" in lower:
        return True
    return False


def polish_txt_from_metrics(metrics: Path) -> Path | None:
    """Map *.metrics.json → sibling .txt (legacy polish or nNp)."""
    name = metrics.name
    if name.endswith(".metrics.json"):
        stem = name[: -len(".metrics.json")]
        txt = metrics.with_name(stem + ".txt")
        if txt.is_file():
            return txt
    # n300p.metrics.json → n300p.txt
    m = _N_FROM_METRICS.match(name)
    if m:
        txt = metrics.with_name(f"n{m.group(1)}p.txt")
        if txt.is_file():
            return txt
    return None


def load_rop(metrics: Path) -> float | None:
    if not metrics.is_file():
        return None
    try:
        data = json.loads(metrics.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    rop = data.get("ropelength")
    if rop is None:
        return None
    try:
        return float(rop)
    except (TypeError, ValueError):
        return None


def list_legacy_polishes(folder: Path) -> list[Path]:
    """*_polish.txt excluding uniform / ladder / finals."""
    out: list[Path] = []
    for p in sorted(folder.glob("*_polish.txt")):
        if is_excluded_polish_name(p.name):
            continue
        out.append(p)
    return out


def list_short_polishes(folder: Path) -> list[Path]:
    """n{N}p.txt short aliases."""
    out: list[Path] = []
    for p in sorted(folder.glob("n*p.txt")):
        if _SHORT_POLISH_RE.match(p.name):
            out.append(p)
    return out


def campaign_root_from_path(path: Path) -> Path:
    """If path is …/t12 or …/r_*, return parent; else path itself."""
    path = path.resolve()
    if path.is_file():
        path = path.parent
    name = path.name
    if _TN_RE.match(name) or (
        name.startswith("r") and (name.startswith("r_") or name[1:].isdigit())
    ):
        return path.parent
    return path


def sibling_run_dirs(campaign: Path) -> list[Path]:
    """tN / r* children of campaign, or [campaign] if none."""
    if not campaign.is_dir():
        return []
    kids = [
        p
        for p in sorted(campaign.iterdir())
        if p.is_dir()
        and (
            _TN_RE.match(p.name)
            or p.name.startswith("r_")
            or (p.name.startswith("r") and p.name[1:].isdigit())
        )
    ]
    return kids if kids else [campaign]


def discover_polish_candidates(folder: Path) -> list[Path]:
    """All polish TXT candidates in one folder."""
    cands = list_legacy_polishes(folder) + list_short_polishes(folder)
    # Prefer unique by resolve
    seen: set[Path] = set()
    out: list[Path] = []
    for p in cands:
        r = p.resolve()
        if r in seen:
            continue
        seen.add(r)
        out.append(p)
    return out


def pick_best_polish_in_folder(folder: Path) -> tuple[Path, float | None, dict[str, Any]]:
    """Pick polish in one folder: seed_selection match, else lowest Rop, else first."""
    info: dict[str, Any] = {"folder": str(folder)}
    cands = discover_polish_candidates(folder)
    if not cands:
        raise FileNotFoundError(f"no polish found in {folder}")

    sel_path = folder / "seed_selection.json"
    if sel_path.is_file():
        try:
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            selected = sel.get("selected")
            if selected:
                stem = Path(selected).stem
                for p in cands:
                    if stem in p.stem:
                        met = Path(str(p).removesuffix(".txt") + ".metrics.json")
                        rop = load_rop(met)
                        info["pick"] = "seed_selection"
                        return p, rop, info
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    scored: list[tuple[float, int, Path]] = []
    for p in cands:
        met = Path(str(p).removesuffix(".txt") + ".metrics.json")
        rop = load_rop(met)
        # Prefer higher N for short names when Rop ties / missing
        n_bonus = 0
        m = _SHORT_POLISH_RE.match(p.name)
        if m:
            n_bonus = int(m.group(1))
        key_rop = rop if rop is not None else float("inf")
        scored.append((key_rop, -n_bonus, p))
    scored.sort()
    best = scored[0][2]
    met = Path(str(best).removesuffix(".txt") + ".metrics.json")
    info["pick"] = "lowest_rop" if scored[0][0] != float("inf") else "fallback"
    return best, load_rop(met), info


def pick_best_across_campaign(
    from_outdir: Path,
) -> tuple[Path, Path, float | None, dict[str, Any]]:
    """
    Return (polish, dest_campaign_root, rop, info).
    Scans sibling tN/r* under campaign root; picks lowest Rop.
    """
    root = campaign_root_from_path(from_outdir)
    runs = sibling_run_dirs(root)
    best: tuple[float, Path, float | None, dict[str, Any]] | None = None
    compared: list[str] = []
    for run in runs:
        compared.append(str(run))
        try:
            polish, rop, info = pick_best_polish_in_folder(run)
        except FileNotFoundError:
            continue
        key = rop if rop is not None else float("inf")
        if best is None or key < best[0]:
            best = (key, polish, rop, info)
    if best is None:
        # Also try root itself for KnotPlot-style flat folders
        try:
            polish, rop, info = pick_best_polish_in_folder(root)
            return polish, root, rop, {**info, "compared_dirs": [str(root)]}
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"no polish under campaign {root} (checked {compared})"
            ) from exc
    _, polish, rop, info = best
    info = {**info, "compared_dirs": compared, "campaign_root": str(root)}
    return polish, root, rop, info


def default_dest_for_polish(polish: Path, *, knots_hint: bool = False) -> Path:
    """Infer destination directory for the snapshot."""
    parent = polish.resolve().parent
    # Under tN / r* → campaign root
    if _TN_RE.match(parent.name) or parent.name.startswith("r_"):
        return parent.parent
    if parent.name.startswith("r") and parent.name[1:].isdigit():
        return parent.parent
    # KnotPlot knots/<id>/ → same folder
    return parent


def infer_build_stem(folder: Path) -> str | None:
    preferred = folder / f"build_{folder.name}.kpc"
    if preferred.is_file():
        return preferred.stem
    builds = sorted(
        p
        for p in folder.glob("build_*.kpc")
        if "effort" not in p.stem.lower()
    )
    if builds:
        return builds[0].stem
    return None


def is_knots_catalog_dest(dest_dir: Path, *, knots_root: Path | None = None) -> bool:
    """True if dest_dir is a direct child of a KnotPlot knots/ catalog root."""
    try:
        dest_dir = dest_dir.resolve()
    except OSError:
        return False
    parent = dest_dir.parent
    if knots_root is not None:
        return parent == knots_root.resolve()
    if parent == DEFAULT_KNOTS_ROOT.resolve():
        return True
    # Also accept …/knots/<id> in tests / alternate checkouts
    return parent.name.lower() == "knots"


def shared_final_stem(build_id: str) -> str:
    """Stable basename without extension: {id}_final."""
    return f"{sanitize_token(build_id)}_final"


def mirror_final_to_shared(
    final_txt: Path,
    *,
    build_id: str,
    shared_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Copy a historical final next to .kpc into knots/final/{id}_final.* (overwrite).
    """
    final_txt = final_txt.resolve()
    if not final_txt.is_file():
        raise FileNotFoundError(f"final not found: {final_txt}")

    dest_root = (shared_dir or DEFAULT_SHARED_FINALS).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    stem = shared_final_stem(build_id)
    out_txt = dest_root / f"{stem}.txt"
    out_met = dest_root / f"{stem}.metrics.json"
    out_alias = dest_root / f"{stem}.alias.json"

    shutil.copy2(final_txt, out_txt)

    src_met = Path(str(final_txt).removesuffix(".txt") + ".metrics.json")
    if src_met.is_file():
        shutil.copy2(src_met, out_met)
    elif out_met.is_file():
        out_met.unlink()

    src_alias = Path(str(final_txt).removesuffix(".txt") + ".alias.json")
    alias: dict[str, Any] = {}
    if src_alias.is_file():
        try:
            alias = json.loads(src_alias.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            alias = {}
    alias["build_id"] = build_id
    alias["source_final"] = str(final_txt)
    alias["shared_final"] = str(out_txt)
    if "final_txt" not in alias:
        alias["final_txt"] = str(final_txt)
    out_alias.write_text(json.dumps(alias, indent=2) + "\n", encoding="utf-8")

    written: dict[str, Path] = {"txt": out_txt, "alias": out_alias}
    if out_met.is_file():
        written["metrics"] = out_met
    return written


def try_mirror_final_to_shared(
    final_txt: Path,
    *,
    build_id: str,
    shared_dir: Path | None = None,
) -> dict[str, Path] | None:
    """Best-effort shared-folder mirror; WARNING on failure."""
    try:
        written = mirror_final_to_shared(
            final_txt, build_id=build_id, shared_dir=shared_dir
        )
        print(f"Shared final: {written['txt']}", flush=True)
        return written
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"WARNING: shared final mirror failed: {exc}", flush=True)
        return None


def write_final_snapshot(
    polish: Path,
    *,
    stem: str,
    tag: str,
    dest: Path | None = None,
    suffix: str | None = None,
    when: datetime | None = None,
    extra_alias: dict[str, Any] | None = None,
    shared_dir: Path | None = None,
    mirror_shared: bool = True,
) -> dict[str, Path]:
    """
    Copy polish (+ metrics) to unique final paths. Returns dict of written paths.
    When dest is knots/<id>/, also mirrors to knots/final/{id}_final.* (overwrite).
    """
    polish = polish.resolve()
    if not polish.is_file():
        raise FileNotFoundError(f"polish not found: {polish}")

    dest_dir = (dest or default_dest_for_polish(polish)).resolve()
    base = final_basename(stem, tag, suffix=suffix, when=when)
    txt_path = unique_path(dest_dir, base, ext=".txt")
    # Keep metrics/alias aligned with txt basename (including _2 suffix)
    stem_out = txt_path.name[: -len(".txt")]
    met_path = dest_dir / f"{stem_out}.metrics.json"
    alias_path = dest_dir / f"{stem_out}.alias.json"

    shutil.copy2(polish, txt_path)
    src_met = Path(str(polish).removesuffix(".txt") + ".metrics.json")
    if src_met.is_file():
        shutil.copy2(src_met, met_path)
    else:
        met_path = None  # type: ignore[assignment]

    alias: dict[str, Any] = {
        "stem": stem,
        "tag": tag,
        "suffix": suffix,
        "polish_path": str(polish),
        "final_txt": str(txt_path),
        "final_metrics": str(met_path) if met_path else None,
    }
    m = re.search(r"_(\d{8}_\d{6})(?:_\d+)?$", stem_out)
    if m:
        alias["timestamp"] = m.group(1)
    if extra_alias:
        alias.update(extra_alias)
    alias_path.write_text(json.dumps(alias, indent=2) + "\n", encoding="utf-8")

    written: dict[str, Path] = {"txt": txt_path, "alias": alias_path}
    if met_path is not None and met_path.is_file():
        written["metrics"] = met_path

    if mirror_shared and is_knots_catalog_dest(dest_dir):
        mirrored = try_mirror_final_to_shared(
            txt_path,
            build_id=dest_dir.name,
            shared_dir=shared_dir,
        )
        if mirrored is not None:
            written["shared_txt"] = mirrored["txt"]
            written["shared_alias"] = mirrored["alias"]
            if "metrics" in mirrored:
                written["shared_metrics"] = mirrored["metrics"]
    return written


def try_write_final_snapshot(
    polish: Path,
    *,
    stem: str,
    tag: str,
    dest: Path | None = None,
    suffix: str | None = None,
    extra_alias: dict[str, Any] | None = None,
) -> Path | None:
    """Best-effort snapshot for outer drivers; prints WARNING and returns None on failure."""
    try:
        written = write_final_snapshot(
            polish,
            stem=stem,
            tag=tag,
            dest=dest,
            suffix=suffix,
            extra_alias=extra_alias,
        )
        print(f"Final snapshot: {written['txt']}", flush=True)
        return written["txt"]
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"WARNING: final snapshot failed: {exc}", flush=True)
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Copy Ridgerunner polish to a unique *_final_* snapshot "
            "(never overwrites; additive only)"
        )
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--polish", type=Path, help="explicit polish .txt path")
    src.add_argument(
        "--from-outdir",
        type=Path,
        help="discover best polish in folder / campaign (compares tN siblings)",
    )
    ap.add_argument("--stem", default=None, help="name stem (e.g. build_knot_3.1)")
    ap.add_argument("--tag", default="finalize", help="tag segment (effort / N900 / …)")
    ap.add_argument("--suffix", default=None, help="optional extra name segment")
    ap.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="destination directory (default: inferred)",
    )
    args = ap.parse_args(argv)

    compared: list[str] = []
    rop: float | None = None
    try:
        if args.polish is not None:
            polish = args.polish.resolve()
            dest = args.dest
            if dest is None:
                dest = default_dest_for_polish(polish)
            stem = args.stem
            if not stem:
                # try build stem if dest/parent is knot folder
                stem = infer_build_stem(dest) or dest.name
            info: dict[str, Any] = {"pick": "explicit"}
        else:
            polish, campaign, rop, info = pick_best_across_campaign(args.from_outdir)
            dest = args.dest or campaign
            # KnotPlot flat folder: dest stays the folder
            if (args.from_outdir / "build_knotplot.log").exists() or list(
                Path(args.from_outdir).glob("build_*.kpc")
            ):
                flat = Path(args.from_outdir).resolve()
                if not _TN_RE.match(flat.name):
                    dest = args.dest or flat
            stem = args.stem
            if not stem:
                stem = infer_build_stem(Path(dest)) or Path(dest).name
            compared = list(info.get("compared_dirs") or [])
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    assert stem is not None
    try:
        written = write_final_snapshot(
            polish,
            stem=stem,
            tag=args.tag,
            dest=dest,
            suffix=args.suffix,
            extra_alias={
                "rop": rop,
                "compared_dirs": compared or info.get("compared_dirs"),
                "pick": info.get("pick"),
            },
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(str(written["txt"]))
    if "metrics" in written:
        print(f"metrics: {written['metrics']}")
    print(f"alias:   {written['alias']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
