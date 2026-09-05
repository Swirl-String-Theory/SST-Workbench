"""SP11: archive zips are staged only when every member has a hash twin."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sp11_decommission as sp11  # noqa: E402


def _make_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def test_safe_when_all_members_match(tmp_path: Path):
    extracted = tmp_path / "tree"
    extracted.mkdir()
    (extracted / "a.txt").write_bytes(b"alpha")
    sub = extracted / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"\x01\x02")
    zpath = tmp_path / "bundle.zip"
    _make_zip(zpath, {"a.txt": b"alpha", "sub/b.bin": b"\x01\x02"})
    ok, reason = sp11.archive_zip_safe_to_stage(zpath, extracted)
    assert ok is True
    assert reason == "all_members_hash_match"


def test_unsafe_when_member_missing(tmp_path: Path):
    extracted = tmp_path / "tree"
    extracted.mkdir()
    (extracted / "a.txt").write_bytes(b"alpha")
    zpath = tmp_path / "bundle.zip"
    _make_zip(zpath, {"a.txt": b"alpha", "missing.txt": b"nope"})
    ok, reason = sp11.archive_zip_safe_to_stage(zpath, extracted)
    assert ok is False
    assert reason.startswith("missing_extracted:")


def test_unsafe_on_hash_mismatch(tmp_path: Path):
    extracted = tmp_path / "tree"
    extracted.mkdir()
    (extracted / "a.txt").write_bytes(b"alpha")
    zpath = tmp_path / "bundle.zip"
    _make_zip(zpath, {"a.txt": b"BETA!"})
    ok, reason = sp11.archive_zip_safe_to_stage(zpath, extracted)
    assert ok is False
    assert reason.startswith("hash_mismatch:") or reason.startswith("size_mismatch:")


def test_unsafe_without_extracted_root(tmp_path: Path):
    zpath = tmp_path / "bundle.zip"
    _make_zip(zpath, {"a.txt": b"x"})
    ok, reason = sp11.archive_zip_safe_to_stage(zpath, tmp_path / "nope")
    assert ok is False
    assert reason == "extracted_root_missing"
