# E010-v0.3.5 — Ruban Torus Dynamics Family (DEVELOPMENT)

This is an **additive, non-destructive research subfamily** of E010 PKLSA (Parametric Knot/Link Seed Atlas). The original v0.3.1 production atlas, v0.3.3 code and v0.3.4 *42-topology multiseed view* are **read only**. This version does **not** confer production/PASS status on any new seed.

## Scientific question

Does the value of the toroidal aspect ratio that maximizes an accurately computed geometric compactness functional (e.g. diameter-normalized ropelength `L/(2 reach)`) coincide with the aspect-ratio intervals that maximize survival time of finite-core induction dynamics? **Do not assume these optima coincide.** A torus `r0` is not a vortex core radius or thickness.

Ruban (2018) found narrow **quasi-stability**, not universal or eternal stationary solutions, for some tori of quantum filaments evolved with regularized Biot–Savart induction and local induction. The effect depends on the shape, `B0=r0/R0`, and `Lambda=ln(R0/xi)`. This subfamily reproduces the *initial geometry* only and registers an unexecuted scan grid. It does not simulate survival, certify topology from a numerical polygon, or numerically optimize ropelength.

## Geometry (Ruban 2018, eqs. 1–3, n=1)

Let `beta` run over `[0,2*pi)`, `p,q` be coprime integers >1, and `theta=q*beta-theta0`. Then:

```
R(beta) = R0 * [1 + B0*sin(theta)]
X(beta) = R(beta)*cos(p*beta)
Y(beta) = R(beta)*sin(p*beta)
Z(beta) = R0*B0*cos(theta)
B0 = r0/R0
```

The pilot uses `R0=1` and exports **dimensionless** `.xyz` coordinates with N=512 periodic vertices, no duplicate endpoint. Each baseline also has an **explicitly dependent** Ruban-inspired symmetry-broken child (`x*1.01`, `y/1.01`, and a small even-q axial modulation). These perturbations are NOT independent second source providers and are NOT exact reproductions of Ruban figure initial conditions; their sampled topology remains unverified until checked. For `0<B0<1` the standard torus embedding is nonsingular; when `gcd(p,q)=1` the continuous curve is a single closed, non-self-intersecting torus knot. This does not certify its polygonal approximations at arbitrary sampling.

## Source-derived candidate/control groups

- Reported windows: `T(2,3)`, `T(3,2)`, `T(2,5)`, `T(2,7)`, `T(3,4)` (Figures 1–2).
- Weaker/unclear evidence for clear windows in the paper text: `T(3,5)`, `T(3,7)`; they remain exploratory.
- **Negative controls within the published scanned regimes**: `T(4,3)`, `T(4,5)`, `T(5,2)`, `T(5,3)`, `T(5,4)` (Figures 3–4).

`T(3,4)` and `T(4,3)` belong to the same **topological** knot type but are not the same **geometric embedding**. `T(2,3)` and `T(3,2)` are likewise trefoil embeddings. A topological name may therefore group dynamically inequivalent initial data.

**Caution:** The `B0` grid is an investigation domain around the plotted ranges; it is **not a numerical digitization or a claim that all listed B0 values lie inside Ruban stability windows**.

## Install / run (Windows)

