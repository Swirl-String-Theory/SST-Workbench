import math
import numpy as np

from pklsa_builder.models import QualificationConfig, Carrier
from pklsa_builder.qualification import qualify_components
from pklsa_builder.nonlocal_metrics import linking_number
from pklsa_builder.literature_gates import (
    IDEAL_TREFOIL_ROPELENGTH_DIAMETER,
    evaluate_contextual_literature_gates,
    torus_analytic_length_ratio,
)


def torus_knot(n=512, p=2, q=3, lam=0.35, R=1.0):
    alpha = np.linspace(0.0, 2.0 * math.pi * p, int(n), endpoint=False)
    w = q / p
    return np.column_stack([
        R * (1.0 + lam * np.cos(w * alpha)) * np.cos(alpha),
        R * (1.0 + lam * np.cos(w * alpha)) * np.sin(alpha),
        R * lam * np.sin(w * alpha),
    ])


def cfg():
    return QualificationConfig(
        resolution_ladder=[64, 128, 256],
        min_levels_for_resolution=3,
        resolved_rel_tol=0.1,
        converging_rel_tol=0.2,
        normalize_length=None,
        expensive_metrics=True,
        adaptive_stop=False,
        literature_gates=True,
        literature_gate_mode="enforce",
        writhe_order_min=1.5,
    )


def test_exact_polygon_linking_number_hopf_is_integer():
    n = 192
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    a = np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)])
    # Circle in x-z plane, offset so the two loops form a Hopf link without intersection.
    b = np.column_stack([0.5 + 0.6 * np.cos(t), np.zeros_like(t), 0.6 * np.sin(t)])
    lk = linking_number(a, b)
    assert abs(abs(lk) - 1.0) < 1e-10


def test_cantarella_writhe_gate_is_quadratic_on_smooth_torus_trefoil():
    q = qualify_components([torus_knot(1024)], cfg())
    g = q["literature_gates"]["gates"]["G2_writhe_quadratic_convergence"]
    assert g["status"] == "PASS"
    finite = [x for x in g["estimated_orders"] if math.isfinite(x)]
    assert finite and finite[-1] > 1.5


def test_signed_frenet_and_writhe_flip_under_mirror():
    p = torus_knot(768)
    qm = p.copy(); qm[:, 0] *= -1.0
    qa = qualify_components([p], cfg())
    qb = qualify_components([qm], cfg())
    ma = qa["levels"][-1]["component_metrics"][0]
    mb = qb["levels"][-1]["component_metrics"][0]
    wa = qa["levels"][-1]["metrics"]["Wr"]
    wb = qb["levels"][-1]["metrics"]["Wr"]
    assert ma["tau_signed_integral"] * mb["tau_signed_integral"] < 0
    assert wa * wb < 0
    assert abs(ma["tau_signed_integral"] + mb["tau_signed_integral"]) < 1e-8
    assert abs(wa + wb) < 1e-10


def test_oberti_ricca_torus_length_ratio_matches_direct_sampling():
    p, q, lam, R = 2, 3, 0.35, 1.7
    curve = torus_knot(200000, p=p, q=q, lam=lam, R=R)
    direct = np.linalg.norm(np.roll(curve, -1, axis=0) - curve, axis=1).sum() / (2 * math.pi * R)
    analytic = torus_analytic_length_ratio(p, q, lam, samples=200000)
    assert abs(direct - analytic) / analytic < 2e-8


def test_przybyl_pieranski_trefoil_reference_gate_passes_at_reference_value():
    carrier = Carrier(
        carrier_id="synthetic-ideal-3_1",
        topology_id="3_1",
        source_family="gilbert_ideal",
        source_role="ideal_reference",
        representation="synthetic",
    )
    qualification = {
        "levels": [{"resolution": 1024, "metrics": {"Rop": IDEAL_TREFOIL_ROPELENGTH_DIAMETER, "reach": 1.0, "Wr": 3.0}}],
        "scale_context": {"native_total_length": 1.0},
    }
    gates = evaluate_contextual_literature_gates(carrier, qualification, cfg())
    assert gates["B1_ideal_trefoil_ropelength"]["status"] == "PASS"
