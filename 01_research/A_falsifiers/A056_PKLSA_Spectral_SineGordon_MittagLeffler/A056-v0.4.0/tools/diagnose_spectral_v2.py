from __future__ import annotations

from pathlib import Path
import argparse
import json

from a056_science.io import discover_cases, uniformity
from a056_science.spectral import spectral_qualification


def main():
    ap = argparse.ArgumentParser(description="Read-only A056-v0.4.0 circular/Fourier G2 diagnostic.")
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--config", default="configs/e010_real_score.json")
    ap.add_argument("--output", default="A056_G2_V040_DIAGNOSTICS_READONLY.json")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    inp = Path(args.input_dir)
    if not inp.is_absolute():
        inp = root / inp
    cp = Path(args.config)
    if not cp.is_absolute():
        cp = root / cp
    cfg = json.loads(cp.read_text(encoding="utf-8"))

    rows = []
    for case in discover_cases(inp):
        m = case["meta"]
        t, s, phi = case["t"], case["s"], case["phi"]
        tr, _ = uniformity(t); sr, _ = uniformity(s)
        sm, _, _ = spectral_qualification(phi, cfg["spectral"], cfg["phase"]["discovery_fraction"])
        inv = sm["blocking"]; legacy = sm["legacy_raw_phase_pod_diagnostic"]
        rows.append({
            "opaque_id": m.get("opaque_id", case["path"].stem),
            "nt": len(t), "ns": len(s),
            "t_uniform_rel": tr, "s_uniform_rel": sr,
            "spectral_method": sm["method"], "spectral_pass": sm["pass"],
            **inv,
            "legacy_raw_phase_pod_diagnostic": legacy,
        })

    payload = {
        "schema": "A056-G2-V040-DIAGNOSTIC-READONLY-1",
        "decision_authority": "NONE_READ_ONLY",
        "input_dir": str(inp),
        "config": str(cp),
        "thresholds": cfg["spectral"],
        "cases": rows,
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = root / out
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
