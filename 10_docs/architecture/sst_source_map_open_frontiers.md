# SST source-backed map for the finite-cell open frontiers

Source archive: `/mnt/data/SST-00_90_source_latex.zip` extracted to `/mnt/data/SST_00_90_src`.

## Executive result

No source file in SST-00..90 contains a completed first-principles derivation of all three open gates: `11/48`, `A_chi`, and `K_cell=E_eff/(8*pi)`. The archive does contain useful source layers for focused upgrades.

## Map

### 1. GP/NLS shell deficit 11/48

**File:** `SST-69_Topological_Mass_Quantization_via_Golden_NLS_Vortex_Cores.tex`  
**Lines:** 256-282;465-493

**Use:** Primary source for NLS smooth-core bridge; useful but explicitly labels NLS branch as closure, not theorem.

**Script / patch target:** `upgrade derive_gp_shell_deficit.py -> derive_gp_core_profile_second_variation.py; solve/expand GP/NLS core profile and test w_perp=1 without α.`

<details><summary>Source excerpt</summary>

```tex
L256: \section{Golden NLS Core Closure and Electron Geometry}
L257: \label{sec:nls_core}
L258: %======================================================================
L260: In SST, the NLS/Gross--Pitaevskii vortex-ring asymptotics are used as a smooth-core closure template to regularize thin-filament divergences and motivate finite-core corrections. This is a reference-model bridge, not a completed identity map to the full SST ontology.
L262: \subsection{Golden-core closure branch}
L263: A standard smooth-core vortex-ring asymptotic form is
L264: \begin{align}
L265: E(R) &= \frac{1}{2}\,\rho\,\Gamma_{\text{SST}}^2 R
L266: \left(\ln \frac{8R}{\rc} - A \right), \\
L267: V(R) &= \frac{\Gamma_{\text{SST}}}{4\pi R}
L268: \left(\ln \frac{8R}{\rc} - B \right),
L269: \end{align}
L270: with \(A\) and \(B\) determined by the chosen core model.
L272: We isolate a closure branch by imposing the constant-pressure boundary relation
L273: \begin{equation}
L274: B = A - 1.
L275: \label{eq:BA_constdruk}
L276: \end{equation}
L277: The algebraic identity \(\varphi^{-1}=\varphi-1\) motivates the Golden branch
L278: \begin{equation}
L279: A=\varphi,\qquad B=\varphi^{-1}.
L280: \label{eq:goldenAB}
L281: \end{equation}
L282: Hence

L465: \section{Supplementary Knot-Energy Functional Notes}
L466: \label{sec:knot_functional_notes}
L467: %======================================================================
L469: We retain the general SST mass-functional form
L470: \begin{equation}
L471: \Eeff[K]=\alpha C(K)+\beta L(K)+\gamma \mathcal{H}(K),
L472: \end{equation}
L473: where \(C\) is a crossing/contact proxy, \(L\) a length/ropelength proxy, and \(\mathcal{H}\) a helicity-like term. At the present stage, this is best treated as an organizing ansatz. Additional knot-complexity measures, such as polynomial degree or tangle decompositions, may be useful as coarse proxies, but they should not be identified uncritically with minimal crossing number or exact mass scaling without separate justification.
L475: Likewise, NLS-core line-tension forms such as
L476: \begin{equation}
L477: \beta_{\rm NLS}
L478: =
L479: \frac{\pi \rho_{\!f}\hbar^2}{m^2}
L480: \ln\!\left(\frac{1.464 R}{\xi}\right)
L481: \end{equation}
L482: are best interpreted as reference-model bridge expressions motivating smooth-core regularization, not as final SST field equations.
L484: %======================================================================
L485: \section{Conclusion}
L486: %======================================================================
L488: This version of the manuscript organizes the Golden-NLS closure program in a canon-safe way. The main points are:
L490: \begin{enumerate}
L491: \item SST core and continuum scales are explicitly anchored to textbook constants plus stated geometric closures.
L492: \item The Golden NLS branch is treated as a selected smooth-core closure, not a completed theorem.
L493: \item The electron solution \(R_e/\rc \approx 0.89838128\) is presented as a calibrated geometric inference under the core-dominated closure.
```
</details>

### 2. Pressure self-duality A_chi

**File:** `SST-83_Resolving Three Open Problems in Swirl-String Theory via the Electron Compton Frequency - Complete.tex`  
**Lines:** 320-365;407-423;569-590

**Use:** Best pressure/mechanical source: Laplace pressure, line tension, kinetic pressure, core density. Does not derive A_chi, but supplies primitive pressure-matching ingredients.

**Script / patch target:** `upgrade derive_pressure_self_duality.py -> derive_pressure_self_duality_from_laplace_matching.py; derive inner/outer terms and equal normalization from pressure matching.`

<details><summary>Source excerpt</summary>

