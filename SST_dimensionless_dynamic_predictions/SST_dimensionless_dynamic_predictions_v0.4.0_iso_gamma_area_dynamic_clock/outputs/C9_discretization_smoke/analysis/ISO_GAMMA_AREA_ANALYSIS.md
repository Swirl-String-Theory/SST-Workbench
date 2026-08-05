# Iso-Γ/A dynamic-clock falsification analysis

## Verdict

`FALSIFIED_WITHIN_FROZEN_BUNDLE_MODEL`

The measured dynamic period is extracted from the evolving trefoil multipole phase. The prescribed value Γ/A is used only afterward to form the falsifier

\[
\mathcal Q_\Gamma=\frac{2(\Omega_{\rm bundle}^{\rm obs}-\Omega_{0}^{\rm obs})}{\Gamma/A}.
\]

The hypothesis predicts \(\mathcal Q_\Gamma=1\).

## Counts

- Input rows: 2
- Compatible rows: 2
- Certified T_dyn rows: 2
- Run-level falsifications: 2
- Run-level passes: 0
- Family-level falsifications: 1
- Family-level passes: 0

## Family ledger

| Family | Certified | mean Q | max |Q-1| | iso-family spread | Verdict |
|---|---:|---:|---:|---:|---|
| zeta_+128_r32_e0.05_rosenhead_trefoil | 2 | 0.0716364 | 0.928387 | 0 | FALSIFIED_WITHIN_MODEL |

## Interpretation boundary

A failure falsifies the claim only for the implemented frozen straight Rankine/discrete bundle model and the selected trefoil observable. Full 3-D mutual backreaction, tube bending and a proper-time identification remain separate open gates.
