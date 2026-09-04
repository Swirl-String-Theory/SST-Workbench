#!/usr/bin/env python3
# =============================================================================
#  fs_trefoil_resolution_test.py  -  the decisive bounded experiment.
#
#  The v3/v4 toposafe runs froze (status=TOPOLOGY_LEAK): at N=128 the knotted
#  Hopf charge is not lattice-protected, so the relaxer refuses to move. The
#  axial leak fell 59->71->98% at N=40->56->72, i.e. resolution is the lever.
#  Question: does the TREFOIL hold Q=7 during GENUINE (non-toposafe) relaxation
#  once the grid is fine enough? Run plain fixed-E2 (no freeze) at rising N and
#  watch the natural retention. If it climbs toward >90% by N~192, the method
#  works for the trefoil and we have a real relax-confirmed Q_H=7 anchor.
#  If it stays ~60-70%, the lattice approach is fundamentally too coarse and the
#  taxonomy test is method-bound (record honestly; consider topology-preserving
#  discretisation as a separate research item).
#
#  Only the trefoil: higher torus knots can't even be SEEDED at N<=256 (strand
#  resolution), so they are out of scope for this test.
# =============================================================================
import torch
from fs_relax_xpu import (get_device, build_mn, torus_knot_curve, knot_seed,
                          relax_fixedE2, hopf_charge, energy)

def meter_efficiency(N, box, device, charges=((1, 1), (2, 1), (1, 2))):
    a = 1.6
    return sum(abs(hopf_charge(*build_mn(N, box, a, m, nn, device))) / (m*nn)
               for (m, nn) in charges) / len(charges)

if __name__ == "__main__":
    dev = get_device()
    box = 10.0
    print(f"[trefoil resolution test] device={dev}  (plain fixed-E2, NO toposafe freeze)\n")
    print(f"{'N':>4}  {'eff':>5}  {'seed Q_H':>8}  {'relaxed Q_H':>11}  {'retained':>8}  {'E2':>7} {'E4_0->E4'}")
    for N in [128, 160, 192]:
        eff = meter_efficiency(N, box, dev)
        M = max(1024, 8 * N)
        curve = torus_knot_curve(2, 3, M=M, scale=box * 0.30, device=dev)
        nf, dx = knot_seed(curve, N, box, R_tube=box / 6.0, framing_twists=7, device=dev)
        q0 = hopf_charge(nf, dx) / eff
        with torch.no_grad(): _, _, E4_0 = energy(nf, dx)
        # PLAIN relaxer: we WANT to see the natural leak, not a frozen seed.
        nf = relax_fixedE2(nf, dx, steps=300, delta=0.01, report=150)
        q1 = hopf_charge(nf, dx) / eff
        with torch.no_grad(): _, E2, E4 = energy(nf, dx)
        ret = 100 * q1 / q0 if q0 else 0
        print(f"{N:>4}  {eff:5.3f}  {q0:+8.2f}  {q1:+11.2f}  {ret:7.0f}%  "
              f"{float(E2)*dx**3:7.0f} {float(E4_0)*dx**3:.0f}->{float(E4)*dx**3:.0f}")
    print("\nRead: retention rising toward >90% by N=192  => trefoil Q_H=7 is relax-confirmable;")
    print("stuck near 60-70%  => lattice too coarse for the knotted core (method-bound).")
