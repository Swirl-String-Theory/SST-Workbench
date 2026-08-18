from __future__ import annotations
from collections import Counter
from pathlib import Path
from .io import read_json,write_json,write_csv


def unblind_and_report(out_root: str|Path):
    root=Path(out_root); blind=root/'blind_campaign'; key=read_json(root/'private_blind_key.json'); scores=read_json(blind/'results'/'blind_scores.json')
    rows=[]
    for s in scores:
        cid=s['case_id']; raw=read_json(blind/'results'/cid/'raw.json'); priv=key['cases'][cid]; gs=s.get('gates',{})
        d=raw.get('dispersion',{}); r=raw.get('radial_response',{}); re=raw.get('relative_equilibrium',{})
        rows.append({
            'case_id':cid,'dataset':priv['filename'],'overall':s['overall'],'backend':raw.get('backend'),'components':len(raw.get('original_points_per_component',[])),
            'original_points':sum(raw.get('original_points_per_component',[])),'resampled_points':raw.get('resampled_points'),'thickness':raw.get('core_radius_model'),'rr_residual':raw.get('rr_residual'),
            'relative_equilibrium_residual':re.get('relative_residual'),'omega_eff':re.get('omega_eff'),'spectral_modes':d.get('n_modes'),'gap_sigma0':d.get('gap_sigma0'),'gap_to_2omega_ratio':d.get('gap_to_2omega_ratio'),
            'dispersion_train_r2':d.get('train_r2'),'dispersion_holdout_nrmse':d.get('holdout_nrmse'),'gap_delta_aic':d.get('delta_aic_zero_minus_gap'),'c_eff':d.get('c_eff'),
            'evanescent_observed_length':r.get('observed_exp_length'),'evanescent_predicted_length':r.get('predicted_kelvin_length'),'evanescent_length_ratio':r.get('length_ratio'),'evanescent_exp_r2':r.get('exp_log_r2'),'evanescent_delta_aic':r.get('delta_aic_power_minus_exp'),
            'geometry_qc':gs.get('geometry_qc',{}).get('status'),'relative_equilibrium_gate':gs.get('relative_equilibrium',{}).get('status'),'kelvin_gap_gate':gs.get('kelvin_2omega_gap',{}).get('status'),'evanescent_gate':gs.get('evanescent_confinement',{}).get('status'),'kirchhoff_detailed_balance':gs.get('kirchhoff_detailed_balance',{}).get('status'),
        })
    write_json(root/'unblinded_summary.json',rows); write_csv(root/'unblinded_summary.csv',rows)
    counts=Counter(r['overall'] for r in rows); lines=[]
    lines += ['# Kelvin–Kirchhoff SST blind falsifier report','',f"Campaign mode: **{key.get('mode','unknown')}**",'',f"Cases: **{len(rows)}** — PASS {counts.get('PASS',0)}, FAIL {counts.get('FAIL',0)}, INCONCLUSIVE {counts.get('INCONCLUSIVE',0)}",'']
    lines += ['## Interpretation boundary','',
      '- The numerical runner uses only the relaxed centerlines, their Ridgerunner thickness metadata, a fixed regularized Biot–Savart model, and preregistered numerical settings.',
      '- It does **not** identify the Ridgerunner tube thickness with SST `r_c`; the current Canon explicitly keeps resolved tube/core thickness separate from the horn/circulation radius.',
      '- A failure falsifies this **Kelvin-inspired centerline closure on the tested geometry/model**, not SST as a whole.',
      '- Kirchhoff detailed balance is reported as `NOT_TESTABLE`: centerline geometry contains no equilibrium mode-resolved incident, absorbed, and emitted fluxes. The package deliberately does not invent a proxy.','']
    lines += ['## Gates','',
      '1. **Geometry QC** — checks the supplied Ridgerunner residual/edge uniformity and provenance of the smoothing radius.',
      '2. **Relative equilibrium** — asks whether self-induced velocity is well approximated by one rigid translation plus one rigid rotation.',
      '3. **Kelvin 2Ω gap** — extracts a spectrum from a finite-difference linearization, fits `sigma^2 = sigma0^2 + c_eff^2 k^2` on a training subset, predicts held-out modes, and only afterward tests `sigma0/(2 Omega_eff) = 1`.',
      '4. **Evanescent confinement** — measures the radial decay of a perturbation response and only afterward compares the fitted decay length with `c_eff/(2 Omega_eff)`; an exponential must also beat a power law by the preregistered AIC margin.',
      '5. **Kirchhoff detailed balance** — not testable from these data alone.','']
    lines += ['## Results','', '| Dataset | Overall | RelEq | Gap | Evanescent | gap/(2Ω) | Lobs/Lpred |','|---|---:|---:|---:|---:|---:|---:|']
    def fmt(x):
        try: return f'{float(x):.5g}'
        except Exception: return '—'
    for r in rows:
        lines.append(f"| {r['dataset']} | {r['overall']} | {r['relative_equilibrium_gate']} | {r['kelvin_gap_gate']} | {r['evanescent_gate']} | {fmt(r['gap_to_2omega_ratio'])} | {fmt(r['evanescent_length_ratio'])} |")
    lines += ['','## Files','', '- `unblinded_summary.csv` — compact machine-readable result table.', '- `blind_campaign/results/CASE_*/raw.json` — target-free extracted observables.', '- `blind_campaign/results/CASE_*/spectrum.csv` — eigenvalue/frequency/wavenumber rows.', '- `blind_campaign/results/CASE_*/operator_A.npy` — projected linearized operators.', '- `blind_campaign/results/frozen_preregistration.json` — thresholds frozen before case results.', '- `private_blind_key.json` — identity mapping kept outside the blind campaign.','']
    (root/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    return rows
