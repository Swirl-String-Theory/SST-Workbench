"""Robust Python-owned focus campaign launcher.

Windows .cmd deliberately does not parse --name=value options.  It forwards the
original command line verbatim to this module, and argparse owns all option
parsing.  This avoids cmd.exe tokenisation surprises around '=' and ','.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from .util import clean_json
from .workflow import (
    run_analyze_sciii_provenance,
    run_analyze_sciii_stage_a,
    run_analyze_sciii_gauge,
    run_analyze_sciii_stage_b,
    run_branch,
    run_prepare_provenance,
    run_scan_provenance,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sst-modal-clock-focus")
    p.add_argument("topology", help="Topology selector, e.g. 3_1, K3.1, L2a1, L2.2.1")
    p.add_argument("--libraries", default=None, help="Comma-separated: Fremlin,Gilbert,Katlas,KnotPlot")
    p.add_argument("--min-carriers", type=int, default=None, help="Minimum distinct source-family carriers")
    p.add_argument("--kind", choices=["all", "knots", "links"], default=None)
    p.add_argument("--config", default=r"config\basic.json")
    p.add_argument("--out", default=None, help="Optional output directory; default outputs/focus_<topology>")
    return p


def parse_args(argv=None):
    ns = build_parser().parse_args(argv)
    if ns.min_carriers is not None and ns.min_carriers < 1:
        build_parser().error("--min-carriers must be >= 1")
    return ns


def _safe_tag(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("._") or "topology"


def _dump(label: str, obj) -> None:
    print(f"\n--- {label} ---", flush=True)
    print(json.dumps(clean_json(obj), indent=2, sort_keys=True), flush=True)


def main(argv=None) -> int:
    ns = parse_args(argv)
    config = ns.config
    out = Path(ns.out) if ns.out else Path("outputs") / f"focus_{_safe_tag(ns.topology)}"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        shutil.rmtree(out)

    print("=" * 60, flush=True)
    print("SST SC-III Koopman/DMD Complex Phase Clock v0.1.0 - Python focus runner", flush=True)
    print(f"Topology:     {ns.topology}", flush=True)
    print(f"Libraries:    {ns.libraries or '(config default)'}", flush=True)
    print(f"Min carriers: {ns.min_carriers if ns.min_carriers is not None else '(config default)'}", flush=True)
    print(f"Kind:         {ns.kind or '(config default)'}", flush=True)
    print(f"Output:       {out}", flush=True)
    print("=" * 60, flush=True)

    scan = run_scan_provenance(config, ns.libraries, ns.min_carriers, ns.kind, ns.topology)
    scan_path = Path("outputs") / f"SOURCE_SCAN_{_safe_tag(ns.topology)}.json"
    scan_path.write_text(json.dumps(clean_json(scan), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _dump("SOURCE SCAN", scan)

    prep = run_prepare_provenance(out, config, ns.libraries, ns.min_carriers, ns.kind, ns.topology)
    _dump("PREPARE", prep)

    _dump("STAGE A", run_branch(out, config, "stage_a"))
    _dump("ANALYZE SC-III STAGE A", run_analyze_sciii_stage_a(out, config))
    _dump("GAUGE LOW", run_branch(out, config, "stage_a_gauge_low"))
    _dump("GAUGE HIGH", run_branch(out, config, "stage_a_gauge_high"))
    _dump("ANALYZE SC-III GAUGE", run_analyze_sciii_gauge(out, config))
    _dump("ANALYZE SC-III PROVENANCE", run_analyze_sciii_provenance(out, config))
    _dump("STAGE B MATERIAL", run_branch(out, config, "material"))
    _dump("STAGE B FIXED", run_branch(out, config, "fixed"))
    final = run_analyze_sciii_stage_b(out, config)
    _dump("FINAL", final)

    print(f"\nSource scan: {scan_path}", flush=True)
    print(f"Blind result: {out / 'analysis' / 'blind_sciii_summary.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
