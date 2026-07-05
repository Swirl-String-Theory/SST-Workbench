# SST–VAM LaTeX Assistant Guide (Rosetta Edition)

> **Scope.** Use this guide to format, translate, and validate LaTeX manuscripts across **Swirl-String Theory (SST)** and the legacy **Vortex Æther Model (VAM)**. It enforces one consistent mathematical core while letting prose switch between frameworks.

---

## How to Use This Guide

- Apply **Structural Cleanup** first.
- Choose a **Rosetta Mode** (SST / VAM / Mixed) for **prose**; **mathematics is invariant** across modes.
- Convert plain text math → AMS-LaTeX; attach the **Macro Prelude** for copy-ready LaTeX.
- For each edited/added equation, perform: **(i) dimensional check, (ii) known-limit check, (iii) numerical check** with canonical constants.
- Keep citations; add BibTeX for all non-original equations/ideas.

---

## Rosetta Modes (prose only)

- **SST mode (default external):**
  - Prefer “foliation”, “swirl string(s)”, “swirl velocity”.
  - Avoid “æther/Æther” except in historical titles/citations.
- **VAM mode (legacy/internal):**
  - Use “Æther/æther”, “vortex”, “vortex line(s)”.
- **Mixed mode (transitional):**
  - First mention: “Swirl-String Theory (SST; legacy Vortex Æther Model, VAM)”.
  - Thereafter, use SST terms; legacy words only when quoting/cross-referencing.

> **Rule:** **Math notation is framework-invariant.** Always use the SST house symbols in equations:  
> \(\rho_{\!f}, \rho_{\!E}, \rho_{\!m}, \rho_{\text{core}}, r_c, \mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\).

---

## Canonical Constants & Identities (validation set)

**Numerical values (SI):**
- \(\lVert \mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\rVert\big|_{r=r_c} = 1.09384563\times10^{6}\ \text{m s}^{-1}\)
- \(r_c = 1.40897017\times10^{-15}\ \text{m}\)
- \(\rho_{\text{core}} = 3.8934358266918687\times10^{18}\ \text{kg m}^{-3}\)
- \(\rho_{\!f}^{\text{(bg)}} = 7.0\times10^{-7}\ \text{kg m}^{-3}\)
- \(F_{\text{swirl}}^{\max} = 29.053507\ \text{N}\)
- \(F_{\text{gr}}^{\max} = 3.02563\times10^{43}\ \text{N}\)

**Canonical equalities (SST form; same physics for VAM):**

$$
\rho_{\!E}=\tfrac12\,\rho_{\!f}\,\lVert\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\rVert^{2},\qquad
\rho_{\!m}=\frac{\rho_{\!E}}{c^{2}},\qquad
K=\frac{\rho_{\text{core}}\,r_c}{\lVert\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\rVert\big|_{r=r_c}},\qquad
\rho_{\!f}=K\,\Omega.
$$

**Chronos–Kelvin invariant** (incompressible, inviscid, barotropic, no reconnection):

$$
\frac{D}{Dt}\!\left(R^{2}\omega\right)=0.
$$

**Dimensional checks:**  
\([\rho_{\!f}]=\text{kg m}^{-3}\), \([\rho_{\!E}]=\text{J m}^{-3}\), \([\rho_{\!m}]=\text{kg m}^{-3}\), \([\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}]=\text{m s}^{-1}\), \([K]=\text{kg m}^{-3}\text{s}\), \([\Omega]=\text{s}^{-1}\).

---

## Macro Prelude (paste into copy-ready LaTeX outputs)

> Include this in deliverables so macros compile locally. `\providecommand` avoids double-defs.

~~~latex
%=== SST/VAM Rosetta Macro Prelude ===
\usepackage{amsmath,amssymb}
\providecommand{\rc}{r_c}
\providecommand{\rhof}{\rho_{\!f}}
\providecommand{\rhoE}{\rho_{\!E}}
\providecommand{\rhoM}{\rho_{\!m}}
\providecommand{\rhocore}{\rho_{\text{core}}}
\providecommand{\vswirl}{\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}}
\providecommand{\vnorm}{\lVert \mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\rVert}
\providecommand{\aetext}{\text{\ae}} % for legacy æ in math subscripts
% \begin{equation}\label{eq:<descriptive-label>} ... \end{equation}
~~~

