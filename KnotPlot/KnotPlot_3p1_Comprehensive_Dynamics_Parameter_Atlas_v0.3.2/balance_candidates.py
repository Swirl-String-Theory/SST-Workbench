from __future__ import annotations
from pathlib import Path
import json,re,math
import numpy as np

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"parameter_manifest.json").read_text(encoding="utf-8"))
R=json.loads((ROOT/"analysis/EXTENDED.json").read_text(encoding="utf-8"))

FAMILIES=("charge","hooke","power")
OBS=("length","rg")

def parse_value(cid,family):
    s=cid[len(family)+2:]
    s=s.replace("m","-").replace("p",".")
    return float(s)

def family_points(name):
    fr=R["families"][name]
    out=[]
    for c in fr.get("candidates",[]):
        v=parse_value(c["candidate"],name)
        m=c["metrics"]
        out.append((v,float(m["length"]),float(m["rg"])))
    return sorted(out)

def central_secant(points,x0,obs_index):
    lower=[p for p in points if p[0]<x0]
    upper=[p for p in points if p[0]>x0]
    if not lower or not upper:
        raise ValueError(f"Need values on both sides of baseline {x0}")
    lo=max(lower,key=lambda p:p[0])
    hi=min(upper,key=lambda p:p[0])
    return (hi[obs_index]-lo[obs_index])/(hi[0]-lo[0]),lo,hi

baseline={k:float(D["baseline"][k]) for k in FAMILIES}
pts={k:family_points(k) for k in FAMILIES}

# The default candidates should agree on the same baseline geometry observables.
base_obs={}
for fam in FAMILIES:
    q=min(pts[fam],key=lambda p:abs(p[0]-baseline[fam]))
    base_obs[fam]={"value":q[0],"length":q[1],"rg":q[2]}

L0=float(np.mean([v["length"] for v in base_obs.values()]))
RG0=float(np.mean([v["rg"] for v in base_obs.values()]))

slopes={}
for fam in FAMILIES:
    dL,loL,hiL=central_secant(pts[fam],baseline[fam],1)
    dR,loR,hiR=central_secant(pts[fam],baseline[fam],2)
    slopes[fam]={
        "d_length_d_parameter":float(dL),
        "d_rg_d_parameter":float(dR),
        "secant_low":float(loL[0]),
        "secant_high":float(hiL[0]),
    }

# Solve the two-observable local balance equations with delta_power = t:
#
# dL/dq * dq + dL/dh * dh + dL/dp * t = 0
# dRg/dq*dq + dRg/dh*dh + dRg/dp*t = 0
A=np.array([
    [slopes["charge"]["d_length_d_parameter"],slopes["hooke"]["d_length_d_parameter"]],
    [slopes["charge"]["d_rg_d_parameter"],slopes["hooke"]["d_rg_d_parameter"]],
],float)
b=-np.array([
    slopes["power"]["d_length_d_parameter"],
    slopes["power"]["d_rg_d_parameter"],
],float)
dq_per_t,dh_per_t=np.linalg.solve(A,b)

candidates=[]
for t in (0.25,0.5,0.75,1.0):
    q=baseline["charge"]+dq_per_t*t
    h=baseline["hooke"]+dh_per_t*t
    p=baseline["power"]+t
    candidates.append({
        "t":t,
        "charge":float(q),
        "hooke":float(h),
        "power":float(p),
        "linearized_predicted_delta_length":0.0,
        "linearized_predicted_delta_rg":0.0,
        "distance_from_baseline":{
            "delta_charge":float(q-baseline["charge"]),
            "delta_hooke":float(h-baseline["hooke"]),
            "delta_power":float(t),
        }
    })

