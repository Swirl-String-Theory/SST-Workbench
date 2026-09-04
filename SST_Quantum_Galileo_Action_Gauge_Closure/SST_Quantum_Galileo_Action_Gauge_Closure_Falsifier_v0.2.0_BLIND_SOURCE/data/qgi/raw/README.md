# QGI raw population input

Preferred scientific input:

`fig2_population_raw.csv`

Required columns:

```csv
twoT_s,population_outport1,sem_population
0.000400,0.523,0.012
...
```

Accepted aliases are documented in `sst_qgi/phase_data.py`.

The pipeline follows the analysis structure published by Dobkowski et al.:

1. identify upper/lower population envelopes;
2. fit seventh-order envelope polynomials;
3. normalize by local mean/visibility;
4. use a Hilbert transform for an initial unwrapped phase;
5. fit a cubic phase polynomial;
6. exclude the first and last oscillation;
7. use the cubic phase as the initial condition for a direct population fit.

No author-level machine-readable raw data file was identified in the paper or supplement, so
this release does **not** invent or relabel digitized points as raw data.
