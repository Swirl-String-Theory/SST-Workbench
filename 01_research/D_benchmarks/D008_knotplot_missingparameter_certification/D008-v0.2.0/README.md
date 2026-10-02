# KnotPlot 3.1 Missing-Parameter Certification v0.2.2

Hotfix for a false `RUN_FAILED` classification observed on the target KnotPlot build.

## What happened

The target logs contain a harmless startup diagnostic preamble such as:

```text
nothing loaded
*** nothing to save
nothing to output
```

before the real KnotPlot session banner and before:

```text
knot loaded from `3.1'
```

The v0.2.1 runner counted those early lines as hard failures even when the actual
candidate later:

- loaded 3.1 successfully;
- wrote the `i00000` checkpoint;
- ran the relaxation;
- wrote the `i00100` checkpoint;
- exited with code 0.

That caused `charge`, `hooke`, and `power` to be falsely labelled `RUN_FAILED`.

## v0.2.2 policy

- `nothing to save` / `nothing to output` **before the first `knot loaded` line**
  are ignored as startup diagnostics.
- The same messages **after** `knot loaded` remain hard failures.
- `Unknown parameter: timeincr` remains a real parameter rejection.

## Expected certification result from the already observed v0.2.1 run

The uploaded outputs show:

- `charge`: accepted and geometrically effective;
- `hooke`: accepted and geometrically effective;
- `power`: accepted and geometrically effective;
- `timeincr`: rejected by KnotPlot as an unknown parameter.

v0.2.2 should therefore certify the first three and run their `i01000` extended stage.

## Run

Overlay the v0.2.2 patch onto the existing v0.2.x folder and run:

```bat
run_dry.cmd
run_all.cmd
```

Return the generated outputs ZIP for the final 1000-iteration sensitivity analysis.
