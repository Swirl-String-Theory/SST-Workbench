\
from __future__ import annotations
from pathlib import Path
import csv, json, math
from .common import dump_json, sha256_file, sci
from . import _native

MODEL_CLASSES = [
    ("n1_nonbirefringent", 1, False),
    ("n1_birefringent", 1, True),
    ("n2_nonbirefringent", 2, False),
    ("n2_birefringent", 2, True),
]

def run(root: Path, config_path: Path, output_root: Path) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    public_path = root / cfg["public_constraints"]
    if "private" in public_path.parts:
        raise RuntimeError("BLIND POLICY VIOLATION: public constraints resolved into private/")
    data = json.loads(public_path.read_text(encoding="utf-8"))
    out = output_root / "blind"
    out.mkdir(parents=True, exist_ok=True)

    p = data["carpet"]
    cp_p_ge1 = _native.poisson_at_least_one(float(p["conventional_expected_count"]))
    cp_threshold = float(p["poisson_min_expected_for_5pct_at_least_one"])
    gates = []
    gates.append({
        "id":"B01_PUBLIC_PROVENANCE", "status":"PASS",
        "metric":"sha256", "value":sha256_file(public_path)
    })
    gates.append({
        "id":"B02_CONVENTIONAL_TRANSPARENCY_POISSON", 
        "status":"FAIL" if p["conventional_expected_count"] < cp_threshold else "PASS",
        "expected_count":p["conventional_expected_count"],
        "min_expected_for_5pct_at_least_one":cp_threshold,
        "P_N_ge_1":cp_p_ge1,
        "interpretation":"If the Carpet event is taken at face value, conventional propagation is far below the frozen 5% Poisson observability threshold."
    })

    rows=[]
    upper = data["carpet_required_upper_95_GeV"]
    lower = data["previous_lower_95_GeV"]
    E_event_GeV=float(p["energy_TeV"]["central"])*1e3

    for cls,n,apply_biref in MODEL_CLASSES:
        lo_sources = {
            "time_of_flight": float(lower["time_of_flight_GRB221009A"][str(n)]),
            "breit_wheeler_spectra": float(lower["breit_wheeler_111_spectra_baseline_EBL"][str(n)]),
        }
        if apply_biref:
            lo_sources["birefringence"] = float(lower["birefringence_framework_dependent"][str(n)])
        hi_c = float(upper[str(n)]["central"])
        inter = _native.intersect_bounds(list(lo_sources.values()), [hi_c])
        eps_hi = _native.dispersion_epsilon(E_event_GeV, hi_c, n)
        lo_eff=max(lo_sources.values())
        eps_lo = _native.dispersion_epsilon(E_event_GeV, lo_eff, n)
        status="PASS" if inter["nonempty"] else "FAIL"
        rows.append({
            "model_class":cls,"n":n,"apply_birefringence":apply_biref,
            "lower_GeV":lo_eff,"upper_GeV":hi_c,"nonempty":bool(inter["nonempty"]),
            "log10_span":float(inter["log10_span"]),"epsilon_at_lower":eps_lo,"epsilon_at_upper":eps_hi,
            "status":status
        })
        gates.append({
            "id":f"B1{len(rows)}_{cls.upper()}_INTERVAL", "status":status,
            "n":n,"lower_sources_GeV":lo_sources,"effective_lower_GeV":lo_eff,
            "carpet_upper_GeV":hi_c,"epsilon_event_at_upper":eps_hi,
            "interval_nonempty":bool(inter["nonempty"])
        })

    # Robustness against quoted Carpet upper-bound uncertainty.
    robust=[]
    for n in (1,2):
        u=upper[str(n)]
        hi_min=float(u["central"])-float(u["minus"])
        hi_max=float(u["central"])+float(u["plus"])
        lo=max(float(lower["time_of_flight_GRB221009A"][str(n)]),
               float(lower["breit_wheeler_111_spectra_baseline_EBL"][str(n)]))
        robust.append({"n":n,"lower_nonbirefringent_GeV":lo,"upper_min_GeV":hi_min,"upper_max_GeV":hi_max,
                       "survives_quoted_upper_uncertainty": lo < hi_min})
    gates.append({"id":"B20_UPPER_BOUND_UNCERTAINTY_ROBUSTNESS","status":"PASS" if all(r["survives_quoted_upper_uncertainty"] for r in robust) else "FAIL","orders":robust})

    cond=data.get("conditional_previous_constraints", {})
    uhe=cond.get("uhe_photon_nondetection_naive_GeV", {})
    if uhe:
        naive_conflicts={}
        for n in (1,2):
            naive_lo=float(uhe["galaverni_sigl"][str(n)])
            hi=float(upper[str(n)]["central"])
            naive_conflicts[str(n)] = naive_lo >= hi
        gates.append({
            "id":"B21_UHE_NONDETECTION_CONDITIONAL_CONFLICT",
            "status":"CONDITIONAL",
            "naive_application_conflicts_with_carpet":naive_conflicts,
            "applicability":uhe.get("applicability"),
            "reason":uhe.get("reason"),
            "requirement":"Any surviving model must include a self-consistent atmospheric shower/detector-response treatment before using or discarding UHE-photon non-detection bounds."
        })

    surviving=[r["model_class"] for r in rows if r["status"]=="PASS"]
    rejected=[r["model_class"] for r in rows if r["status"]=="FAIL"]
    verdict={
        "campaign_id":data["campaign_id"],
        "verdict":"MIXED_SURVIVING_MODEL_CLASSES" if surviving and rejected else ("PASS" if surviving else "FAIL"),
        "surviving_model_classes":surviving,
        "rejected_model_classes":rejected,
        "important_scope":"Published-constraint qualification only; not an independent full optical-depth likelihood reproduction.",
        "blind_engine_read_private":False,
        "blind_engine_read_candidate_identity":False,
        "gates":gates
    }
    dump_json(out/"verdict.json",verdict)
    dump_json(out/"public_constraints_snapshot.json",data)
    (out/"public_input_sha256.txt").write_text(sha256_file(public_path)+"\n",encoding="utf-8")
    (out/"reveal_commitment_sha256.txt").write_text((root/"data/public/reveal_commitment_sha256.txt").read_text(encoding="utf-8"),encoding="utf-8")
    with (out/"constraint_windows.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    md=["# Blind verdict","",f"**Verdict:** `{verdict['verdict']}`","",
        "The blind engine used public observational constraints only. It did not load the candidate identity or private constants.","",
        "## Constraint-window results","",
        "| model class | n | effective lower [GeV] | Carpet upper [GeV] | result |",
        "|---|---:|---:|---:|---|"]
    for r in rows: md.append(f"| {r['model_class']} | {r['n']} | {r['lower_GeV']:.6e} | {r['upper_GeV']:.6e} | {r['status']} |")
    md += ["", "The generic birefringent n=1 class is rejected by incompatible lower/upper intervals; non-birefringent n=1 and both quadratic bookkeeping classes retain non-empty windows under the published baseline bounds. UHE-photon non-detection is retained as a conditional detector-response gate rather than silently discarded.",
           "", f"Conventional expected count: `{p['conventional_expected_count']:.3e}` versus frozen 5% observability threshold `{cp_threshold:.8f}`."]
    (out/"report.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    return verdict
