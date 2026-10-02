
# Ridgerunner bridge — role and limits

Ridgerunner is **not required** to analyze the supplied Gilbert Fourier geometries. Those are the
objects being measured. Re-optimizing them first would change the object and could hide source
errors or introduce optimizer-dependent drift.

Ridgerunner is useful as an independent second-stage gate:

1. export the unchanged Fourier geometry to a closed multi-component `.vect` file;
2. record the source SHA-256, sample count and `D=1` normalization;
3. run Ridgerunner in a separate output directory;
4. compare length, thickness, strut/contact structure and topology before accepting a refined shape;
5. never overwrite the Gilbert-source baseline.

Export the 18 low-crossing links:

```powershell
python -m sst_link_suite.cli export-ridgerunner `
  --input data\idealLinks.txt `
  --output ridgerunner_inputs `
  --sample-n 2048
```

Export all 130 database links:

```powershell
python -m sst_link_suite.cli export-ridgerunner `
  --input data\idealLinks.txt `
  --output ridgerunner_inputs_all `
  --sample-n 2048 `
  --all-database
```

The suite deliberately does not guess Ridgerunner command-line flags because builds and local
pipelines differ. The generated manifest fixes provenance and states that the target tube thickness
under Gilbert's diameter convention is `0.5`.
