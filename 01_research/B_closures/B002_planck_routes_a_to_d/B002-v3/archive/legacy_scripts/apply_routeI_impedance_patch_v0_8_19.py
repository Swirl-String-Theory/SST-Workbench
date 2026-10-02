from pathlib import Path
import difflib, json, zipfile, subprocess, sys, os, re

base = Path('/mnt/data')
main_in = base/'SST_CANON-v0.8.19.tex'
rt_in = base/'SST_CANON-v0.8.19-research-track.tex'
py_in = base/'sst_v0_8_17_verification_suite.py'

main_out = base/'SST_CANON-v0.8.19-routeI-heat-guard.patched.tex'
rt_out = base/'SST_CANON-v0.8.19-research-track-routeI-heat-guard.patched.tex'
py_out = base/'sst_v0_8_19_verification_suite_impedance_patched.py'

main = main_in.read_text(encoding='utf-8')
rt = rt_in.read_text(encoding='utf-8')
py = py_in.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# Main canon v0.8.19 patch: add concise semantic guard in Two-Speed Discipline.
# ---------------------------------------------------------------------------
main_anchor = r"""        Until Eq.~\eqref{eq:core_torsion_impedance_gate_main} is derived from a controlled field calculation, the Swirl-Clock remains an orthodox functional form with an SST interpretation, or a derived-conditional bridge result, rather than a hard theorem from the NLSE core alone.
"""
main_insert = main_anchor + r"""

        \textbf{[CANON SEMANTIC RULE: THERMODYNAMIC SECTORS]} In Route-I and
        horizon-thermodynamic statements, the heat flux symbol must be
        sector-tagged.  The internal hydrodynamic redistribution channel is
        denoted \(Q_{\rm Kelvin}\) and is controlled by \(\vchar\), or by the
        core diagnostic speed \(c_s=\vchar/\sqrt{2}\).  The horizon/torsion
        channel is denoted \(Q_{\rm hor}^{(T)}\) and is controlled by the
        transverse causal speed \(c_T=c\). Therefore the Jacobson/Unruh
        temperature must not be computed with \(\vchar\) or \(c_s\). Substituting
        \(\vchar\) gives the wrong-sector ratio
        \begin{align}
            \frac{T_{\vchar}}{T_c}
            =
            \frac{c}{\vchar}
            =
            274.0719986,
            \label{eq:main_routeI_wrong_speed_guard}
        \end{align}
        not a derivation of horizon thermodynamics.  The detailed Route-I
        falsifier, entropy-area circularity guard, and nomenclature protocol are
        recorded in the research-track companion until the torsion-sector Unruh
        response and the area-law coefficient are independently derived.
"""
if main_anchor not in main:
    raise RuntimeError('main Two-Speed anchor not found')
main = main.replace(main_anchor, main_insert, 1)

# Update v0.8.19 history paragraph.
hist_anchor = r"""        \subsubsection{v0.8.19}
            \textbf{v0.8.19} adds an orthodox radius-convention ropelength/thickness foundation, a main-text guard that knot type alone does not determine a unique physical representative, a scalarized research-track screening functional \(E_{\rm screen}\) with \(Q_G\) retained only as a sector label unless mapped to \(I_G\), a derived leading thin-filament length/log energy anchor, a density and dimensional audit for geometric mass branches, a geometric impedance bridge demoted to research-track pointer form, an explicit $T_{\rm core}$ free-symbol guard, symmetry-metadata guards for dark-knot taxonomy, research-track operator-valued Swirl-Clock diagnostics, and stricter reintegration rules for derived Hamiltonian terms versus screening surrogates on top of v0.8.18.
"""
hist_insert = hist_anchor + r"""

            \textbf{v0.8.19 Route-I heat-guard patch} adds the sector-tagged
            thermodynamic nomenclature \(Q_{\rm Kelvin}\) versus
            \(Q_{\rm hor}^{(T)}\), the wrong-speed Unruh guard
            \(T_{\vchar}/T_c=c/\vchar\), the line-density area-law circularity
            guard, and the companion verification-suite protocol for the
            core--torsion impedance residual \(\chi_K^{(T)}\).
"""
if hist_anchor not in main:
    raise RuntimeError('main v0.8.19 history anchor not found')
