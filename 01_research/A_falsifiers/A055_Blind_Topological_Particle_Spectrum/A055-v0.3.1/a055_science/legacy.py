from __future__ import annotations
from pathlib import Path
from .util import read_json
from .upstream import verify_a055_v030_output


def summarize_legacy_controls(out:Path):
    out=Path(out); seal=verify_a055_v030_output(out)
    dyn_dir=out/'BLIND'/'dynamics'; cells={}; provider_runs=mode_reports=qualified_modes=rpo_accepted=promoted=0
    conflicts=[]
    for p in sorted(dyn_dir.glob('*.json')):
        obj=read_json(p); dyn=obj.get('dynamic') or {}
        if dyn.get('particle_promotion_qualified'): promoted+=1
        for pr in dyn.get('providers',[]):
            provider_runs+=1; pg=pr.get('provider_group')
            if pr.get('rpo',{}).get('accepted') or pr.get('rpo_accepted'): rpo_accepted+=1
            for mr in pr.get('mode_reports',[]):
                mode_reports+=1
                if mr.get('qualified'): qualified_modes+=1
                mm=mr.get('mode_m')
                for lv in mr.get('levels',[]):
                    key=(obj.get('case',{}).get('case_id'),pg,mm,lv.get('N'))
                    new={'available':True,'status':lv.get('status','OSCILLATORY_PAIR_AVAILABLE')}
                    if key in cells and cells[key]!=new: conflicts.append({'key':key,'old':cells[key],'new':new})
                    cells[key]=new
                for fail in mr.get('failures',[]):
                    key=(obj.get('case',{}).get('case_id'),pg,mm,fail.get('N'))
                    new={'available':False,'status':fail.get('status','MODE_FAIL_CLOSED')}
                    if key in cells and cells[key].get('available'):
                        conflicts.append({'key':key,'kept':cells[key],'ignored':new})
                    else: cells[key]=new
            # v0.3.0 also persisted a provider-level duplicate failure list; do not add it again.
    return {'schema':'A055-LEGACY-CONTROL-SUMMARY-031','source':str(out),'seal':seal,
            'unique_mode_resolution_cells':len(cells),'available_legacy_oscillatory_cells':sum(v['available'] for v in cells.values()),
            'unavailable_cells':sum(not v['available'] for v in cells.values()),'provider_runs':provider_runs,
            'mode_reports':mode_reports,'qualified_modes':qualified_modes,'accepted_rpo':rpo_accepted,
            'particle_promotions':promoted,'dedup_conflict_count':len(conflicts),'dedup_conflicts':conflicts[:20],
            'interpretation_guard':'Legacy sign-of-imaginary-eigenvalue availability is retained only as an implementation/control baseline and is not interpreted as physical counterpropagation.'}
