"""Create SP03 catalog skeleton (domains + letter leaves)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LEAVES = {
    "01_research/A_falsifiers": "Formal SST falsifiers and gates (catalog A001–A042).",
    "01_research/B_closures": "Closure and field-equation research families.",
    "01_research/C_dynamics": "Vortex, finite-core, and Floquet dynamics research.",
    "01_research/D_benchmarks": "Audits, verification, certification, and metrology gates.",
    "01_research/E_pipelines": "Dataset, knot, and campaign pipeline families.",
    "01_research/F_exploratory": "PoCs and not-yet-formalized research.",
    "02_libraries/A_knot_libraries": "Shared knot geometry and knot data libraries.",
    "02_libraries/B_finite_core": "Finite-core spectral selector and related libraries.",
    "02_libraries/D_numerics": (
        "Reserved for shared numerical kernels extracted later. Empty on purpose."
    ),
    "03_data/A_knots": "Knot datasets: ideal, Fourier, KAtlas, KnotPlot, twist knots.",
    "03_data/B_external": "External reference datasets (e.g. SPARC).",
    "03_data/C_media": "Media assets relocated from media/.",
    "03_data/D_generated": "Generated figures, meshes, QHP, and research output dumps.",
    "03_data/E_reference": "Reserved reference-data namespace. No concrete moves yet.",
    "04_tools/A_geometry": "KnotPlot drivers, RidgeRunner, and geometry tooling.",
    "04_tools/B_crawlers": "Source crawlers (e.g. Katlas).",
    "04_tools/C_fabrication": "Coil / gear / mold generators and fabrication sources.",
    "04_tools/D_proof": "Proof scripts and swirl simulator trees.",
    "04_tools/D_compute": "Compute probes (SYCL and related experiment tooling).",
    "05_apps": "End-user applications (dashboard, coil GUI, VortexLab, Math Lab).",
    "06_templates": "Audit and packaging templates for new packs.",
    "07_scripts": "Repo tooling, path resolver, junctions, and migration scripts.",
    "08_third_party": "Vendored third-party trees (e.g. KnotTheory).",
    "09_archive": "Restore archives, bundles, and non-active trees.",
    "09_archive/restore": "Themed restore zip buckets from Restore_Archives.",
    "09_archive/bundles": "Large bundle archives relocated from bundles/.",
    "10_docs/inventory": "Workbench inventory documents and manifests.",
    "10_docs/architecture": "Architecture notes (path resolution, layout).",
    "10_docs/migration": "Restructure freeze, path map, junctions, provenance.",
    "10_docs/registry": "Catalog registry and FAMILY index (SP08).",
}

DOMAIN_READMES = {
    "01_research": (
        "Research catalog: falsifiers, closures, dynamics, benchmarks, "
        "pipelines, exploratory."
    ),
    "02_libraries": "Reusable libraries shared across research packs.",
    "03_data": "Datasets and generated data, organized by provenance.",
    "04_tools": "Developer and campaign tooling (not end-user apps).",
    "10_docs": "Workbench documentation domains.",
}


def main() -> None:
    created: list[str] = []
    for rel, purpose in LEAVES.items():
        d = ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        readme = d / "README.md"
        if not readme.exists():
            readme.write_text(purpose.strip() + "\n", encoding="utf-8")
            created.append(str(readme.relative_to(ROOT)))
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
            created.append(str(keep.relative_to(ROOT)))

    for rel, purpose in DOMAIN_READMES.items():
        d = ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        readme = d / "README.md"
        if not readme.exists():
            readme.write_text(purpose.strip() + "\n", encoding="utf-8")
            created.append(str(readme.relative_to(ROOT)))

    marker = ROOT / ".sst-workbench-root"
    marker.write_text("catalog_schema: 1\n", encoding="utf-8")
    print(f"marker written: {marker}")
    print(f"files created: {len(created)}")
    for p in created:
        print(f"  {p}")


if __name__ == "__main__":
    main()
