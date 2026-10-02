from pathlib import Path
import json,csv,math
import numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text());A=D["analysis"]
ET=float(A["late_zero_abs_E_tolerance"]);DT=float(A["late_drift_abs_per_1000_tolerance"]);ST=float(A["late_span_tolerance"])
ZT=float(A["zero_track_slope_abs_t_per_10000_tolerance"]);ZS=float(A["zero_track_last3_spread_tolerance"])

def xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try:vals.append(float(t))
            except:pass
        if len(vals)>=3:rows.append(vals[:3])
    return np.asarray(rows,float)
def length(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def rg(a):
    c=a-a.mean(0,keepdims=True);return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))
def slope(xs,ys,scale=1):
    x=np.asarray(xs,float);y=np.asarray(ys,float)
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])*scale
def qhp(t):return {"t":float(t),"charge":15+22.27046411874018*t,"hooke":1+0.3563655804274017*t,"power":5+t}

CPS=[0,15000,20000,25000,30000,40000,50000,60000,70000,80000,90000,100000]
LATE=D["continuation"]["late_window"];TRACK=D["continuation"]["zero_track"];VEL=D["continuation"]["zero_velocity_window"]

rows=[]
for s in D["settings"]:
    vals={}
    for it in CPS:
        p=ROOT/"out"/f"K31__{s['id']}_i{it:05d}.txt"
        if not p.is_file():raise SystemExit(f"ERROR missing {p}")
        a=xyz(p);vals[it]=(length(a),rg(a))
    L0,R0=vals[0]
    dL={it:vals[it][0]/L0-1 for it in CPS}
    dR={it:vals[it][1]/R0-1 for it in CPS}
    E={it:0.5*(dL[it]+dR[it]) for it in CPS}
    lv=[E[i] for i in LATE]
    med=float(np.median(lv));dr=slope(LATE,lv,1000);span=float(max(lv)-min(lv))
    direct=abs(med)<=ET and abs(dr)<=DT and span<=ST
    r={"setting":s["id"],"t":s["t"],"charge":s["charge"],"hooke":s["hooke"],"power":s["power"],
       "late_E_median":med,"late_drift_per_1000":dr,"late_span":span,"direct_equilibrium":bool(direct),
       "late_dL_median":float(np.median([dL[i] for i in LATE])),
       "late_dRg_median":float(np.median([dR[i] for i in LATE]))}
    for it in CPS:
        r[f"E_i{it:05d}"]=E[it];r[f"dL_i{it:05d}"]=dL[it];r[f"dRg_i{it:05d}"]=dR[it]
    rows.append(r)
rows.sort(key=lambda x:x["t"])

def crossings(key):
    out=[]
    for a,b in zip(rows[:-1],rows[1:]):
        y1,y2=a[key],b[key]
        if y1==0:
            t=a["t"];f=0.0
        elif y1*y2<0:
            f=-y1/(y2-y1);t=a["t"]+f*(b["t"]-a["t"])
        else:continue
        out.append({"low":a["setting"],"high":b["setting"],"fraction":float(f),"t":float(t),
                    "qhp":qhp(t)})
    return out

track=[]
prior_t=D["source"]["observed_60k_zero_t"]
for it in TRACK:
    xs=crossings(f"E_i{it:05d}")
    chosen=min(xs,key=lambda x:abs(x["t"]-prior_t)) if xs else None
    if chosen: prior_t=chosen["t"]
    track.append({"iteration":it,"crossings":xs,"chosen":chosen})
late_track=[x for x in track if x["iteration"] in VEL]
late_t=[x["chosen"]["t"] for x in late_track if x["chosen"]]
late_i=[x["iteration"] for x in late_track if x["chosen"]]
all_late_crossings=len(late_t)==len(VEL)
zero_velocity=slope(late_i,late_t,10000) if len(late_t)>=2 else None
last3=late_t[-3:]
spread=float(max(last3)-min(last3)) if len(last3)>=2 else None
increments=[]
for a,b in zip(late_track[:-1],late_track[1:]):
    if a["chosen"] and b["chosen"]:
        increments.append({"from":a["iteration"],"to":b["iteration"],
                           "delta_t":b["chosen"]["t"]-a["chosen"]["t"]})
settled=bool(all_late_crossings and zero_velocity is not None and abs(zero_velocity)<=ZT and spread is not None and spread<=ZS)
tmin=min(r["t"] for r in rows);tmax=max(r["t"] for r in rows)
lastzero=late_t[-1] if late_t else None
boundary=False if lastzero is None else min(lastzero-tmin,tmax-lastzero)<float(A["boundary_margin_t"])
direct=[r for r in rows if r["direct_equilibrium"]]
best_fixed=min(rows,key=lambda r:abs(r["late_E_median"])/ET+abs(r["late_drift_per_1000"])/DT+r["late_span"]/ST)

