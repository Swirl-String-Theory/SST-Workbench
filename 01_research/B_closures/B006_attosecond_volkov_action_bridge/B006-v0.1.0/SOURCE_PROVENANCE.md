# Source provenance

## Source-supported orthodox layer

Gao et al. (2026) use an SFA/Volkov ionization amplitude for attosecond streaking and reconstruct broadband XUV/IR fields from angle-resolved helium photoelectron data. Their experiment demonstrates 18 ± 2 as isolated pulses, 50–320 eV bandwidth, angle-resolved VMI streaking, and explicit attochirp compensation.

The exact notation here is deliberately recast as a generic complex kernel \(K_0\) so the SST bridge does not modify the orthodox photoionization model internally.

## New derivation in this package

The following are bridge constructions, not claims made by Gao et al.:

1. \(\Phi_V\mapsto\Phi_V+\delta S/\hbar\).
2. Target-blind specific-action form \(\delta\phi=\delta s/(\hbar/m)\).
3. First-order \(\delta I=2\operatorname{Re}(M_0^*\delta M)\).
4. Global-phase observability null.
5. A strict producer contract: no freely fitted SST phase field.

## Missing physics

No existing A029 output is automatically equivalent to \(\delta S\). A mapping from finite-core SST dynamics to a physical action difference must be independently derived and dimensionally qualified before this bridge can produce an SST attosecond prediction.
