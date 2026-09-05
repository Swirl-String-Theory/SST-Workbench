#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.fourier import sample_component
from sst_link_suite.biot_savart import sign_matrix
from sst_link_suite.native_ext import BackendOptions
from sst_link_suite.native_ext.audit import run_native_parity_audit, write_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict C++/Python parity audit for ideal-link kernels.")
    parser.add_argument("--input", default=str(ROOT / "data" / "idealLinks.txt"))
    parser.add_argument("--ids", nargs="+", default=["L2a1", "L6a4"])
    parser.add_argument("--sample-n", type=int, default=128)
    parser.add_argument("--epsilons", default="0.05,0.1,0.2")
    parser.add_argument("--out", default=str(ROOT / "native_audit_out.json"))
    parser.add_argument("--force-build", action="store_true")
    parser.add_argument("--build-verbose", action="store_true")
    args = parser.parse_args()

    database = parse_ideal_links(args.input)
    options = BackendOptions(
        require_native=True,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
    )
    reports = []
    for link_id in args.ids:
        link = database[link_id]
        curves = [sample_component(component, args.sample_n).r for component in link.components]
        report = run_native_parity_audit(
            curves,
            sign_matrix(len(curves)),
            [float(x) for x in args.epsilons.split(",")],
            options,
        )
        reports.append({"link_id": link_id, **report})
    summary = {"ok": all(report["ok"] for report in reports), "reports": reports}
    write_audit(args.out, summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
