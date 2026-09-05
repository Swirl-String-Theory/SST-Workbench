# Prior SST conclusions integrated into v0.2.2

This release deliberately incorporates methodological conclusions from earlier SST workbenches rather than treating the Planck gate in isolation.

1. **Trust layering / fail closed.** File labels are hypotheses, not topology certificates. The pipeline records source SHA-256 and canonical geometry SHA-256. Physical claims may be downgraded when topology is not independently certified.
2. **Relaxed geometry is not dynamical equilibrium.** Every carrier is checked for a best rigid relative equilibrium via
   \(\mathbf F\approx\mathbf U+\boldsymbol\Omega\times\mathbf X\) and \(\epsilon_{RE}\).
3. **Intrinsic modes before mechanisms.** The action frequency is discovered with a POD/SVD basis learned only on a discovery interval and frozen for holdout scoring. No Q/H/P coordinate is preselected.
4. **Matched +/- perturbations.** Odd response is extracted from anonymous \(+\epsilon/-\epsilon\) arms to suppress even/background drift.
5. **Measured recurrence before delay/feedback claims.** A recurrent mode is a prerequisite. A measured-delay mechanism belongs downstream and cannot create a mode retroactively.
6. **No false Floquet language.** A frozen spectrum is not Floquet. True Floquet monodromy is scientifically locked unless a relative-periodic orbit closes.
7. **Numerical certification first.** RK4, \(\Delta t\propto\Delta s^2\), dynamic subcycling, fixed final physical time, scheduled arclength redistribution, and separate resolution convergence are required before stronger claims.
8. **Multi-component geometry.** Links remain multiple closed components; components are never flattened with artificial connector segments.
9. **Action quantization is stronger than discrete modes.** The package contains a classical-continuity null. If modal action scales smoothly with excitation amplitude, discrete eigenfrequencies do not count as Planck-like quantization.
10. **Anti-circularity.** v0.2.2 strengthens the previous rule: the pre-reveal Universal Action branch uses no canonical SST constant and no SI scale at all. It is normalized only by \(L_{\rm hat}=1\) and \(\Gamma_{\rm hat}=1\).

11. **Focused carriers retained from the intrinsic-modal campaign.** Convenience presets are included for `knot_6.3` discovery, `link_9.2.20` comparison, `link_4.2.1` anti-restoring control, and trefoil `3_1` runs. These are search priorities, not privileged truths.


## v0.2.2 anti-circularity conclusion

The Universal Action discovery must be fully dimensionless and must not use any canonical SST constant or SI scale before reveal. The legacy mapping `rho_core`, `Gamma=2*pi*r_c*v`, `L=r_c` is retained only as a reveal-only contaminated normalization negative control.
