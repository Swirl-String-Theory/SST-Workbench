#!/usr/bin/env python3
"""validate-v7_5.py — statische validator voor vortexring-lab-v7.5 (variant van
validate-v7.4.2 conform spec §B.7): nieuwe markers (solverFrame, rowEpsRev, T8),
verbod op de oude P.coRot-dubbele-rol-identifiers, node --check, unieke DOM-ids."""
import re, subprocess, sys, tempfile, os

SRC = sys.argv[1] if len(sys.argv) > 1 else '../v7/vortexring-lab-v7_5.html'
html = open(SRC, encoding='utf-8').read()
fails = []

def check(name, ok, detail=''):
    print(('PASS  ' if ok else 'FAIL  ') + name + ('  — ' + detail if detail else ''))
    if not ok:
        fails.append(name)

# 1. provenance
check('meta vortexlab-version 7.5', '<meta name="vortexlab-version" content="7.5">' in html)
check('meta vortexlab-base 7.4.2', '<meta name="vortexlab-base" content="7.4.2">' in html)
check('title bevat v7.5', bool(re.search(r'<title>[^<]*v7\.5[^<]*</title>', html)))
check("APP_VERSION='7.5'", "const APP_VERSION='7.5';" in html)
check("APP_BASE_VERSION='7.4.2'", "const APP_BASE_VERSION='7.4.2';" in html)
check('patch-meta noemt frame-split + t8 + eps-rev + ga + n-sweep',
      all(t in html for t in ['frame-split-solver-display-bgflow', 't8-frame-equivalence',
                              'eps-rev-on-demand', 'ga-hud', 't1-n-sweep', 'v7.5-validator']))

# 2. nieuwe markers (v7.4b §B.7)
MARKERS = [
    "solverFrame:'corot', displayFrame:'corot', bgFlow:'none',",   # P-defaults
    'function bgWallInSolver()',
    'function bundleFlowActive()',
    'const P_DEFAULTS=Object.freeze(',
    'id="rowEpsRev"', 'id="hEpsRev"', 'id="bEpsRev"',
    'function measureEpsRev()',
    'id="rowGa"', 'id="hGa"',
    "add('T8 frame-equivalentie E_frame<1e-6'",
    "add('T1b N-sweep 96/192/384",
    "add('T0i verse start: coreFlowLock uit, frames corot/corot/none'",
    'solverFrame:P.solverFrame,displayFrame:P.displayFrame,bgFlow:P.bgFlow',  # ModelLog snapP
    "'solverFrame','displayFrame','bgFlow'",                                   # zelftest-PKEYS
]
for m in MARKERS:
    check('marker aanwezig: ' + m[:60], m in html)

# 3. verbod op de oude dubbele-rol-identifiers (volledig geretireerd)
for banned in ['coRot', 'bgOmegaCoupling', 'bundleFlowCoupling']:
    n = html.count(banned)
    check('verboden identifier afwezig: ' + banned, n == 0, 'gevonden: %d' % n)

# 4. bestaande zelftest-familie intact (T0–T9)
for t in ["'T0 versie/provenance", "'T1 Kelvin-snelheid", "'T2 segmentafstand",
          "'T3a Hopf", "'T3c trefoil", "'T4 batch-invariantie", "'T5 round-trip",
          "'T6 wrijving", "'T9a bundel", "'T9c rendering", "'T9d tekeninversie",
          "'T9e splay"]:
    check('zelftest-marker: ' + t, t in html)

# 5. node --check op het inline script
m = re.search(r'<script>\s*("use strict";.*?)</script>', html, re.S)
check('inline script gevonden', bool(m))
if m:
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(m.group(1)); tmp = f.name
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    os.unlink(tmp)
    check('node --check', r.returncode == 0, (r.stderr or 'groen').strip().splitlines()[0][:120])

# 6. unieke DOM-ids — alleen in de statische HTML; het inline script bevat één
# bewuste template-herschrijving van #hTitle (met daarin id="hOm") die de
# statische span vervángt, dus nooit een levende DOM-dubbeling oplevert.
html_only = re.sub(r'<script>\s*"use strict";.*?</script>', '', html, flags=re.S)
ids = re.findall(r'\bid="([^"]+)"', html_only)
dupes = sorted({i for i in ids if ids.count(i) > 1})
check('DOM-ids uniek', not dupes, '%d ids%s' % (len(set(ids)), (', dubbel: ' + ', '.join(dupes)) if dupes else ''))

print()
if fails:
    print('VALIDATOR: FAIL (%d)' % len(fails)); sys.exit(1)
print('VALIDATOR: PASS (%d unieke IDs)' % len(set(ids)))
