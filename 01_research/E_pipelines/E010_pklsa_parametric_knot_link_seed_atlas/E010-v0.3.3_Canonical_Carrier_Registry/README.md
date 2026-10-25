# E010 PKLSA Canonical Carrier Registry v0.3.3 — create-only installer

This is a separate **versioned source registry release**, not a copy of the full E010 v0.3.2 data distribution. Run `e010_registry_v033.py` to create E010-v0.3.3 as a sibling copied from YOUR original local E010-v0.3.2 tree. Never overwrite an existing target. It requires the exact frozen parent source-contract and native resolver SHA256 and all eight original A003 source XYZ SHA256.

```bat
python e010_registry_v033.py --base "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.2" --target "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.3" --workbench "C:\workspace\projects\SST-Workbench" --atlas "C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003-v0.1.2"
```

Repeat with `--verify` to check independently after installation. The new release contains `registries/a003_carriers_v033.json`, changed source contract, `RELEASE_CARRIER_REGISTRY_v033.json`; old parent remains immutable. The registry consists of eight analytic A003 F3/F4 carriers in **two** independence groups and **zero** independently measured carriers. It does not certify physical dynamics.
