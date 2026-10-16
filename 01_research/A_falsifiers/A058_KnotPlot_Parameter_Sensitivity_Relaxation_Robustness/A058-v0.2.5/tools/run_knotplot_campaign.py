from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time,math,threading,queue,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiment.metrics import read_xyz,curve_metrics,shape_distance

def _sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def resolve_exe(explicit=''):
    if explicit.strip():return Path(os.path.expandvars(explicit)).expanduser().resolve(),'argument'
    if os.environ.get('KNOTPLOT_EXE','').strip():return Path(os.path.expandvars(os.environ['KNOTPLOT_EXE'])).expanduser().resolve(),'KNOTPLOT_EXE'
    for key in ('USER_PROFILE','USERPROFILE'):
        raw=os.environ.get(key,'').strip()
        if raw:
            p=Path(raw)/'AppData'/'Local'/'Programs'/'KnotPlot'/'KnotPlot.exe'
            if p.is_file():return p.resolve(),f'{key}_default'
    return None,'not_found'
def workbench_root():
    for key in ('SST_WORKBENCH','SST_WORKBENCH_ROOT'):
        raw=os.environ.get(key,'').strip()
        if raw:return Path(os.path.expandvars(raw)).expanduser().resolve(),key
    for p in [ROOT,*ROOT.parents]:
        if (p/'04_tools'/'A_geometry').is_dir() and (p/'01_research').is_dir():return p.resolve(),'inferred_from_instance'
    return None,None
def resolve_workdir(explicit=''):
    raw=explicit.strip() or os.environ.get('KNOTPLOT_STARTIN','').strip()
    if raw:return Path(os.path.expandvars(raw)).expanduser().resolve(),'argument_or_env'
    wb,src=workbench_root()
    if wb:
        p=wb/'04_tools'/'A_geometry'/'A001_knotplot'
        if p.is_dir():return p.resolve(),f'{src}:04_tools/A_geometry/A001_knotplot'
    out=ROOT/'A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness_Falsifier_v0.2.5-outputs';out.mkdir(exist_ok=True);return out.resolve(),'instance_outputs'
def _wait_file(path:Path,old_mtime:int|None,timeout:float):
    end=time.time()+timeout
    while time.time()<end:
        try:
            st=path.stat()
            if st.st_size>0 and (old_mtime is None or st.st_mtime_ns!=old_mtime):
                try:
                    x=read_xyz(path)
                    if len(x)>=100:return x
                except Exception:pass
        except FileNotFoundError:pass
        time.sleep(0.05)
    raise TimeoutError(f'timed out waiting for KnotPlot export {path}')
def _scalar_delta(a,b):
    ma,mb=curve_metrics(a),curve_metrics(b); vals=[]
    for k in ('length','rg','edge_cv'):
        aa=float(ma[k]);bb=float(mb[k]);vals.append(abs(bb-aa)/max(abs(aa),abs(bb),1e-12))
    return max(vals)
def _all_params(seg):
    out={}
    for m in re.finditer(r'(?mi)^\s*([A-Za-z0-9_-]+)\s*=\s*([^\r\n]+)',seg):
        name=m.group(1).strip(); raw=m.group(2).strip(); low=raw.casefold()
        if low in {'on','true','yes'}: val=True
        elif low in {'off','false','no'}: val=False
        else:
            try: val=float(raw.split()[0])
            except ValueError: val=raw
        out[name]=val
    return out
def _segment(text,a,b):
    i=text.find(a);j=text.find(b,i+len(a))
    if i<0 or j<0:return ''
    return text[i+len(a):j]
class KP:
    def __init__(self,exe:Path,wd:Path,log:Path):
        log.parent.mkdir(parents=True,exist_ok=True);self.logfh=log.open('w',encoding='utf-8',newline='\n');self.proc=subprocess.Popen([str(exe),'-stdin','-nographics'],cwd=wd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1,universal_newlines=True);self.q=queue.Queue();self.th=threading.Thread(target=self._reader,daemon=True);self.th.start()
    def _reader(self):
        try:
            for line in self.proc.stdout:
                self.logfh.write(line);self.logfh.flush();self.q.put(line)
        finally:self.q.put(None)
    def send(self,*lines):
        if self.proc.poll() is not None:raise RuntimeError(f'KnotPlot exited early rc={self.proc.returncode}')
        for line in lines:self.proc.stdin.write(str(line)+'\n')
        self.proc.stdin.flush()
    def close(self,timeout=30):
        try:self.send('quit')
        except Exception:pass
        try:self.proc.stdin.close()
        except Exception:pass
        try:self.proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        self.th.join(timeout=2);self.logfh.close();return self.proc.returncode
    def kill(self):
        try:self.proc.kill();self.proc.wait(timeout=5)
        except Exception:pass
        try:self.logfh.close()
        except Exception:pass

