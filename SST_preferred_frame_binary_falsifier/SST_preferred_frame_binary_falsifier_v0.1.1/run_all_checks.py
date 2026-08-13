#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np

from sst_pf_binary_falsifier.core import (
    backend_name, biot_savart_velocity, dipole_universality_gate, drift_scan,
    energy_balance_gate, filament_energy, j1738_corrected_pdot,
    linear_euler_bulk_wave_gate, preferred_frame_gate, torus_knot, write_json, write_csv,
    filament_system_energy, biot_savart_system_velocity
)
from sst_pf_binary_falsifier.ideal_db import load_knot_record, load_link_record, sample_record, audit_record, catalog_summary


def main()->int:
    p=argparse.ArgumentParser(description='Full SST preferred-frame + binary-radiation falsifier battery.')
    p.add_argument('--out-dir',default='audit_out'); p.add_argument('--force-build',action='store_true')
    p.add_argument('--quick',action='store_true',help='Use smaller filament grids.')
    a=p.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)

    if a.force_build:
        from sst_pf_binary_falsifier.build_ext_if_needed import build_if_needed
        build_if_needed(force=True,verbose=True)

    # 1) Native/Python parity on the real filament kernels.
    p0=torus_knot(n=36 if a.quick else 56)
    e_py=filament_energy(p0,force_python=True)
    e_auto=filament_energy(p0,force_python=False)
    v_py=biot_savart_velocity(p0,force_python=True)
    v_auto=biot_savart_velocity(p0,force_python=False)
    e_rel=abs(e_auto-e_py)/max(abs(e_py),1e-300)
    v_rel=float(np.linalg.norm(v_auto-v_py)/max(np.linalg.norm(v_py),1e-300))
    parity={'backend_auto':backend_name(False),'energy_python_J':e_py,'energy_auto_J':e_auto,
            'energy_relative_error':e_rel,'velocity_relative_l2_error':v_rel,
            'ok':bool(e_rel<1e-11 and v_rel<1e-11)}
    write_json(out/'backend_parity.json',parity)

    # 1b) User-supplied Gilbert Ideal.txt / IdealLinks.txt parser and Fourier convention checks.
    cat=catalog_summary()
    ideal_k=audit_record(load_knot_record('3:1:1'),linking=False)
    ideal_l=audit_record(load_link_record('L2a1'),linking=True)
    ideal_ok=(cat['knot_count']==250 and cat['link_count']==130 and
              max(abs(c['relative_length_error']) for c in ideal_k['curves'])<5e-6 and
              max(abs(c['relative_length_error']) for c in ideal_l['curves'])<5e-5 and
              len(ideal_l['linking_pairs'])==1 and abs(abs(ideal_l['linking_pairs'][0]['gauss_linking'])-1.0)<2e-3)
    write_json(out/'ideal_catalog.json',cat); write_json(out/'ideal_trefoil_3_1_1.json',ideal_k); write_json(out/'ideal_hopf_L2a1.json',ideal_l)

    # 1c) Multi-component kernel parity on physical-core-scaled L2a1.
    comps=sample_record(load_link_record('L2a1'),32,scale_mode='sst_core')
    se_py=filament_system_energy(comps,force_python=True); se_auto=filament_system_energy(comps,force_python=False)
    sv_py=np.vstack(biot_savart_system_velocity(comps,force_python=True)); sv_auto=np.vstack(biot_savart_system_velocity(comps,force_python=False))
    se_rel=abs(se_auto-se_py)/max(abs(se_py),1e-300); sv_rel=float(np.linalg.norm(sv_auto-sv_py)/max(np.linalg.norm(sv_py),1e-300))
    system_parity={'energy_relative_error':se_rel,'velocity_relative_l2_error':sv_rel,'ok':bool(se_rel<1e-11 and sv_rel<1e-11)}
    write_json(out/'ideal_link_backend_parity.json',system_parity)

    # 2) Galilean drift baseline: pure Euler should not generate intrinsic PF response.
    drift=drift_scan(n=40 if a.quick else 64,beta_values=(0,5e-4,1e-3,2e-3,0.00364867628),steps=1)
    write_json(out/'drift_baseline.json',drift); write_csv(out/'drift_baseline.csv',drift['rows'])

    # 3) Fit-recovery control: detect known injected isotropic/anisotropic terms.
    injected=drift_scan(n=36 if a.quick else 52,beta_values=(0,5e-4,1e-3,2e-3,0.00364867628),steps=1,
                        inject_chi0=1.25,inject_chi2=-0.40)
    rec=injected['fit']
    injection_ok=abs(rec['chi0']-1.25)<5e-5 and abs(rec['chi2']+0.40)<5e-5
    injected['fit_recovery_ok']=bool(injection_ok)
    write_json(out/'drift_injected_recovery.json',injected)

    # 4) Universal q/m cancellation vs deliberate violation.
    dip_ok=dipole_universality_gate([{'name':'A','mass':1.0,'charge':2.0},{'name':'B','mass':3.0,'charge':6.0}])
    dip_bad=dipole_universality_gate([{'name':'A','mass':1.0,'charge':2.0},{'name':'B','mass':3.0,'charge':6.03}],tolerance=1e-8)
    dipole_control_ok=dip_ok['universal_within_tolerance'] and not dip_bad['universal_within_tolerance']
    write_json(out/'dipole_universal.json',dip_ok); write_json(out/'dipole_violation_control.json',dip_bad)

    # 5) Linear homogeneous incompressible Euler structural mode gate.
    linear=linear_euler_bulk_wave_gate(); write_json(out/'linear_euler_gate.json',linear)

    # 6) J1738 source-data correction and preferred-frame scale diagnostics.
    j1738=j1738_corrected_pdot(); write_json(out/'j1738_reference.json',j1738)
    pf=preferred_frame_gate(); write_json(out/'preferred_frame_scale.json',pf)
    expected_corr=-2.72e-14
    j_ok=abs(j1738['pdot_corrected_s_per_s']-expected_corr)<1e-28

    # 7) Manufactured energy-balance closure plus failing negative control.
    t=np.linspace(0,10,101); power=2.5
    eb_ok=energy_balance_gate(t,100-power*t,np.full_like(t,power),np.full_like(t,-power),0.01)
    eb_bad=energy_balance_gate(t,100-power*t,np.full_like(t,power*1.5),np.full_like(t,-power),0.01)
    eb_control_ok=eb_ok['ok'] and not eb_bad['ok']
    write_json(out/'energy_balance_pass_control.json',eb_ok); write_json(out/'energy_balance_fail_control.json',eb_bad)

    checks={
        'backend_parity':parity['ok'],
        'ideal_database_parser_and_fourier':ideal_ok,
        'ideal_link_multicomponent_backend_parity':system_parity['ok'],
        'galilean_drift_baseline':drift['baseline_ok'],
        'injected_chi_fit_recovery':injection_ok,
        'dipole_universality_controls':dipole_control_ok,
        'linear_euler_structural_gate':not linear['propagating_bulk_mode_found'],
        'j1738_reference_correction':j_ok,
        'energy_balance_controls':eb_control_ok,
    }
    summary={
        'package':'SST_preferred_frame_binary_falsifier', 'version':'0.1.1',
        'checks':checks, 'all_internal_checks_pass':all(checks.values()),
        'scientific_status':{
            'plain_euler_uniform_drift':'tested',
            'sst_drift_sensitivity':'NOT_YET_DERIVED',
            'sst_q_over_m_universality':'INPUT_REQUIRED',
            'sst_binary_radiative_mode':'NOT_YET_SUPPLIED',
            'sst_j1738_prediction':'NOT_YET_SUPPLIED'
        },
        'falsification_rule':'A FAIL in an SST-supplied prediction gate is evidence against that supplied closure/mapping, not automatically against every SST formulation.'
    }
    write_json(out/'audit_summary.json',summary); print(json.dumps(summary,indent=2))
    return 0 if summary['all_internal_checks_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
