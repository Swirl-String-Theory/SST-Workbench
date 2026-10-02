from sklsa.parent import locate_e010_output
from sklsa.loaders import load_topology_bundle
from sklsa.analysis import admission_record, join_carriers, representative_rows, consensus_rows, build_availability


def test_mirror_does_not_inflate_provider_count(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    bundle = load_topology_bundle(out, "8_5")
    carriers = join_carriers(bundle)
    strict = representative_rows(carriers, "strict_upstream")
    assert {r["provider_group"] for r in strict} == {"fremlin", "gilbert"}
    assert len(strict) == 2
    mirror = next(r for r in carriers if r["source_family"] == "knotplot_fourier_series")
    assert mirror["analysis_evidence_class"] == "MIRROR"


def test_writhe_absolute_consensus_ignores_orientation_sign(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    bundle = load_topology_bundle(out, "8_5")
    strict = representative_rows(join_carriers(bundle), "strict_upstream")
    rows = consensus_rows("8_5", strict, ["Wr", "Wr_abs"], "strict_upstream")
    signed = next(r for r in rows if r["metric"] == "Wr")
    absrow = next(r for r in rows if r["metric"] == "Wr_abs")
    assert signed["n"] == 2 and absrow["n"] == 2
    assert absrow["relative_span"] < signed["relative_span"]


def test_availability_comes_from_e010_matrix(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    bundle = load_topology_bundle(out, "8_5")
    carriers = join_carriers(bundle)
    rows = build_availability(bundle, ["fremlin_fourier", "ridgerunner"], carriers)
    fremlin = next(r for r in rows if r["source_family"] == "fremlin_fourier")
    rr = next(r for r in rows if r["source_family"] == "ridgerunner")
    assert fremlin["availability_status"] == "QUALIFIED_BY_E010"
    assert fremlin["literature_gate_pass_carriers"] == 1
    assert rr["availability_status"] == "ABSENT"


def test_per_topology_literature_admission(synthetic_workbench):
    out = locate_e010_output(synthetic_workbench)
    good = load_topology_bundle(out, "8_5")
    bad = load_topology_bundle(out, "3_1")
    passed = {"8_5"}
    assert admission_record(good, passed)["admission_status"] == "ADMITTED_ALL_E010_CARRIERS_PASS"
    rec = admission_record(bad, passed)
    assert rec["admission_status"] == "ADMITTED_WITH_CARRIER_EXCLUSIONS"
    assert rec["admitted"] is True
    assert rec["literature_admitted_carrier_count"] == 2
    assert rec["literature_excluded_carrier_count"] == 1
    assert rec["literature_gate_failure_counts"]["G2_writhe_quadratic_convergence"] == 1