```tex
L320: \subsection{Derivation of $\rhocore$ from the maximum force constraint}
L321: \label{subsec:rhocore}
L323: The numerical sweep of Section~\ref{sec:gap} identified the winning
L324: route as the \emph{maximum force constraint}. We now derive it in
L325: closed form.
L327: The SST maximum vortex interaction force is~\cite{IskandaraniCanon078}
L328: \begin{equation}
L329: F_{\max}
L330: = \alpha\!\left(\frac{\rc}{L_p}\right)^{\!-2}\frac{c^4}{4G},
L331: \label{eq:Fmax_def}
L332: \end{equation}
L333: where $L_p=\sqrt{\hbar G/c^3}$ is the Planck length. Substituting
L334: $L_p^2=\hbar G/c^3$ and eliminating $G$:
L335: \begin{equation}
L336: F_{\max}
L337: = \frac{\alpha\,\hbar\,c}{4\,\rc^2}.
L338: \label{eq:Fmax_simplified}
L339: \end{equation}
L341: The swirl-string vortex tube is a closed loop. The appropriate
L342: pressure model is therefore the \emph{cylindrical Laplace pressure}:
L343: the total force $F_{\max}$ acts on the full circumference
L344: $2\pi\rc$ of the tube cross-section, yielding a line tension
L345: \begin{equation}
L346: \mathcal{T}
L347: \;=\; \frac{F_{\max}}{2\pi\rc}
L348: \;=\; \frac{\alpha\,\hbar\,c}{8\pi\,\rc^3}.
L349: \label{eq:line_tension}
L350: \end{equation}
L351: The inward Laplace pressure on a cylindrical tube of radius $\rc$ is
L352: $P=\mathcal{T}/\rc$~\cite{Donnelly1991}:
L353: \begin{equation}
L354: P_{\mathrm{Laplace}}
L355: = \frac{\mathcal{T}}{\rc}
L356: = \frac{F_{\max}}{2\pi\rc^2}
L357: = \frac{\alpha\,\hbar\,c}{8\pi\,\rc^4}.
L358: \label{eq:Plaplace}
L359: \end{equation}
L360: Setting this equal to the kinetic pressure of the core fluid,
L361: $P_{\mathrm{Laplace}}=\tfrac{1}{2}\rhocore\vswirl^2$, and solving:
L362: \begin{equation}
L363: \rhocore
L364: = \frac{\alpha\,\hbar\,c}{4\pi\,\rc^4\,\vswirl^2}.
L365: \label{eq:rhocore_alpha}

L407: \subsection{Physical interpretation via the virial theorem}
L409: Equation~\eqref{eq:rhocore_final} has a transparent physical meaning.
L410: The total kinetic energy stored in a spherical vortex core of
L411: radius $\rc$ is
L412: \begin{equation}
L413: E_{\mathrm{kin}}
L414: = \tfrac{1}{2}\rhocore\vswirl^2 \cdot \tfrac{4\pi}{3}\rc^3
L415: = \frac{m_e c^2}{2\pi\vswirl^2\rc^3}
L416: \cdot\frac{\vswirl^2}{2}\cdot\frac{4\pi\rc^3}{3}
L417: = \frac{2\,m_e c^2}{3}.
L418: \label{eq:Ekin_core}
L419: \end{equation}
L420: The core kinetic energy equals \emph{exactly two-thirds of the electron
L421: rest energy}. This is consistent with the virial theorem for a
L422: three-dimensional harmonic system: $\langle T\rangle = E_{\mathrm{tot}}/2$
L423: gives $E_{\mathrm{kin}}=(2/3)m_ec^2$ when the spherical volume

L569: \section{Summary of Resolved and Open Problems}
L570: % ═════════════════════════════════════════════════════════════════════════════
L572: \begin{table}[h]
L573: \centering
L574: \caption{Status of the three Route-2 open problems after the present work.}
L575: \label{tab:status}
L576: \begin{tabular}{clp{7.5cm}l}
L577: \toprule
L578: \# & Problem & Resolution & Status \\
L579: \midrule
L580: (i) & $\rc$ is an external constant
L581: & Derived via $\rc=\vswirl/\omC$,
L582: equation~\eqref{eq:rc_derived}.
L583: & \textbf{Resolved} \\[4pt]
L584: (ii) & $\GammaZ$ defined self-referentially
L585: & Derived via $\GammaZ=2\pi\vswirl^2/\omC$,
L586: equation~\eqref{eq:Gamma0_derived}.
L587: & \textbf{Resolved} \\[4pt]
L588: (iii)& Energy-scale gap
L589: & $\rhocore$ derived via Laplace pressure
L590: and $F_{\max}$ constraint,
```
</details>

### 3. Leading geometric gate / α-free scale

**File:** `SST-88_The Geometric Limit of the Swirl-String Mass Functional.tex`  
**Lines:** 88-137;184-190

**Use:** Source for Compton-core length-ratio identity and geometric shielding gate 4/α = λ_c/(π r_c). Useful for leading gate context, not for 11/48.

**Script / patch target:** `keep as contextual theorem for α-free geometric gates; do not use to justify sub-ppm correction.`

<details><summary>Source excerpt</summary>

```tex
L88: \subsection{Elimination of kinematic variables via the Compton--core identity}
L89: From \eqref{eq:lc_geom}, we isolate the velocity ratios:
L90: \begin{equation}
L91: \frac{v_{\circlearrowleft}}{c}=\frac{2\pi r_c}{\lambda_c},
L92: \qquad
L93: \frac{c}{v_{\circlearrowleft}}=\frac{\lambda_c}{2\pi r_c}.
L94: \label{eq:vratio}
L95: \end{equation}
L97: \subsection{Geometric baseline mass scale}
L98: Assume a localized kinetic-energy density of the form
L99: \begin{equation}
L100: u = \frac{1}{2}\rho_m v_{\circlearrowleft}^2
L101: = \frac{1}{2}\frac{\rho_E}{c^2} v_{\circlearrowleft}^2,
L102: \label{eq:u_def}
L103: \end{equation}
L104: and a geometric core volume
L105: \begin{equation}
L106: V := \pi r_c^3 L_{\mathrm{tot}}(T),
L107: \label{eq:V_def}
L108: \end{equation}
L109: where $L_{\mathrm{tot}}(T)$ is a dimensionless ropelength-like factor.
L111: Then the inertial mass scale defined by energy equivalence is
L112: \begin{equation}
L113: M_0(T) := \frac{uV}{c^2}
L114: = \frac{1}{2}\rho_m\left(\frac{v_{\circlearrowleft}}{c}\right)^2 \pi r_c^3 L_{\mathrm{tot}}(T).
L115: \label{eq:M0_start}
L116: \end{equation}
L118: Substituting \eqref{eq:vratio} into \eqref{eq:M0_start} gives the \emph{pure geometric} form:
L119: \begin{equation}
L120: M_0(T) = 2\pi^3 \rho_m \frac{r_c^5}{\lambda_c^2} L_{\mathrm{tot}}(T).
L121: \label{eq:M0_geom}
L122: \end{equation}
L123: Dimensional check: $\rho_m$ (kg/m$^3$) times $r_c^5/\lambda_c^2$ (m$^3$) yields kg. \emph{No free kinematic variable remains.}
L125: \subsection{Substitution of the shielding gate}
L126: From the previously established geometric identity for the sector gate:
L127: \begin{equation}
L128: \frac{4}{\alpha}=\frac{2c}{v_{\circlearrowleft}}=\frac{\lambda_c}{\pi r_c},
L129: \label{eq:gate_geom}
L130: \end{equation}
L131: we define the exposure gate $G(T)\in\{0,1\}$ and a dimensionless topology kernel $\mathcal{K}(T)$.
L132: The canonical mass functional becomes:
L133: \begin{equation}
L134: M(T) = \left(\frac{\lambda_c}{\pi r_c}\right)^{G(T)} \mathcal{K}(T) \left( 2\pi^3 \rho_m \frac{r_c^5}{\lambda_c^2} L_{\mathrm{tot}}(T) \right).
L135: \label{eq:M_master}
L136: \end{equation}
L137: This form contains no explicit fine-structure constant $\alpha$ and no explicit swirl velocity $v_{\circlearrowleft}$.

L184: \section{Status, Assumptions, and Falsifiers}
L186: Assumptions: (i) energy density model follows $u = \frac{1}{2}\rho_m v_{\circlearrowleft}^2$; (ii) geometric core volume follows $V = \pi r_c^3 L_{\mathrm{tot}}$; (iii) closure identity maps the kinematic foliation parameters to the Compton scale exactly; (iv) the exposure gate is discrete and binary $G(T)\in\{0,1\}$.
L188: Falsifiers: Any empirical inconsistency in the core identity network (e.g., measuring independent drifts in $\lambda_c$, $r_c$, or $v_{\circlearrowleft}$) breaks the geometric gate derivation. Furthermore, any failure of the master equation to accurately predict hadronic-to-leptonic sector ratios when $L_{\mathrm{tot}}$ and $\mathcal{K}$ are fixed invalidates the physical interpretation of $G(T)$ as an impedance coupling.
L190: \begin{thebibliography}{9}
```
</details>

