# A058 — exact BLIND precommitted 32k subset

Source: v0.2.10's actual 2048-iteration run, 237 PASS and 34 `UNSUPPORTED_RUNTIME`. All 27 selections were made using the unmodified registered v0.2.10 selector before any 32768 outcomes.

| Group | Selected condition IDs | Rationale |
|---|---|---|
| Reference controls | C0000 C0001 C0002 C0003 C0005 | Five executable sector-on references |
| Activation control | C0006 | Separate OFF-versus-ON comparison |
| S0 | C0007 C0008 C0023 | Maximum response, extra diagnostic, local |
| S1 | C0040 C0056 C0064 | Zero endpoint, local, maximum response |
| S2 | C0073 C0090 C0105 | Zero endpoint, local, maximum response |
| S3 | C0106 C0123 C0135 | Zero endpoint, local, maximum response |
| S4 | C0139 C0156 C0171 | Zero endpoint, local, maximum response |
| S5 | C0172 C0189 C0199 | Maximum response, local, extra diagnostic |
| S7 | C0238 C0239 C0254 | Negative-control sweep across zero, low and local values |
| R4 / S6 | *Excluded* | Runtime unavailable; cannot be treated as no effect |

Important: The primary selection does **not** claim to establish a new reciprocal S0–S5 mathematical symmetry. If a dedicated exact reciprocal-pair test is desired, preregister it as a **separate experiment** rather than changing these locked 27 cases.