Unzip the containing release ZIP into `C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\`. You will get a new sibling `E010-v0.3.5` next to `E010-v0.3.3`.

```bat
cd /d C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.5
python -m unittest discover -s tests -v
python build_ruban_family.py --dry-run
python build_ruban_family.py --mode pilot --archive --base-view "..\E010-v0.3.3\E010_PKLSA_Multiseed_View_v0.3.4-outputs.zip"
```

Replace `--base-view` with the actual local location of the v0.3.4 ZIP (or expanded output directory); **omit `--base-view` if that file is not present**. The baseline reference is optional and is never modified. The default output is created at `../E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs/`. To avoid overwriting old scientific output, the script **refuses to write to an existing directory**.

The code only needs `numpy` and Python 3.10+. `--mode fine` generates a dense `B0=0.08..0.22` shape grid (step 0.0025), **not** a dynamics run.

Output contains `seeds/T_p_q/*.xyz`, `seeds_perturbed/T_p_q/*.xyz`, `FAMILY_INDEX.json`, `DYNAMICS_PENDING.json`, `GEOMETRY_VS_SURVIVAL.csv`, `BUILD_SUMMARY.json`, `MANIFEST_SHA256.txt`, and automatically a matching ZIP + `.sha256` when `--archive` is passed.

## Acceptance / research gates

**G0 — Registration and provenance:** two variants of one analytic family are *not* two independent source providers. Keep SHA-256, p, q, aspect ratio, source ID and embedding ID separate. All these seeds have `qualified_for_active_atlas=false` until explicit promotion through normal E010 source contracts. Historical 42 remains immutable.

**G1 — Geometry and topology:** analytic closure and gcd condition, finite coordinates, positive torus radius, independent polygon convergence checks, component count, external knot table cross-check. Distinguish the continuous analytic knot from discrete polygonal approximations.

**G2 — Compactness:** compute `L/(2 reach)` from a *validated* thickness estimate, not `L/(2r0)`, and independently compare against existing ideal references for that topology at common conventions. The pilot computes only length and chord-quality diagnostics. Ideal optimization and geometric qualification are pending.

**G3 — Dynamics:** simulate the **same geometry** using a precisely documented finite-core regularized Biot–Savart plus local-induction operator. Calibrate `xi`, `delta`, `Lambda0`, `Gamma` consistently; don't equate SST `r_c` to Ruban `xi` without a separate physical identification. Test at common physical time, with spatial/temporal convergence and validated vortex ring benchmark. A run cannot be marked PASS from its initial shape or a stationary-looking visualization.

**G4 — Survival / relative equilibrium:** measure deformation after factoring out translation and rotation; detect resonances, geometry degeneration, nonlocal self-approach and reconnection criterion. Perturb initial conditions, include matched negative controls, and plot the **lifetime measured by the verified dynamical solver** against `B0,Lambda`. A persistent topology alone is not proof of an attractor or force restoring stability.

**G5 — Comparison:** compare `argmin_B0 Rop(B0)` to `argmax_B0 T_survival(B0,Lambda)` **for the same topology, same core convention**, including uncertainty and multimodal or censored lifetimes. Never replace missing results with literature labels.

Status: all geometric initial conditions `CONSTRUCTED`; G2–G5 scientific findings `NOT_RUN/UNASSESSED`.

## References

1. V. P. Ruban, *Long-lived quantum vortex knots*, arXiv:1801.04822, https://arxiv.org/abs/1801.04822 (2018).
2. V. P. Ruban, *Quasi-stable configurations of torus vortex knots and links*, arXiv:1806.10783, https://arxiv.org/abs/1806.10783 (2018). Figures 1–4, equations (1)–(7).
3. R. L. Ricca, D. C. Samuels, C. F. Barenghi, *Evolution of vortex knots*, J. Fluid Mech. **391** (1999), https://doi.org/10.1017/S0022112099005224. Background: Biot–Savart evolution can extend a torus-knot lifetime compared to local induction alone.

This paper-derived family does not claim that an inviscid Euler vortex tube, Ruban's quantum-vortex filament, and SST mechanical filaments are physically equivalent.

## Registration boundary

`configs/family_registry_overlay.json` supplies a **research-only registry record** pointing to the separately generated `FAMILY_INDEX.json`. The official 42-topology `ACTIVE_TOPOLOGY_SET.json` is not rewritten, and no new source counts toward the multi-seed admission gate merely by appearing in the Ruban family's parameter grid. Integration into an E010 production loader requires a deliberate later promotion and renewed provenance, topology, and geometry gates.
