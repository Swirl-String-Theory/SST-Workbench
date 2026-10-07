# PKLSA / dynamic-provider integration

A056 v0.2.1 is prepared for the source-native E010/PKLSA v0.3.x evidence chain, but it does not pretend that static PKLSA geometry is time-dependent data.

The intended real chain is

\[
\text{E010 carrier}
\rightarrow
\text{Euler/finite-core perturbation provider}
\rightarrow
\{t,s,\varphi(t,s),R(t)\}
\rightarrow
\text{A056 blind scoring}.
\]

The dynamic provider must freeze the definition of \(\varphi\) before model selection. Examples of admissible identifiers are a material-frame torsion phase or a Kelvin-mode phase, but the identifier alone is not enough: the producing solver and perturbation protocol must also be hashed/versioned.

`tools/ingest_pklsa_dynamic_provider.py` is fail-closed. It will not accept an NPZ without the metadata required by `A056-DYNAMIC-PROVIDER-3`.

This is intentionally stricter than v0.1.0, where the dynamic NPZ contract was minimal.