### 4. Master-equation status discipline

**File:** `SST-90_Master_Equation.tex`  
**Lines:** 132-150;329-350

**Use:** Canon-side status split: geometric gate is structurally fixed, coefficient choices remain modeled/open.

**Script / patch target:** `use for manuscript label audit; prevents over-upgrading closures.`

<details><summary>Source excerpt</summary>

```tex
L132: \section{Geometric gate lemma}
L134: \begin{lemma}[Canonical geometric shielding gate]
L135: The geometric sector factor is
L136: \begin{equation}
L137: \Pi_K=\left(\frac{\lambda_c}{\pi \rc}\right)^{G(K)}.
L138: \end{equation}
L139: Using the SST closure relation, this is equivalently
L140: \begin{equation}
L141: \Pi_K=\left(\frac{4}{\alpha}\right)^{G(K)}.
L142: \end{equation}
L143: \end{lemma}
L145: \begin{proof}
L146: The existing SST geometric closure identifies the dimensionless shielding ratio as
L147: \begin{equation}
L148: \frac{\lambda_c}{\pi \rc}=\frac{4}{\alpha}.
L149: \end{equation}
L150: Since \(G(K)\) is binary, the state either remains unamplified (\(G=0\)) or receives one geometric exposure factor (\(G=1\)).

L329: \section{Status and assumptions}
L331: \subsection*{Derived / structurally fixed}
L332: \begin{equation}
L333: \rhoE=\frac12 \rhoF \norm{\vswirl}^2,
L334: \qquad
L335: \rhoM=\rhoE/c^2,
L336: \qquad
L337: \SwirlClock=\sqrt{1-\norm{\vswirl}^2/c^2},
L338: \qquad
L339: \frac{\lambda_c}{\pi \rc}=\frac4\alpha.
L340: \end{equation}
L342: \subsection*{Closure-level / modeled}
L343: \begin{equation}
L344: G(K)\in\{0,1\},
L345: \qquad
L346: \Xi_K=
L347: \left[\alpha_C C+\beta_L L+\gamma_H \mathcal H\right]\varphi^{-2k}.
L348: \end{equation}
L350: \subsection*{Open}
```
</details>

### 5. Mode cutoff N_p=4 / delay selection

**File:** `SST-55_Delay-Induced_Mode_Selection_in_Circulating_Feedback_Systems.tex`  
**Lines:** 91-165;177-208

**Use:** Orthodox delay-mode selection foundation. Useful to formulate N_p=4 as stability-selected low-mode pressure manifold, but not yet a direct proof.

**Script / patch target:** `new test_pressure_mode_cutoff_delay_stability.py; compute l=0,1 vs l≥2 branch stability without fitting α.`

<details><summary>Source excerpt</summary>

```tex
L91: \section*{III. Minimal Effective Phase Description with Temporal Nonlocality}
L92: The purpose of this reduced model is not quantitative prediction for a specific experimental platform, but to expose the minimal dynamical ingredients required for delay-induced spectral discreteness. By isolating the phase degree of freedom, the analysis highlights the constitutive role of temporal nonlocality in enforcing discrete, stability-selected operating states.
L94: Let $\phi(t)$ denote the instantaneous phase of the circulating field. The dynamics are governed by a generic frequency-pulling equation with delayed self-interaction \cite{Yeung1999},
L95: \begin{equation}
L96: \dot{\phi}(t) = \omega_0 + \kappa \sin\big[\phi(t-\tau) - \phi(t)\big],
L97: \end{equation}
L98: where $\omega_0$ is the intrinsic frequency and $\kappa$ is the feedback coupling strength.
L100: \begin{figure}[h]
L101: \centering
L102: \begin{tikzpicture}[>=Stealth]
L103: \draw[->] (0,0) -- (6,0) node[right] {$t$};
L104: \draw[->] (0,0) -- (0,3) node[above] {$\phi(t)$};
L106: \draw[blue, thick, domain=0:5, samples=100]
L107: plot (\x,{1.5+0.8*sin(1.5*\x r)});
L108: \draw[dashed] (1.5,0) -- (1.5,3);
L109: \node at (1.5,-0.4) {$t-\tau$};
L110: \node[blue] at (4.2,2.3) {$\phi(t)$};
L111: \end{tikzpicture}
L112: \caption{Phase evolution illustrating delayed self-interaction: the instantaneous phase $\phi(t)$ depends on its value one circulation time earlier.}
L113: \label{fig:phase_feedback}
L114: \end{figure}
L116: \subsection*{A. Emergent Spectral Discreteness}
L117: We seek uniformly rotating solutions $\phi(t) = \Omega t + \phi_0$. Substitution yields the transcendental condition
L118: \begin{equation}
L119: \Omega = \omega_0 - \kappa \sin(\Omega \tau).
L120: \end{equation}
L122: \begin{figure}[h]
L123: \centering
L124: \includegraphics[width=0.8\textwidth]{fig1_1_120817.png}
L125: \caption{Discrete intersections correspond to stable phase-locked circulating modes. Finite delay alone enforces spectral discreteness.}
L126: \label{fig:transcendental}
L127: \end{figure}
L129: In the long-delay regime $(\kappa \tau > 1)$, this equation admits multiple stable solutions organized into a discrete ladder,
L130: \begin{equation}
L131: \Omega_n \approx \frac{2\pi n}{\tau} + \delta\Omega, \qquad n \in \mathbb{Z}.
L132: \end{equation}
L134: \begin{figure}[h]
L135: \centering
L136: \begin{tikzpicture}
L137
[...]

L177: \section*{IV. Discussion}
L178: The results presented here demonstrate that temporal circulation alone is sufficient to generate discrete mode families through stability constraints, without reliance on spatial standing-wave boundary conditions or microscopic quantization. This mechanism mirrors the emergence of bianisotropic cross-couplings in homogenized metamaterials, where hidden microstructure necessitates an expanded macroscopic description.
L180: This parallels the Willis framework \cite{Willis2012}, where effective constitutive relations acquire additional degrees of freedom when microstructural information is averaged out. In the present context, temporal nonlocality plays the role of an effective constitutive ingredient, legitimizing additional dynamical structure at the macroscopic level.
L182: \begin{figure}[h]
L183: \centering
L184: \begin{tikzpicture}
L185: \node (a) at (0,0) {
L186: \begin{tikzpicture}[scale=0.8]
L187: \draw[->, thick] (0,0)--(2,0);
L188: \node at (1,-0.5) {space};
L189: \node at (1,0.5) {spatial microstructure};
L190: \end{tikzpicture}
L191: };
L192: \node (b) at (5,0) {
L193: \begin{tikzpicture}[scale=0.8]
L194: \draw[->, thick] (0,0)--(2,0);
L195: \node at (1,-0.5) {time};
L196: \node at (1,0.5) {temporal memory};
L197: \end{tikzpicture}
L198: };
L199: \node at (0,-1.5) {(a)};
L200: \node at (5,-1.5) {(b)};
L201: \end{tikzpicture}
L202: \caption{Analogy between spatial homogenization (left) and temporal nonlocality in delayed circulation (right). Both generate emergent effective structure.}
L203: \label{fig:analogy}
L204: \end{figure}
L206: By explicitly incorporating finite circulation time, the model avoids the infinite-speed paradox associated with parabolic transport theories. The resulting dynamics exhibit hyperbolic-like features, akin to second-sound phenomena in nonlocal thermal media.
L208: \section*{V. Conclusion}
```
</details>

