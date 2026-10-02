"""Unit tests for consolidate_archives classification and collision handling."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("consolidate_archives.py")


def _load():
    spec = importlib.util.spec_from_file_location("consolidate_archives", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    import sys

    sys.modules["consolidate_archives"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_classify_key_themes():
    m = _load()
    assert m.classify("SST_fermat_pybind_research_v0.6.1.zip")[0] == "Fermat"
    assert m.classify("SST_routeB_RT_bem_research_v18.zip")[0] == "RouteB_BEM"
    assert m.classify("sst_chi_phase_package_v16B0.zip")[0] == "ChiPhase"
    assert m.classify("vortexring-lab-v7.6.22-package.zip")[0] == "VortexLab"
    assert m.classify("SST_CANON-v0.8.23-release.zip")[0] == "Canon"
    assert m.classify("SST_Route_I_relative_entropy_PoC_v0.1.0.zip")[0] == "Route_I"
    assert m.classify("SST_contact_billiard_hydrodynamic_falsifier_v0.2.0.zip")[0] == (
        "ContactBilliard"
    )
    assert m.classify("triple_gear_blender_package.zip")[0] == "TripleGear"
    assert m.classify("totally_unknown_blob.zip")[0] == "Misc"


def test_classify_archive_ingest_themes():
    m = _load()
    assert m.classify("1_Maxwell_SST_Kinetic_Falsifier_v0.3.1.zip")[0] == "Maxwell"
    assert m.classify("Kelvin_Joule_SST_Transient_Energy_Falsifier_v0.1.0.zip")[0] == (
        "KelvinFloquet"
    )
    assert m.classify("Kelvin_Kirchhoff_SST_Falsifier_v0.1.1.zip")[0] == "KelvinFloquet"
    assert (
        m.classify(
            "SST_Finite_Core_Axial_Toroidal_Phase_Delay_Blind_Falsifier_v0.1.0.zip"
        )[0]
        == "Falsifiers"
    )
    assert m.classify("Einstein_SST_Emergent_Metric_Poisson_Closure_Gates_v0.1.1.zip")[0] == (
        "Falsifiers"
    )
    assert m.classify("Helmholtz_SST_Vortex_Gates_Falsifier_v0.1.0.zip")[0] == "Falsifiers"
    assert (
        m.classify("KnotPlot_3p1_Comprehensive_Dynamics_Parameter_Atlas_v0.3.0.zip")[0]
        == "KnotPlot"
    )
    assert m.classify("SST_Knot_Library_v0.2.5.zip")[0] == "KnotLibrary"
    assert m.classify("SST_Knot_Geometry_Library_v0.1.3.zip")[0] == "KnotLibrary"
    assert m.classify("SST_Katlas_Link_Geometry_Conditioning_v2.0.0.zip")[0] == (
        "KnotLibrary"
    )
    assert m.classify("SST_Trefoil_v0.3.0_with_Knot_Library_v0.2.5.zip")[0] == "Trefoil"
    assert (
        m.classify(
            "SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.0.zip"
        )[0]
        == "Falsifiers"
    )
    assert (
        m.classify(
            "SST_SCIII_Koopman_DMD_Complex_Phase_Clock_Blind_Falsifier_v0.1.0.zip"
        )[0]
        == "Falsifiers"
    )
    assert (
        m.classify("KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.7.zip")[0]
        == "KnotPlot"
    )


def test_classify_root_zip_themes():
    m = _load()
    assert m.classify("Independent_FiniteCore_SpectralSelector_v0.1.2.4.zip")[0] == (
        "DeriveConstants"
    )
    assert m.classify("SST_ideal_links_comprehensive_test_suite_v0.3.6.zip")[0] == (
        "IdealLinks"
    )
    assert m.classify("SST_v0.3.4_to_v0.3.4.1_CMD_runners_patch.zip")[0] == "IdealLinks"
    assert m.classify("SST_v0.3.3_continuum_ladder_runner.zip")[0] == "IdealLinks"
    assert m.classify("SST_Kelvin_Floquet_Workbench_cpp_pybind_v0.1.1.zip")[0] == (
        "KelvinFloquet"
    )
    assert m.classify("sst_relclock_checks.zip")[0] == "Dimensionless"
    assert m.classify("SST_counterpulley_alpha_falsifier_v0.5.0.zip")[0] == "Falsifiers"
    assert m.classify("SST_Hopf_cpp_pybind_v0.1.4.zip")[0] == "Hopf"
    assert m.classify("Ideal_Links_Comprehensive_Test_first-120_outputs_full.zip")[0] == (
        "IdealLinks"
    )


def test_iter_restore_root_zips(tmp_path, monkeypatch):
    m = _load()
    restore = tmp_path / "Restore_Archives"
    restore.mkdir()
    (restore / "Fermat").mkdir()
    root_zip = restore / "SST_ideal_links_comprehensive_test_suite_v0.3.0.zip"
    nested = restore / "Fermat" / "nested.zip"
    root_zip.write_bytes(b"a")
    nested.write_bytes(b"b")
    monkeypatch.setattr(m, "RESTORE", restore)
    found = m.iter_restore_root_zips()
    assert found == [root_zip]


def test_plan_misc_reclassify_ideal_links(tmp_path, monkeypatch):
    m = _load()
    restore = tmp_path / "Restore_Archives"
    misc = restore / "Misc"
    misc.mkdir(parents=True)
    src = misc / "SST_ideal_links_comprehensive_test_suite_v0.1.0.zip"
    src.write_bytes(b"ideal")
    monkeypatch.setattr(m, "RESTORE", restore)
    monkeypatch.setattr(m, "SOURCES_ZIPS", restore / "Sources_Zips")
    plans = m.plan_misc_reclassify()
    assert len(plans) == 1
    assert plans[0].theme == "IdealLinks"
    assert plans[0].action == "move"
    assert plans[0].dest == restore / "IdealLinks" / src.name


def test_classify_fermat_series():
    m = _load()
    theme, series = m.classify("SST_fermat_pybind_research_v0.6.1.zip")
    assert theme == "Fermat"
    assert series == "v0.6.1"


def test_dest_for_with_series():
    m = _load()
    dest = m.dest_for("SST_fermat_pybind_research_v0.6.1.zip", "Fermat", "v0.6.1")
    assert dest == m.RESTORE / "Fermat" / "v0.6.1" / "SST_fermat_pybind_research_v0.6.1.zip"


def test_resolve_collision_identical(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "RESTORE", tmp_path / "Restore_Archives")
    m.RESTORE.mkdir()
    dest_dir = m.RESTORE / "Fermat"
    dest_dir.mkdir()
    dest = dest_dir / "a.zip"
    src = tmp_path / "a.zip"
    payload = b"same-bytes"
    dest.write_bytes(payload)
    src.write_bytes(payload)
    plan = m.resolve_collision(src, dest, "__from_repo")
    assert plan.action == "delete_duplicate"


def test_resolve_collision_different(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "RESTORE", tmp_path / "Restore_Archives")
    m.RESTORE.mkdir()
    dest_dir = m.RESTORE / "Fermat"
    dest_dir.mkdir()
    dest = dest_dir / "a.zip"
    src = tmp_path / "a.zip"
    dest.write_bytes(b"old")
    src.write_bytes(b"new-content")
    plan = m.resolve_collision(src, dest, "__from_repo")
    assert plan.action == "move_renamed"
    assert plan.dest.name == "a__from_repo.zip"


def test_resolve_collision_fresh(tmp_path, monkeypatch):
    m = _load()
    monkeypatch.setattr(m, "RESTORE", tmp_path / "Restore_Archives")
    m.RESTORE.mkdir()
    dest = m.RESTORE / "Misc" / "fresh.zip"
    src = tmp_path / "fresh.zip"
    src.write_bytes(b"x")
    plan = m.resolve_collision(src, dest, "__from_repo")
    assert plan.action == "move"
    assert plan.dest == dest


def test_apply_plan_move_and_manifest(tmp_path, monkeypatch):
    m = _load()
    restore = tmp_path / "Restore_Archives"
    restore.mkdir()
    monkeypatch.setattr(m, "WB", tmp_path)
    monkeypatch.setattr(m, "RESTORE", restore)
    monkeypatch.setattr(m, "SOURCES_ZIPS", restore / "Sources_Zips")

    src_dir = tmp_path / "SST_fermat_pybind_research"
    src_dir.mkdir()
    src = src_dir / "SST_fermat_pybind_research_v0.1.zip"
    src.write_bytes(b"fermat-zip")

    theme, series = m.classify(src.name)
    dest = m.dest_for(src.name, theme, series)
    plans = [m.resolve_collision(src, dest, "__from_repo")]
    rows = m.apply_plan(plans, apply=True)
    assert not src.exists()
    assert dest.exists()
    assert dest.read_bytes() == b"fermat-zip"
    assert rows[0]["action"] == "move"
    assert rows[0]["theme"] == "Fermat"

    man = restore / "_MANIFEST.csv"
    m.write_manifest(rows, man)
    assert man.exists()
    text = man.read_text(encoding="utf-8")
    assert "Fermat" in text


def test_is_output_archive():
    m = _load()
    assert m.is_output_archive("Trefoil_Balance_Point_Campaign_v0.2.4_outputs.zip")
    assert m.is_output_archive("SST_pack_v0.2.2-outputs.zip")
    assert not m.is_output_archive(
        "SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.8.zip"
    )
    assert not m.is_output_archive(
        "Trefoil_Balance_Point_Campaign_v0.2.4.2_INCOMPLETE_CONTINUATION_RECOVERY_HOTFIX.zip"
    )


def test_plan_repo_skips_output_archives(tmp_path, monkeypatch):
    m = _load()
    wb = tmp_path / "wb"
    restore = wb / "Restore_Archives"
    restore.mkdir(parents=True)
    pack = wb / "KnotPlot"
    pack.mkdir()
    out_zip = pack / "Trefoil_Balance_Point_Campaign_v0.2.4_outputs.zip"
    out_zip.write_bytes(b"outputs")
    src_zip = pack / "Trefoil_Balance_Point_Campaign_v0.2.4.zip"
    src_zip.write_bytes(b"source")
    monkeypatch.setattr(m, "WB", wb)
    monkeypatch.setattr(m, "RESTORE", restore)
    monkeypatch.setattr(m, "SOURCES_ZIPS", restore / "Sources_Zips")
    names = {p.source.name for p in m.plan_repo()}
    assert "Trefoil_Balance_Point_Campaign_v0.2.4.zip" in names
    assert "Trefoil_Balance_Point_Campaign_v0.2.4_outputs.zip" not in names


def test_plan_downloads_copy_skip_duplicate(tmp_path, monkeypatch):
    m = _load()
    restore = tmp_path / "Restore_Archives"
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    dest_dir = restore / "Falsifiers"
    dest_dir.mkdir(parents=True)
    name = "SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.8.zip"
    payload = b"swirl-src"
    (dest_dir / name).write_bytes(payload)
    (downloads / name).write_bytes(payload)
    (downloads / "SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.7.zip").write_bytes(
        b"swirl-7"
    )
    monkeypatch.setattr(m, "RESTORE", restore)
    monkeypatch.setattr(m, "SOURCES_ZIPS", restore / "Sources_Zips")
    plans = m.plan_downloads_copy(downloads)
    by_name = {p.source.name: p for p in plans}
    assert by_name[name].action == "skip_duplicate"
    assert (
        by_name["SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.7.zip"].action
        == "copy"
    )
    m.apply_plan(plans, apply=True)
    assert (downloads / name).exists()
    assert (
        restore / "Falsifiers" / "SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.7.zip"
    ).exists()
