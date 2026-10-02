# Validation record — v0.2.0

Validation performed before packaging:

- `python -m py_compile sst_chiral/*.py`: PASS.
- All JSON campaign configurations parse successfully: PASS.
- Multi-component pack/unpack and proportional resampling: PASS.
- Blank-block XYZ two-component parsing: PASS.
- Geomview/KnotPlot VECT component-count parsing: PASS.
- `torus_2.4` VECT component-count consistency gate: PASS.
- Physical mirror mapping of local differential chirality: parity-odd to floating-point precision in the synthetic trefoil test.
- C++17/OpenMP `_native.cpp` syntax compilation: PASS.
- Native shared-library compilation in the packaging container using locally available pybind11 headers: PASS.
- Native `sst_chiral.selftest`: PASS.
- Native multi-component superposition relative error: approximately `3.77e-16`.
- Native off-filament velocity parity relative error: approximately `2.54e-16`.
- Native centerline-helicity parity/time-reversal residual: approximately `6.61e-17`.
- Native trajectory-variational self-test transport pair: approximately `+0.0571932` and `-0.0571932`.
- Full native synthetic end-to-end `prepare -> blind -> analyze -> seal -> reveal`: PASS.
- Full native synthetic end-to-end mirror transport odd residual after the smooth directional-moment correction: approximately `5.5e-14`.
- Private reveal key is absent from the blind output directory and commitment/seal verification succeeds before reveal: PASS.
- Independent-statistics regression confirms that multiple resolution/core conditions aggregate to one source mirror-pair rather than inflating sample size: PASS.

## Packaging-environment note

The container does not have the `pybind11` Python package installed and cannot download packages, so `setup.py build_ext --inplace` itself could not be exercised through `pybind11.setup_helpers`. The C++ extension was nevertheless compiled and executed successfully using an already-present local copy of the pybind11 headers. On Windows, `run_00_setup.cmd` installs the declared `pybind11>=3.0` dependency before `run_01_build_native.cmd`, and `run_05_selftest.cmd` is mandatory before every campaign.
