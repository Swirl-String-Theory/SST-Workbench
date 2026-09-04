# v0.1.1 — Windows/MSVC native-build repair

## Fixed

- Replaced non-portable POSIX `ssize_t` loop/index declarations in `cpp/native.cpp`
  with standard C++17 `std::ptrdiff_t`.  MSVC does not define `ssize_t`, which caused
  the C4430/C2146 cascade seen under Visual Studio 2022.
- Kept the OpenMP loops in canonical signed-integral form accepted by MSVC.
- Added explicit `<cstddef>` and `<stdexcept>` includes.
- Made the native build helper use `--force`, verify import after compilation, and
  retry once without OpenMP when the compiler/toolchain lacks OpenMP support.
- Preserved the Python/C++ numerical parity tests for curve length and Gauss linking.

## Expected Windows result

`run_all.cmd` should now pass the native build on Visual Studio 2022 / Python 3.14.
If OpenMP itself is unavailable, the package automatically builds the serial C++17
extension instead of failing installation.
