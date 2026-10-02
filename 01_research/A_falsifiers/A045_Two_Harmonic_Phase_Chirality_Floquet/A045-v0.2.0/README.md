# SST Two-Harmonic Phase-Chirality Floquet Blind Falsifier v0.2.1

v0.2.1 is a **non-scientific execution-robustness patch** over v0.2.0. The finite-core surrogate, two-colour drive, frozen A038 seed ensemble, preregistered gates, thresholds, phases, core ladder, and blind salts are unchanged.

## New in v0.2.1

- prior output directories are never deleted;
- the first run uses the canonical `..._v0.2.1-outputs/` path;
- if that path already exists or is being synchronized, the runner writes to a unique `..._v0.2.1-outputs_RUN_<UTC+PID>/` sibling;
- reveal maps are per-run and are never silently overwritten;
- BLIND/REVEALED ZIP packaging is non-destructive; repeated packages use run-suffixed archive names;
- scientific configs and `blind_salt` values remain byte-for-byte inherited from v0.2.0 so anonymous condition identities remain comparable.

## Scientific model

The v0.2.0 scientific protocol is retained: a dimensionless regularized finite-core nonlocal filament surrogate driven by a two-colour \(\omega/2\omega\) trace-free strain waveform. Formal Floquet analysis remains blocked until an independently certified periodic or relative-periodic orbit exists.

## Run

Python smoke test:

```bat
run_smoke.cmd
```

Native basic campaign (Visual Studio Developer Command Prompt):

```bat
run_build_cpp.cmd
run_all.cmd
```

Extended campaign:

```bat
run_all_extended.cmd
```

## Output policy

First run:

```text
./SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier_v0.2.1-outputs/
```

If that directory already exists, it is preserved and the new run goes to:

```text
./SST_Two_Harmonic_Phase_Chirality_Floquet_Blind_Falsifier_v0.2.1-outputs_RUN_<run-id>/
```

The same non-destructive policy applies to sibling `*_outputs_BLIND.zip` and `*_outputs_REVEALED.zip` archives.

## Scientific status

This remains a blind **dimensionless finite-core surrogate**. It does not identify graphene Berry curvature with fluid vorticity and does not claim a closed SST mechanism. No SST calibration constants are used in the blind campaign.