def _state_ok(txt,c,priv,cal,marker_a,marker_b):
    seg=_segment(txt,marker_a,marker_b); params=_all_params(seg)
    if not seg:return False,{'error':'missing marker segment'}
    rid=c['sector_id']; sw=cal['resolved_sectors'][rid]; sm=priv['sectors'][rid]
    checks={};off_control=c['role']=='activation_control'
    expected_switch=not off_control
    # Internal parameter names are PRIVATE and never serialized into the
    # PUBLIC campaign/runlog_pilot.json. Results contain anonymous S*/R* only.
    if sw in params: checks['sector_switch']=params[sw] is expected_switch
    else: checks['sector_switch']=True  # weaker evidence: setter accepted, no getter
    unreported=[]; reported=[]
    for axis_id in sm['axes']:
        axis=priv['axes'][axis_id];p=axis['parameter'];expected=float(cal['defaults'][p])
        if c['role']=='sweep' and axis_id==c.get('axis_id'): expected*=float(c['multiplier'])
        obs=params.get(p);mode=axis.get('verification','runtime_roundtrip')
        if off_control and obs is None:
            checks[axis_id]=True;unreported.append(axis_id)
        elif mode=='setter_acceptance' and obs is None:
            checks[axis_id]=True;unreported.append(axis_id)
        else:
            checks[axis_id]=isinstance(obs,(int,float)) and math.isclose(float(obs),expected,rel_tol=1e-9,abs_tol=1e-12)
        if obs is not None:reported.append(axis_id)
    return all(checks.values()),{'checks':checks,'reported_axis_ids':reported,
                                'accepted_unreported_axis_ids':unreported,
                                'switch_reported':sw in params,
                                'switch_state_expected':'off' if off_control else 'on',
                                'activation_control':off_control,
                                'evidence_limitation':bool(unreported or sw not in params)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tier',choices=['pilot'],default='pilot');ap.add_argument('--exe',default='');ap.add_argument('--workdir',default='');ap.add_argument('--resume',action='store_true');a=ap.parse_args()
    cfg=json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8'));priv=json.loads((ROOT/'private/axis_map.json').read_text(encoding='utf-8'));cal=json.loads((ROOT/'private/install_test_runtime/defaults.json').read_text(encoding='utf-8'));man=json.loads((ROOT/'campaign/manifest_pilot.json').read_text(encoding='utf-8'))
    exe,es=resolve_exe(a.exe);wd,ws=resolve_workdir(a.workdir)
    if exe is None or not exe.is_file():raise SystemExit('KnotPlot executable not found')
    if not wd.is_dir():raise SystemExit(f'KnotPlot Start In directory not found: {wd}')
    runtime={'schema':'A058-KNOTPLOT-RUNTIME-7','tier':'pilot','executable':str(exe),'executable_source':es,'executable_sha256':_sha256(exe),'executable_bytes':exe.stat().st_size,'working_directory':str(wd),'working_directory_source':ws,'regime':cfg['regime'],'install_calibration_schema':cal.get('schema')}
    (ROOT/'campaign/runtime_pilot.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    defaults=cal['defaults'];resolved=cal['resolved_sectors'];ad=cfg['adaptive_relaxation'];rows=[];top=priv['topology']['T00'];workroot=ROOT/'private/adaptive_work';workroot.mkdir(parents=True,exist_ok=True);total=len(man['conditions'])
    for idx,c in enumerate(man['conditions'],1):
        cid=c['condition_id'];rdir=ROOT/'campaign/results'/cid;rdir.mkdir(parents=True,exist_ok=True);final=rdir/'final.txt';tracep=rdir/'convergence_trace.json'
        if a.resume and final.is_file() and final.stat().st_size>0 and tracep.is_file():print(f'[{idx}/{total}] {cid} SKIP');continue
        wdir=workroot/cid
        if wdir.exists():shutil.rmtree(wdir)
        wdir.mkdir(parents=True);log=ROOT/'private/campaign_logs/pilot'/f'{cid}.log';kp=None;trace=[];converged=False;iteration=0;sector_switch=resolved[c['sector_id']]
        try:
            kp=KP(exe,wd,log);initial=wdir/'initial.txt';lines=['reset all','collision fast',f"load {top['spec']}",f"refine nbeads {top['baseline_n']}",f'{sector_switch} = on']
            axis_id=c.get('axis_id'); sm=priv['sectors'][c['sector_id']]
            # Materialize the complete sector reference explicitly. This is required for
            # controls such as S3 that are setter-visible but absent from `parameters`.
            for aid in sm['axes']:
                p=priv['axes'][aid]['parameter']; val=float(defaults[p])
                if c['role']=='sweep' and aid==axis_id: val*=float(c['multiplier'])
                lines.append(f'{p} = {val:.17g}')
            if c['role']=='activation_control':
                lines.append(f'{sector_switch} = off')
            lines += ['echo A058_PARAMETER_STATE_BEGIN','parameters','echo A058_PARAMETER_STATE_END','echo A058_START_SAFE_BEGIN','safe','echo A058_START_SAFE_END',f'save {initial.resolve().as_posix()} ascii']
            kp.send(*lines);prev=_wait_file(initial,None,ad['per_block_timeout_seconds']);stable=0
            while iteration < int(ad['max_iterations_safety_cap']):
                probe=wdir/f'probe_{iteration+int(ad["quantum_iterations"]):06d}.txt';kp.send(f'go {int(ad["quantum_iterations"])}',f'save {probe.resolve().as_posix()} ascii');cur=_wait_file(probe,None,ad['per_block_timeout_seconds']);iteration += int(ad['quantum_iterations']);sd=float(shape_distance(prev,cur,m=128));sc=float(_scalar_delta(prev,cur));trace.append({'iteration':iteration,'shape_delta':sd,'scalar_delta':sc});prev=cur
                if iteration>=int(ad['minimum_iterations']) and sd<=float(ad['shape_delta_threshold']) and sc<=float(ad['scalar_delta_threshold']):stable+=1
                else:stable=0
                if stable>=int(ad['stable_windows_required']):converged=True;break
                try:probe.unlink()
                except Exception:pass
            kp.send(f'save {final.resolve().as_posix()} ascii','echo A058_FINAL_SAFE_BEGIN','safe','echo A058_FINAL_SAFE_END','echo A058_FINAL_STATE_BEGIN','parameters','echo A058_FINAL_STATE_END','dowker');_wait_file(final,None,ad['per_block_timeout_seconds']);rc=kp.close();kp=None
            txt=log.read_text(encoding='utf-8',errors='replace');unknown='unknown command' in txt.casefold();safe_start=('A058_START_SAFE_BEGIN' in txt and 'not safe' not in _segment(txt,'A058_START_SAFE_BEGIN','A058_START_SAFE_END').casefold());safe_final=('A058_FINAL_SAFE_BEGIN' in txt and 'not safe' not in _segment(txt,'A058_FINAL_SAFE_BEGIN','A058_FINAL_SAFE_END').casefold())
            start_ok,start_detail=_state_ok(txt,c,priv,cal,'A058_PARAMETER_STATE_BEGIN','A058_PARAMETER_STATE_END');final_ok,final_detail=_state_ok(txt,c,priv,cal,'A058_FINAL_STATE_BEGIN','A058_FINAL_STATE_END');state_ok=start_ok and final_ok and not unknown
            status='PASS' if rc==0 and state_ok and safe_start and safe_final and final.is_file() else 'FAIL';reason='' if status=='PASS' else f'rc={rc}, unknown={unknown}, state_start={start_ok}, state_final={final_ok}, safe_start={safe_start}, safe_final={safe_final}'
            row={'condition_id':cid,'role':c['role'],'reference_id':c['reference_id'],'axis_id':axis_id,'multiplier':c['multiplier'],'returncode':rc,'status':status,'reason':reason,'converged':converged,'iterations':iteration,'safety_cap_hit':not converged,'unknown_command':unknown,'parameter_state_verified':state_ok,'parameter_state_start':start_detail,'parameter_state_final':final_detail,'safe_start_verified':safe_start,'safe_final_verified':safe_final,'final_sha256':_sha256(final) if final.is_file() else None,'trace_points':len(trace)}
        except Exception as e:
            if kp is not None:kp.kill()
            row={'condition_id':cid,'role':c['role'],'reference_id':c['reference_id'],'axis_id':c.get('axis_id'),'multiplier':c['multiplier'],'returncode':None,'status':'FAIL','reason':f'{type(e).__name__}: {e}','converged':False,'iterations':iteration,'safety_cap_hit':False,'unknown_command':None,'parameter_state_verified':False,'safe_start_verified':False,'safe_final_verified':False,'final_sha256':None,'trace_points':len(trace)}
        tracep.write_text(json.dumps({'schema':'A058-CONVERGENCE-TRACE-7','condition_id':cid,'converged':row['converged'],'iterations':row['iterations'],'trace':trace},indent=2,sort_keys=True)+'\n',encoding='utf-8');rows.append(row);print(f'[{idx}/{total}] {cid} {c["role"]} {c.get("axis_id") or c["reference_id"]} m={c["multiplier"]:.9g} -> {row["status"]} converged={row["converged"]} iter={row["iterations"]}')
    payload={'schema':'A058-RUNLOG-7','conditions':rows,'count':len(rows)};(ROOT/'campaign/runlog_pilot.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(f'Complete: {len(rows)} attempted; failures={sum(r["status"]!="PASS" for r in rows)}; nonconverged={sum(not r["converged"] for r in rows)}')
    return 0
if __name__=='__main__':raise SystemExit(main())
