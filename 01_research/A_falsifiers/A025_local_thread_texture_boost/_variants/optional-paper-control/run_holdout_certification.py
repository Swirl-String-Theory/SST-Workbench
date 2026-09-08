from __future__ import annotations
import argparse,json,shutil,subprocess,sys,time
from pathlib import Path
from sst_thread_falsifier.io import discover_dataset


def main():
    ap=argparse.ArgumentParser(description="v0.3.0 dedicated prior-release holdout certification")
    ap.add_argument("--config",default="config/holdout.json"); ap.add_argument("--dataset",default=r"..\..\KnotPlot\knots\final")
    ap.add_argument("--out",default=None); ap.add_argument("--force-python",action="store_true"); ap.add_argument("--skip-build",action="store_true"); ap.add_argument("--require-all",action="store_true")
    a=ap.parse_args(); cfg=json.loads(Path(a.config).read_text(encoding="utf-8")); patterns=[str(x).lower() for x in cfg.get("holdout_patterns",["link_0.3.1","torus_6.21"])]
    files=discover_dataset(a.dataset,0); selected=[]; missing=[]
    for pat in patterns:
        hits=[p for p in files if pat in str(p).lower()]
        if hits: selected.extend(hits)
        else: missing.append(pat)
    # Stable dedupe
    seen=set(); selected=[p for p in selected if not (str(p.resolve()) in seen or seen.add(str(p.resolve())))]
    out=Path(a.out or f"outputs_holdout_{time.strftime('%Y%m%d_%H%M%S')}"); out.mkdir(parents=True,exist_ok=True)
    selection={"patterns":patterns,"selected":[str(p) for p in selected],"missing":missing,"dataset":str(Path(a.dataset).resolve())}
    (out/"holdout_selection.json").write_text(json.dumps(selection,indent=2),encoding="utf-8")
    require=bool(a.require_all or cfg.get("holdout_require_all",False))
    if missing and require:
        print(json.dumps({"status":"FAIL_MISSING_HOLDOUTS",**selection},indent=2)); raise SystemExit(3)
    if not selected:
        print(json.dumps({"status":"NOT_RUN_NO_HOLDOUT_MATCH",**selection},indent=2)); raise SystemExit(4)
    inp=out/"holdout_inputs"; inp.mkdir(exist_ok=True)
    for i,p in enumerate(selected): shutil.copy2(p,inp/f"{i:03d}_{p.name}")
    run_cfg=dict(cfg); run_cfg.pop("holdout_patterns",None); run_cfg.pop("holdout_require_all",None); cp=out/"holdout_run_config.json"; cp.write_text(json.dumps(run_cfg,indent=2),encoding="utf-8")
    cmd=[sys.executable,str(Path(__file__).with_name("run_extended.py")),"--config",str(cp),"--dataset",str(inp),"--out",str(out/"certification")]
    if a.force_python: cmd.append("--force-python")
    if a.skip_build: cmd.append("--skip-build")
    print("[SST-THREAD-HOLDOUT]", " ".join(cmd)); raise SystemExit(subprocess.call(cmd))
if __name__=="__main__": main()
