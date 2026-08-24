from __future__ import annotations
import argparse,re,sys
from pathlib import Path
from datetime import datetime
from run_matrix_batch import (
    resolve_shortcut, DEFAULT_SHORTCUT, select_load_strategy, probe_bead_command,
    run_one_script, rel_matrix_root
)
from knotplot_runtime import render_catalogue_loads
from catalog_recipe_support import load_recipe, recipe_hash

ROOT=Path(__file__).resolve().parent

def render_catalog_runtime(source:Path,strategy,bead_command:str)->Path:
    text=source.read_text(encoding="utf-8",errors="replace")
    text=text.replace("__MATRIX_ROOT__",rel_matrix_root(ROOT,strategy.process_cwd))
    if bead_command=="nbeads 300":
        text=re.sub(r"(?mi)^\s*refine\s+nbeads\s+(\d+)\s*$",r"nbeads \1",text)
    else:
        text=re.sub(r"(?mi)^\s*nbeads\s+(\d+)\s*$",r"refine nbeads \1",text)
    text,resolved=render_catalogue_loads(text,strategy)
    dd=ROOT/"catalog_runtime"/source.parent.name; dd.mkdir(parents=True,exist_ok=True)
    out=dd/source.name
    header=f"% RUNTIME LOAD STRATEGY {strategy.name}\n% PROCESS_CWD {strategy.process_cwd}\n"
    for cid,line in sorted(resolved.items()): header+=f"% RESOLVED_LOAD {cid} -> {line}\n"
    out.write_text(header+text,encoding="utf-8",newline="\n"); return out

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--shortcut",type=Path,default=DEFAULT_SHORTCUT); ap.add_argument("--one"); ap.add_argument("--dry-run",action="store_true"); a=ap.parse_args(argv)
    try: recipe=load_recipe(ROOT/"catalog_recipe.json",False)
    except Exception as e:
        print(f"ERROR: {e}. Select/approve recipe before catalog run.",file=sys.stderr); return 2
    rh=recipe_hash(recipe); scripts=sorted((ROOT/"catalog").glob("*/build_*.kpc"))
    if a.one: scripts=[p for p in scripts if p.parent.name==a.one or p.name==a.one]
    if not scripts:
        print("ERROR: no catalog scripts; run run_prepare_catalog.cmd first",file=sys.stderr); return 2
    for p in scripts:
        m=re.search(r"^% RECIPE_SHA256 (\S+)",p.read_text(errors="replace"),re.M)
        if not m or m.group(1)!=rh:
            print(f"ERROR: stale/unlocked catalog script: {p}",file=sys.stderr); return 3
    try:
        exe,shortcut_wd=resolve_shortcut(a.shortcut.resolve())
        strategy,basics,seed=select_load_strategy(exe,shortcut_wd,ROOT)
        bead_command=probe_bead_command(exe,ROOT,strategy)
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr); return 1
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Catalog recipe: {recipe['recipe_id']} SHA={rh} scripts={len(scripts)}")
    print(f"Load mode: {strategy.name}; runtime CWD: {strategy.process_cwd}")
    for i,p in enumerate(scripts,1):
        cid=p.parent.name; print(f"\n--- [{i}/{len(scripts)}] {cid} ---")
        runtime=render_catalog_runtime(p,strategy,bead_command)
        rc=run_one_script(exe=exe,strategy=strategy,source_script=p,runtime_script=runtime,
            log_path=ROOT/"catalog_logs"/f"{cid}_console.log",audit_path=ROOT/"catalog_logs"/f"{cid}_audit.json",
            archive_dir=ROOT/"archive"/stamp/"catalog"/cid,dry_run=a.dry_run)
        if rc: return rc
    print("CATALOG RUN PASS"); return 0

if __name__=="__main__": raise SystemExit(main())
