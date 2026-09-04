"""Tests for scripts/seed_path_map.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("seed_path_map.py")


def _load():
    spec = importlib.util.spec_from_file_location("seed_path_map", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


SAMPLE_PLAN = """# plan
## Path abbreviations used in the tables

| Short | Full |
|-------|------|
| `R/A` | `01_research/A_falsifiers/` |
| `L/C` | `02_libraries/C_finite_core/` |
| `D/A` | `03_data/A_knots/` |
| `T/B` | `04_tools/B_crawlers/` |
| `APP` | `05_apps/` |

## 1. Simple moves — one root, one destination

| # | Current root | Destination | Kind | Phase |
|---|--------------|-------------|------|-------|
| 1 | `Fremlin_FourierSeries/` | `D/A/A006_fremlin_fourier_series/` | data | SP04 |
| 2 | `scripts/` | `07_scripts/` | tooling | SP04 |

## 2. Clean family moves — root already equals one family

| # | Current root | Destination | Versions | Phase |
|---|--------------|-------------|---------:|-------|
| 19 | `SST_Foo/` | `R/A/A001_contact_billiard_hydrodynamic/` | 2 | SP05 |

## 3. Container splits — one root, several families

| # | Current root | Splits into | Count | Phase |
|---|--------------|-------------|------:|-------|
| 52 | `SST_Maxwell/` | `R/A/{A011,A012}` | 2 | SP06 |

## 4. KnotPlot — its own refactor

| # | Current sub-path | Destination | Kind | Approx. size |
|---|------------------|-------------|------|-------------:|
| 69c | `KnotPlot/knots/` | `D/A/A001_knotplot_relaxed/` | data | ~7.8 GB |

## 5. Variants that are not families and not versions

| Current | Belongs to | Placement |
|---------|------------|-----------|
| `SST_Foo/key/` | A001 v0.1.0 | `A001_.../keys/` |

## 6. Stubs and deletions

| # | Current root | Disposition | Phase |
|---|--------------|-------------|-------|
| 70 | `to_be_processed/` | delete — stub | SP11 |

## Non-root items also handled

| Item | Disposition | Phase |
|------|-------------|-------|
| Root `*.zip` | `09_archive/restore/` under theme rules | SP04 |
"""

SAMPLE_CATALOG = """# 01_research

## A_falsifiers — formal

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| A001 | `contact_billiard_hydrodynamic` | SST Contact | `SST_Foo/` | 2026-08-01 | confirmed |
| A011 | `maxwell_kinetic` | Maxwell Kinetic | `SST_Maxwell/` | 2026-08-13 | confirmed |
| A012 | `maxwell_dynamical_field_closure` | Maxwell Dyn | `SST_Maxwell/` | 2026-08-13 | confirmed |

# 03_data

## A_knots

| ID | Family | Official name | Current location | First version | Status |
|----|--------|---------------|------------------|---------------|--------|
| A001 | `knotplot_relaxed` | KnotPlot relaxed | `KnotPlot/knots/` | 2026-01-01 | confirmed |
| A006 | `fremlin_fourier_series` | Fremlin | `Fremlin/` | 2026-01-01 | confirmed |
"""


def test_parse_abbreviations():
    m = _load()
    abbrev = m.parse_abbreviations(SAMPLE_PLAN)
    assert abbrev["R/A"] == "01_research/A_falsifiers/"
    assert abbrev["APP"] == "05_apps/"
    assert abbrev["D/A"].endswith("A_knots/")


def test_expand_braces_uses_catalog_family():
    m = _load()
    abbrev = m.parse_abbreviations(SAMPLE_PLAN)
    catalog = m.parse_catalog(SAMPLE_CATALOG)
    dests = m.expand_destination("R/A/{A011,A012}", abbrev, catalog)
    assert dests == [
        "01_research/A_falsifiers/A011_maxwell_kinetic",
        "01_research/A_falsifiers/A012_maxwell_dynamical_field_closure",
    ]


def test_six_layouts_produce_rows(tmp_path: Path):
    m = _load()
    # Create old_paths so they are not auto-skipped
    for name in (
        "Fremlin_FourierSeries",
        "scripts",
        "SST_Foo",
        "SST_Maxwell",
        "KnotPlot/knots",
        "SST_Foo/key",
        "to_be_processed",
    ):
        (tmp_path / name).mkdir(parents=True, exist_ok=True)
    rows = m.rows_from_plan(SAMPLE_PLAN, SAMPLE_CATALOG, workbench=tmp_path)
    phases = {r["phase"] for r in rows}
    assert "SP04" in phases and "SP05" in phases and "SP06" in phases
    assert "SP07" in phases and "SP11" in phases
    assert all(r["status"] in {"pending", "skipped"} for r in rows)
    news = [r["new_path"] for r in rows]
    assert len(news) == len(set(news))
    # simple move
    assert any(r["old_path"] == "Fremlin_FourierSeries" and r["kind"] == "data" for r in rows)
    # brace split produced two rows from one container
    maxwell = [r for r in rows if r["old_path"] == "SST_Maxwell"]
    assert len(maxwell) == 2


def test_malformed_row_raises():
    m = _load()
    with pytest.raises(ValueError):
        m.split_table_row("not a table")


def test_write_and_load_roundtrip(tmp_path: Path):
    m = _load()
    (tmp_path / "Fremlin_FourierSeries").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "SST_Foo").mkdir()
    (tmp_path / "SST_Maxwell").mkdir()
    (tmp_path / "KnotPlot" / "knots").mkdir(parents=True)
    (tmp_path / "SST_Foo" / "key").mkdir(parents=True)
    (tmp_path / "to_be_processed").mkdir()
    rows = m.rows_from_plan(SAMPLE_PLAN, SAMPLE_CATALOG, workbench=tmp_path)
    out = tmp_path / "path_map.csv"
    m.write_path_map(rows, out)
    loaded = m.load_path_map(out)
    assert len(loaded) == len(rows)
    assert any(r["status"] == "pending" for r in loaded)
