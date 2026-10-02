# Route A derivation/falsification attempt: three pre-registered families

## Executive verdict

The parallel attempt does **not** derive Route A. It separates three facts:

1. Crofton/stereology supplies the geometric factor

   \[
   \langle N_{\rm pierce}\rangle/A = \frac12\Lambda_L.
   \]

2. Ordinary Onsager/KT/core-packing physics supplies no natural path to
   \(\Lambda_L\sim 10^{69}\,\mathrm{m^{-2}}\); it is short by roughly 40 orders.

3. Strict Weyl/torsion phase-space counting can generate large amplification, but still misses the target by orders unless one reintroduces the old fitted seed coefficient.

Therefore the defensible status remains:

\[
\text{[RESEARCH-TRACK] [PREREGISTERED] [FALSIFICATION-HARNESS] [NOT DERIVED]}.
\]

## Target

\[
(\sigma\Lambda)_{\rm target}=\frac1{2L_p^2}
=1.914036558578934e+69\,\mathrm{m^{-2}}.
\]

If \(\sigma_{\rm pierce}=1\), the target line spacing is

\[
d_\Lambda=(\sigma\Lambda)_{\rm target}^{-1/2}
=2.285729775093407e-35\,\mathrm{m}.
\]

## Family 1: Onsager/KT-like vortex gas

A plain vortex gas with core cutoff \(a=r_c\) gives at most

\[
\sigma\Lambda\sim r_c^{-2}
\]

or with disk packing

\[
\sigma\Lambda\sim (\pi r_c^2)^{-1}.
\]

The required single-density multiplier is

\[
y_{\rm req}=(\sigma\Lambda)_{\rm target}r_c^2
=3.799739519043e+39,
\]

and the pair-fugacity analogue is

\[
y_{\rm pair,req}=\sqrt{(\sigma\Lambda)_{\rm target}r_c^2}
=6.164202721393e+19.
\]

These are not acceptable ordinary BKT fugacities. The KT-like route is falsified unless SST supplies an additional non-thermal channel degeneracy.

## Family 2: Crofton/stereology

The geometric lemma is solid:

\[
\left\langle |\cos\theta|\right\rangle_{S^2}=\frac12.
\]

The Monte Carlo check gives

\[
\left\langle |\cos\theta|\right\rangle_{\rm MC}
=0.499892882.
\]

This validates the projection factor in

\[
\langle N_{\rm pierce}\rangle=\frac12\Lambda_L A.
\]

But stereology does not derive \(\Lambda_L\). It only converts line density into expected piercings.

## Family 3: torsion-channel phase-space counting

A strict 3D Weyl-style transverse channel count with \(g_T=2\) gives

\[
\sigma\Lambda_{\rm Weyl3}
=r_c^{-2}\frac{\rho_{\rm core}}{\rho_f}\frac2{6\pi^2}\left(\frac c{\vchar}\right)^3,
\]

which is far too small. A paired version gives

\[
\sigma\Lambda_{\rm WeylPair}
=r_c^{-2}\frac{\rho_{\rm core}}{\rho_f}\left(\frac2{6\pi^2}\right)^2\left(\frac c{\vchar}\right)^6,
\]

but still misses the target by about a factor

\[
1.413100e+03.
\]

The old seed coefficient requires

\[
K_{\rm req}=1.611873086584e+00,
\]

close to \(16/\pi^2\), but that remains a fitted/scan-motivated kernel unless derived independently.

## Conclusion

The next admissible step is not coefficient search. It is a real lemma for one of:

\[
\Lambda_L,\quad \sigma_{\rm pierce},\quad \text{or a non-fitted torsion-channel degeneracy}.
\]
