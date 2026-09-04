"""CMD paths.cmd must match the Python resolver."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import sst_workbench_paths as swp  # noqa: E402

PATHS_CMD = WB / "07_scripts" / "paths.cmd"


@pytest.mark.skipif(os.name != "nt", reason="paths.cmd is Windows CMD")
def test_paths_cmd_exists():
    assert PATHS_CMD.is_file()


def _run_paths_cmd(cwd: Path, *, extra_env: dict | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in (
        "SST_WORKBENCH_ROOT",
        "SST_DATA_ROOT",
        "SST_KNOT_DATASET",
        "SST_IDEAL_SOURCES",
        "SST_KATLAS_SOURCES",
        "SST_FSERIES_ROOT",
    ):
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)

    script = f'''
@echo off
call "{PATHS_CMD}"
if errorlevel 1 exit /b 1
echo SST_WORKBENCH_ROOT=%SST_WORKBENCH_ROOT%
echo SST_DATA_ROOT=%SST_DATA_ROOT%
echo SST_KNOT_DATASET=%SST_KNOT_DATASET%
echo SST_IDEAL_SOURCES=%SST_IDEAL_SOURCES%
echo SST_FSERIES_ROOT=%SST_FSERIES_ROOT%
'''
    bat = cwd / "_probe_paths.cmd"
    bat.write_text(script, encoding="utf-8")
    # /d disables CMD AutoRun (machine AutoRun can fail and poison errorlevel).
    proc = subprocess.run(
        ["cmd", "/d", "/c", str(bat)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"paths.cmd failed rc={proc.returncode}\n"
            f"stdout={proc.stdout}\nstderr={proc.stderr}"
        )
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line and line.startswith("SST_"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


@pytest.mark.skipif(os.name != "nt", reason="paths.cmd is Windows CMD")
@pytest.mark.parametrize(
    "rel_cwd",
    [
        ".",
        "scripts",
        "07_scripts",
        "SST_Fourier_vs_Ideal_Blind_Falsifier",
    ],
)
def test_paths_cmd_matches_python_from_depth(rel_cwd, tmp_path):
    cwd = (WB / rel_cwd).resolve()
    assert cwd.is_dir()
    got = _run_paths_cmd(cwd)

    # Align Python resolution to the same cleared env
    for key in (
        "SST_WORKBENCH_ROOT",
        "SST_DATA_ROOT",
        "SST_KNOT_DATASET",
        "SST_IDEAL_SOURCES",
        "SST_FSERIES_ROOT",
    ):
        os.environ.pop(key, None)

    assert Path(got["SST_WORKBENCH_ROOT"]).resolve() == swp.workbench_root()
    assert Path(got["SST_DATA_ROOT"]).resolve() == swp.data_root()
    assert Path(got["SST_KNOT_DATASET"]).resolve() == swp.knot_dataset()
    assert Path(got["SST_IDEAL_SOURCES"]).resolve() == swp.ideal_sources()
    assert Path(got["SST_FSERIES_ROOT"]).resolve() == swp.fseries_root()


@pytest.mark.skipif(os.name != "nt", reason="paths.cmd is Windows CMD")
def test_paths_cmd_env_override(tmp_path):
    marker = tmp_path / swp.ROOT_MARKER
    marker.write_text("catalog_schema: 1\n", encoding="utf-8")
    (tmp_path / "03_data").mkdir()
    got = _run_paths_cmd(
        tmp_path,
        extra_env={"SST_WORKBENCH_ROOT": str(tmp_path)},
    )
    assert Path(got["SST_WORKBENCH_ROOT"]).resolve() == tmp_path.resolve()
    assert Path(got["SST_DATA_ROOT"]).resolve() == (tmp_path / "03_data").resolve()