### 6. Mode cutoff N_p=4 / closed-loop phase locking

**File:** `SST-60_Swirl-Clock_Phase_Locking_in_Closed_Circulation_Loops.tex`  
**Lines:** 101-150;225-260;509-544

**Use:** SST-specific phase-locking and branch filtering; likely best SST source for pressure-sector stability selection.

**Script / patch target:** `same as above; derive or falsify low-mode cutoff with stability filtering.`

<details><summary>Source excerpt</summary>

```tex
L101: \section{Minimal delayed phase model}
L102: A minimal classical description capturing this delayed feedback is given by a delayed phase oscillator of the form
L103: \begin{equation}
L104: \dot{\phi}(t) = \Omega_0 + K \sin\big(\phi(t-\tau) - \phi(t)\big),
L105: \label{eq:delayed_oscillator}
L106: \end{equation}
L107: where $\Omega_0$ is the natural angular frequency associated with unperturbed circulation, $K$ is a real coupling constant encoding the strength of feedback between successive circulations, and $\tau$ is the circulation delay. This equation represents a continuous, deterministic dynamical system with finite propagation time and smooth nonlinearity.
L109: Importantly, the model contains no quantization postulates, no discrete variables, and no topological constraints. All discreteness that emerges from the dynamics is therefore generated internally by classical delay--induced feedback. Variants of this equation appear naturally in delayed oscillators, phase--locked loops, and wave propagation in closed resonant structures \cite{Erneux2009,Earl2003,Gardner2005,Ikeda1979}.
L111: \section{Phase--locked solutions}
L113: Uniformly rotating, or phase--locked, solutions are sought in the form
L114: \begin{equation}
L115: \phi(t) = \Omega t + \phi_0,
L116: \label{eq:ansatz}
L117: \end{equation}
L118: where $\Omega$ is a constant rotation rate and $\phi_0$ is arbitrary.
L119: Substitution into Eq.~\ref{eq:delayed_oscillator} yields
L120: \begin{equation}
L121: \Omega = \Omega_0 - K \sin(\Omega\tau).
L122: \label{eq:self_consistency}
L123: \end{equation}
L125: When $\beta=K\tau$ is small, Eq.~\ref{eq:self_consistency} admits a single solution.
L126: For sufficiently large delay or feedback strength, multiple branches emerge.
L128: In this work, we define the \emph{dynamically selected spectrum} as the set
L129: \begin{equation}
L130: \mathcal{S} :=
L131: \left\{
L132: \Omega \in \mathbb{R} \;\middle|\;
L133: \Omega \text{ satisfies Eq.~\ref{eq:self_consistency} and is linearly stable}
L134: \right\}.
L135: \label{eq:frequency_set}
L136: \end{equation}
L138: Thus the term ``spectrum'' refers to the discrete set of attracting phase--locked frequencies of the delay equation, not to eigenvalues of a linear operator.
L140: \section{Linear stability and branch filtration}
L141: \label{sec:stability}
L143: We now turn from the existence of phase--locked bran
[...]

L225: \section{Derivation: Asymptotic Spacing, Stability Filtering, and Branch Density}
L227: We compare the kinematic boundary quantization of a scalar wave equation to the dynamical frequency selection of the delayed phase oscillator.
L229: For a classical scalar wave $\psi(x,t) = C e^{i(kx-\omega t)}$ on a closed loop of length $L$, periodicity imposes $\psi(x,t)=\psi(x+L,t)$, which implies $e^{ikL}=1$, yielding
L230: \begin{equation}
L231: k_n=\frac{2\pi n}{L}.
L232: \label{eq:k_n}
L233: \end{equation}
L235: In the delayed dynamical system governed by Eq.~\ref{eq:delayed_oscillator}, a phase-locked solution $\phi_s(t)=\Omega t+\phi_0$ satisfies the self-consistency condition of Eq.~\ref{eq:self_consistency}. Defining the phase lag $\theta=\Omega\tau$ and the dimensionless coupling $\beta=K\tau$, Eq.~\ref{eq:self_consistency} can be rewritten as
L236: \begin{equation}
L237: \theta=\Omega_0\tau-\beta\sin\theta.
L238: \label{eq:theta_beta}
L239: \end{equation}
L241: For $\beta\gg1$, roots lie near $\theta_m=m\pi$. Writing $\theta_m=m\pi+\delta_m$ with $|\delta_m|\ll1$ and using $\sin(m\pi+\delta_m)\approx(-1)^m\delta_m$, we obtain
L242: \begin{equation}
L243: \delta_m=\frac{\Omega_0\tau-m\pi}{1+(-1)^m\beta}.
L244: \label{eq:delta_m}
L245: \end{equation}
L247: Thus $\delta_m\to0$ as $\beta\to\infty$, and the asymptotic spacing becomes
L248: \begin{equation}
L249: \Omega_m\tau\approx m\pi.
L250: \label{eq:omega_m_approx}
L251: \end{equation}
L253: The graphical structure of the transcendental roots and their asymptotic organization is illustrated in Fig.~\ref{fig:phase_locking}.
L255: \begin{figure}[ht]
L256: \centering
L257: \begin{tikzpicture}
L258: \pgfplotsset{compat=1.18}
L260: % Parameters

L509: \section{Numerical validation of branch selection}
L510: \label{sec:numerics}
L512: To supplement the linearized analysis, we performed direct numerical integrations of the delayed phase equation
L513: \begin{equation}
L514: \dot{\phi}(t) = \Omega_0 + K \sin\big(\phi(t-\tau)-\phi(t)\big)
L515: \end{equation}
L516: for representative parameter values in the multibranch regime. The purpose of these simulations is not to provide a full nonlinear basin classification, but to verify the minimal dynamical claim that branches classified as linearly stable are observed as attracting locked motions, whereas branches classified as unstable are not.
L518: Initial histories were chosen near selected phase--locked branches in the form
L519: \begin{equation}
L520: \phi(t)=\Omega_\ast t+\phi_0+\varepsilon \eta(t),
L521: \qquad
L522: t\in[-\tau,0],
L523: \end{equation}
L524: with $\varepsilon\ll1$. Figure~\ref{fig:numerical_validation} shows direct numerical integration for one branch with $A>0$ and one branch with $A\tau<-1$. In the stable case, the instantaneous frequency remains in a small oscillatory neighborhood of the selected locked branch and the residual frequency tends toward zero in an oscillatory manner, consistent with orbital stability. In the unstable case, the trajectory does not converge to the unstable reference branch and instead departs from it persistently, approaching a nearby admissible stable branch.
L526: For completeness, the corresponding residual magnitudes are shown on a logarithmic scale in Fig.~\ref{fig:numerical_validation_log}. The sharp downward spikes in the stable curve correspond to zero crossings of the oscillatory residual and should not be interpreted as separate branch transitions; the relevant quantity is the decay of the residual envelope over successive delay cycles.
L528: \begin{figure}[ht]
L529: \centering
L530: \includegraphics[width=\textwidth]{sst60_numerics_output/sst60_optionA_threepanel.png}
L531: \caption{\footnotesize
L532: Direct numerical integration of the delayed phase equation for initial histories chosen near a linearly stable branch and a linearly unstable branch. Top: instantaneous frequency trajectories $\omega_{\mathrm{inst}}(t)=\dot{\phi}(t)$, together with the stable locked branch and the unstable reference branch. Middle: residual frequency relative to the stable locked branch, showing oscillatory rela
[...]
```
</details>

