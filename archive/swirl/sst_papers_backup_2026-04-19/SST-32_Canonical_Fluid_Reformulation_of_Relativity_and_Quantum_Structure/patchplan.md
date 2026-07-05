# Patch Plan: Consolidate Self-Citations, Add Macros, Normalize Keys

## 0) Safety first

-   Create a backup: duplicate the `.tex` file to `SST_main_backup.tex`.

-   Ensure the `.bib` file(s) are present and compile once to confirm baseline.


## 1) Insert helper macros in the preamble

**Find:** the block with other `\newcommand` definitions in the preamble (after packages, before `\begin{document}`).

**Insert exactly (once):**

```latex
% --- SST citation helpers ---
\newcommand{\SSTbundle}{Refs.~\cite{sstCanon,EM_G,chiralSwirl,sstLagrangian}}
\newcommand{\Sref}[1]{Sec.~\ref{#1}}
\newcommand{\Appref}[1]{App.~\ref{#1}}
% One-line provenance footnote (use sparingly)
\newcommand{\provnote}{\footnote{Derivations and identities used here are collected in \SSTbundle; explicit Lagrangian densities in \Appref{app:fullL}.}}
```

**Acceptance check:** No duplicate macro names; file compiles.

## 2) Normalize bibliography keys and typos

Perform exact global replacements (case-sensitive):

1.  `sst-Lagrangian` → `sstLagrangian`

2.  `sstLagrangian4` → `sstLagrangian` *(if this is not a distinct paper; otherwise add a distinct bib entry and skip this replace)*

3.  In EM analog line, fix punctuation:

    -   Replace:  
        `BECs~\cite{BarceloLiberatiVisser2011,SchererWeilerNeelyAnderson2007}. or type-II`  
        with:  
        `BECs~\cite{BarceloLiberatiVisser2011,SchererWeilerNeelyAnderson2007} or type-II`


**Acceptance check:** No remaining instances of the old keys; citations render.

## 3) Add “Author’s note” to Introduction once

**Locate:** end of `\section{Introduction}` (just before the next `\section`).

**Insert:**

```latex
\paragraph*{Author’s note.}
To reduce citation clutter, references to prior SST work are grouped at the start of each section via \SSTbundle, with detailed formulae collected in \Appref{app:fullL}. External anchors are cited where they directly constrain or motivate assumptions.
```

## 4) Convert dense self-cites to bundle or internal refs

### 4A) Introduction, first paragraph

**Replace** the current footnote at the end of the first paragraph with:

```latex
\provnote
```

### 4B) Core Postulates section lead line

**Replace**:

```css
Core postulates follow from SST Canon v0.5.10~\cite{sstCanon}, with corresponding derivations in~\cite{sstLagrangian}.
```

**with**:

```csharp
Core postulates follow from the SST canon and Lagrangian framework (\SSTbundle).
```

### 4C) Core Postulates bullets

-   **Remove** trailing self-cites `~\cite{sstCanon}` or `~\cite{sstLagrangian}` inside the 6 bullets.

-   **Retain** external anchors; e.g. keep `\cite{Onsager1949}` for quantized circulation.


### 4D) Lagrangian subsections (three intros)

At the *end* of each of these three subsections:

-   “Preferred foliation…”

-   “Two-form vorticity…”

-   “Emergent gauge…”  
    **Append once** (if not already present):


```css
(Technical details and parameter choices: \SSTbundle.)
```

Then **remove** any inline `\cite{sstLagrangian}` / `\cite{sstCanon}` in the body of those three subsections.

### 4E) Lagrangian “Summary of the Canonical Lagrangian”

Inside the itemize list:

-   **Clock / Two-form / Emergent gauge**: remove your self-cites.

-   **Matter**: **keep** external anchors `\cite{Skyrme1962,MantonSutcliffe2004}`; remove your self-cite.

-   **Bridge term**: **keep** `\cite{EM_G}`.


### 4F) Gravity section

-   Keep **one** self-cite at the section start (`\cite{chiralSwirl}`).

-   In the Euler/pressure paragraph, replace `~\cite{sstCanon}` with:

    ```css
    (\Appref{app:fullL})
    ```

-   In the redshift paragraph, replace `~\cite{sstCanon}` with:

    ```rust
    (see Eq.~\ref{eq:swirlclock})
    ```


### 4G) EM section

-   Keep **one** `\cite{EM_G}` at the section start.

-   Elsewhere in the section, **remove** repeated `\cite{EM_G}` and rely on internal refs: `Fig.~\ref{fig:swirl_em_causal}`, `Eq.~\ref{eq:modfaraday}`, `\Sref{sec:falsifiability}`.


### 4H) Chirality section

