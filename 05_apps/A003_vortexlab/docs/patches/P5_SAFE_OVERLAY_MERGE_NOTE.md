# P5 SAFE OVERLAY — merge note (25 okt 2026)

`python install_patch.py` weigerde terecht: runtime / `package.json` / hashes / `verify-parity` waren al gewijzigd door SSTcore native-accel.

## Wat wel gedaan is

1. Officiële installer eerst gedraaid → **REFUSED**, geen writes.
2. Back-ups in `.A003_P5_backups/<timestamp>/`.
3. Byte-voor-byte gekopieerd waar `before`-hash matchte of bestand nieuw was (twist-flow UI, fluid-qualification, P5-tests, docs).
4. P5-runtime als basis, daarna **native-accel hook** opnieuw gezet (opt-in).
5. `package.json` gemerged: P5-tests **én** `test:physics` / `sst-core` / `start:native`.
6. Lokale `apps/web/data/twist_knot_data.js` **niet** aangeraakt (hash `e33ba876…` behouden).

## Provenance

Patch-id: `sstcore-native-accel-on-twistflow-p5`  
Parent: `twist-flow-p5-adaptive-cfl-precision-gate` (runtime `2fde1306…`).