### 7. Mode cutoff / SST embedding of delay branch selection

**File:** `SST-72_Delay-Selected Swirl Modes, Two-Mode Correlations, and the Clock--Loop Sector of Swirl--String Theory.tex`  
**Lines:** 315-367;469-523;812-833

**Use:** Canonical embedding of delay-selected modes and explicit assumptions/falsifiers. Good for writing a clean derivation-target appendix.

**Script / patch target:** `use as assumptions/falsifiers template for N_p=4 stability program.`

<details><summary>Source excerpt</summary>

```tex
L315: \subsection{Reduced phase equation}
L317: \begin{definition}[Loop phase observable]
L318: Let \(\phi(t)\) denote the phase of a closed circulating reduced SST mode, sampled at a fixed Poincar\'e section of the loop.
L319: \end{definition}
L321: The most general delayed scalar phase law compatible with loop return is
L322: \begin{equation}
L323: \dot{\phi}(t)=\omega_0+F\!\left(\phi(t-\tauloop)-\phi(t)\right),
L324: \tag{\TagD}
L325: \label{eq:generic}
L326: \end{equation}
L327: where \(F\) is \(2\pi\)-periodic. Retaining the leading Fourier harmonic yields
L328: \begin{equation}
L329: \dot{\phi}(t)
L330: =
L331: \omega_0+\kappa\sin\!\big[\phi(t-\tauloop)-\phi(t)\big].
L332: \tag{\TagD}
L333: \label{eq:delay}
L334: \end{equation}
L336: \begin{proposition}[First-harmonic loop-phase reduction]
L337: Under weak phase pulling and periodic mismatch feedback, closed-loop transport reduces to Eq.~\eqref{eq:delay}.
L338: \end{proposition}
L340: \begin{proof}
L341: Expand the periodic mismatch functional \(F(\Delta\phi)\) in Fourier modes. The constant term can be absorbed into \(\omega_0\). The leading odd locking contribution is proportional to \(\sin(\Delta\phi)\), giving Eq.~\eqref{eq:delay}.
L342: \end{proof}
L344: \subsection{Branch equation and stability}
L346: Uniformly rotating solutions
L347: \begin{equation}
L348: \phi(t)=\Oloop t+\phi_0
L349: \tag{\TagD}
L350: \label{eq:uniform}
L351: \end{equation}
L352: exist iff
L353: \begin{equation}
L354: \Oloop=\omega_0-\kappa\sin(\Oloop\tauloop).
L355: \tag{\TagD}
L356: \label{eq:branch}
L357: \end{equation}
L358: Linear stability requires
L359: \begin{equation}
L360: 1+\kappa\tauloop\cos(\Oloop\tauloop)>0.
L361: \tag{\TagD}
L362: \label{eq:stability}
L363: \end{equation}
L365: \begin{lemma}[Approximate branch ladder]
L366: For \(\kappa\tauloop\gtrsim 1\), Eq.~\eqref{eq:branch} admits an approximately discrete family
L367: \begin{equation}

L469: \section{Positivity-inspired consistency filtering}\label{sec:positivity}
L471: \subsection{Motivation}
L473: Recent positivity-bootstrap results show that, in relativistic EFTs with large scale separation and weak coupling, amplitudes cannot be consistently dominated by terms growing faster than \(E^4\). When the leading reduced amplitude scales as \(E^n\) with \(n>4\), positivity typically forces tunings or the inclusion of extra light sectors; isolated massive spin-$3/2$ sectors fail in precisely this way. \tag{\TagT}
L475: Motivated by this, we introduce an SST reduced-sector filter.
L477: \begin{definition}[Reduced growth filter]
L478: Let \(\mathcal M_{\rm red}(E,\vartheta)\) denote a reduced SST amplitude or response kernel expanded as
L479: \begin{equation}
L480: \mathcal M_{\rm red}(E,\vartheta)
L481: =
L482: c_2(\vartheta)E^2+c_4(\vartheta)E^4+c_6(\vartheta)E^6+\cdots.
L483: \tag{\TagR}
L484: \label{eq:Mred}
L485: \end{equation}
L486: We call the reduced sector \emph{admissible in isolation} if, after all internally available SST tunings are imposed, the dominant term satisfies
L487: \begin{equation}
L488: \mathcal M_{\rm red}(E,\vartheta)=O(E^4)
L489: \quad\text{as }E\to \infty
L490: \text{ within the reduced EFT regime.}
L491: \tag{\TagR}
L492: \label{eq:E4rule}
L493: \end{equation}
L494: \end{definition}
L496: \begin{remark}
L497: Equation~\eqref{eq:E4rule} is not claimed as a theorem of full SST. It is an imported consistency heuristic from positivity bootstrap, promoted here to a working criterion for reduced SST sectors.
L498: \end{remark}
L500: \subsection{No isolated branch principle}
L502: \begin{proposition}[No isolated branch principle]
L503: If a proposed reduced SST excitation yields a leading isolated response of the form
L504: \begin{equation}
L505: \mathcal M_{\rm red}^{\rm iso}(E,\vartheta)\sim E^n,
L506: \qquad n>4,
L507: \tag{\TagR}
L508: \label{eq:iso-growth}
L509: \end{equation}
L510: and if no internal SST tuning reduces this growth to \(O(E^4)\), then the excitation should not be treated as an admissible isolated low-energy branch. It must instead be embedded into a coupled reduced sector with additional companion fields, channels, or topological constraints.
L511: \tag{\TagR/\TagD}
L512: \label{prop:noisolated}
L513: \end{proposition}
L515: \begin{proof}[Heuristic derivation]
L516: This is a direct adaptation of the po
[...]

L812: \section{Status, assumptions, and falsifiers}\label{sec:status}
L814: \subsection*{Assumptions}
L815: \begin{enumerate}[label=(A\arabic*)]
L816: \item A closed SST excitation admits a collective phase variable.
L817: \item The leading mismatch feedback is well approximated by the first Fourier harmonic.
L818: \item The reduced amplitude sector can be modeled to leading order by cubic saturation.
L819: \item The relevant loop transport speed \(\vtr\) is well defined.
L820: \item Topological stabilization acts after branch selection, not before it.
L821: \item Some reduced SST sectors admit enough analyticity and symmetry structure for positivity-inspired filtering to be meaningful.
L822: \end{enumerate}
L824: \subsection*{Falsifiers}
L825: \begin{enumerate}[label=(F\arabic*)]
L826: \item Closed-loop SST simulations fail to exhibit delay-selected branch families as \(L_{\rm loop}/\vtr\) is varied.
L827: \item Finite-amplitude reduced SST branches do not require any saturation-like mechanism.
L828: \item The SST topological sector is found to be fully independent of any pre-topological branch structure.
L829: \item Reduced collective observables near threshold show no correlation structure when the unified model predicts it.
L830: \item No sensible analyticity or null-constraint program can be constructed for any nontrivial reduced SST amplitude.
L831: \end{enumerate}
L833: \section{Conclusion}\label{sec:conclusion}
```
</details>

