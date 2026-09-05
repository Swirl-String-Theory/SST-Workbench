from __future__ import annotations
import argparse,json,sys,re,os
from pathlib import Path
from datetime import datetime
from run_matrix_batch import (
    resolve_shortcut, run_one_script, DEFAULT_SHORTCUT, preflight,
    rel_matrix_root
)
from knotplot_runtime import render_catalogue_loads
from catalog_recipe_support import load_recipe, recipe_hash

ROOT=Path(__file__).resolve().parent

def render_catalog_runtime(source:Path, workdir:Path, bead_command:str, basic_dirs:list[Path])->Path:
    text=source.read_text(encoding="utf-8",errors="replace")
    text=text.replace("__MATRIX_ROOT__", rel_matrix_root(ROOT,workdir))
    text=re.sub(r"(?mi)^\s*(?:refine\s+)?nbeads\s+\d+\s*$",
                lambda m: re.sub(r"(?i)^(?:refine\s+)?nbeads", bead_command.rsplit(" ",1)[0], m.group(0).strip()),
                text)
    text,resolved=render_catalogue_loads(text,basic_dirs)
    dd=ROOT/"catalog_runtime"/source.parent.name
    dd.mkdir(parents=True,exist_ok=True)
    out=dd/source.name
    header="% RUNTIME-RENDERED CATALOG SCRIPT\n"
    for cid,path in sorted(resolved.items()):
        header+=f"% RESOLVED_LOAD {cid} -> {path}\n"
    out.write_text(header+text,encoding="utf-8",newline="\n")
    return out

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--shortcut',type=Path,default=DEFAULT_SHORTCUT)
    ap.add_argument('--one')
    ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args(argv)

    try:
        recipe=load_recipe(ROOT/'catalog_recipe.json',False)
    except Exception as e:
        print(f'ERROR: {e}. Select/approve recipe before catalog run.',file=sys.stderr)
        return 2
    rh=recipe_hash(recipe)
    scripts=sorted((ROOT/'catalog').glob('*/build_*.kpc'))
    if a.one:
        scripts=[p for p in scripts if p.parent.name==a.one or p.name==a.one]
    if not scripts:
        print('ERROR: no catalog scripts; run run_prepare_catalog.cmd first',file=sys.stderr)
        return 2
    for p in scripts:
        t=p.read_text(errors='replace')
        m=re.search(r'^% RECIPE_SHA256 (\S+)',t,re.M)
        if not m or m.group(1)!=rh:
            print(f'ERROR: stale/unlocked catalog script: {p}',file=sys.stderr)
            return 3

    try:
        exe,wd=resolve_shortcut(a.shortcut.resolve())
        bead_command,basic_dirs=preflight(exe,wd,ROOT,{})
    except Exception as e:
        print(f'ERROR: {e}',file=sys.stderr)
        return 1

    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f'Catalog recipe: {recipe["recipe_id"]} SHA={rh} scripts={len(scripts)}')
    print(f'KnotPlot catalogue: {basic_dirs[0]}')
    for i,p in enumerate(scripts,1):
        cid=p.parent.name
        print(f'\n--- [{i}/{len(scripts)}] {cid} ---')
        try:
            runtime=render_catalog_runtime(p,wd,bead_command,basic_dirs)
        except Exception as e:
            print(f'ERROR rendering catalog entry {cid}: {e}',file=sys.stderr)
            return 4
        rc=run_one_script(
            exe=exe,workdir=wd,source_script=p,runtime_script=runtime,
            log_path=ROOT/'catalog_logs'/f'{cid}_console.log',
            audit_path=ROOT/'catalog_logs'/f'{cid}_audit.json',
            archive_dir=ROOT/'archive'/stamp/'catalog'/cid,
            dry_run=a.dry_run
        )
        if rc:
            return rc
    print('CATALOG RUN PASS')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