main = main.replace(hist_anchor, hist_insert, 1)

# Add Unruh1976 in main bibliography if missing.
if r"\bibitem{Unruh1976}" not in main:
    bib_anchor = r"""            \bibitem{Unruh1981}
"""
    bib_insert = r"""            \bibitem{Unruh1976}
            W.~G. Unruh,
            ``Notes on black-hole evaporation,''
            \emph{Physical Review D} \textbf{14}, 870--892 (1976).
            DOI: \href{https://doi.org/10.1103/PhysRevD.14.870}{10.1103/PhysRevD.14.870}.

""" + bib_anchor
    if bib_anchor not in main:
        raise RuntimeError('main bib anchor Unruh1981 not found')
    main = main.replace(bib_anchor, bib_insert, 1)

# ---------------------------------------------------------------------------
# Research-track v0.8.19 patch: detailed Route-I heat split + circularity guard.
# ---------------------------------------------------------------------------
rt_route_anchor = r"""\end{align}

\textbf{[RESEARCH TRACK]} This is the most promising route because it connects
directly to horizon, boundary, and holographic SST sectors.
"""
rt_route_insert = r"""\end{align}

\textbf{[ROUTE-I SECTOR GUARD: KELVIN HEAT VERSUS HORIZON HEAT].}
The thermodynamic-gravity route must not identify the heat flux in
\(\delta Q=T\,dS\) with the internal Kelvin/core thermalization channel.
Kelvin-wave and NLSE/Gross--Pitaevskii core modes are hydrodynamic internal
modes whose characteristic speeds are controlled by \(\vchar\) or by
\(c_s=\vchar/\sqrt{2}\). Substituting the circulation speed into the Unruh
temperature gives
\begin{align}
    T_{\vchar}
    =
    \frac{\hbar a}{2\pi k_B\vchar},
    \qquad
    \frac{T_{\vchar}}{T_c}
    =
    \frac{c}{\vchar}
    =
    274.0719986 .
    \label{eq:rt_routeI_unruh_wrong_speed_guard}
\end{align}
This does not reproduce the orthodox Jacobson route \cite{Unruh1976,Jacobson1995}.
It is a wrong-sector diagnostic: it falsifies a Kelvin/core implementation of
Route I, not the existence of a separate torsion/horizon route.

The only canon-compatible Route-I heat flux is therefore the boost/horizon
energy flux of the hyperbolic transverse torsion/shear sector,
\begin{align}
    \delta Q_{\rm hor}^{(T)},
    \qquad
    c_T=c,
    \qquad
    T_{\rm SST}^{\rm hor}
    =
    \frac{\hbar a}{2\pi c k_B}.
    \label{eq:rt_routeI_horizon_heat_temperature}
\end{align}
Route I is conditional on three independent results:
\begin{align}
    c_T=c,
    \qquad
    \mathsf M_{\rm torsion}[K]
    =
    \frac{2E_0[K]}{c_T^2}\,\mathsf I,
    \qquad
    S=\eta A
    \quad\text{with}\quad
    \eta\ \text{derived independently}.
    \label{eq:rt_routeI_three_conditions}
\end{align}
If the thermal response entering \(\delta Q\) is instead shown to be controlled
by the Kelvin/core sector, Route I is falsified as a derivation of Einstein
dynamics \cite{Volovik2003,BarceloLiberatiVisser2011}.

\textbf{[THERMODYNAMIC NOMENCLATURE PROTOCOL].}
To prevent cross-contamination of energy scales, SST thermodynamic accounting
must explicitly distinguish
\begin{align}
    Q_{\rm Kelvin}
    &\quad\text{internal mode-redistribution heat, controlled by }\vchar
    \text{ or }c_s,\\
    Q_{\rm hor}^{(T)}
    &\quad\text{horizon/torsion heat flux, controlled by }c_T=c.
    \label{eq:rt_thermo_heat_channel_split}
\end{align}
Only \(Q_{\rm hor}^{(T)}\) is eligible for Unruh radiation, superradiant echoes,
and Jacobson-style horizon thermodynamics. \(Q_{\rm Kelvin}\) remains the
internal swelling, heat-capacity, and topological-relaxation channel of the
core.

\textbf{[AREA-LAW LINE-DENSITY GUARD].}
If the entropy-area law is modeled by horizon piercings of vortex strings, the
minimal stereological form is
\begin{align}
    N_{\rm pierce}
    =
    \frac12\Lambda_L A,
    \qquad
    S_{\rm pierce}
    =
    k_B\sigma_{\rm pierce}N_{\rm pierce}
    =
    \eta A,
    \qquad
    \eta=\frac12 k_B\sigma_{\rm pierce}\Lambda_L .
    \label{eq:rt_line_piercing_entropy_guard}
\end{align}
This is not a derivation of the Bekenstein--Hawking/Jacobson coefficient until
\(\Lambda_L\) and \(\sigma_{\rm pierce}\) are obtained from SST vacuum statistics
without calibrating them from \(G\). If \(\Lambda_L\) depends on local pressure,
temperature, or swirl state, \(\eta\) becomes local and Route I yields a
variable-coupling theory rather than exact Einstein dynamics.

\textbf{[RESEARCH TRACK]} This is the most promising route because it connects
directly to horizon, boundary, and holographic SST sectors.
"""
if rt_route_anchor not in rt:
    raise RuntimeError('RT Route-I anchor not found')
