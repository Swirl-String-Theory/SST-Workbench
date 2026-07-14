#!/usr/bin/env python3
"""Extract the WebGL-free physics core from the vortexring-lab monolith
into a CommonJS module for node regression testing."""
import re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'work.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'core.cjs'

html = open(SRC, encoding='utf-8').read()
m = re.search(r'"use strict";(.*)</script>', html, re.S)
if not m:
    sys.exit('main script block not found')
js = m.group(1)

def scan_end(start, stop_at_semicolon):
    depth, j = 0, start
    in_str = None
    while j < len(js):
        c = js[j]
        if in_str:
            if c == '\\':
                j += 2
                continue
            if c == in_str:
                in_str = None
        elif c == '/' and j+1 < len(js) and js[j+1] == '/':
            j = js.index('\n', j)
        elif c == '/' and j+1 < len(js) and js[j+1] == '*':
            j = js.index('*/', j) + 1
        elif c in '"\'`':
            in_str = c
        elif c in '{[(':
            depth += 1
        elif c in '}])':
            depth -= 1
            if depth == 0 and not stop_at_semicolon:
                return j
        elif c == ';' and depth == 0 and stop_at_semicolon:
            return j
        j += 1
    raise SystemExit('unterminated scan from %d' % start)

def extract_function(name):
    m = re.search(r'\nfunction %s\(' % re.escape(name), js)
    if not m:
        sys.exit('function %s not found' % name)
    p = js.index('(', m.end() - 2)
    pend = scan_end(p, False)      # end of parameter list
    i = js.index('{', pend + 1)    # body opening brace
    j = scan_end(i, False)
    return js[m.start():j+1] + '\n'

def extract_const(name):
    m = re.search(r'\nconst %s\s*=' % re.escape(name), js)
    if not m:
        sys.exit('const %s not found' % name)
    j = scan_end(m.end(), True)
    return js[m.start():j+1] + '\n'

CONSTS = ['A_SIM_EPS','A_SIM_INPUT_FLOOR','CONTACT_ULP_FACTOR','IDEAL_TREFOIL_3_1_1',
          'KAPPA_HE','GAMMA0_SST','RCORE_SST','VSWIRL_SST','OMEGA_CORE_SST','C0','DELTA','P',
          'MF_TABLE','P_DEFAULTS']
FUNCS = ['bgWallInSolver','bundleFlowActive','zMin','zMax','cylinderHeight','cylinderVolume','signedMag','applySigned','clamp',
         'effectiveW','carrierAxialDrift','Gamma','kappaMedium','applyMfTemp','mfActive',
         'mfTransform','kelvinSpeed','filamentGamma','velocityCore','sampleFourierKnot',
         'gauss2','segSegDist2',
         'bundleQuantum','bundleScaleAtU','bundleScaleExtrema','bundleUFromZ','bundleOmegaAtZ',
         'bundleDensityAtZ','bundleReferenceRadius','bundlePhysicalCountAtZ','bundleVelocityAt',
         'bundleMaxOmega']

parts = ['"use strict";\nlet tPhys=0;\n']
for c in CONSTS:
    parts.append(extract_const(c))
parts.append('const MF_TMP3=new Float64Array(3);\n')
for f in FUNCS:
    parts.append(extract_function(f))

exports = CONSTS + FUNCS + ['MF_TMP3']
parts.append('module.exports={%s,setTPhys:v=>{tPhys=v;}};\n' % ','.join(exports))
open(OUT, 'w', encoding='utf-8').write('\n'.join(parts))
print('wrote', OUT)
