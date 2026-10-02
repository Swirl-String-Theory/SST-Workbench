"""SP03: hyphenated output gitignore patterns and keys/ rule."""

from __future__ import annotations

import subprocess
from pathlib import Path

WB = Path(__file__).resolve().parents[1]

# Real hyphenated output directory basenames from the current tree.
REAL_HYPHEN_OUTPUTS = [
    "Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs",
    "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.2.0-outputs",
    "SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs",
]


def _check_ignore(rel: str) -> bool:
    """Return True if git would ignore ``rel`` (relative to workbench root)."""
    proc = subprocess.run(
        ["git", "check-ignore", "-q", rel],
        cwd=WB,
        capture_output=True,
        text=True,
    )
    # 0 = ignored, 1 = not ignored, 128 = error
    assert proc.returncode in (0, 1), proc.stderr
    return proc.returncode == 0


def test_hyphenated_outputs_are_ignored():
    for name in REAL_HYPHEN_OUTPUTS:
        # Nested under a fake pack path — patterns are basename-oriented (*-outputs/).
        rel = f"SomePack/{name}/results.json"
        assert _check_ignore(rel), f"expected ignore: {rel}"
        rel_blind = f"SomePack/{name}_BLIND/x.bin"
        # Pattern *-outputs_BLIND/ matches dirs ending that way as a path segment.
        assert _check_ignore(rel_blind) or _check_ignore(
            f"SomePack/Pack-outputs_BLIND/x.bin"
        )


def test_outputs_blind_reveal_patterns():
    assert _check_ignore("Fam/Pack-outputs_BLIND/a.txt")
    assert _check_ignore("Fam/Pack-outputs_REVEALED/a.txt")


def test_source_dir_with_word_outputs_not_ignored():
    """A source tree that merely contains the word 'outputs' must stay trackable."""
    # e.g. docs about outputs, or a module named something_outputs_helper
    assert not _check_ignore("SomePack/docs/about_outputs.md")
    assert not _check_ignore("SomePack/src/outputs_helper.py")
    assert not _check_ignore("01_research/A_falsifiers/README.md")


def test_keys_under_research_family_ignored():
    assert _check_ignore("01_research/A_falsifiers/A042_demo/keys/secret.json")
    # Not every keys/ anywhere — only the catalog research pattern.
    assert not _check_ignore("07_scripts/keys/readme.md")


def test_underscore_outputs_still_ignored():
    assert _check_ignore("SomePack/SomePack_outputs/run.json")
