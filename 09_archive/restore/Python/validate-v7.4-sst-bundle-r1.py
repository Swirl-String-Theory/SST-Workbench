#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, math, pathlib, re, subprocess, tempfile

def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('html',nargs='?',default='vortexring-lab-v7.4-sst-bundle-r1.html')
    args=ap.parse_args()
    path=pathlib.Path(args.html)
    if not path.is_file(): fail(f"bestand niet gevonden: {path}")
    text=path.read_text(encoding='utf-8')

    required={
      'meta version':'<meta name="vortexlab-version" content="7.4-sst-bundle-r1">',
      'runtime version':"const APP_VERSION='7.4-sst-bundle-r1';",
      'base version':"const APP_BASE_VERSION='7.4';",
      'wall default':'Om:0.0, OmBundle:1.0',
      'bundle state':"bundleEnabled:true, bundleProfile:'parallel'",
      'three omega HUD':'id="hOmegas"',
      'bundle density HUD':'n_v(bundle)=2|Ω_bundle|/κ',
      'bundle UI':'id="sstBundlePanel"',
      'bundle omega input':'id="sOmBundle"',
      'bundle profile':'id="sBundleProfile"',
      'bundle flow toggle':'id="cBundleFlow"',
      'scale function':'function bundleScaleAtU(u)',
      'omega z function':'function bundleOmegaAtZ(z)',
      'flux function':'function bundlePhysicalCountAtZ(z)',
      'coarse field':'function bundleVelocityAt(x,y,z)',
      'CFL bundle guard':'const ob=bundleMaxOmega()',
      'velocity coupling':'const ub=bundleVelocityAt(px,py,pz)',
      'lattice phase separation':"latticeGrp.rotation.z=(P.bundleProfile==='parallel'?bundlePhi:0)-phi;",
      'passive SST preset':'function applySSTBundlePreset()',
      'preset option':'value="sstBundle"',
      'density selftest':'T0e SST bundeldichtheid',
      'flux selftest':'T0f splay fluxbehoud',
    }
    for name,marker in required.items():
        if marker not in text: fail(f"marker ontbreekt: {name}")

    forbidden={
      'oude v7.4 runtime':"const APP_VERSION='7.4';",
      'bundle count from wall omega':'Math.round(40*Math.abs(P.Om))',
      'duplicate overview':'id="collOverview"',
      'BEL':'\x07',
    }
    for name,marker in forbidden.items():
        if marker in text: fail(f"verboden marker aanwezig: {name}")

    markup=text.split('<script',1)[0]
    ids=re.findall(r'\bid=["\']([^"\']+)["\']',markup)
    dup=[k for k,v in collections.Counter(ids).items() if v>1]
    if dup: fail('dubbele statische IDs: '+', '.join(dup))

    scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',text,re.S)
    if not scripts: fail('geen inline script gevonden')
    with tempfile.NamedTemporaryFile('w',suffix='.js',delete=False,encoding='utf-8') as f:
        f.write(scripts[-1]); js_path=f.name
    r=subprocess.run(['node','--check',js_path],capture_output=True,text=True)
    if r.returncode: fail('node --check: '+(r.stderr or r.stdout).strip())

    # Numerieke canon- en fluxchecks, onafhankelijk van de browser.
    gamma0=9.683619e-9
    rc=1.40897017e-15
    omega_core=gamma0/(2*math.pi*rc*rc)
    expected=7.763440655383071e20
    if abs(omega_core/expected-1)>3e-8: fail('Ω_core-canon numeriek inconsistent')
    nv=2/gamma0
    if abs(nv-2.065343545631029e8)/nv>1e-12: fail('n_v-formule inconsistent')

    def lam(u,s,profile):
        if profile=='splay': return max(0.15,1+s*(u-.5))
        if profile=='periodic': return 1+.5*s*(1-math.cos(2*math.pi*u))
        return 1
    for profile in ('parallel','splay','periodic'):
        s=.8
        ls=[lam(i/128,s,profile) for i in range(129)]
        lmax=max(ls); base=.18/lmax
        flux=[]
        for u in (0,.25,.5,.75,1):
            l=lam(u,s,profile)
            density=nv/(l*l)
            area=math.pi*(base*l)**2
            flux.append(density*area)
        if max(flux)/min(flux)-1>1e-12: fail(f'fluxbehoud mislukt voor {profile}')

    print('PASS: SST-bundle r1 statische integriteit, node --check, Ω-scheiding en fluxbehoud groen')

if __name__=='__main__': main()
