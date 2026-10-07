# Framework v1.0.2 DD32 / FP32x2 backend note

The external SYCL worker includes an experimental double-single arithmetic smoke.  A scalar is represented as two FP32 values,

\[
x \approx x_{\mathrm{hi}} + x_{\mathrm{lo}}.
\]

Addition uses compensated `TwoSum`/`QuickTwoSum`; multiplication uses an FMA product residual.  The worker is compiled with precise floating-point semantics to avoid reassociation invalidating compensated transforms.

The A056 package uses DD32 only as a framework/backend validation lane.  CPU/Python FP64 is the reference and C++ FP64 is the confirmatory backend.  DD32 is never labeled IEEE FP64 and cannot independently promote G4 or any later physics gate.

The local DD32 arithmetic smoke requires

\[
\varepsilon_{\mathrm{DD32}}\le 10^{-8}
\]

and at least a factor 20 error reduction relative to ordinary FP32 for the same cancellation-sensitive test.

The worker executable is content-addressed by source, flags, and compiler fingerprint, preventing a running worker from being overwritten on Windows.

## References

T. J. Dekker, 1971, "A floating-point technique for extending the available precision," *Numerische Mathematik* **18**, 224--242. DOI: 10.1007/BF01397083.

G. Da Graça and D. Defour, 2006, "Implementation of float-float operators on graphics hardware," arXiv:cs/0603115. https://arxiv.org/abs/cs/0603115
