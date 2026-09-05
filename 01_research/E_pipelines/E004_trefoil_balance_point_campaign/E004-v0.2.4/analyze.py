from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"));A=D["analysis"]
ITS=[200000]+D["continuation"]["checkpoints"];LATE=D["continuation"]["late_window"]

def xyz(p):
    a=[]
    for l in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        v=[]
        for x in l.replace(","," ").split():
            try:v.append(float(x))
            except:pass
        if len(v)>=3:a.append(v[:3])
    return np.asarray(a,float)
def length(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def rg(a):
    b=a-a.mean(0);return float(np.sqrt(np.mean(np.sum(b*b,axis=1))))
def slope(x,y,scale=1):
    x=np.asarray(x,float);y=np.asarray(y,float)
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])*scale
def qhp(t):
    r=D["qhp_ray"];return {"t":float(t),"charge":r["q0"]+r["q1"]*t,"hooke":r["h0"]+r["h1"]*t,"power":r["p0"]+t}

def preflight_complete():
    required=[0,200000]+[int(x) for x in D["continuation"]["checkpoints"]]
    missing=[]
    rows=[]
    for s in D["panel"]:
        rr=f"XQHP__{s['id']}"
        have=[]
        miss=[]
        for it in required:
            p=ROOT/"out"/f"{rr}_i{it:06d}.txt"
            if p.is_file() and p.stat().st_size>0:have.append(it)
            else:miss.append(it);missing.append(str(p))
        rows.append({"id":s["id"],"t":s["t"],"latest_present":max(have) if have else None,"missing":miss})
    if missing:
        payload={"format":"TREFOIL-V0242-ANALYSIS-PREFLIGHT-1.0","overall":"INCOMPLETE",
                 "missing_file_count":len(missing),"rows":rows}
        (ROOT/"analysis").mkdir(exist_ok=True)
        (ROOT/"analysis/ANALYSIS_BLOCKED_INCOMPLETE.json").write_text(
            json.dumps(payload,indent=2)+"\n",encoding="utf-8")
        print("ANALYSIS BLOCKED: continuation outputs are incomplete.")
        for x in rows:
            if x["missing"]:
                print(f"  {x['id']} t={x['t']}: latest={x['latest_present']} missing={x['missing']}")
        print("")
        print("Do not rerun the cold-start stages.")
        print("Run: run_resume_continuation_then_analyze.cmd")
        raise SystemExit(6)

preflight_complete()
rows=[]
for s in D["panel"]:
    rr=f"XQHP__{s['id']}";a0=xyz(ROOT/"out"/f"{rr}_i000000.txt");L0,R0=length(a0),rg(a0)
    r={"id":s["id"],"t":s["t"],"role":s["role"]}
    for it in ITS:
        a=xyz(ROOT/"out"/f"{rr}_i{it:06d}.txt");dl=length(a)/L0-1;dr=rg(a)/R0-1
        r[f"dL_{it}"]=dl;r[f"dRg_{it}"]=dr;r[f"E_{it}"]=.5*(dl+dr)
    ev=[r[f"E_{i}"] for i in LATE]
    r["late_E_median"]=float(np.median(ev));r["late_E_drift_per_1000"]=slope(LATE,ev,1000);r["late_E_span"]=float(max(ev)-min(ev))
    r["fixed_E_gate"]=abs(r["late_E_median"])<=A["fixed_E_abs_median_tolerance"] and abs(r["late_E_drift_per_1000"])<=A["fixed_E_drift_abs_per_1000_tolerance"] and r["late_E_span"]<=A["fixed_E_span_tolerance"]
    rows.append(r)
rows.sort(key=lambda x:x["t"])

def crosses(it):
    key=f"E_{it}";out=[]
    for a,b in zip(rows[:-1],rows[1:]):
        y1,y2=a[key],b[key]
        if y1==0:f=0.;tt=a["t"]
        elif y1*y2<0:f=-y1/(y2-y1);tt=a["t"]+f*(b["t"]-a["t"])
        else:continue
        dl=a[f"dL_{it}"]+f*(b[f"dL_{it}"]-a[f"dL_{it}"])
        dr=a[f"dRg_{it}"]+f*(b[f"dRg_{it}"]-a[f"dRg_{it}"])
        out.append({"low":a["id"],"high":b["id"],"t":float(tt),"fraction":float(f),"qhp":qhp(tt),"dL_at_zero":float(dl),"dRg_at_zero":float(dr)})
    return out

prior=D["source"]["historical_zero_t_200k"];track=[]
for it in ITS:
    cs=crosses(it);ch=min(cs,key=lambda x:abs(x["t"]-prior)) if cs else None
    if ch:prior=ch["t"]
    track.append({"iteration":it,"crossings":cs,"chosen":ch,
                  "E_tmin":rows[0][f"E_{it}"],"E_tmax":rows[-1][f"E_{it}"]})

