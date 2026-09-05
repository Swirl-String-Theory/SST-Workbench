# VALIDATION — v0.1.3

## Recovered target syntax

Direct target logs prove that the old commands `charge`, `hooke`, `power`,
`timeincr` are unknown and `nbeads 300` is obsolete. The user's working
`build_knot_0.1.kpc` supplies the accepted literal forms used here.

## Release checks

- Frozen seed manifest: byte-identical to v0.1.2
- Seed count: 38
- Synthetic seed safety+uniqueness selftest: PASS
- `refine nbeads 300`: required
- `nbeads 300`: forbidden
- `charge`, `hooke`, `power`, `timeincr`: forbidden
- `alex`: forbidden
- strict KPC command whitelist: enabled
- parent directories for save/coords: created before KnotPlot launch