rt = rt.replace(rt_route_anchor, rt_route_insert, 1)

old = r"""The next open lemma is the Unruh-response derivation in the hyperbolic
torsion sector.  The area law may be attacked through a line-piercing entropy
model, but its coefficient remains calibrated unless the vacuum line density is
derived independently.
"""
new = r"""The next open lemma is the Unruh-response derivation in the hyperbolic
torsion sector.  The area law may be attacked through the line-piercing entropy
model of Eq.~\eqref{eq:rt_line_piercing_entropy_guard}, but its coefficient
remains calibrated unless the vacuum line density \(\Lambda_L\) and the
per-piercing entropy \(\sigma_{\rm pierce}\) are derived independently.
"""
if old not in rt:
    raise RuntimeError('RT line-density closing anchor not found')
rt = rt.replace(old, new, 1)

ct_anchor = r"""A derivation that produces \(u^2/\vchar{}^2\) or \(u^2/c_s^2\) therefore does not yet derive the Lorentz-compatible factor \(u^2/c^2\).
"""
ct_insert = ct_anchor + r"""

\textbf{[THERMODYNAMIC CROSS-REFERENCE].}
This two-speed separation is the same guard used in Route I:
\(Q_{\rm Kelvin}\) belongs to the internal hydrodynamic core layer, whereas
\(Q_{\rm hor}^{(T)}\) belongs to the transverse torsion/shear horizon layer.
The core--torsion impedance programme is precisely the test of whether the
slow internal energy reservoir \(E_0[K]\) can be dressed into a Lorentz-compatible
inertial response without reassigning the Kelvin/core signal speed to \(c\).
"""
if ct_anchor not in rt:
    raise RuntimeError('RT core-torsion cross-reference anchor not found')
rt = rt.replace(ct_anchor, ct_insert, 1)

