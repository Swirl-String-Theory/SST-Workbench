# A054 v0.4.0-r2 native/MSVC hotfix

Scientific contracts, geometry cohorts, mechanism definitions, gains and hard gates are unchanged from r1.

Execution fixes:
1. Replace POSIX-only `ssize_t` in `cpp/native.cpp` with `py::ssize_t`, which is portable across MSVC and GCC/Clang.
2. Add native parity coverage for both the ELASTIC and CORE raw kernels.
3. Fix Windows CMD failure propagation: r1 used `%RC%` inside the same parenthesized block in which it was assigned, so expansion could use a stale/empty value and allow later stages to run after a failed install. r2 exits immediately on every failed setup/FREEZE/certification command.
4. Update the maintenance release identifier/output path to v0.4.0-r2.

No framework v1.0.4 modification is required.
