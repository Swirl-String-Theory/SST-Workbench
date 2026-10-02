from __future__ import annotations
from pathlib import Path
import json,os,re,subprocess,time,csv
from datetime import datetime
from .kpc import resume_script,resume_probe_script
from .model import prepare_components_from_coords,parse_multicomponent_coords,is_unlink_control,synthesize_unlink_components,write_multicomponent_coords,closed_arclength,allocate_beads_by_length,resample_closed_component

REJECT=("unknown command","unknown parameter","invalid parameter","illegal parameter","not a parameter","obsolete")
HARD=("can't open file","cannot open file","failed to open","freeglut error")

def resolve_knotplot(package_root):
    override=os.environ.get("KNOTPLOT_LNK","").strip()
    sc=Path(override) if override else package_root.parent/"KnotPlot.lnk"
    if not sc.is_file(): raise FileNotFoundError(f"KnotPlot shortcut missing: {sc}")
    ps="$s=(New-Object -ComObject WScript.Shell).CreateShortcut('"+str(sc).replace("'","''")+"'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"
    cp=subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True)
    rows=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
    if not rows: raise RuntimeError("Could not resolve KnotPlot.lnk")
    return Path(rows[0]),Path(rows[1]) if len(rows)>1 and rows[1] else package_root.parent

def render(text,campaign,cwd,name):
    rel=os.path.relpath(campaign,cwd).replace("\\","/")
    if " " in rel: raise RuntimeError("Campaign relative path contains spaces")
    rd=campaign/"runtime_kpc";rd.mkdir(parents=True,exist_ok=True)
    p=rd/name;p.write_text(text.replace("__CAMPAIGN_REL__",rel),encoding="utf-8",newline="\n");return p

def fmt_duration(seconds):
    if seconds is None or not isinstance(seconds,(int,float)) or seconds<0:return "--:--:--"
    seconds=int(round(seconds));d,rem=divmod(seconds,86400);h,rem=divmod(rem,3600);m,s=divmod(rem,60)
    return f"{d}d {h:02d}:{m:02d}:{s:02d}" if d else f"{h:02d}:{m:02d}:{s:02d}"

def log_progress(campaign,message):
    stamp=datetime.now().astimezone().isoformat(timespec="seconds");line=f"{stamp} {message}"
    print(line,flush=True)
    with (campaign/"progress.log").open("a",encoding="utf-8") as f:f.write(line+"\n");f.flush()

def run_kpc(exe,cwd,kpc,log):
    with kpc.open("rb") as fin,log.open("wb") as fout:
        cp=subprocess.run([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
    txt=log.read_text(encoding="utf-8",errors="replace")
    rej=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in REJECT)]
    hard=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in HARD)]
    return cp.returncode,rej,hard

def _single_component_coords(path):
    comps=parse_multicomponent_coords(path)
    if len(comps)!=1:
        raise RuntimeError(f"Expected one component in isolated export {path}, parsed {len(comps)}")
    return comps[0]

