"""Repo-root Based Pyright config must skip junctions and generated trees."""

from __future__ import annotations

import json
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
CONFIG = WB / "pyrightconfig.json"
SETTINGS = WB / ".vscode" / "settings.json"

# Real source lives under these catalog domains. Compat junctions at the repo
# root point at the same trees; enumerating both is what triggered the
# "workspace source files > 10 seconds" warning.
SOURCE_DOMAINS = {
    "01_research",
    "02_libraries",
    "04_tools",
    "05_apps",
    "06_templates",
    "07_scripts",
    "10_docs",
}

HEAVY_ROOTS = {
    "03_data",
    "08_third_party",
    "09_archive",
    "DELETE",
    "Restore_Archives",
    "KnotPlot",
}

REQUIRED_EXCLUDES = {
    "**/node_modules",
    "**/__pycache__",
    "**/.venv",
    "**/venv",
    "**/outputs",
}


def test_pyrightconfig_exists_and_is_json():
    assert CONFIG.is_file()
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert isinstance(data.get("include"), list)
    assert isinstance(data.get("exclude"), list)


def test_include_is_catalog_source_domains_only():
    """Junction aliases at the root must not be part of the analysis set."""
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    include = set(data["include"])
    assert include == SOURCE_DOMAINS
    assert include.isdisjoint(HEAVY_ROOTS)


def test_exclude_covers_venvs_caches_and_run_outputs():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    exclude = set(data["exclude"])
    missing = REQUIRED_EXCLUDES - exclude
    assert missing == set(), f"pyright exclude missing {sorted(missing)}"


def test_vscode_analysis_is_open_files_only():
    """Full-workspace diagnostics re-walk the tree; open-files mode does not."""
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert settings["python.analysis.diagnosticMode"] == "openFilesOnly"
    watcher = settings["files.watcherExclude"]
    assert watcher["SST_*/**"] is True
    assert watcher["03_data/**"] is True
    assert watcher["Restore_Archives/**"] is True
