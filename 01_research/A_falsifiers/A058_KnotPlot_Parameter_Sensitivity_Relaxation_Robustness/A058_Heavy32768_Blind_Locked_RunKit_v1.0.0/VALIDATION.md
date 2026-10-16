# A058 BLIND-32768 lock-kit validation

## Offline test outcomes — PASS

1. Recomputed the actual v0.2.10 `heavy_selection` algorithm on the user-provided 2048 campaign and its 237 valid final-coordinate files. It returned **exactly 27 selected conditions**, including 5 references + 1 activation control + 21 perturbations.
2. Checked SHA-256 fingerprints of the native source programs, 2048 runlog/manifest/runtime/summary, the immutable trefoil seed and all 237 valid final-coordinate files. The recomputed selector object is byte-identical under the canonical JSON representation to the saved decision.
3. `CHECK` routine passed in the offline mirror with **only the live Windows KnotPlot.exe existence/SHA test mocked**, since KnotPlot is not installed here.
4. A synthetic postrun `VERIFY` test confirmed exact selected-ID and selection-object matching. This was a *synthetic test*; no heavy-run measurements were created or bundled.
5. Modified one 2048 final-coordinate file by one byte. The integrity gate correctly failed; the original bytes were restored.
6. Python syntax compilation PASS, selection-lock checksum PASS, ZIP contents/integrity checked during release packaging.

## Unverified on this environment

- Real Windows CMD invocation, v0.2.10 Framework-v1.0.8 FREEZE, the local KnotPlot.exe SHA-256 and actual 32768 steps are **not tested here**. `CHECK_ONLY` performs these pre-run identity checks on the Windows installation.
- This kit does not alter the original v0.2.10 model, scientific protocol, BLIND outputs or science gates. The original runner's inability to certify *every intermediate* checkpoint as SAFE remains a documented limitation.

## Frozen selection checksum

`HEAVY_SELECTION_LOCK.json`: `11c0bb20703a8bcc7c0565620a485131a6feb36d649f21516c84f6b59be37137`
