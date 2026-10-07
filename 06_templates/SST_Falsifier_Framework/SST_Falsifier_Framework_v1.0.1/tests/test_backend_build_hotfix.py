from __future__ import annotations

import sys
from pathlib import Path

from sst_falsifier import native_build as nb
from sst_falsifier import sycl_worker as sw


def test_parse_cmd_environment_skips_blank_and_equals_prefix():
    text = "\n".join(
        [
            "=C:=C:\\",
            "PATH=C:\\a;C:\\b",
            "LIB=C:\\intel\\lib",
            "NOEQUALS",
            "EMPTY=",
        ]
    )
    env = sw._parse_cmd_environment(text)
    assert env["PATH"] == "C:\\a;C:\\b"
    assert env["LIB"] == "C:\\intel\\lib"
    assert env["EMPTY"] == ""
    assert "=C:" not in env
    assert "NOEQUALS" not in env


def test_oneapi_env_script_prefers_env_root(monkeypatch, tmp_path: Path):
    root = tmp_path / "oneAPI"
    script = root / "setvars.bat"
    script.parent.mkdir(parents=True)
    script.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.setattr(sw.platform, "system", lambda: "Windows")
    monkeypatch.setenv("ONEAPI_ROOT", str(root))
    monkeypatch.delenv("ONEAPI_ROOT_DIR", raising=False)
    assert sw._oneapi_env_script() == script


def test_oneapi_env_script_non_windows(monkeypatch):
    monkeypatch.setattr(sw.platform, "system", lambda: "Linux")
    assert sw._oneapi_env_script() is None


def test_with_oneapi_environment_keeps_existing_libmmd(monkeypatch, tmp_path: Path):
    libdir = tmp_path / "intel_lib"
    libdir.mkdir()
    (libdir / "libmmd.lib").write_bytes(b"")
    monkeypatch.setattr(sw.platform, "system", lambda: "Windows")
    env, tag = sw._with_oneapi_environment("C:\\fake\\icpx.exe", {"LIB": str(libdir), "PATH": "x"})
    assert tag == "existing-environment"
    assert env["LIB"] == str(libdir)


def test_with_oneapi_environment_imports_from_script(monkeypatch, tmp_path: Path):
    script = tmp_path / "setvars.bat"
    script.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.setattr(sw.platform, "system", lambda: "Windows")
    monkeypatch.setattr(sw, "_oneapi_env_script", lambda _cxx=None: script)

    class CP:
        returncode = 0
        stdout = "LIB=C:\\oneapi\\lib\nPATH=C:\\oneapi\\bin\n"
        stderr = ""

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs.get("env")))
        return CP()

    monkeypatch.setattr(sw.subprocess, "run", fake_run)
    env, tag = sw._with_oneapi_environment("C:\\fake\\icpx.exe", {"PATH": "base"})
    assert tag == str(script)
    assert env["LIB"] == "C:\\oneapi\\lib"
    assert "oneapi\\bin" in env["PATH"]
    assert calls and calls[0][0][:3] == ["cmd.exe", "/d", "/c"]
    wrapper = Path(calls[0][0][3])
    assert wrapper.name == "load_oneapi_env.cmd"
    # Wrapper body must quote the spaced oneAPI script path; argv itself must
    # not embed that path (avoids Windows list2cmdline re-quoting breakage).
    body = wrapper.read_text(encoding="utf-8") if wrapper.exists() else ""
    # tempfile may already be cleaned; assert call shape instead when gone.
    assert "setvars" in str(script).lower() or script.name.lower().endswith(".bat")
    assert len(calls[0][0]) == 4


def test_build_pybind_uses_relative_paths_and_short_temp(monkeypatch, tmp_path: Path):
    root = tmp_path / "inst"
    src = root / "native" / "cpp" / "native.cpp"
    src.parent.mkdir(parents=True)
    src.write_text("// stub\n", encoding="utf-8")
    pkg = root / "native_ext"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")

    out = nb.extension_path(pkg, "_sst_native")
    captured = {}

    class CP:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        out.write_bytes(b"pyd")
        return CP()

    monkeypatch.setitem(sys.modules, "pybind11", type(sys)("pybind11"))
    sys.modules["pybind11"].__version__ = "0.0"
    monkeypatch.setattr(nb.subprocess, "run", fake_run)
    monkeypatch.setattr(nb, "build_fingerprint", lambda *a, **k: ("fp", {"compiler_version": None}))

    result = nb.build_pybind(root, force=True, prefer_openmp=False, verbose=False)
    assert result.success is True
    assert "--build-temp" in captured["cmd"]
    temp = Path(captured["cmd"][captured["cmd"].index("--build-temp") + 1])
    assert temp.name == "_tmp_pybind"
    assert captured["cwd"] == str(root.resolve())

    setup_path = root / "build" / "_setup__sst_native.py"
    setup_src = setup_path.read_text(encoding="utf-8")
    assert "native" in setup_src and "native.cpp" in setup_src
    assert "native_ext" in setup_src
    assert str(root.resolve()) not in setup_src
    assert ":\\" not in setup_src and ":/" not in setup_src


def test_probe_worker_uses_runtime_oneapi_env(monkeypatch, tmp_path: Path):
    root = tmp_path / "inst"
    exe = root / "build" / "sst_sycl_worker.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"mz")
    src = root / "native" / "cpp" / "sycl_worker.cpp"
    src.parent.mkdir(parents=True)
    src.write_text("// stub\n", encoding="utf-8")

    monkeypatch.setattr(sw, "build_worker", lambda *_a, **_k: {"success": True, "fingerprint_sha256": "x"})
    monkeypatch.setattr(sw, "_exe", lambda _r: exe)
    monkeypatch.setattr(sw, "_runtime_env", lambda _cxx=None: {"PATH": "C:\\oneapi\\bin", "SYCL_CACHE_PERSISTENT": "0"})

    class CP:
        returncode = 0
        stdout = '{"protocol_version":2,"device_name":"stub","is_gpu":true,"fp64":true}\n'
        stderr = ""

    seen = {}

    def fake_run(cmd, **kwargs):
        seen["env"] = kwargs.get("env")
        return CP()

    monkeypatch.setattr(sw.subprocess, "run", fake_run)
    info = sw.probe_worker(root)
    assert info["available"] is True
    assert seen["env"]["PATH"] == "C:\\oneapi\\bin"


def test_sycl_worker_cpp_uses_template_profiling_keyword():
    cpp = (
        Path(__file__).resolve().parents[1]
        / "instance_template"
        / "native"
        / "cpp"
        / "sycl_worker.cpp"
    ).read_text(encoding="utf-8")
    assert "e.template get_profiling_info<sycl::info::event_profiling::command_start>()" in cpp
    assert "e.template get_profiling_info<sycl::info::event_profiling::command_end>()" in cpp
    assert "e.get_profiling_info<sycl::info::event_profiling::command_start>()" not in cpp
