# A058 v0.3.2 — Distribution audit: evidence and interpretation

**Input:** user-supplied `kpdist-23mar2025.zip`. Relative paths below are inside archive root `kpdist-23mar2025/`. Source statements refer to the **March 2025** distribution, not necessarily identical behavior in the October 2026 Windows binary. All file SHA-256 values appear in generated `SOURCE_EVIDENCE.json`.

| Evidence file | Observed fact | Qualified inference |
|---|---|---|
| `demos/Dyna_help.txt` | `elec` repels beads with radial power exponent; `mech` nonlinear neighbor attraction; `amech` spring-rest-length alternative; `tanf` implementation bug; `velfo` proportional to velocity; Damped loses inertia; `dstep` controls redraw cadence | Do not conflate software force options with a physically derived Euler/Biot–Savart model |
| `demos/relax2.kps` | Has `force 1`, `velforce = true`, `velmag = .2`, **and** `collision allow` | Describes a Newtonian/velocity-drag demo, **not** safe evidence for Damped KnotPlot or no-reconnection runs |
| `demos/FreeDrag.kps` | `mech = off`, `amech = on`, `spring = 1.4`, `drag = on`, `dragmag = 15` | `amech` must be independently tested and not silently equated with `mech`; `drag` is not proof of GUI `velfo` equivalence |
| `benchmarks/relaxA-bm.kps` vs `benchmarks/relaxB-bm.kps` | `dstep = 1` vs `dstep = 4`, but both `coll a` and very large `go` | Negative-control *motivation* only; **do not** execute unchanged for collision-safe tests |
| `resource/Lua/Dynamics.lua` | Computes measured bead displacement divided by wall-clock interval from coordinate samples | This is a measurement/display utility, not a force solver or independent time-dilation law |
| `resource/src/simple-reader-writer/kpf_io.cpp` and `.h` | KnotPlot 1.0 binary geometry fields: `LOCC`, `LOCS`, `LOCF`, `LOCD`; big-endian | Independent read-only Python decoder is possible without full KnotPlot engine |
| `resource/src/simple-reader-writer/README.txt` | Minimal reader limited to single closed component | `basic/6.3.3` multi-component link **must not** be silently imported as one curve |

## Independent KPF test measured here (native KnotPlot coordinate units)

| File | Field | N | Centerline length | Radius of gyration | Edge CV | Verdict |
|---|---|---:|---:|---:|---:|---|
| `basic/0_1` | LOCS | 42 | 62.77332743 | 10.00000775 | 0.00007466 | Parsed single-component |
| `basic/3.1` | LOCS | 47 | 56.75846494 | 4.35586441 | 0.01985269 | Parsed single-component |
| `basic/4.1` | LOCS | 69 | 82.63735586 | 5.70296687 | 0.02249113 | Parsed single-component |
| `basic/8.19` | LOCS | 86 | 105.83031809 | 5.78355799 | 0.04615040 | Parsed single-component |
| `basic/6.3.3` | Multiple `comp` chunks | — | — | — | — | UNSUPPORTED_LINK_OR_ENCODING |

**Important:** KPF parsing does not confirm topological equivalence, intrinsic thickness, relaxed/ideal status or physical SI scale. No winding/linking number or Euler flow result is inferred. The `LOCC` decode test also guards its *first* point: the original minimal C++ helper has a missing `vertex[0] = loc` assignment in that branch; our separate decoder explicitly handles it. This is a scoped inspection finding, not a claim that current KnotPlot's engine has this bug.

## Force/control restrictions

- Standard audit controls are **Damped**, `collision fast`, `elec = on`, `mech = on`, `amech = off` (other forces off). This is a *new independent control probe*, not the frozen old A058 experiment.
- `velfo`/CLI `velforce`: excluded from Damped, candidate for a separate Undamped control with initial velocities and a validated numerical clock. The demo does not prove force parameters in 2026 are aliases.
- `tanf`: demonstration-only because source explicitly identifies implementation bug. `tanmag` is not independently physically validated.
- `No Collide`: goal is no self-crossing. `collision fast` is the CLI guard but requires a runtime safety check and segment-distance/time-step envelope; do not claim certainty from a Boolean switch.
- `max-dr < close`: screenshot has 0.100 < 0.120 (both native lengths). This is a *necessary* numerical margin in the cited collision-handling setup, not a global topological theorem. 
- `tinc` (GUI) versus `timeincr` command mapping remains **UNVERIFIED**.
- `dstep`: at matched 32 solver iterations, differing redraw cadence should not change the saved centerline. If it does, record `DIFFERENCE_DETECTED` and investigate GUI side effects, randomization and solver stepping, not immediate model falsification.

## Original sources

```latex
\begin{thebibliography}{9}
\bibitem{Scharein2005} R. G. Scharein, \emph{KnotPlot: A Program for Viewing Mathematical Knots}, KnotPlot manual, Hypnagogic Software, https://knotplot.com/doc/KnotPlot-Manual.pdf.
\bibitem{Scharein2025} R. G. Scharein, \emph{KnotPlot Distribution and Utility Source Code}, build 5093, 23 March 2025, Hypnagogic Software, https://knotplot.com/download/.
\bibitem{SchareinFile} R. G. Scharein, \emph{KnotPlot Distribution}, KnotPlot documentation, https://knotplot.com/manual/Distribution.html.
\end{thebibliography}
```
