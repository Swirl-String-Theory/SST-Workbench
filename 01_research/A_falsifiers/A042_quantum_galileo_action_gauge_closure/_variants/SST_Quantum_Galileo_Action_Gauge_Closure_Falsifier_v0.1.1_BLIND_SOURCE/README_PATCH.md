# QGI v0.1.1 dual Visual Studio patch

This patch **adds** Visual Studio 2026 support while preserving the previous
Visual Studio 2022 path.

Compiler selection order:

1. existing `cl.exe` already on PATH;
2. Visual Studio 2026 Community:
   - `x64`
   - `x86_amd64`
3. Visual Studio 2022 Community:
   - `x64`
   - `x86_amd64`
4. Visual Studio 2026 BuildTools:
   - `x64`
   - `x86_amd64`
5. Visual Studio 2022 BuildTools:
   - `x64`
   - `x86_amd64`

After each `vcvarsall.bat` call the script verifies `where cl`.
A nominal `ERRORLEVEL=0` is therefore not enough by itself.

Once a real compiler is found, the script sets:

```bat
set DISTUTILS_USE_SDK=1
set MSSdk=1
```

This prevents setuptools from invoking `vcvarsall.bat` a second time and failing
on installations that emit harmless `The system cannot find the path specified`
messages during Visual Studio environment setup.

## Apply

Overwrite only:

```text
run_02_build_native.cmd
```

Do **not** remove the previous `setup.py` package-discovery fix or the
`py::ssize_t` MSVC portability fix.

Then rerun:

```bat
run_all.cmd
```
