"""A075 non-scientific progress telemetry. Does not change fluid state or gates.

Writes outside the framework's audited output tree to avoid immutable-manifest races.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json, os, threading, time

_lock=threading.RLock()
_active=None

def _stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def _seconds(x):
    if x is None:return 'unknown'
    x=max(0,int(x))
    if x>=3600:return f'{x//3600}h{(x%3600)//60:02d}m'
    if x>=60:return f'{x//60}m{x%60:02d}s'
    return f'{x}s'

class Monitor:
    def __init__(self,root,mode,interval=10.):
        self.root=Path(root).resolve();self.folder=self.root/'run_status'
        self.folder.mkdir(parents=True,exist_ok=True)
        self.path=self.folder/'heartbeat.json';self.interval=float(interval)
        self.start_mono=time.monotonic();self.phase_mono=self.start_mono
        self.last_step_mono=None;self.stop_flag=threading.Event()
        self.state={'schema':'A075-HEARTBEAT-1','version':'v0.2.8','pid':os.getpid(),
          'started_utc':_stamp(),'updated_utc':_stamp(),'mode':mode,'state':'RUNNING',
          'phase':'startup','phase_index':None,'phase_total':None,'phase_progress_pct':None,'phase_eta_seconds':None,
          'estimate':'phase_only_provisional_not_whole_run','step':0,'accepted_t':None,
          'physical_end_time':None,'grid':None,'backend':None,'knot':None,'last_dt':None,
          'rejected_steps_total':0,'message':'Starting; heartbeat reports liveness even before first accepted step'}
        self._persist();self.worker=threading.Thread(target=self._loop,daemon=True,name='a075-heartbeat');self.worker.start()
        self._announce()
    def _persist(self):
        self.state['updated_utc']=_stamp()
        tmp=self.folder/f'.heartbeat.{os.getpid()}.tmp'
        tmp.write_text(json.dumps(self.state,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        os.replace(tmp,self.path)
    def phase(self,name,*,backend=None,knot=None,grid=None,physical_end_time=None,message=None,phase_index=None,phase_total=None):
        with _lock:
            self.phase_mono=time.monotonic();self.last_step_mono=None
            self.state.update(phase=str(name),backend=backend,knot=knot,grid=grid,phase_index=phase_index,phase_total=phase_total,
                physical_end_time=physical_end_time,accepted_t=0. if physical_end_time else None,
                step=0,last_dt=None,phase_progress_pct=0. if physical_end_time else None,
                phase_eta_seconds=None,rejected_steps_total=0,
                message=message or 'Phase running; adaptive time-step progress is measured in physical time')
            self._persist()
        self._announce()
    def advance(self,step,t,T,dt,rejected=0):
        with _lock:
            now=time.monotonic();self.last_step_mono=now
            f=max(0.,min(1.,float(t)/float(T))) if T>0 else 0.
            elapsed=now-self.phase_mono
            # Provisional ETA for current phase only; avoid extrapolation from startup transients.
            eta=elapsed*(1-f)/f if f>=.05 and step>=3 else None
            self.state.update(step=int(step),accepted_t=float(t),physical_end_time=float(T),
                last_dt=float(dt),phase_progress_pct=round(f*100,2),
                phase_eta_seconds=round(eta,1) if eta is not None else None,
                rejected_steps_total=int(self.state['rejected_steps_total'])+int(rejected))
    def _announce(self):
        with _lock:
            s=dict(self.state);last=self.last_step_mono
            now=time.monotonic();s['elapsed_wall_seconds']=round(now-self.start_mono,2)
            s['phase_wall_seconds']=round(now-self.phase_mono,2)
            s['seconds_since_accepted_step']=round(now-last,2) if last is not None else None
            # Persist periodically, even when RK step blocks or the GPU is busy.
            self.state.update(elapsed_wall_seconds=s['elapsed_wall_seconds'],
                 phase_wall_seconds=s['phase_wall_seconds'],
                 seconds_since_accepted_step=s['seconds_since_accepted_step'])
            try:self._persist()
            except OSError:pass
        percent=(f"{s['phase_progress_pct']:.1f}%" if s.get('phase_progress_pct') is not None else 'unknown')
        position=(f"{s['phase_index']}/{s['phase_total']}" if s.get('phase_index') and s.get('phase_total') else '?')
        caution=(' no-step-yet' if last is None else
            (' no-recent-accepted-step' if s['seconds_since_accepted_step']>max(60,3*self.interval) else ''))
        print(f"[A075 HEARTBEAT {_stamp()}] state={s['state']} phase={s['phase']} stage={position} backend={s.get('backend') or '-'} knot={s.get('knot') or '-'} grid={s.get('grid') or '-'} progress={percent} t={s.get('accepted_t')} / {s.get('physical_end_time')} steps={s['step']} phase-ETA~{_seconds(s.get('phase_eta_seconds'))} elapsed={_seconds(s['elapsed_wall_seconds'])}{caution}",flush=True)
    def _loop(self):
        while not self.stop_flag.wait(self.interval):self._announce()
    def finish(self,code=0,reason=None):
        with _lock:
            self.state['state']='COMPLETED' if code==0 else 'BLOCKED_OR_FAILED'
            self.state['exit_code']=int(code)
            self.state['message']=reason or ('Process completed' if code==0 else 'Nonzero exit: inspect framework gate ledger / console log')
        self.stop_flag.set();self.worker.join(timeout=2);self._announce()

def start(root,mode,interval=10.):
    global _active
    if interval<=0:raise ValueError('Heartbeat interval must be positive')
    with _lock:
        _active=Monitor(root,mode,interval)
    return _active

def phase(name,**kwargs):
    if _active is not None:_active.phase(name,**kwargs)

def advance(step,t,T,dt,rejected=0):
    if _active is not None:_active.advance(step,t,T,dt,rejected)

def finish(code=0,reason=None):
    global _active
    if _active is not None:
        _active.finish(code,reason);_active=None

def status(root):
    path=Path(root)/'run_status'/'heartbeat.json'
    if not path.is_file():return {'state':'NO_HEARTBEAT','reason':'No instrumented A075-v0.2.6 run has started','path':str(path)}
    try:
        s=json.loads(path.read_text(encoding='utf-8'))
        modified_age=max(0.,time.time()-path.stat().st_mtime)
        s['heartbeat_file_age_seconds']=round(modified_age,1)
        if s.get('state')=='RUNNING' and modified_age>60:
            s['observation']='STALE_TELEMETRY: may be hung or process gone; check process separately'
        return s
    except (OSError,ValueError) as exc:return {'state':'HEARTBEAT_UNREADABLE','error':str(exc)}
