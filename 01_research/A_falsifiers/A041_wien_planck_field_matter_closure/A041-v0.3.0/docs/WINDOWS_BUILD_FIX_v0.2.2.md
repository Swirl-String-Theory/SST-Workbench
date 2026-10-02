# Windows native-build hotfix v0.3.0

## Failure reproduced from the v0.2.1 user log

The Python 3.14 environment and dependencies installed successfully. The failure occurred at `build_ext`, before `native.cpp` compiled, while setuptools attempted to initialize MSVC through:

```text
cmd /u /c "...vcvarsall.bat" x86_amd64 && set
```

The log simultaneously showed repeated `The system cannot find the path specified.` messages and a Visual Studio 2026 Developer Command Prompt banner. This means the compiler installation was discovered, but the subprocess bootstrap shell was contaminated by a path/AutoRun failure.

## v0.3.0 fix

`run_01_build_native.cmd` now:

1. reuses an existing `cl.exe` environment when available;
2. otherwise locates Visual Studio with `VSINSTALLDIR`, `vswhere.exe`, or conservative VS 18/2022 fallbacks;
3. calls `vcvarsall.bat` directly in the current batch process;
4. checks `cl.exe` and `link.exe` explicitly;
5. sets

```text
DISTUTILS_USE_SDK=1
MSSdk=1
```

before invoking setuptools, so setuptools does **not** launch its own `cmd /u /c vcvarsall...` environment bootstrap;
6. provides `run_01_build_native_clean.cmd`, which starts the native build under `cmd.exe /d` so registry `Command Processor\AutoRun` hooks are disabled in the child shell.

All runners now enter their own package directory via `pushd "%~dp0"`, and normal Python steps invoke `.venv\Scripts\python.exe` directly instead of depending on activation or the caller's working directory.

## Recommended first retry

```bat
run_01_build_native_clean.cmd
```

If that succeeds:

```bat
run_all.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
```

Use the actual dataset path on the machine. The build fix changes no scientific gate, no blind constant policy, no numerical kernel, and no threshold.