---

## Translation Tables (Rosetta)

### Narrative terms
| VAM legacy phrase | SST phrase (house) | Notes |
|---|---|---|
| “Æther/æther” | foliation / medium | Keep legacy only in titles/citations. |
| vortex line(s) | swirl string(s) | Object label; math unchanged. |
| æther time | absolute (foliation) time | Global time parameter. |
| Kelvin’s vortex theorem | Kelvin circulation theorem | Same equation; SST wording. |

### Symbols & fields (shared math)
| Concept | Symbol | Units | Note |
|---|---|---|---|
| effective density | \(\rho_{\!f}\) | kg m\(^{-3}\) | Coarse-grained |
| energy density | \(\rho_{\!E}=\tfrac12\rho_{\!f}\vnorm^{2}\) | J m\(^{-3}\) | Local relation |
| mass-equiv. density | \(\rho_{\!m}=\rho_{\!E}/c^{2}\) | kg m\(^{-3}\) | For mass accounting |
| core density | \(\rho_{\text{core}}\) | kg m\(^{-3}\) | Calibration |
| swirl velocity | \(\vswirl\), \(\vnorm\) | m s\(^{-1}\) | Field & magnitude |
| coarse-grain coeff. | \(K=(\rho_{\text{core}}\,r_c)/\vnorm|_{r=r_c}\) | kg m\(^{-3}\) s | With \(\rho_{\!f}=K\Omega\) |
| leaf rate | \(\Omega\) | s\(^{-1}\) | Coarse rate |

---

## Expectations for Converted LaTeX

- Use canonical constants; verify numerically.
- Add BibTeX for all non-original content.
- Use **SST macros** in equations; prose switches via **Rosetta Mode**.
- **Do not overwrite** original `.tex`; deliver clean snippets or new files with comments.

---

## Equation & Citation Standards

- Packages: `amsmath, amssymb` (add `amsthm` if needed).
- Label: `\label{eq:<descriptive-label>}`, reference with `\eqref{...}`.
- Cite with `\cite{key}`; `.bib` needs author, title, venue, year, DOI/permalink.

---

## Figure/Table Conventions

- Figures: descriptive captions; prefer vector; consistent units.
- Tables: consistent `tabular` style with headers. Choose one caption style per manuscript.

---

## Structural Cleanup (run before translation)

### Remove redundant commands
~~~latex
\maketitle
% Removed duplicate \maketitle
~~~

### Normalize `itemize` blocks
- No blank lines between `\item`s.
- One newline between items; 2–4 spaces indentation is fine.

**Regex helper (collapse blank lines before items):**  
Find: `\n\s*\\item` → Replace: `\n\\item`

### Unicode & spacing fixes
- Replace Unicode math with LaTeX: `∣→|`, `∇→\nabla`, `…→\ldots`.
- Escape percent in text: `% → \%`.

---

## Æ/æ Handling (math vs prose, mode-aware)

- **Math subscripts (legacy mentions):** use `\text{\ae}` inside math, e.g., `\rho_{\text{\ae}}`.
- **SST prose:** avoid “æther/Æther”; use “foliation/medium”.
- **VAM prose:** “Vortex Æther Model (VAM)” capitalization is canonical.
- **Section titles:** in SST mode, prefer neutral titles; if quoting legacy, retain capitalization.

**Regex quick-fix (only when match is in math):**  
Find: `(?<=\{)æ(?=\})` → Replace: `\\text{\\ae}`

---

## Duplicate / Mixed Equation Cleanup

**Keep only the AMS-LaTeX form**; remove plain-text duplicates.

**Before:**  
`LFmax=Λ(∣∇pæ∣ρæ−Fmax), L_{F_{\text{max}}} = \Lambda\Big(\frac{|\nabla p_{æ}|}{\rho_{æ}} - F_{\text{max}}\Big)~,`

**After (scalable delimiters & labe**
