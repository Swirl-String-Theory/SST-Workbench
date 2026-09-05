"""Strict KnotPlot batch orchestrator for the 3.1 discovery matrix."""
from __future__ import annotations
import argparse, subprocess, sys, json, shutil, hashlib
from pathlib import Path
from datetime import datetime, timezone
from kpc_audit import script_issues, log_issues, expected_outputs

MATRIX_DIR=Path(__file__).resolve().parent
KNOTPLOT_ROOT=MATRIX_DIR.parent
DEFAULT_SHORTCUT=KNOTPLOT_ROOT/"KnotPlot.lnk"
CORE_FAMILY=["10_force_ablation_matrix.kpc","20_charge_sweep_ME.kpc","30_bend_sweep_MB.kpc","40_power_sweep_ME.kpc","50_close_sweep_MEB.kpc","90_charge_anneal_MEB.kpc"]
ALL_FAMILY=["00_baseline_MEB_tight.kpc","10_force_ablation_matrix.kpc","20_charge_sweep_ME.kpc","30_bend_sweep_MB.kpc","40_power_sweep_ME.kpc","50_close_sweep_MEB.kpc","60_hooke_sweep_ME.kpc","70_maxdr_sweep_MEB.kpc","80_timeincr_sweep_MEB.kpc","90_charge_anneal_MEB.kpc"]
NOTHING_LOADED_MARKERS=("nothing loaded","*** nothing loaded","nothing to save","nothing to output")

def resolve_shortcut(lnk:Path)->tuple[Path,Path]:
    if not lnk.is_file(): raise FileNotFoundError(f"KnotPlot shortcut not found: {lnk}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(lnk).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    p=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True,check=False)
    lines=[x.strip() for x in (p.stdout or "").splitlines() if x.strip()]
    if not lines: raise RuntimeError(f"Could not resolve TargetPath from {lnk}")
    exe=Path(lines[0]); wd=Path(lines[1]) if len(lines)>1 and lines[1] else KNOTPLOT_ROOT
    if not exe.is_file(): raise FileNotFoundError(f"KnotPlot.exe from shortcut not found: {exe}")
    return exe,wd

def log_indicates_nothing_loaded(t:str)->bool:
    lo=t.lower()
    if "knot loaded" in lo or "knot saved" in lo: return False
    return any(m in lo for m in NOTHING_LOADED_MARKERS)

def resolve_script(matrix_dir:Path,name:str)->Path:
    p=Path(name); return (p if p.is_absolute() else matrix_dir/p).resolve()

def knotplot_argv(exe:Path)->list[str]: return [str(exe),"-nog"]

def sha256(path:Path)->str:
    h=hashlib.sha256();
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def archive_old(paths:list[Path], archive_dir:Path)->int:
    n=0
    for p in paths:
        if not p.exists(): continue
        archive_dir.mkdir(parents=True,exist_ok=True)
        target=archive_dir/p.name
        if target.exists(): target=archive_dir/(p.stem+"_dup"+p.suffix)
        shutil.move(str(p),str(target)); n+=1
    return n

def run_one_script(*,exe:Path,workdir:Path,script:Path,log_path:Path,audit_path:Path,archive_dir:Path,dry_run:bool=False)->int:
    if not script.is_file(): raise FileNotFoundError(script)
    static=script_issues(script)
    if static:
        print(f"ERROR: static KPC audit failed for {script.name}: {static}",file=sys.stderr); return 2
    expected=expected_outputs(script,workdir)
    print(f"KnotPlot: {exe}\nCWD:      {workdir}\nScript:   {script}\nLog:      {log_path}\nExpected outputs: {len(expected)}\nMode:     non-graphics (-nog)")
    if dry_run: print("DRY-RUN:"," ".join(knotplot_argv(exe))); return 0
    archived=archive_old(expected,archive_dir/"outputs")
    if log_path.exists(): archive_old([log_path],archive_dir/"logs")
    log_path.parent.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc)
    with script.open('rb') as fin, log_path.open('wb') as fout:
        p=subprocess.run(knotplot_argv(exe),cwd=str(workdir),stdin=fin,stdout=fout,stderr=subprocess.STDOUT,check=False)
    ended=datetime.now(timezone.utc)
    text=log_path.read_text(encoding='utf-8',errors='replace')
    issues=log_issues(text)
    missing=[str(p) for p in expected if not p.is_file() or p.stat().st_size==0]
    audit={"script":script.name,"script_sha256":sha256(script),"process_exit":int(p.returncode),"started_utc":started.isoformat(),"ended_utc":ended.isoformat(),"archived_old_outputs":archived,"expected_output_count":len(expected),"missing_outputs":missing,"log_issues":issues,"status":"PASS"}
    if int(p.returncode)!=0 or issues or missing or log_indicates_nothing_loaded(text): audit['status']='FAIL'
    audit_path.parent.mkdir(parents=True,exist_ok=True); audit_path.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    if audit['status']!='PASS':
        print("ERROR: strict audit failed:",json.dumps(audit,indent=2),file=sys.stderr); return int(p.returncode) or 3
    return 0

def family_scripts(d:Path,names:list[str])->list[Path]: return [resolve_script(d,n) for n in names]

def main(argv=None)->int:
    ap=argparse.ArgumentParser(); g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--all',action='store_true'); g.add_argument('--core',action='store_true'); g.add_argument('--one')
    ap.add_argument('--matrix-dir',type=Path,default=MATRIX_DIR); ap.add_argument('--shortcut',type=Path,default=DEFAULT_SHORTCUT); ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args(argv); d=a.matrix_dir.resolve()
    if a.all: scripts=family_scripts(d,ALL_FAMILY); title='FULL Multi-Dynamics Discovery Matrix'
    elif a.core: scripts=family_scripts(d,CORE_FAMILY); title='CORE Multi-Dynamics Discovery Matrix'
    else: scripts=[resolve_script(d,a.one)]; title=f'ONE script: {scripts[0].name}'
    if a.dry_run and not a.shortcut.resolve().is_file():
        exe=Path("KnotPlot.exe"); wd=KNOTPLOT_ROOT
        print(f"DRY-RUN: shortcut not present in this environment; using placeholders {exe}, {wd}")
    else:
        try: exe,wd=resolve_shortcut(a.shortcut.resolve())
        except Exception as e: print(f"ERROR: {e}",file=sys.stderr); return 1
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    print('='*60); print(f'KnotPlot 3.1 {title}'); print('='*60); print(f'Shortcut : {a.shortcut}\nTarget   : {exe}\nStart in : {wd}\nOutput   : {d}\nScripts  : {len(scripts)}'); print('='*60)
    for i,s in enumerate(scripts,1):
        print(f'\n-------- [{i}/{len(scripts)}] {s.name} --------')
        rc=run_one_script(exe=exe,workdir=wd,script=s,log_path=d/'logs'/f'{s.stem}_console.log',audit_path=d/'logs'/f'{s.stem}_audit.json',archive_dir=d/'archive'/stamp/s.stem,dry_run=a.dry_run)
        if rc: return rc
        print(f'OK+AUDITED: {s.name}')
    print('\nAll requested scripts finished and passed strict audit.'); return 0
if __name__=='__main__': raise SystemExit(main())
