# Roadmap naar een sterkere falsificatie

## v0.2 — Contact certification

- importeer Ridgerunner strutlists en residual sidecars;
- continue segment–segment DCSD-solver in plaats van sampled reach;
- expliciete kink/contact complementarity multipliers;
- D3-symmetry alignment en test van de thesis-seed op een \(\pi\)-rotatieas;
- branch-swap detector en orbit continuation over resolutie.

## v0.3 — Core-profile independence

- minstens twee onafhankelijke regularisaties, bijvoorbeeld Rosenhead-type en een
glad Gaussian/Lamb–Oseen-profiel;
- core-profile holdout: thresholds worden vooraf op de ringbenchmark vastgelegd;
- sweep in \(a/\Delta\), quadrature order en segment local-band;
- extrapolatie naar een verklaard continuum/core-profile error budget.

## v0.4 — Resolved finite-core hydrodynamics

- tube mesh rond dezelfde authoritative centerline;
- divergence-free vorticiteitsprofiel in de tube;
- 3D Euler/BEM/spectral velocity en pressure reconstruction;
- onafhankelijke traction-integratie op de core boundary;
- vergelijking met de geometrische contactkracht zonder globale lokale tuning.

## v0.5 — Blind cross-knot controls

- trefoil als vooraf geregistreerde target;
- \(0_1,4_1,5_1,5_2\) en geometrisch geperturbeerde trefoils als holdouts;
- geen thresholdwijziging na inzage in targetresultaten;
- family-wise false-positive control voor periodieke contactorbits;
- reproduceerbaar evidence archive met inputhashes en softwareversies.

## Beslissende falsificatie

De route wordt verworpen wanneer één van de volgende structureel blijft gelden onder
verfijning:

\[
\begin{aligned}
&\text{geen twee continue inverse contacttakken},\\
&\text{geen gepaarde primitieve 9-orbit},\\
&\text{Carlen-compatibiliteit convergeert niet},\\
&\text{Biot--Savart-vorm is geen relative equilibrium},\\
&\frac{\delta H_a}{\delta\mathbf X}\not\parallel-\kappa\mathbf n,\\
&\text{de uitkomst verdwijnt bij core-profile- of nonlocal-holdout}.
\end{aligned}
\]
