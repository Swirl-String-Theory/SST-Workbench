# Integration into the *actual* frozen framework v1.0.7

Do not edit the frozen framework. It is Drive folder `1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE` at:
`SST-Workbench/06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.7`.

1. Resolve the catalog conflict: A059 already exists and was v0.2.0. Either register a new revision `A059-v0.3.0` under the same family, or obtain a new unique catalog ID via Workbench before production freeze. **Do not overwrite A059 v0.2.0.**
2. In Workbench, generate the fresh target instance using exactly the frozen framework:

```bat
cd C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7
python tools\new_falsifier.py A059 swirlclock_bohr_delay_action C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A059_SST_Quantum_Number_Rosetta_Mega_Falsifier\A059-v0.3.0 --profile minimal --version v0.3.0
```

3. Copy scientific routines from `src/core.py` and `src/run.py` into a dedicated instance-local module, and map preregistered G0-G9 to `experiment/pipeline.py` using the instance template's `science_contract.json`, `gate_plan.json`, `source_contract.json` and `blind_policy.json`. Never replace `framework_bootstrap.py`, `run_instance.py`, `run_python.py` or framework-owned files with this standalone runner.
4. Move synthetic controls into `inputs/` as `synthetic_control`; do not claim 3 independent scientific sources. The real time-resolved PKLSA source must pass qualification before science gates can be registered as executable.
5. Set `.sst_framework_root` using the generator's strict relative locator. `run_all.cmd SELFTEST`, `run_all.cmd FREEZE`, `run_all.cmd FULL`. Use `REVEAL_IF_ALLOWED` for scheduled orchestration; do not force reveal. The framework writes its own authoritative gate ledger, report PDF, output manifest and archives.
6. In protocol, promote synthetic control metrics only to `PASS_CONTROL`. G7-G9 remain `UNRESOLVED` with no physical certification. Record CPU Python FP64 only as reference; no unexecuted C++/SYCL certification.

This ZIP is *framework-targeted*, but not a replacement for the actual frozen runtime. There is no valid v1.0.7 certification certificate in the isolated environment used to build this package.
