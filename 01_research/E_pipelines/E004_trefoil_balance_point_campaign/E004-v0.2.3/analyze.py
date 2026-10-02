from pathlib import Path
import json,csv,numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text());A=D["analysis"]
ALL=[0,30000,40000,50000,60000,70000,80000,90000,100000,120000,140000,160000,180000,200000]
LATE=D["continuation"]["late_window"]

def xyz(p):
    a=[]
    for line in p.read_text(errors="ignore").splitlines():
        v=[]
        for x in line.replace(","," ").split():
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
def qhp(t):return {"t":float(t),"charge":15+22.27046411874018*t,"hooke":1+0.3563655804274017*t,"power":5+t}

rows=[]
for s in D["settings"]:
    vals={}
    for it in ALL:
        p=ROOT/"out"/f"K31__{s['id']}_i{it:05d}.txt"
        if not p.is_file():raise SystemExit(f"missing {p}")
        a=xyz(p);vals[it]=(length(a),rg(a))
    L0,R0=vals[0]
    dL={i:vals[i][0]/L0-1 for i in ALL};dR={i:vals[i][1]/R0-1 for i in ALL};E={i:.5*(dL[i]+dR[i]) for i in ALL}
    ev=[E[i] for i in LATE]
    med=float(np.median(ev));dr=slope(LATE,ev,1000);span=float(max(ev)-min(ev))
    direct=abs(med)<=A["fixed_E_abs_median_tolerance"] and abs(dr)<=A["fixed_E_drift_abs_per_1000_tolerance"] and span<=A["fixed_E_span_tolerance"]
    r={"setting":s["id"],"t":s["t"],"charge":s["charge"],"hooke":s["hooke"],"power":s["power"],
       "late_E_median":med,"late_E_drift_per_1000":dr,"late_E_span":span,"direct_fixed_E_gate":bool(direct)}
    for i in ALL:r[f"E_i{i:05d}"]=E[i];r[f"dL_i{i:05d}"]=dL[i];r[f"dRg_i{i:05d}"]=dR[i]
    rows.append(r)
rows.sort(key=lambda x:x["t"])
tmin,tmax=rows[0]["t"],rows[-1]["t"]

def crosses(it):
    key=f"E_i{it:05d}";out=[]
    for a,b in zip(rows[:-1],rows[1:]):
        y1,y2=a[key],b[key]
        if y1==0:f=0.;tt=a["t"]
        elif y1*y2<0:f=-y1/(y2-y1);tt=a["t"]+f*(b["t"]-a["t"])
        else:continue
        # interpolate individual observables at the same zero
        dl=a[f"dL_i{it:05d}"]+f*(b[f"dL_i{it:05d}"]-a[f"dL_i{it:05d}"])
        dr=a[f"dRg_i{it:05d}"]+f*(b[f"dRg_i{it:05d}"]-a[f"dRg_i{it:05d}"])
        out.append({"low":a["setting"],"high":b["setting"],"fraction":float(f),"t":float(tt),"qhp":qhp(tt),
                    "dL_at_zero":float(dl),"dRg_at_zero":float(dr)})
    return out

# follow the nearest continuous zero, starting from observed 100k
source_t=D["source"]["observed_zero_t_100k"]
track=[]
prior=source_t
for it in D["continuation"]["zero_track_history"]+D["continuation"]["zero_track_new"]:
    cs=crosses(it)
    ch=min(cs,key=lambda x:abs(x["t"]-prior)) if cs else None
    if ch:prior=ch["t"]
    # diagnose sign if crossing absent
    signs={"E_at_tmin":rows[0][f"E_i{it:05d}"],"E_at_tmax":rows[-1][f"E_i{it:05d}"]}
    track.append({"iteration":it,"chosen":ch,"crossings":cs,"boundary_signs":signs})

late=[x for x in track if x["iteration"] in LATE]
late_ch=[x for x in late if x["chosen"]]
cross_all=len(late_ch)==len(LATE)
zero_left=False
escape_direction=None
if not cross_all:
    # If crossing existed earlier and disappears with same-signed panel endpoints,
    # classify panel escape rather than runtime/scientific failure.
    for x in late:
        if x["chosen"] is None:
            lo=x["boundary_signs"]["E_at_tmin"];hi=x["boundary_signs"]["E_at_tmax"]
            if lo<0 and hi<0:zero_left=True;escape_direction="above_tmax"
            elif lo>0 and hi>0:zero_left=True;escape_direction="below_tmin"

