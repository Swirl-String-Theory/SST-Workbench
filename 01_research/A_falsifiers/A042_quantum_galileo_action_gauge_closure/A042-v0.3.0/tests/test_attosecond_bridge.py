from pathlib import Path
import json
import numpy as np

from sst_qgi.attosecond_bridge import producer_provenance_ok, run_attosecond_bridge_gate


def _cfg():
    return {
        "project_name": "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.3.0",
        "attosecond_bridge": {
            "bundle_npz": "data/attosecond/prepared/action_kernel_bundle.npz",
            "provenance_json": "data/attosecond/prepared/action_provenance.json",
            "global_phase_null_rel_max": 1e-12,
            "relative_phase_rms_floor_rad": 1e-12,
            "linearization_phase_max_rad": 0.05,
        },
    }


def _meta():
    return {
        "status": "DERIVED_SPECIFIC_ACTION",
        "source_model": "unit-test",
        "free_phase_fit_parameters": 0,
        "mapping_to_attosecond_kernel": "PHYSICALLY_DERIVED_AND_FROZEN",
        "depends_on_h": False,
        "depends_on_hbar": False,
        "depends_on_compton_radius": False,
        "depends_on_electron_mass": False,
        "depends_on_alpha": False,
    }


def test_provenance_rejects_free_phase_fit():
    m = _meta(); m["free_phase_fit_parameters"] = 1
    ok, reasons = producer_provenance_ok(m)
    assert not ok and reasons


def test_missing_data_is_not_run(tmp_path):
    qgi = {"available": True, "h_over_m_m2_s": 4e-7, "source_grade": "RAW_POPULATION_CSV"}
    r = run_attosecond_bridge_gate(tmp_path, _cfg(), qgi=qgi, mode="basic")
    assert r["status"] == "NOT_RUN"


def test_target_blind_forward_bridge(tmp_path):
    p = tmp_path / "data/attosecond/prepared"; p.mkdir(parents=True)
    t = np.linspace(-2, 2, 401)
    w = np.gradient(t)
    kernel = np.vstack([
        np.exp(-t*t) * np.exp(1j*0.2*t),
        np.exp(-0.8*t*t) * np.exp(-1j*0.15*t),
    ])
    # h/m=4e-7 => hbar/m≈6.37e-8; this produces a small relative phase.
    ds = np.vstack([1e-10*t, -1.5e-10*t])
    np.savez(p/"action_kernel_bundle.npz", kernel_re=kernel.real, kernel_im=kernel.imag,
             weights=w, delta_specific_action_m2_s=ds,
             energy_eV=np.array([100., 150.]), theta_rad=np.array([0., 3.14159]),
             delay_s=np.array([0., 1e-16]), direction=np.array([1, -1]))
    (p/"action_provenance.json").write_text(json.dumps(_meta()), encoding="utf-8")
    qgi = {"available": True, "h_over_m_m2_s": 4e-7, "source_grade": "RAW_POPULATION_CSV"}
    r = run_attosecond_bridge_gate(tmp_path, _cfg(), qgi=qgi, mode="basic")
    assert r["status"] == "READY"
    assert r["gates"]["G13_ATTOS_ACTION_PRODUCER_PROVENANCE"]["status"] == "PASS"
    assert r["gates"]["G14_TARGET_BLIND_ACTION_TO_PHASE"]["planck_target_used"] is False
    assert r["gates"]["G15_GLOBAL_PHASE_NULL"]["status"] == "PASS"
    assert r["gates"]["G16_RELATIVE_PHASE_OBSERVABILITY"]["status"] == "PASS"
