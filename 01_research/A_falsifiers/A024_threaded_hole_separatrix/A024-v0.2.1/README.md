# SST Threaded-Hole Substrate Blind Falsifier v0.2.1

Blind C++/Python workbench for a coupled knotted-carrier + closed threaded-vortex substrate. Stability, thread focusing, pressure deficit and gravity-profile claims are deliberately independent.

## v0.2.1 fixes

1. **Zero-circulation ghost threads** remain in anonymous geometry but are excluded from physical contact and CFL gates.
2. **Free-space pressure-Poisson** replaces the periodic mean-subtracted FFT as the primary gravity test. No source mean is removed and no `k=0` mode is discarded.
3. The pressure source now reports induced **monopole, dipole and quadrupole** moments. A Newton-like `-1/r` tail cannot pass without a non-negligible, convergent positive induced source monopole.
4. The pressure source box is large enough to include the complete closed return legs of the substrate threads.
5. The triple-gear phase clock is geometric and marker-independent: toroidal/poloidal carrier phase plus central-helix phase after global rigid alignment.
6. Passive zero-circulation threads are also used as **tracers** for a dynamic thread-focusing diagnostic.
7. Fresh fixed-condition stability confirmation is separated from the discovery scan.
8. A fixed-per-thread campaign varies `N_threads` without compensating total circulation.
9. Discovery beta range is extended to `|beta| <= 3`.

## Coupling

Fixed-total bundle:

```text
beta = N_threads * Gamma_thread / Gamma_core
Gamma_thread = beta * Gamma_core / N_threads
```

Fixed-per-thread density scans use:

```text
Gamma_thread = beta_per_thread * Gamma_core
Gamma_bundle_total = N_threads * Gamma_thread
```

## Carrier strata

- analytic `T(2,3)`, `T(2,5)`, `T(2,7)`, `T(2,9)`;
- source-qualified Fremlin twist carriers `4_1`, `5_2`, `6_1`, `7_2` with a geometrically searched threading axis;
- analytic `T(3,3)` triple-gear proxy: three individually unknotted linked components sharing a central passage.

The default strict preregistration requires `d_min/a > 2.5`. `TWIST_6_1` is excluded under the standard threaded construction when it fails this gate.

## Gravity gate

The induced source is

\[
S_\delta=-\rho\,\partial_i v_j\partial_jv_i\big|_{A-B},
\]

and free-space pressure is evaluated from

\[
p(\mathbf x)=-\frac{1}{4\pi}\int\frac{S(\mathbf x')}{|\mathbf x-\mathbf x'|}\,d^3x'.
\]

The blind runner fits the anonymous pair-difference profile to

\[
p_A-p_B=A+\frac{B}{r^\nu}
\]

without a gravity target. Reveal may call the candidate gravity closure surviving only if **all** are satisfied:

- carrier-clustered central pressure deficit;
- positive, non-negligible induced source monopole (correct sign for `delta p ~ -Q/(4 pi r)`);
- monopole convergence across the preregistered box/grid ladder;
- freely fitted exponent consistent with `nu=1` after reveal;
- exponent convergence across the ladder.

A pressure deficit alone never closes gravity.

## Main Windows runs

```cmd
run_all.cmd
run_all_extended.cmd
run_all_pressure_law.cmd
run_all_far_field.cmd
run_all_confirmatory_stability.cmd
run_all_thread_focusing.cmd
run_all_similarity.cmd
run_all_triple_gear.cmd
run_all_fixed_per_thread.cmd
run_all_stability_islands.cmd
```

`run_all_full.cmd` runs the confirmatory core. The two largest exploratory scans (`fixed_per_thread`, `stability_islands`) remain optional.

## Important outputs

- `REVEAL_SUMMARY.json`
- `CONCLUSIONS.md`
- `revealed_pairs.csv`
- `pressure_law.csv`
- `stability_islands_discovery.csv`
- `triple_gear_phase_lock.csv`

Every blind result tree, public anonymous catalog, code tree and config are SHA-256 sealed before reveal.
