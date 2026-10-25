# A003 Fourier Knot Import Adapter v0.2.1

**Status: DEVELOPMENT / GEOMETRIC_IMPORT_QUALIFIED.** This release adds explicit **G4 dimensional scale-binding** and an optional **G5 independent Alexander-determinant screen**. It does **not** establish a physically unique core radius, an independently certified knot identity, chirality, or Euler/PKLSA dynamics.

The pinned external source remains `A003-v0.1.1` (30 seeds; 240 SHA-256-protected XYZ exports), with BASIC N=1200/2400 and FULL N=4800/9600, `uniform_t` and `uniform_s_polyline`. Neither the source atlas nor frozen SST Knot Library is modified.

## Target installation (Windows)

```text
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\
  A003_Fourier_Knot_Seed_Atlas\
    A003-v0.1.1\
    A003_Fourier_Knot_Import_Adapter_v0.1.0\
    A003_Fourier_Knot_Import_Adapter_v0.1.1\
    A003_Fourier_Knot_Import_Adapter_v0.2.0\  <-- frozen previous release
    A003_Fourier_Knot_Import_Adapter_v0.2.1\  <-- unzip this package
```

Python >= 3.10 and NumPy are required for G0–G4. Independent G5 is **optional** and requires an explicitly installed and functional `pyknotid` runtime (no automatic third-party installation).

```bat
cd /d C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.2.1
run_all.cmd
```

`run_all.cmd` performs a **demonstration G4 scale binding with an assumed** `a*=0.05` (unchanged from the v0.2.0 CMD default). This is only a configurable hypothesis, not a measured or canonical dimensionless core radius. G5 remains **NOT_RUN** unless explicitly requested. To run *without* any G4 assumption, invoke `python fourier_atlas_adapter.py --out outputs catalog` directly.

## G4: explicit physical-scale hypothesis

The source atlas coordinates \(\mathbf X^*\) are dimensionless. A **user-chosen**, positive dimensionless finite-core radius \(a_*\) gives a *conditional* scale

$$
\ell_0 = \frac{r_c}{a_*},\quad r_c=1.40897017\times10^{-15}\,\mathrm m,\quad
\mathbf X_{\rm SI}=\ell_0\mathbf X^*,\quad L_{\rm SI}=\ell_0 L_*.
$$

**Nothing in the Fourier centerline proves that \(a_*\) equals the physical vortex core radius.** In particular, assigning \(a_* = 0.05\) is an example, **not** an SST measurement or canonical dimensionless core radius. It gives \(\ell_0=2.81794034\times10^{-14}\,\mathrm{m}\) per coordinate unit.

```bat
python fourier_atlas_adapter.py --reference-core-radius-units 0.05 --out outputs catalog
```

Reports G4 `PASS_DIMENSIONAL_HYPOTHESIS_ONLY`: arithmetic and SI units are defined, while finite-core thickness, self-confinement and any mass, gravity or time claims remain **UNRESOLVED**. G4 uses independently measured polyline length per file and preserves every original XYZ byte.

You may also configure `run_all.cmd`:

```bat
set "SST_A003_REFERENCE_CORE_RADIUS_UNITS=0.05"
run_all.cmd
```

To prepare a geometrically scaled file with the *existing pinned* `sst_knotlib` interface, specify the core radius in meters once G4 is anchored:

```bat
set "SST_KNOT_LIBRARY_HOME=C:\path\to\SST_Knot_Library_v0.2.5"
python fourier_atlas_adapter.py --reference-core-radius-units 0.05 --out outputs prepare --seed torus_8_19_direct --N 2400 --target-N 512 --core-radius 1.40897017e-15 --expected-library-version 0.2.5
```

The original v0.1.1 `--unit-scale-m` path remains available for explicit legacy preparation, but cannot be combined with G4 reference-core-radius mode. The full native Knot Library runtime was **not executed in this environment**, only its mock contract. Do not assert equivalence to Knot Library v0.3.2 without a real compatibility test.

## G5: independent topology diagnostic (optional)

```bat
python -m pip install pyknotid
run_g5.cmd
rem Equivalent explicit command:
python fourier_atlas_adapter.py --g5 --require-g5-evidence --g5-resolutions BASIC --out outputs catalog
```

G5 loads and rehashes actual source XYZ data at N=1200 and N=2400, calculates the Alexander determinant with `pyknotid`, compares to algebraic necessary reference values for coprime torus/twist families, and checks resolution agreement. `--g5-resolutions FULL` checks N=4800 and 9600; `ALL` uses all four. Computations may be expensive; provider success depends on local installation and compatibility.

