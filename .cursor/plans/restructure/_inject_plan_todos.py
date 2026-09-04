"""Insert ## Todos sections into all restructure plan files."""
from __future__ import annotations

from pathlib import Path

PLAN = Path(__file__).resolve().parent

TODOS: dict[str, tuple[str, list[tuple[bool, str]], str]] = {
    # filename -> (optional status_override_note, [(done, text), ...], next_hint)
    "RESTRUCTURE_EPIC.plan.md": (
        None,
        [
            (True, "Catalog model + 10 domains documented"),
            (True, "Invariants written (incl. git_mv-only + DELETE/<relpath> soft-retire)"),
            (True, "Phase graph SP00–SP11 defined"),
            (True, "A001–A042 chronology frozen; 01/02/03 catalog tables aligned"),
            (True, "SP00 freeze & provenance completed (`10_docs/migration/FREEZE.md`)"),
            (False, "SP01 path resolver implemented & verified"),
            (False, "SP02 junction layer live for moved roots"),
            (False, "SP03 catalog skeleton + hygiene on disk"),
            (False, "SP04–SP07 physical `git mv` waves complete"),
            (False, "SP08–SP09 metadata + version rename"),
            (False, "SP10 reproducibility gate passed"),
            (False, "SP11 soft-retire stubs to `DELETE/` + junction decommission"),
        ],
        "SP01 path resolver",
    ),
    "RESTRUCTURE_PLAN_v0.1.plan.md": (
        None,
        [
            (True, "All 73 roots mapped (human-readable tables)"),
            (True, "`path_map.csv` seeded / updated to match CATALOG (machine artifact wins)"),
            (True, "01_research / 02_libraries / 03_data destinations frozen to inventory tables"),
            (True, "Soft-delete rule: former deletes → `DELETE/<original/relative/path>`"),
            (True, "JSON restructure map regenerated from CATALOG + path_map"),
            (False, "SP04: 18 simple moves executed (`git mv` + junctions)"),
            (False, "SP05: clean family moves executed (pilot A038 first)"),
            (False, "SP06: container splits executed"),
            (False, "SP07: KnotPlot tool/data/campaign/result split executed"),
            (False, "SP09: version dirs renamed to `<ID>-v…`"),
            (False, "SP11: stubs soft-retired under `DELETE/`"),
        ],
        "SP01 (no physical moves until resolver + junctions)",
    ),
    "SP00_freeze_and_provenance.plan.md": (
        None,
        [
            (True, "Baseline tests recorded (`baseline_tests.md`)"),
            (True, "`pre-restructure-tree.json` generated"),
            (True, "`file_manifest.csv` generated"),
            (True, "`checksums.sha256` generated"),
            (True, "`path_map.csv` seeded with schema"),
            (True, "Q1 / Q2 / Q3 answered (`open_questions.md`)"),
            (True, "`FREEZE.md` written with SHA + inventory numbers"),
            (True, "Done-criteria met — SP00 closed"),
        ],
        "Proceed to SP01",
    ),
    "SP01_path_resolver.plan.md": (
        None,
        [
            (False, "Create `07_scripts/sst_workbench_paths/` module"),
            (False, "Implement `WORKBENCH_ROOT` / `DATA_ROOT` / `KNOT_DATASET` / … resolution"),
            (False, "Implement `resolve_family(catalog_id[, version])` against `path_map.csv`"),
            (False, "Create matching `07_scripts/paths.cmd`"),
            (False, "Write `10_docs/architecture/path_resolution.md`"),
            (False, "List seven absolute `paths.cmd` conversion targets (do not convert yet)"),
            (False, "Add `test_workbench_paths.py`"),
            (False, "Add `test_resolve_family.py`"),
            (False, "Add `test_paths_cmd.py`"),
            (False, "Done-criteria: identical resolution from ≥3 depths; all three tests green"),
        ],
        "Start here — next executable sub-plan after SP00",
    ),
    "SP02_compat_junction_layer.plan.md": (
        None,
        [
            (False, "Document junction policy (`mklink /J`, `.git/info/exclude` not `.gitignore`)"),
            (False, "Implement `junctions.py` create/verify/remove/status"),
            (False, "Create `junction_registry.csv` schema"),
            (False, "Ship `bootstrap_junctions.cmd` + `junctions.md`"),
            (False, "Tests: junctions, git-invisibility, bootstrap; remove must not delete targets"),
            (False, "Done-criteria: machinery ready before first SP04 move"),
        ],
        "Blocked on SP01 + SP03",
    ),
    "SP03_catalog_skeleton_and_hygiene.plan.md": (
        None,
        [
            (False, "Create 10-domain + letter skeleton (`.gitkeep` / README per leaf)"),
            (False, "Write `.sst-workbench-root` marker (`catalog_schema: 1`)"),
            (False, "Ensure `core.longpaths` / Windows LongPathsEnabled"),
            (False, "Confirm/fix `gui` casing (SP00 Q3: already lowercase — verify no-op)"),
            (False, "Extend `.gitignore` for `*-outputs*` and `keys/`"),
            (False, "Tests for skeleton / marker / gitignore"),
            (False, "Done-criteria: skeleton present; hygiene tests green"),
        ],
        "Can run in parallel with SP01 after SP00",
    ),
    "SP04_low_risk_moves.plan.md": (
        None,
        [
            (False, "Preconditions: SP02 + SP03 done"),
            (False, "Move 18 low-risk roots least-referenced-first (`git mv` only)"),
            (False, "Per move: path_map row → git mv → junction → SHA verify → commit"),
            (False, "Update docs/tests for `07_scripts/` path"),
            (False, "Done-criteria: 18 rows `verified`; baseline matches SP00; old paths work via junctions"),
        ],
        "Blocked on SP02 + SP03",
    ),
    "SP05_clean_family_moves.plan.md": (
        None,
        [
            (False, "Pilot A038 trefoil dynamic seed qualification (full run + output hash)"),
            (False, "Move remaining clean families (version names unchanged)"),
            (False, "Stub `FAMILY.yaml` per family"),
            (False, "Place variants/keys correctly (no new catalog IDs)"),
            (False, "Route-B last (shared outputs split rows)"),
            (False, "Done-criteria: families at catalog paths; SHA junctions; ≥5 packs run via old paths"),
        ],
        "Blocked on SP04",
    ),
    "SP06_container_splits.plan.md": (
        None,
        [
            (False, "Split Maxwell / Einstein / Kelvin / Swirl Clock / Threaded Hole / Trefoil Lobe"),
            (False, "Split remaining mixed roots (Hopf, routes, horn, GUI, Knot_Library, 3D, …)"),
            (False, "Reveal keys under `keys/`; multi-junction roots where needed"),
            (False, "Record `sst_trefoil_biot_py` diffs (no dedupe)"),
            (False, "Done-criteria: all children accounted; provisional taxonomy resolved; baseline matches"),
        ],
        "Blocked on SP05",
    ),
    "SP07_knotplot_refactor.plan.md": (
        None,
        [
            (False, "Archive zips → `09_archive/restore/KnotPlot/`"),
            (False, "Move qhp* → `03_data/D_generated/qhp/`"),
            (False, "Move Fourier / campaigns / ridgerunner out / tool scripts"),
            (False, "Move `knots/` last after `SST_KNOT_DATASET` + ≥3 pack conversions"),
            (False, "Done-criteria: old KnotPlot is junction scaffold; ≥5 packs run unmodified; file count conserved"),
        ],
        "Blocked on SP05 (can parallel SP06 after SP05)",
    ),
    "SP08_catalog_metadata_and_registry.plan.md": (
        None,
        [
            (False, "Complete every `FAMILY.yaml`"),
            (False, "Add `project.json` per version"),
            (False, "Migrate `falsifier_registry.yaml` to `catalog_id` + `resolve_family`"),
            (False, "Build `catalog_index.json`; refresh inventories"),
            (False, "Done-criteria: registry validate/discover clean; metadata tests green"),
        ],
        "Blocked on SP06 + SP07",
    ),
    "SP09_version_rename_stage2.plan.md": (
        None,
        [
            (False, "Convert output-name scripts to `output_prefix` first"),
            (False, "Rename version dirs to `<catalog_id>-v…`"),
            (False, "Build level-2 junction scaffolds from `legacy_dir`"),
            (False, "Family-at-a-time: rename → scaffold → verify → commit"),
            (False, "Done-criteria: all versions renamed; legacy paths hash-resolve; path lengths OK"),
        ],
        "Blocked on SP08",
    ),
    "SP10_reproducibility_gate.plan.md": (
        None,
        [
            (False, "Gate every active family's `latest` (install → build → run → manifest)"),
            (False, "Record tolerances in `FAMILY.yaml` gate section"),
            (False, "Write `reproducibility_gate.md`"),
            (False, "Special cases: blind-only, datasets, non-runnable, GPU skip-with-reason"),
            (False, "Done-criteria: no unjustified fails; gate report committed"),
        ],
        "Blocked on SP09",
    ),
    "SP11_decommission.plan.md": (
        None,
        [
            (False, "Soft-retire stubs: `git mv` → `DELETE/<original/relative/path>` (never unlink research)"),
            (False, "Stage disposable caches/venvs under `DELETE/` only if reproducible"),
            (False, "Remove junctions domain-by-domain after SP10 clean"),
            (False, "Archive dedup with hash-matched siblings only; stage candidates to `DELETE/`"),
            (False, "Decide `.tmp.driveupload/` separately"),
            (False, "Done-criteria: soft-retire complete; junctions gone safely; provenance retained"),
        ],
        "Blocked on SP10 — last phase",
    ),
}


