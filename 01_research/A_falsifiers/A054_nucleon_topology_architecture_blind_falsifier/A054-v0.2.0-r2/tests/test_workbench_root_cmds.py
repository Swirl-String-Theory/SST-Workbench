from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WB = r"C:\workspace\projects\SST-Workbench"
CMD_FILES = (
    "run_all.cmd",
    "run_all_extended.cmd",
    "run_all_full.cmd",
    "run_02_prepare_cert.cmd",
)


def test_run_cmds_resolve_default_workbench_root() -> None:
    for name in CMD_FILES:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert 'set "WB=%~1"' in text
        assert "SST_WORKBENCH_ROOT" in text
        assert DEFAULT_WB in text
        assert "SST-Workbench root not found" in text
        assert "Usage:" not in text


def test_run_all_cmds_pass_resolved_wb_to_prepare() -> None:
    for name in ("run_all.cmd", "run_all_extended.cmd", "run_all_full.cmd"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert 'call run_02_prepare_cert.cmd "!WB!"' in text
        assert 'call run_02_prepare_cert.cmd "%~1"' not in text