-   Keep external anchors (`\cite{Nahon2020}`, `\cite{Beaulieu2018}`, etc.).

-   Replace repeated self-cites with a **single** closing sentence at the end of the section:

    ```css
    (Background and modeling choices: \SSTbundle.)
    ```


### 4I) Quantization section

-   Keep `\cite{Kauffman2001}` (external).

-   Remove repeated `\cite{sstCanon,sstLagrangian}` mid-paragraphs; add at the **end** of the section:

    ```css
    Further algebraic details are summarized in \SSTbundle.
    ```


### 4J) Experimental section

-   Keep `\cite{Hossenfelder2018}` and **one** `\cite{EM_G}`.

-   In platform list, keep external anchors; remove repeated `\cite{EM_G}`.


### 4K) Comparison section

-   In the GR paragraph, replace the trailing self-cite with internal refs:

    ```css
    (see \Sref{sec:intro} and \Sref{sec:gravity})
    ```


## 5) Apply targeted global regex to strip residual self-cites

Run these **in order**, global, case-sensitive. (Use a regex engine that supports lookarounds.)

1.  Remove bare single self-cites not followed by letters/digits:

    -   Find: `~\\cite\{(?:sstCanon|EM_G|chiralSwirl|sstLagrangian)\}`

    -   Replace: *(empty)*

2.  Preserve external cites: **Do not** match keys not in the set above.

3.  Compact doubled spaces left behind:

    -   Find: `[ ]{2,}`

    -   Replace:


**Acceptance check:** No orphan punctuation like `,,` or `).` with extra spaces.

## 6) Insert the provenance footnote only once per major section (optional)

If you want a footnote at the start of a few key sections (e.g., Lagrangian, EM), add `\provnote` at the **end of the first paragraph** in those sections. Do **not** repeat within the same section.

## 7) Internal reference integrity check

Verify that all referenced labels exist:

-   Sections / Appendices:

    -   `\ref{sec:intro}`, `\ref{sec:lagrangian}`, `\ref{sec:gravity}`, `\ref{sec:em}`, `\ref{sec:chirality}`, `\ref{sec:quantization}`, `\ref{sec:falsifiability}`, `\ref{sec:comparison}`, `\ref{sec:conclusion}`, `\ref{sec:swirlbraid}`, `\ref{app:fullL}`

-   Equations / Figures / Tables:

    -   `\ref{eq:swirlclock}`, `\ref{eq:L_summary}`, `\ref{eq:masslaw}`, `\ref{eq:modfaraday}`, `\ref{eq:gswirl}`, `\ref{fig:swirl_em_causal}`, `\ref{fig:swirl_em_units}`, `\ref{tab:knotetable}`


If any are missing, add a `\label{...}` at the corresponding environment.

## 8) Build and lint

-   Compile with: `pdflatex → bibtex → pdflatex → pdflatex`.

-   Ensure there are **no** “Citation ‘…’ undefined” and **no** “Label(s) may have changed” after the final run.

-   Scan the PDF quickly: check that each section retains **one** self-cite (where intended) and external anchors remain.


## 9) Keep/Drop matrix (fast policy for the assistant)

| Section | Keep self-cite? | Which one | Notes |
| --- | --- | --- | --- |
| Introduction | **No** (use `\provnote`) | — | External Susskind/Hossenfelder stay. |
| Core Postulates | **No** inside bullets | — | Use bundle once in section lead line. |
| Lagrangian | **Yes** (once) | `sstLagrangian` | Plus external Skyrme/Manton where relevant. |
| Gravity | **Yes** (once) | `chiralSwirl` | Use internal refs elsewhere. |
| EM (Bridge) | **Yes** (once) | `EM_G` | Then internal refs to fig/eq/predictions. |
| Chirality | **Optional** | `sstAttosecondPhotoionization` OR bundle line at end | Keep external experimental anchors. |
| Quantization | **Optional** | Bundle at end | Keep Kauffman external. |
| Experimental | **Yes** (once) | `EM_G` | Keep Hossenfelder and experimental externals. |
| Comparison | **No** | — | Use internal refs to Intro/Gravity. |

## 10) Minimal test edits (copy/paste ready)

-   **Intro paragraph end:** append `\provnote`

-   **Core Postulates lead:** replace with `(\SSTbundle)` form.

-   **Gravity Euler sentence:** append `(\Appref{app:fullL})`

-   **Redshift sentence:** replace cite with `(see Eq.~\ref{eq:swirlclock})`

-   **EM “Identification with flux quantum” end:** append `(\Sref{sec:falsifiability})`

-   **Comparison/GR end:** append `(see \Sref{sec:intro} and \Sref{sec:gravity})`


---