if not all_late_crossings:
    overall="ZERO_NOT_TRACKABLE_THROUGH_100K"
elif boundary:
    overall="ZERO_AT_FROZEN_RANGE_BOUNDARY"
elif settled and direct:
    overall="SETTLED_LATE_EQUILIBRIUM_FOUND"
elif settled:
    overall="SETTLED_MOVING_FRAME_ZERO_NO_FIXED_SETTING_GATE"
else:
    overall="MOVING_LATE_BALANCE_ZERO"

report={
    "format":"TREFOIL-QHP-ASYMPTOTIC-ZERO-REPORT-2.2",
    "horizon":100000,
    "overall":overall,
    "best_fixed_setting":best_fixed,
    "direct_equilibrium_settings":[r["setting"] for r in direct],
    "zero_track":track,
    "late_zero_velocity_t_per_10000":zero_velocity,
    "late_zero_last3_spread":spread,
    "late_zero_increments":increments,
    "zero_track_settled":settled,
    "zero_at_boundary":boundary,
    "gates":{
        "abs_zero_velocity_t_per_10000_max":ZT,
        "last3_spread_max":ZS,
        "fixed_setting_abs_E_max":ET,
        "fixed_setting_abs_drift_per_1000_max":DT,
        "fixed_setting_span_max":ST
    },
    "rows":rows,
    "guardrails":[
        "E is a geometric balance surrogate, not direct force proof.",
        "A fixed-setting E gate alone is insufficient if the interpolated zero continues migrating.",
        "dL and dRg are reported separately to expose cancellation inside E."
    ]
}
(ROOT/"analysis").mkdir(exist_ok=True)
(ROOT/"analysis/REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

md=["# Trefoil Balance Point Campaign v0.2.2","",
    "**Horizon:** 100000",f"**Overall:** `{overall}`","",
    "## Asymptotic zero-track gate","",
    f"- late zero velocity per 10k: `{zero_velocity}` (limit `{ZT}`)",
    f"- last-three zero spread: `{spread}` (limit `{ZS}`)",
    f"- settled: **{settled}**",
    f"- boundary warning: **{boundary}**","",
    "| iteration | t-zero | q | h | p |","|---:|---:|---:|---:|---:|"]
for x in track:
    if x["chosen"]:
        q=x["chosen"]["qhp"];md.append(f"| {x['iteration']} | {q['t']:.10g} | {q['charge']:.10g} | {q['hooke']:.10g} | {q['power']:.10g} |")
    else:md.append(f"| {x['iteration']} | — | — | — | — |")
md += ["","## Late zero increments","",
       "| from | to | Δt |","|---:|---:|---:|"]
for x in increments:md.append(f"| {x['from']} | {x['to']} | {x['delta_t']:.10g} |")
md += ["","## Fixed-setting late-window gates","",
       "| setting | t | late E median | drift/1000 | span | median ΔL/L0 | median ΔRg/Rg0 | direct gate |",
       "|---|---:|---:|---:|---:|---:|---:|---|"]
for r in rows:
    md.append(f"| {r['setting']} | {r['t']:.3f} | {r['late_E_median']:.8g} | {r['late_drift_per_1000']:.8g} | {r['late_span']:.8g} | {r['late_dL_median']:.8g} | {r['late_dRg_median']:.8g} | {r['direct_equilibrium']} |")
md += ["","## Interpretation","",
       "A zero that continues to migrate is classified as `MOVING_LATE_BALANCE_ZERO`, even when one or more fixed QHP settings satisfy the old E-based gate.",
       "The new primary asymptotic test is therefore the zero-track velocity plus last-three spread.",
       "ΔL/L0 and ΔRg/Rg0 are reported separately so an E≈0 cancellation cannot be mistaken for both geometric observables being individually stationary."]
(ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")

keys=["setting","t","charge","hooke","power","late_E_median","late_drift_per_1000","late_span","late_dL_median","late_dRg_median","direct_equilibrium"]
with (ROOT/"analysis/runs.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
    for r in rows:w.writerow({k:r[k] for k in keys})
print("HORIZON: 100000")
print("OVERALL:",overall)
print("ZERO VELOCITY t/10k:",zero_velocity)
print("LAST3 SPREAD:",spread)
print("SETTLED:",settled)
print("BEST FIXED:",best_fixed["setting"],best_fixed["t"])