### 8. Phase-Hessian / Hodge boundary determination

**File:** `SST-63_Holograpic.tex`  
**Lines:** 213-260;611-665

**Use:** Source for Euler/Hodge boundary determination theorem. Useful for one-cell Hodge phase-Hessian framing.

**Script / patch target:** `upgrade derive_one_cell_phase_hessian.py -> solve_one_cell_hodge_phase_hessian.py using Hodge/DEC/FEEC; test Λ_phi=E_eff/2.`

<details><summary>Source excerpt</summary>

```tex
L213: \section{Boundary Determination Theorem (Euler/Hodge Form)}
L215: We now state the precise theorem underlying SHP in the classical Euler regime.
L217: \paragraph{Theorem (Boundary Determination of Bulk Swirl State).}
L218: Let $V\subset\mathbb{R}^3$ be smooth and simply connected.
L219: Assume $\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}(t,\cdot)\in H^s(V)$ with
L220: $s>5/2$, impermeable boundary conditions, and inviscid evolution without
L221: reconnection so that $\mathcal{T}$ is conserved.
L222: Then for each $t$ in the local existence interval, the solenoidal bulk field
L223: $\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}(t,\cdot)$ is uniquely determined
L224: by $\mathbf{v}_\tau(t,\cdot)|_{\partial V}$ and $\mathcal{T}$, up to pressure gauge.
L226: \paragraph{Sketch of proof.}
L227: For divergence-free vector fields with $\mathbf{v}\cdot\mathbf{n}=0$, Hodge
L228: decomposition yields
L229: \begin{equation}
L230: \mathbf{v}_{\!\boldsymbol{\circlearrowleft}}
L231: = \nabla\times\mathbf{A} + \mathbf{h},
L232: \end{equation}
L233: where $\mathbf{h}$ is harmonic (curl-free and divergence-free).
L234: In simply connected $V$, $\mathbf{h}=0$; otherwise, $\mathbf{h}$ is finite-dimensional
L235: and fixed by circulation around nontrivial cycles, which are included in
L236: $\mathcal{T}$.
L238: The vector potential satisfies a Poisson problem
L239: $-\Delta\mathbf{A}=\boldsymbol{\omega}$ with gauge and boundary conditions,
L240: so that $\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=\nabla\times\mathbf{A}$
L241: is uniquely determined by the vorticity field $\boldsymbol{\omega}$.
L243: By Stokes' theorem, boundary circulations determine vorticity fluxes through
L244: all interior surfaces anchored on $\partial V$,
L245: \begin{equation}
L246: \oint_{\partial S}\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\cdot
L247: d\boldsymbol{\ell}
L248: =
L249: \int_S \boldsymbol{\omega}\cdot d\mathbf{S}.
L250: \end{equation}
L251: Conservation of the topological sector $\mathcal{T}$ restricts admissible
L252: interior rearrangements of vorticity. Together, these conditions uniquely fix
L253: $\boldsymbol{\omega}$ and hence the bulk field
L254: $\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}$.
L256: \paragraph{Consequence.}
L257: The Euler equations act as constraint equations: the bulk is the unique
L258: configuration compatible with boundary swirl data and conserved top
[...]

L611: \section{Clock Holography, Falsifiers, and Minimal Experiments}
L612: %==============================================================================
L614: The Swirl Holographic Principle is not a metaphysical claim; it produces concrete,
L615: falsifiable consequences. In SST, time, gravity, and bulk dynamics inherit their
L616: structure from boundary swirl data and conserved topology. This section states the
L617: key predictions and the minimal conditions under which SHP must fail.
L619: \subsection{Clock holography}
L621: In SST, the local clock rate is a functional of swirl intensity. A representative
L622: form used throughout SST is
L623: \begin{equation}
L624: dt_{\mathrm{local}}
L625: =
L626: dt_{\infty}
L627: \sqrt{1 - \frac{\lVert \boldsymbol{\omega} \rVert^2}{c^2}},
L628: \qquad
L629: \boldsymbol{\omega}=\nabla\times\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}.
L630: \end{equation}
L632: By SHP, the bulk vorticity field $\boldsymbol{\omega}(t,\cdot)$ is uniquely
L633: determined by boundary swirl data and the conserved sector $\mathcal{T}$.
L634: Consequently, the bulk clock field is also boundary-determined.
L636: \paragraph{Clock holography (statement).}
L637: Given fixed $\mathcal{T}$, the entire bulk distribution of clock rates in $V$ is a
L638: functional of boundary swirl data:
L639: \begin{equation}
L640: dt_{\mathrm{local}}(t,\mathbf{x})
L641: =
L642: \mathcal{C}\!\left[
L643: \mathbf{v}_\tau(t,\cdot)\big|_{\partial V}
L644: \right].
L645: \end{equation}
L647: This result has no direct analogue in GR or AdS/CFT: in SST, time dilation is not
L648: merely influenced by boundary conditions but \emph{encoded} by them.
L650: \subsection{Topology as protected information}
L652: The discrete sector labels $\mathcal{T}$ play the role of protected information.
L653: Helicity and linking numbers cannot change under ideal evolution and therefore act
L654: as robust memory degrees of freedom.
L656: \paragraph{Prediction.}
L657: Two systems driven with identical boundary swirl data but prepared in different
L658: topological sectors $\mathcal{T}_1\neq\mathcal{T}_2$ will exhibit distinct bulk
L659: responses (clock-rate distributions, pressure fields, mode spectra), despite
L660: indistinguishable boundary forcing.
L662: This is a sharp discriminator between SST and purely metric theories, where
L663: topology without curvature has no dynamical 
[...]
```
</details>