open_anchor = r"""\textbf{[OPEN LEMMA].}
The equality \(\chi_K^{(T)}=1\) is the falsifiable theorem target. If numerical torsion-dressing returns a stable non-unity value, the Lorentz clock factor remains a constitutive bridge rather than a derived theorem from the core model.
"""
open_insert = open_anchor + r"""

\textbf{[FALSIFICATION PROTOCOL].}
For a fixed knot type \(K\), a stable residual
\(\chi_K^{(T)}\neq1\) falsifies the claim that this topology supplies a
Lorentz-compatible inertial carrier through the proposed torsion dressing. It
need not falsify SST as hydrodynamics, but it does block promotion of the
core--torsion bridge to a derivation of relativistic matter dynamics. Separately,
if the transverse sector itself yields \(c_T\neq c\) after the stiffness
\(K_T\) is independently fixed, the route is excluded by the tensor-speed gate.
A wrong-speed Kelvin closure may be recorded as
\begin{align}
    \chi_{\rm Kelvin\ target}^{(T)}
    =
    \left(\frac{c}{\vchar}\right)^2
    =
    7.5115469\times10^{4},
    \label{eq:rt_core_torsion_wrong_speed_residual}
\end{align}
when a Kelvin-normalized inertial tensor is tested against the torsion/horizon
cone. This diagnostic must be reported as a sector error, not as a successful
Route-I computation.
"""
if open_anchor not in rt:
    raise RuntimeError('RT open lemma anchor not found')
rt = rt.replace(open_anchor, open_insert, 1)

# Add final standalone bibitems to RT bibliography if missing.
if r"\bibitem{Unruh1976}" not in rt:
    rt_bib_anchor = r"""\bibitem{LIGOVirgoFermiINTEGRAL2017}
"""
    rt_bib_insert = r"""\bibitem{Unruh1976}
W.~G. Unruh,
``Notes on black-hole evaporation,''
\emph{Physical Review D} \textbf{14}, 870--892 (1976).
DOI: \href{https://doi.org/10.1103/PhysRevD.14.870}{10.1103/PhysRevD.14.870}.

\bibitem{Jacobson1995}
T.~Jacobson,
``Thermodynamics of spacetime: The Einstein equation of state,''
\emph{Physical Review Letters} \textbf{75}, 1260--1263 (1995).
DOI: \href{https://doi.org/10.1103/PhysRevLett.75.1260}{10.1103/PhysRevLett.75.1260}.

\bibitem{BarceloLiberatiVisser2011}
C.~Barcel\'o, S.~Liberati, and M.~Visser,
``Analogue gravity,''
\emph{Living Reviews in Relativity} \textbf{14}, 3 (2011).
DOI: \href{https://doi.org/10.12942/lrr-2011-3}{10.12942/lrr-2011-3}.

\bibitem{Volovik2003}
G.~E. Volovik,
\emph{The Universe in a Helium Droplet},
Oxford University Press (2003).
ISBN: 9780198507826.

""" + rt_bib_anchor
    if rt_bib_anchor not in rt:
        raise RuntimeError('RT final bib anchor not found')
    rt = rt.replace(rt_bib_anchor, rt_bib_insert, 1)

# ---------------------------------------------------------------------------
# Verification suite patch. Make a v0.8.19-labeled derivative of the suite.
# ---------------------------------------------------------------------------
py = py.replace('sst_v0_8_17_verification_suite.py', 'sst_v0_8_19_verification_suite.py')
py = py.replace('SST Canon v0.8.17-compatible', 'SST Canon v0.8.19-compatible')
py = py.replace('**Swirl-String Theory (SST) Canon v0.8.17-compatible**', '**Swirl-String Theory (SST) Canon v0.8.19-compatible**')
py = py.replace('v0.8.17-compatible port', 'v0.8.19-compatible port')
py = py.replace('v0.8.17 update', 'v0.8.19 update')
py = py.replace('v0.8.12/v0.8.17-compatible', 'v0.8.12/v0.8.19-compatible')
py = py.replace('v0.8.17-compatible', 'v0.8.19-compatible')
py = py.replace(
"the Onsager KT transition, and\n    the alpha finite-cell *coincidence-and-obstruction* ledger.",
"the Onsager KT transition, the Route-I heat-sector guard, and\n    the alpha finite-cell *coincidence-and-obstruction* ledger.",
1)
py = py.replace(
"  * Onsager T_KT                    -> chat fc5e123d (SST-15 complement)\n",
"  * Onsager T_KT                    -> chat fc5e123d (SST-15 complement)\n  * Route-I heat split / impedance  -> SST_CANON-v0.8.19 research-track patch\n",
1)