- `INVARIANT_SCREEN_ONLY_NOT_CERTIFIED`: values agree at chosen resolutions, **not** a proof of knot identity. Chirality remains unresolved. This state is a *screening result*, not G5 `CERTIFIED`.
- `FAIL_INVARIANT_SCREEN`: mismatch to algebraic reference or resolution disagreement. Command exits 2 and saves an audit report.
- `PROVIDER_UNAVAILABLE`: `pyknotid` absent; command exits 2 and saves audit report.
- `PARTIAL_UNRESOLVED`: per-seed provider errors; command exits 2 and saves audit report.

A knot determinant is not a complete topological invariant. The optional provider may reveal errors, but it cannot prove isotopy, classify mirror chirality or certify geometry in general. **G5 remains incomplete as a full knot-identity gate even after all determinant checks match.**

To run G4 and G5 together in `run_all.cmd` (with a supported provider), set:

```bat
set "SST_A003_REFERENCE_CORE_RADIUS_UNITS=0.05"
set "SST_A003_RUN_G5=1"
run_all.cmd
```

No third-party library is silently installed. Source hashes are verified before each independent G5 provider call. All results are registered in JSON sidecars, without writing `catalog_index.json` or `family_hierarchy.json`.

## Gate semantics

| Gate | Normal `run_all.cmd` | Explicit optional execution |
|---|---|---|
| G0 manifest/source pin | PASS | same |
| G1 240 SHA-256/XYZ files | PASS | same |
| G2 mirror projection diagnostic | PASS | same; does not establish chirality |
| G3 BASIC/FULL convergence | PASS | same; **20 polygon-chord warnings preserved** |
| G4 SI mapping | PASS_DIMENSIONAL_HYPOTHESIS_ONLY from default assumed a*=0.05 | NOT_DEFINED only without radius option |
| G5 independent topology | NOT_RUN | invariant screen only; not topological proof |
| G6 PKLSA/Euler | NOT_RUN | remains NOT_RUN |

`outputs/validation_report.json` and `outputs/fourier_external_registry.json` are regenerated every run; old releases and the pinned atlas are untouched. This adapter is not an SST Falsifier Framework v1.0.7 instance; it is only a geometry-provider bridge and scale/invariant screening tool.

## Implementation and literature

- `fourier_atlas_adapter.py`: pinned G0–G3 atlas audit, read-only registry and existing `sst_knotlib` adapter, new CLI.
- `gates_g4_g5.py`: pure G4 mapping and optional independent `pyknotid` G5 invariant screen.
- `tests/test_adapter.py`: regression tests with mock provider checks explicitly marked as mock, not real G5 evidence.
- `MANIFEST_SHA256.txt`: hashes the shipped release source files and docs, not the mutable `outputs/` directory.

### References (LaTeX bibliography-ready)

```latex
\bibitem{Kauffman1997} L. H. Kauffman (1997),
\textit{Fourier Knots}, arXiv:q-alg/9711013,
https://arxiv.org/abs/q-alg/9711013.
\bibitem{Hoste2009} J. Hoste (2009),
\textit{Torus Knots Are Fourier-(1,1,2) Knots},
J. Knot Theory Ramifications 18, 265--270,
https://doi.org/10.1142/S0218216509006926.
\bibitem{Boocher2009} A. Boocher, J. Daigle, J. Hoste, W. Zheng (2009),
\textit{Sampling Lissajous and Fourier Knots},
Experimental Mathematics 18, 481--497,
https://doi.org/10.1080/10586458.2009.10129057.
\bibitem{Pyknotid} A. J. Taylor and collaborators,
\textit{pyknotid: knot analysis software}, software documentation,
https://pyknotid.readthedocs.io/en/stable/.
```

## v0.2.1 CLI hotfix notes

The **v0.2.0 A003 build** accepts `--reference-core-radius-units`, whereas an alternate v0.2.0 distribution used `--a-star`. They are not interchangeable without a matching Python CLI. v0.2.1 standardizes on the former and additionally accepts `--a-star` as a deprecated alias. The new CMD launcher uses the canonical option. This hotfix does **not** modify Fourier XYZ exports, validation tolerances, physical assumptions, G5 provider rules, or PKLSA/Euler computations.

### Fast in-place fix if you do not install v0.2.1

Open `run_all.cmd` in your installed v0.2.0 A003 folder. Change only:

```text
--a-star "%A_STAR%"   -->   --reference-core-radius-units "%A_STAR%"
```

After this substitution the original v0.2.0 launcher should invoke the supported parser; v0.2.1 is preferable for a versioned audit.