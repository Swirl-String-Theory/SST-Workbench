# Blind protocol

1. `run_campaign.py` hashes each input file and replaces the filename by a 16-hex blind ID.
2. The blind score uses only geometry and field observables computed from coordinates.
3. Identity mapping is written to `private/reveal_map.json`. Do not inspect it before freeze.
4. `frozen_result.json` is SHA256-hashed immediately after the campaign.
5. Only `reveal_results.py` verifies that hash, restores filenames, and adds SST-specific secondary interpretations.
6. The following are excluded from blind scoring: particle assignment, `alpha`, electron mass, the secondary `G_H/r_c=4` target, density interpretation, and the torsion impedance target.

Scientific falsification is **not** a process error. `run_all*.cmd` returns success if the numerical campaign completed; the scientific state is recorded as `PASS_CANDIDATE`, `FALSIFIED_RELATIVE_EQUILIBRIUM`, `INCONCLUSIVE_NUMERICS`, or `INVALID_GEOMETRY`.