report={
    "format":"KNOTPLOT-ATLAS-SURROGATE-BALANCE-0.3.3",
    "status":"CANDIDATE_ONLY_NOT_FORCE_PROOF",
    "interpretation":(
        "Derived from one-factor-at-a-time endpoint response slopes. "
        "It identifies parameter combinations predicted to cancel first-order "
        "changes in curve length and radius of gyration. It does not establish "
        "instantaneous mechanical force balance or nonlinear joint additivity."
    ),
    "baseline":{
        "charge":baseline["charge"],
        "hooke":baseline["hooke"],
        "power":baseline["power"],
        "length":L0,
        "rg":RG0,
    },
    "local_secant_slopes":slopes,
    "balance_ray":{
        "delta_charge_per_t":float(dq_per_t),
        "delta_hooke_per_t":float(dh_per_t),
        "delta_power_per_t":1.0,
        "equations":[
            "dL/dq*dq + dL/dhooke*dh + dL/dpower*dp = 0",
            "dRg/dq*dq + dRg/dhooke*dh + dRg/dpower*dp = 0",
        ]
    },
    "recommended_first_candidate":candidates[1],
    "candidate_ladder":candidates,
    "required_next_test":[
        "Run the joint parameter combinations prospectively; do not assume one-factor additivity.",
        "Measure instantaneous/stepwise expansion versus contraction response, not endpoint length alone.",
        "Perturb geometry around each joint candidate and test restoring sign on both sides.",
        "Require a stable zero crossing: expansion below/above must reverse sign across the candidate.",
    ],
}
(ROOT/"analysis/BALANCE_CANDIDATES.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

s=slopes
md=[
    "# Surrogate expansion/contraction balance candidates — Atlas v0.3.3",
    "",
    "> **Candidate only.** This is not yet a proof that instantaneous "
    "`F_expand + F_contract = 0`.",
    "",
    "Baseline:",
    f"- `charge = {baseline['charge']}`",
    f"- `hooke = {baseline['hooke']}`",
    f"- `power = {baseline['power']}`",
    f"- `L ≈ {L0:.9g}`",
    f"- `Rg ≈ {RG0:.9g}`",
    "",
    "Local one-factor response model:",
    "",
    f"\\[\\Delta L \\approx {s['charge']['d_length_d_parameter']:.6g}\\,\\Delta q"
    f" {s['hooke']['d_length_d_parameter']:+.6g}\\,\\Delta h"
    f" {s['power']['d_length_d_parameter']:+.6g}\\,\\Delta p\\]",
    "",
    f"\\[\\Delta R_g \\approx {s['charge']['d_rg_d_parameter']:.6g}\\,\\Delta q"
    f" {s['hooke']['d_rg_d_parameter']:+.6g}\\,\\Delta h"
    f" {s['power']['d_rg_d_parameter']:+.6g}\\,\\Delta p\\]",
    "",
    "Solving both first-order cancellation conditions gives:",
    "",
    f"\\[\\Delta q \\approx {dq_per_t:.6g}t,\\qquad "
    f"\\Delta h \\approx {dh_per_t:.6g}t,\\qquad \\Delta p=t.\\]",
    "",
    "## Recommended first joint candidate",
    "",
    f"\\[\\boxed{{q\\approx{candidates[1]['charge']:.4g},\\quad "
    f"hooke\\approx{candidates[1]['hooke']:.4g},\\quad "
    f"power\\approx{candidates[1]['power']:.4g}}}\\]",
    "",
    "This is the `t=0.5` point: deliberately close to the baseline so the "
    "local linear surrogate is least extrapolative.",
    "",
    "## Candidate ladder",
    "",
    "| t | charge | hooke | power |",
    "|---:|---:|---:|---:|",
]
for c in candidates:
    md.append(f"| {c['t']:.2f} | {c['charge']:.6g} | {c['hooke']:.6g} | {c['power']:.6g} |")

md += [
    "",
    "## What must falsify/confirm it next",
    "",
    "The next campaign must run these parameters **jointly**. A real restoring "
    "balance candidate requires a stable zero crossing of an expansion/contraction "
    "observable under perturbations around the candidate. Merely recovering the "
    "baseline endpoint length is insufficient.",
]
(ROOT/"analysis/BALANCE_CANDIDATES.md").write_text("\n".join(md)+"\n",encoding="utf-8")
print("WROTE analysis/BALANCE_CANDIDATES.json")
print("WROTE analysis/BALANCE_CANDIDATES.md")
print("Recommended:",json.dumps(candidates[1],indent=2))
