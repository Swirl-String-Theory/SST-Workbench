"""Strict, version-independent KnotPlot batch orchestrator for the 3.1 discovery matrix."""
from __future__ import annotations
import argparse, subprocess, sys, json, shutil, hashlib, os, re
from pathlib import Path
from datetime import datetime, timezone
from kpc_audit import script_issues, log_issue_details, expected_outputs
from knotplot_runtime import (
    run_knotplot, runtime_info, find_basic_dirs, find_catalogue_file,
    candidate_load_strategies, render_catalogue_loads, LoadStrategy,
)

MATRIX_DIR=Path(__file__).resolve().parent
KNOTPLOT_ROOT=MATRIX_DIR.parent
DEFAULT_SHORTCUT=KNOTPLOT_ROOT/"KnotPlot.lnk"

CORE_FAMILY=[
    "10_force_ablation_matrix.kpc","20_charge_sweep_ME.kpc","30_bend_sweep_MB.kpc",
    "40_power_sweep_ME.kpc","50_close_sweep_MEB.kpc","90_charge_anneal_MEB.kpc"
]
ALL_FAMILY=[
    "00_baseline_MEB_tight.kpc","10_force_ablation_matrix.kpc","20_charge_sweep_ME.kpc",
    "30_bend_sweep_MB.kpc","40_power_sweep_ME.kpc","50_close_sweep_MEB.kpc",
    "60_hooke_sweep_ME.kpc","70_maxdr_sweep_MEB.kpc","80_timeincr_sweep_MEB.kpc",
    "90_charge_anneal_MEB.kpc"
]

