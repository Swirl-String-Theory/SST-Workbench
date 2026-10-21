# A058-v0.3.4 shortcut working-directory contract

Problem in v0.3.2: the probe process used `cwd=<A058_probes>/dstep_1` and
`cwd=<A058_probes>/dstep_4`.  That is **not** the Windows Shortcut **Start in**
directory. KnotPlot can therefore resolve relative built-in resources in the
wrong directory, and naive relative `save` commands also redirect output.

## Fixed launch behaviour

- `--exe ".\KnotPlot.lnk"`: PowerShell 5+ `WScript.Shell.CreateShortcut` retrieves
  `.TargetPath`, `.WorkingDirectory`, and `.Arguments` from the original
  shortcut. It is parsed as metadata, not executed as a `.lnk` binary.
- `--exe ".\KnotPlot.exe"` (or a full EXE path): uses the EXE's parent as cwd.
- Absolute shortcut Start-in is authoritative. Relative `.` uses the target EXE's parent; other relative paths are considered against both the target EXE's parent and the shortcut's parent. A unique existing candidate is accepted; ambiguous or nonexistent paths require an explicit absolute `--workdir` override. Empty Start-in falls back to the target EXE's parent. All decisions are recorded in private provenance.
- All arguments already embedded in the shortcut are carried through; A058
  appends `-stdin -nographics`. The target build must accept those arguments.
- The inherited `probe.kpc` is preserved byte-for-byte. A per-run
  `probe.native.kpc` supplies absolute input and output locations:
  - `load <A058_probes>/dstep_N/A058_seed.kpf`
  - `data open <A058_probes>/dstep_N/A058_native_metrics.csv`
  - `save <A058_probes>/dstep_N/A058_final.txt ascii`
- KnotPlot starts with cwd = the Shortcut's `Start in`, but the three A058
  input/output files remain in the respective `dstep_N` directories. This
  avoids polluting the KnotPlot installation or relying on ambiguous cwd.
- Paths containing spaces are double-quoted in the generated KnotPlot script.
  Support for quoted filenames must be checked against the real 2026 executable.
- Private provenance: `A058_probes/NATIVE_LAUNCH_PRIVATE.json`, hash-bound
  runtime script and original `probe.kpc`; filenames may expose user paths.
- Existing native results/logs are never overwritten; use a freshly generated
  probe tree for retries or copy a still-unused tree.

Example:

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\KnotPlot.lnk"
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --out ".\A058_probes" --timeout 120
```

## Remaining limitations

Shortcut *startup semantics* are emulated by starting its EXE with its
Start-in and arguments; ShellExecute-specific features (administrator run level,
window style, shortcut environment setup, and shell hooks) are not reproduced.
No real 2026 KnotPlot execution was available during package validation. The
runner still requires stronger getter, positive `safe`, and iteration-counter
verification for scientific certification. Internal KnotPlot-generated files
outside of the three explicit A058 commands are not controlled by this patch.

## v0.3.4 optional explicit disambiguation

If shortcut Start-in is relative and resolves to two different valid directories, run:

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\KnotPlot.lnk" --workdir "C:\absolute\KnotPlot-workdir"
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --workdir "C:\absolute\KnotPlot-workdir" --out ".\A058_probes" --timeout 120
```

Only the **process working directory** changes. All three A058-managed I/O commands use absolute paths under the probe output tree. `CHECK_SHORTCUT` executes neither KnotPlot nor scientific tests. The real shortcut startup mode is not wholly emulated by COM metadata (shell hooks, elevated permissions and other settings may differ).
