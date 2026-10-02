# Sutcliffe–HSS feasibility gate v0.1.0

This package executes the five pre-project checks for a renormalized non-local
extension of the Harland–Speight–Sutcliffe elastic-rod approximation:

1. inventory machine-readable centreline/framing data;
2. define a near-diagonal subtraction;
3. calculate and validate the circular value analytically;
4. test the local rank of the \(C\)-\(g\) calibration on \(Q=1,2\);
5. assess independent topology-sector relaxation.

## Scope

This is an **alpha-free Hopf-soliton feasibility study**. It does not calibrate
or validate an SST electron functional.

## Run

```bash
python run_all.py
```

Dependencies:

```text
numpy
scipy
```

## Main result

- Publicly reconstructible benchmark geometry is currently limited to the
  analytic axial circles \(Q=1,2\). No attached machine-readable final
  centreline/framing files were located for the 2007 Skyrme–Faddeev catalogue
  or the 2011 HSS non-axial rod minima.
- The straight-filament subtraction is mathematically well defined and the
  circle has a closed elliptic-integral expression.
- \(Q=2\) energy alone has rank one for two parameters.
- Adding the \(Q=2\) length ratio can make the local Jacobian rank two, but the
  result is normalization- and active-constraint-sensitive.
- Independent rod-sector relaxation is technically feasible and was already
  demonstrated in HSS for axial, buckled, linked and trefoil sectors. It cannot
  reproduce topology-changing field relaxation without reconnection.