insert_before = "# ===========================================================================\n# SECTION: delay  (claim 26) -- DDE mode condition, current SSTcore aligned\n# ===========================================================================\n"
impedance_section = r'''# ===========================================================================
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

'''
if insert_before not in py:
    raise RuntimeError('python insert anchor not found')
py = py.replace(insert_before, impedance_section + insert_before, 1)

registry_anchor = '    "onsager":    sec_onsager,\n    "delay":      sec_delay,\n'
registry_insert = '    "onsager":    sec_onsager,\n    "impedance_matching": sec_impedance_matching,\n    "delay":      sec_delay,\n'
if registry_anchor not in py:
    raise RuntimeError('registry anchor not found')
py = py.replace(registry_anchor, registry_insert, 1)

nb_anchor = "  NOW REPRODUCED (standalone scripts + suite sections):\n"
nb_insert = "  NOW REPRODUCED (standalone scripts + suite sections):\n    Route-I     section 'impedance_matching' adds the v0.8.19 heat-sector guard\n                 and chi_K^(T) protocol check; it is a normalization/falsifier\n                 audit, not a PDE-level M_torsion[K] solver.\n"
if nb_anchor not in py:
    raise RuntimeError('NOT_BUNDLED anchor not found')
py = py.replace(nb_anchor, nb_insert, 1)

# Write patched files.
main_out.write_text(main, encoding='utf-8')
rt_out.write_text(rt, encoding='utf-8')
py_out.write_text(py, encoding='utf-8')

# Diffs.
def write_diff(orig_path, patched_path, diff_path):
    a = orig_path.read_text(encoding='utf-8').splitlines(keepends=True)
    b = patched_path.read_text(encoding='utf-8').splitlines(keepends=True)
    diff = difflib.unified_diff(a, b, fromfile=orig_path.name, tofile=patched_path.name)
    diff_path.write_text(''.join(diff), encoding='utf-8')

main_diff = base/'SST_CANON-v0.8.19-routeI-heat-guard.diff'
rt_diff = base/'SST_CANON-v0.8.19-research-track-routeI-heat-guard.diff'
py_diff = base/'sst_v0_8_19_verification_suite_impedance.diff'
write_diff(main_in, main_out, main_diff)
write_diff(rt_in, rt_out, rt_diff)
write_diff(py_in, py_out, py_diff)

# Run the new impedance section only.
json_path = base/'impedance_check_v0_8_19.json'
cmd = [sys.executable, str(py_out), '--only', 'impedance_matching', '--json', str(json_path)]
proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
run_txt = base/'impedance_check_v0_8_19.txt'
run_txt.write_text(proc.stdout + ('\nSTDERR:\n' + proc.stderr if proc.stderr else ''), encoding='utf-8')
if proc.returncode != 0:
    print(proc.stdout)
    print(proc.stderr, file=sys.stderr)
    raise RuntimeError(f'impedance suite failed with return code {proc.returncode}')

# Zip bundle.
bundle = base/'routeI_heat_guard_patch_bundle_v0_8_19.zip'
with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in [main_out, rt_out, py_out, main_diff, rt_diff, py_diff, json_path, run_txt, Path(__file__) if '__file__' in globals() else Path('/mnt/data/apply_routeI_impedance_patch_v0_8_19.py')]:
        if p.exists():
            z.write(p, arcname=p.name)

manifest = {
    'patched_files': [str(p) for p in [main_out, rt_out, py_out]],
    'diffs': [str(p) for p in [main_diff, rt_diff, py_diff]],
    'verification_json': str(json_path),
    'verification_txt': str(run_txt),
    'bundle': str(bundle),
}
(base/'routeI_heat_guard_patch_manifest_v0_8_19.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

print('Wrote v0.8.19 patch bundle:')
for p in [main_out, rt_out, py_out, main_diff, rt_diff, py_diff, json_path, run_txt, bundle]:
    print(f'{p}  {p.stat().st_size} bytes')
print('\nVerification output excerpt:')
print('\n'.join(proc.stdout.splitlines()[:40]))