def prepare_topologies(package_root,campaign,force=False):
    plan=json.loads((campaign/"campaign.json").read_text())
    exe,cwd=resolve_knotplot(package_root)
    rawd=campaign/"prep_raw";prepd=campaign/"prepared_inputs";logs=campaign/"logs"
    rawd.mkdir(exist_ok=True);prepd.mkdir(exist_ok=True);logs.mkdir(exist_ok=True)
    result=[];dur=[];total=len(plan["topologies"])

    for i,t in enumerate(plan["topologies"],1):
        prepared=prepd/f"{t['topo_id']}.txt"
        ap=prepd/f"{t['topo_id']}.allocation.json"
        start=time.monotonic()
        ncomp=int(t["components"])

        if is_unlink_control(t["kind"],t["spec"]):
            comps,allocation=synthesize_unlink_components(
                ncomp,int(t["nbeads"]),plan["min_beads_per_component"]
            )
            raw_combined=rawd/f"{t['topo_id']}__synthetic.txt"
            write_multicomponent_coords(raw_combined,comps)
            write_multicomponent_coords(prepared,comps)
            allocation.update({
                "raw_paths":[str(raw_combined)],
                "prepared_path":str(prepared),
                "topology_id":t["topo_id"],
                "kind":t["kind"],
                "spec":t["spec"],
                "expected_components":ncomp,
                "parsed_components":len(comps),
                "preparation_source":"synthetic_null_control"
            })
            log_progress(
                campaign,
                f"[PREP {i:03d}/{total:03d}] SYNTHETIC {t['spec']} "
                f"components={ncomp} beads={allocation['allocated_beads']}"
            )
        else:
            raw_paths=[rawd/f"{t['topo_id']}__comp{j:03d}.txt" for j in range(ncomp)]
            need_probe=force or any(not p.is_file() or p.stat().st_size==0 for p in raw_paths)

            if need_probe:
                src=(campaign/"prep_kpc"/f"{t['topo_id']}.kpc").read_text(encoding="utf-8")
                rt=render(src,campaign,cwd,f"PREP__{t['topo_id']}.kpc")
                log_progress(
                    campaign,
                    f"[PREP {i:03d}/{total:03d}] START {t['spec']} "
                    f"isolated-components={ncomp}"
                )
                rc,rej,hard=run_kpc(exe,cwd,rt,logs/f"PREP__{t['topo_id']}.log")
                missing=[str(p) for p in raw_paths if not p.is_file() or p.stat().st_size==0]
                if rc or rej or hard or missing:
                    raise RuntimeError(
                        f"Topology component probe failed for {t['spec']}: "
                        f"rc={rc} reject={rej[-3:]} hard={hard[-3:]} missing={missing[:3]}"
                    )

            # Every file is generated after `keep j`, therefore each must contain
            # exactly one component regardless of how the original full-link
            # coords exporter formats component separators.
            comps=[_single_component_coords(p) for p in raw_paths]
            lengths=[closed_arclength(x) for x in comps]
            alloc=allocate_beads_by_length(
                lengths,int(t["nbeads"]),plan["min_beads_per_component"]
            )
            prepared_comps=[resample_closed_component(x,n) for x,n in zip(comps,alloc)]
            write_multicomponent_coords(prepared,prepared_comps)

            allocation={
                "raw_paths":[str(p) for p in raw_paths],
                "prepared_path":str(prepared),
                "component_count":len(comps),
                "expected_components":ncomp,
                "parsed_components":len(comps),
                "total_beads":int(t["nbeads"]),
                "min_beads_per_component":int(plan["min_beads_per_component"]),
                "component_lengths":lengths,
                "length_fractions":[float(x/sum(lengths)) for x in lengths],
                "allocated_beads":alloc,
                "allocated_fractions":[float(x/int(t["nbeads"])) for x in alloc],
                "allocation_sum":sum(alloc),
                "method":"KnotPlot reload + keep component + isolated coords; proportional closed-arclength allocation",
                "topology_id":t["topo_id"],
                "kind":t["kind"],
                "spec":t["spec"],
                "preparation_source":"knotplot_keep_component"
            }

        ap.write_text(json.dumps(allocation,indent=2)+"\n",encoding="utf-8")
        dt=time.monotonic()-start
        dur.append(dt)
        eta=(sum(dur)/len(dur))*(total-i)
        log_progress(
            campaign,
            f"[PREP {i:03d}/{total:03d}] DONE {t['spec']} "
            f"elapsed={fmt_duration(dt)} prepETA={fmt_duration(eta)} "
            f"lengths={['%.6g'%x for x in allocation['component_lengths']]} "
            f"beads={allocation['allocated_beads']}"
        )
        result.append(allocation)

    (prepd/"ALLOCATIONS.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def checkpoint_file(campaign,rid,it,ext):return campaign/"out"/f"{rid}_i{it:06d}.{ext}"
def completed_checkpoint(campaign,rid,checkpoints):
    found=[]
    for it in checkpoints:
        m=checkpoint_file(campaign,rid,it,"metrics.csv");k=checkpoint_file(campaign,rid,it,"k")
        if m.is_file() and m.stat().st_size>0 and k.is_file() and k.stat().st_size>0:found.append(it)
    return max(found) if found else None

def append_timing(campaign,row):
    p=campaign/"timings.csv";fields=["run_index","run_total","run_id","mode","status","start_time","end_time","elapsed_seconds","start_checkpoint","final_checkpoint","max_ago"]
    exists=p.is_file()
    with p.open("a",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        if not exists:w.writeheader()
        w.writerow({k:row.get(k) for k in fields})

def recent_mean(v,n=12):
    x=[float(a) for a in v if a and a>0][-n:]
    return sum(x)/len(x) if x else None

def execute_one(exe,cwd,rt,log,campaign,rid,index,total,cps,max_ago,mode,done_durations,progress_every):
    start_wall=datetime.now().astimezone();start=time.monotonic();start_cp=completed_checkpoint(campaign,rid,cps) or 0;last_seen=start_cp;last_report=-1
    log_progress(campaign,f"[RUN {index:04d}/{total:04d}] START {rid} mode={mode} from={start_cp} target={max_ago}")
    with rt.open("rb") as fin,log.open("ab" if mode.startswith("RESUME") else "wb") as fout:
        proc=subprocess.Popen([str(exe),"-nog"],cwd=str(cwd),stdin=fin,stdout=fout,stderr=subprocess.STDOUT)
        while True:
            rc=proc.poll();elapsed=time.monotonic()-start;cpnow=completed_checkpoint(campaign,rid,cps) or start_cp
            changed=cpnow!=last_seen; heartbeat=last_report<0 or elapsed-last_report>=max(1,progress_every)
            if changed or heartbeat or rc is not None:
                denom=max(1,max_ago-start_cp);frac=max(0,min(1,(cpnow-start_cp)/denom));run_eta=(elapsed/frac-elapsed) if frac>0.001 else None
                avg=recent_mean(done_durations);remaining=max(0,total-index)
                if avg is not None:camp_eta=(run_eta if run_eta is not None else avg)+remaining*avg
                elif run_eta is not None:camp_eta=run_eta+remaining*(elapsed/max(frac,0.001))
                else:camp_eta=None
                log_progress(campaign,f"[TIMER {index:04d}/{total:04d}] {rid} elapsed={fmt_duration(elapsed)} checkpoint={cpnow}/{max_ago} ({frac*100:5.1f}%) runETA={fmt_duration(run_eta)} campaignETA={fmt_duration(camp_eta)}")
                last_seen=cpnow;last_report=elapsed
            if rc is not None:break
            time.sleep(min(5,max(1,progress_every)))
    return rc,time.monotonic()-start,start_wall,datetime.now().astimezone(),start_cp

def read_metric_csv(path):
    p=Path(path)
    rows=[x.strip() for x in p.read_text(encoding="utf-8",errors="ignore").splitlines() if x.strip()]
    vals=None
    for line in reversed(rows):
        parts=[x.strip() for x in line.split(",")]
        if len(parts)>=5:
            try:
                vals={
                    "iteration":float(parts[0]),
                    "length":float(parts[1]),
                    "rog":float(parts[2]),
                    "nbeads":int(float(parts[3])),
                    "safeness":float(parts[4]),
                }
                break
            except Exception:
                pass
    if vals is None:
        raise RuntimeError(f"Could not parse metric CSV: {p}")
    return vals

def verify_resume_probe(campaign,rid,from_it,tol=2e-5):
    original=checkpoint_file(campaign,rid,from_it,"metrics.csv")
    probe=campaign/"resume_checks"/f"{rid}_from_i{from_it:06d}.metrics.csv"
    a=read_metric_csv(original);b=read_metric_csv(probe)
    def rel(x,y):return abs(x-y)/max(abs(x),abs(y),1e-300)
    rL=rel(a["length"],b["length"]);rR=rel(a["rog"],b["rog"])
    ok=(a["nbeads"]==b["nbeads"] and rL<=tol and rR<=tol)
    audit={
        "run_id":rid,"from_iteration":from_it,"tolerance":tol,
        "original":a,"reload_probe":b,
        "relative_length_error":rL,"relative_rog_error":rR,
        "pass":ok
    }
    out=campaign/"resume_checks"/f"{rid}_from_i{from_it:06d}.audit.json"
    out.write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    return audit

def execute_resume_probe(exe,cwd,campaign,r,baseline,from_it):
    rid=r["run_id"]
    (campaign/"resume_checks").mkdir(exist_ok=True)
    text=resume_probe_script(r,baseline,from_it)
    rt=render(text,campaign,cwd,f"{rid}__resume_probe_i{from_it:06d}.kpc")
    log=campaign/"logs"/f"{rid}__resume_probe_i{from_it:06d}.log"
    rc,rej,hard=run_kpc(exe,cwd,rt,log)
    if rc or rej or hard:
        raise RuntimeError(
            f"Resume probe failed for {rid}@{from_it}: "
            f"rc={rc} reject={rej[-3:]} hard={hard[-3:]}"
        )
    audit=verify_resume_probe(campaign,rid,from_it)
    log_progress(
        campaign,
        f"[RESUME-CHECK] {rid} from={from_it} "
        f"relL={audit['relative_length_error']:.3e} "
        f"relRg={audit['relative_rog_error']:.3e} "
        f"status={'PASS' if audit['pass'] else 'FAIL'}"
    )
    if not audit["pass"]:
        raise RuntimeError(
            f"Metric-neutral resume continuity failed for {rid}@{from_it}; "
            f"see {campaign/'resume_checks'}"
        )
    return audit

def execute(package_root,campaign,baseline,fit_mindist,save_coords,force=False,limit=None,progress_every=30):
    plan=json.loads((campaign/"campaign.json").read_text());prepare_topologies(package_root,campaign,False);exe,cwd=resolve_knotplot(package_root)
    out=campaign/"out";logs=campaign/"logs";out.mkdir(exist_ok=True);logs.mkdir(exist_ok=True);runs=plan["runs"][:limit] if limit else plan["runs"];max_ago=plan["max_ago"]
    log_progress(campaign,f"[CAMPAIGN] START name={plan['name']} runs={len(runs)} max_ago={max_ago} heartbeat={progress_every}s")
    fail=skip=0;durations=[];campaign_start=time.monotonic()
    for i,r in enumerate(runs,1):
        rid=r["run_id"];cps=plan["checkpoints"];final=cps[-1]
        if not force and checkpoint_file(campaign,rid,final,"metrics.csv").is_file() and checkpoint_file(campaign,rid,final,"k").is_file():
            skip+=1;log_progress(campaign,f"[RUN {i:04d}/{len(runs):04d}] SKIP {rid} final={final} already complete");continue
        last=None if force else completed_checkpoint(campaign,rid,cps)
        if last is not None and last<final:
            # Validate the loaded checkpoint before allowing any further `ago`.
            execute_resume_probe(exe,cwd,campaign,r,baseline,last)
            remain=[x for x in cps if x>last]
            text=resume_script(r,baseline,remain,last,fit_mindist,save_coords)
            name=f"{rid}__resume_i{last:06d}.kpc"
            mode=f"RESUME@{last}"
        else:
            text=(campaign/"kpc"/f"{rid}.kpc").read_text()
            name=f"{rid}.kpc"
            mode="START"
        rt=render(text,campaign,cwd,name);log=logs/f"{rid}.log"
        rc,elapsed,sw,ew,start_cp=execute_one(exe,cwd,rt,log,campaign,rid,i,len(runs),cps,max_ago,mode,durations,progress_every)
        txt=log.read_text(encoding="utf-8",errors="replace");rej=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in REJECT)];hard=[x.strip() for x in txt.splitlines() if any(k in x.lower() for k in HARD)];last_done=completed_checkpoint(campaign,rid,cps)
        ok=rc==0 and not rej and not hard and checkpoint_file(campaign,rid,final,"metrics.csv").is_file();status="PASS" if ok else "FAIL"
        (logs/f"{rid}_audit.json").write_text(json.dumps({"run_id":rid,"mode":mode,"status":status,"exit":rc,"rejections":rej[-20:],"hard_errors":hard[-20:],"last_checkpoint":last_done,"elapsed_seconds":elapsed},indent=2)+"\n")
        append_timing(campaign,{"run_index":i,"run_total":len(runs),"run_id":rid,"mode":mode,"status":status,"start_time":sw.isoformat(timespec="seconds"),"end_time":ew.isoformat(timespec="seconds"),"elapsed_seconds":round(elapsed,3),"start_checkpoint":start_cp,"final_checkpoint":last_done,"max_ago":max_ago})
        if ok:durations.append(elapsed)
        else:fail+=1
        avg=recent_mean(durations);eta=avg*(len(runs)-i) if avg is not None else None
        log_progress(campaign,f"[RUN {i:04d}/{len(runs):04d}] DONE {rid} status={status} elapsed={fmt_duration(elapsed)} last={last_done} avgRun={fmt_duration(avg)} remainingETA={fmt_duration(eta)}")
    log_progress(campaign,f"[CAMPAIGN] DONE pass_or_skip={len(runs)-fail} fail={fail} skipped={skip} elapsed={fmt_duration(time.monotonic()-campaign_start)}")
    return 1 if fail else 0
