# SST FFS Research Package v2

This is the corrected package for the fractional-filament-sea / attachment-barrier workflow.

## Critical fix in v2

The original package used:

```text
5:2:1
```

for \(5_2\). That ID does **not** exist in the included Brian Gilbert `ideal.txt`.

The actual 5-crossing entries are:

```text
5:1:1  Conway="5"    L=23.598564
5:1:2  Conway="3 2"  L=24.734148
```

Therefore the corrected SST light-quark IDs are:

\[
u \longleftrightarrow 5_2 \longleftrightarrow \texttt{5:1:2},
\]

\[
d \longleftrightarrow 6_1 \longleftrightarrow \texttt{6:1:1}.
\]

The trefoil remains:

\[
e^- \text{ sector} \longleftrightarrow 3_1 \longleftrightarrow \texttt{3:1:1}.
\]

The deprecated assignments remain deprecated:

\[
6_2,\;7_4
\]

should not be used as light-quark anchors.

## Quick check available IDs

```bat
python scripts\list_ideal_ids.py data\ideal.txt --prefix 5:
```

or:

```bash
python scripts/list_ideal_ids.py data/ideal.txt --prefix "5:"
```

Expected output:

```text
Id,Conway,L,D
5:1:1,5,23.598564, 1.000000
5:1:2,3 2,24.734148, 1.000000
# rows=2
```

## Install

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

`SSTcore` is optional. Without SSTcore the scripts use canonical fallback constants:

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\,{\rm m\,s^{-1}},
\quad
r_c=1.40897017\times10^{-15}\,{\rm m},
\quad
\rho_{\!f}=7.0\times10^{-7}\,{\rm kg\,m^{-3}},
\quad
\Gamma_0=9.68361918\times10^{-9}\,{\rm m^2\,s^{-1}}.
\]

## Run all

Windows:

```bat
run_all_windows.bat
```

Linux/macOS:

```bash
./run_all_unix.sh
```

This runs:

1. \(G^{(1)}\) synthetic demo fit,
2. analytic Rosetta spectrum,
3. ideal-knot projection for:
   \[
   3{:}1{:}1,\quad 5{:}1{:}2,\quad 6{:}1{:}1,
   \]
4. attachment-threshold scan for all three.

Outputs go to:

```text
results/
```

## Extended convergence scan

Windows:

```bat
run_extended_windows.bat
```

Linux/macOS:

```bash
./run_extended_unix.sh
```

This tests:

\[
N\in\{2048,4096,8192\},
\qquad
\text{smooth width}\in\{5,9,15\}.
\]

Outputs go to:

```text
results_ext/
```

## Core equations

Fractional top-hat sector:

\[
\vartheta_\ell(q)=\frac{1}{\ell}\Theta(\ell q_0-|q|).
\]

Line density:

\[
\mathcal{N}_{\rm line}=\frac{q_0}{\pi}.
\]

Second line moment:

\[
M_2^{(\ell)}=\frac{\ell^2q_0^3}{3\pi}.
\]

Normalized second spectral moment:

\[
\langle q^2\rangle_\ell=\frac{M_2^{(\ell)}}{\mathcal{N}_{\rm line}}
=\frac{\ell^2q_0^2}{3}.
\]

Attachment barrier:

\[
\mathcal{B}_\ell
=
\frac{\langle q^2\rangle_\ell}{q_{\rm crit}^2}
=
\frac{\ell^2(q_0a_{\rm crit})^2}{3}.
\]

Default cutoff:

\[
a_{\rm crit}=r_c,
\qquad
q_{\rm crit}=r_c^{-1}.
\]

Actual spectrum diagnostic from script 02:

\[
u(s)=e^{i\varphi(s)},
\qquad
P(q)=|\mathcal{F}\{u(s)-\langle u\rangle\}|^2.
\]

Contained power:

\[
F_\ell=
\frac{\sum_{|q|\le \ell q_0}P(q)}{\sum_qP(q)}.
\]

Effective support:

\[
\ell_{\rm eff,95}=\frac{q_{95}}{q_0}.
\]

## Interpretation

The current research-track statement is:

\[
\text{fermion-like SST sector}
=
\text{chiral knot or confined chiral twist subknot}
+
\text{half-exchange/framing}
+
\text{supercritical torsion/R-phase attachment barrier}.
\]

Corrected light-quark taxonomy:

\[
p\sim uud\sim 5_2+5_2+6_1,
\]

\[
n\sim udd\sim 5_2+6_1+6_1.
\]

## Files

```text
scripts/sst_ffs_00_reproduce_g1.py
scripts/sst_ffs_01_rosetta_spectrum.py
scripts/sst_ffs_02_filament_projection.py
scripts/sst_ffs_02_filament_projection_ideal.py
scripts/sst_ffs_03_attachment_threshold_scan.py
scripts/list_ideal_ids.py
data/ideal.txt
docs/research_track_canon_block.tex
```
