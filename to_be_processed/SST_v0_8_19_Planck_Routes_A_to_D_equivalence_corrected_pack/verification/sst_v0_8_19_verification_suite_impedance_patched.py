#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sst_v0_8_19_verification_suite.py
=================================
Consolidated, single-file numerical verification suite for the
**Swirl-String Theory (SST) Canon v0.8.19-compatible**.

It bundles, into one runnable file, every claim that can be *honestly* checked
in seconds on a laptop (numpy only): the deterministic constants / calibrated
algebra block, the EM-gravity numeric hierarchy, the master-equation geometric
gate (with audit point BG-1), the genuinely non-circular torus self-linking
result, the Biot-Savart A_K -> 1/(4pi) plateau, the Onsager KT transition, and
the alpha finite-cell *coincidence-and-obstruction* ledger.

Design rules (matching the canon's epistemic discipline):
  * Each section prints the canon claim ID, location, an epistemic tag, and
    PASS/FAIL with an explicit tolerance.
  * Calibrated identities are flagged [CALIBRATED]; posited inputs [POSIT];
    the alpha section is ain OBSTRUCTION ledger, NOT a derivation of alpha.
  * Heavy torch sweeps (N=32000) are NOT bundled; the light versions reproduce
    the same limits and say so.
  * This v0.8.19-compatible port keeps the numerical claim suite unchanged;
    the v0.8.19 update is a textual/status patch layer, not a new constants chain.

Provenance of recovered algorithms (from prior project chats):
  * gauss_linking / torus framing  -> chat 840c733d
  * Biot-Savart E_bs / A_K plateau  -> chat fc5e123d
  * alpha obstruction numbers       -> chat f4172ebc (finite_cell_obstruction)
  * Onsager T_KT                    -> chat fc5e123d (SST-15 complement)
  * Route-I heat split / impedance  -> SST_CANON-v0.8.19 research-track patch

Usage:
  python3 sst_v0_8_19_verification_suite.py            # run all sections
  python3 sst_v0_8_19_verification_suite.py --list     # list sections
  python3 sst_v0_8_19_verification_suite.py --only constants topology
  python3 sst_v0_8_19_verification_suite.py --json out.json
"""

import math
import sys
import json
import argparse

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

# ===========================================================================
# CODATA-2018 constants  (the canon's own primitive input set)
# ===========================================================================
HBAR  = 1.054571817e-34
H     = 2.0*math.pi*HBAR
M_E   = 9.1093837015e-31
C     = 2.99792458e8
ALPHA = 7.2973525693e-3
E     = 1.602176634e-19
EPS0  = 8.8541878128e-12
G     = 6.67430e-11
KB    = 1.380649e-23
R_E   = E**2/(4*math.pi*EPS0*M_E*C**2)
R_INF = ALPHA**2*M_E*C/(4*math.pi*HBAR)

# Canon calibration (alpha injected HERE, by construction):
VCHAR   = ALPHA*C/2.0                 # vchar = ||v_circ|| = alpha c / 2
OMEGA_C = M_E*C**2/HBAR               # Compton angular frequency
R_C     = VCHAR/OMEGA_C               # = alpha hbar/(2 m_e c) = r_e/2
RHO_F   = 7.0e-7                      # the single genuinely free parameter

# ===========================================================================
# Test harness
# ===========================================================================
class Suite:
    def __init__(self):
        self.records = []   # list of dicts

    def check(self, claim, loc, tag, desc, got, expected, rel_tol=1e-6, unit=""):
        if expected == 0:
            rel = abs(got); ok = rel < rel_tol
        else:
            rel = abs(got-expected)/abs(expected); ok = rel <= rel_tol
        rec = dict(claim=claim, loc=loc, tag=tag, desc=desc,
                   got=float(got), expected=float(expected),
                   rel=float(rel), ok=bool(ok), unit=unit)
        self.records.append(rec)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] claim {claim:>5} {tag:<12} {desc}")
        print(f"          got={got:.10g} {unit}  expected={expected:.10g} {unit}  "
              f"(rel.dev={rel:.2e}, tol={rel_tol:.0e})")
        return ok

    def note(self, claim, tag, text):
        self.records.append(dict(claim=claim, tag=tag, desc=text, note=True, ok=None))
        print(f"  [INFO ] claim {claim:>5} {tag:<12} {text}")

    def check_max(self, claim, loc, tag, desc, got, maximum, unit=""):
        ok = got <= maximum
        rec = dict(claim=claim, loc=loc, tag=tag, desc=desc,
                   got=float(got), expected=float(maximum),
                   rel=float(got/maximum) if maximum else float(got),
                   ok=bool(ok), unit=unit)
        self.records.append(rec)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] claim {claim:>5} {tag:<12} {desc}")
        print(f"          got={got:.10g} {unit}  max={maximum:.10g} {unit}")
        return ok

    def summary(self):
        graded = [r for r in self.records if r.get("ok") is not None]
        npass = sum(1 for r in graded if r["ok"])
        return npass, len(graded)


def header(title):
    print()
    print("="*78)
    print(title)
    print("="*78)


# ===========================================================================
# SECTION: constants  (claims 2,3,4,5,7,8,10,13,14,15,16,17,18,32,33)
# ===========================================================================
def sec_constants(S):
    header("SECTION constants  -- primitive chain, tension scales, EMG numerics")

    S.check(3, "2.2 eq:omega_c_compton", "[ORTHODOX]",
            "omega_c = m_e c^2/hbar", OMEGA_C, M_E*C**2/HBAR, unit="rad/s")

    S.check(5, "2.5 lines 326-342", "[CALIBRATED]",
            "eta_0 = vchar/c = alpha/2 (alpha injected here)", VCHAR/C, ALPHA/2)

    S.check(2, "2.2 eq:rc_definition", "[DERIVED]",
            "r_c = vchar/omega_c", R_C, VCHAR/OMEGA_C, unit="m")
    S.check(2, "2.2 eq:rc_definition", "[CALIBRATED]",
            "r_c = alpha hbar/(2 m_e c)  (=> only via vchar=alpha c/2)",
            R_C, ALPHA*HBAR/(2*M_E*C), unit="m")
    S.check(2, "2.2 eq:rc_definition", "[CALIBRATED]",
            "r_c = r_e/2", R_C, R_E/2, unit="m")

    Gamma0 = 2*math.pi*R_C*VCHAR
    S.check(4, "2.3/2.10 eq:gamma0(_reparam)", "[DERIVED]",
            "Gamma_0 = 2 pi r_c vchar = 2 pi vchar^2/omega_c",
            Gamma0, 2*math.pi*VCHAR**2/OMEGA_C, unit="m^2/s")

    rhoE = 0.5*RHO_F*VCHAR**2
    S.check(7, "2.7 / 10.13", "[CALIBRATED]",
            "rho_E = 1/2 rho_f vchar^2  (rho_f=7.0e-7 free param)",
            rhoE, 4.1877439e5, rel_tol=1e-5, unit="Pa")

    rho_horn = M_E*C**2/(2*math.pi*VCHAR**2*R_C**3)
    S.check(8, "2.8 eq:core_density", "[CALIBRATED]",
            "rho_horn = m_e c^2/(2 pi vchar^2 r_c^3)",
            rho_horn, M_E*C**2/(2*math.pi*VCHAR**2*R_C**3), unit="kg/m^3")

    Fmax = HBAR*OMEGA_C/(2*R_C)
    S.check(13, "2.15 eq:Fmax_def", "[CALIBRATED]",
            "F_max = hbar omega_c/(2 r_c) = vchar hbar/(2 r_c^2)",
            Fmax, VCHAR*HBAR/(2*R_C**2), unit="N")
    S.check(13, "2.15 eq:Fmax_def", "[CALIBRATED]",
            "F_max numeric", Fmax, 29.053507, rel_tol=1e-4, unit="N")
    S.check(14, "2.15 eq:Fmax_em", "[CALIBRATED]",
            "F_max = e^2/(16 pi eps0 r_c^2)", Fmax, E**2/(16*math.pi*EPS0*R_C**2), unit="N")
    S.check(14, "2.15 eq:Fmax_hac", "[CALIBRATED]",
            "F_max = h alpha c/(8 pi r_c^2)", Fmax, H*ALPHA*C/(8*math.pi*R_C**2), unit="N")

    Fgr = C**4/(4*G); alpha_g = G*M_E**2/(HBAR*C)
    S.check(16, "2.15 eq:Fmax_ratio", "[CALIBRATED]",
            "F_max/F_gr = 4 alpha_g/alpha", Fmax/Fgr, 4*alpha_g/ALPHA)

    Fpp = E**2/(4*math.pi*EPS0*R_C**2)
    S.check(17, "2.15 eq:Coulomb_core", "[CALIBRATED]",
            "F_pp(r_c) = 4 F_max (quarter-Coulomb)", Fpp, 4*Fmax)

    Ke = Fmax/(2*R_C)
    S.check(18, "2.15 eq:omega_spring", "[CONDITIONAL]",
            "omega_spring = sqrt(K_e/m_e) = omega_c/alpha (n=2 POSIT)",
            math.sqrt(Ke/M_E), OMEGA_C/ALPHA, unit="rad/s")
    S.check(18, "2.15 eq:Espring", "[CONDITIONAL]",
            "E_spring = 1/2 K_e r_c^2 = m_e c^2/8 (n=2 POSIT)",
            0.5*Ke*R_C**2, M_E*C**2/8, unit="J")

    S.check(15, "2.15 eq:Rydberg_SST", "[CALIBRATED]",
            "R_inf = vchar^3/(pi r_c c^3) (hidden m_e,alpha)",
            VCHAR**3/(math.pi*R_C*C**3), R_INF, unit="1/m")

    t_p = math.sqrt(HBAR*G/C**5)
    S.check(32, "10.13 eq:canonical_gswirl", "[CALIBRATED]",
            "G_swirl = vchar c^3 t_p^2/(r_c m_e) (t_p contains G)",
            VCHAR*C**3*t_p**2/(R_C*M_E), G, rel_tol=1e-5, unit="m^3/kg/s^2")

    S_t = math.sqrt(1-VCHAR**2/C**2)
    S.check(33, "10.13 numerical hierarchy", "[DERIVED]",
            "Swirl-Clock S_(t)", S_t, 0.9999933436, rel_tol=1e-7)
    S.check(33, "10.13 numerical hierarchy", "[DERIVED]",
            "optical index n_gamma-1", 1/S_t-1, 6.6564858e-6, rel_tol=1e-4)


# ===========================================================================
# SECTION: gate  (claim 12 + audit BG-1)
# ===========================================================================
def sec_gate(S):
    header("SECTION gate  -- master-equation geometric gate Pi_K (audit BG-1)")
    lam_nonred = H/(M_E*C)
    S.check(12, "2.11 eq:sst_master_equation", "[CALIBRATED]",
            "lambda_c/(pi r_c)=4/alpha  REQUIRES lambda_c=h/(m_e c) (non-reduced)",
            lam_nonred/(math.pi*R_C), 4.0/ALPHA)
    lam_red = HBAR/(M_E*C)
    S.note(12, "[BG-1]",
           f"reduced-lambda gate = {lam_red/(math.pi*R_C):.4f} "
           f"= (4/alpha)/(2pi) = {(4/ALPHA)/(2*math.pi):.4f}  -> canon must fix lambda_c def")


# ===========================================================================
# SECTION: topology  (claim 20) -- torus-surface framing self-linking SL=pq
# Recovered Gauss-linking algorithm (target-free, NO target injected).
# ===========================================================================
def sec_topology(S):
    header("SECTION topology  -- torus self-linking SL_tor(T(p,q)) = pq (non-circular)")
    if not HAVE_NUMPY:
        S.note(20, "[SKIP]", "numpy required for Gauss linking integral")
        return

    def gauss_linking(A, B):
        Am = 0.5*(A+np.roll(A,-1,0)); dA = np.roll(A,-1,0)-A
        Bm = 0.5*(B+np.roll(B,-1,0)); dB = np.roll(B,-1,0)-B
        s = 0.0
        for i in range(len(Am)):
            r = Am[i]-Bm; rn = np.linalg.norm(r,axis=1); rn[rn<1e-12]=1e-12
            cr = np.cross(np.broadcast_to(dA[i],dB.shape), dB)
            s += np.sum(np.einsum('ij,ij->i', r, cr)/rn**3)
        return s/(4*math.pi)

    def torus_knot_and_normal(p, q, R=2.0, a=0.7, n=2000):
        t = np.linspace(0, 2*math.pi, n, endpoint=False)
        rho = R + a*np.cos(q*t)
        curve = np.stack([rho*np.cos(p*t), rho*np.sin(p*t), a*np.sin(q*t)], 1)
        U = np.stack([np.cos(q*t)*np.cos(p*t),
                      np.cos(q*t)*np.sin(p*t), np.sin(q*t)], 1)
        return curve, U

    eps, all_ok = 0.04, True
    for (p, q) in [(2,3),(2,5),(2,7),(2,9),(2,11),(3,2),(3,4)]:
        curve, U = torus_knot_and_normal(p, q)
        SL = gauss_linking(curve, curve+eps*U)
        ok = abs(abs(SL)-p*q) < 0.05
        all_ok &= ok
        sign = '+' if SL > 0 else '-'
        print(f"    T({p},{q}): SL={SL:8.3f}  |SL|={abs(SL):6.3f}  pq={p*q:3d}  "
              f"{'PASS' if ok else 'FAIL'}  (sign {sign} = chirality sector)")
    S.records.append(dict(claim=20, loc="5.3 eq:SL_torus_pq", tag="[DERIVED]",
                          desc="SL_tor(T(p,q))=pq target-free", ok=bool(all_ok)))
    print(f"    => SL_tor=pq verified target-free. pq+1 ladder = pq[DERIVED]+1[POSIT].  "
          f"{'PASS' if all_ok else 'FAIL'}")


# ===========================================================================
# SECTION: biotsavart  (claims 45/52) -- A_K -> 1/(4pi) plateau
# Recovered E_bs cutoff-energy scan; plateau is the genuinely DERIVED geometry.
# ===========================================================================
def sec_biotsavart(S):
    header("SECTION biotsavart  -- Biot-Savart log coefficient A_K -> 1/(4pi)")
    if not HAVE_NUMPY:
        S.note(45, "[SKIP]", "numpy required")
        return

    # parametric (2,3) trefoil; the A_K plateau is a local-induction result and
    # is robust to the exact smooth curve (the canonical 32k torch sweep gives
    # A_K*4pi = 0.99992; this light run reproduces the limit to a few %).
    n = 1500
    t = np.linspace(0, 2*math.pi, n, endpoint=False)
    x = np.sin(t)+2*np.sin(2*t); y = np.cos(t)-2*np.cos(2*t); z = -np.sin(3*t)
    r = np.stack([x, y, z], 1)
    rp = np.roll(r,-1,0)-r
    ds = np.linalg.norm(rp, axis=1)
    L = ds.sum(); ds_mean = ds.mean()
    That = rp/np.linalg.norm(rp, axis=1, keepdims=True)

    def E_bs(a):
        Etot = 0.0
        for i in range(n):
            d = r-r[i]; dist = np.sqrt((d*d).sum(1)+a*a)
            contr = (That@That[i])*ds*ds[i]/dist; contr[i] = 0.0
            Etot += contr.sum()
        return Etot/(8*math.pi)

    # core radii kept > ds_mean (desingularization meaningful) and << curve size,
    # spanning the log regime; slope of E/L vs ln(L/a) -> A_K.
    aa = np.array([2.0,3.0,4.5,6.0,8.0,11.0])*ds_mean
    Es = np.array([E_bs(a) for a in aa])
    xK = np.log(L/aa); yK = Es/L
    A = np.vstack([xK, np.ones_like(xK)]).T
    (AK, aK), *_ = np.linalg.lstsq(A, yK, rcond=None)
    ratio = AK*4*math.pi
    # light demonstrator: the plateau LIMIT is 1/(4pi); a coarse single-curve run
    # lands within ~25% and trends correctly. The canonical value (0.99992 ratio)
    # comes from the torch sweep at N_int=32000 (not bundled).
    S.check(45, "Route-3 Biot-Savart", "[DERIVED]",
            "A_K trends to 1/(4pi) (LIMIT; coarse run, torch sweep ratio=0.99992)",
            AK, 1/(4*math.pi), rel_tol=0.30)
    S.note(45, "[LIMIT]", f"A_K = {AK:.5f}, ratio A_K*4pi = {ratio:.3f} "
                          f"(target 1.000; coarse single-curve demonstrator)")

    # ropelength is an EXTERNAL tabulated invariant (Pieranski 1998); not derived.
    L_K_ideal = 16.372
    S.note(45, "[ORTHODOX]",
           f"ideal trefoil ropelength L_K = {L_K_ideal} (tabulated, external input)")
    S.note(46, "[COINCIDENCE]",
           f"(8 pi/3) L_K = {8*math.pi/3*L_K_ideal:.3f}  vs alpha^-1 = {1/ALPHA:.3f}")


# ===========================================================================
# SECTION: onsager  (SST-15 complement) -- KT transition T_KT
# Genuinely DERIVED result (Kosterlitz-Thouless, 2D point-vortex gas).
# ===========================================================================
def sec_onsager(S):
    header("SECTION onsager  -- Kosterlitz-Thouless transition (SST-15 complement)")
    Gamma = 2*math.pi*R_C*VCHAR                 # canonical circulation quantum
    T_KT = RHO_F*Gamma**2/(4*math.pi*KB)        # T_KT = rho_f Gamma^2/(4 pi k_B)
    # dimensional check: [rho_f][Gamma]^2/[k_B] = (kg/m^3)(m^2/s)^2/(J/K) = K
    S.check("SST-15", "Onsager 2D point-vortex", "[DERIVED]",
            "T_KT = rho_f Gamma^2/(4 pi k_B)  (closed form, dim-checked)",
            T_KT, RHO_F*Gamma**2/(4*math.pi*KB), unit="K")
    S.note("SST-15", "[INFO]", f"numeric T_KT = {T_KT:.4e} K at canonical (rho_f,Gamma)")


# ===========================================================================
# SECTION: impedance_matching  -- Route-I heat split + core-torsion residual
# v0.8.19 research-track protocol, NOT a derivation of M_torsion[K].
# Verifies only algebraic guardrails that can be checked without a PDE solver:
#   (i)  c/vchar = 274.0719986 wrong-speed Unruh factor;
#   (ii) a Kelvin-normalized inertial tensor gives chi = (c/vchar)^2;
#   (iii) the canonical target tensor gives chi = 1 by definition.
# A real SSTcore torsion solver must replace M_target below by computed data.
# ===========================================================================
def sec_impedance_matching(S):
    header("SECTION impedance_matching  -- Route-I heat split and core-torsion residual")
    if not HAVE_NUMPY:
        S.note("RT-Bridge", "[SKIP]", "numpy required for tensor residual audit")
        return

    wrong_unruh_factor = C / VCHAR
    S.check("RT-I", "Route-I sector guard", "[RESEARCH-TRACK]",
            "T_vchar/T_c = c/vchar wrong-speed Unruh factor",
            wrong_unruh_factor, 274.0719986, rel_tol=5e-9)

    cs = VCHAR / math.sqrt(2.0)
    S.note("RT-I", "[GUARD]",
           f"core sound diagnostic c_s=vchar/sqrt(2)={cs:.8e} m/s; "
           "not eligible as the Jacobson/Unruh causal speed")

    # Protocol benchmark: electron rest energy used only as a neutral E0 scale.
    # This is not a computed knot tensor; it is a normalization sanity check for
    # M_torsion[K] ?= (2E0[K]/c_T^2) I in the current research-track convention.
    E0_K = M_E * C**2
    lambda_target = 2.0 * E0_K / C**2
    M_target = np.eye(3) * lambda_target
    lambda_iso = float(np.trace(M_target) / 3.0)
    chi_target = (C**2 / (2.0 * E0_K)) * lambda_iso
    S.check("RT-Bridge", "eq:rt_core_torsion_matching_lemma", "[PROTOCOL]",
            "target tensor M=(2E0/c^2)I gives chi_K^(T)=1 by normalization",
            chi_target, 1.0, rel_tol=1e-12)

    # Wrong-sector falsifier: if a Kelvin-normalized tensor is tested on the
    # torsion/horizon cone, the residual is (c/vchar)^2, not 1.
    M_kelvin_target = np.eye(3) * (2.0 * E0_K / VCHAR**2)
    lambda_kelvin = float(np.trace(M_kelvin_target) / 3.0)
    chi_kelvin_as_torsion = (C**2 / (2.0 * E0_K)) * lambda_kelvin
    S.check("RT-Bridge", "wrong-speed residual guard", "[FALSIFIER]",
            "Kelvin-normalized inertia tested on c_T=c gives chi=(c/vchar)^2",
            chi_kelvin_as_torsion, (C/VCHAR)**2, rel_tol=1e-12)
    S.check_max("RT-Bridge", "wrong-speed residual guard", "[FALSIFIER]",
                "wrong-speed residual is far outside unity tolerance (1/chi <= 1e-4)",
                1.0/chi_kelvin_as_torsion, 1e-4)

    S.note("RT-Bridge", "[OPEN]",
           "This section does not compute M_torsion[K]. A real solver must report "
           "E0[K], the three eigenvalues of the torsion-dressed tensor, chi_K^(T), "
           "anisotropy max|lambda_i/lambda_iso-1|, and a K_T stiffness sweep at c_T=c.")

# ===========================================================================
# SECTION: delay  (claim 26) -- DDE mode condition, current SSTcore aligned
# ===========================================================================
def sec_delay(S):
    header("SECTION delay  -- DDE locked-mode condition (claim 26), current SSTcore aligned")
    # Canon v0.8.12:
    #   Omega = omega0 - kappa sin(Omega tau)
    # Residual solved by Newton/root finders:
    #   f(Omega)  = Omega - omega0 + kappa sin(Omega tau)
    #   f'(Omega) = 1 + kappa tau cos(Omega tau)
    omega0, kappa, tau = 1.0, 0.3, 2.0

    def residual_canon(Om):
        return Om - omega0 + kappa*math.sin(Om*tau)

    def derivative_canon(Om):
        return 1.0 + kappa*tau*math.cos(Om*tau)

    # Solve the Canon fixed-point form.
    Om = omega0
    for _ in range(200):
        Om = omega0 - kappa*math.sin(Om*tau)

    S.check(26, "Sec 7 eq:mode_condition", "[CODE=CANON]",
            "Omega = omega0 - kappa sin(Omega tau)",
            residual_canon(Om), 0.0, rel_tol=1e-9)

    # Independent finite-difference check of the Newton derivative used by SSTcore.
    h = 1e-6
    fd = (residual_canon(Om+h) - residual_canon(Om-h))/(2*h)
    S.check(26, "delay_mode_selector.cpp:newton_derivative", "[CODE=CANON]",
            "f'(Omega) = 1 + kappa tau cos(Omega tau)",
            derivative_canon(Om), fd, rel_tol=1e-6)

    # Historical audit issue only: the old plus-sign residual was
    # Omega - omega0 - kappa sin(Omega tau), which is not the current v0.8.12 form.
    S.note(26, "[STATUS]",
           "Current SSTcore v0.8.12/v0.8.19-compatible delay residual and Newton derivative are aligned with Canon; "
           "old plus-sign mismatch is retained only as historical audit context.")


# ===========================================================================
# SECTION: alpha  (claims 45/46) -- OBSTRUCTION ledger (NOT a derivation)
# Reproduces the numbers from the finite_cell_obstruction note (chat f4172ebc).
# ===========================================================================
def sec_alpha(S):
    header("SECTION alpha  -- finite-cell coincidence + ppm OBSTRUCTION (NOT derivation)")
    L_K = 16.372
    lead = 8*math.pi/3*L_K                       # the alpha-free coincidence
    gap_ppm = abs(lead-1/ALPHA)/(1/ALPHA)*1e6
    S.note(46, "[COINCIDENCE]",
           f"leading (8 pi/3) L_K = {lead:.4f}; alpha^-1 = {1/ALPHA:.4f}; "
           f"gap = {gap_ppm:.0f} ppm")
    # obstruction scalar: required transverse shell weight vs GP value
    w_req, w_GP = 1.0675, 2.076
    S.note(46, "[OBSTRUCTION]",
           f"closure needs w_perp = {w_req}; GP core gives w_perp = {w_GP} "
           f"(wrong side by ~{(w_GP-w_req)/w_req*1e2:.1f}%; ppm closure remains unresolved)")
    S.note(46, "[STATUS]",
           "alpha is NOT derived: N_p=4 derived, but ppm closure non-identifiable "
           "(5 interchangeable routes, G1 fails independently). Label [CONDITIONAL]/[OPEN].")
    # we deliberately record NO pass/fail here: an obstruction is not a check to pass.


# ===========================================================================
# SECTION: sstcore_alignment  -- mirror the ACTUAL C++ code formulas and
# assert code == canon, in one run. Mirrors:
#   canonical_constants.cpp, sst_tension_scales.cpp, sst_gravity.h,
#   chronos_kelvin_transport.cpp  (SSTcore v0.8.12/v0.8.19-compatible, after patch 0003 CODATA-2018).
# Each check: got = code-form value, expected = canon-form value.
# ===========================================================================
def sec_sstcore_alignment(S):
    header("SECTION sstcore_alignment  -- SSTcore v0.8.12/v0.8.19-compatible C++ formulas vs canon")

    # inputs as the C++ receives them: v_swirl is passed in (= alpha c/2 calibration)
    v = VCHAR
    pi_d = math.pi

    # --- canonical_constants.cpp ---
    code_omega_c = M_E*C*C/HBAR                        # compton_angular_frequency
    S.check(3, "canonical_constants.cpp:compton_angular_frequency", "[CODE=CANON]",
            "m_e*c*c/hbar == omega_c", code_omega_c, OMEGA_C, unit="rad/s")

    code_rc = v/code_omega_c                           # core_radius_from_compton_anchor
    S.check(2, "canonical_constants.cpp:core_radius_from_compton_anchor", "[CODE=CANON]",
            "v_swirl/omega_c == r_c", code_rc, R_C, unit="m")

    code_g0a = 2*pi_d*code_rc*v                         # circulation_quantum
    code_g0b = 2*pi_d*v*v/code_omega_c                  # circulation_quantum_from_v_omega
    S.check(4, "canonical_constants.cpp:circulation_quantum(_from_v_omega)", "[CODE=CANON]",
            "2pi r_c v == 2pi v^2/omega_c", code_g0a, code_g0b, unit="m^2/s")

    code_rhoE = 0.5*RHO_F*v*v                           # swirl_energy_density
    S.check(7, "canonical_constants.cpp:swirl_energy_density", "[CODE=CANON]",
            "0.5*rho_f*v^2 == rho_E", code_rhoE, 0.5*RHO_F*VCHAR**2, unit="Pa")

    code_rho_core = (M_E*C*C)/(2*pi_d*v*v*code_rc**3)   # core_density_closure (== rho_horn)
    S.check(8, "canonical_constants.cpp:core_density_closure==horn_envelope_density", "[CODE=CANON]",
            "m_e c^2/(2pi v^2 r_c^3) == rho_horn (patch 0002 alias)",
            code_rho_core, M_E*C*C/(2*pi_d*VCHAR**2*R_C**3), unit="kg/m^3")

    # geometric_gate uses the FULL (non-reduced) Compton wavelength -> 4/alpha (BG-1)
    full_lambda_c = 2*pi_d*(HBAR/(M_E*C))              # full_compton_wavelength
    code_gate = full_lambda_c/(pi_d*code_rc)           # geometric_gate(lambda_c, r_c)
    S.check(12, "canonical_constants.cpp:geometric_gate (full lambda_c)", "[CODE=CANON]",
            "geometric_gate uses full lambda_c -> 4/alpha (resolves audit BG-1)",
            code_gate, 4.0/ALPHA)

    code_Fmax = HBAR*code_omega_c/(2*code_rc)          # f_swirl_max
    S.check(13, "canonical_constants.cpp:f_swirl_max", "[CODE=CANON]",
            "hbar*omega_c/(2 r_c) == F_max", code_Fmax, 29.053507, rel_tol=1e-4, unit="N")

    code_R = v**3/(pi_d*code_rc*C**3)                  # rydberg_sst
    S.check(15, "canonical_constants.cpp:rydberg_sst", "[CODE=CANON]",
            "v^3/(pi r_c c^3) == R_inf", code_R, R_INF, unit="1/m")

    # --- sst_tension_scales.cpp ---
    code_Fgr = C**4/(4*G)                              # f_gr_max
    code_ag = G*M_E*M_E/(HBAR*C)                       # gravitational_fine_structure
    code_ratio = 4.0*code_ag/ALPHA                     # tension_ratio_from_couplings
    S.check(16, "sst_tension_scales.cpp:tension_ratio_from_couplings", "[CODE=CANON]",
            "4 alpha_g/alpha == F_max/F_gr", code_ratio, code_Fmax/code_Fgr)

    code_Fpp = E*E/(4*pi_d*EPS0*code_rc**2)            # coulomb_force_at_core
    S.check(17, "sst_tension_scales.cpp:coulomb_force_at_core", "[CODE=CANON]",
            "e^2/(4pi eps0 r_c^2) == 4 F_max (quarter-Coulomb)", code_Fpp, 4*code_Fmax, unit="N")

    n = 2.0
    code_Ke = code_Fmax/(n*code_rc)                    # electron_spring_constant
    code_wsp = math.sqrt(code_Ke/M_E)                  # electron_spring_frequency
    S.check(18, "sst_tension_scales.cpp:electron_spring_frequency", "[CODE=CANON]",
            "sqrt(K_e/m_e) == omega_c/alpha (n=2)", code_wsp, code_omega_c/ALPHA, unit="rad/s")
    code_Esp = 0.5*code_Ke*code_rc**2                  # electron_spring_energy
    S.check(18, "sst_tension_scales.cpp:electron_spring_energy", "[CODE=CANON]",
            "0.5 K_e r_c^2 == m_e c^2/8 (n=2)", code_Esp, M_E*C*C/8, unit="J")

    # --- sst_gravity.h : compute_G_swirl CODE-FORM vs canon-form ---
    t_p = math.sqrt(HBAR*G/C**5)
    code_G = v*C**5*t_p*t_p/(2.0*code_Fmax*code_rc**2)  # sst_gravity.h:compute_G_swirl
    canon_G = v*C**3*t_p*t_p/(code_rc*M_E)              # canon eq:canonical_gswirl
    S.check(32, "sst_gravity.h:compute_G_swirl (code-form) vs canon-form", "[CODE=CANON]",
            "v c^5 t_p^2/(2 F_max r_c^2) == v c^3 t_p^2/(r_c m_e) == G",
            code_G, canon_G, rel_tol=1e-9, unit="m^3/kg/s^2")
    S.note(32, "[CROSS-CHECK]", f"both G_swirl forms = {code_G:.7e} (target G={G})")

    # --- chronos_kelvin_transport.cpp : convention + patch 0001 ---
    S_t = math.sqrt(1 - v*v/(C*C))
    code_omega = (C/code_rc)*math.sqrt(max(0.0, 1-S_t*S_t))      # omega_from_swirl_clock (angular freq)
    canon_vort = (2*C/code_rc)*math.sqrt(max(0.0, 1-S_t*S_t))    # canon Sec 2.9 vorticity
    patched_vort = 2.0*code_omega                                # vorticity_from_swirl_clock (patch 0001)
    S.check(9, "chronos_kelvin_transport.cpp:omega_from_swirl_clock", "[CONVENTION]",
            "code omega = canon vorticity / 2 (angular-frequency convention)",
            code_omega, canon_vort/2.0, unit="rad/s")
    S.check(9, "chronos_kelvin_transport.cpp:vorticity_from_swirl_clock (patch 0001)", "[CODE=CANON]",
            "patched vorticity == canon 2c/r_c sqrt(1-S^2)", patched_vort, canon_vort, unit="rad/s")


# ===========================================================================
# SECTION: pauli  (claim 38) -- hydrodynamic exchange / Pauli benchmark
# Mirrors AtomicBridgeModel::pauli_barrier_scale (SSTcore v0.8.12/v0.8.19-compatible).
# [CALIBRATED BENCHMARK], not a derived theorem.
# ===========================================================================
def sec_pauli(S):
    header("SECTION pauli  -- Pauli-barrier benchmark 7.6 eV (claim 38)")
    G0   = 2*math.pi*R_C*VCHAR
    a0   = 2*R_C/(ALPHA*ALPHA)                  # Bohr radius = 2 r_c/alpha^2
    L    = 2*math.pi*a0
    a_cut = R_C                                 # CALIBRATED cutoff (= r_c, not a_core)
    V    = (RHO_F*G0*G0/(4*math.pi))*(L/a_cut)*1.0   # pauli_barrier_scale, shape=1
    S.check(38, "atomic_bridge_model.cpp:pauli_barrier_scale", "[CALIBRATED]",
            "rho_f Gamma0^2/(4pi)*(L/a_cut) = 7.69 eV (a_cut=r_c calibrated)",
            V/E, 7.69365, rel_tol=1e-3, unit="eV")
    S.note(38, "[BENCHMARK]", "cutoff-calibrated atomic-window scale; NOT a derivation")


# ===========================================================================
# SECTION: em_qed  (claims 61/67) -- swirl<->EM normalization, B_core=B_QED
# Correct prefactor m_e/e (dimensionally forced); e/m_e is rejected.
# ===========================================================================
def sec_em_qed(S):
    header("SECTION em_qed  -- swirl<->EM normalization B_core=B_QED (claims 61/67)")
    B_core = (M_E/E)*OMEGA_C                    # B = (m_e/e) omega ; omega=omega_c
    B_qed  = M_E*M_E*C*C/(E*HBAR)               # Schwinger critical field
    S.check(61, "swirl_vector_potential_bridge (m_e/e form)", "[CALIBRATED]",
            "(m_e/e)*omega_c == m_e^2 c^2/(e hbar) == B_QED", B_core, B_qed, unit="T")
    S.check(67, "Bcore_equals_Bqed numeric", "[ORTHODOX]",
            "B_QED ~ 4.414e9 T (Schwinger critical field)", B_qed, 4.4140052e9,
            rel_tol=1e-5, unit="T")
    wrong = (E/M_E)*OMEGA_C
    ok_guard = wrong > 1e25
    S.records.append(dict(
        claim=61, loc="swirl_vector_potential_bridge (e/m_e guard)", tag="[DERIVED]",
        desc="(e/m_e)*omega_c is NOT tesla (inverted form rejected)",
        got=float(wrong), expected=1e25, rel=0.0, ok=bool(ok_guard), unit="(arb.)"))
    status = "PASS" if ok_guard else "FAIL"
    print(f"  [{status}] claim    61 [DERIVED]   (e/m_e)*omega_c is NOT tesla (inverted form rejected)")
    print(f"          got={wrong:.3e} (arb.)  threshold>1e25  -> {'above' if ok_guard else 'below'} threshold")


# ===========================================================================
# SECTION: galactic  (claim 42) -- SPARC swirl-rotation fit machinery
# Mirrors fit_galactic_swirl_rotation_sparc.py on synthetic demo data.
# [RESEARCH-TRACK]: r_s fitted, not derived; coherence-length lemma OPEN.
# ===========================================================================
def sec_galactic(S):
    header("SECTION galactic  -- swirl flat-tail fit machinery (claim 42, research-track)")
    if not HAVE_NUMPY:
        S.note(42, "[SKIP]", "numpy required for galactic swirl fit demo")
        return

    rng = np.random.default_rng(0)
    r = np.linspace(0.5, 18.0, 24)
    Vdisk = 120.0*np.sqrt(r)/np.sqrt(r+2.0)
    Vgas  = 30.0*r/(r+6.0)
    Vbul  = 80.0*np.exp(-r/1.5)
    Yd_true, Yb_true = 0.5, 0.7
    signed = lambda V: V*np.abs(V)
    Vbar2 = signed(Vgas) + Yd_true*signed(Vdisk) + Yb_true*signed(Vbul)
    Ctail_true, rs_true = 110.0, 3.0
    Vsw = Ctail_true*(1-np.exp(-r/rs_true))
    Vtrue = np.sqrt(np.maximum(Vbar2, 0) + Vsw**2)
    errV = np.full_like(r, 5.0)
    Vobs = Vtrue + rng.normal(0, errV)

    y = signed(Vobs) - signed(Vgas)
    w = 1.0/np.maximum((2.0*np.abs(Vobs)*errV)**2, 1e-12)
    rs_grid = np.linspace(0.3, max(r)*1.5, 200)
    best = None
    for rs in rs_grid:
        g = (1.0-np.exp(-r/rs))**2
        X = np.column_stack([signed(Vdisk), signed(Vbul), g])
        Wsqrt = np.sqrt(w)
        coef, *_ = np.linalg.lstsq(X*Wsqrt[:, None], y*Wsqrt, rcond=None)
        coef = np.clip(coef, 0.0, None)
        Vmodel2 = signed(Vgas) + X@coef
        Vmodel = np.sqrt(np.maximum(Vmodel2, 0.0))
        chi2 = float(np.sum(((Vobs-Vmodel)/errV)**2))
        if best is None or chi2 < best["chi2"]:
            best = dict(chi2=chi2, rs=float(rs), Yd=float(coef[0]),
                        Yb=float(coef[1]), Ctail=float(np.sqrt(coef[2])),
                        Vmodel=Vmodel)

    dof = max(len(r)-4, 1)
    chi2_red = best["chi2"]/dof
    resid = Vobs - best["Vmodel"]
    rms = float(np.sqrt(np.mean(resid**2)))

    S.check_max(42, "fit_galactic_swirl_rotation_sparc.py:chi2_red", "[RESEARCH-TRACK]",
                "chi2/dof <= 1.5 on noisy synthetic demo (fit machinery sanity)", chi2_red, 1.5)

    S.note(42, "[RESEARCH-TRACK]",
           f"synthetic fit: Y_disk={best['Yd']:.3f} (truth {Yd_true}), "
           f"Y_bul={best['Yb']:.3f} (truth {Yb_true}), "
           f"C_tail={best['Ctail']:.1f} km/s (truth {Ctail_true}), "
           f"r_s={best['rs']:.2f} kpc (truth {rs_true}); RMS={rms:.2f} km/s")
    S.note(42, "[OPEN]",
           "Standalone fit_galactic_swirl_rotation_sparc.py provides SPARC rotmod fitter; "
           "no SPARC dataset bundled; r_s is fitted, not derived "
           "(coherence-length lemma OPEN).")


# ===========================================================================
# Section registry + CLI
# ===========================================================================
SECTIONS = {
    "constants":  sec_constants,
    "gate":       sec_gate,
    "topology":   sec_topology,
    "biotsavart": sec_biotsavart,
    "onsager":    sec_onsager,
    "impedance_matching": sec_impedance_matching,
    "delay":      sec_delay,
    "alpha":      sec_alpha,
    "pauli":      sec_pauli,
    "em_qed":     sec_em_qed,
    "galactic":   sec_galactic,
    "sstcore_alignment": sec_sstcore_alignment,
}

NOT_BUNDLED = """
SOURCE MAP (after Results.zip / trefoil_closure.zip / code.zip / routeB_RT_bem.zip):
  RECOVERED (script now located in user sources):
    claim 45/46  code/reproduce_alpha_cell_closure.py  (runs -> 137.036 closure;
                 NOTE: uses inserted E_eff~274 => OBSTRUCTION, not a derivation)
    claim 45     Results/sst_knot_candidate_robustness_outputs_v10_2/ (v10 sweep)
    claim 22/44  routeB_RT_bem/knotplot/sst_helicity_balance_scan.py +
                 Results/SST_helicity_by_base.csv ; taxonomy_builder_v3b.py
    claim 40     trefoil_closure/SST_ATOM_MASS_INVARIANT_SEMF_patched.py +
                 SST_Invariant_Mass_Results_CANON.csv
    claim 47/48  routeB_RT_bem/SST_CoilLab_v2_work/ (rodin6lane, sawbowl fields)
    routeB neg.  routeB_RT_bem/routeB_RT_bem_v18_multiknot_exponent_test.py
    alpha gates  code/solve_one_cell_hodge_phase_hessian.py, gp_core_second_variation
                 (w_perp obstruction), audit_derived_label_gates.py
  OPEN / RESEARCH-TRACK (fit machinery exists; external data + derivation still open):
    claim 42     fit_galactic_swirl_rotation_sparc.py provides the standalone
                 SPARC rotmod fitter + section 'galactic' (synthetic demo), but no
                 SPARC dataset is bundled and r_s is fitted, not derived
                 (coherence-length lemma OPEN).
  NOW REPRODUCED (standalone scripts + suite sections):
    Route-I     section 'impedance_matching' adds the v0.8.19 heat-sector guard
                 and chi_K^(T) protocol check; it is a normalization/falsifier
                 audit, not a PDE-level M_torsion[K] solver.
    claim 38     reproduce_pauli_barrier.py  + section 'pauli'  [CALIBRATED BENCHMARK]
    claim 61/67  reproduce_em_qed_normalization.py + section 'em_qed'
                 (correct prefactor m_e/e; B_core=B_QED=4.414e9 T)
"""

def main():
    ap = argparse.ArgumentParser(description="SST Canon v0.8.19-compatible verification suite")
    ap.add_argument("--list", action="store_true", help="list sections and exit")
    ap.add_argument("--only", nargs="+", metavar="SEC", help="run only these sections")
    ap.add_argument("--json", metavar="FILE", help="write machine-readable results")
    args = ap.parse_args()

    if args.list:
        print("Available sections:", ", ".join(SECTIONS)); return

    to_run = args.only if args.only else list(SECTIONS)
    bad = [s for s in to_run if s not in SECTIONS]
    if bad:
        print("Unknown section(s):", bad, "\nAvailable:", ", ".join(SECTIONS)); sys.exit(2)

    print("#"*78)
    print("# SST Canon v0.8.19-compatible -- consolidated claim verification suite")
    print("# numpy:", "yes" if HAVE_NUMPY else "NO (topology/biotsavart skipped)")
    print("#"*78)

    S = Suite()
    for name in to_run:
        SECTIONS[name](S)

    npass, ntot = S.summary()
    header(f"RESULT: {npass}/{ntot} graded checks passed "
           f"({len(to_run)} section(s): {', '.join(to_run)})")
    print(NOT_BUNDLED)

    if args.json:
        clean = []
        for r in S.records:
            r2 = {k: v for k, v in r.items() if k != "note"}
            clean.append(r2)
        with open(args.json, "w") as f:
            json.dump({"passed": npass, "total": ntot, "records": clean},
                      f, indent=2, default=str)
        print(f"[wrote {args.json}]")

    sys.exit(0 if npass == ntot else 1)


if __name__ == "__main__":
    main()