### 9. Far-field 1/r / Green-function structure

**File:** `SST-49_Emergent_Inverse-Square_Law_from_Hydrodynamic_Derivations.tex`  
**Lines:** 37-105;135-180

**Use:** Direct derivation of 1/r Green function and far-field monopole flux. Supports q_phi=1/exterior capacity, not interior Hessian Λ_phi.

**Script / patch target:** `use to justify exterior Green function part already derived; not enough for K_cell=E_eff/8π.`

<details><summary>Source excerpt</summary>

```tex
L37: \section{Derivation I: Gauss-law scalar EFT $\Rightarrow$ $1/r$ Green's function}
L38: \subsection{Specify the mediator and write the quadratic EFT}
L39: In the static weak-field monopole sector, the minimal local mediator is a scalar field $\phi(\mathbf{x})$ coupled linearly to the source density. The most general rotationally invariant quadratic functional (Euclidean static limit of a Lorentzian EFT) is
L40: \begin{equation}\label{eq:S_static}
L41: S_{\rm stat}[\phi]
L42: \;=\;
L43: \int_{\mathbb{R}^3} d^3x\,
L44: \left[
L45: \frac{\kappa}{2}\,(\nabla \phi)^2 \;-\; \lambda\,\phi\,\rho_m(\mathbf{x})
L46: \right],
L47: \end{equation}
L48: with constants $\kappa>0$ and coupling $\lambda$.
L50: \subsection{Euler--Lagrange equation: Poisson form}
L51: Varying \eqref{eq:S_static}:
L52: \begin{align}
L53: \delta S_{\rm stat}
L54: &=
L55: \int d^3x\,
L56: \left[
L57: \kappa\,\nabla\phi\cdot\nabla(\delta\phi) \;-\; \lambda\,\rho_m\,\delta\phi
L58: \right]\\
L59: &=
L60: \int d^3x\,
L61: \left[
L62: -\kappa\,(\nabla^2\phi)\,\delta\phi \;-\; \lambda\,\rho_m\,\delta\phi
L63: \right]
L64: \quad (\text{integrate by parts, drop boundary term})
L65: \end{align}
L66: so stationarity for arbitrary $\delta\phi$ gives
L67: \begin{equation}\label{eq:Poisson_general}
L68: \kappa\,\nabla^2\phi(\mathbf{x}) \;=\; -\,\lambda\,\rho_m(\mathbf{x}).
L69: \end{equation}
L70: Define the ``Gauss-law charge density'' $\rho_Q := \rho_m$ and total charge
L71: \begin{equation}\label{eq:Q_def}
L72: Q \;:=\;\int \rho_Q\,d^3x \;=\; \int \rho_m\,d^3x \;=\; M,
L73: \end{equation}
L74: so the source is monopolar with charge $Q$.
L76: \subsection{Solve using the Green's function of $\nabla^2$ on $\mathbb{R}^3$}
L77: The Green's function $G(\mathbf{x})$ satisfying
L78: \begin{equation}
L79: \nabla^2 G(\mathbf{x}) = -4\pi\,\delta^{(3)}(\mathbf{x})
L80: \end{equation}
L81: is
L82: \begin{equation}\label{eq:Green_1overr}
L83: G(\mathbf{x}) = \frac{1}{\|\mathbf{x}\|}.
L84: \end{equation}
L85: This is a standard result: $G(r)=1/r$ is the unique (up to addition of harmonic functions) spherically symmetric fundamental solution on $\mathbb{R}^3$ \cite{Jackson1999,Arfken2013}.
L87: Convolving \eqref{eq:Poisson_general} with $G$ gives
L88: \begin{align}
L89: \phi(\mathbf{x})
L90: &=
L91: \frac{\lambda}{4\pi\kappa}\int d^3x'\,
L92: \frac{\rho_m(\mathbf{x}')}{\|\mathbf{x}-\mathbf{x}'\|}.
L93: \end{align}
L9
[...]

L135: \section{Derivation II: Identify the SST far-field carrier, compute $T_{ij}$, and extract the $1/r^2$ flux}
L136: \subsection{Which SST field carries far-field momentum flux?}
L137: In SST language, the long-range static field is taken to be carried by a \emph{clock/foliation} mode: a scalar that labels preferred-time hypersurfaces (``swirl-clock''). Denote this field by $T(x)$ and consider small perturbations about an inertial foliation:
L138: \begin{equation}
L139: T(x) = t + \tau(x),
L140: \end{equation}
L141: where $t$ is the operational background time coordinate and $\tau$ is a weak perturbation sourced by matter.
L143: At quadratic order, the most general Lorentz-invariant action for $\tau$ (ignoring higher derivatives) is
L144: \begin{equation}\label{eq:tau_Lorentz}
L145: S[\tau]
L146: =
L147: \int d^4x\,
L148: \left[
L149: \frac{\kappa}{2}\,\partial_\mu \tau\,\partial^\mu \tau
L150: -\lambda\,\tau\,\rho_m(\mathbf{x})
L151: \right],
L152: \end{equation}
L153: with $\rho_m$ treated as static, $\partial_t\rho_m=0$. The static sector of \eqref{eq:tau_Lorentz} reduces to \eqref{eq:S_static} with $\phi\equiv\tau$.
L155: \subsection{Compute the stress-energy tensor}
L156: From \eqref{eq:tau_Lorentz}, the symmetric stress-energy tensor (metric variation, or canonical symmetrized) for the free part is
L157: \begin{equation}\label{eq:Tmunu_tau}
L158: T_{\mu\nu}^{(\tau)}
L159: =
L160: \kappa\left(
L161: \partial_\mu \tau\,\partial_\nu \tau
L162: -\frac{1}{2}\eta_{\mu\nu}\,\partial_\alpha\tau\,\partial^\alpha\tau
L163: \right).
L164: \end{equation}
L165: In the static regime, $\partial_0\tau=0$, so $\partial_\alpha\tau\,\partial^\alpha\tau = -(\nabla\tau)^2$ and
L166: \begin{equation}\label{eq:Tij_static}
L167: T_{ij}^{(\tau)}
L168: =
L169: \kappa\left(
L170: \partial_i\tau\,\partial_j\tau
L171: -\frac{1}{2}\delta_{ij}(\nabla\tau)^2
L172: \right),
L173: \qquad
L174: T_{00}^{(\tau)}=\frac{\kappa}{2}(\nabla\tau)^2.
L175: \end{equation}
L177: \subsection{Monopole solution and the \emph{conserved} radial flux density}
L178: From Derivation I, for $r$ outside the source,
L179: \begin{equation}\label{eq:tau_mono}
L180: \tau(r) = \frac{\lambda Q}{4\pi\kappa}\,\frac{1}{r},
```
</details>

