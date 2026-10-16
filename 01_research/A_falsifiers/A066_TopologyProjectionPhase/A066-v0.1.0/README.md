# SST Topology / Projection / Phase blind falsifier v0.1.0

**Scientific grade:** synthetic mechanism-discrimination calibration only. **Not** a qualified Euler or Navier–Stokes reconnection demonstration and **not** native framework v1.0.7 backend certification.

## Why this test exists

The 2025 preprint *Superluminal Correlations in Ensembles of Optical Phase Singularities* (Bucher et al., arXiv:2509.17675v1) shows optical phase zeroes can display extremely high apparent velocities during +/- pair annihilation. This test checks whether a 2D vortex phase-pair event corresponds to an actual 3D topology change, a 3D closed-loop tangency at a measurement plane, or purely phase-pattern motion. All three deliberately share **byte-for-byte identical 2D phase frames**: there is no possible legitimate 2D-only discriminator.

## Windows quick start

1. Extract `SST_TopologyProjectionPhase_v0.1.0_SOURCE_BLIND.zip` to an ordinary work directory, preferably `SST-Workbench/01_research/A_falsifiers/<registry-approved-family>/SST_TopologyProjectionPhase_v0.1.0/`.
2. Keep the separately supplied `..._REVEAL_KEYS.zip` in a different location; **do not extract it for blind analysis**.
3. Run `run_all.cmd SELFTEST`, then `run_all.cmd FREEZE`.
4. Review the PDF and JSON under `../SST_TopologyProjectionPhase_v0.1.0-outputs/`, including `FREEZE_LEDGER.json`. The run also packages `../SST_TopologyProjectionPhase_v0.1.0-outputs_BLIND.zip`.
5. Only after decisions are frozen, if you want to reveal, extract keys *outside* the blind work directory, then `run_all.cmd REVEAL --keys C:\secure\REVEAL_KEYS.json`. This produces `REVEALED_RESULTS.json` and a separate `_REVEALED.zip`.

### Supported commands

```bat
run_all.cmd SELFTEST
run_all.cmd BASIC
run_all.cmd FREEZE
run_all.cmd CERTIFY
run_all.cmd PKLSA_IMPORT --pklsa C:\your\file.npz
run_all.cmd REVEAL_IF_ALLOWED
run_all.cmd REVEAL --keys C:\secure\REVEAL_KEYS.json
```

`CERTIFY` deliberately returns status 2 (physical/native certification remains open) and never modifies frozen output. `REVEAL_IF_ALLOWED` with no external keys does not reveal the truth.

### Requirements

- Python >= 3.10, NumPy, ReportLab and pytest; `run_all.cmd` creates a `.venv` and installs versions in `requirements.txt` (internet/package mirror needed for a fresh environment).
- `cryptography` is used only to decrypt labels after explicit reveal.
- No internet is used at runtime after dependencies are installed; three complete test arrays are included.

### Output structure

- `datasets/DS01.npz`, `DS02.npz`, `DS03.npz`: full observable time-dependent 2D complex fields, polygonal 3D loops, visibility, and circulation markers.
- `datasets/DSxx.truth.aesgcm`: separate AES-256-GCM-encrypted truth, not accessible to blind code; random nonce and salt per dataset.
- `datasets/INPUT_MANIFEST.json`: SHA-256 integrity commitments on both observed bytes and encrypted truth, and salted post-reveal label commitments.
- `preregistration/PROTOCOL.json`: read-only scientific gates and meanings; immutable for any qualified comparison.
- `src/metrics.py`: 2D topological winding, closed 3D intersection counting, material component test, fold fit.
- `src/pklsa.py`: **static** external PKLSA input; no automatic physical claims.
- `docs/SCIENCE_METHODS.pdf`, `docs/SCIENCE_METHODS.tex`: 5-page equations, protocol, gates, limitations, references.

## Three archives are separately sealed

The three standalone `DSxx_SEALED_INPUT.zip` archives are optional independent transport copies of the same immutable datasets included in the blind source package. Their `SEAL.json` is checked against `datasets/INPUT_MANIFEST.json`. The encrypted truths are authenticated and require the **separate** key distribution. The secrecy is operational rather than adversarial because a recipient with both archive sets can choose to open the key archive at any time.

## SST-Workbench framework v1.0.7 integration

The Google Drive canonical framework README identifies v1.0.7 as `CANONICAL_FROZEN`. It supplies its own instance generator, strict framework resolver, blinded ledgers, profile/backend controls, and PDF reporting. **This source archive is an external standalone science module targeting that framework; it does not embed, fork or impersonate v1.0.7.** To obtain actual native certification, generate a fresh instance using the **installed** framework generator (choose a free ID only after checking the current registry), import `src/metrics.py` and the preregistered input contract, and route conclusions to its native gate/reveal API. Do not run two independent reveal implementations as if they shared ledger semantics. v1.0.7 C++ FP64 certification, SYCL screening, true PKLSA time evolution, and cross-source replication remain explicitly unresolved here.

Drive sources reviewed 2026-10-15:
- Framework source: https://drive.google.com/drive/folders/1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE
- PKLSA notes: https://drive.google.com/file/d/1TVLmS3tkswEXX0IR6nk55BOT8md28EuI/view

## Stop conditions

Do **not** interpret the synthetic topology surgery as a physically realized Euler reconnection. A conservation of **aggregate** signed Gamma does not preserve each material loop's Kelvin circulation. Never claim superluminal material transport from a rapidly moving 2D intersection.
