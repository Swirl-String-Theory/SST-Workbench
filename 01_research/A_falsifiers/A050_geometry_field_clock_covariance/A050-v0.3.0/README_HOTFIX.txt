A050 v0.3.1 HOTFIX
==================

Cause
-----
The first patch package had malformed a/ paths for three newly-added files:
  config/SEAL_v0.3.1.json
  sst_gfcc_blind/nonstationary.py
  tests/test_v031.py

The observed run also shows that v0.3.1 files were placed below A050-v0.3.0\overlay,
while A050-v0.3.0\run_all.cmd remained the active entrypoint.

Safe repair
-----------
1. Put repair_A050_v031_from_overlay.cmd in the A050-v0.3.0 directory that
   currently contains the overlay directory.
2. Run:
     cmd /c repair_A050_v031_from_overlay.cmd
3. The script creates sibling A050-v0.3.1 and does NOT overwrite v0.3.0.
4. It runs an import smoke test and tests\test_v031.py.
5. Then run from the new directory:
     run_all.cmd C:\workspace\projects\SST-Workbench

The corrected .patch is included for clean future applications.
