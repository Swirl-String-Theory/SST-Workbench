"""A058 v0.2.10: budgeted, matched-iteration KnotPlot observations.

A budget is an observation horizon, NOT evidence of an equilibrated attractor.
Private KnotPlot stdout and mappings never appear in public CSV/JSON output.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,math,subprocess,sys,time,shutil,re
import numpy as np
from experiment.metrics import curve_metrics,read_xyz,shape_distance
from tools.run_knotplot_campaign import (KP, _safe_diagnostic, _segment, _wait_log_section,
     _state_ok, _sha256, _all_params, resolve_exe, resolve_workdir)

ROOT=Path(__file__).resolve().parents[1]

def loadj(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def savej(p,payload):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def _read_status(log:Path,start:str,end:str,timeout:int=15):
    seg=_wait_log_section(log,start,end,float(timeout))
    return _safe_diagnostic(seg)

def _fatal(log:Path,kp:KP,tag:str)->None:
    if kp.proc.poll() is not None:
        raise RuntimeError(f'{tag}: KnotPlot process exited rc={kp.proc.returncode} (see PRIVATE log)')
    txt=log.read_text(encoding='utf-8',errors='replace') if log.is_file() else ''
    if re.search(r'freeglut\s+error\s*:',txt,re.I):
        raise RuntimeError(f'{tag}: freeglut graphics initialization error (see PRIVATE log)')
    if re.search(r'\bunknown command\b',txt,re.I):
        raise RuntimeError(f'{tag}: unrecognized KnotPlot command (see PRIVATE log)')

def wait_coords(path:Path,kp:KP,log:Path,timeout:float=40):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        _fatal(log,kp,'awaiting coordinate export')
        if path.is_file() and path.stat().st_size>0:
            try:
                data=read_xyz(path)
                if len(data)==300:return data
            except Exception:pass
        time.sleep(0.075)
    raise TimeoutError(f'coordinate export timeout after {timeout:g}s; {path.name} (see PRIVATE log)')

def _sector_lines(c,priv,cal,seed):
    sid=c['sector_id'];sm=priv['sectors'][sid];sw=cal['resolved_sectors'][sid]
    items=['reset all','collision fast',f'load {seed.resolve().as_posix()}',f'{sw} = on']
    for aid in sm['axes']:
        p=priv['axes'][aid]['parameter'];v=float(cal['defaults'][p])
        if c['role']=='sweep' and c['axis_id']==aid:v*=float(c['multiplier'])
        items.append(f'{p} = {v:.17g}')
    if c['role']=='activation_control':items.append(f'{sw} = off')
    return items

def _probe_sector(exe,wd,seed,priv,cal,cfg,sid,out):
    """Probe required sector under both headless and (where necessary) initialized GUI modes.

    A failed sector is quarantined; the other seven sliders remain actionable.
    The GUI fallback is only enabled after a real observed headless failure.
    """
    ref={'condition_id':'PROBE','role':'reference','reference_id':sid,'sector_id':sid,'axis_id':None,'multiplier':1.0}
    out.mkdir(parents=True,exist_ok=True)
    trials=[]
    for graphics in (False,True):
        # User's observed freeglut failure occurs for drag when -nographics is used.
        # Avoid opening GUI for already-qualified headless sectors.
        mode='graphics' if graphics else 'headless'
        log=out/f'{sid}_{mode}.log';a=out/f'{sid}_{mode}_start.txt';b=out/f'{sid}_{mode}_after32.txt'
        kp=None;old=KP.__init__
        try:
            kp=KP(exe,wd,log) if not graphics else _start_graphics_kp(exe,wd,log)
            kp.send(*_sector_lines(ref,priv,cal,seed),'echo A058_PROBE_START_BEGIN','safe','echo A058_PROBE_START_END',f'save {a.resolve().as_posix()} ascii')
            wait_coords(a,kp,log,20)
            safe=_read_status(log,'A058_PROBE_START_BEGIN','A058_PROBE_START_END')
            if not safe['safe']:raise RuntimeError('start safety '+safe['status'])
            kp.send('go 32','echo A058_PROBE_STEP_BEGIN','parameters','echo A058_PROBE_STEP_END',f'save {b.resolve().as_posix()} ascii')
            wait_coords(b,kp,log,20)
            seg=_wait_log_section(log,'A058_PROBE_STEP_BEGIN','A058_PROBE_STEP_END',15)
            it=_all_params(seg).get('iteration')
            if not isinstance(it,(int,float)) or int(round(it))<32:
                raise RuntimeError('go 32 iteration counter not verified')
            rc=kp.close();kp=None
            if rc!=0:raise RuntimeError(f'exit status={rc}')
            return {'status':'PASS','mode':mode,'observed_iteration':int(round(it)),'log_private':str(log.relative_to(ROOT)),'fallback_used':graphics}
        except Exception as e:
            trials.append({'mode':mode,'status':'FAIL','reason':str(e),'log_private':str(log.relative_to(ROOT))})
        finally:
            if kp is not None:kp.kill()
        if sid!='R4':break  # GUI fallback reserved for historically crashing R4 sector
    return {'status':'UNSUPPORTED_RUNTIME','mode':None,'trials':trials}

def _start_graphics_kp(exe,wd,log):
    """Construct a KP-compatible controller with -stdin and glut initialized."""
    import threading,queue
    kp=KP.__new__(KP)
    log.parent.mkdir(parents=True,exist_ok=True)
    kp.logfh=log.open('w',encoding='utf-8',newline='\n')
    kp.proc=subprocess.Popen([str(exe),'-stdin'],cwd=wd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,text=True,bufsize=1,universal_newlines=True)
    kp.q=queue.Queue();kp.th=threading.Thread(target=kp._reader,daemon=True);kp.th.start()
    return kp

def run_condition(exe,wd,seed,priv,cal,cfg,c,run_dir,mode,checkpoints):
    cid=c['condition_id'];wdir=run_dir/'results'/cid;wdir.mkdir(parents=True,exist_ok=True)
    log=ROOT/'private/campaign_logs'/run_dir.name/f'{cid}.log';log.parent.mkdir(parents=True,exist_ok=True)
    kp=None;iter_now=0;trace=[];row={'condition_id':cid,'role':c['role'],'reference_id':c['reference_id'],
           'axis_id':c.get('axis_id'),'multiplier':c['multiplier'],'status':'FAIL','iterations':0,
           'converged':False,'safety_cap_hit':False,'safe_final_verified':False,
           'parameter_state_verified':False,'returncode':None,'reason':'not_started',
           'shared_seed_sha256':cal['shared_seed_sha256'],'checkpoints':[]}
    try:
        kp=KP(exe,wd,log) if mode=='headless' else _start_graphics_kp(exe,wd,log)
        initial=wdir/'initial.txt'
        kp.send(*_sector_lines(c,priv,cal,seed),'echo A058_PARAMETER_STATE_BEGIN','parameters',
           'echo A058_PARAMETER_STATE_END','echo A058_START_SAFE_BEGIN','safe','echo A058_START_SAFE_END',
           f'save {initial.resolve().as_posix()} ascii')
        prev=wait_coords(initial,kp,log,40)
        status=_read_status(log,'A058_START_SAFE_BEGIN','A058_START_SAFE_END')
        row['safety_start_status']=status['status'];row['safe_start_verified']=status['safe']
        if not status['safe']:raise RuntimeError('unsafe or unconfirmed shared seed at condition start')
        stable=0
        for target in checkpoints:
            delta=target-iter_now
            if delta<=0:raise AssertionError('checkpoint budget not increasing')
            fp=wdir/f'checkpoint_{target:06d}.txt'
            start=time.monotonic()
            kp.send(f'go {delta}',f'save {fp.resolve().as_posix()} ascii')
            cur=wait_coords(fp,kp,log,40 if target<=512 else (600 if target>=32768 else 180))
            shape=float(shape_distance(prev,cur,m=128))
            x=curve_metrics(prev);y=curve_metrics(cur)
            scal=max(abs(float(y[k])-float(x[k]))/max(abs(float(y[k])),abs(float(x[k])),1e-12) for k in ('length','rg','edge_cv'))
            iter_now=target
            trace.append({'iteration':target,'go_increment':delta,'shape_delta':shape,'scalar_delta':scal,'wall_seconds':round(time.monotonic()-start,4)})
            row['checkpoints'].append(target);prev=cur
        final=wdir/'final.txt';shutil.copy2(wdir/f'checkpoint_{checkpoints[-1]:06d}.txt',final)
        kp.send('echo A058_FINAL_SAFE_BEGIN','safe','echo A058_FINAL_SAFE_END',
                'echo A058_FINAL_STATE_BEGIN','parameters','echo A058_FINAL_STATE_END')
        _wait_log_section(log,'A058_FINAL_STATE_BEGIN','A058_FINAL_STATE_END',20)
        rc=kp.close();kp=None
        txt=log.read_text(encoding='utf-8',errors='replace')
        start_ok,sd=_state_ok(txt,c,priv,cal,'A058_PARAMETER_STATE_BEGIN','A058_PARAMETER_STATE_END')
        end_ok,ed=_state_ok(txt,c,priv,cal,'A058_FINAL_STATE_BEGIN','A058_FINAL_STATE_END')
        safety=_safe_diagnostic(_segment(txt,'A058_FINAL_SAFE_BEGIN','A058_FINAL_SAFE_END'))
        observed_iteration=_all_params(_segment(txt,'A058_FINAL_STATE_BEGIN','A058_FINAL_STATE_END')).get('iteration')
        iter_ok=isinstance(observed_iteration,(float,int)) and int(round(float(observed_iteration)))>=iter_now
        good=rc==0 and start_ok and end_ok and safety['safe'] and iter_ok and 'unknown command' not in txt.casefold() and not re.search('freeglut\\s+error\\s*:',txt,re.I)
        row.update({'status':'PASS' if good else 'FAIL','iterations':iter_now,'returncode':rc,
                    'safe_final_verified':safety['safe'],'safety_final_status':safety['status'],
                    'parameter_state_verified':start_ok and end_ok,'parameter_state_start':sd,'parameter_state_final':ed,
                    'iteration_counter_verified':iter_ok,'final_sha256':_sha256(final),
                    'reason':'' if good else f'rc={rc} state={start_ok}/{end_ok} safe={safety["status"]} iter_ok={iter_ok}',
                    'trace_points':len(trace),'convergence_assessed':False})
    except Exception as e:
        if kp is not None:kp.kill()
        # A partially advanced condition never receives valid final-coordinate status.
        (wdir/'final.txt').unlink(missing_ok=True)
        row.update({'iterations':iter_now,'reason':f'{type(e).__name__}: {e}','trace_points':len(trace)})
    savej(wdir/'convergence_trace.json',{'schema':'A058-FIXED-OBSERVATION-1','condition_id':cid,
       'budget':checkpoints[-1],'converged':False,'convergence_assessed':False,'iterations':iter_now,'trace':trace})
    return row

def run_budget(tier:str,selected:list[dict],selection:dict,run_dir:Path):
    cfg=loadj(ROOT/'configs/default.json');priv=loadj(ROOT/'private/axis_map.json')
    cal=loadj(ROOT/'private/install_test_runtime/defaults.json')
    exe,es=resolve_exe('');wd,ws=resolve_workdir('')
    if exe is None or not exe.is_file():raise RuntimeError('KnotPlot executable missing')
    if not wd.is_dir():raise RuntimeError('KnotPlot working directory missing')
    if _sha256(exe)!=cal['executable_sha256']:raise RuntimeError('KnotPlot executable changed since installation')
    seed=ROOT/'private/install_test_runtime/trefoil_install_test.txt'
    if not seed.is_file() or _sha256(seed)!=cal['shared_seed_sha256']:raise RuntimeError('Shared trefoil seed changed since calibration')
    if len(read_xyz(seed))!=300:raise RuntimeError('Shared seed does not have 300 beads')
    checkpoints=cfg['response_budgets'][tier]['checkpoints']
    run_dir.mkdir(parents=True,exist_ok=False)
    savej(run_dir/'selection.json',selection)
    savej(run_dir/'manifest.json',{'tier':tier,'conditions':selected,'count':len(selected),'shared_seed_sha256':cal['shared_seed_sha256']})
    # Sector probes are always performed before any costly condition.
    sectors={c['sector_id'] for c in selected}
    probes={}
    for sid in sorted(sectors):
        probes[sid]=_probe_sector(exe,wd,seed,priv,cal,cfg,sid,ROOT/'private/sector_preflight'/run_dir.name)
        print('SECTOR PROBE',sid,probes[sid]['status'],probes[sid].get('mode',''))
    savej(run_dir/'sector_preflights.json',probes)
    savej(run_dir/'runtime.json',{'schema':'A058-BUDGET-RUNTIME-1','budget':tier,'iterations_per_condition':checkpoints[-1],
       'checkpoints':checkpoints,'source_executable_sha256':_sha256(exe),'source_executable':str(exe),
       'source_workdir':str(wd),'shared_seed_sha256':cal['shared_seed_sha256'],
       'registered_conditions':271,'selected_conditions':len(selected),'sector_modes':{k:v.get('mode') for k,v in probes.items()},'regime':cfg['regime']})
    rows=[]
    for i,c in enumerate(selected,1):
        cid=c['condition_id'];sid=c['sector_id'];probe=probes[sid]
        if probe['status']!='PASS':
            row={'condition_id':cid,'role':c['role'],'reference_id':c['reference_id'],'axis_id':c.get('axis_id'),
                 'multiplier':c['multiplier'],'status':'UNSUPPORTED_RUNTIME','iterations':0,'converged':False,
                 'parameter_state_verified':False,'safe_final_verified':False,'returncode':None,
                 'reason':f'sector {sid} did not pass preflight in headless or graphics mode',
                 'shared_seed_sha256':cal['shared_seed_sha256'],'checkpoints':[]}
            savej(run_dir/'results'/cid/'convergence_trace.json',{'schema':'A058-FIXED-OBSERVATION-1','trace':[],'condition_id':cid,'reason':row['reason']})
        else:row=run_condition(exe,wd,seed,priv,cal,cfg,c,run_dir,probe['mode'],checkpoints)
        rows.append(row)
        if i<=7 or i%10==0 or row['status']!='PASS':
            print(f'[{i}/{len(selected)}] {cid} {c["role"]} {row["status"]} {row["iterations"]}/{checkpoints[-1]}',flush=True)
        savej(run_dir/'runlog.json',{'schema':'A058-BUDGET-RUNLOG-1','tier':tier,'conditions':rows,'count':len(rows),'selected_count':len(selected)})
    complete=sum(r['status']=='PASS' for r in rows)
    summary={'schema':'A058-BUDGET-SUMMARY-1','tier':tier,'budget':checkpoints[-1],
       'selected_count':len(selected),'pass_count':complete,
       'unsupported_runtime':sum(r['status']=='UNSUPPORTED_RUNTIME' for r in rows),
       'failed_count':sum(r['status']=='FAIL' for r in rows),
       'shared_seed_sha256':cal['shared_seed_sha256'],
       'complete':complete==len(selected),'no_attractor_claim':True}
    savej(run_dir/'summary.json',summary)
    print('BUDGET COMPLETE',tier,complete,'/',len(selected),'PASS; failed',summary['failed_count'],'unsupported',summary['unsupported_runtime'])
    return summary
