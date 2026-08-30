"""Tests for output zip naming, size classes, split/join, and packing."""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("output_zip_policy.py")
MIB = 1024 * 1024


def _load():
    spec = importlib.util.spec_from_file_location("output_zip_policy", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_output_zip_path_matches_trefoil():
    p = _load()
    pack = Path("KnotPlot") / "Trefoil_Balance_Point_Campaign_v0.2.3"
    assert p.output_zip_path(pack) == Path(
        "KnotPlot"
    ) / "Trefoil_Balance_Point_Campaign_v0.2.3_outputs.zip"


def test_part_path_and_parse():
    p = _load()
    z = Path("SST_x") / "SST_x_v0.1.0_outputs.zip"
    part = p.part_path(z, 3)
    assert part.name == "SST_x_v0.1.0_outputs.zip.part03"
    assert p.parse_part_name(part.name) == ("SST_x_v0.1.0_outputs.zip", 3)
    assert p.parse_part_name("SST_x_v0.1.0_outputs.zip") is None


def test_output_zip_class():
    p = _load()
    assert p.output_zip_class(49 * MIB) == "single"
    assert p.output_zip_class(50 * MIB) == "parts"
    assert p.output_zip_class(499 * MIB) == "parts"
    assert p.output_zip_class(500 * MIB) == "local_only"


def test_is_commitable_skips_restore_keeps_sibling_and_parts(tmp_path):
    p = _load()
    pack = tmp_path / "Fam" / "Pack_v0.1.0"
    pack.mkdir(parents=True)
    small = p.output_zip_path(pack)
    small.write_bytes(b"x" * 100)
    restore = tmp_path / "Restore_Archives" / "Falsifiers" / "Pack_v0.1.0_outputs.zip"
    restore.parent.mkdir(parents=True)
    restore.write_bytes(b"z" * 100)
    part = tmp_path / "Fam" / "Pack_v0.2.0_outputs.zip.part01"
    part.write_bytes(b"part")
    assert p.is_commitable_output_artifact(small)
    assert not p.is_commitable_output_artifact(restore)
    assert p.is_commitable_output_artifact(part)


def test_split_join_roundtrip(tmp_path):
    p = _load()
    z = tmp_path / "Pack_v0.1.0_outputs.zip"
    payload = bytes([7]) * (50 * MIB + 2048)
    z.write_bytes(payload)
    parts = p.split_zip_into_parts(z)
    assert len(parts) == 2
    assert parts[0].stat().st_size == 50 * MIB
    z.unlink()
    p.join_zip_parts(z)
    assert z.read_bytes() == payload
    assert (tmp_path / "Pack_v0.1.0_outputs.zip.parts.json").is_file()


def test_split_skips_small(tmp_path):
    p = _load()
    small = tmp_path / "a_outputs.zip"
    small.write_bytes(b"tiny")
    assert p.split_zip_into_parts(small) == []


def test_pack_output_dirs(tmp_path):
    p = _load()
    pack = tmp_path / "Fam" / "Blind_v0.1.0"
    out = pack / "outputs" / "run"
    out.mkdir(parents=True)
    (out / "a.npz").write_bytes(b"npz")
    (pack / "README.md").write_text("src", encoding="utf-8")
    dest = p.pack_output_dirs(pack)
    assert dest == p.output_zip_path(pack)
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    assert "outputs/run/a.npz" in names
    assert "README.md" not in names
    assert p.prepare_output_archive_for_git(dest) == [dest]


def test_prepare_parts_for_git(tmp_path):
    p = _load()
    z = tmp_path / "Blind_v0.1.0_outputs.zip"
    z.write_bytes(b"Q" * (50 * MIB + 10))
    git_paths = p.prepare_output_archive_for_git(z)
    names = {q.name for q in git_paths}
    assert "Blind_v0.1.0_outputs.zip" not in names
    assert "Blind_v0.1.0_outputs.zip.part01" in names
    assert "Blind_v0.1.0_outputs.zip.parts.json" in names
