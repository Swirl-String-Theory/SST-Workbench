# Trefoil_Balance_Point_Campaign_v0.2.4

Overlap-calibrated QHP panel extension for the K31 balance-zero program.

## Run

Place this folder next to the completed:

```text
Trefoil_Balance_Point_Campaign_v0.2.3_outputs.zip
```

Then run one line:

```bat
run_all.cmd
```

## Scientific structure

```text
import v0.2.3
-> verify all 20 historical i0 geometries are byte-identical
-> cold-start t=1.30,1.31,1.32 to 200k
-> overlap calibration gate
-> cold-start new t>1.32 states to 200k
-> verify extended panel brackets the zero at 200k
-> metric-neutral continue all 16 settings 200k->400k
-> analyze zero-track + separate ΔL/ΔRg
-> pack
```

## Extended panel

```text
[1.3, 1.31, 1.32, 1.325, 1.33, 1.335, 1.34, 1.345, 1.35, 1.355, 1.36, 1.365, 1.37, 1.375, 1.38, 1.4]
```

Fine spacing is 0.005 from 1.32 through 1.38, with t=1.40 as an upper sentinel.

## Important fail-closed behavior

The expensive new extension does **not** start until the historical overlap gate
passes. If regenerating t=1.30/1.31/1.32 from the frozen common i0 does not reproduce
the historical 200k metrics/zero, the campaign stops.

## Runtime/restart behavior

The runner prints a heartbeat every 60 seconds during long KnotPlot runs.

Completed settings are automatically skipped on a rerun. If Windows or KnotPlot is
interrupted halfway through one setting, only that incomplete setting is restarted;
already completed settings are preserved.

Based on the preceding campaign, full sequential wall time is likely on the order
of 12–14 hours, depending on KnotPlot runtime.

## 400k planning forecast

The preregistered planning-only estimate is around:

```text
t*(400k) ~ 1.346404
```

The actual result may settle earlier, migrate differently, or leave the extended
panel; none of those outcomes is forced by the forecast.
