"""Guard against version skew observed during v1.0.10 Windows qualification."""
from pathlib import Path
import tomllib
import ast
import sst_falsifier

ROOT = Path(__file__).resolve().parents[1]


def test_framework_version_identity():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    instance = (ROOT / "instance_template/falsifier.toml").read_text(encoding="utf-8")
    assert project["project"]["version"] == sst_falsifier.__version__ == "1.1.0"
    assert 'framework_version = "1.1.0"' in instance


def test_backend_report_derives_framework_version():
    src = (ROOT / "tools/backend_selftest.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert any(isinstance(n,ast.ImportFrom) and n.module == "sst_falsifier" and any(a.name=="__version__" and a.asname=="FRAMEWORK_VERSION" for a in n.names) for n in tree.body)
    assert '"framework_version":FRAMEWORK_VERSION' in src
    assert "SKIPPED (--skip-cpp)" in src
    assert '"framework_version":"1.0.9"' not in src
