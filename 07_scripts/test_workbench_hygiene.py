"""Tests for beside-pack zip copy and DELETE relocate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("workbench_hygiene.py")
MIB = 1024 * 1024


def _load():
    spec = importlib.util.spec_from_file_location("workbench_hygiene", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_canonical_zip_basename():
    m = _load()
    assert m.canonical_zip_basename("foo_v0.1.0 (1).zip") == "foo_v0.1.0.zip"


def test_copy_if_missing(tmp_path):
    m = _load()
    src = tmp_path / "src.zip"
    dest = tmp_path / "fam" / "src.zip"
    src.write_bytes(b"abc")
    assert m.copy_if_missing(src, dest) == "copy"
    assert dest.read_bytes() == b"abc"
    assert m.copy_if_missing(src, dest) == "skip_exists"
    assert src.exists()


def test_relocate_to_delete_preserves_relative_path(tmp_path):
    m = _load()
    wb = tmp_path / "SST-Workbench"
    pack = wb / "Fam" / "Pack_v0.2.2.5"
    pack.mkdir(parents=True)
    (pack / "README.md").write_text("x", encoding="utf-8")
    delete_root = tmp_path / "DELETE"
    dest = m.relocate_to_delete(pack, wb, delete_root)
    assert dest == delete_root / "Fam" / "Pack_v0.2.2.5"
    assert (dest / "README.md").read_text(encoding="utf-8") == "x"
    assert not pack.exists()


def test_plan_family_zip_copies_skips_outputs_and_large(tmp_path):
    m = _load()
    wb = tmp_path / "wb"
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (wb / "SST_Intrinsic_Modal_Swirl_Clock").mkdir(parents=True)
    (wb / "SST_Katlas_Link_Geometry_Conditioning_v2.0.0").mkdir(parents=True)
    small = downloads / "SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.7.zip"
    small.write_bytes(b"src")
    out_zip = downloads / "SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2_outputs.zip"
    out_zip.write_bytes(b"out")
    katlas = downloads / "SST_Katlas_Link_Geometry_Conditioning_v2.0.0.zip"
    katlas.write_bytes(b"kat")
    planned = m.plan_family_zip_copies(wb, downloads)
    names = {src.name for src, _dest in planned}
    assert small.name in names
    assert out_zip.name not in names
    assert katlas.name in names
    dests = {dest for _src, dest in planned}
    assert any(d.name == katlas.name and "Katlas_Link_Geometry" in str(d) for d in dests)


def test_should_untrack_rel(tmp_path):
    import importlib.util

    pol_path = Path(__file__).with_name("output_zip_policy.py")
    spec = importlib.util.spec_from_file_location("output_zip_policy", pol_path)
    pol = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pol)
    m = _load()
    wb = tmp_path
    pack = wb / "Fam" / "Pack_v0.1.0"
    pack.mkdir(parents=True)
    z = pack.parent / "Pack_v0.1.0_outputs.zip"
    z.write_bytes(b"ok")
    (wb / "Restore_Archives" / "Falsifiers").mkdir(parents=True)
    rz = wb / "Restore_Archives" / "Falsifiers" / "x.zip"
    rz.write_bytes(b"r")
    generic = pack.parent / "dataset_official.zip"
    generic.write_bytes(b"ds")
    assert not m.should_untrack_rel("Fam/Pack_v0.1.0_outputs.zip", wb, pol)
    assert not m.should_untrack_rel("Fam/dataset_official.zip", wb, pol)
    assert m.should_untrack_rel("Restore_Archives/Falsifiers/x.zip", wb, pol)
    assert m.should_untrack_rel("Fam/Pack_v0.1.0/outputs/a.npz", wb, pol)
    assert m.should_untrack_rel("Fam/Pack_v0.1.0/src/a.npz", wb, pol)
    assert not m.should_untrack_rel("Fam/Pack_v0.1.0/src/run.py", wb, pol)
