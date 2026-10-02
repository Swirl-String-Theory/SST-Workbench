"""E010-v0.1.1 packaging tests (geometry may be absent)."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_version_and_project():
    init = (ROOT / "pklsa" / "__init__.py").read_text(encoding="utf-8")
    assert "0.1.1" in init
    proj = json.loads((ROOT / "project.json").read_text(encoding="utf-8"))
    assert proj["catalog_id"] == "E010"
    assert proj["version"] == "v0.1.1"
    assert proj.get("geometry_status") == "MISSING_NPZ"


def test_manifest_lists_npz():
    man = json.loads((ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    npz = [f for f in man["files"] if f["path"].endswith(".npz")]
    assert len(npz) == 98


def test_geometry_restore_doc_present():
    assert (ROOT / "GEOMETRY_RESTORE.md").is_file()
