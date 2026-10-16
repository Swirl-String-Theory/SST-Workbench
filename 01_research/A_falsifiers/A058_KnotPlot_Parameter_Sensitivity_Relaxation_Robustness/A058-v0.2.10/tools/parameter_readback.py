"""Anonymous getter qualification at KnotPlot's 6-place DISPLAY precision.

A passing readback does NOT establish exact internal FP64 assignment.
"""
from __future__ import annotations
import math

def qualify_numeric(expected, observed, *, decimals=6):
    if isinstance(observed,bool) or not isinstance(observed,(int,float)):
        return {'pass':False,'evidence':'MISSING_NUMERIC_GETTER','abs_error':None,'display_step':10.0**-decimals}
    expected=float(expected); observed=float(observed)
    if not (math.isfinite(expected) and math.isfinite(observed)):
        return {'pass':False,'evidence':'NONFINITE_GETTER','abs_error':None,'display_step':10.0**-decimals}
    unit=10.0**(-int(decimals));delta=abs(expected-observed)
    # Half a decimal display quantum plus floating point representation slack.
    ok=delta<=0.5*unit+max(1e-12,2.0*math.ulp(max(abs(expected),abs(observed),1.0)))
    status=('ROUNDED_GETTER_QUANTIZATION_LIMITED' if abs(expected)<unit else 'ROUNDED_GETTER') if ok else 'GETTER_MISMATCH'
    return {'pass':bool(ok),'evidence':status,'abs_error':delta,'display_step':unit,'display_quantum_half_width':0.5*unit}

def state_getter_name(axis):
    return axis.get('getter_parameter',axis['parameter'])

def state_switch_getter_name(sector,resolved):
    return sector.get('getter_switch',resolved)
