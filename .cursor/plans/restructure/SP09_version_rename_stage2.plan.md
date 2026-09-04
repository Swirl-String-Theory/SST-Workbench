---
name: SP09 version rename stage2
todos:
  - id: t00
    content: "Convert output-name scripts to `output_prefix` first"
    status: pending
  - id: t01
    content: "Rename version dirs to `<catalog_id>-v…`"
    status: pending
  - id: t02
    content: "Build level-2 junction scaffolds from `legacy_dir`"
    status: pending
  - id: t03
    content: "Family-at-a-time: rename → scaffold → verify → commit"
    status: pending
  - id: t04
    content: "Done-criteria: all versions renamed; legacy paths hash-resolve; path lengths OK"
    status: pending
---
# SP09 — Version-directory rename, stage 2

Status: `PLANNED` · Priority: P3 · Risk: medium · Depends on: SP08

## Todos

Progress tracker — checkboxes include completed work so status is obvious at a glance.

- [ ] Convert output-name scripts to `output_prefix` first
- [ ] Rename version dirs to `<catalog_id>-v…`
- [ ] Build level-2 junction scaffolds from `legacy_dir`
- [ ] Family-at-a-time: rename → scaffold → verify → commit
- [ ] Done-criteria: all versions renamed; legacy paths hash-resolve; path lengths OK

**Next:** Blocked on SP08

Version directories get their short catalog-prefixed names. This is the second half of the
deliberately split rename, and the phase that finally shortens paths.

```text
01_research/A_falsifiers/A042_quantum_galileo_action_gauge_closure/
├── SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0/     ->  A042-v0.1.0/
└── SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1/     ->  A042-v0.1.1/
```

## Why the catalog prefix and not a bare version

`A042-v0.1.1` costs eleven characters more than `v0.1.1` and buys the thing that matters for a
ZIP-driven workflow: a version directory copied loose, mailed, or extracted from an archive is
still unambiguously identifiable. Combined with `project.json` inside it, a stray `A042-v0.1.1/`
found in a downloads folder resolves to a family, a name and a version with no guesswork.

## The path-length payoff

This is where the transition's worst moment ends. The longest tracked relative path today is 231
characters, and 543 exceed 220. During stage 1 those got *longer*, because families moved deeper
while keeping long version names. Stage 2 reverses it decisively:

```text
SST_Trefoil_Lobe_Orientation_Blind_Falsifier/
  SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact/
                                                                          129 chars

01_research/A_falsifiers/A023_multitopology_rpo_floquet/A021-v0.4.8/
                                                                           73 chars
```

Verify after the phase that no tracked path exceeds 200 characters. If any does, it is a genuinely
deep tree inside a pack, not a naming problem, and should be noted rather than fixed here.

## The two-level junction scaffold

This is the part that makes stage 2 more than a rename. After stage 1, an old reference works like
this:

```text
SST_Quantum_Galileo_Action_Gauge_Closure/          -> junction -> A039_.../
  SST_..._Falsifier_v0.1.1/                        -> real directory, unchanged name
```

After the rename, the junction still resolves but the directory it lands on no longer has that
name. So every root that was a junction becomes a **real directory** containing one junction per old
version name:

```text
SST_Quantum_Galileo_Action_Gauge_Closure/          real directory, in .git/info/exclude
├── SST_..._Falsifier_v0.1.0/    -> junction -> 01_research/.../A042_.../A042-v0.1.0/
└── SST_..._Falsifier_v0.1.1/    -> junction -> 01_research/.../A039_.../A042-v0.1.1/
```

Roughly 73 real directories and 272 junctions. `junctions.py` gains a `--level 2` mode that reads
`legacy_dir` from each `project.json` and builds the scaffold from it — which is why SP08 must
record `legacy_dir` before this phase runs.

SP06 §3 already rehearsed this pattern for
`SST_Threaded_Hole_Substrate_Blind_Falsifier_v0.1.0/`, which needed two junctions under one real
root. Reuse that code path rather than writing a second one.

## Applying the normalization from SP08

The renames come straight from `project.json`:

| Recorded | Directory name |
|----------|----------------|
| `version: v0.1.1`, `revision: null` | `A042-v0.1.1` |
| `version: v0.2.2`, `revision: 8` | `A032-v0.2.2-r8` |
| `version: v0.4.8`, config `adaptive-spectral-dd32-compact` | `A021-v0.4.8` |
| `version: v16B0` (documented exception) | `C001-v16B0` |

Closed historical series keep their identifiers and simply gain the prefix. The exception is
recorded in `FAMILY.yaml`, so nothing has to infer it.

## Output artifacts do not change

The single most important invariant of this phase. A run from `A042-v0.1.1/` still produces:

```text
SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs/
SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs_BLIND/
SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs_REVEALED/
```

with zips at the agreed higher level. The name is built from `output_prefix` in `FAMILY.yaml` plus
`version` in `project.json` — never from the directory name.

Any run script that derives its output name from `%~dp0` or `Path(__file__).parent.name` **will
break silently**, producing `A042-v0.1.1-outputs/` instead. Silently, because the run succeeds and
the artifact is simply misnamed. Enumerate and convert these before renaming; a test that only
checks "the run succeeded" will not catch it.

## Execution order

1. Enumerate every run script that derives an output name from its directory. Convert them to read
   `output_prefix`.
2. One family at a time: rename its version directories, build its two-level scaffold, verify, commit.
3. Start with A039 — two versions, recently created, few inbound references.
4. Leave A021 (nine versions, config-laden names) and A001-data (`knotplot_relaxed`) until the
   pattern is proven.

## Tests to write

- `test_version_rename.py` — every version directory matches `^<catalog_id>-v` after the rename;
  the count per family is unchanged; every `project.json` `version` still matches.
- `test_output_naming.py` — for a sample of families, the computed output directory name equals the
  pre-migration name exactly. This is the regression test for the silent-misnaming failure above.
- `test_level2_junctions.py` — every `legacy_dir` recorded in every `project.json` resolves through
  the scaffold to the correct renamed directory, verified by SHA-256 of a known file.
- `test_path_length.py` — no tracked path exceeds 200 characters; report the longest ten.

## Rollback

Per family. The rename is a `git mv` inside one directory, so reverting is symmetrical. The
scaffold is removed with `junctions.py remove --level 2`.

The risk that does not roll back cleanly is a *partially converted* run script: one that was
changed to use `output_prefix` while its family was reverted to long directory names. Convert
scripts and rename directories in the same commit, per family.

## Done criteria

- Every version directory across all 109 families uses `<catalog_id>-v...`.
- The two-level scaffold resolves every `legacy_dir`, verified by hash.
- Output artifact names are byte-identical to their pre-migration form for a sampled set of at least
  ten families.
- No tracked path exceeds 200 characters.
- Test suite matches the SP00 baseline.