late=[x for x in track if x["iteration"] in LATE]
chosen=[x for x in late if x["chosen"]]
cross_all=len(chosen)==len(LATE)
left=False;direction=None
if not cross_all:
    for x in late:
        if x["chosen"] is None:
            if x["E_tmin"]<0 and x["E_tmax"]<0:left=True;direction="above_tmax"
            elif x["E_tmin"]>0 and x["E_tmax"]>0:left=True;direction="below_tmin"

if chosen:
    xi=[x["iteration"] for x in chosen];tz=[x["chosen"]["t"] for x in chosen]
    zv=slope(xi,tz,10000) if len(tz)>=2 else None
    spread=float(max(tz[-3:])-min(tz[-3:])) if len(tz)>=3 else None
    dls=[x["chosen"]["dL_at_zero"] for x in chosen];drs=[x["chosen"]["dRg_at_zero"] for x in chosen]
    dlslope=slope(xi,dls,10000) if len(dls)>=2 else None;drslope=slope(xi,drs,10000) if len(drs)>=2 else None
    last_t=tz[-1];boundary=min(last_t-rows[0]["t"],rows[-1]["t"]-last_t)<=A["boundary_margin_t"]
else:
    zv=spread=dlslope=drslope=last_t=None;boundary=False
settled=bool(cross_all and zv is not None and abs(zv)<=A["zero_track_slope_abs_t_per_10000_tolerance"] and spread is not None and spread<=A["zero_track_last3_spread_tolerance"])
geom=bool(settled and dlslope is not None and drslope is not None and abs(dlslope)<=A["individual_observable_slope_abs_per_10000_tolerance"] and abs(drslope)<=A["individual_observable_slope_abs_per_10000_tolerance"])

overlap=json.loads((ROOT/"analysis/OVERLAP_CALIBRATION_200K.json").read_text(encoding="utf-8"))
if overlap["overall"]!="PASS":overall="OVERLAP_CALIBRATION_FAILED"
elif left:overall="ZERO_LEFT_EXTENDED_PANEL"
elif boundary:overall="ZERO_AT_EXTENDED_PANEL_BOUNDARY"
elif geom:overall="TRUE_GEOMETRIC_FIXED_POINT_CANDIDATE"
elif settled:overall="SETTLED_COMPENSATING_BALANCE_ZERO"
else:overall="MOVING_LATE_BALANCE_ZERO"

rep={"format":"TREFOIL-V024-EXTENDED-PANEL-REPORT-1.0","horizon":400000,"overall":overall,
     "overlap_calibration":overlap,"zero_track":track,"late_zero_velocity_t_per_10000":zv,
     "late_zero_last3_spread":spread,"dL_at_zero_slope_per_10000":dlslope,
     "dRg_at_zero_slope_per_10000":drslope,"zero_track_settled":settled,
     "individual_observables_stationary":geom,"zero_left_panel":left,"escape_direction":direction,
     "zero_at_boundary":boundary,"fixed_E_gate_settings":[r["id"] for r in rows if r["fixed_E_gate"]],
     "planning":D["planning"],"gates":A,"rows":rows}
(ROOT/"analysis/REPORT.json").write_text(json.dumps(rep,indent=2)+"\n",encoding="utf-8")

md=["# Trefoil Balance Point Campaign v0.2.4","",f"**Overall:** `{overall}`","",
    "## Overlap calibration","",f"- status: **{overlap['overall']}**",
    f"- historical zero @200k: `{overlap['historical_zero_200k']}`",
    f"- regenerated zero @200k: `{overlap['new_zero_200k']}`",
    f"- absolute difference: `{overlap['zero_abs_difference']}`","",
    "## Extended zero track","",
    "| iteration | t* | ΔL/L0 at zero | ΔRg/Rg0 at zero |","|---:|---:|---:|---:|"]
for x in track:
    if x["chosen"]:
        c=x["chosen"];md.append(f"| {x['iteration']} | {c['t']:.10f} | {c['dL_at_zero']:.8g} | {c['dRg_at_zero']:.8g} |")
    else:md.append(f"| {x['iteration']} | — | — | — |")
md += ["","## Late gates","",
       f"- zero velocity /10k: `{zv}`",
       f"- last-three spread: `{spread}`",
       f"- ΔL-at-zero slope /10k: `{dlslope}`",
       f"- ΔRg-at-zero slope /10k: `{drslope}`",
       f"- settled: `{settled}`",
       f"- individual observables stationary: `{geom}`",
       f"- boundary: `{boundary}`",
       f"- left extended panel: `{left}` ({direction})","",
       "The overlap gate is a prerequisite: failure there invalidates use of the cold-start extended panel."]
(ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
print("HORIZON 400000")
print("OVERALL",overall)
print("overlap",overlap["overall"],"delta zero",overlap["zero_abs_difference"])
print("zero velocity/10k",zv)
print("last3 spread",spread)
print("dL zero slope/10k",dlslope)
print("dRg zero slope/10k",drslope)
