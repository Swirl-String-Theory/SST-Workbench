from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_maxwell_falsifier.io import load_npz
from sst_maxwell_falsifier.gates import transverse_gate, displacement_gate, gravity_gate
from sst_maxwell_falsifier.freeze import sha256_file, write_frozen_result


def main():
    ap = argparse.ArgumentParser(description="Run target-blind Maxwell-SST DFC gates")
    ap.add_argument("--campaign", required=True, type=Path, help="directory containing transverse.npz, displacement.npz, gravity.npz")
    ap.add_argument("--config", type=Path, default=ROOT/"configs"/"preregister_v0.2.0.json")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    config_hash = sha256_file(args.config)
    gates = []
    metas = {}
    for name, fn, file in [
        ("transverse", transverse_gate, "transverse.npz"),
        ("displacement", displacement_gate, "displacement.npz"),
        ("gravity", gravity_gate, "gravity.npz"),
    ]:
        arrays, meta = load_npz(args.campaign/file)
        metas[name] = meta
        gates.append(fn(arrays, meta, cfg))

    statuses = [g["status"] for g in gates]
    overall = "INVALID" if "INVALID" in statuses else ("FAIL" if "FAIL" in statuses else "PASS")
    result = {
        "protocol": cfg["protocol"],
        "protocol_version": cfg["version"],
        "campaign": str(args.campaign.resolve()),
        "preregistration_file": str(args.config.resolve()),
        "preregistration_sha256": config_hash,
        "overall_status": overall,
        "gates": gates,
        "campaign_metadata": metas,
        "blindness_statement": "No c target, Newtonian exponent target, or electromagnetic SI K_P target participates in this run."
    }
    out = args.out or (args.campaign/"frozen_result.json")
    out, digest = write_frozen_result(out, result)
    print(json.dumps({"overall_status": overall, "result": str(out), "sha256": digest}, indent=2))
    for g in gates:
        print(f"{g['gate']}: {g['status']}")
    return 0 if overall == "PASS" else (2 if overall == "FAIL" else 3)

if __name__ == "__main__":
    raise SystemExit(main())