if late_ch:
    xi=[x["iteration"] for x in late_ch];yt=[x["chosen"]["t"] for x in late_ch]
    zero_vel=slope(xi,yt,10000) if len(yt)>=2 else None
    spread=float(max(yt[-3:])-min(yt[-3:])) if len(yt)>=3 else None
    last_t=yt[-1]
    boundary=min(last_t-tmin,tmax-last_t)<=A["boundary_margin_t"]
    dls=[x["chosen"]["dL_at_zero"] for x in late_ch];drs=[x["chosen"]["dRg_at_zero"] for x in late_ch]
    dl_slope=slope(xi,dls,10000) if len(dls)>=2 else None
    dr_slope=slope(xi,drs,10000) if len(drs)>=2 else None
else:
    zero_vel=spread=last_t=dl_slope=dr_slope=None;boundary=False

settled=bool(cross_all and zero_vel is not None and abs(zero_vel)<=A["zero_track_slope_abs_t_per_10000_tolerance"] and spread is not None and spread<=A["zero_track_last3_spread_tolerance"])
individual_stationary=bool(settled and dl_slope is not None and dr_slope is not None and
                           abs(dl_slope)<=A["individual_observable_slope_abs_per_10000_tolerance"] and
                           abs(dr_slope)<=A["individual_observable_slope_abs_per_10000_tolerance"])
fixed_pass=[r["setting"] for r in rows if r["direct_fixed_E_gate"]]

if zero_left:
    overall="ZERO_LEFT_FROZEN_PANEL"
elif boundary:
    overall="ZERO_AT_FROZEN_RANGE_BOUNDARY"
elif settled and individual_stationary:
    overall="TRUE_GEOMETRIC_FIXED_POINT_CANDIDATE"
elif settled:
    overall="SETTLED_COMPENSATING_BALANCE_ZERO"
else:
    overall="MOVING_LATE_BALANCE_ZERO"

rep={"format":"TREFOIL-V023-ASYMPTOTIC-REPORT-1.0","horizon":200000,"overall":overall,
     "zero_track":track,"late_crossing_all":cross_all,"zero_left_panel":zero_left,"escape_direction":escape_direction,
     "late_zero_velocity_t_per_10000":zero_vel,"late_zero_last3_spread":spread,"zero_at_boundary":boundary,
     "dL_at_zero_slope_per_10000":dl_slope,"dRg_at_zero_slope_per_10000":dr_slope,
     "zero_track_settled":settled,"individual_observables_stationary":individual_stationary,
     "fixed_E_gate_settings":fixed_pass,"gates":A,"planning_forecast":D["planning_forecast"],"rows":rows}
(ROOT/"analysis/REPORT.json").write_text(json.dumps(rep,indent=2)+"\n",encoding="utf-8")

md=["# Trefoil Balance Point Campaign v0.2.3","",f"**Overall:** `{overall}`","",
    "## Zero track","",
    "| iteration | t* | ΔL/L0 at zero | ΔRg/Rg0 at zero |","|---:|---:|---:|---:|"]
for x in track:
    if x["chosen"]:
        c=x["chosen"];md.append(f"| {x['iteration']} | {c['t']:.10f} | {c['dL_at_zero']:.8g} | {c['dRg_at_zero']:.8g} |")
    else:md.append(f"| {x['iteration']} | — | — | — |")
md += ["","## Late gates","",
       f"- zero velocity / 10k: `{zero_vel}`",
       f"- last-3 zero spread: `{spread}`",
       f"- boundary: `{boundary}`",
       f"- left panel: `{zero_left}` ({escape_direction})",
       f"- ΔL-at-zero slope /10k: `{dl_slope}`",
       f"- ΔRg-at-zero slope /10k: `{dr_slope}`",
       f"- fixed-E passes: `{fixed_pass}`","",
       "## Classification semantics","",
       "- `TRUE_GEOMETRIC_FIXED_POINT_CANDIDATE`: zero settles and both separate geometric observables are stationary.",
       "- `SETTLED_COMPENSATING_BALANCE_ZERO`: zero settles but at least one separate observable keeps drifting.",
       "- `MOVING_LATE_BALANCE_ZERO`: zero remains inside the panel but keeps migrating.",
       "- `ZERO_AT_FROZEN_RANGE_BOUNDARY`: crossing is within the frozen boundary margin.",
       "- `ZERO_LEFT_FROZEN_PANEL`: the crossing has moved outside the existing q/h/p panel."]
(ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
print("HORIZON 200000")
print("OVERALL",overall)
print("zero velocity/10k",zero_vel)
print("last3 spread",spread)
print("dL zero slope/10k",dl_slope)
print("dRg zero slope/10k",dr_slope)
