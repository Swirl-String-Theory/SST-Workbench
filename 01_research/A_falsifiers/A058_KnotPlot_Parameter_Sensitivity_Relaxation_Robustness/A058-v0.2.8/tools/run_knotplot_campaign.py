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
    out=ROOT/'A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness_Falsifier_v0.2.8-outputs';out.mkdir(exist_ok=True);return out.resolve(),'instance_outputs'
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


def _wait_log_section(log:Path, marker_a:str, marker_b:str, timeout:float=20.0) -> str:
    end=time.time()+timeout
    while time.time()<end:
        if log.is_file():
            segment=_segment(log.read_text(encoding='utf-8', errors='replace'),marker_a,marker_b)
            if segment.strip(): return segment
        time.sleep(0.04)
    return ''

def _safe_diagnostic(segment: str) -> dict:
    """Parse KnotPlot safety output with stderr warnings interleaved in stdout.

    KnotPlot build 5125W can produce e.g.::
      Current position is  *** khat_mag is zero! ...
      safe.

    The WARNING is NOT proof the curve is unsafe.  The safety parser must
    preserve that warning, strip only explicit diagnostic lines, and demand
    the complete affirmative sentence.  Explicit negative or empty/ambiguous
    responses fail closed; a missing/empty current knot is never accepted.
    """
    warnings = [line.strip() for line in segment.splitlines() if '***' in line]
    # Remove only inline diagnostic substrings, preserving text before them.
    cleaned = re.sub(r'\*{3}[^\r\n]*', ' ', segment)
    # KnotPlot prompts are often attached directly to the status line.
    cleaned = re.sub(r'(?i)\bknotplot>\s*', ' ', cleaned)
    normalized = re.sub(r'\s+', ' ', cleaned).strip().casefold()
    if not normalized:
        status = 'UNCONFIRMED'
    elif re.search(r'\bcurrent\s+position\s+is\s+not\s+safe\b', normalized) or re.search(r'\bcurrent\s+position\s+is\s+unsafe\b',normalized):
        status = 'UNSAFE'
    elif re.search(r'\bnothing\s+(?:loaded|to\s+save|to\s+output)\b',segment.casefold()) or re.search(r'\bunknown\s+command\b',segment.casefold()):
        status = 'UNCONFIRMED'
    elif re.search(r'\bcurrent\s+position\s+is\s+safe\b(?:\s*\.|$)', normalized):
        status = 'SAFE_WITH_WARNING' if warnings else 'SAFE'
    else:
        status = 'UNCONFIRMED'
    return {'status': status, 'safe': status in {'SAFE','SAFE_WITH_WARNING'},
            'warning_count':len(warnings), 'warnings':warnings,
            'diagnostic_interleaved':bool(warnings), 'normalized_excerpt':normalized[-240:]}


def _safe_response(segment: str) -> bool:
    return bool(_safe_diagnostic(segment)['safe'])

def _diagnostic_tail(log:Path,limit:int=2500) -> str:
    try:return log.read_text(encoding='utf-8',errors='replace')[-limit:]
    except OSError:return 'log unreadable'

