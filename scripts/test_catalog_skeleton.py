"""SP03: catalog domain/letter skeleton from CATALOG_v0.1.md."""

from __future__ import annotations

from pathlib import Path

WB = Path(__file__).resolve().parents[1]

# Leaves required by CATALOG_v0.1.md + SP03 reserved D_numerics / tools letters.
CATALOG_LEAVES = [
    "01_research/A_falsifiers",
    "01_research/B_closures",
    "01_research/C_dynamics",
    "01_research/D_benchmarks",
    "01_research/E_pipelines",
    "01_research/F_exploratory",
    "02_libraries/A_knot_libraries",
    "02_libraries/B_finite_core",
    "02_libraries/D_numerics",
    "03_data/A_knots",
    "03_data/B_external",
    "03_data/C_media",
    "03_data/D_generated",
    "03_data/E_reference",
    "04_tools/A_geometry",
    "04_tools/B_crawlers",
    "04_tools/C_fabrication",
    "04_tools/D_proof",
    "04_tools/D_compute",
    "05_apps",
    "06_templates",
    "07_scripts",
    "08_third_party",
    "09_archive",
    "10_docs/inventory",
    "10_docs/architecture",
    "10_docs/migration",
    "10_docs/registry",
]


def test_every_catalog_leaf_exists_with_namespace_doc():
    """Each leaf documents itself in _NAMESPACE.md.

    Deliberately not README.md: incoming packs bring their own README.md, and a
    placeholder of the same name collides on every merge move (SP04 hit this on
    media/, Restore_Archives/ and scripts/).
    """
    missing = []
    for rel in CATALOG_LEAVES:
        d = WB / rel
        if not d.is_dir():
            missing.append(f"missing dir: {rel}")
            continue
        if not (d / "_NAMESPACE.md").is_file():
            missing.append(f"missing _NAMESPACE.md: {rel}")
    assert missing == [], "\n".join(missing)


def test_no_placeholder_readme_shadows_incoming_content():
    """A skeleton leaf must never carry its own README.md."""
    offenders = [rel for rel in CATALOG_LEAVES if (WB / rel / "README.md").is_file()]
    assert offenders == [], f"placeholder README.md would collide on merge: {offenders}"


def test_d_numerics_is_intentionally_empty_of_packs():
    """SP03 reserve: only scaffolding, no library packs yet."""
    d = WB / "02_libraries" / "D_numerics"
    assert d.is_dir()
    children = [p.name for p in d.iterdir() if p.name not in {".gitkeep", "_NAMESPACE.md"}]
    assert children == [], f"D_numerics should be empty of packs, found {children}"


def test_ten_domains_present():
    for i in range(1, 11):
        # 01_research .. 10_docs
        prefix = f"{i:02d}_"
        matches = [p for p in WB.iterdir() if p.is_dir() and p.name.startswith(prefix)]
        assert matches, f"missing domain directory for {prefix}*"
