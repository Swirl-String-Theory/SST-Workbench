from pathlib import Path
import argparse,subprocess,os,re,json,time
ROOT=Path(__file__).resolve().parent
SHORTCUT=ROOT.parent/"KnotPlot.lnk"
REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete")
HARD=("can't open file","cannot open file","failed to open","freeglut error")

def resolve():
    sc=Path(os.environ.get("KNOTPLOT_LNK","").strip() or SHORTCUT)
    if not sc.is_file():raise FileNotFoundError(sc)
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    cp=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    a=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
    if not a:raise RuntimeError("Could not resolve KnotPlot shortcut")
    return Path(a[0]),Path(a[1]) if len(a)>1 and a[1] else ROOT.parent

def render(src,cwd,stage):
    rel=os.path.relpath(ROOT,cwd).replace("\\","/")
    d=ROOT/"runtime_kpc"/stage
    d.mkdir(parents=True,exist_ok=True)
    p=d/src.name
    p.write_text(src.read_text(encoding="utf-8").replace("__BUNDLE_ROOT__",rel),encoding="utf-8",newline="\n")
    return p

def outputs(rt,cwd):
    ans=[]
    for line in rt.read_text(encoding="utf-8",errors="replace").splitlines():
        m=re.match(r"^\s*(?:save|coords)\s+(\S+)",line,re.I)
        if m:
            ans.append((cwd/Path(m.group(1))).resolve())
    return ans

