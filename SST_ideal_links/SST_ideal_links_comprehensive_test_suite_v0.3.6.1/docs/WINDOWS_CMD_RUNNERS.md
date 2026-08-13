# Windows CMD runners — v0.3.4.1

This hotfix adds a native `cmd.exe` equivalent for every top-level `run_*.ps1`.
None of the CMD runners invokes PowerShell.

The runner always prefers:

`.\.venv\Scripts\python.exe`

and falls back to `python` only when that file does not exist.

## Mapping

| PowerShell | CMD |
|---|---|
| `run_all.ps1` | `run_all.cmd` |
| `run_all_chunked.ps1` | `run_all_chunked.cmd` |
| `run_continuum.ps1` | `run_continuum.cmd` |
| `run_qm.ps1` | `run_qm.cmd` |
| `run_qm_chunked.ps1` | `run_qm_chunked.cmd` |
| `run_spectral.ps1` | `run_spectral.cmd` |

## Continuum examples

PowerShell form:

`.\run_continuum.ps1 -Preset max -Ids L6a4,L4a1,L6n1,L7n2`

CMD accepts the same option names:

`run_continuum.cmd -Preset max -Ids L6a4,L4a1,L6n1,L7n2`

or conventional argparse syntax:

`run_continuum.cmd --preset max --ids L6a4 L4a1 L6n1 L7n2`

## Spectral

`run_spectral.cmd -Ids L6a4,L4a1,L6n1,L7n2`

## QM full

`run_qm.cmd -Preset full -Ids L2a1,L4a1,L6a4,L6n1,L7n2 -NativeThreads 16`

## Process-isolated QM

`run_qm_chunked.cmd -Preset full -Ids L2a1,L4a1,L6a4,L6n1,L7n2 -NativeThreads 16 -Retry 1`

## General full campaign

`run_all.cmd -Preset full -NativeThreads 16`

All runners propagate the Python process exit code to cmd.exe.


## v0.3.5 QM spectral choice

```cmd
run_qm.cmd -Preset full -Spectral raw -Ids L6a4
run_qm.cmd -Preset full -Spectral raw-resolved -Ids L6a4
run_qm.cmd -Preset full -Spectral filtered -Ids L6a4
run_qm_spectral_ladder.cmd -Ids L4a1,L6a4,L6n1,L7n2
```
