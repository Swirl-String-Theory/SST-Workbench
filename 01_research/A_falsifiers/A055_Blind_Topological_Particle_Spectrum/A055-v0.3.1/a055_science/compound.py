from __future__ import annotations
from pathlib import Path
import numpy as np
from .util import read_json
from .upstream import verify_a054_seal, import_a054_runner
from .traveling import analyze_eigensystem,eigenvalue_multiset_relative_error,analytic_selftest


def _stored_complex(rows):
    return np.asarray([complex(float(x['re']),float(x['im'])) for x in rows],complex)


def recompute_compound_signed(campaign:Path,cfg:dict):
    campaign=Path(campaign); seal=verify_a054_seal(campaign)
    manifest=read_json(campaign/'BLIND_MANIFEST.json'); ccfg=read_json(campaign/'CERT_CONFIG.json')
    results=read_json(campaign/'CERT_RESULTS_BLIND.json'); analysis=read_json(campaign/'CERT_ANALYSIS_BLIND.json')
    runner=import_a054_runner(campaign); cert=runner['certify']; geom=runner['geometry']; phys=runner['physics']; modes=runner['modes']
    sealed_backend=read_json(campaign/'BACKEND_QUALIFICATION.json').get('backend')
    actual_backend=phys.backend_name()
    if cfg.get('require_a054_backend_match',True) and actual_backend!=sealed_backend:
        raise RuntimeError(f'A054 backend mismatch: sealed={sealed_backend}, importable/current={actual_backend}')
    backend=sealed_backend if cfg.get('require_a054_backend_match',True) else ('numpy_reference' if actual_backend=='numpy_reference' else actual_backend)
    fine=max(int(x) for x in ccfg['n_ladder']); fine_by={(r['anonymous_id'],r['sector']):r for r in results['results'] if r.get('N')==fine}
    candidates=list(manifest['candidates']); limit=cfg.get('candidate_limit')
    if limit is not None: candidates=candidates[:int(limit)]
    sectors=list(cfg.get('sectors') or ccfg['circulation_sectors']); rows=[]; parity_errors=[]
    for ci,row in enumerate(candidates,1):
        base=geom.load_components_npz(campaign/'blind_inputs'/row['file'])
        comps=[geom.resample_closed_curve(c,fine) for c in base]
        total_L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in comps)
        core=float(ccfg['core_ratio'])*total_L
        mi=modes.build_mode_basis(comps,tuple(ccfg['kelvin_harmonics']),True,True)
        for sec in sectors:
            gammas=phys.circulation_vector(3,sec)
            J=cert.projected_jacobian(comps,gammas,core,mi,float(ccfg['jacobian_eps_values'][-1]),backend)
            vals,vecs=np.linalg.eig(J)
            stored=fine_by[(row['anonymous_id'],sec)]
            err=eigenvalue_multiset_relative_error(vals,_stored_complex((stored.get('spectrum') or {}).get('eigenvalues',[])))
            parity_errors.append(err)
            signed=analyze_eigensystem(vals,vecs,mi['basis'],comps,families=mi.get('families'),
                harmonics=tuple(cfg['harmonics']),relative_imag_floor=float(cfg['relative_imag_floor']),
                min_kelvin_basis_fraction=float(cfg['min_kelvin_basis_fraction']),min_harmonic_participation=float(cfg['min_harmonic_participation']),min_traveling_purity=float(cfg['min_traveling_purity']),
                max_re_over_im=float(cfg['max_re_over_im']),max_pair_frequency_asymmetry=float(cfg['max_pair_frequency_asymmetry']))
            bs=(analysis.get('summaries',{}).get(row['anonymous_id'],{}).get('sectors',{}).get(sec,{}) or {})
            rpo=stored.get('rpo') or {}; floq=stored.get('floquet') or {}
            rows.append({'anonymous_id':row['anonymous_id'],'sector':sec,'fine_resolution':fine,
                         'recompute_eigenvalue_assignment_relative_error':float(err),
                         'stored_status':bs.get('status'),'spatial_converged':bs.get('spatial_converged'),
                         'spatial_reasons':bs.get('spatial_reasons',[]),'upstream_rpo_accepted':bool(rpo.get('accepted',False)),
                         'upstream_rpo_recurrence':rpo.get('recurrence'),'upstream_floquet_evaluated':bool(floq.get('evaluated',False)),
                         'upstream_floquet_max_nontrivial_abs':floq.get('max_nontrivial_abs'),
                         'upstream_normalized_growth':(stored.get('spectrum') or {}).get('normalized_max_real'),
                         'upstream_kelvin_growth':((stored.get('spectrum') or {}).get('kelvin_restricted') or {}).get('normalized_max_real'),
                         'signed_travel':signed})
    by={}
    for r in rows: by.setdefault(r['anonymous_id'],[]).append(r)
    summaries=[]; robust_min=int(cfg['robust_sector_count_min'])
    for aid,rr in sorted(by.items()):
        pair_count=sum(bool(x['signed_travel']['qualified_bidirectional_pair']) for x in rr)
        promoted=sum(bool(x['signed_travel']['qualified_bidirectional_pair'] and x['spatial_converged'] and x['upstream_rpo_accepted']) for x in rr)
        summaries.append({'anonymous_id':aid,'evaluated_sector_count':len(rr),'qualified_pair_sector_count':pair_count,
                          'robust_blind_pair':bool(pair_count>=robust_min),'mechanism_promoted_sector_count':promoted})
    maxerr=max(parity_errors) if parity_errors else float('inf')
    return {'schema':'A055-COMPOUND-SIGNED-TRAVEL-BLIND-031','source_campaign':str(campaign),'source_seal':seal,
            'config':cfg,'a054_sealed_backend':sealed_backend,'a054_actual_backend':actual_backend,'fine_resolution':fine,
            'analytic_selftest':analytic_selftest(),'rows':rows,'candidate_summaries':summaries,
            'max_recompute_eigenvalue_assignment_relative_error':float(maxerr),
            'robust_candidate_count':sum(x['robust_blind_pair'] for x in summaries),
            'mechanism_promoted_sector_count':sum(x['mechanism_promoted_sector_count'] for x in summaries)}
