# A050-v0.3.1 patch notes

Target: `A050-v0.3.0` copied to a new `A050-v0.3.1` directory.

Purpose: add a blind diagnostic that distinguishes stationary coherent phase, coherent frequency drift/chirp, and incoherent/unresolved phase on the dynamically selected transverse branch. The v0.3.0 primary acceptance logic is replayed unchanged and remains authoritative for the primary verdict.

Recommended copy-on-write creation from the existing v0.3.0 directory:

```bat
make_A050_v0.3.1_from_v0.3.0.cmd C:\\workspace\\projects\\SST-Workbench\\01_research\\A_falsifiers\\<A050-folder>\\A050-v0.3.0
```

Or, if you already copied the directory yourself:

```bat
apply_A050_v0.3.1_patch.cmd C:\\path\\to\\A050-v0.3.1
```

Then run:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench
```

The patch does not change the PKLSA source panel or introduce a synthetic fallback. It keeps source identity reveal-only and does not hard-code m=3.
