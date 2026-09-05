"""SP11: relocation stubs retired; content preserved under migration docs."""

from __future__ import annotations

from pathlib import Path

WB = Path(__file__).resolve().parents[1]

STUBS = (
    "to_be_processed",
    "falsifier_registry",
    "experiments/derive_constants",
    "experiments/trefoil",
)

RETIRED = WB / "10_docs" / "migration" / "retired_stubs"


def test_stub_paths_absent_at_repo_root():
    present = []
    for rel in STUBS:
        p = WB / rel.replace("\\", "/")
        if p.exists():
            present.append(rel)
    assert present == [], f"stubs still at root: {present}"


def test_stub_readmes_preserved_in_migration():
    expected = {
        "to_be_processed_README.md",
        "falsifier_registry_README.md",
        "experiments_derive_constants_README.md",
        "experiments_trefoil_README.md",
    }
    have = {p.name for p in RETIRED.glob("*.md")}
    assert expected <= have, f"missing retired stubs: {expected - have}"


def test_falsifier_registry_yaml_stays_at_root():
    assert (WB / "falsifier_registry.yaml").is_file()


def test_delete_folder_gone():
    assert not (WB / "DELETE").exists()
