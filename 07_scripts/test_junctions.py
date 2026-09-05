"""Tests for 07_scripts/junctions.py (SP02)."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import junctions as jn  # noqa: E402

pytestmark = pytest.mark.skipif(os.name != "nt", reason="junctions need Windows")


def _init_scratch(tmp_path: Path) -> Path:
    """Minimal workbench: marker, git, path_map, migration dir."""
    (tmp_path / ".sst-workbench-root").write_text("catalog_schema: 1\n", encoding="utf-8")
    (tmp_path / "10_docs" / "migration").mkdir(parents=True)
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "sp02@test.local"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "SP02 Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    exclude = tmp_path / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    if not exclude.is_file():
        exclude.write_text("", encoding="utf-8")
    return tmp_path


def _write_path_map(root: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "old_path",
        "new_path",
        "domain",
        "letter",
        "catalog_id",
        "kind",
        "phase",
        "junction",
        "status",
        "note",
    ]
    path = root / "10_docs" / "migration" / "path_map.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def _moved_fixture(root: Path, *, phase: str = "SP04") -> tuple[Path, Path]:
    """Simulate a moved pack: content at new_path only."""
    old_rel = "LegacyPack"
    new_rel = "03_data/A_knots/Z999_legacy_pack"
    target = root / new_rel
    target.mkdir(parents=True)
    (target / "marker.txt").write_text("payload-v1\n", encoding="utf-8")
    _write_path_map(
        root,
        [
            {
                "old_path": old_rel,
                "new_path": new_rel,
                "domain": "03_data",
                "phase": phase,
                "junction": "yes",
                "status": "moved",
            }
        ],
    )
    return root / old_rel, target


def test_create_is_idempotent(tmp_path: Path):
    root = _init_scratch(tmp_path)
    link, target = _moved_fixture(root)
    assert jn.main(["--root", str(root), "create"]) == 0
    assert jn.is_junction(link)
    assert jn.junction_target(link) == target.resolve()
    assert jn.main(["--root", str(root), "create"]) == 0  # second time
    assert (link / "marker.txt").read_text(encoding="utf-8") == "payload-v1\n"


def test_verify_fails_on_wrong_target(tmp_path: Path):
    root = _init_scratch(tmp_path)
    link, target = _moved_fixture(root)
    wrong = root / "wrong_target"
    wrong.mkdir()
    (wrong / "x.txt").write_text("x\n", encoding="utf-8")
    jn.create_junction(link, wrong)
    # path_map still expects `target`
    assert jn.main(["--root", str(root), "verify"]) == 1


def test_verify_fails_on_real_directory(tmp_path: Path):
    root = _init_scratch(tmp_path)
    link, target = _moved_fixture(root)
    link.mkdir()
    (link / "not_a_junction.txt").write_text("nope\n", encoding="utf-8")
    assert jn.main(["--root", str(root), "verify"]) == 1


def test_remove_safe_when_already_gone(tmp_path: Path):
    root = _init_scratch(tmp_path)
    _moved_fixture(root)
    assert jn.main(["--root", str(root), "remove"]) == 0


def test_remove_does_not_delete_target(tmp_path: Path):
    root = _init_scratch(tmp_path)
    link, target = _moved_fixture(root)
    marker = target / "marker.txt"
    assert jn.main(["--root", str(root), "create"]) == 0
    assert jn.main(["--root", str(root), "remove"]) == 0
    assert not link.exists()
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8") == "payload-v1\n"


def test_git_exclude_updated_once(tmp_path: Path):
    root = _init_scratch(tmp_path)
    link, _target = _moved_fixture(root)
    assert jn.main(["--root", str(root), "create"]) == 0
    assert jn.main(["--root", str(root), "create"]) == 0
    text = jn.git_exclude_path(root).read_text(encoding="utf-8")
    assert text.count("LegacyPack/") == 1
    assert jn.EXCLUDE_HEADER in text


def test_phase_filter(tmp_path: Path):
    root = _init_scratch(tmp_path)
    link, target = _moved_fixture(root, phase="SP05")
    assert jn.main(["--root", str(root), "create", "--phase", "SP04"]) == 0
    assert not link.exists()
    assert jn.main(["--root", str(root), "create", "--phase", "SP05"]) == 0
    assert jn.is_junction(link)
    assert jn.junction_target(link) == target.resolve()


def test_hardcoded_path_through_junction(tmp_path: Path):
    """Proof: unconverted pack path still reaches payload via old root."""
    root = _init_scratch(tmp_path)
    link, target = _moved_fixture(root)
    assert jn.main(["--root", str(root), "create"]) == 0
    # Simulate a hardcoded relative/absolute old path read:
    hardcoded = root / "LegacyPack" / "marker.txt"
    assert hardcoded.is_file()
    assert hardcoded.read_text(encoding="utf-8") == (
        target / "marker.txt"
    ).read_text(encoding="utf-8")


def test_live_workbench_status_dry_run_safe():
    """Live status/create --dry-run must not mutate the tree (SP11-safe)."""
    assert jn.main(["--root", str(WB), "status"]) == 0
    assert jn.main(["--root", str(WB), "create", "--dry-run"]) == 0
    # After SP11, verify is expected to fail (junctions intentionally absent).
    # Do not call verify here — that would pressure operators to recreate them.


def test_verified_rows_still_select_for_junctions():
    """A signed-off phase must not make junction checks vacuous.

    selectable_rows once matched only status="moved". The moment move_phase --verify
    promoted rows to "verified", junctions.py reported zero rows and `verify` passed
    without checking anything - which is how two missing junctions went unnoticed.
    """
    import junctions as j

    rows = [
        {"old_path": "A", "new_path": "01_research/x", "junction": "yes",
         "status": "moved", "phase": "SP04"},
        {"old_path": "B", "new_path": "01_research/y", "junction": "yes",
         "status": "verified", "phase": "SP04"},
        {"old_path": "C", "new_path": "01_research/z", "junction": "yes",
         "status": "pending", "phase": "SP04"},
        {"old_path": "D", "new_path": "01_research/w", "junction": "no",
         "status": "verified", "phase": "SP04"},
    ]
    picked = {r["old_path"] for r in j.selectable_rows(rows)}
    assert picked == {"A", "B"}, picked


def test_glob_row_expands_to_one_junction_per_directory(tmp_path):
    """A glob old_path cannot be a junction; each moved child gets one instead.

    SP07 moved KnotPlot/qhp* and six campaign globs. mklink cannot create a link at a
    wildcard, so junctions.py expands the row against the destination and links each
    directory match next to where the glob used to live. File matches are skipped
    because a junction can only point at a directory.
    """
    import junctions as j

    root = tmp_path
    dest = root / "03_data" / "D_generated" / "qhp"
    for name in ("qhp", "qhp_6p3", "qhp_extended"):
        (dest / name).mkdir(parents=True)
    (dest / "loose_file.txt").write_text("x", encoding="utf-8")

    pairs = j.expand_glob_row(root, "KnotPlot/qhp*", "03_data/D_generated/qhp")
    links = {rel for rel, _target in pairs}
    assert links == {
        "KnotPlot/qhp",
        "KnotPlot/qhp_6p3",
        "KnotPlot/qhp_extended",
    }, links
    for rel, target in pairs:
        assert target.is_dir()
        assert target.name == rel.split("/")[-1]


def test_glob_detection():
    import junctions as j

    assert j.has_glob("KnotPlot/*.py")
    assert j.has_glob("KnotPlot/qhp*")
    assert not j.has_glob("KnotPlot/knots")
