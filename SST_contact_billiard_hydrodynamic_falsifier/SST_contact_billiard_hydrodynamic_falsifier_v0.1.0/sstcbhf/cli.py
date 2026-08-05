from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .campaign import analyze_curve, convergence_campaign
from .constants import R_C
from .io import load_curve, load_gilbert_curve, torus_trefoil, write_xyz
from .util import sha256_file


def _source_for_path(path: Path, kind: str, extra: dict | None = None) -> dict:
    payload = {
        "kind": kind,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
    }
    if extra:
        payload.update(extra)
    return payload


def _load_input(args):
    if getattr(args, "database", None):
        path = Path(args.database)
        points, record = load_gilbert_curve(path, args.id, args.source_samples, args.component)
        source = _source_for_path(path, "gilbert_fourier_database", {
            "record_id": record.record_id,
            "component": args.component,
            "reported_length": record.reported_length,
            "diameter": record.diameter,
            "coefficient_count": len(record.components[args.component]),
            "highest_mode": max(item[0] for item in record.components[args.component]),
        })
        return points, source
    if getattr(args, "input", None):
        path = Path(args.input)
        source = _source_for_path(path, "xyz_or_vect")
        sidecar = path.with_suffix(".metrics.json")
        if sidecar.exists():
            source["metrics_sidecar_path"] = str(sidecar.resolve())
            source["metrics_sidecar_sha256"] = sha256_file(sidecar)
        return load_curve(path), source
    raise ValueError("provide --input or --database")


def add_input_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path, help="KnotPlot/Ridgerunner XYZ/TXT or VECT curve")
    group.add_argument("--database", type=Path, help="Brian Gilbert ideal.txt/ideal_favorites.txt")
    parser.add_argument("--id", default="3:1:1", help="Gilbert record ID")
    parser.add_argument("--component", type=int, default=0, help="zero-based component index")
    parser.add_argument("--source-samples", type=int, default=4096, help="initial Fourier samples")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sst-cbhf",
        description="SST contact-map -> 9-billiard -> force balance -> finite-core hydrodynamic falsification harness",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the full harness on an analytic non-ideal torus trefoil control")
    demo.add_argument("--out", type=Path, default=Path("outputs/demo_torus_trefoil"))
    demo.add_argument("--samples", type=int, default=192)
    demo.add_argument("--hydro-samples", type=int, default=64)
    demo.add_argument("--skip-hydro", action="store_true")
    demo.add_argument("--thresholds-json", type=Path)

    analyze = sub.add_parser("analyze", help="analyze one Ridgerunner/KnotPlot or Gilbert curve")
    add_input_arguments(analyze)
    analyze.add_argument("--out", type=Path, required=True)
    analyze.add_argument("--samples", type=int, default=256)
    analyze.add_argument("--hydro-samples", type=int, default=96)
    analyze.add_argument("--exclusion-fraction", type=float, default=0.03)
    analyze.add_argument("--core-ratios", type=float, nargs="+", default=[0.10, 0.20, 0.35, 0.50, 0.75, 1.00])
    analyze.add_argument("--physical-thickness", type=float, default=R_C, help="metres; default maps geometric thickness to canonical r_c")
    analyze.add_argument("--skip-hydro", action="store_true")
    analyze.add_argument("--hydro-interactions", nargs="+", choices=["full", "local", "nonlocal"], default=["full", "nonlocal"])
    analyze.add_argument("--local-band", type=int, default=3, help="cyclic segment half-band removed in the nonlocal diagnostic")
    analyze.add_argument("--thresholds-json", type=Path, help="JSON object overriding configured gate thresholds")

    conv = sub.add_parser("convergence", help="contact and 9-billiard resolution ladder")
    add_input_arguments(conv)
    conv.add_argument("--out", type=Path, required=True)
    conv.add_argument("--resolutions", type=int, nargs="+", default=[128, 192, 256, 384])
    conv.add_argument("--exclusion-fraction", type=float, default=0.03)

    export = sub.add_parser("export-gilbert", help="export one Gilbert Fourier record as XYZ")
    export.add_argument("--database", type=Path, required=True)
    export.add_argument("--id", default="3:1:1")
    export.add_argument("--component", type=int, default=0)
    export.add_argument("--samples", type=int, default=1200)
    export.add_argument("--out", type=Path, required=True)

    bridge = sub.add_parser("make-rr-bridge", help="write a Windows BAT that analyzes an existing Ridgerunner output")
    bridge.add_argument("--input", type=Path, required=True)
    bridge.add_argument("--out-dir", type=Path, default=Path("outputs/ridgerunner_contact_hydro"))
    bridge.add_argument("--bat", type=Path, default=Path("RUN_RIDGERUNNER_CONTACT_HYDRO.bat"))
    bridge.add_argument("--samples", type=int, default=384)
    bridge.add_argument("--hydro-samples", type=int, default=96)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "demo":
            points = torus_trefoil(max(2048, args.samples * 8))
            thresholds = json.loads(args.thresholds_json.read_text(encoding="utf-8")) if args.thresholds_json else None
            summary = analyze_curve(
                points,
                args.out,
                source={"kind": "analytic_torus_trefoil_negative_control", "major_radius": 2.0, "minor_radius": 1.0},
                samples=args.samples,
                hydro_samples=args.hydro_samples,
                skip_hydro=args.skip_hydro,
                thresholds=thresholds,
            )
            print(summary["scientific_verdict"])
            print(args.out.resolve())
            return 0
        if args.command == "analyze":
            points, source = _load_input(args)
            thresholds = json.loads(args.thresholds_json.read_text(encoding="utf-8")) if args.thresholds_json else None
            summary = analyze_curve(
                points,
                args.out,
                source=source,
                samples=args.samples,
                hydro_samples=args.hydro_samples,
                exclusion_fraction=args.exclusion_fraction,
                core_ratios=args.core_ratios,
                physical_thickness_m=args.physical_thickness,
                skip_hydro=args.skip_hydro,
                hydro_interactions=args.hydro_interactions,
                local_band=args.local_band,
                thresholds=thresholds,
            )
            print(summary["scientific_verdict"])
            print(args.out.resolve())
            return 0 if summary["all_executed_blocking_gates_pass"] else 2
        if args.command == "convergence":
            points, source = _load_input(args)
            convergence_campaign(points, args.out, source=source, resolutions=args.resolutions, exclusion_fraction=args.exclusion_fraction)
            print(args.out.resolve())
            return 0
        if args.command == "export-gilbert":
            points, record = load_gilbert_curve(args.database, args.id, args.samples, args.component)
            write_xyz(args.out, points)
            print(f"{record.record_id}: {len(points)} points -> {args.out.resolve()}")
            return 0
        if args.command == "make-rr-bridge":
            text = f'''@echo off
setlocal
cd /d "%~dp0"
py -3 -m sstcbhf analyze --input "{args.input}" --samples {args.samples} --hydro-samples {args.hydro_samples} --out "{args.out_dir}"
set RC=%ERRORLEVEL%
echo.
if %RC% EQU 0 (
  echo All configured gates passed.
) else (
  echo One or more gates failed or remain unresolved. Exit code %RC%.
)
pause
exit /b %RC%
'''
            args.bat.write_text(text, encoding="utf-8")
            print(args.bat.resolve())
            return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 1
