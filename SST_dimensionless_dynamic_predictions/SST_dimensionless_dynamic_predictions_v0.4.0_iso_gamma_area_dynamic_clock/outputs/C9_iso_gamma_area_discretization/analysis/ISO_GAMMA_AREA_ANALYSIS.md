# Iso-Γ/A dynamic-clock falsification analysis

## Verdict

`FALSIFIED_WITHIN_FROZEN_BUNDLE_MODEL`

The measured dynamic period is extracted from the evolving trefoil multipole phase. The prescribed value Γ/A is used only afterward to form the falsifier

\[
\mathcal Q_\Gamma=\frac{2(\Omega_{\rm bundle}^{\rm obs}-\Omega_{0}^{\rm obs})}{\Gamma/A}.
\]

The hypothesis predicts \(\mathcal Q_\Gamma=1\).

## Counts

- Input rows: 32
- Compatible rows: 32
- Certified T_dyn rows: 32
- Run-level falsifications: 32
- Run-level passes: 0
- Family-level falsifications: 4
- Family-level passes: 0

## Family ledger

| Family | Certified | mean Q | max |Q-1| | iso-family spread | Verdict |
|---|---:|---:|---:|---:|---|
| zeta_+128_r64_e0.05_rosenhead_trefoil | 8 | 0.0453644 | 0.978896 | 0.048505 | FALSIFIED_WITHIN_MODEL |
| zeta_+128_r96_e0.05_rosenhead_trefoil | 8 | 0.0452505 | 0.978864 | 0.0482159 | FALSIFIED_WITHIN_MODEL |
| zeta_-128_r64_e0.05_rosenhead_trefoil | 8 | 0.0437666 | 0.979048 | 0.0456289 | FALSIFIED_WITHIN_MODEL |
| zeta_-128_r96_e0.05_rosenhead_trefoil | 8 | 0.0434052 | 0.979104 | 0.0450182 | FALSIFIED_WITHIN_MODEL |

## Interpretation boundary

A failure falsifies the claim only for the implemented frozen straight Rankine/discrete bundle model and the selected trefoil observable. Full 3-D mutual backreaction, tube bending and a proper-time identification remain separate open gates.