def fmt(sec):
    if sec is None:return "--:--:--"
    sec=max(0,int(sec))
    h,r=divmod(sec,3600);m,s=divmod(r,60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def iteration_of(path):
    m=re.search(r"_i(\d+)\.(?:k|txt)$",path.name)
    return int(m.group(1)) if m else -1

def checkpoint_iterations(expected):
    return sorted({iteration_of(p) for p in expected if iteration_of(p)>=0})

def complete_iteration(expected,it):
    files=[p for p in expected if iteration_of(p)==it]
    return bool(files) and all(p.is_file() and p.stat().st_size>0 for p in files)

def completed_checkpoints(expected,checkpoints):
    return [it for it in checkpoints if complete_iteration(expected,it)]

def complete(expected):
    cps=checkpoint_iterations(expected)
    return bool(cps) and complete_iteration(expected,cps[-1])

def stage_start_iteration(rt,checkpoints):
    """Infer the logical stage start for progress percentages."""
    txt=rt.read_text(encoding="utf-8",errors="replace")
    m=re.search(r"(?mi)^\s*load\s+\S*_i(\d+)\.k\s*$",txt)
    if m:
        return int(m.group(1))
    # Cold starts load the frozen i0 coordinate source and explicitly save i0.
    if checkpoints and checkpoints[0]==0:
        return 0
    return checkpoints[0] if checkpoints else 0

def latest_log_line(path,max_bytes=8192):
    """Best-effort tail of KnotPlot log while process is running."""
    try:
        if not path.is_file() or path.stat().st_size==0:
            return None
        size=path.stat().st_size
        with path.open("rb") as f:
            f.seek(max(0,size-max_bytes))
            data=f.read()
        txt=data.decode("utf-8",errors="replace")
        lines=[x.strip() for x in txt.splitlines() if x.strip()]
        if not lines:return None
        # Keep terminal output bounded.
        line=lines[-1]
        return line if len(line)<=180 else line[-180:]
    except OSError:
        return None

def pct(value,start,end):
    if end<=start:return 100.0
    return max(0.0,min(100.0,100.0*(value-start)/(end-start)))

def one(exe,cwd,src,stage,i,n,avg_setting,progress_every):
    rt=render(src,cwd,stage)
    exp=outputs(rt,cwd)
    cps=checkpoint_iterations(exp)
    if not cps:
        raise RuntimeError(f"No checkpoint outputs declared by {src}")

    start_it=stage_start_iteration(rt,cps)
    final_it=cps[-1]
    stage_cps=[x for x in cps if x>=start_it]

    for p in exp:
        p.parent.mkdir(parents=True,exist_ok=True)

    if complete(exp):
        print(
            f"[{i:02d}/{n:02d}] SKIP {src.stem} stage={stage} "
            f"final={final_it} already complete",
            flush=True
        )
        return {"run_id":src.stem,"status":"SKIP","elapsed_seconds":0.0}

    # A partial interrupted setting is restarted. Completed settings are skipped above.
    for p in exp:
        try:
            if p.is_file():p.unlink()
        except OSError:
            pass

    log=ROOT/"logs"/f"{stage}__{src.stem}.log"
    log.parent.mkdir(parents=True,exist_ok=True)

    print(
        f"[{i:02d}/{n:02d}] START {src.stem} stage={stage} "
        f"range={start_it}->{final_it} checkpoints={len(stage_cps)} "
        f"heartbeat={progress_every:g}s",
        flush=True
    )
    if len(stage_cps)<=16:
        print(f"[{i:02d}/{n:02d}] PLAN  {src.stem} checkpoints={stage_cps}",flush=True)

    start_wall=time.monotonic()
    last_heartbeat=start_wall
    last_checkpoint_wall=start_wall
    latest_checkpoint=start_it
    observed_cps=[]
    segment_samples=[]  # (delta_iterations, delta_seconds)
    last_kp_line=None

    with rt.open("rb") as fin,log.open("wb") as fout:
        proc=subprocess.Popen(
            [str(exe),"-nog"],
            cwd=str(cwd),
            stdin=fin,
            stdout=fout,
            stderr=subprocess.STDOUT
        )

        while proc.poll() is None:
            now=time.monotonic()

            # Check every poll for newly completed checkpoint outputs, independent
            # of heartbeat cadence. This gives immediate progress when `ago` returns.
            done=completed_checkpoints(exp,stage_cps)
            new_done=[x for x in done if x not in observed_cps]
            for cp_it in new_done:
                cp_wall=time.monotonic()
                if observed_cps:
                    prev=observed_cps[-1]
                    dt=cp_wall-last_checkpoint_wall
                    di=cp_it-prev
                    if di>0 and dt>0:
                        segment_samples.append((di,dt))
                elif cp_it>start_it:
                    dt=cp_wall-start_wall
                    di=cp_it-start_it
                    if di>0 and dt>0:
                        segment_samples.append((di,dt))

                observed_cps.append(cp_it)
                latest_checkpoint=cp_it
                last_checkpoint_wall=cp_wall

                idx=stage_cps.index(cp_it)+1
                stage_pct=pct(cp_it,start_it,final_it)
                print(
                    f"[{i:02d}/{n:02d}] CHECKPOINT {src.stem} "
                    f"{idx}/{len(stage_cps)} i={cp_it} "
                    f"stage={stage_pct:6.2f}% elapsed={fmt(cp_wall-start_wall)}",
                    flush=True
                )

            # Heartbeat with inferred current segment.
            if now-last_heartbeat>=progress_every:
                done=completed_checkpoints(exp,stage_cps)
                if done:
                    latest_checkpoint=max(done)
                else:
                    latest_checkpoint=start_it

                next_candidates=[x for x in stage_cps if x>latest_checkpoint]
                next_it=next_candidates[0] if next_candidates else final_it
                seg_elapsed=now-last_checkpoint_wall
                stage_pct=pct(latest_checkpoint,start_it,final_it)

                # Estimate seconds/iteration using completed segments in this setting.
                sec_per_it=None
                if segment_samples:
                    total_i=sum(di for di,dt in segment_samples)
                    total_s=sum(dt for di,dt in segment_samples)
                    if total_i>0:
                        sec_per_it=total_s/total_i

                next_eta=None
                setting_eta=None
                seg_est_pct=None
                if sec_per_it and next_it>latest_checkpoint:
                    expected_seg=(next_it-latest_checkpoint)*sec_per_it
                    next_eta=max(0.0,expected_seg-seg_elapsed)
                    seg_est_pct=max(0.0,min(99.9,100.0*seg_elapsed/max(expected_seg,1e-9)))
                    remaining_after_next=max(0,final_it-next_it)
                    setting_eta=next_eta+remaining_after_next*sec_per_it
                elif avg_setting:
                    # Early fallback before the first segment timing is learned.
                    setting_eta=max(0.0,avg_setting-(now-start_wall))

                idx_done=sum(1 for x in stage_cps if x<=latest_checkpoint)
                msg=(
                    f"[{i:02d}/{n:02d}] HEARTBEAT {src.stem} "
                    f"elapsed={fmt(now-start_wall)} "
                    f"cp={idx_done}/{len(stage_cps)} latest={latest_checkpoint} next={next_it} "
                    f"stage={stage_pct:6.2f}% "
                    f"segmentElapsed={fmt(seg_elapsed)}"
                )
                if seg_est_pct is not None:
                    msg+=f" segmentEst={seg_est_pct:5.1f}% nextETA={fmt(next_eta)}"
                if setting_eta is not None:
                    msg+=f" settingETA={fmt(setting_eta)}"
                if avg_setting:
                    campaign_eta=setting_eta if setting_eta is not None else 0.0
                    campaign_eta += max(0,n-i)*avg_setting
                    msg+=f" campaignETA={fmt(campaign_eta)}"
                print(msg,flush=True)

                # Surface KnotPlot's latest changing log line without flooding.
                kp=latest_log_line(log)
                if kp and kp!=last_kp_line:
                    print(f"[{i:02d}/{n:02d}] KNOTPLOT {src.stem}: {kp}",flush=True)
                    last_kp_line=kp

                last_heartbeat=now

            time.sleep(min(2.0,max(0.5,progress_every/8.0)))

        rc=proc.returncode

    elapsed=time.monotonic()-start_wall
    txt=log.read_text(encoding="utf-8",errors="replace")
    rej=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in HARD)]
    missing=[str(p) for p in exp if not p.is_file() or p.stat().st_size==0]
    status="PASS" if rc==0 and not rej and not hard and not missing else "FAIL"
    eta=(avg_setting if avg_setting else elapsed)*(n-i)

    print(
        f"[{i:02d}/{n:02d}] DONE {src.stem} {status} "
        f"elapsed={fmt(elapsed)} remainingETA={fmt(eta)}",
        flush=True
    )
    if status=="FAIL":
        for x in (hard+rej)[:5]:
            print("   ERROR:",x,flush=True)
        for x in missing[:5]:
            print("   MISSING:",x,flush=True)

    audit={
        "run_id":src.stem,
        "stage":stage,
        "status":status,
        "elapsed_seconds":elapsed,
        "process_exit":rc,
        "rejections":rej[:50],
        "hard_errors":hard[:50],
        "missing_outputs":missing,
        "progress":{
            "start_iteration":start_it,
            "final_iteration":final_it,
            "checkpoints":stage_cps,
            "observed_checkpoints":observed_cps,
            "segment_samples":[{"delta_iterations":di,"seconds":dt} for di,dt in segment_samples],
            "heartbeat_seconds":progress_every
        }
    }
    (ROOT/"logs"/f"{stage}__{src.stem}_audit.json").write_text(
        json.dumps(audit,indent=2)+"\n",
        encoding="utf-8"
    )
    return audit

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",choices=["cold_overlap","cold_extension","continuation"],required=True)
    ap.add_argument("--progress-every",type=float,default=15.0)
    a=ap.parse_args()

    if a.progress_every<2:
        raise SystemExit("--progress-every must be >= 2 seconds")

    folder={
        "cold_overlap":"kpc_cold_overlap",
        "cold_extension":"kpc_cold_extension",
        "continuation":"kpc_continuation"
    }[a.stage]

    exe,cwd=resolve()
    scripts=sorted((ROOT/folder).glob("*.kpc"))
    times=[]
    bad=0

    print("Executable :",exe)
    print("CWD        :",cwd)
    print("Stage      :",a.stage)
    print("Scripts    :",len(scripts))
    print("Heartbeat  :",f"{a.progress_every:g}s")

    for i,p in enumerate(scripts,1):
        avg_setting=sum(times)/len(times) if times else None
        r=one(exe,cwd,p,a.stage,i,len(scripts),avg_setting,a.progress_every)
        if r["status"]=="PASS":
            times.append(r["elapsed_seconds"])
        elif r["status"]=="FAIL":
            bad+=1

    print(f"{a.stage.upper()} COMPLETE: FAIL={bad}")
    return 1 if bad else 0

if __name__=="__main__":
    raise SystemExit(main())
