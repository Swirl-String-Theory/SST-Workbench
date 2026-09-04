#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from finite_core_spectral.core import independence_manifest, spectrum_at_q, write_json
from finite_core_spectral.convergence import evaluate_gap_convergence

def _synthetic_gate_regression():
    base={'kind':'full_spectrum_isolated_gap_minimum','q':2.75,'cell_over_core':15.6,'gap':1e-3}
    cases=[]
    for axis,vals in [('resolution',[(64,2.750),(96,2.755)]),('image_shell',[(2,2.751),(3,2.754)]),('fd_eps',[(3e-4,2.749),(1e-4,2.752),(3e-5,2.756)])]:
        for v,q in vals:
            cases.append({'axis':axis,'case':str(v),'value':v,'result':{'refined_primary_candidates':[{**base,'q':q}]}})
    clusters=evaluate_gap_convergence(cases,0.02)
    return {'n_clusters':len(clusters),'promoted':bool(clusters and clusters[0]['promote_converged_candidate']),'clusters':clusters}

def main():
    p=argparse.ArgumentParser(description='Smoke, dimensionless-manifest, native/Python parity, isolation, roundoff-gate and convergence-gate checks.')
    p.add_argument('--out-dir',default='audit_checks'); p.add_argument('--force-build',action='store_true'); p.add_argument('--threads',type=int,default=1)
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    cfg={'n_nodes':8,'ring_radius_over_core':2.0,'q_min':2.0,'q_max':3.0,'q_step':0.5,'image_shell':1,'fd_eps_over_core':1e-3,'core_model':0,'threads':a.threads,'neutral_modes':6,'eig_zero_tol':1e-8,'residual_max':0.2}
    manifest=independence_manifest(cfg); write_json(out/'independence_manifest.json',manifest)
    q=2.5; primary=spectrum_at_q(cfg,q,force_build=a.force_build); py=spectrum_at_q(cfg,q,force_python=True)
    native_available=(primary['backend']=='cpp')
    parity={'native_backend_available':native_available}
    if native_available:
        parity.update({
          'gap_rel':abs(primary['gap_after_neutral']-py['gap_after_neutral'])/max(abs(py['gap_after_neutral']),1e-12),
          'sigma_abs':abs(primary['spectral_abscissa']-py['spectral_abscissa']),
          'interaction_norm_rel':abs(primary['interaction_jacobian_norm']-py['interaction_jacobian_norm'])/max(abs(py['interaction_jacobian_norm']),1e-12),
          'ok':False,
        })
        parity['ok']=parity['gap_rel']<2e-5 and parity['sigma_abs']<2e-5 and parity['interaction_norm_rel']<2e-5
    else:
        parity.update({'ok':None,'note':'Native extension unavailable in this environment; Python reference path passed.'})
    write_json(out/'backend_parity.json',{'primary':primary,'python':py,'parity':parity})
    iso=spectrum_at_q({**cfg,'image_shell':0},3.0,force_python=True)
    isolation={'interaction_norm':iso['interaction_jacobian_norm'],'ok':iso['interaction_jacobian_norm']==0.0}; write_json(out/'isolation_probe.json',isolation)

    noise_cfg={**cfg,'fd_eps_over_core':1e-4}
    strong=spectrum_at_q(noise_cfg,3.0,force_python=True); weak=spectrum_at_q(noise_cfg,8.0,force_python=True)
    noise_gate={'strong_q':3.0,'strong_ratio':strong['neutral_signal_to_fd_floor'],'strong_gate':strong['neutral_signal_gate_ok'],
                'weak_q':8.0,'weak_ratio':weak['neutral_signal_to_fd_floor'],'weak_gate':weak['neutral_signal_gate_ok'],
                'ok':bool(strong['neutral_signal_gate_ok'] and not weak['neutral_signal_gate_ok'])}
    write_json(out/'roundoff_gate_probe.json',noise_gate)

    conv=_synthetic_gate_regression(); conv['ok']=conv['n_clusters']==1 and conv['promoted']; write_json(out/'convergence_gate_regression.json',conv)
    summary={
      'dimensionless_manifest_ok':manifest['dimensionless_only'] and not manifest['external_physical_constants_used'] and not manifest['external_target_values_used'],
      'python_reference_ok':math.isfinite(py['gap_after_neutral']) and math.isfinite(py['spectral_abscissa']),
      'native_backend_available':native_available,
      'backend_parity_ok':parity['ok'],
      'isolation_probe_ok':isolation['ok'],
      'roundoff_gate_ok':noise_gate['ok'],
      'convergence_gate_regression_ok':conv['ok'],
    }
    summary['ok']=all(summary[k] for k in ['dimensionless_manifest_ok','python_reference_ok','isolation_probe_ok','roundoff_gate_ok','convergence_gate_regression_ok']) and (parity['ok'] is not False)
    write_json(out/'audit_summary.json',summary); print(json.dumps(summary,indent=2)); return 0 if summary['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
