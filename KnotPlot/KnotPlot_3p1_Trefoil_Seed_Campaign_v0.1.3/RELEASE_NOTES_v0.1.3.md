# v0.1.3 — literal KnotPlot syntax recovery

This release is a methodological correction based on two direct sources:

1. the user's known-working `build_knot_0.1.kpc`;
2. target KnotPlot console logs from the earlier MultiDynamics campaign.

The target logs prove:

```text
*** this command is obsolete, use `refine nbeads' instead
*** unknown command: `charge'
*** unknown command: `hooke'
*** unknown command: `power'
*** unknown command: `timeincr'
```

Therefore v0.1.3 removes those four unknown commands completely and replaces
obsolete `nbeads 300` by the literal working form:

```text
refine nbeads 300
```

The fixed relaxation KPC is intentionally restricted to the user's known-good
forms:

```text
reset all
load ...
refine nbeads 300
mode cb

centre
fitto mindist 1.05

collision fast
close = 1.0
max-dr = 0.01

mechforce = on
elecforce = on
bendforce = on
bencon = 1.0

stusplit = 0
dstep = 1

bradius = 0.1
cradius = 0.05

energy model MD
energy
```

No parameter aliases are inferred.

A new `validate_kpc_syntax.py` hard-fails if `nbeads`, `charge`, `hooke`,
`power`, `timeincr`, `alex`, or any unregistered command appears in a generated
production KPC.

## Scientific consequence for the previous matrix

The old parameter-labelled sweeps for `charge`, `hooke`, `power` and `timeincr`
were not actually applying those values on the target KnotPlot executable.
This is a plausible direct explanation for the large blocks of byte-identical
end geometries. Those labels must not be interpreted as successful parameter
variations.
