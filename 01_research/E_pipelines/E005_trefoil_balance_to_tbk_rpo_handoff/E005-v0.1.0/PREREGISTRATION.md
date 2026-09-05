# Preregistration — Trefoil Balance → TBK/RPO Handoff v0.1.0

## Scope

This package bridges the completed:

```text
KnotPlot/Trefoil_Balance_Point_Campaign_v0.1.0/out
```

into one of the repository targets:

```text
SST_Trefoil_Lobe_Orientation_Blind_Falsifier/
  SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact

SST_Trefoil_Lobe_Orientation_Blind_Falsifier/
  SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.6_DD32_compact
```

The v0.4.8 route is preferred.

## Separation of selection from downstream outcome

Candidate selection is computed exclusively from the frozen Trefoil Balance
campaign checkpoints. The selection code does not inspect any TBK/RPO output.

Every prepared set is hashed in `SELECTION_LOCK.json` before any target stage
is invoked.

The target receives blind IDs only:

```text
BALX_001
BALX_002
...
```

The target entry contains only:

```python
{
    "source": blind_id,
    "kind": "knotplot",
    "topology_class": "knot",
    "canonical_id": "3_1",
    "path": blind_xyz_path,
}
```

No `charge`, `hooke`, `power`, K31/T23 identity, balance score, or selection
reason is passed to `run_panel`.

## Prepared candidate sets

All four sets are generated before downstream execution.

### `selected` — default

For each embedding the union of:

- B00 baseline control;
- the setting minimizing the worst early balance response across both embeddings;
- that embedding's individual minimum-|early E| setting;
- nearest actual q-bracket zero candidate;
- nearest actual hooke-bracket zero candidate.

Duplicates are removed before blinding.

### `core`

Exactly:

```text
B00, QLO, QCEN, QHI
```

for both K31 and T23. Eight inputs. This is the strict reduced-q bracket test.

### `full_balance`

Exactly:

```text
B00, R25, R50, R75, R100
```

for both K31 and T23. Ten inputs.

### `all20`

All ten frozen q/h/p settings on both embeddings.

## Geometry policy

The downstream source is the exact KnotPlot `i10000` XYZ file.

The handoff also writes a 300-point uniform-arclength copy for provenance, but
the raw file is what the TBK/RPO target receives.

- scale is preserved in the handoff;
- point order is preserved;
- orientation reversal is forbidden.

The v0.4.8 target itself subsequently normalizes each geometry to total
arclength `2*pi`; therefore absolute KnotPlot scale is not a downstream tested
quantity.

## v0.4.8 route

1. FP64/OpenMP screen with `configs/panel_extended.json`.
2. Adaptive spectral ladder `k_max = 16 -> 24 -> 32 -> 48 -> 64`, default
   backend `sycl-dd32`.
3. Only spectrally converged P2-PASS candidates are promoted.
4. FP64/OpenMP robust full confirmation.
5. Target PASS/FAIL and P7/P8 RPO/Floquet diagnostics are reported unchanged.

DD32 is not promoted to confirmatory authority.

## v0.4.6 fallback

The selected custom entries are run through `configs/archive_full.json` using
CPU/OpenMP FP64.

## Historical comparison

The user-stated prior PASS set `{2.2.1, 4.2.1}` is retained only as context in
the final report. It is not used for candidate selection, ranking, thresholds,
or target gate decisions.
