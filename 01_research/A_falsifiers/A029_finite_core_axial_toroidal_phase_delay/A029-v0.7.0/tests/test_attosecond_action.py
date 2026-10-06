import json
import numpy as np

from sst_finite_core_falsifier.attosecond_action import (
    cumulative_specific_action,
    effective_parcel_specific_lagrangian,
    delta_specific_lagrangian_from_euler_fields,
    existing_modal_phase_classification,
    export_from_contract_file,
    stationary_delay_action,
)


def clean_meta():
    return {
        "physical_scale_status": "INDEPENDENT_PHYSICAL_SCALE",
        "free_attosecond_phase_fit_parameters": 0,
        "depends_on_h": False,
        "depends_on_hbar": False,
        "depends_on_compton_radius": False,
        "depends_on_electron_mass": False,
        "depends_on_alpha": False,
    }



def test_effective_parcel_lagrangian_dimensions_and_difference():
    v0=np.array([[1.0,0.0,0.0],[2.0,0.0,0.0]])
    v1=np.array([[2.0,0.0,0.0],[3.0,0.0,0.0]])
    p0=np.array([2.0,4.0]); p1=np.array([3.0,5.0]); rho=2.0
    l0=effective_parcel_specific_lagrangian(v0,p0,rho)
    assert np.allclose(l0,[0.5-1.0,2.0-2.0])
    d=delta_specific_lagrangian_from_euler_fields(v1,p1,v0,p0,rho)
    assert np.allclose(d, effective_parcel_specific_lagrangian(v1,p1,rho)-l0)

def test_specific_lagrangian_integrates_to_specific_action():
    t = np.array([0., 1., 2.])
    q = np.array([2., 2., 2.])
    s = cumulative_specific_action(t, q)
    assert np.allclose(s[0], [0., 2., 4.])


def test_delay_energy_units_relation():
    e = np.array([3., 4.])
    dt = np.array([2., -1.])
    assert np.allclose(stationary_delay_action(e, dt), [-6., 4.])


def test_legacy_modal_phase_is_not_promoted():
    q = existing_modal_phase_classification({"loop_phase": 0.3, "tau_return": 12.0})
    assert q["status"] == "DIMENSIONLESS_MODAL_PHASE_ONLY"
    assert q["qualifies_as_specific_action"] is False


def test_export_lagrangian_contract(tmp_path):
    t = np.linspace(0, 2e-15, 101)
    q = np.vstack([np.sin(np.linspace(0, np.pi, 101))*2e11,
                   np.cos(np.linspace(0, np.pi, 101))*1e11])
    np.savez(tmp_path/"producer.npz", t_s=t, delta_specific_lagrangian_m2_s2=q)
    contract = {
        "mode": "specific_lagrangian_timeseries",
        "npz": "producer.npz",
        "provenance": clean_meta(),
    }
    p = tmp_path/"contract.json"; p.write_text(json.dumps(contract), encoding="utf-8")
    r = export_from_contract_file(p, tmp_path/"out")
    assert r["status"] == "DERIVED_SPECIFIC_ACTION"
    assert r["gates"]["A29A2_SPECIFIC_ACTION_DIMENSIONAL_CLOSURE"]["status"] == "PASS"


def test_stationary_delay_is_conditional_without_derivation(tmp_path):
    np.savez(tmp_path/"producer.npz", specific_energy_m2_s2=np.ones((2,3))*4., delta_t_s=np.ones((2,3))*1e-3)
    contract = {"mode":"stationary_delay_energy", "npz":"producer.npz", "provenance":clean_meta()}
    p=tmp_path/"contract.json"; p.write_text(json.dumps(contract), encoding="utf-8")
    r=export_from_contract_file(p,tmp_path/"out")
    assert r["status"] == "CONDITIONAL_SPECIFIC_ACTION"
