
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_all_cmd_runners_use_shared_resolver():
    runners = sorted(ROOT.glob("run_*.cmd"))
    assert runners
    for runner in runners:
        text = runner.read_text(encoding="utf-8").lower()
        assert "scripts\\resolve_python.cmd" in text


def test_resolver_searches_parent_workbench_venv():
    text = (ROOT / "scripts" / "resolve_python.cmd").read_text(encoding="utf-8").lower()
    assert "..\\..\\.venv\\scripts\\python.exe" in text
