1. Extract into Workbench 01_research/A_falsifiers/A062_sst_microgravity_force_gradient/A062-v0.1.0.
2. Ensure canonical frozen framework exists at 06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.7.
3. Run `python -m pip install -r requirements.txt` in your intended venv.
4. Run `run_science.cmd SELFTEST`; then `run_science.cmd FREEZE`; `run_science.cmd FULL`; `run_science.cmd CERTIFY`.
5. For strict framework run: `run_all.cmd FREEZE` / `run_all.cmd BASIC`, etc. The installed v1.0.7 instance requirements must be tested locally; the framework itself is NOT included.
6. Do not interpret a standalone success as framework certification; inspect `GATE_LEDGER.json` and `STATUS.json`.
7. All outputs are disposable/rebuildable; edit protocol only by incrementing the falsifier version.
