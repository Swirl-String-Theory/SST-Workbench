# Generation validation

- Python fallback unit tests: **PASS**.
- Native C++ compile in this generation container: **NOT RUN** because pybind11 headers are not installed here; the Windows scientific chain requires a real native build.
- Synthetic Planck-like positive control blind pass: `True`.
- Synthetic classical continuous-action control blind pass: `False`; classical null triggered: `True`.
- Tiny isolated raw-geometry trefoil fallback campaign: **executed successfully** and blind analysis completed; its blind pass was `False`. The resolved-energy gate passed fraction was `0.0`. This is pipeline validation only.

No synthetic or fallback result is SST evidence.

- Python source compileall after final patch: **PASS**.
- Windows/MSVC portability guard: C++ uses an explicit PI constant and relative `cpp/native.cpp` source with compact `build\temp_native`.
