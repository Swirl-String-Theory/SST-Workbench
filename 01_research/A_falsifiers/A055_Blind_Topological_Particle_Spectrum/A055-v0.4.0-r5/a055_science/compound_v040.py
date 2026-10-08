from __future__ import annotations
from pathlib import Path
import numpy as np
from .util import read_json
from .upstream import verify_a054_seal,import_a054_runner
from .chirality import analyze_circulation_relative_modes,sector_bias_qualified,metamorphic_errors,analytic_covariance_selftest
from .traveling import eigenvalue_multiset_relative_error,reconstruct_field


def _stored_complex(rows): return np.asarray([complex(float(x['re']),float(x['im'])) for x in rows],complex)

def _level(comps,gammas,core,mi,eps,backend,cert,cfg):
    J=cert.projected_jacobian(comps,gammas,core,mi,float(eps),backend); vals,vecs=np.linalg.eig(J)
    s=analyze_circulation_relative_modes(vals,vecs,mi['basis'],comps,gammas,families=mi.get('families'),harmonics=tuple(cfg['harmonics']),
       relative_imag_floor=float(cfg['relative_imag_floor']),min_kelvin_basis_fraction=float(cfg['min_kelvin_basis_fraction']),
       min_harmonic_participation=float(cfg['min_harmonic_participation']),min_circulation_relative_purity=float(cfg['min_circulation_relative_purity']),max_re_over_im=float(cfg['max_re_over_im']))
    return J,vals,vecs,s

