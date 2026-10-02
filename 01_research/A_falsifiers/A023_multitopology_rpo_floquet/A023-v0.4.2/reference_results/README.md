# Reference results

`v0.3.0_basic/` is a convenience snapshot from a BASIC Python-reference-backend validation against the exact files in `repro_inputs/`.

It is **not** used as expected-answer input by the falsifier. Recompute it with:

```bat
run_reproduce_history_basic.cmd
```

or run v0.3.0 directly against `repro_inputs/`. The scientific source of truth remains the versioned code, preregistered config and bundled input hashes.
