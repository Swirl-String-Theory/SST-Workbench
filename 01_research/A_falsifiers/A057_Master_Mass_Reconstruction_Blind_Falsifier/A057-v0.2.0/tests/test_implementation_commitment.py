from pathlib import Path

from master_mass.commitment import COVERAGE, verify_implementation_commitment

ROOT = Path(__file__).resolve().parents[1]


def test_implementation_commitment_matches_packaged_tree():
    result = verify_implementation_commitment(ROOT)
    assert result["ok"], (result["expected"], result["actual"])


def test_commitment_covers_native_and_science_implementation():
    assert "experiment/**/*.py" in COVERAGE
    assert "master_mass/**/*.py" in COVERAGE
    assert "native_ext/*.cpp" in COVERAGE
    assert "native_ext/*.hpp" in COVERAGE
    assert "native_ext/*.py" in COVERAGE


def test_commitment_covers_e013_member_contract():
    assert "cross_falsifier_contract.json" in COVERAGE