def _streaming_preflight(exe:Path,wd:Path,seed:Path,priv:dict,cal:dict,ad:dict) -> dict:
    """Validate actual streaming CLI and one real go quantum BEFORE 271-condition run.

    Unlike install (file-fed CLI), the adaptive campaign depends on keeping
    KnotPlot alive and accepting commands from a persistent stdin pipe.
    A process with a successful install check may still fail here.
    """
    from experiment.metrics import read_xyz
    result_dir=ROOT/'private/stream_preflight'
    if result_dir.exists():shutil.rmtree(result_dir)
    result_dir.mkdir(parents=True)
    log=result_dir/'stream_probe.log';a=result_dir/'initial.txt';b=result_dir/'after_go.txt'
    sw=cal['resolved_sectors']['R1'];p=priv['axes']['S2']['parameter'];v=float(cal['defaults'][p])
    kp=None;result={'schema':'A058-STREAM-PREFLIGHT-1','status':'FAIL','reason':'not started','iterations_verified':False,'safe_verified':False,'before_export_ok':False,'after_export_ok':False,'log':str(log)}
    try:
        kp=KP(exe,wd,log)
        kp.send('reset all','collision fast',f'load {seed.resolve().as_posix()}',f'{sw} = on',f'{p} = {v:.17g}',
                'echo A058_STREAM_START_BEGIN','safe','echo A058_STREAM_START_END',f'save {a.resolve().as_posix()} ascii')
        x0=_wait_file(a,None,float(ad['per_block_timeout_seconds']));result['before_export_ok']=len(x0)==300
        segment=_wait_log_section(log,'A058_STREAM_START_BEGIN','A058_STREAM_START_END',timeout=20.0)
        result['safe_response_excerpt']=segment[-500:];result['safety_diagnostic']=_safe_diagnostic(segment);result['safe_verified']=result['safety_diagnostic']['safe']
        if not result['safe_verified']:
            raise RuntimeError('KnotPlot streaming safety check was '+result['safety_diagnostic']['status']+'; inspect private segment')
        q=int(ad['quantum_iterations'])
        kp.send(f'go {q}','echo A058_STREAM_ITER_BEGIN','parameters','echo A058_STREAM_ITER_END',f'save {b.resolve().as_posix()} ascii')
        x1=_wait_file(b,None,float(ad['per_block_timeout_seconds']));result['after_export_ok']=len(x1)==300
        seg=_wait_log_section(log,'A058_STREAM_ITER_BEGIN','A058_STREAM_ITER_END',timeout=20.0)
        result['iteration_response_excerpt']=seg[-700:]
        observed=_all_params(seg).get('iteration')
        result['observed_iteration']=observed
        result['iterations_verified']=isinstance(observed,(float,int)) and int(round(float(observed)))>=q
        if not result['iterations_verified']:
            raise RuntimeError(f'go {q} not confirmed by streamed runtime iteration counter; got {observed!r}')
        if 'unknown command' in _diagnostic_tail(log).casefold():
            raise RuntimeError('unknown command in streaming log')
        rc=kp.close();kp=None;result['returncode']=rc
        if rc!=0:raise RuntimeError(f'KnotPlot streamed process exit={rc}')
        result.update({'status':'PASS','reason':'streamed SAFE status (possibly interleaved with projection diagnostics) + go quantum + second ASCII export confirmed'})
    except Exception as exc:
        result['reason']=f'{type(exc).__name__}: {exc}'
    finally:
        if kp is not None:kp.kill()
    (result_dir/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if result['status']!='PASS':
        print('STREAM PREFLIGHT FAIL: '+result['reason'],file=sys.stderr)
        print('Inspect '+str(log)+' and '+str(result_dir/'result.json'),file=sys.stderr)
        print('Diagnostic stdout retained in PRIVATE logfile; not echoed to preserve blindness.',file=sys.stderr)
    else:print('STREAM PREFLIGHT PASS: safe shared seed, streamed go quantum, iteration and coordinate export')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tier',choices=['pilot'],default='pilot');ap.add_argument('--exe',default='');ap.add_argument('--workdir',default='');ap.add_argument('--resume',action='store_true');ap.add_argument('--preflight-only',action='store_true');a=ap.parse_args()
    cfg=json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8'));priv=json.loads((ROOT/'private/axis_map.json').read_text(encoding='utf-8'));cal=json.loads((ROOT/'private/install_test_runtime/defaults.json').read_text(encoding='utf-8'));man=json.loads((ROOT/'campaign/manifest_pilot.json').read_text(encoding='utf-8'))
    exe,es=resolve_exe(a.exe);wd,ws=resolve_workdir(a.workdir)
    if exe is None or not exe.is_file():raise SystemExit('KnotPlot executable not found')
    if not wd.is_dir():raise SystemExit(f'KnotPlot Start In directory not found: {wd}')
    if _sha256(exe)!=cal.get('executable_sha256'):
        raise SystemExit('EXECUTABLE PROVENANCE FAIL: campaign KnotPlot executable differs from install-qualified executable')
    defaults=cal['defaults'];resolved=cal['resolved_sectors'];ad=cfg['adaptive_relaxation'];rows=[];top=priv['topology']['T00'];
    seed=ROOT/'private/install_test_runtime/trefoil_install_test.txt'; seedinfo=cal.get('shared_seed',{});
    if not seed.is_file() or not seedinfo or _sha256(seed)!=seedinfo.get('sha256'):
        raise SystemExit('SHARED SEED INTEGRITY FAIL: missing or changed install-qualified safe-seed bytes; rerun install before campaign')
    if len(read_xyz(seed))!=int(top['baseline_n']):
        raise SystemExit('SHARED SEED INTEGRITY FAIL: bead count differs from frozen design')
    check=_streaming_preflight(exe,wd,seed,priv,cal,ad)
    if check['status']!='PASS':return 2
    if a.preflight_only:return 0

    runtime={'schema':'A058-KNOTPLOT-RUNTIME-7','tier':'pilot','executable':str(exe),'executable_source':es,'executable_sha256':_sha256(exe),'executable_bytes':exe.stat().st_size,'working_directory':str(wd),'working_directory_source':ws,'regime':cfg['regime'],'install_calibration_schema':cal.get('schema'),'shared_seed_sha256':seedinfo.get('sha256'),'shared_seed_normalization_factor':seedinfo.get('target_over_close_default')}
    (ROOT/'campaign/runtime_pilot.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    workroot=ROOT/'private/adaptive_work';workroot.mkdir(parents=True,exist_ok=True);total=len(man['conditions'])
    for idx,c in enumerate(man['conditions'],1):
        cid=c['condition_id'];rdir=ROOT/'campaign/results'/cid;rdir.mkdir(parents=True,exist_ok=True);final=rdir/'final.txt';tracep=rdir/'convergence_trace.json'
        if a.resume and final.is_file() and final.stat().st_size>0 and tracep.is_file():print(f'[{idx}/{total}] {cid} SKIP');continue
        wdir=workroot/cid
        if wdir.exists():shutil.rmtree(wdir)
        wdir.mkdir(parents=True);log=ROOT/'private/campaign_logs/pilot'/f'{cid}.log';kp=None;trace=[];converged=False;iteration=0;sector_switch=resolved[c['sector_id']]
        try:
            kp=KP(exe,wd,log);initial=wdir/'initial.txt';lines=['reset all','collision fast',f'load {seed.resolve().as_posix()}',f'{sector_switch} = on']
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
            # Verify that this condition's actual loaded shared seed remains safe
            # after force-sector initialization BEFORE running any relaxation.
            limit=time.time()+min(float(ad['per_block_timeout_seconds']),30.0)
            start_segment=''
            while time.time()<limit:
                current_log=log.read_text(encoding='utf-8',errors='replace')
                start_segment=_segment(current_log,'A058_START_SAFE_BEGIN','A058_START_SAFE_END')
                if start_segment:break
                time.sleep(0.05)
            start_diagnostic=_safe_diagnostic(start_segment)
            if not start_diagnostic['safe']:
                raise RuntimeError('shared seed safety '+start_diagnostic['status']+' after streamed reload; no relaxation performed')
            while iteration < int(ad['max_iterations_safety_cap']):
                probe=wdir/f'probe_{iteration+int(ad["quantum_iterations"]):06d}.txt';kp.send(f'go {int(ad["quantum_iterations"])}',f'save {probe.resolve().as_posix()} ascii');cur=_wait_file(probe,None,ad['per_block_timeout_seconds']);iteration += int(ad['quantum_iterations']);sd=float(shape_distance(prev,cur,m=128));sc=float(_scalar_delta(prev,cur));trace.append({'iteration':iteration,'shape_delta':sd,'scalar_delta':sc});prev=cur
                if iteration>=int(ad['minimum_iterations']) and sd<=float(ad['shape_delta_threshold']) and sc<=float(ad['scalar_delta_threshold']):stable+=1
                else:stable=0
                if stable>=int(ad['stable_windows_required']):converged=True;break
                try:probe.unlink()
                except Exception:pass
            kp.send(f'save {final.resolve().as_posix()} ascii','echo A058_FINAL_SAFE_BEGIN','safe','echo A058_FINAL_SAFE_END','echo A058_FINAL_STATE_BEGIN','parameters','echo A058_FINAL_STATE_END','dowker');_wait_file(final,None,ad['per_block_timeout_seconds']);rc=kp.close();kp=None
            txt=log.read_text(encoding='utf-8',errors='replace');unknown='unknown command' in txt.casefold();start_diagnostic=_safe_diagnostic(_segment(txt,'A058_START_SAFE_BEGIN','A058_START_SAFE_END'));final_diagnostic=_safe_diagnostic(_segment(txt,'A058_FINAL_SAFE_BEGIN','A058_FINAL_SAFE_END'));safe_start=start_diagnostic['safe'];safe_final=final_diagnostic['safe']
            start_ok,start_detail=_state_ok(txt,c,priv,cal,'A058_PARAMETER_STATE_BEGIN','A058_PARAMETER_STATE_END');final_ok,final_detail=_state_ok(txt,c,priv,cal,'A058_FINAL_STATE_BEGIN','A058_FINAL_STATE_END');state_ok=start_ok and final_ok and not unknown
            status='PASS' if rc==0 and state_ok and safe_start and safe_final and final.is_file() else 'FAIL';reason='' if status=='PASS' else f'rc={rc}, unknown={unknown}, state_start={start_ok}, state_final={final_ok}, safe_start={safe_start}, safe_final={safe_final}'
            row={'condition_id':cid,'role':c['role'],'reference_id':c['reference_id'],'axis_id':axis_id,'multiplier':c['multiplier'],'returncode':rc,'status':status,'reason':reason,'converged':converged,'iterations':iteration,'safety_cap_hit':not converged,'unknown_command':unknown,'parameter_state_verified':state_ok,'parameter_state_start':start_detail,'parameter_state_final':final_detail,'safe_start_verified':safe_start,'safe_final_verified':safe_final,'safety_start_status':start_diagnostic['status'],'safety_final_status':final_diagnostic['status'],'safety_warnings':start_diagnostic['warning_count']+final_diagnostic['warning_count'],'final_sha256':_sha256(final) if final.is_file() else None,'trace_points':len(trace),'shared_seed_sha256':seedinfo.get('sha256')}
        except Exception as e:
            if kp is not None:kp.kill()
            row={'condition_id':cid,'role':c['role'],'reference_id':c['reference_id'],'axis_id':c.get('axis_id'),'multiplier':c['multiplier'],'returncode':None,'status':'FAIL','reason':f'{type(e).__name__}: {e}','converged':False,'iterations':iteration,'safety_cap_hit':False,'unknown_command':None,'parameter_state_verified':False,'safe_start_verified':False,'safe_final_verified':False,'final_sha256':None,'trace_points':len(trace),'shared_seed_sha256':seedinfo.get('sha256')}
        tracep.write_text(json.dumps({'schema':'A058-CONVERGENCE-TRACE-7','condition_id':cid,'converged':row['converged'],'iterations':row['iterations'],'trace':trace},indent=2,sort_keys=True)+'\n',encoding='utf-8');rows.append(row);print(f'[{idx}/{total}] {cid} {c["role"]} {c.get("axis_id") or c["reference_id"]} m={c["multiplier"]:.9g} -> {row["status"]} converged={row["converged"]} iter={row["iterations"]}')
        if idx<=7 and row['status']=='FAIL' and row['iterations']==0:
            partial={'schema':'A058-RUNLOG-7','conditions':rows,'count':len(rows),'aborted_early':True,'abort_reason':'first reference/control condition failed before first go; inspect private campaign log'}
            (ROOT/'campaign/runlog_pilot.json').write_text(json.dumps(partial,indent=2,sort_keys=True)+'\n',encoding='utf-8')
            print('ACQUISITION FAIL-FAST: early reference/control at iteration 0; campaign stopped to protect time. Inspect '+str(log),file=sys.stderr)
            print('REASON: '+row['reason'],file=sys.stderr)
            print('Diagnostic stdout retained in PRIVATE logfile; not echoed to preserve blindness.',file=sys.stderr)
            return 3
    payload={'schema':'A058-RUNLOG-7','conditions':rows,'count':len(rows)};(ROOT/'campaign/runlog_pilot.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(f'Complete: {len(rows)} attempted; failures={sum(r["status"]!="PASS" for r in rows)}; nonconverged={sum(not r["converged"] for r in rows)}')
    return 0 if all(r['status']=='PASS' for r in rows) else 4
if __name__=='__main__':raise SystemExit(main())
