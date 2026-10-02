"""SP09 done-criteria: every version directory uses ``<catalog_id>-v…``."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402


def test_every_version_directory_matches_catalog_id_prefix():
    bad = []
    for fam in cm.discover():
        pat = re.compile(rf"^{re.escape(fam.catalog_id)}-v")
        for v in fam.versions:
            pj = fam.path / v.directory / "project.json"
            if not pj.is_file():
                continue
            if not pat.match(v.directory):
                bad.append((fam.domain, fam.catalog_id, v.directory))
    assert bad == [], f"version dirs not renamed: {bad[:20]}"


def test_family_yaml_directories_match_disk():
    mismatches = []
    for fam in cm.discover():
        yp = fam.path / "FAMILY.yaml"
        if not yp.is_file():
            continue
        yaml_dirs = re.findall(r'directory: "([^"]+)"', yp.read_text(encoding="utf-8"))
        disk = sorted(
            v.directory
            for v in fam.versions
            if (fam.path / v.directory / "project.json").is_file()
        )
        if yaml_dirs and sorted(yaml_dirs) != disk:
            mismatches.append((fam.catalog_id, sorted(yaml_dirs), disk))
    assert mismatches == [], mismatches[:5]


def test_project_json_version_still_matches_parsed_version():
    bad = []
    for fam in cm.discover():
        for v in fam.versions:
            pj = fam.path / v.directory / "project.json"
            if not pj.is_file():
                continue
            data = json.loads(pj.read_text(encoding="utf-8"))
            if data.get("version") != v.version:
                bad.append((fam.catalog_id, v.directory, data.get("version"), v.version))
    assert bad == [], bad[:10]