def recompute_compound_chirality(campaign:Path,cfg:dict):
    campaign=Path(campaign); seal=verify_a054_seal(campaign); manifest=read_json(campaign/'BLIND_MANIFEST.json'); ccfg=read_json(campaign/'CERT_CONFIG.json')
    results=read_json(campaign/'CERT_RESULTS_BLIND.json'); analysis=read_json(campaign/'CERT_ANALYSIS_BLIND.json'); runner=import_a054_runner(campaign)
    cert,geom,phys,modes=runner['certify'],runner['geometry'],runner['physics'],runner['modes']; sealed_backend=read_json(campaign/'BACKEND_QUALIFICATION.json').get('backend'); actual=phys.backend_name()
    if cfg.get('require_a054_backend_match',True) and actual!=sealed_backend: raise RuntimeError(f"A054 backend mismatch: sealed={sealed_backend}, actual={actual}, native_probe={runner.get('native_probe')}")
    backend=sealed_backend if cfg.get('require_a054_backend_match',True) else actual
    sealed_ladder=sorted(int(x) for x in ccfg['n_ladder']); ladder=sorted(int(x) for x in (cfg.get('resolution_ladder') or sealed_ladder)); epsvals=[float(x) for x in (cfg.get('epsilon_values') or ccfg['jacobian_eps_values'])]
    if any(n not in sealed_ladder for n in ladder): raise ValueError('resolution_ladder must be a subset of sealed A054 ladder')
    fine=max(sealed_ladder); fine_by={(r['anonymous_id'],r['sector']):r for r in results['results'] if r.get('N')==fine}
    cand=list(manifest['candidates']); limit=cfg.get('candidate_limit'); cand=cand if limit is None else cand[:int(limit)]; sectors=list(cfg.get('sectors') or ccfg['circulation_sectors'])
    rows=[]; parity=[]; metaerrs=[]
    for row in cand:
        base=geom.load_components_npz(campaign/'blind_inputs'/row['file']); per_sector=[]
        for sec in sectors:
            levels=[]; gammas=phys.circulation_vector(3,sec); fine_alt=None
            for N in ladder:
                comps=[geom.resample_closed_curve(c,N) for c in base]; total_L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in comps); core=float(ccfg['core_ratio'])*total_L
                mi=modes.build_mode_basis(comps,tuple(ccfg['kelvin_harmonics']),True,True); eps=epsvals[-1]
                J,vals,vecs,s=_level(comps,gammas,core,mi,eps,backend,cert,cfg)
                err=None
                if N==fine:
                    stored=fine_by[(row['anonymous_id'],sec)]; err=eigenvalue_multiset_relative_error(vals,_stored_complex((stored.get('spectrum') or {}).get('eigenvalues',[]))); parity.append(err)
                    if len(epsvals)>1:
                        _J2,v2,e2,s2=_level(comps,gammas,core,mi,epsvals[0],backend,cert,cfg); fine_alt={'epsilon':epsvals[0],'summary':s2}
                    q=[m for m in s['modes'] if m['qualifies']]
                    for m in sorted(q,key=lambda x:(-x['harmonic_participation'],-abs(x['circulation_relative_purity'])))[:int(cfg['metamorphic_modes_per_sector'])]:
                        field=reconstruct_field(vecs[:,m['eigen_index']],mi['basis']); me=metamorphic_errors(field,comps,gammas,m['dominant_harmonic']); metaerrs.append(me['max_abs_error'])
                levels.append({'N':N,'epsilon':eps,'summary':s,'sealed_spectrum_assignment_relative_error':err})
            # aggregate convergence of the directional bias; no branch identity claim
            qflags=[sector_bias_qualified(x['summary'],cfg['min_qualified_modes_per_sector'],cfg['min_sector_vote_bias']) for x in levels]
            signs=[]
            for x in levels:
                b=float(x['summary']['sector_vote_bias']); signs.append(0 if abs(b)<1e-15 else (1 if b>0 else -1))
            res_stable=bool(all(qflags) and len(set(signs))==1 and signs[0]!=0)
            eps_stable=True
            if fine_alt is not None:
                main=levels[-1]['summary']; alt=fine_alt['summary']; qm=sector_bias_qualified(main,cfg['min_qualified_modes_per_sector'],cfg['min_sector_vote_bias']); qa=sector_bias_qualified(alt,cfg['min_qualified_modes_per_sector'],cfg['min_sector_vote_bias'])
                sm=0 if abs(main['sector_vote_bias'])<1e-15 else (1 if main['sector_vote_bias']>0 else -1); sa=0 if abs(alt['sector_vote_bias'])<1e-15 else (1 if alt['sector_vote_bias']>0 else -1)
                eps_stable=bool(qm and qa and sm==sa and sm!=0)
            stable=bool(res_stable and eps_stable); sign=signs[-1] if stable else 0
            stored=fine_by[(row['anonymous_id'],sec)]; bs=(analysis.get('summaries',{}).get(row['anonymous_id'],{}).get('sectors',{}).get(sec,{}) or {}); rpo=stored.get('rpo') or {}
            per_sector.append({'anonymous_id':row['anonymous_id'],'sector':sec,'levels':levels,'fine_epsilon_alternate':fine_alt,
                'resolution_stable_directional_bias':res_stable,'epsilon_stable_directional_bias':eps_stable,'robust_chiral_sector':stable,'robust_direction':sign,
                'spatial_converged':bs.get('spatial_converged'),'upstream_rpo_accepted':bool(rpo.get('accepted',False)),'stored_status':bs.get('status')})
        rows.extend(per_sector)
    by={}
    for r in rows: by.setdefault(r['anonymous_id'],[]).append(r)
    summaries=[]; rmin=int(cfg['robust_sector_count_min'])
    for aid,rr in sorted(by.items()):
        stable=[x for x in rr if x['robust_chiral_sector']]; plus=sum(x['robust_direction']>0 for x in stable); minus=sum(x['robust_direction']<0 for x in stable); same=max(plus,minus)
        robust=bool(same>=rmin); promoted=sum(bool(x['robust_chiral_sector'] and x['spatial_converged'] and x['upstream_rpo_accepted']) for x in rr)
        summaries.append({'anonymous_id':aid,'evaluated_sector_count':len(rr),'robust_chiral_sector_count':len(stable),'positive_robust_sector_count':plus,'negative_robust_sector_count':minus,
                          'robust_same_direction_sector_count':same,'robust_chiral_candidate':robust,'mechanism_promoted_sector_count':promoted})
    selftest=analytic_covariance_selftest(); maxmeta=max(metaerrs) if metaerrs else 0.0; maxpar=max(parity) if parity else float('inf')
    return {'schema':'A055-CHIRAL-COVARIANCE-BLIND-040','source_campaign':str(campaign),'source_seal':seal,'config':cfg,'a054_sealed_backend':sealed_backend,'a054_actual_backend':actual,
            'resolution_ladder':ladder,'epsilon_values':epsvals,'analytic_covariance_selftest':selftest,'max_metamorphic_abs_error':float(maxmeta),
            'max_recompute_eigenvalue_assignment_relative_error':float(maxpar),'rows':rows,'candidate_summaries':summaries,
            'robust_candidate_count':sum(x['robust_chiral_candidate'] for x in summaries),'mechanism_promoted_sector_count':sum(x['mechanism_promoted_sector_count'] for x in summaries)}