def resolve_shortcut(lnk:Path)->tuple[Path,Path]:
    if not lnk.is_file():
        raise FileNotFoundError(f"KnotPlot shortcut not found: {lnk}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(lnk).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    p=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True,check=False)
    lines=[x.strip() for x in (p.stdout or "").splitlines() if x.strip()]
    if not lines:
        raise RuntimeError(f"Could not resolve TargetPath from {lnk}")
    exe=Path(lines[0])
    wd=Path(lines[1]) if len(lines)>1 and lines[1] else KNOTPLOT_ROOT
    if not exe.is_file():
        raise FileNotFoundError(f"KnotPlot.exe from shortcut not found: {exe}")
    return exe,wd

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
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

def rel_matrix_root(matrix_dir:Path, workdir:Path)->str:
    try:
        return os.path.relpath(str(matrix_dir),str(workdir)).replace("\\","/")
    except ValueError:
        return str(matrix_dir.resolve()).replace("\\","/")

def fatal_probe_details(text:str):
    """Startup may print 'nothing loaded'; pass/fail is based on actual write plus hard operation failures."""
    all_details=log_issue_details(text)
    fatal_markers={"unknown command","this command is obsolete","can't open file","nothing to save","nothing to output"}
    return [x for x in all_details if x["marker"] in fatal_markers]

def print_issue_excerpt(details:list[dict], prefix="  "):
    if not details: return
    print("Exact KnotPlot log issues:",file=sys.stderr)
    for x in details[:20]:
        print(f"{prefix}L{x['line']}: [{x['marker']}] {x['text']}",file=sys.stderr)
    if len(details)>20:
        print(f"{prefix}... {len(details)-20} more",file=sys.stderr)

def _clean_probe_files(*paths:Path):
    for p in paths:
        try:
            p.unlink()
        except FileNotFoundError:
            pass

def select_load_strategy(exe:Path, shortcut_wd:Path, matrix_dir:Path):
    pf=matrix_dir/"preflight"
    if pf.exists(): shutil.rmtree(pf)
    pf.mkdir(parents=True,exist_ok=True)

    rc, info=runtime_info(exe,shortcut_wd,pf)
    (pf/"00_runtime_info.txt").write_text(info,encoding="utf-8",errors="replace")
    basics=find_basic_dirs(exe,shortcut_wd,info)
    if not basics:
        raise RuntimeError("KnotPlot `basic` catalogue directory not found.")
    seed=find_catalogue_file("3.1",basics)
    if seed is None:
        raise RuntimeError("KnotPlot catalogue seed 3.1 not found in: "+"; ".join(map(str,basics)))

    attempts=[]
    chosen=None
    for idx,strategy in enumerate(candidate_load_strategies(shortcut_wd,seed.parent),1):
        outk=pf/f"strategy_{idx}.k"
        outtxt=pf/f"strategy_{idx}.txt"
        _clean_probe_files(outk,outtxt)
        rel=rel_matrix_root(matrix_dir,strategy.process_cwd)
        # Output paths remain path-without-spaces and relative whenever possible.
        script=(
            "reset all\n"
            + strategy.prefix
            + strategy.load_line("3.1") + "\n"
            + f"save {rel}/preflight/{outk.name} float\n"
            + f"coords {rel}/preflight/{outtxt.name}\n"
            + "stop\n"
        )
        log=pf/f"strategy_{idx}_{strategy.name}.log"
        prc=run_knotplot(exe,strategy.process_cwd,script,log)
        text=log.read_text(encoding="utf-8",errors="replace")
        details=fatal_probe_details(text)
        ok=(
            prc==0 and outk.is_file() and outk.stat().st_size>0
            and outtxt.is_file() and outtxt.stat().st_size>0
            and not details
        )
        attempts.append({
            "name":strategy.name,"cwd":str(strategy.process_cwd),
            "prefix":strategy.prefix.strip(),"load":strategy.load_line("3.1"),
            "exit":prc,"k_bytes":outk.stat().st_size if outk.exists() else 0,
            "txt_bytes":outtxt.stat().st_size if outtxt.exists() else 0,
            "fatal_log_issues":details,"status":"PASS" if ok else "FAIL",
            "log":str(log)
        })
        print(f"[PREFLIGHT] load strategy {strategy.name}: {'PASS' if ok else 'FAIL'}")
        if not ok:
            print_issue_excerpt(details,prefix="    ")
        if ok and chosen is None:
            chosen=strategy
            break

    (pf/"LOAD_STRATEGIES.json").write_text(json.dumps({
        "basic_dirs":[str(x) for x in basics],
        "seed_3_1":str(seed),"attempts":attempts,
        "selected":chosen.name if chosen else None
    },indent=2)+"\n",encoding="utf-8")

    if chosen is None:
        raise RuntimeError(f"No KnotPlot catalogue-load strategy succeeded; inspect {pf/'LOAD_STRATEGIES.json'}")
    return chosen, basics, seed

def probe_bead_command(exe:Path, matrix_dir:Path, strategy:LoadStrategy):
    pf=matrix_dir/"preflight"; accepted=[]
    for idx,(tag,cmd) in enumerate([("nbeads","nbeads 300"),("refine_nbeads","refine nbeads 300")],1):
        outk=pf/f"beads_{tag}.k"; _clean_probe_files(outk)
        rel=rel_matrix_root(matrix_dir,strategy.process_cwd)
        script=(
            "reset all\n"+strategy.prefix+strategy.load_line("3.1")+"\n"
            +cmd+"\n"
            +f"save {rel}/preflight/{outk.name} float\nstop\n"
        )
        log=pf/f"beads_{idx}_{tag}.log"
        rc=run_knotplot(exe,strategy.process_cwd,script,log)
        text=log.read_text(encoding="utf-8",errors="replace")
        details=fatal_probe_details(text)
        ok=rc==0 and outk.is_file() and outk.stat().st_size>0 and not details
        print(f"[PREFLIGHT] bead syntax {cmd}: {'PASS' if ok else 'FAIL'}")
        if ok: accepted.append(cmd)
        else: print_issue_excerpt(details,prefix="    ")
    if not accepted:
        raise RuntimeError("Neither bead syntax succeeded; inspect preflight/beads_*.log")
    return "nbeads 300" if "nbeads 300" in accepted else accepted[0]

def render_runtime_script(source:Path,matrix_dir:Path,strategy:LoadStrategy,bead_command:str)->Path:
    text=source.read_text(encoding="utf-8",errors="replace")
    text=text.replace("__MATRIX_ROOT__",rel_matrix_root(matrix_dir,strategy.process_cwd))
    text=re.sub(r"(?mi)^\s*(?:refine\s+)?nbeads\s+300\s*$",bead_command,text)
    text,resolved=render_catalogue_loads(text,strategy)
    runtime_dir=matrix_dir/"runtime_scripts"; runtime_dir.mkdir(parents=True,exist_ok=True)
    out=runtime_dir/source.name
    header=f"% RUNTIME LOAD STRATEGY {strategy.name}\n% PROCESS_CWD {strategy.process_cwd}\n"
    for cid,line in sorted(resolved.items()): header+=f"% RESOLVED_LOAD {cid} -> {line}\n"
    out.write_text(header+text,encoding="utf-8",newline="\n")
    return out

def run_one_script(*,exe:Path,strategy:LoadStrategy,source_script:Path,runtime_script:Path,
                   log_path:Path,audit_path:Path,archive_dir:Path,dry_run:bool=False)->int:
    static=script_issues(source_script)
    if static:
        print(f"ERROR: static KPC audit failed for {source_script.name}: {static}",file=sys.stderr); return 2
    expected=expected_outputs(runtime_script,strategy.process_cwd)
    print(f"KnotPlot: {exe}\nCWD:      {strategy.process_cwd}\nLoad mode:{strategy.name}\nSource:   {source_script}\nRuntime:  {runtime_script}\nLog:      {log_path}\nExpected outputs: {len(expected)}\nMode:     -nographics -stdin")
    if dry_run: return 0
    archived=archive_old(expected,archive_dir/"outputs")
    if log_path.exists(): archive_old([log_path],archive_dir/"logs")
    started=datetime.now(timezone.utc)
    rc=run_knotplot(exe,strategy.process_cwd,runtime_script.read_text(encoding="utf-8",errors="replace"),log_path)
    ended=datetime.now(timezone.utc)
    text=log_path.read_text(encoding="utf-8",errors="replace")
    details=log_issue_details(text)
    # For real scripts, "nothing loaded" is a failure if present anywhere.
    missing=[str(p) for p in expected if not p.is_file() or p.stat().st_size==0]
    audit={
        "script":source_script.name,"source_script_sha256":sha256(source_script),
        "runtime_script_sha256":sha256(runtime_script),"process_exit":rc,
        "started_utc":started.isoformat(),"ended_utc":ended.isoformat(),
        "load_strategy":strategy.name,"process_cwd":str(strategy.process_cwd),
        "archived_old_outputs":archived,"expected_output_count":len(expected),
        "missing_outputs":missing,"log_issue_details":details,
        "log_issues":sorted({x["marker"] for x in details}),"status":"PASS"
    }
    if rc!=0 or details or missing: audit["status"]="FAIL"
    audit_path.parent.mkdir(parents=True,exist_ok=True)
    audit_path.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    if audit["status"]!="PASS":
        print("ERROR: strict audit failed:",json.dumps(audit,indent=2),file=sys.stderr)
        print_issue_excerpt(details); return rc or 3
    return 0

def main(argv=None):
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all",action="store_true"); g.add_argument("--core",action="store_true"); g.add_argument("--one")
    ap.add_argument("--matrix-dir",type=Path,default=MATRIX_DIR); ap.add_argument("--shortcut",type=Path,default=DEFAULT_SHORTCUT); ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args(argv); d=a.matrix_dir.resolve()
    names=ALL_FAMILY if a.all else CORE_FAMILY if a.core else [a.one]
    scripts=[(d/n).resolve() for n in names]
    title="FULL Multi-Dynamics Discovery Matrix" if a.all else "CORE Multi-Dynamics Discovery Matrix" if a.core else f"ONE script: {a.one}"
    try:
        exe,shortcut_wd=resolve_shortcut(a.shortcut.resolve())
        strategy,basics,seed=select_load_strategy(exe,shortcut_wd,d)
        bead_command=probe_bead_command(exe,d,strategy)
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr); return 1
    print("="*60); print(f"KnotPlot 3.1 {title}"); print("="*60)
    print(f"Shortcut : {a.shortcut}\nTarget   : {exe}\nShortcut CWD: {shortcut_wd}\nRuntime CWD : {strategy.process_cwd}\nLoad mode: {strategy.name}\n3.1 seed : {seed}\nOutput   : {d}\nScripts  : {len(scripts)}\nBeads    : {bead_command}"); print("="*60)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    for i,source in enumerate(scripts,1):
        runtime=render_runtime_script(source,d,strategy,bead_command)
        print(f"\n-------- [{i}/{len(scripts)}] {source.name} --------")
        rc=run_one_script(exe=exe,strategy=strategy,source_script=source,runtime_script=runtime,
            log_path=d/"logs"/f"{source.stem}_console.log",audit_path=d/"logs"/f"{source.stem}_audit.json",
            archive_dir=d/"archive"/stamp/source.stem,dry_run=a.dry_run)
        if rc: return rc
        print(f"OK+AUDITED: {source.name}")
    print("\nAll requested scripts finished and passed strict audit."); return 0

if __name__=="__main__": raise SystemExit(main())