### 10. NLS delay-mode extension

**File:** `SST-70_Delay-Induced_mode_Selection_in_NLS.tex`  
**Lines:** 222-260;466-501

**Use:** Direct NLS+delay bridge; may help couple mode selection and NLS core analysis, but contains phenomenological mass ladder assumptions.

**Script / patch target:** `secondary support for test_pressure_mode_cutoff_delay_stability.py and NLS branch modeling.`

<details><summary>Source excerpt</summary>

```tex
L222: \section{Delay-Induced Mode Selection in the NLS}\label{sec:modes}
L223: % ============================================================
L225: \subsection{From Phase Oscillator to NLS}
L227: In \cite{Iskandarani2026AIP}, the minimal phase oscillator model:
L228: \[
L229: \dot{\phi}(t) = \omega_0 + \kappa\sin\!\left(\phi(t-\tau) - \phi(t)\right)
L230: \]
L231: was shown to produce discrete stable modes $\Omega_n \approx 2\pi n/\tau$, with
L232: selection governed by the stability criterion $1 + \kappa\tau\cos(\Omega\tau) > 0$.
L234: The full NLS framework appropriate for the incompressible SST fluid is:
L235: \[
L236: i\hbar\,\partial_t\Psi
L237: = -\frac{\hbar^2}{2m_*}\nabla^2\Psi + g|\Psi|^2\Psi,
L238: \]
L239: where $m_* = \rho_c V_\text{torus}$ is the effective vortex inertia and
L240: $g = F_{\circlearrowleft}^{\max} r_c^2 / \rho_c$ encodes the cavitation nonlinearity.
L242: Vortex solutions take the form:
L243: \[
L244: \Psi(r,\theta,t) = f(r)\,e^{in\theta}\,e^{-i\omega_n t},
L245: \]
L246: where $n \in \mathbb{Z}$ is the topological winding number and $f(r)$ is the
L247: Rankine radial profile (solid-body inside $r_c$, decaying outside).
L249: \subsection{Mode Frequencies and Mass Ladder}
L251: Substituting the vortex ansatz, the NLS eigenvalue condition becomes:
L252: \[
L253: \omega_n = n\cdot\frac{v_{\circlearrowleft}}{r_c} + \frac{g\rho_c}{\hbar}
L254: = n\,\omega_c + \delta\omega, \label{eq:ladder}
L255: \]
L256: which reproduces the discrete ladder of \cite{Iskandarani2026AIP} with spacing
L257: $\Delta\omega = 2\pi/\tau = \omega_c$. The integer $n$ is both the knot winding
L258: number and the phase-delay mode index.
L260: \subsection{Knot Topology as Mode Selector}

L466: \section{Falsifiable Predictions}\label{sec:falsifiers}
L467: % ============================================================
L469: SST makes the following falsifiable predictions beyond mass values:
L471: \begin{enumerate}
L472: \item \textbf{Knot-mass correspondence.} The masses of the $5_2$ and $6_1$ knots
L473: fix the quark mass ratio. SST predicts
L474: $m_d / m_u = V_{6_1}/V_{5_2} = 3.16396/2.82812 \approx 1.119$.
L475: Lattice QCD gives $m_d/m_u \approx 1.9$--$2.2$; the current SST value is a
L476: factor $\sim 2$ low. This discrepancy is a falsifier if it cannot be resolved
L477: by the inter-knot coupling corrections.
L479: \item \textbf{Swirl speed as universal constant.} The prediction
L480: $v_{\circlearrowleft} = c\alpha/2$ should appear as a limiting surface
L481: acoustic velocity in any solid-state vortex system. Independent experimental
L482: confirmation from SAW/MEMS devices \cite{Iskandarani2026AIP} is consistent
L483: at $< 0.1\%$.
L485: \item \textbf{Achiral knots decouple.} Knots with zero amphichirality
L486: (e.g.\ figure-eight $4_1$) should carry no electromagnetic coupling.
L487: This predicts a gravitationally interacting but electromagnetically inert
L488: dark sector. Its density is constrained by cosmological observations.
L490: \item \textbf{NLS discreteness in BEC vortices.} The delay-induced mass ladder
L491: should appear as anomalous discrete frequency shifts in Bose-Einstein
L492: condensate vortex rings under parametric driving at $f_c$.
L494: \item \textbf{Neutron mass correction.} Once the inter-knot gear coupling
L495: coefficient is computed analytically from knot linking numbers, the
L496: neutron mass prediction should improve to $< 1\%$. Failure to do so
L497: would challenge the knot-assignment for the down quark.
L498: \end{enumerate}
L500: % ============================================================
L501: \section{Discussion}
```
</details>

## Recommended next scripts

1. `derive_gp_core_profile_second_variation.py`: use SST-69 plus GP/NLS profile equations to test whether `w_perp=1` follows without tuning.

2. `test_pressure_mode_cutoff_delay_stability.py`: use SST-55/60/72 to test whether only the `l=0⊕l=1` pressure manifold survives stability selection.

3. `solve_one_cell_hodge_phase_hessian.py`: use SST-63 and SST-49 to replace the scalar capacity audit by a genuine Hodge/DEC one-cell Hessian.

4. `derive_pressure_self_duality_from_laplace_matching.py`: use SST-83 to derive or falsify equal inner/outer normalization in `A_chi`.

## Label advice

Use `[DERIVED]` for ropelength/geometric/Hodge/Green-function pieces already supported by source and calculation; use `[CANDIDATE / RESEARCH-TRACK]` for the full sub-ppm fine-structure closure until the upgraded scripts close the gates independently.
