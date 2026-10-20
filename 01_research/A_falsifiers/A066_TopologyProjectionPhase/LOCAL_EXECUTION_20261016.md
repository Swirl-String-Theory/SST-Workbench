# Local execution 2026-10-16

Both source packages were already extracted. No scientific source code was modified. Existing v0.3.0 results were preserved. No reveal was performed.

Each package was installed using its own run_all.cmd SELFTEST, which created .venv and installed requirements.txt. Python selected by py -3: 3.14 (see environment files). Test outputs are in execution_SELFTEST_20261016.log.

v0.2.0: 16 tests passed (exit 0). Commands from its source directory:

    run_all.cmd SELFTEST
    run_all.cmd FREEZE
    run_all.cmd EULER_PILOT --pklsa external_pklsa\reference\PKLSA_TREFOIL_3_1_N300_CENTERLINE.npz --grid 24 --steps 8 --duration-model 0.10 --sigma-model 0.50
    run_all.cmd CERTIFY

FREEZE and EULER_PILOT exited 0. Input hashes, freeze-ledger self hash and all frozen output hashes were independently checked: PASS. CERTIFY exited 2 as documented (native framework, independent trajectories and nonideal PDE qualification unavailable).

v0.3.0: 28 tests passed (exit 0). Small deterministic Euler smoke run (exit 0) from its source directory:

    .venv\Scripts\python.exe -c "from pathlib import Path; from src.long_euler import selected_cases,run; it=selected_cases()['KP_3_1_N300']; run(it['curves'],name='KP_3_1_N300',grid=24,steps=8,duration=0.1,sigma=0.5,output=Path('local_runs/20261016_smoke'),source_sha256=it['sha256'])"

Outputs: local_runs/20261016_smoke/*.json and *.npz. The full LONG campaign and whole-library Euler queue were not run. These are dimensionless exploratory calculations, not physical SST certification or convergence qualification.
