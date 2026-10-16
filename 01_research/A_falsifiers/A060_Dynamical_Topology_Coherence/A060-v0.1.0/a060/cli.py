from __future__ import annotations
import argparse,json,csv,hashlib
from pathlib import Path
import numpy as np
from .core import overlap_series,rate_function,critical_candidate,two_mode_observables,spectral_pairing

def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def analyze(p,cfg):
 d=np.load(p,allow_pickle=False)
 t=np.asarray(d["t"],float)
 key="psi" if "psi" in d.files else "modes"
 x=np.asarray(d[key],complex)
 g=overlap_series(x); lam=rate_function(g,x.shape[1])
 c=critical_candidate(t,g,cfg["thresholds"]["return_candidate_abs"])
 modes=np.asarray(d["modes"],complex) if "modes" in d.files else x
 M=np.asarray(d["monodromy"],complex) if "monodromy" in d.files else None
 tm=two_mode_observables(modes)
 sp=spectral_pairing(M)
 gates={}
 gates["G0"]="PASS"
 gates["G1"]="PASS" if np.all(np.isfinite(t)) and np.all(np.isfinite(x)) and len(t)==len(x) else "FAIL"
 gates["G2"]="PASS" if c.get("present") else "FAIL"
 gates["G4"]="INDETERMINATE_NO_MONODROMY" if sp is None else ("PASS" if sp["conjugate_phase_residual_median"]<=cfg["thresholds"]["pairing_phase_tol_rad"] else "FAIL")
 gates["G5"]="INDETERMINATE_NO_TWO_MODE" if tm is None else ("PASS" if tm["R12"]>=cfg["thresholds"]["phase_lock_R_min"] and tm["chi_abs_mean"]>=cfg["thresholds"]["time_odd_abs_min"] else "FAIL")
 # ensemble gates are resolved by summarize()
 for gk in ["G3","G6","G7","G8","G9"]: gates[gk]="INDETERMINATE_REQUIRES_ENSEMBLE"
 return {"file":p.name,"sha256":sha(p),"n_time":len(t),"state_dim":x.shape[1],
         "critical":c,"two_mode":tm,"floquet":sp,"gates":gates,
         "_series":{"t":t.tolist(),"abs_G":np.abs(g).tolist(),"rate":lam.tolist(),"phase":np.angle(g).tolist()}}

def summarize(rows,cfg):
 # Conservative: do not infer metadata from filenames.
 # Optional sidecar <case>.meta.json provides anonymous condition/resolution/family.
 metas=[]
 for r in rows:
  p=Path(r["_path"]); mp=p.with_suffix(".meta.json")
  m=json.loads(mp.read_text()) if mp.exists() else {}
  metas.append((r,m))
 # G3 resolution convergence
 byfam={}
 for r,m in metas:
  if "resolution" in m and r["critical"].get("present"):
   byfam.setdefault(str(m.get("family","anon")),[]).append((int(m["resolution"]),r["critical"]["t"],r["critical"]["abs_G"]))
 g3="INDETERMINATE_REQUIRES_RESOLUTION_LADDER"
 for vals in byfam.values():
  vals=sorted(vals)
  if len(vals)>=3:
   rel=abs(vals[-1][1]-vals[-2][1])/max(abs(vals[-1][1]),1e-15)
   deep=vals[-1][2] <= max(vals[-2][2]*1.25, cfg["thresholds"]["return_candidate_abs"])
   g3="PASS" if rel<=cfg["thresholds"]["critical_time_rel_convergence_max"] and deep else "FAIL"
   break
 # condition metrics use minimum |G| as coherent-return strength = 1-min|G|
 cond={}
 for r,m in metas:
  c=m.get("condition")
  if c: cond.setdefault(c,[]).append(1-r["critical"].get("abs_G",1.0))
 def mean(c):
  v=cond.get(c,[]); return float(np.mean(v)) if v else None
 b,s,d=mean("baseline"),mean("static_disorder"),mean("dephasing")
 g6="INDETERMINATE_NO_STATIC_CONTROL" if b is None or s is None else ("PASS" if s>=cfg["thresholds"]["static_survival_fraction_min"]*max(b,1e-15) else "FAIL")
 g7="INDETERMINATE_NO_DEPHASING_CONTROL" if b is None or d is None else ("PASS" if d<= (1-cfg["thresholds"]["dephasing_suppression_fraction_min"])*max(b,1e-15) else "FAIL")
 null=mean("null")
 g8="INDETERMINATE_NO_NULL_CONTROL" if b is None or null is None else ("PASS" if null < .65*max(b,1e-15) else "FAIL")
 g9="INDETERMINATE_REQUIRES_MULTIPLE_FAMILIES" if len(byfam)<2 else "PASS"
 return {"G3":g3,"G6":g6,"G7":g7,"G8":g8,"G9":g9}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=["SELFTEST","BASIC","FULL"]); ap.add_argument("input",nargs="?"); ap.add_argument("--out",default="outputs/run")
 a=ap.parse_args()
 cfg=json.loads((Path(__file__).parents[1]/"configs/default.json").read_text())
 if a.mode=="SELFTEST":
  t=np.linspace(0,2*np.pi,129); x=np.c_[np.cos(t),1j*np.sin(t)]
  g=overlap_series(x)
  assert len(g)==len(t) and np.isfinite(rate_function(g,2)).all()
  print("A060 SELFTEST PASS"); return
 if not a.input: raise SystemExit("input path required")
 ip=Path(a.input); files=[ip] if ip.is_file() and ip.suffix==".npz" else sorted(ip.glob("*.npz"))
 if not files: raise SystemExit("no .npz cases found")
 out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
 rows=[]
 for p in files:
  r=analyze(p,cfg); r["_path"]=str(p); rows.append(r)
  public={k:v for k,v in r.items() if not k.startswith("_")}
  (out/(p.stem+".json")).write_text(json.dumps(public,indent=2))
  s=r["_series"]
  with open(out/(p.stem+"_timeseries.csv"),"w",newline="") as f:
   w=csv.writer(f); w.writerow(["t","abs_G","rate_function","phase"])
   w.writerows(zip(s["t"],s["abs_G"],s["rate"],s["phase"]))
 ens=summarize(rows,cfg)
 for r in rows:
  for k,v in ens.items(): r["gates"][k]=v
 terminal=[v for r in rows for v in r["gates"].values()]
 if any(v=="FAIL" for v in terminal): verdict="FAIL_TESTED_DOMAIN"
 elif any(str(v).startswith("INDETERMINATE") for v in terminal): verdict="INDETERMINATE_PREREQUISITES"
 else: verdict="SUPPORTED_TESTED_DOMAIN"
 summary={"schema":"A060-BLIND-SUMMARY-1.0","mode":a.mode,"verdict":verdict,
          "ensemble_gates":ens,"cases":[{k:v for k,v in r.items() if not k.startswith("_")} for r in rows]}
 (out/"blind_summary.json").write_text(json.dumps(summary,indent=2))
 print(json.dumps({"verdict":verdict,"output":str(out)},indent=2))
if __name__=="__main__": main()
