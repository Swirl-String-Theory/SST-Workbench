import math
import numpy as np

from sst_pf_binary_falsifier.constants import V_SWIRL_OVER_C_SQ
from sst_pf_binary_falsifier.core import (
    dipole_universality_gate,
    energy_balance_gate,
    fit_drift_sensitivity,
    j1738_corrected_pdot,
    linear_euler_bulk_wave_gate,
    preferred_frame_gate,
    torus_knot,
    filament_energy,
)


def test_canonical_ratio_scale():
    assert abs(V_SWIRL_OVER_C_SQ - 1.331283856e-5) < 5e-13


def test_torus_energy_positive():
    e = filament_energy(torus_knot(n=32), force_python=True)
    assert math.isfinite(e) and e > 0


def test_fit_chi_recovers_exact_model():
    rows=[]
    for beta in [0,1e-3,2e-3,3e-3]:
        for mu_factor in [0.0,1/3,1.0]:
            b2=beta**2; mu2=mu_factor*b2
            y=1.2*b2-0.4*(mu2-b2/3)
            rows.append({'beta2':b2,'axis_projection_sq':mu2,'delta_E_over_E0':y})
    f=fit_drift_sensitivity(rows)
    assert abs(f['chi0']-1.2) < 1e-10
    assert abs(f['chi2']+0.4) < 1e-10


def test_j1738_correction():
    r=j1738_corrected_pdot()
    assert abs(r['pdot_corrected_s_per_s'] + 2.72e-14) < 1e-28


def test_preferred_frame_scale_caps():
    r=preferred_frame_gate()
    assert 5.3 < r['C1_cap_from_J1738_90_one_sided_magnitude_proxy'] < 5.5
    assert 0.007 < r['C2_cap_from_solar_system_abs_proxy'] < 0.008


def test_dipole_universal_and_nonuniversal():
    a=dipole_universality_gate([{'mass':1,'charge':2},{'mass':4,'charge':8}])
    b=dipole_universality_gate([{'mass':1,'charge':2},{'mass':4,'charge':8.1}],tolerance=1e-8)
    assert a['universal_within_tolerance']
    assert not b['universal_within_tolerance']


def test_linear_euler_no_bulk_modes():
    r=linear_euler_bulk_wave_gate()
    assert not r['propagating_bulk_mode_found']
    assert r['max_abs_eigenvalue_per_s']==0.0


def test_energy_balance_control():
    t=np.linspace(0,3,31); p=2.0
    r=energy_balance_gate(t,10-p*t,np.full_like(t,p),np.full_like(t,-p),1e-8)
    assert r['ok']



def test_gilbert_ideal_trefoil_reconstructs_source_length():
    from sst_pf_binary_falsifier.ideal_db import load_knot_record, audit_record
    r=audit_record(load_knot_record('3:1:1'),linking=False)
    assert r['id']=='3:1:1'
    assert abs(r['curves'][0]['sampled_length']-16.371637) < 5e-6


def test_gilbert_hopf_link_parse_and_linking():
    from sst_pf_binary_falsifier.ideal_db import load_link_record, audit_record
    r=audit_record(load_link_record('L2a1'),linking=True)
    assert r['component_count']==2
    assert len(r['linking_pairs'])==1
    assert abs(abs(r['linking_pairs'][0]['gauss_linking'])-1.0)<2e-3


def test_sst_core_scaling_maps_D_to_2rc():
    from sst_pf_binary_falsifier.constants import R_C
    from sst_pf_binary_falsifier.ideal_db import load_knot_record, audit_record
    r=audit_record(load_knot_record('3:1:1'),scale_mode='sst_core',linking=False)
    expected=16.371637*(2*R_C)
    assert abs(r['curves'][0]['target_length']/expected-1)<1e-14


def test_multicomponent_system_single_component_matches_old_kernel():
    from sst_pf_binary_falsifier.core import torus_knot, filament_energy, filament_system_energy
    p=torus_knot(32)
    a=filament_energy(p,force_python=True); b=filament_system_energy([p],force_python=True)
    assert abs(a-b)/abs(a)<1e-13
