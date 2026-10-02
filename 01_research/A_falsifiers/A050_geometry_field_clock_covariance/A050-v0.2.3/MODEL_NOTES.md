# MODEL NOTES — v0.2.3

The evolution law and modal diagnostics are inherited from v0.2.2 without target-value tuning. The local-basin directions are smooth transverse Bishop-frame Fourier mixtures spanning modes 2 through 8. Their complex coefficients are independent Gaussian draws weighted by 1/m; all twelve directions are generated and hash-locked before the scientific run.

The m=3 overlap of each direction is recorded only as a diagnostic covariate. It is not used to accept, reject, replace, or weight a direction.

This is an explicitly outcome-guided follow-up: G0002 and branch m=3 were selected because of the revealed v0.2.2 result. Consequently, v0.2.3 is suitable for mechanism localization and experiment design, not for independent confirmation.

Rigid translations and infinitesimal rotations are removed from each direction before RMS normalization, so the nominal epsilon tracks Kabsch-aligned shape displacement rather than coordinate-frame motion.
