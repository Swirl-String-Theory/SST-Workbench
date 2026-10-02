#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sst_link_suite.models import jsonable
from sst_link_suite.parser import parse_ideal_links, select_links
from sst_link_suite.continuum import audit_link_continuum
from sst_link_suite.native_ext import BackendOptions, backend_status


def main() -> int:
    ap = argparse.ArgumentParser(description="v0.3.5 split spectral/hydrodynamic continuum audit")
    ap.add_argument("--input", default=str(ROOT / "data" / "idealLinks.txt"))
    ap.add_argument("--output", default=str(ROOT / "outputs_continuum"))
    ap.add_argument("--config", default=str(ROOT / "configs" / "qm_full.json"))
    ap.add_argument("--ids", nargs="*", default=["L2a1", "L4a1", "L6a4", "L6n1", "L7n2"])
    ap.add_argument("--all-database", action="store_true")
    ap.add_argument("--require-native", action="store_true", default=True)
    ap.add_argument("--skip-native-build", action="store_true")
    ap.add_argument("--force-native-build", action="store_true")
    ap.add_argument("--build-verbose", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    options = BackendOptions(
        require_native=args.require_native,
        skip_build=args.skip_native_build,
        force_build=args.force_native_build,
        build_verbose=args.build_verbose,
    )
    backend = backend_status(options)
    links = select_links(parse_ideal_links(args.input), args.ids, args.all_database)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    per = out / "per_link"; per.mkdir(exist_ok=True)
    results = []
    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] continuum {link.link_id}", flush=True)
        result = audit_link_continuum(link, cfg, options)
        (per / f"{link.link_id}.json").write_text(json.dumps(jsonable(result), indent=2), encoding="utf-8")
        results.append(result)
    rows = [{
        "link_id": r["link_id"],
        "continuum_pass": r["continuum_pass"],
        "v040_numerical_spectral_ready": r["v040_numerical_spectral_ready"],
        "geometry_continuum_pass": r["geometry_continuum_pass"],
        "hydrodynamic_continuum_pass": r["hydrodynamic_continuum_pass"],
        "spectral_tail_contaminated_risk": r["spectral_tail_audit"]["spectral_tail_contaminated_risk"],
        "max_last_pair_relative_difference": r["max_last_pair_relative_difference"],
        "geometry_max_last_pair_relative_difference": r["geometry_max_last_pair_relative_difference"],
        "hydrodynamic_max_last_pair_relative_difference": r["hydrodynamic_max_last_pair_relative_difference"],
        "spectral_geometry_sample_ns": ",".join(map(str, r["spectral_geometry_sample_ns"])),
        "hydrodynamic_sample_ns": ",".join(map(str, r["hydrodynamic_sample_ns"])),
        "energy_exclusion_arc_D": r["self_exclusion_energy_arc_D"],
        "velocity_exclusion_arc_D": r["self_exclusion_velocity_arc_D"],
    } for r in results]
    pd.DataFrame(rows).to_csv(out / "continuum_summary.csv", index=False)
    (out / "continuum_metadata.json").write_text(json.dumps(jsonable({
        "backend": backend, "config": cfg, "ids": [r["link_id"] for r in results]
    }), indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
