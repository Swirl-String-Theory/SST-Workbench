#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TIERS = {
    "quick": {
        "step01": ["--n", "24"],
        "step02": ["--resolutions", "24", "48", "64", "--integer-tolerance", "0.12", "--gauge-tolerance", "0.04"],
        "step03": ["--n-grid", "32"],
        "step06": ["--samples", "500"],
        "step07": ["--samples", "501"],
        "step08": ["--samples", "220", "--radial-samples", "6", "--angular-samples", "16"],
    },
    "standard": {
        "step01": ["--n", "48"],
        "step02": ["--resolutions", "24", "32", "48", "64"],
        "step03": ["--n-grid", "64"],
        "step06": ["--samples", "1000"],
        "step07": ["--samples", "1001"],
        "step08": ["--samples", "400", "--radial-samples", "8", "--angular-samples", "24"],
    },
    "high": {
        "step01": ["--n", "80"],
        "step02": ["--resolutions", "48", "64", "96", "128", "--fiber-samples", "1200", "--integer-tolerance", "0.06"],
        "step03": ["--n-grid", "96"],
        "step06": ["--samples", "4000"],
        "step07": ["--samples", "4001"],
        "step08": ["--samples", "1200", "--radial-samples", "12", "--angular-samples", "48"],
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run SST Hopf steps 1-8 in one chain.")
    p.add_argument("--tier", choices=TIERS, default="standard")
    p.add_argument("--out-root", type=Path)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--force-build", action="store_true")
    p.add_argument("--build-verbose", action="store_true")
    p.add_argument("--continue-on-error", action="store_true")
    return p.parse_args()


def run(cmd: list[str], env: dict[str, str], log: Path) -> dict:
    print("\n>>", " ".join(cmd), flush=True)
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - t0
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(proc.stdout, encoding="utf-8")
    print(proc.stdout, end="")
    return {"command": cmd, "returncode": proc.returncode, "elapsed_s": elapsed, "log": str(log)}


def main() -> int:
    args = parse_args()
    out = args.out_root or ROOT / "results" / f"{args.tier}_{'python' if args.force_python else 'cpp'}"
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    logs = out / "logs"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["SST_HOPF_FORCE_PYTHON"] = "1" if args.force_python else "0"
    env["SST_HOPF_FORCE_BUILD"] = "1" if args.force_build else "0"
    env["SST_HOPF_BUILD_VERBOSE"] = "1" if args.build_verbose else "0"

    records: list[dict] = []
    if not args.force_python:
        build_cmd = [sys.executable, "-m", "sst_hopf_native.build_ext_if_needed", "--strict"]
        if args.force_build:
            build_cmd.append("--force")
        if not args.build_verbose:
            build_cmd.append("--quiet")
        rec = run(build_cmd, env, logs / "00_build.log")
        records.append({"step": "build", **rec})
        if rec["returncode"] != 0:
            (out / "run_summary.json").write_text(json.dumps({"ok": False, "records": records}, indent=2), encoding="utf-8")
            return rec["returncode"]

    cfg = TIERS[args.tier]
    s01 = out / "step01_order_parameter"
    s02 = out / "step02_hopf_benchmark"
    s03 = out / "step03_toroflux_spinor"
    s04 = out / "step04_hopf_charge"
    s05 = out / "step05_helicity_bridge"
    s06 = out / "step06_spin_action"
    s07 = out / "step07_four_pi"
    s08 = out / "step08_trefoil"

    commands = [
        ("step01", [sys.executable, "01_definieer_sst_orderparameter.py", "--output", str(s01), *cfg["step01"]]),
        ("step02", [sys.executable, "02_analytische_hopf_benchmark.py", "--output", str(s02), *cfg["step02"]]),
        ("step03", [sys.executable, "03_toroflux_spinorveld.py", "--output", str(s03), *cfg["step03"]]),
        ("step04", [sys.executable, "04_hopf_lading_numeriek.py", str(s02 / "analytic_hopf_benchmark.npz"), "--output", str(s04)]),
        ("step05", [sys.executable, "05_heliciteitsbridge.py", str(s04 / "hopf_charge_fields.npz"), "--output", str(s05)]),
        ("step06", [sys.executable, "06_effectieve_spinactie.py", "--output", str(s06), *cfg["step06"]]),
        ("step07", [sys.executable, "07_vier_pi_configuratieruimte.py", "--output", str(s07), *cfg["step07"]]),
        ("step08", [sys.executable, "08_trefoil_integratie.py", "--output", str(s08), *cfg["step08"]]),
    ]

    ok = True
    for step, cmd in commands:
        rec = run(cmd, env, logs / f"{step}.log")
        records.append({"step": step, **rec})
        if rec["returncode"] != 0:
            ok = False
            if not args.continue_on_error:
                break

    try:
        from sst_hopf_common import backend_info
        backend = backend_info()
    except Exception as exc:
        backend = {"backend": "unknown", "error": repr(exc)}

    summary = {
        "tier": args.tier,
        "backend": backend,
        "force_python": args.force_python,
        "ok": ok,
        "records": records,
        "total_elapsed_s": sum(r["elapsed_s"] for r in records),
    }
    (out / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== SST HOPF RUN SUMMARY ===")
    print(json.dumps(summary, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
