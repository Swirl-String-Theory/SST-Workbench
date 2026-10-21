from __future__ import annotations
import json, math
from pathlib import Path
from .core import *


def run(root: Path, config_path: Path, output_root: Path) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    public_path = root / cfg["public_constraints"]
    if "private" in public_path.parts:
        raise RuntimeError("BLIND POLICY VIOLATION: public constraints resolved into private/")
    data = json.loads(public_path.read_text(encoding="utf-8"))
    out = output_root / "blind"
    out.mkdir(parents=True, exist_ok=True)

    p = data["carpet"]
    threshold = float(p["poisson_min_expected_for_5pct_at_least_one"])
    ncp = float(p["conventional_expected_count_order"])
    nalp = float(p["alp_expected_count_upper_order"])

    gates = [
      {"id":"B01_PUBLIC_PROVENANCE", "status":"PASS", "sha256":sha256_file(public_path)},
      {"id":"B02_CONVENTIONAL_POISSON", "status":"FAIL" if ncp < threshold else "PASS",
       "expected_count_order":ncp, "threshold":threshold, "P_N_ge_1":poisson_at_least_one(ncp)},
      {"id":"B03_ALP_ONLY_POISSON", "status":"FAIL" if nalp < threshold else "PASS",
       "expected_count_upper_order":nalp, "threshold":threshold, "P_N_ge_1_upper":poisson_at_least_one(nalp)}
    ]

    upper = data["transparency_upper_95_GeV"]
    pol = data["polarization_lower_GeV_framework_dependent"]
    legacy = data["legacy_A044_v0_1_lower_95_GeV"]
    rows = []
    for n in (1,2):
        hi = float(upper[str(n)]["central"])
        for biref in (False, True):
            # The final compact Letter gives a universal transparency upper bound.
            # Its quoted polarization lower bound is explicitly framework dependent,
            # so it is only applied to the birefringent bookkeeping class.
            lo = float(pol[str(n)]) if biref else 0.0
            inter = intersect([lo], [hi])
            status = "PASS" if inter["nonempty"] else "FAIL"
            cls = f"n{n}_{'birefringent' if biref else 'nonbirefringent'}"
            rows.append({"model_class":cls,"n":n,"birefringent":biref,"primary_lower_GeV":lo,"upper_GeV":hi,"status":status})
            gates.append({"id":f"B1{len(rows)}_{cls.upper()}_PRIMARY_WINDOW", "status":status, **rows[-1]})

    legacy_rows=[]
    for n in (1,2):
        lo=max(float(legacy["time_of_flight_GRB221009A"][str(n)]), float(legacy["breit_wheeler_spectral"][str(n)]))
        hi=float(upper[str(n)]["central"])
        legacy_rows.append({"n":n,"legacy_effective_lower_GeV":lo,"upper_GeV":hi,"nonempty":lo<hi})
    gates.append({"id":"B15_LEGACY_V0_1_BASELINE_WINDOWS", "status":"CONDITIONAL", "rows":legacy_rows,
                  "note":"Retained for A044 continuity. Applicability to an SST candidate depends on its electron sector, reaction kinematics and source-timing assumptions; therefore these lower bounds are not silently promoted to universal hard bounds."})

    # Kinematic threshold uplift at the event energy.
    Eevent = float(p["energy_TeV"]["central"])
    eps0 = pair_threshold_eV(Eevent)
    threshold_diag = []
    for n in (1,2):
        hi = float(upper[str(n)]["central"])
        eps = pair_threshold_eV(Eevent, hi, n)
        threshold_diag.append({"n":n,"E_star_GeV":hi,"epsilon_standard_eV":eps0,
                               "epsilon_modified_eV":eps,"uplift_ratio":eps/eps0})
    gates.append({"id":"B20_PAIR_THRESHOLD_UPLIFT_DIAGNOSTIC", "status":"DIAGNOSTIC", "rows":threshold_diag,
                  "scope":"Head-on threshold only; not a full optical-depth reproduction."})

    # Conditional timing inversion from observed windows.
    c = data["diagnostic_cosmology"]
    lowE = float(cfg["timing_diagnostic"]["representative_low_energy_TeV"])
    N = int(cfg["timing_diagnostic"]["simpson_intervals"])
    tcarpet = float(p["arrival_time_after_trigger_s"])
    tlow = data["lhaaso"]["km2a_arrival_time_after_trigger_s"]
    dt_min = tcarpet - float(tlow["high"])
    dt_max = tcarpet - float(tlow["low"])
    timing = []
    for n in (1,2):
        # Larger dt -> smaller inferred E*.
        e_lo = invert_tof_scale_GeV(Eevent, lowE, dt_max, n, data["source_object"]["redshift"],
                                    c["H0_km_s_Mpc"], c["Omega_m"], c["Omega_Lambda"], N)
        e_hi = invert_tof_scale_GeV(Eevent, lowE, dt_min, n, data["source_object"]["redshift"],
                                    c["H0_km_s_Mpc"], c["Omega_m"], c["Omega_Lambda"], N)
        timing.append({"n":n,"delay_window_s":[dt_min,dt_max],"representative_low_energy_TeV":lowE,
                       "inferred_E_star_GeV":[e_lo,e_hi]})
    gates.append({"id":"B21_SIMPLE_TOF_INVERSION", "status":"CONDITIONAL", "rows":timing,
                  "assumption":"Common emission episode; intrinsic source delay neglected."})

    pubt = data["published_timing_scale_n2_GeV"]
    n2_hi = float(upper["2"]["central"])
    pub_c = float(pubt["central"])
    gates.append({"id":"B22_PUBLISHED_N2_TIMING_VS_TRANSPARENCY", "status":"PASS" if pub_c < n2_hi else "FAIL",
                  "timing_scale_central_GeV":pub_c,"transparency_upper_GeV":n2_hi,
                  "interpretation":"Matches the compatibility statement made in the final Letter."})

    legacy_n2_lower = max(float(legacy["time_of_flight_GRB221009A"]["2"]), float(legacy["breit_wheeler_spectral"]["2"]))
    gates.append({"id":"B23_LEGACY_N2_LOWER_VS_PUBLISHED_TIMING_SCALE", "status":"CONDITIONAL",
                  "legacy_effective_lower_GeV":legacy_n2_lower,
                  "published_timing_interval_GeV":[pub_c-float(pubt["minus"]), pub_c+float(pubt["plus"])],
                  "note":"Numerical tension under naive interval combination is recorded, not promoted to a hard rejection because the constraints are framework/model-likelihood dependent."})

    surviving = [r["model_class"] for r in rows if r["status"] == "PASS"]
    rejected = [r["model_class"] for r in rows if r["status"] == "FAIL"]
    verdict = {
      "campaign_id":data["campaign_id"],
      "verdict":"BLIND_WINDOWS_FROZEN",
      "surviving_model_classes":surviving,
      "rejected_model_classes":rejected,
      "sst_closure":"NOT_EVALUATED_IN_BLIND_PHASE",
      "blind_engine_read_private":False,
      "gates":gates
    }
    dump_json(out/"verdict.json", verdict)
    dump_json(out/"public_constraints_snapshot.json", data)
    (out/"public_input_sha256.txt").write_text(sha256_file(public_path)+"\n", encoding="utf-8")

    lines=["# A044 v0.2.0 blind report","",f"**Verdict:** `{verdict['verdict']}`","",
           "The blind phase did not read SST constants or candidate identity.","",
           "## Published observability gates","",
           f"- Conventional expected count: ~`{ncp:.1e}` vs 5% one-event threshold `{threshold:.8f}` -> **FAIL**.",
           f"- ALP-only upper expected count: ~`{nalp:.1e}` -> **FAIL**.","",
           "## Constraint windows","",
           "| class | primary lower [GeV] | upper [GeV] | status |","|---|---:|---:|---|"]
    for r in rows:
        lines.append(f"| {r['model_class']} | {r['primary_lower_GeV']:.6e} | {r['upper_GeV']:.6e} | {r['status']} |")
    lines += ["", "## Derived diagnostics", ""]
    for r in threshold_diag:
        lines.append(f"- n={r['n']}: at 300 TeV the head-on soft-photon threshold moves from {r['epsilon_standard_eV']:.6e} eV to {r['epsilon_modified_eV']:.6e} eV at the published transparency upper scale (uplift ×{r['uplift_ratio']:.3g}).")
    for r in timing:
        lines.append(f"- n={r['n']}: simple common-emission TOF inversion gives E* = [{r['inferred_E_star_GeV'][0]:.6e}, {r['inferred_E_star_GeV'][1]:.6e}] GeV for the observed LHAASO-to-Carpet delay window; this is conditional, not a hard bound.")
    lines += ["", "SST comparison is intentionally deferred to reveal."]
    (out/"report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return verdict
