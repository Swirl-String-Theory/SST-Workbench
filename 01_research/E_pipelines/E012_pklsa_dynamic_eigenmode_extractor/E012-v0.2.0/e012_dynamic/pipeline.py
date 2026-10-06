from __future__ import annotations
import json, math, platform, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

from .paths import detect_workbench_root, find_e011_seedset, find_c006_version
from .seed import select_provider_anchors, resolve_provider
from .c006_bridge import import_c006, provenance as c006_provenance
from .tracking import track_from_finest, select_fine_anchored_branch
from .conditioning import run_rpo_conditioning
from .scale import load_scale_contract, make_physical_candidate
from .reporting import render_report
from .util import dump_json, relative_shift, centered_slopes, sha256_file


def _complex_rows(values):
    return [{'re':float(complex(z).real),'im':float(complex(z).imag)} for z in values]

def _complex_matrix_cols(mat):
    a=np.asarray(mat,dtype=complex)
    return [[{'re':float(a[i,j].real),'im':float(a[i,j].imag)} for j in range(a.shape[1])] for i in range(a.shape[0])]

def _complex_from_rows(rows):
    return np.asarray([complex(r['re'],r['im']) for r in rows],dtype=complex)

def _complex_matrix_from_rows(rows):
    return np.asarray([[complex(z['re'],z['im']) for z in row] for row in rows],dtype=complex)

def _rel_span(vals, floor=1e-30):
    xs=np.asarray(list(vals),dtype=float)
    if len(xs)<2: return math.inf
    med=float(np.median(np.abs(xs)))
    return float((float(np.max(xs))-float(np.min(xs)))/max(med,floor))

