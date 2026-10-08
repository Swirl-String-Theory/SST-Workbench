A055 v0.4.0-r3 -> r4 Windows native short-path patch

Apply over an A055 v0.4.0 directory that already contains the r3 fixes.

Observed Windows failure:
  ImportError: DLL load failed while importing _native:
  The filename or extension is too long.

Important:
- The canonical A054 native hash is already correct.
- Do NOT replace or rebuild the sealed A054 native binary again.
- r4 verifies the source blind_runner manifest, copies it byte-for-byte to a
  short TEMP staging directory, verifies the staged copy again, and imports
  a054_blind._native from there.
- The staged tree is retained for process lifetime and removed at exit.
- The frozen v0.4.0 scientific protocol is unchanged.

After applying:
  run_all.cmd

Expected diagnostic when G2 runs:
- source_manifest_verification.status = PASS
- staged_manifest_verification.status = PASS
- native_probe.status = PASS
- native_probe.openmp_enabled = true
- a054_actual_backend = cpp_pybind11_openmp
