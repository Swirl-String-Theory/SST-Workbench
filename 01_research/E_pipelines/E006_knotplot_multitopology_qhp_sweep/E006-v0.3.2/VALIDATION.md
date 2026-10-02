# Validation — v0.3.2.2

- v0.3.1 proportional bead-allocation tests: PASS.
- v0.3.2 timer/stage tests: PASS.
- v0.3.2.1 synthetic unlink tests: PASS.
- 2.2.1 prep script reconstructs topology twice and exports `keep 0`, `keep 1`.
- 6.3.2 prep reconstructs topology three times and exports components 0..2.
- generated torus 6.9 does the same for its 3 components.
- Stage-1 generate-only: 90/90 QHP scripts plus isolated component prep scripts.
- Full-link coords component separators are no longer required.
- Real Windows KnotPlot execution is required to validate the actual component files.


## v0.3.2.3 metric-neutral resume

- Resume KPC prefix contains no `fitto`, `refine`, or `centre`: PASS.
- Resume probe contains no geometric transform: PASS.
- Resume probe writes length/Rg/nbeads metrics before further evolution.
- Runner blocks resumed `ago` until relative length and Rg continuity pass at 2e-5.
- Existing stage/component/allocation tests remain PASS.