def render_todos(items: list[tuple[bool, str]], next_hint: str) -> str:
    lines = [
        "## Todos",
        "",
        "Progress tracker — checkboxes include completed work so status is obvious at a glance.",
        "",
    ]
    for done, text in items:
        mark = "x" if done else " "
        lines.append(f"- [{mark}] {text}")
    lines += ["", f"**Next:** {next_hint}", ""]
    return "\n".join(lines)


def insert_after_status(text: str, block: str) -> str:
    # Remove existing ## Todos section if re-running
    if "\n## Todos\n" in text:
        import re

        text = re.sub(r"\n## Todos\n.*?(?=\n## |\Z)", "\n", text, count=1, flags=re.S)

    lines = text.splitlines(keepends=True)
    out = []
    inserted = False
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if not inserted and lines[i].startswith("Status:"):
            # skip following blank lines then insert
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            out.append("\n")
            out.append(block if block.endswith("\n") else block + "\n")
            if not block.endswith("\n\n"):
                out.append("\n")
            inserted = True
            continue
        i += 1
    if not inserted:
        raise SystemExit("Status: line not found")
    return "".join(out)


def frontmatter(items: list[tuple[bool, str]], name: str) -> str:
    # Cursor-style todos for plan files
    lines = [
        "---",
        f"name: {name}",
        "todos:",
    ]
    for idx, (done, text) in enumerate(items):
        status = "completed" if done else "pending"
        # escape quotes in text
        safe = text.replace('"', "'")
        lines.append(f'  - id: t{idx:02d}')
        lines.append(f'    content: "{safe}"')
        lines.append(f"    status: {status}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    for fname, (_note, items, nxt) in TODOS.items():
        path = PLAN / fname
        raw = path.read_text(encoding="utf-8")
        # strip existing frontmatter if we added it before
        if raw.startswith("---\n"):
            end = raw.find("\n---\n", 4)
            if end != -1:
                raw = raw[end + 5 :]
                if raw.startswith("\n"):
                    raw = raw[1:]

        name = fname.replace(".plan.md", "").replace("_", " ")
        fm = frontmatter(items, name)
        body = insert_after_status(raw, render_todos(items, nxt))
        # Ensure title still first after frontmatter
        path.write_text(fm + body, encoding="utf-8")
        done_n = sum(1 for d, _ in items if d)
        print(f"{fname}: {done_n}/{len(items)} done — next: {nxt}")


if __name__ == "__main__":
    main()
