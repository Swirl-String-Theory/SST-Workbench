from __future__ import annotations

import json
import sys
from pathlib import Path

from sst_kelvin_workbench import build_ext_if_needed as b


def test_windows_link_args_select_single_existing_import_library(monkeypatch, tmp_path: Path):
    maj, minor = sys.version_info[:2]
    (tmp_path / f"python{maj}{minor}.lib").write_bytes(b"")
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.setattr(b, "_candidate_python_lib_dirs", lambda: [tmp_path])
    args = b._python_link_args_for_windows()
    link_args = [x for x in args if x.startswith("-l")]
    assert link_args == [f"-lpython{maj}{minor}"]
    assert f"-lpython{maj}.{minor}" not in args


def test_windows_link_args_fallback_is_single_name(monkeypatch):
    maj, minor = sys.version_info[:2]
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.setattr(b, "_candidate_python_lib_dirs", lambda: [])
    args = b._python_link_args_for_windows()
    assert args == [f"-lpython{maj}{minor}"]


def test_setuptools_fallback_declares_only_real_python_package():
    src = b._setuptools_setup_source()
    assert "packages=['sst_kelvin_workbench']" in src
    assert "Extension('sst_kelvin_workbench._native'" in src


def test_windows_build_prefers_setuptools_msvc(monkeypatch, tmp_path: Path):
    out = tmp_path / "_native.pyd"
    stamp = tmp_path / "stamp.json"
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.delenv("SST_KELVIN_ALLOW_MINGW", raising=False)
    monkeypatch.setattr(b, "have_pybind11", lambda: True)
    monkeypatch.setattr(b, "extension_path", lambda: out)
    monkeypatch.setattr(b, "BUILD", tmp_path)
    monkeypatch.setattr(b, "STAMP", stamp)
    monkeypatch.setattr(b, "CPP", tmp_path / "native.cpp")
    b.CPP.write_text("// stub\n", encoding="utf-8")
    monkeypatch.setattr(b, "_hash_files", lambda _paths: "deadbeef")
    monkeypatch.setenv("CXX", "C:\\workspace\\Strawberry\\c\\bin\\c++.EXE")

    calls: list[str] = []

    def fake_setuptools(_out: Path, _verbose: bool) -> bool:
        calls.append("setuptools")
        out.write_bytes(b"pyd")
        return True

    def fake_run(_cmd: list[str], _cwd: Path, _verbose: bool) -> bool:
        calls.append("direct")
        return False

    monkeypatch.setattr(b, "_build_with_setuptools", fake_setuptools)
    monkeypatch.setattr(b, "_run", fake_run)

    assert b.build_if_needed(force=True, verbose=False) is True
    assert calls == ["setuptools"]
    meta = json.loads(stamp.read_text(encoding="utf-8"))
    assert meta["builder"] == "setuptools-msvc"


def test_windows_mingw_opt_in_uses_direct_compiler(monkeypatch, tmp_path: Path):
    out = tmp_path / "_native.pyd"
    stamp = tmp_path / "stamp.json"
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.setenv("SST_KELVIN_ALLOW_MINGW", "1")
    monkeypatch.setattr(b, "have_pybind11", lambda: True)
    monkeypatch.setattr(b, "extension_path", lambda: out)
    monkeypatch.setattr(b, "BUILD", tmp_path)
    monkeypatch.setattr(b, "STAMP", stamp)
    monkeypatch.setattr(b, "CPP", tmp_path / "native.cpp")
    b.CPP.write_text("// stub\n", encoding="utf-8")
    monkeypatch.setattr(b, "_hash_files", lambda _paths: "cafe")
    monkeypatch.setattr(b.shutil, "which", lambda _name: "g++")
    monkeypatch.delenv("CXX", raising=False)

    calls: list[str] = []

    def fake_setuptools(_out: Path, _verbose: bool) -> bool:
        calls.append("setuptools")
        return False

    def fake_run(cmd: list[str], _cwd: Path, _verbose: bool) -> bool:
        calls.append("direct")
        assert cmd[0] == "g++"
        out.write_bytes(b"pyd")
        return True

    monkeypatch.setattr(b, "_build_with_setuptools", fake_setuptools)
    monkeypatch.setattr(b, "_run", fake_run)
    monkeypatch.setattr(
        b.subprocess,
        "check_output",
        lambda *_a, **_k: "-I/pybind11",
    )
    monkeypatch.setattr(b, "_python_link_args_for_windows", lambda: [])

    assert b.build_if_needed(force=True, verbose=False) is True
    assert calls == ["direct"]
    meta = json.loads(stamp.read_text(encoding="utf-8"))
    assert meta["builder"] == "g++"


def test_stale_builder_stamp_triggers_rebuild(monkeypatch, tmp_path: Path):
    out = tmp_path / "_native.pyd"
    out.write_bytes(b"old")
    stamp = tmp_path / "stamp.json"
    stamp.write_text(
        json.dumps({"hash": "same", "builder": "C:\\mingw\\c++.exe", "ext": out.name}),
        encoding="utf-8",
    )
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.delenv("SST_KELVIN_ALLOW_MINGW", raising=False)
    monkeypatch.setattr(b, "have_pybind11", lambda: True)
    monkeypatch.setattr(b, "extension_path", lambda: out)
    monkeypatch.setattr(b, "BUILD", tmp_path)
    monkeypatch.setattr(b, "STAMP", stamp)
    monkeypatch.setattr(b, "CPP", tmp_path / "native.cpp")
    b.CPP.write_text("// stub\n", encoding="utf-8")
    monkeypatch.setattr(b, "_hash_files", lambda _paths: "same")

    rebuilt = {"n": 0}

    def fake_setuptools(_out: Path, _verbose: bool) -> bool:
        rebuilt["n"] += 1
        out.write_bytes(b"new")
        return True

    monkeypatch.setattr(b, "_build_with_setuptools", fake_setuptools)
    assert b.build_if_needed(force=False, verbose=False) is True
    assert rebuilt["n"] == 1
    meta = json.loads(stamp.read_text(encoding="utf-8"))
    assert meta["builder"] == "setuptools-msvc"
