from __future__ import annotations
import math, numpy as np
from .geometry import normalize, sample_spline, local_metrics, tangent_unit, polygon_length
from .nonlocal_metrics import min_nonlocal_segment_distance, approximate_dcsd, writhe_acn, linking_number, min_intercomponent_segment_distance
from .convergence import classify_metric_table

METRICS=('L','kappa_max','kappa_rms','sigma_kappa','tau_rms','Wr','ACN','d_min','dcsd','reach','Thi','Rop','ropelength_reach')

def qualify_components(components, config, reference_observables=None):
    comps=[np.asarray(c,float) for c in components]
    native_component_lengths=[polygon_length(c) for c in comps]
    native_total_length=float(sum(native_component_lengths))
    scale=1.0
    if config.normalize_length is not None:
        total=native_total_length
        scale=float(config.normalize_length)/total
        # Translation must be COMMON to every component. Centering each component
        # independently destroys a link's relative placement, inter-component
        # distances and linking geometry (e.g. it collapses the Hopf component centres).
        origin=np.vstack(comps).mean(axis=0)
        comps=[(c-origin)*scale for c in comps]
    levels=[]
    for N in config.resolution_ladder:
        per=[]; sampled=[]
        for c in comps:
            s=sample_spline(c,N); sampled.append(s); m=local_metrics(s)
            t=tangent_unit(s['tangent_raw'])
            exclusion=max(2,int(round(config.nonlocal_exclusion_fraction*N)))
            if config.expensive_metrics:
                dmin=min_nonlocal_segment_distance(s['points'],exclusion)
                dcs=approximate_dcsd(s['points'],t,exclusion,config.dcs_orthogonality_tol)
                wr,acn=writhe_acn(s['points'])
            else:
                dmin=dcs=wr=acn=None
            kmax=m['kappa_max']; rho=(1.0/kmax if kmax and kmax>0 else None)
            candidates=[x for x in (rho,0.5*dcs if dcs is not None and math.isfinite(dcs) else None) if x is not None and math.isfinite(x)]
            reach=min(candidates) if candidates else None
            thi=(2.0*reach if reach is not None else None)
            m['sigma_kappa']=m.get('kappa_std')
            m.update({'Wr':wr,'ACN':acn,'d_min':dmin,'dcsd':dcs if dcs is not None and math.isfinite(dcs) else None,
                      'reach':reach,'Thi':thi,'thickness':thi,
                      'Rop':(m['L']/thi if thi and thi>0 else None),
                      'ropelength':(m['L']/thi if thi and thi>0 else None),
                      'ropelength_reach':(m['L']/reach if reach and reach>0 else None),
                      'curvature_radius_min':rho})
            per.append(m)
        # aggregate link metrics conservatively: sum length/ACN, sum writhe components; thickness constrained globally.
        metrics={}
        for key in ('L','ACN','Wr'):
            vals=[m.get(key) for m in per]
            metrics[key]=sum(v for v in vals if v is not None) if all(v is not None for v in vals) else None
        for key in ('kappa_max',): metrics[key]=max((m[key] for m in per if m[key] is not None),default=None)
        for key in ('kappa_rms','kappa_std','tau_rms'):
            metrics[key]=float(np.sqrt(np.mean([m[key]**2 for m in per if m[key] is not None]))) if any(m[key] is not None for m in per) else None
        metrics['sigma_kappa']=metrics.get('kappa_std')
        self_d=[m.get('d_min') for m in per if m.get('d_min') is not None]
        inter=[]; lk=[]
        if config.expensive_metrics and len(sampled)>1:
            for i in range(len(sampled)):
                for j in range(i+1,len(sampled)):
                    inter.append(min_intercomponent_segment_distance(sampled[i]['points'],sampled[j]['points']))
                    lk.append({'i':i,'j':j,'Lk':linking_number(sampled[i]['points'],sampled[j]['points'])})
        metrics['d_min']=min(self_d+inter) if self_d or inter else None
        dcsvals=[m.get('dcsd') for m in per if m.get('dcsd') is not None]
        metrics['dcsd']=min(dcsvals) if dcsvals else None
        reach_candidates=[m.get('reach') for m in per if m.get('reach') is not None]
        if inter: reach_candidates += [0.5*min(inter)]
        metrics['reach']=min(reach_candidates) if reach_candidates else None
        metrics['Thi']=2.0*metrics['reach'] if metrics['reach'] is not None else None
        metrics['thickness']=metrics['Thi']
        metrics['Rop']=metrics['L']/metrics['Thi'] if metrics['Thi'] else None
        metrics['ropelength']=metrics['Rop']
        metrics['ropelength_reach']=metrics['L']/metrics['reach'] if metrics['reach'] else None
        levels.append({'resolution':int(N),'metrics':metrics,'component_metrics':per,'linking_matrix_entries':lk,'intercomponent_dmin':min(inter) if inter else None})
    conv=classify_metric_table(levels,METRICS,resolved_tol=config.resolved_rel_tol,converging_tol=config.converging_rel_tol,min_levels=config.min_levels_for_resolution)
    overall='RESOLVED' if all(x['status'] in ('RESOLVED','REFERENCE_VALUE') for x in conv.values()) else ('CONVERGING' if all(x['status'] in ('RESOLVED','CONVERGING','REFERENCE_VALUE') for x in conv.values()) else 'UNRESOLVED')
    refs=dict(reference_observables or {})
    for _name,_entry in refs.items():
        if isinstance(_entry,dict): _entry.setdefault('status','REFERENCE_VALUE')
    return {'scale_context':{'native_total_length':native_total_length,'native_component_lengths':native_component_lengths,'normalization_target_total_length':config.normalize_length,'normalization_scale':scale,'guard':'Native coordinate units are source-specific. Cross-source shape comparison uses one common translation plus the declared global total-length scale; relative placement of link components is preserved. Ropelength and Wr are scale-invariant.'},'method':{
       'centerline_reconstruction':'periodic cubic spline through native source polygon',
       'reach':'radius convention: min(min curvature radius, 0.5 numerical doubly-critical self-distance); links additionally constrained by 0.5 inter-component separation; numerical estimate, not analytic certificate',
       'thickness':'PKLSA/KnotPlot diameter convention Thi = 2*reach, so Rop=L/Thi is directly comparable to Gilbert/KnotPlot D=1 length references; `thickness` is an alias of `Thi`',
       'ropelength_conventions':'ropelength=L/Thi (diameter convention requested by PKLSA); ropelength_reach=L/reach is also emitted for radius-convention literature comparisons',
       'writhe_acn':'Gauss double integral midpoint quadrature over polygonal samples; convergence ladder mandatory'
    },'levels':levels,'convergence':conv,'reference_observables':refs,'overall_convergence':overall}
