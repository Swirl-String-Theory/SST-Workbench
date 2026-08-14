# v0.2.0 changes — 5_Maxwell branch

- renamed branch/package with required `5_` prefix;
- adopted the supplied pybind11 C++ audit-template architecture;
- added multithreaded C++ segment/contact/kink kernel;
- added strict `--require-native` production runs;
- added shared `..\..\.venv` installer/build flow;
- added direct `..\..\KnotPlot\knots\final` scanner;
- fixed component parsing for shared-final links via `vertices_per_component`;
- changed inferred contacts from a one-sided distance cutoff to a two-sided thickness shell;
- set baseline contact-shell fraction to `1e-4` and added a frozen extended tolerance ladder;
- added preregistered Ridgerunner residual QC (`<=0.05`) so under-relaxed data are inventoried but not interpreted as equilibrium falsifiers;
- added near-singular coordinate-perturbation testing in extended mode;
- replaced slow sparse bounded least-squares with dense Lawson–Hanson NNLS for the current matrix sizes;
- retained blind hashing, private mapping separation, positive self-stress LP, rank/nullity, local closure, projection sanity, force-area identity and strict-reciprocity guard;
- added `5_run_install.cmd`, `5_run_basic.cmd`, `5_run_extended.cmd`, `5_run_all.cmd`, `5_run_tests.cmd`, `5_run_benchmark.cmd`, and `5_run_custom.cmd`.
