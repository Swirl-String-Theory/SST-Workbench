# A003 first deviating pyknotid operation — reproducible probe

This is an independent **read-only** diagnostic add-on for A003 v0.2.6. Put this directory beside `A003-v0.1.2` under the A003 atlas parent and run `run_probe.cmd` using the same SST-Workbench `.venv` that contains NumPy 2.4.6 and pyknotid 0.5.3. Or use `run_probe.cmd --atlas C:\...\A003-v0.1.2`.

The script verifies the exact SHA-256 records for both N1200/N2400 XYZ files, projects using frozen P1 (0.63,1.17), evaluates all four frozen crossing pairs, and produces `FIRST_DIVERGENCE_REPORT.json`. It additionally reads the installed helper's source and, if pyknotid is available, compares stock `raw_crossings`, unmodified Gauss code, simplified Gauss code and Alexander at t=-1 against a **strictly temporary, in-process scale-invariant orientation guard**. The original helper function is restored after each comparison; no site-packages or atlas files are edited.

Use `run_probe.cmd --offline-only` for an independent numeric reproduction without the pyknotid provider. The provider stage is marked `UNRESOLVED` if the package is missing or raises an exception; it is never silently marked PASS.

The origin of the error is the first conditional in `pyknotid.spacecurves.helpers.do_vectors_intersect`: `abs(cross_product(...)) < 0.00001` tests a quantity with units of coordinate² against a constant unrelated to the mesh resolution. The 131/2083 crossing at N2400/P1 has raw cross product magnitude 9.6924960e-6, i.e. below cutoff, whereas N1200/P1 counterpart 65/1041 is 3.9213100e-5. Its angle is still nondegenerate, sine ~0.2657. Changing `use_max_jump` to `naive` does not repair this hard cutoff since both use the same `do_vectors_intersect` test.

**Scientific boundaries:** a successful temporary numerical test does not certify `pyknotid` generally or knot chirality, A003-G5 or SST physics. The G5 historical failure must remain archived. A permanent correction requires a new version and independent regression tests for other knots.

### Independent reproduction (this analysis environment)

The independent numeric probe ran on the SHA-verified atlas snapshot, without installing pyknotid in this environment, and confirmed all 8 expected crossing pairs. In particular, for N2400/P1 it confirmed that `find_crossings` with the stock `use_max_jump` scheduler **does visit segment 2083** when processing segment 131; it is the subsequent absolute `do_vectors_intersect` guard that wrongly rejects this particular pair. Other three crossings are not suppressed by that guard. The installed-provider test in the CMD script will additionally check this inference against your local 0.5.3 package and write its internal Gauss-code state.
