# SST Blind Multi-Library Falsifier Template v0.1.0

Reusable C++/Python template for adversarial SST falsifiers. It standardizes blinding, provenance, gate ordering, independence units, CPU/GPU authority, output packaging and explicit reveal separation.

## One-click infrastructure test

```cmd
run_all.cmd
```

The bundled `example_experiment` is **not scientific**. It only proves that the scaffold, protocol freeze, gate ledger and packaging work.

For a real study, copy the template, replace `example_experiment`, freeze `PREREGISTRATION.md`, and create a private reveal file whose SHA-256 alone is copied into the blind package.
