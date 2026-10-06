# Validation

`run_python.cmd` must pass unit tests and the deterministic **instrument-only** evaluator self-test.

The self-test is designed so all four hypotheses survive; this verifies that the evaluator is capable of representing every preregistered outcome. It is not physical evidence for any hypothesis.

A physical result requires a separate producer manifest satisfying `docs/INPUT_CONTRACT.md`.


Native build hotfix validation additionally requires:

- `python -m pybind11 --cmakedir` returns a directory containing `pybind11Config.cmake`;
- CMake configure completes using that directory;
- `run_native_parity.cmd` agrees with the Python `circular_order` implementation to `< 1e-12`.
