# QGI v0.1.0 patch — MSVC `ssize_t` portability fix

## Root cause

The setuptools discovery error is fixed. The current build reaches MSVC successfully.

The first real compiler error is:

```text
cpp/sst_qgi_native.cpp(14): error C4430: missing type specifier
```

Line 14 used the POSIX/global type:

```cpp
const ssize_t n = b.shape(0);
```

`ssize_t` is not a portable global C++ type on MSVC. The remaining compiler messages are
cascade errors caused by that first parse failure.

## Fix

All geometry-index variables now use pybind11's portable signed-size type:

```cpp
py::ssize_t
```

The patch also adds:

```cpp
#include <algorithm>
```

because `std::min` is used explicitly.

`run_02_build_native.cmd` is also hardened so its diagnostic `echo` lines contain no
unescaped CMD parentheses and it now distinguishes source portability errors from
setuptools/compiler-installation errors.

## Apply

Copy these files over the project:

```text
cpp\sst_qgi_native.cpp
run_02_build_native.cmd
```

Keep the previous `setup.py` package-discovery fix in place.

Then rerun:

```bat
run_all.cmd
```

A successful build should reach:

```text
native backend: cpp-pybind11
```
