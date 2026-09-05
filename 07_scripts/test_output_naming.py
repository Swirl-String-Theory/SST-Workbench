"""SP09: output artifact names stay on the pre-rename stem."""
from __future__ import annotations

import json
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402
import output_naming as on  # noqa: E402
import output_zip_policy as oz  # noqa: E402


def test_stem_falls_back_to_directory_name(tmp_path: Path):
    pack = tmp_path / "Pack_v0.1.0"
    pack.mkdir()
    assert on.artifact_stem(pack) == "Pack_v0.1.0"
    assert on.outputs_dir_name(pack) == "Pack_v0.1.0-outputs"
    assert on.outputs_zip_name(pack) == "Pack_v0.1.0_outputs.zip"


def test_stem_uses_legacy_dir_not_the_short_folder(tmp_path: Path):
    pack = tmp_path / "A042-v0.1.0"
    pack.mkdir()
    (pack / "project.json").write_text(
        json.dumps({
            "catalog_id": "A042",
            "version": "v0.1.0",
            "legacy_dir": "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0",
        }),
        encoding="utf-8",
    )
    assert on.artifact_stem(pack) == (
        "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0"
    )
    assert oz.output_zip_path(pack) == tmp_path / (
        "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0_outputs.zip"
    )


def test_zip_policy_without_metadata_still_uses_directory_name():
    pack = Path("KnotPlot") / "Trefoil_Balance_Point_Campaign_v0.2.3"
    assert oz.output_zip_path(pack) == Path(
        "KnotPlot"
    ) / "Trefoil_Balance_Point_Campaign_v0.2.3_outputs.zip"


def test_live_stems_equal_legacy_dir():
    """Output names follow project.json, not the (possibly shortened) folder."""
    mismatches = []
    for fam in cm.discover():
        for v in fam.versions:
            path = fam.path / v.directory
            pj = path / "project.json"
            if not pj.is_file():
                continue
            legacy = json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir")
            if on.artifact_stem(path) != legacy:
                mismatches.append((fam.catalog_id, v.directory, on.artifact_stem(path), legacy))
    assert mismatches == [], mismatches[:10]
