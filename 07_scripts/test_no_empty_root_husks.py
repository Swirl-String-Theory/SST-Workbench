"""Post-SP11: empty container husks must not remain at repo root."""

from __future__ import annotations

from pathlib import Path

WB = Path(__file__).resolve().parents[1]

# Empty scaffolds / leftovers cleaned in the husk-cleanup pass.
ROOT_HUSKS = (
    "SST_chi_phase_research",
    "SST_Hopf_Benchmark",
    "SST_horn_bem_research",
    "SST_ideal_trefoil_biot_research",
    "SST_Route_I_relative_entropy_PoC",
    "SST_Maxwell",
    "SST_Kelvin_Floquet",
    "Knot_Library",
    "experiments",
    "bundles",
    "KnotPlot",
    "Katlas_Sources_v0.2.2_Outputs",
    "KnotInfo",
    "SST_Trefoil_Closure",
)

# Intentional root files after cleanup (everything else is a leftover).
ROOT_KEEP_FILES = {
    "README.md",
    "falsifier_registry.yaml",
    "requirements-workbench.txt",
    "pyrightconfig.json",
    ".gitignore",
    ".gitattributes",
    ".sst-workbench-root",
}

ROOT_KEEP_DIRS = {
    "01_research",
    "02_libraries",
    "03_data",
    "04_tools",
    "05_apps",
    "06_templates",
    "07_scripts",
    "08_third_party",
    "09_archive",
    "10_docs",
    ".git",
    ".cursor",
    ".vscode",
    ".github",
}


def test_root_husks_absent():
    present = [name for name in ROOT_HUSKS if (WB / name).exists()]
    assert present == [], f"husks still at root: {present}"


def test_root_only_has_domains_and_keepers():
    unexpected = []
    for p in WB.iterdir():
        if p.name in ROOT_KEEP_DIRS or p.name in ROOT_KEEP_FILES:
            continue
        if p.name.startswith("."):
            continue
        unexpected.append(p.name)
    assert unexpected == [], f"unexpected root entries: {unexpected}"


def test_katlas_lives_under_catalog():
    dest = WB / "03_data" / "A_knots" / "03_katlas" / "v0.2.2"
    assert dest.is_dir()
    assert (dest / "knots").is_dir() or (dest / "links").is_dir()


def test_knotinfo_lives_under_catalog():
    dest = WB / "03_data" / "A_knots" / "07_knotinfo"
    assert dest.is_dir()
    assert any(dest.glob("*.zip")) or any(dest.glob("*.tar.gz"))


def test_maxwell_kinetic_outputs_parked_under_a011():
    base = WB / "01_research" / "A_falsifiers" / "A011_maxwell_1_kinetic_energy"
    for ver in ("v0.1.0", "v0.2.0", "v0.3.0", "v0.3.1"):
        z = base / f"A011-{ver}" / f"1_Maxwell_SST_Kinetic_Falsifier_{ver}_outputs.zip"
        assert z.is_file(), z


def test_kelvin_joule_outputs_parked_under_a032():
    z = (
        WB
        / "01_research"
        / "A_falsifiers"
        / "A032_kelvin_joule_transient_energy"
        / "A032-v0.1.0"
        / "Kelvin_Joule_SST_Transient_Energy_Falsifier_v0.1.0_outputs.zip"
    )
    assert z.is_file()


def test_knot_library_docs_under_a002():
    a002 = WB / "02_libraries" / "A_knot_libraries" / "A002_knot_library"
    assert (a002 / "README.md").is_file()
    assert (a002 / "_setup_provenance.py").is_file()
