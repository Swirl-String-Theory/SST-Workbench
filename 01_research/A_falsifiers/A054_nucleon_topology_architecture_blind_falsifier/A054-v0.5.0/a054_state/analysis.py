from __future__ import annotations
import numpy as np
from .utils import safe_cv
from .selector import cyclic_kabsch_rmsd


def rel_span(vals):
    a=np.asarray(vals,float)
    if len(a)<2:return None
    return float((a.max()-a.min())/max(abs(a.mean()),1e-30))


def provider_convergence(rows,cfg):
    by={}
    for r in rows: by.setdefault(r['topology_id'],[]).append(r)
    details={}
    for top,rs in sorted(by.items()):
        groups={str(r.get('provider_group')) for r in rs if r.get('provider_group')}
        if len(groups)<2:
            details[top]={'eligible':False,'provider_groups':sorted(groups),'reason':'fewer_than_two_provider_groups'}; continue
        initial=[r['initial_energy'] for r in rs]; final=[r['final_energy'] for r in rs]
        final_stat=all(bool(r.get('stationary')) for r in rs)
        energy_cv=safe_cv(final); source_cv=safe_cv(initial)
        rop=[r['final_descriptors']['ropelength_proxy'] for r in rs]; wr=[abs(r['final_descriptors']['writhe_sum']) for r in rs]
        rop_span=rel_span(rop); wr_span=float(max(wr)-min(wr)) if len(wr)>=2 else None
        rmsd=None
        if len(rs)==2 and all(len(r.get('_components_for_analysis',[]))==1 for r in rs):
            try:rmsd=cyclic_kabsch_rmsd(rs[0]['_components_for_analysis'][0],rs[1]['_components_for_analysis'][0])
            except Exception:rmsd=None
        conv=bool(final_stat and energy_cv is not None and energy_cv<=float(cfg['provider_energy_cv_max']) and rop_span is not None and rop_span<=float(cfg['provider_ropelength_rel_span_max']) and wr_span is not None and wr_span<=float(cfg['provider_writhe_abs_span_max']))
        details[top]={
          'eligible':True,'provider_groups':sorted(groups),'provider_count':len(groups),'source_energy_cv':source_cv,'endpoint_energy_cv':energy_cv,
          'provider_ropelength_rel_span':rop_span,'provider_abs_writhe_span':wr_span,'cyclic_kabsch_rmsd_diagnostic':rmsd,
          'all_endpoints_stationary':final_stat,'all_endpoints_stable':all(bool(r.get('stable_candidate')) for r in rs),
          'all_ringdown_bounded':all(bool(r.get('ringdown_bounded')) for r in rs),'provider_converged':conv,
        }
        if source_cv is not None and source_cv>0:
            details[top]['provider_cv_collapse_fraction']=float(1.0-energy_cv/source_cv) if energy_cv is not None else None
    return details
