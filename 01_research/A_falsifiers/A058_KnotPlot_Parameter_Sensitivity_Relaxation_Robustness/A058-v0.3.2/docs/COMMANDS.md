# New KnotPlot commands — isolated acquisition qualification

Source: user-supplied text from https://knotplot.com/man/ (web retrieval may fail). The commands below are *not silently added to the 271 blinded conditions*.

- `hedgehog Nbeads EdgeLength` produces a synthetic knot; do not substitute for the calibrated T00 trefoil seed.
- `spool Nbeads R r h` produces a spooling-model knot; separate topology check needed.
- `alias <name> "commands;..."` and `frame command "..."; frame N` automate command entry. They can modify geometry if used inside a science run; test only on non-blind scratch inputs.
- `length`, `rog`, `alex -1` compute/capture measures, where `alex -1` is a knot determinant rather than a complete knot identifier.
- `data open`, `data format`, `data header`, `data`, `data close` write CSV. **`data` does not itself calculate quantities**. Invoke the corresponding measure command first. E.g. `length`, `rog`, `alex -1` then `data format "/N,/l,/g,/D,/I"` then `data`.
- Available format tokens also include `/w /W /t /q /s /H /a /L /F` etc. Only use after the appropriate explicit calculation and native command qualification; a valid CSV is not equivalent to validated physics.

Run `python tools/knotplot_command_probe.py --out scratch_probes` to generate 5 standalone scripts. With a tested executable and isolated working directory, add `--exe ... --workdir ...` to attempt each script, retaining `.log` and the native result manifest. Do not run in the clone's `private/` or `campaign/` folders; keep to an isolated non-blind scratch directory.
