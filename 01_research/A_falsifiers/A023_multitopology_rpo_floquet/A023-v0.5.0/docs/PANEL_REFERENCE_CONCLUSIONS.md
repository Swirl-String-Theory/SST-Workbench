# v0.4.0 BASIC Reference Conclusions

Reference run: the exact 17 bundled canonical inputs, Python reference backend, `configs/panel_basic.json`. These results are a reproducibility snapshot, not hard-coded decisions; rerunning the package recomputes them.

## Main comparative observations

1. **Source-independent `5_2` signal.** Both Fremlin and KnotPlot/RidgeRunner `5_2` fail the generic linear-growth gate, with normalized growth approximately 0.124 and 0.140 respectively. Both remain bounded over the short ringdown. This is the clearest same-topology agreement near the preregistered `P2=0.12` boundary.

2. **`4_1` agreement.** Both `4_1` representations pass the generic linear-growth and short-ringdown gates, with normalized growth approximately 0.049 and 0.047.

3. **Trefoil generic basis is quiet.** Fremlin `3_1`, KnotPlot/RidgeRunner `3_1`, and `T(2,3)` all pass `P2` in the generic low-order Frenet/Fourier basis. This does **not** contradict v0.3.0, whose trefoil-specific lobe basis detected growing modes outside this generic BASIC subspace.

4. **Hopf-like link versus unlink controls.** `link_2.2.1` has high-resolution Gauss linking `Lk = +1.00007`, passes the generic `P2` and `P5` gates, and has positive nearest mutual separation rate. In contrast, `link_0.2.1` and `link_0.3.1` have pairwise `Lk ≈ 0` and fail `P2` while remaining short-ringdown bounded. This is an interesting candidate topology/mutual-induction effect, but it requires EXTENDED and matched-geometry controls before causal interpretation.

5. **Three-component links.** `link_6.3.1` and `link_6.3.3` have pairwise linking magnitudes near one and both fail `P2`; `link_6.3.1` additionally fails the short-ringdown gate, while `link_6.3.3` remains bounded in BASIC.

6. **`T(6,9)` is a three-component torus link.** High-resolution pairwise Gauss linking is approximately `-6.0035`, `-6.0033`, `-6.0035`, consistent with magnitude six. It fails both generic linear-growth and short-ringdown gates in BASIC.

7. **No RPO in BASIC.** None of the 17 inputs produced a valid excursion-and-return RPO under the preregistered phase scan; therefore no Floquet stability claim is made for any input.

8. **No reconnection/topology drift.** Every multi-component reference run preserved pairwise Gauss linking to well inside the BASIC tolerance during short ringdown.

## Important caution on the unknot

Both `0_1` representations are exact/nearly exact translating-ring geometries with extremely small intrinsic shape-velocity ratios, yet the selected generic perturbation Jacobian has a real ± pair and therefore fails `P2`. This should be interpreted as a reduced-mode stability signal of the very thick regularized ring (`a \approx 0.9` of its maximum tube radius), not as evidence that an ideal circular Euler vortex ring radially collapses. The separate circle radial-null remains a distinct statement.

See `reference_results/v0.4.0_panel_basic/` for all gate evidence.
