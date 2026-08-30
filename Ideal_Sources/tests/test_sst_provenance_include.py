"""Offline tests for Ideal_Sources sst_provenance --include and inventory coverage."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_provenance import iter_init_files  # noqa: E402

EXPECTED_IDEALLINKS = [
    "IdealLinks.txt.gz",
    "IdealLinks_10a.txt.gz",
    "IdealLinks_10n.txt.gz",
    "IdealLinks_11a1.txt.gz",
    "IdealLinks_11a2.txt.gz",
    "IdealLinks_11n1.txt.gz",
    "IdealLinks_11n2.txt.gz",
]
EXPECTED_TWELVE = ["TwelveData.zip", "TwelveSummary.zip", "0TwelveData.csv"]


def test_iter_init_files_include_filters(tmp_path: Path):
    (tmp_path / "keep.gz").write_bytes(b"\x1f\x8b" + b"\x00" * 8)
    (tmp_path / "keep.zip").write_bytes(b"PK\x03\x04")
    (tmp_path / "noise.pdf").write_bytes(b"%PDF")
    (tmp_path / "SOURCE.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "sst_provenance.py").write_text("# no\n", encoding="utf-8")

    all_files = iter_init_files(tmp_path, None)
    assert {p.name for p in all_files} == {
        "keep.gz",
        "keep.zip",
        "noise.pdf",
        "SOURCE.md",
        "sst_provenance.py",
    }

    filtered = iter_init_files(tmp_path, ["*.gz", "*.zip", "*.csv", "SOURCE.md"])
    assert {p.name for p in filtered} == {"keep.gz", "keep.zip", "SOURCE.md"}


def test_source_md_lists_ideallinks_and_twelve():
    text = (ROOT / "SOURCE.md").read_text(encoding="utf-8")
    for name in EXPECTED_IDEALLINKS + EXPECTED_TWELVE:
        assert f"`{name}`" in text or name in text, f"SOURCE.md missing {name}"


def test_on_disk_inventory_matches_source_names():
    for name in EXPECTED_IDEALLINKS + EXPECTED_TWELVE + [
        "Ideal.txt.gz",
        "Ideal_11a.txt.gz",
        "Ideal_11n.txt.gz",
    ]:
        assert (ROOT / name).is_file(), f"missing on disk: {name}"


def test_manifest_includes_filtered_artifacts_only():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    paths = {a["path"] for a in manifest["artifacts"]}
    assert "TwelveData.zip" in paths
    assert "TwelveSummary.zip" in paths
    assert "IdealLinks_11n2.txt.gz" in paths
    assert "SOURCE.md" in paths
    # Must not have pulled in the PDF or the tool itself
    assert not any(p.endswith(".pdf") for p in paths)
    assert "sst_provenance.py" not in paths
    assert "PROVENANCE.md" not in paths


def test_cli_include_roundtrip(tmp_path: Path):
    import gzip

    (tmp_path / "a.gz").write_bytes(gzip.compress(b"hello\n"))
    (tmp_path / "b.pdf").write_bytes(b"%PDF")
    out = tmp_path / "M.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "sst_provenance.py"),
            "init",
            str(tmp_path),
            "-o",
            str(out),
            "--include",
            "*.gz",
            "--no-records",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "1 artifacts" in r.stdout
    m = json.loads(out.read_text(encoding="utf-8"))
    assert [a["path"] for a in m["artifacts"]] == ["a.gz"]
