# Surface-tension sensitivity (hypothetical, not a measurement)

Camilotto explicitly neglects capillarity in the published analytical sloshing model (PDF pp. 39–40). Accordingly, the **source reproduction** configuration sets `surface_tension_N_m=0.0`. This is an idealization, not a property measurement of the soluble-coffee solution.

For illustration **only**, an external standard-water illustrative value `sigma=0.072 N/m` at `rho=998 kg/m³`, `g=9.81 m/s²` gives the following comparison using the same geometry. This is NOT the published liquid's verified surface tension and must NOT overwrite the source reproduction configuration.

| Mode | Source-reproduction frequency [Hz] (sigma=0) | Illustrative frequency [Hz] (sigma=.072) | Relative difference |
|---:|---:|---:|---:|
| 0 | 3.01892 | 3.03599 | 0.57% |
| 1 | 5.41038 | 5.67979 | 4.98% |
| 2 | 6.98505 | 7.91356 | 13.29% |
| 3 | 8.26482 | 10.30856 | 24.73% |

**Implication:** modes 2 and 3 can be appreciably shifted by capillarity in an 8-cm vessel. If the pure-gravity Euler prediction deviates, do not retrofit an unknown surface tension using the held-out wave response. Seek independent fluid-property characterization, or report a predeclared sensitivity envelope with the model assumption explicit.