def run(root: Path, *, workbench_root=None, preset='quick', force_python=False, physical_scale_path: Path|None=None):
    root=Path(root).resolve(); cfg=json.loads((root/'configs/frozen_policy.json').read_text(encoding='utf-8'))
    if preset not in cfg['presets']: raise ValueError('preset must be quick or full')
    pcfg=cfg['presets'][preset]; track_cfg=cfg['eigenvector_tracking']; cp_cfg=cfg['cross_provider_agreement']; rpo_cfg=cfg['rpo_conditioning']
    workbench=detect_workbench_root(workbench_root); out=root/'outputs'; out.mkdir(parents=True,exist_ok=True)

    seedset=find_e011_seedset(workbench,cfg['topology_id'])
    anchors,summary=select_provider_anchors(seedset,tuple(cfg['e011_provider_groups']),topology_id=cfg['topology_id'])
    providers=[resolve_provider(a,workbench,canonical_writhe_sign=int(cfg['canonical_writhe_sign'])) for a in anchors]
    c006_root=find_c006_version(workbench); dynamics,spectral,orbit=import_c006(c006_root)

    run_context={'schema':'E012-RUN-CONTEXT-2.0','created_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,
      'platform':platform.platform(),'workbench_root':str(workbench),'preset':preset,'force_python':bool(force_python),
      'frozen_policy_sha256':sha256_file(root/'configs/frozen_policy.json'),'e011_seedset_path':str(seedset),
      'e011_seedset_sha256':sha256_file(seedset),'c006_root':str(c006_root),'provider_groups':[p['anchor'].get('provider_group') for p in providers]}
    dump_json(out/'E012_RUN_CONTEXT.json',run_context); dump_json(out/'C006_PROVENANCE.json',c006_provenance(c006_root))

    provider_seed_rows=[]
    for p in providers:
        a=p['anchor']; provider_seed_rows.append({'provider_group':a.get('provider_group'),'static_seed_id':a.get('static_seed_id'),
          'carrier_id':a.get('carrier_id'),'static_ready':a.get('static_ready'),'static_status':summary.get('static_status'),
          'source_locator':a.get('source_locator'),'source_path_resolved':str(p['source_path']),'source_sha256':p['source_sha256'],
          'e011_finest_metrics':a.get('finest_metrics'),'representation':p['representation'],'canonical_writhe_sign':cfg['canonical_writhe_sign'],
          'normalization':cfg['provider_scale_normalization']})
    dump_json(out/'E011_PROVIDER_SEEDS.json',{'topology_id':cfg['topology_id'],'static_status':summary.get('static_status'),'providers':provider_seed_rows})

    # Same-generator RPO qualification, with no parameter scan.
    rpo_results=[]
    for p in providers:
        a=p['anchor']; pg=a.get('provider_group')
        try:
            center,norm=p['sample'](int(pcfg['rpo_resolution']))
            rcfg={'offset_over_D':cfg['offset_over_D'],'eps_over_D':cfg['eps_over_D'],'channel_phase_rad':cfg['channel_phase_rad'],
                  'gamma_plus_hat':cfg['gamma_plus_hat'],'gamma_minus_hat':cfg['gamma_minus_hat'],'dt_hat':pcfg['rpo_dt_hat'],
                  'max_time_hat':pcfg['rpo_max_time_hat'],'min_time_hat':rpo_cfg['min_time_hat'],'snapshot_stride':rpo_cfg['snapshot_stride'],
                  'recurrence_tol_over_D':rpo_cfg['recurrence_tol_over_D']}
            rr=run_rpo_conditioning(orbit,center,D=1.0,cfg=rcfg,force_python=bool(force_python))
            rpo_results.append({'provider_group':pg,'normalization':norm,**rr})
        except Exception as exc:
            rpo_results.append({'provider_group':pg,'candidate':{'accepted':False},'error':repr(exc)})
    dump_json(out/'RPO_CONDITIONING.json',{'policy':rpo_cfg,'preset_parameters':{'resolution':pcfg['rpo_resolution'],'dt_hat':pcfg['rpo_dt_hat'],'max_time_hat':pcfg['rpo_max_time_hat']},'providers':rpo_results})
    rpo_by_provider={r['provider_group']:r for r in rpo_results}

    n_ladder=[int(x) for x in pcfg['n_ladder']]; mmax=int(pcfg['mode_m_max']); reltol=float(pcfg['stable_root_relative_shift_max'])
    all_levels=[]; all_failures=[]; provider_outputs=[]
    min_modes=int(cfg['policy']['minimum_mode_samples_per_provider'])

    for p in providers:
        a=p['anchor']; pg=a.get('provider_group'); per_mode={m:[] for m in range(1,mmax+1)}; failures=[]
        for N in n_ladder:
            center,norm=p['sample'](N); L=float(norm['normalized_polygon_length'])
            for m in range(1,mmax+1):
                try:
                    z=dynamics.projected_kelvin_analysis(center,D=1.0,offset_over_D=float(cfg['offset_over_D']),eps_over_D=float(cfg['eps_over_D']),
                        fd_step_over_D=float(cfg['fd_step_over_D']),gamma_plus=float(cfg['gamma_plus_hat']),gamma_minus=float(cfg['gamma_minus_hat']),
                        channel_phase=float(cfg['channel_phase_rad']),basis_phase=float(cfg['basis_phase_rad']),mode_m=m,
                        force_python=bool(force_python),skip_build=True)
                    vals=np.asarray(z['eigenvalues'],dtype=complex); vecs=np.asarray(z['eigenvectors'],dtype=complex)
                    row={'provider_group':pg,'N':N,'mode_m':m,'L_polygon':L,'D_source':1.0,'kD':float(2*math.pi*m/L),
                         'relative_equilibrium_residual':float(z['rigid']['relative_equilibrium_residual']),'backend':str(z['backend']),
                         'selected_positive_index':int(z['selected_positive_index']),'c006_selected_lambda_positive_hat':z['lambda_positive_hat'],
                         'c006_selected_quality_re_over_im':float(z['positive_quality_re_over_im']),
                         'eigenvalues':_complex_rows(vals),'eigenvectors':_complex_matrix_cols(vecs),'normalization':norm}
                    all_levels.append(row); per_mode[m].append(row)
                except Exception as exc:
                    f={'provider_group':pg,'N':N,'mode_m':m,'error':repr(exc)}; failures.append(f); all_failures.append(f)

        mode_reports=[]; qualified_samples=[]; freq_pass_modes=[]; overlap_pass_modes=[]; quality_pass_modes=[]
        for m in range(1,mmax+1):
            rows=per_mode[m]
            if len(rows)!=len(n_ladder):
                mode_reports.append({'mode_m':m,'status':'FAIL_INCOMPLETE_RESOLUTION_LADDER'}); continue
            track_levels=[{'label':r['N'],'eigenvalues':_complex_from_rows(r['eigenvalues']),'eigenvectors':_complex_matrix_from_rows(r['eigenvectors'])} for r in rows]
            tr=track_from_finest(track_levels,rel_tol=reltol,overlap_min=float(track_cfg['minimum_adjacent_overlap']),
                                 eigenvalue_weight=float(track_cfg['eigenvalue_weight']),overlap_weight=float(track_cfg['overlap_weight']))
            fine=rows[-1]; sb=select_fine_anchored_branch(tr,int(fine['selected_positive_index']))
            lambdas=[complex(pnt['lambda']) for pnt in sb['points']]
            omegas=[float(z.imag) for z in lambdas]
            freq_shifts=[relative_shift(omegas[i],omegas[i+1]) for i in range(len(omegas)-1)]
            freq_ok=bool(all(x<=reltol for x in freq_shifts) and all(w>0 for w in omegas))
            overlap_ok=bool(sb.get('persistent',False))
            qualities=[abs(float(z.real))/max(abs(float(z.imag)),1e-30) for z in lambdas]
            quality_ok=bool(all(q<=float(track_cfg['maximum_re_over_im']) for q in qualities))
            legacy=spectral.track_spectrum([{'label':r['N'],'eigenvalues':_complex_from_rows(r['eigenvalues'])} for r in rows],rel_tol=reltol)
            mode_ok=bool(freq_ok and overlap_ok and quality_ok)
            if freq_ok: freq_pass_modes.append(m)
            if overlap_ok: overlap_pass_modes.append(m)
            if quality_ok: quality_pass_modes.append(m)
            if mode_ok:
                z=lambdas[-1]; qualified_samples.append({'mode_m':m,'N':fine['N'],'kD':fine['kD'],'omega_hat':float(z.imag),
                    'growth_hat':float(z.real),'quality_re_over_im':float(qualities[-1]),
                    'relative_equilibrium_residual':fine['relative_equilibrium_residual'],'backend':fine['backend'],
                    'selected_branch_min_overlap':float(sb.get('min_eigenvector_overlap',0.0)),
                    'selected_branch_max_eigenvalue_shift':float(sb.get('max_eigenvalue_shift',math.inf))})
            mode_reports.append({'mode_m':m,'N_ladder':n_ladder,'fine_selected_index':int(fine['selected_positive_index']),
                'tracked_lambda_hat':_complex_rows(lambdas),'tracked_omega_hat':omegas,'selected_frequency_relative_shifts':freq_shifts,
                'selected_frequency_converged':freq_ok,'selected_eigenvector_branch_persistent':overlap_ok,
                'selected_quality_re_over_im':qualities,'oscillatory_quality_ok':quality_ok,'mode_qualified':mode_ok,
                'overlap_tracking':tr,'legacy_full_spectrum_tracking':legacy})
        qualified_samples.sort(key=lambda r:r['mode_m'])
        numerical_ok=len(qualified_samples)>=min_modes and not failures
        rpo_accepted=bool(rpo_by_provider.get(pg,{}).get('candidate',{}).get('accepted',False))
        provider_outputs.append({'provider_group':pg,'static_seed_id':a.get('static_seed_id'),'numerical_branch_ok':bool(numerical_ok),
            'rpo_accepted':rpo_accepted,'qualified_mode_count':len(qualified_samples),'qualified_samples':qualified_samples,
            'frequency_pass_modes':freq_pass_modes,'overlap_pass_modes':overlap_pass_modes,'quality_pass_modes':quality_pass_modes,
            'mode_reports':mode_reports,'failures':failures})

    dump_json(out/'DYNAMIC_EIGENMODE_LEVELS.json',{'levels':all_levels,'failures':all_failures})
    dump_json(out/'PROVIDER_DYNAMIC_BRANCHES.json',{'providers':provider_outputs})

    # Cross-provider agreement on modes independently qualified by every provider.
    qmaps={p['provider_group']:{int(r['mode_m']):r for r in p['qualified_samples']} for p in provider_outputs}
    common=set.intersection(*(set(m.keys()) for m in qmaps.values())) if qmaps else set()
    agreement_rows=[]; consensus=[]
    for m in sorted(common):
        rows=[qmaps[p['provider_group']][m] for p in provider_outputs]
        ospan=_rel_span([r['omega_hat'] for r in rows]); kspan=_rel_span([r['kD'] for r in rows])
        ok=ospan<=float(cp_cfg['omega_hat_relative_span_max']) and kspan<=float(cp_cfg['kD_relative_span_max'])
        agreement_rows.append({'mode_m':m,'providers':[p['provider_group'] for p in provider_outputs],
            'omega_hat':[r['omega_hat'] for r in rows],'kD':[r['kD'] for r in rows],
            'omega_hat_relative_span':ospan,'kD_relative_span':kspan,'pass':bool(ok)})
        if ok:
            consensus.append({'mode_m':m,'kD':float(np.median([r['kD'] for r in rows])),
                              'omega_hat':float(np.median([r['omega_hat'] for r in rows])),
                              'growth_hat':float(np.median([r['growth_hat'] for r in rows])),
                              'provider_count':len(rows),'provider_omega_hat':[r['omega_hat'] for r in rows],
                              'provider_kD':[r['kD'] for r in rows]})
    cp_ok=bool(len(provider_outputs)>=int(cfg['minimum_independent_providers']) and
               len(consensus)>=int(cp_cfg['minimum_common_qualified_modes']) and
               len(consensus)==len(agreement_rows) and len(agreement_rows)>=int(cp_cfg['minimum_common_qualified_modes']))
    cp_payload={'provider_count':len(provider_outputs),'common_qualified_modes':sorted(common),'agreement_rows':agreement_rows,
                'consensus_samples':consensus,'cross_provider_dynamic_agreement_ok':cp_ok,'policy':cp_cfg}
    dump_json(out/'CROSS_PROVIDER_AGREEMENT.json',cp_payload)

    provider_numerics_ok=all(p['numerical_branch_ok'] for p in provider_outputs)
    all_rpo_ok=all(p['rpo_accepted'] for p in provider_outputs)
    branch_ok=bool(provider_numerics_ok and all_rpo_ok and cp_ok)
    consensus.sort(key=lambda r:r['kD'])
    branch={'schema':'E012-CROSS-PROVIDER-DYNAMIC-EIGENBRANCH-2.0',
      'classification':'RPO_CONDITIONED_CROSS_PROVIDER_KELVIN_EIGENBRANCH' if branch_ok else 'CROSS_PROVIDER_KELVIN_EIGENBRANCH_CANDIDATE_UNQUALIFIED',
      'topology_id':cfg['topology_id'],'provider_groups':[p['provider_group'] for p in provider_outputs],'c006_version':'0.3.0','preset':preset,
      'samples':consensus,'dimensionless_group_slopes':centered_slopes([r['kD'] for r in consensus],[r['omega_hat'] for r in consensus]),
      'dimensionless_dynamic_branch_ok':branch_ok,'provider_numerics_ok':provider_numerics_ok,'rpo_conditioning_ok':all_rpo_ok,
      'cross_provider_dynamic_agreement_ok':cp_ok,'physical_scale_status':'UNRESOLVED_UNLESS_APPROVED_SCALE_CONTRACT',
      'true_floquet_status':'NOT_COMPUTED__RPO_CONDITIONING_IS_NOT_MONODROMY',
      'scientific_boundary':'Cross-provider local Kelvin branch with same-generator RPO qualification. RPO acceptance does not by itself establish true Floquet monodromy, photon identity, or SI dispersion.'}
    dump_json(out/'DYNAMIC_EIGENBRANCH.json',branch)

    expected=len(providers)*len(n_ladder)*mmax
    freq_gate=all(len(p['frequency_pass_modes'])>=min_modes for p in provider_outputs)
    overlap_gate=all(len(p['overlap_pass_modes'])>=min_modes for p in provider_outputs)
    quality_gate=all(len(p['quality_pass_modes'])>=min_modes for p in provider_outputs)
    residuals={p['provider_group']:[r['relative_equilibrium_residual'] for r in p['qualified_samples']] for p in provider_outputs}
    gates=[
      {'id':'G01_E011_MULTI_PROVIDER_STATIC_READY_PROVENANCE','status':'PASS' if len(providers)>=int(cfg['minimum_independent_providers']) else 'FAIL',
       'static_status':summary.get('static_status'),'providers':[p['provider_group'] for p in provider_outputs]},
      {'id':'G02_C006_DYNAMIC_GENERATOR_AVAILABLE','status':'PASS' if len(all_levels)==expected and not all_failures else ('PARTIAL' if all_levels else 'FAIL'),
       'c006_version':'0.3.0','level_count':len(all_levels),'expected_level_count':expected,'failures':len(all_failures)},
      {'id':'G03_SAME_GENERATOR_RPO_BACKGROUND_CONDITIONING','status':'PASS' if all_rpo_ok else 'FAIL',
       'required_for_dimensionless_handoff':bool(rpo_cfg['required_for_dimensionless_handoff']),
       'providers':[{ 'provider_group':r['provider_group'],'accepted':bool(r.get('candidate',{}).get('accepted',False)),
                      'recurrence_rms_over_D':r.get('candidate',{}).get('recurrence_rms_over_D'),
                      'endpoint_vectorfield_error':r.get('candidate',{}).get('endpoint_vectorfield_error')} for r in rpo_results]},
      {'id':'G04_SELECTED_BRANCH_FREQUENCY_CONVERGENCE','status':'PASS' if freq_gate else 'FAIL','relative_tolerance':reltol,
       'minimum_modes_per_provider':min_modes},
      {'id':'G05_EIGENVECTOR_SUBSPACE_BRANCH_PERSISTENCE','status':'PASS' if overlap_gate else 'FAIL',
       'minimum_adjacent_overlap':track_cfg['minimum_adjacent_overlap'],'relative_tolerance':reltol,'minimum_modes_per_provider':min_modes},
      {'id':'G06_OSCILLATORY_MODE_QUALITY','status':'PASS' if quality_gate else 'FAIL','maximum_re_over_im':track_cfg['maximum_re_over_im'],
       'minimum_modes_per_provider':min_modes},
      {'id':'G07_CROSS_PROVIDER_DYNAMIC_AGREEMENT','status':'PASS' if cp_ok else 'FAIL',
       'common_qualified_mode_count':len(common),'consensus_mode_count':len(consensus),'minimum_common_modes':cp_cfg['minimum_common_qualified_modes']},
      {'id':'G08_BACKGROUND_RELATIVE_EQUILIBRIUM','status':'DIAGNOSTIC','policy':'Best rigid-frame residual retained as a diagnostic; v0.2 handoff requires the independent same-generator RPO gate instead of inventing a new residual threshold.','provider_residuals':residuals},
      {'id':'G09_TRUE_FLOQUET','status':'NOT_CLAIMED','policy':'RPO qualification is not monodromy. No true Floquet claim is made in v0.2.0.'}
    ]

    scale_path=Path(physical_scale_path) if physical_scale_path else root/'configs/physical_scale.json'
    scale=load_scale_contract(scale_path); scale_candidate,scale_reasons=make_physical_candidate(branch,scale); scale_ok=scale_candidate is not None
    candidate=scale_candidate if (scale_ok and branch_ok) else None
    blockers=[]
    for p in provider_outputs:
        if not p['numerical_branch_ok']: blockers.append(f'PROVIDER_NUMERICAL_BRANCH_NOT_QUALIFIED:{p["provider_group"]}')
        if not p['rpo_accepted']: blockers.append(f'RPO_BACKGROUND_NOT_QUALIFIED:{p["provider_group"]}')
    if not cp_ok: blockers.append('CROSS_PROVIDER_DYNAMIC_AGREEMENT_FAILED')
    blockers.extend(scale_reasons)
    if candidate is not None:
        dump_json(out/'a052_dynamic_candidate.json',candidate); handoff='A052_PHYSICAL_HANDOFF_READY'
    else: handoff='A052_PHYSICAL_HANDOFF_BLOCKED'
    gates += [
      {'id':'G10_PHYSICAL_SCALE_AND_ENERGY_MAPPING','status':'PASS' if scale_ok else 'BLOCKED','reasons':scale_reasons,'contract_path':str(scale_path) if scale_path.exists() else None},
      {'id':'G11_A052_HANDOFF','status':'PASS' if candidate is not None else 'BLOCKED','candidate_emitted':candidate is not None,'reasons':blockers}
    ]
    if branch_ok and candidate is not None: verdict='A052_PHYSICAL_DYNAMIC_CANDIDATE_EMITTED'
    elif branch_ok: verdict='DIMENSIONLESS_CROSS_PROVIDER_BRANCH_OK__A052_PHYSICAL_HANDOFF_BLOCKED'
    else: verdict='DYNAMIC_EIGENBRANCH_NOT_QUALIFIED'
    dump_json(out/'GATES.json',{'verdict':verdict,'gates':gates})
    dump_json(out/'A052_HANDOFF_STATUS.json',{'verdict':handoff,'candidate_emitted':candidate is not None,
      'dimensionless_dynamic_branch_ok':branch_ok,'blocking_reasons':blockers,
      'next_action':'Copy outputs/a052_dynamic_candidate.json into A052 private/dynamic_candidate.json and rerun A052.' if candidate is not None else 'Resolve listed E012 branch/RPO/provider/scale blockers; do not hand anything to A052 yet.'})
    report=render_report(verdict=verdict,preset=preset,providers=provider_outputs,cross_provider_ok=cp_ok,branch_ok=branch_ok,handoff_status=handoff,handoff_blockers=blockers)
    (out/'report.md').write_text(report,encoding='utf-8')
    return {'verdict':verdict,'branch_ok':branch_ok,'handoff':handoff,'outputs':str(out)}
