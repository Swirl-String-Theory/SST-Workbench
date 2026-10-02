#!/usr/bin/env python3
"""SST chi-phase v16B.0 — patched Madelung-SST bridge simulation runner."""

import csv, json, time, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sst_chi_phase_v16B0_py as v16

EXPORTS = Path(__file__).parent / "exports"
EXPORTS.mkdir(exist_ok=True)

def write_csv(path, rows):
    if not rows: return
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def run():
    t0 = time.perf_counter()
    print("SST chi-phase v16B.0: patched Madelung-SST bridge")
    print("=" * 52)

    res = v16.run_v16b0()

    # --- Step 1: Pythagorean ---
    p = res["step1_madelung_pythagorean"]
    print()
    print("Step 1: Pythagorean identity  →  A=B")
    print(f"  |∇Ψ|² = {p['grad_Psi_sq']}")
    print(f"  L_gradient = {p['L_gradient']}")
    print(f"  A (amplitude gradient) = 1")
    print(f"  B (phase gradient)     = 1")
    print(f"  A = B: {p['A_equals_B']}  ← {p['reason']}")

    # --- Step 2: EL recovery ---
    e = res["step4_EL_recovery"]
    print()
    print("Step 2: EL of unit Lagrangian  →  unit GP/NLSE ODE")
    print(f"  L = {e['L_unit']}")
    print(f"  EL/(2r) = {e['EL_divided_by_2r'][:60]}...")
    print(f"  Expected = {e['expected_GP_ODE'][:60]}...")
    print(f"  Residual = {e['residual']}")
    print(f"  EL recovers GP ODE: {e['EL_recovers_GP_ODE']}")

    # --- Step 3: healing length ---
    h = res["step2_C_equals_A_healing"]
    print()
    print("Step 3: Healing length normalization  →  C=A")
    print(f"  ξ² = {h['healing_length_def']}")
    print(f"  Dimensionless ratio λξ²/κ = {h['dimensionless_depletion_to_gradient_ratio']}")
    print(f"  C = A: {h['C_equals_A']}  ← {h['interpretation']}")

    # --- Classical vs quantum ---
    stab = res["step3_classical_vs_quantum"]
    print()
    print("Classical (A→0) vs quantum (A=1) core stability:")
    for row in stab:
        tag = "(physical)" if row["physical"] else ""
        F1  = f"{row['F_at_r1']:.4f}" if not (isinstance(row['F_at_r1'], float) and
                                               row['F_at_r1'] != row['F_at_r1']) else "NaN"
        F3  = f"{row['F_at_r3']:.4f}" if not (isinstance(row['F_at_r3'], float) and
                                               row['F_at_r3'] != row['F_at_r3']) else "NaN"
        w   = f"{row['core_transition_width']:.3f}" if not (isinstance(row['core_transition_width'], float) and
                                               row['core_transition_width'] != row['core_transition_width']) else "NaN"
        print(f"  A={row['A_coeff']:.3f}: F(1)={F1}  F(3)={F3}  core_width={w}  {tag}")

    # --- Final result ---
    print()
    print("Result:")
    print(f"  A = B = C = 1  (derived conditional on single-modulus Madelung core)")
    print(f"  α_ring = {res['derived_alpha_ring']:.9f}  (from v12B.0 tail correction; conditional sector)")
    print(f"  β_ring (q=0) = {res['derived_beta_ring_q0']:.9f}")
    print(f"  φ      = {res['phi']:.9f}")
    print(f"  α_ring − φ = {res['delta_alpha_ring_minus_phi']:+.2e}")
    print()
    print("Gate G5: conditionally closed only inside the accepted single-modulus Madelung core sector")
    print("Remaining open gates:", res["remaining_open_gates"])

    # Write exports
    write_csv(EXPORTS / "chi_v16B0_pythagorean_proof.csv",
              [res["step1_madelung_pythagorean"]])
    write_csv(EXPORTS / "chi_v16B0_healing_C_equals_A.csv",
              [res["step2_C_equals_A_healing"]])
    write_csv(EXPORTS / "chi_v16B0_classical_vs_quantum.csv",
              res["step3_classical_vs_quantum"])
    write_csv(EXPORTS / "chi_v16B0_el_recovery.csv",
              [res["step4_EL_recovery"]])

    summary = {k: v for k, v in res.items()
               if k not in ["step1_madelung_pythagorean",
                            "step2_C_equals_A_healing",
                            "step3_classical_vs_quantum",
                            "step4_EL_recovery"]}
    with open(EXPORTS / "chi_v16B0_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    lines = [
        "SST chi-phase v16B.0 — Madelung-SST bridge",
        "=" * 48,
        "",
        "Gate G5: conditionally closed only inside the accepted single-modulus Madelung core sector",
        "",
        "Derivation chain:",
        "  SST axiom: quantum superfluid + quantized vortex",
        "  → Madelung: Ψ = √ρ exp(iφ)  [mathematical identity]",
        "  → |∇Ψ|² = (∂F/∂r)² + n²F²/r²  [Pythagorean → A=B]",
        "  → Depletion: c_s²ρ₀(|Ψ|²-1)²  [barotropic linearization]",
        "  → Healing length ξ² = (ħ/m)²/c_s²  [physical, not convention]",
        "  → After r→r/ξ: C=A  [dimensionless ratio = 1]",
        "  → A=B=C=1 derived conditionally",
        "",
        f"α_ring = {res['derived_alpha_ring']:.9f}  (v12B.0 result; conditional resolved-core sector)",
        f"β_ring = {res['derived_beta_ring_q0']:.9f}  (q=0 line)",
        f"φ      = {res['phi']:.9f}",
        f"α_ring - φ = {res['delta_alpha_ring_minus_phi']:+.2e}",
        "",
        "The classical (A=0) limit loses quantum pressure → no stable core.",
        "A=B requires quantum coherence of SST vacuum.",
        "",
        "Remaining open gates:",
        "  G6: φ-structural selector (α_ring=φ not yet proven)",
        "  G7: ξ=r_c identification (c_s=c from SST EoS not yet derived)",
        "",
        f"Elapsed: {time.perf_counter()-t0:.2f}s",
    ]
    with open(EXPORTS / "chi_v16B0_run_results_summary.txt", "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nExports written to: {EXPORTS}")
    print(f"Elapsed: {time.perf_counter()-t0:.2f}s")

if __name__ == "__main__":
    run()
