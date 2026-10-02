"""Strict, version-independent KnotPlot batch orchestrator for the 3.1 discovery matrix."""
from __future__ import annotations
import argparse, subprocess, sys, json, shutil, hashlib, os, re
from pathlib import Path
from datetime import datetime, timezone
from kpc_audit import script_issues, log_issue_details, expected_outputs
from knotplot_runtime import (
    run_knotplot, runtime_info, find_basic_dirs, find_catalogue_file,
    render_catalogue_loads, kp_path,
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
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def archive_old(paths:list[Path], archive_dir:Path)->int:
    n=0
    for p in paths:
        if not p.exists():
            continue
        archive_dir.mkdir(parents=True,exist_ok=True)
        target=archive_dir/p.name
        if target.exists():
            target=archive_dir/(p.stem+"_dup"+p.suffix)
        shutil.move(str(p),str(target))
        n+=1
    return n

def rel_matrix_root(matrix_dir:Path, workdir:Path)->str:
    try:
        rel=os.path.relpath(str(matrix_dir),str(workdir))
    except ValueError:
        return kp_path(matrix_dir)
    return rel.replace("\\","/")

def print_issue_excerpt(details:list[dict], prefix="  "):
    if not details:
        return
    print("Exact KnotPlot log issues:",file=sys.stderr)
    for x in details[:20]:
        print(f"{prefix}L{x['line']}: [{x['marker']}] {x['text']}",file=sys.stderr)
    if len(details)>20:
        print(f"{prefix}... {len(details)-20} more issue lines",file=sys.stderr)

def resolve_runtime(exe:Path, shortcut_wd:Path, matrix_dir:Path):
    pf=matrix_dir/"preflight"
    pf.mkdir(parents=True,exist_ok=True)

    rc, info = runtime_info(exe, shortcut_wd, pf)
    (pf/"00_runtime_info.txt").write_text(info,encoding="utf-8",errors="replace")
    basic_dirs=find_basic_dirs(exe, shortcut_wd, info)
    if not basic_dirs:
        raise RuntimeError(
            "Could not locate KnotPlot's `basic` catalogue directory. "
            f"Inspect {pf/'00_runtime_info.log'} and {pf/'00_runtime_info.txt'}"
        )
    seed=find_catalogue_file("3.1",basic_dirs)
    if seed is None:
        raise RuntimeError(
            "Located KnotPlot basic directory/directories but not catalogue seed `3.1`: "
            + "; ".join(str(x) for x in basic_dirs)
        )

    return {
        "shortcut_workdir":shortcut_wd,
        "basic_dirs":basic_dirs,
        "seed_3_1":seed,
        "runtime_info_exit":rc,
    }

def preflight(exe:Path, workdir:Path, matrix_dir:Path, runtime)->str:
    pf=matrix_dir/"preflight"
    if pf.exists():
        # Preserve runtime-info logs created by resolve_runtime only by recreating after cleanup.
        shutil.rmtree(pf)
    pf.mkdir(parents=True,exist_ok=True)

    rc, info = runtime_info(exe, workdir, pf)
    (pf/"00_runtime_info.txt").write_text(info,encoding="utf-8",errors="replace")
    basic_dirs=find_basic_dirs(exe, workdir, info)
    seed=find_catalogue_file("3.1",basic_dirs)
    if seed is None:
        raise RuntimeError("KnotPlot catalogue seed `3.1` could not be resolved during preflight.")

    rel=rel_matrix_root(matrix_dir,workdir)

    # A. Explicit seed-file load/write probe.
    load_script=(
        "reset all\n"
        f"load {kp_path(seed)}\n"
        f"save {rel}/preflight/load_probe.k float\n"
        f"coords {rel}/preflight/load_probe.txt\n"
        "stop\n"
    )
    load_log=pf/"01_load_write_probe.log"
    rc=run_knotplot(exe,workdir,load_script,load_log)
    txt=load_log.read_text(encoding="utf-8",errors="replace")
    details=log_issue_details(txt)
    outputs=[pf/"load_probe.k",pf/"load_probe.txt"]
    missing=[p for p in outputs if not p.is_file() or p.stat().st_size==0]
    if rc!=0 or details or missing:
        print("ERROR: KnotPlot explicit catalogue load/write preflight failed.",file=sys.stderr)
        print(f"  CWD: {workdir}",file=sys.stderr)
        print(f"  Seed 3.1: {seed}",file=sys.stderr)
        print(f"  Missing/empty: {[str(x) for x in missing]}",file=sys.stderr)
        print_issue_excerpt(details)
        print(f"  Full log: {load_log}",file=sys.stderr)
        raise RuntimeError("explicit seed load/write preflight failed")

    # B. Probe both bead syntaxes on the explicit seed.
    accepted=[]
    for tag,cmd in [("nbeads","nbeads 300"),("refine_nbeads","refine nbeads 300")]:
        outk=pf/f"{tag}_probe.k"
        script=(
            "reset all\n"
            f"load {kp_path(seed)}\n"
            f"{cmd}\n"
            f"save {rel}/preflight/{tag}_probe.k float\n"
            "stop\n"
        )
        log=pf/f"02_{tag}_probe.log"
        rc=run_knotplot(exe,workdir,script,log)
        text=log.read_text(encoding="utf-8",errors="replace")
        bad=log_issue_details(text)
        ok=(rc==0 and outk.is_file() and outk.stat().st_size>0 and not bad)
        if ok:
            accepted.append(cmd)
        else:
            print(f"[PREFLIGHT] rejected bead syntax: {cmd}",file=sys.stderr)
            print_issue_excerpt(bad,prefix="    ")

    if not accepted:
        raise RuntimeError(f"Neither bead syntax was accepted; inspect {pf}")
    chosen="nbeads 300" if "nbeads 300" in accepted else accepted[0]

    report={
        "status":"PASS",
        "load_write":"PASS",
        "seed_3_1":str(seed),
        "basic_dirs":[str(x) for x in basic_dirs],
        "accepted_bead_commands":accepted,
        "selected_bead_command":chosen,
        "matrix_root_relative_to_cwd":rel,
    }
    (pf/"PREFLIGHT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"[PREFLIGHT] KnotPlot basic catalogue: {basic_dirs[0]}")
    print(f"[PREFLIGHT] explicit 3.1 seed: {seed}")
    print("[PREFLIGHT] explicit load/write PASS")
    print(f"[PREFLIGHT] selected bead command: {chosen}")
    return chosen, basic_dirs

def render_runtime_script(source:Path, matrix_dir:Path, workdir:Path, bead_command:str, basic_dirs:list[Path])->Path:
    text=source.read_text(encoding="utf-8",errors="replace")
    text=text.replace("__MATRIX_ROOT__", rel_matrix_root(matrix_dir,workdir))
    text=re.sub(r"(?mi)^\s*(?:refine\s+)?nbeads\s+300\s*$", bead_command, text)
    text,resolved=render_catalogue_loads(text,basic_dirs)
    runtime_dir=matrix_dir/"runtime_scripts"
    runtime_dir.mkdir(parents=True,exist_ok=True)
    out=runtime_dir/source.name
    header="% RUNTIME-RENDERED; source remains catalogue-ID based\n"
    for cid,path in sorted(resolved.items()):
        header+=f"% RESOLVED_LOAD {cid} -> {path}\n"
    out.write_text(header+text,encoding="utf-8",newline="\n")
    return out

def run_one_script(*,exe:Path,workdir:Path,source_script:Path,runtime_script:Path,
                   log_path:Path,audit_path:Path,archive_dir:Path,dry_run:bool=False)->int:
    static=script_issues(source_script)
    if static:
        print(f"ERROR: static KPC audit failed for {source_script.name}: {static}",file=sys.stderr)
        return 2
    expected=expected_outputs(runtime_script,workdir)
    print(
        f"KnotPlot: {exe}\n"
        f"CWD:      {workdir}\n"
        f"Source:   {source_script}\n"
        f"Runtime:  {runtime_script}\n"
        f"Log:      {log_path}\n"
        f"Expected outputs: {len(expected)}\n"
        f"Mode:     -nographics -stdin"
    )
    if dry_run:
        for p in expected[:4]:
            print("  expect:",p)
        if len(expected)>4:
            print(f"  ... plus {len(expected)-4} more")
        return 0

    archived=archive_old(expected,archive_dir/"outputs")
    if log_path.exists():
        archive_old([log_path],archive_dir/"logs")

    started=datetime.now(timezone.utc)
    with runtime_script.open("rb") as fin:
        script_text=fin.read().decode("utf-8",errors="replace")
    rc=run_knotplot(exe,workdir,script_text,log_path)
    ended=datetime.now(timezone.utc)
    text=log_path.read_text(encoding="utf-8",errors="replace")
    details=log_issue_details(text)
    issues=sorted({x["marker"] for x in details})
    missing=[str(p) for p in expected if not p.is_file() or p.stat().st_size==0]

    audit={
        "script":source_script.name,
        "source_script_sha256":sha256(source_script),
        "runtime_script_sha256":sha256(runtime_script),
        "process_exit":rc,
        "started_utc":started.isoformat(),
        "ended_utc":ended.isoformat(),
        "archived_old_outputs":archived,
        "expected_output_count":len(expected),
        "expected_output_root":str((MATRIX_DIR/"out").resolve()),
        "missing_outputs":missing,
        "log_issues":issues,
        "log_issue_details":details,
        "status":"PASS",
    }
    if rc!=0 or details or missing:
        audit["status"]="FAIL"
    audit_path.parent.mkdir(parents=True,exist_ok=True)
    audit_path.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    if audit["status"]!="PASS":
        print("ERROR: strict audit failed:",json.dumps(audit,indent=2),file=sys.stderr)
        print_issue_excerpt(details)
        return rc or 3
    return 0

def family_scripts(d:Path,names:list[str])->list[Path]:
    return [(d/n).resolve() for n in names]

def main(argv=None)->int:
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all",action="store_true")
    g.add_argument("--core",action="store_true")
    g.add_argument("--one")
    ap.add_argument("--matrix-dir",type=Path,default=MATRIX_DIR)
    ap.add_argument("--shortcut",type=Path,default=DEFAULT_SHORTCUT)
    ap.add_argument("--dry-run",action="store_true")
    a=ap.parse_args(argv)

    d=a.matrix_dir.resolve()
    if a.all:
        scripts=family_scripts(d,ALL_FAMILY); title="FULL Multi-Dynamics Discovery Matrix"
    elif a.core:
        scripts=family_scripts(d,CORE_FAMILY); title="CORE Multi-Dynamics Discovery Matrix"
    else:
        scripts=[(d/a.one).resolve()]; title=f"ONE script: {scripts[0].name}"

    try:
        exe,wd=resolve_shortcut(a.shortcut.resolve())
        if a.dry_run:
            rc,info=runtime_info(exe,wd,d/"preflight")
            basic_dirs=find_basic_dirs(exe,wd,info)
            if not basic_dirs:
                raise RuntimeError("KnotPlot basic catalogue directory not found.")
            bead_command="nbeads 300"
        else:
            bead_command,basic_dirs=preflight(exe,wd,d,{})
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr)
        return 1

    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    print("="*60)
    print(f"KnotPlot 3.1 {title}")
    print("="*60)
    print(f"Shortcut : {a.shortcut}\nTarget   : {exe}\nStart in : {wd}\nOutput   : {d}\nScripts  : {len(scripts)}")
    print(f"Beads    : {bead_command}")
    print(f"Catalogue: {basic_dirs[0]}")
    print("="*60)

    for i,source in enumerate(scripts,1):
        try:
            runtime=render_runtime_script(source,d,wd,bead_command,basic_dirs)
        except Exception as e:
            print(f"ERROR rendering {source.name}: {e}",file=sys.stderr)
            return 2
        print(f"\n-------- [{i}/{len(scripts)}] {source.name} --------")
        rc=run_one_script(
            exe=exe,workdir=wd,source_script=source,runtime_script=runtime,
            log_path=d/"logs"/f"{source.stem}_console.log",
            audit_path=d/"logs"/f"{source.stem}_audit.json",
            archive_dir=d/"archive"/stamp/source.stem,
            dry_run=a.dry_run
        )
        if rc:
            return rc
        print(f"OK+AUDITED: {source.name}")

    print("\nAll requested scripts finished and passed strict audit.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
