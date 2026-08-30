from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import datetime as _dt
import math
import time


def _fmt_seconds(seconds):
    if seconds is None or not math.isfinite(float(seconds)) or seconds < 0:
        return '--:--:--'
    n=int(round(float(seconds)));h,n=divmod(n,3600);m,s=divmod(n,60)
    if h>=100: return f'{h:d}:{m:02d}:{s:02d}'
    return f'{h:02d}:{m:02d}:{s:02d}'


def _stamp():
    return _dt.datetime.now().astimezone().isoformat(timespec='seconds')

@dataclass
class BranchProgress:
    branch: str
    total: int
    log_path: Path
    start_monotonic: float = 0.0
    completed_wall_seconds: float = 0.0
    completed_planned_steps: int = 0
    completed_count: int = 0

    def __post_init__(self):
        self.start_monotonic=time.monotonic()
        self.log_path=Path(self.log_path);self.log_path.parent.mkdir(parents=True,exist_ok=True)
        self._write(f'[{_stamp()}] BEGIN branch={self.branch} total={self.total}')

    def _write(self,msg):
        print(msg,flush=True)
        with self.log_path.open('a',encoding='utf-8',newline='\n') as f:f.write(msg+'\n')

    def branch_elapsed(self): return time.monotonic()-self.start_monotonic

    def _sec_per_step(self):
        if self.completed_planned_steps<=0:return None
        return self.completed_wall_seconds/self.completed_planned_steps

    def estimate_branch_remaining(self,idx,current_step=0,current_planned_steps=0):
        sps=self._sec_per_step()
        if sps is None:
            if self.completed_count<=0:return None
            avg=self.completed_wall_seconds/self.completed_count
            return max(0,self.total-(idx-1))*avg
        remaining_current=max(0,int(current_planned_steps)-int(current_step))
        # Future candidates do not all have identical step counts. Use completed
        # average planned steps per candidate as a deliberately rough forecast.
        avg_steps=self.completed_planned_steps/max(1,self.completed_count)
        future=max(0,self.total-idx)*avg_steps
        return (remaining_current+future)*sps

    def start_candidate(self,idx,candidate,carrier,arm,components,planned_steps,out_name):
        pct=100.0*(idx-1)/max(1,self.total)
        eta=self.estimate_branch_remaining(idx,0,planned_steps)
        self._write(f'[{self.branch} {idx:04d}/{self.total:04d} {pct:5.1f}%] START candidate={candidate} carrier={carrier} arm={arm} comps={components} output={out_name} planned_steps={planned_steps} branch_elapsed={_fmt_seconds(self.branch_elapsed())} ETA~{_fmt_seconds(eta)}')
        return time.monotonic()

    def heartbeat(self,idx,candidate,candidate_start,step,planned_steps,sim_t,target_t):
        frac=float(step)/max(1,int(planned_steps));pct=100.0*((idx-1)+frac)/max(1,self.total)
        cel=time.monotonic()-candidate_start;cur_eta=(cel/max(frac,1e-12)-cel) if frac>0 else None
        beta=self.estimate_branch_remaining(idx,step,planned_steps)
        self._write(f'[{self.branch} {idx:04d}/{self.total:04d} {pct:5.1f}%] RUN candidate={candidate} step={int(step)}/{int(planned_steps)} sim_t={float(sim_t):.4g}/{float(target_t):.4g} candidate_elapsed={_fmt_seconds(cel)} candidate_ETA~{_fmt_seconds(cur_eta)} branch_elapsed={_fmt_seconds(self.branch_elapsed())} branch_ETA~{_fmt_seconds(beta)}')

    def done_candidate(self,idx,candidate,candidate_start,planned_steps,details):
        wall=time.monotonic()-candidate_start;self.completed_count+=1;self.completed_wall_seconds+=wall;self.completed_planned_steps+=max(1,int(planned_steps))
        pct=100.0*idx/max(1,self.total);eta=self.estimate_branch_remaining(idx,planned_steps,planned_steps)
        self._write(f'[{self.branch} {idx:04d}/{self.total:04d} {pct:5.1f}%] DONE candidate={candidate} wall={_fmt_seconds(wall)} branch_elapsed={_fmt_seconds(self.branch_elapsed())} ETA~{_fmt_seconds(eta)} {details}')

    def skip_candidate(self,idx,candidate,reason='existing'):
        pct=100.0*idx/max(1,self.total);self._write(f'[{self.branch} {idx:04d}/{self.total:04d} {pct:5.1f}%] SKIP candidate={candidate} reason={reason} branch_elapsed={_fmt_seconds(self.branch_elapsed())}')

    def error_candidate(self,idx,candidate,candidate_start,error):
        wall=time.monotonic()-candidate_start;self._write(f'[{self.branch} {idx:04d}/{self.total:04d}] ERROR candidate={candidate} wall={_fmt_seconds(wall)} branch_elapsed={_fmt_seconds(self.branch_elapsed())} error={error!r}')

    def finish(self,done,errors,skipped):
        self._write(f'[{_stamp()}] END branch={self.branch} done={done} errors={errors} skipped_existing={skipped} elapsed={_fmt_seconds(self.branch_elapsed())}')
