# A058-v0.2.8 — validated engineering patch

## Diagnosis grounded in user-supplied KnotPlot 1.022 build 5125W logs

- Persistent stdin of v0.2.7 **loaded the shared seed** and **produced the first 300-point ASCII export** (`before_export_ok=true`), but the stream SAFE parse returned `false`.
- Actual safety segment: `Current position is  *** khat_mag is zero! ...\nsafe.` The prior code searched for the contiguous words `current position is safe`, incorrectly rejecting a positive safety status with interleaved stderr text.
- This is a **safety text parser false negative**, NOT evidence that the loaded seed was rejected as unsafe. However, `khat_mag is zero` warns of a potentially invalid knot embedding or projection: it is preserved for scientific scrutiny and not silently reinterpreted as proof of geometry validity.
- The stdout log also contains `nothing loaded` and other startup diagnostics before the banner / before the marked reload. Their temporal ordering cannot be reliably inferred from combined buffered stdout/stderr. A `nothing loaded` INSIDE a controlled safety marker remains a failure.
- Because the v0.2.7 parser aborted before `go 32`, the user's log contains no evidence yet of successful streaming iterations or second export.

## v0.2.8 changes

- Centralized safety interpretation across install, preflight, condition start and condition final: statuses `SAFE`, `SAFE_WITH_WARNING`, `UNSAFE`, `UNCONFIRMED`.
- Remove only interleaved `*** ...` diagnostic text; require explicit `Current position is safe` for positive status; reject explicit `not safe`, missing response, `nothing loaded`, `nothing to save`, `nothing to output`, `unknown command` in marker segment.
- Record safety diagnostic/warning separately in private preflight `result.json`, and record warning counts and safety status in acquisition metadata. Preserve exact warning text for review.
- Do not alter numerical defaults, 271 registered conditions, seed preparation, science/thresholds, adaptive relaxation, or Framework-v1.0.8 pin. Fresh private commitment material is generated for this new release version.
- Store a path-redacted version of the user-provided log in regression fixtures; do not leak the full source/installation path in public test files.

## Isolated checks performed

- Python/pytest: 41/41 PASS (including literal real user log regression and mocked streamed go-32 with warning).
- Python compile: PASS.
- Exact SST Framework-v1.0.8 science/source/gate/report validation: PASS.
- Blind scan: 0 forbidden hits.
- Nonced blind/reveal commitments, FREEZE and FROZEN verification on a copy: PASS.
- LaTeX -> PDF: PASS.
- Clean source release, SHA-256 package manifest and ZIP integrity: PASS.

## Not validated

- KnotPlot Windows user-machine live persistent-stdin go-32 and iteration counter have not been executed in this Linux environment.
- A `SAFE_WITH_WARNING` output is not by itself a geometry-certification result. Before interpreting scientific response curves, inspect projection warnings and complete safety/topology records.
