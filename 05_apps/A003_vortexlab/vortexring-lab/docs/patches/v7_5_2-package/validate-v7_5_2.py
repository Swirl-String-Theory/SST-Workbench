#!/usr/bin/env python3
"""Static integrity validator for vortexring-lab v7.5.2.

Checks provenance, v7.5.1 SST-scale separation, the v7.5.2 topology guard,
Level-C discrete Neumann source-panel BEM/MFS, self-test markers, unique static
DOM IDs, and JavaScript syntax via node --check.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess
import sys
import tempfile


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", nargs="?", default="vortexring-lab-v7_5_2.html")
    args = ap.parse_args()
    path = pathlib.Path(args.html)
    if not path.is_file():
        fail(f"bestand niet gevonden: {path}")
    text = path.read_text(encoding="utf-8")

    required = {
        "meta version": '<meta name="vortexlab-version" content="7.5.2">',
        "meta base": '<meta name="vortexlab-base" content="7.5.1">',
        "runtime version": "const APP_VERSION='7.5.2';",
        "runtime base": "const APP_BASE_VERSION='7.5.1';",
        "BEM model id": "const BEM_SOURCE_MODEL='neumann-source-panel-mfs-v1';",
        "topology guard default": "autoRelax:false, timeReverse:false, topologyGuard:true,",
        "BEM defaults": "bundleBEMEnabled:true, bundleBoundaryMode:'asim', bundleBEMQuality:'mid',",
        "BEM UI": 'id="cBundleBEM" checked',
        "boundary selector": 'id="sBundleBoundaryMode"',
        "quality selector": 'id="sBundleBEMQuality"',
        "topology UI": 'id="cTopologyGuard" checked',
        "Neumann solve": "function solveBundleNeumann(nodes,fieldFn,radius)",
        "dense pivot solve": "function solveDensePivot(A,b,n)",
        "full tube nodes": "function buildBundleBEMNodes(radius,target=bundleBEMTargetCount())",
        "velocity correction": "function bundleExteriorVelocityAt(x,y,z,projectInside=true)",
        "filament surface average": "function backgroundVelocityForFilamentPoint(px,py,pz,tx,ty,tz)",
        "vorticity correction": "function bundleVorticityAt(x,y,z)",
        "bent lines": "function traceBundleVorticityLine(sample,steps=96)",
        "topology clearance": "function topologyClearance()",
        "transient contact": "function transientContactWithinStep(signedDtFull,lia)",
        "safe-side landing": "const land=P.topologyGuard?lo:hi;",
        "contact CFL": "0.12*Math.max(margin,0.05*dc)",
        "auto-relax rollback": "topology guard heeft een auto-relax-mutatie teruggedraaid",
        "selftest T0l": "T0l topology guard standaard actief",
        "selftest T0m": "T0m Niveau-C BEM standaard actief op a_sim",
        "selftest T0n": "T0n BEM-bronmodel geversioneerd",
        "selftest T9j": "T9j Neumann-BEM dwingt u·n≈0",
        "selftest T9k": "T9k vorticiteits-Neumannprojectie",
        "selftest T9l": "T9l BEM compatibiliteitsconstraint Σq=0",
        "selftest T9m": "T9m transient-contact risicopredicaat",
        "ACN early declaration": "const ACN=ACNpass; // direct na de exacte passage",
        "ModelLog schema": "schema:'vortexlab-model-log/0.2'",
        "SST horn constant": "const R_HORN_SST= 1.40897017e-15;",
    }
    for name, marker in required.items():
        if marker not in text:
            fail(f"marker ontbreekt: {name}")

    forbidden = {
        "old runtime version": "const APP_VERSION='7.5.1';",
        "old base": "const APP_BASE_VERSION='7.5';",
        "old ontknot claim": "hier zou de knoop ontknopen",
        "old RCORE symbol": "RCORE_SST",
        "old physical a alias": "aPhys",
        "BEL byte": "\x07",
        "replacement char": "\ufffd",
    }
    for name, marker in forbidden.items():
        if marker in text:
            fail(f"verboden marker aanwezig: {name}")

    # Structural ordering: BEM helpers must exist before runtime loop use.
    order = [
        "function solveBundleNeumann",
        "function ensureBundleBEM",
        "function velocityCore",
        "function loop(now)",
    ]
    positions = [text.find(x) for x in order]
    if any(p < 0 for p in positions) or positions != sorted(positions):
        fail(f"ongeldige BEM/runtime-volgorde: {list(zip(order, positions))}")

    # Only count static markup IDs. Inline templates are not live duplicate nodes.
    markup = text.split("<script", 1)[0]
    ids = re.findall(r'\bid=["\']([^"\']+)["\']', markup)
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        fail(f"dubbele statische IDs: {dup}")

    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", text, re.S)
    if not scripts:
        fail("geen inline script gevonden")
    js = scripts[-1]
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as f:
        f.write(js)
        js_path = pathlib.Path(f.name)
    try:
        proc = subprocess.run(["node", "--check", str(js_path)], text=True, capture_output=True)
    except FileNotFoundError:
        fail("Node.js ontbreekt; voer node --check handmatig uit")
    finally:
        try:
            js_path.unlink()
        except OSError:
            pass
    if proc.returncode:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        fail("JavaScript-syntaxis ongeldig")

    print("PASS: statische v7.5.2-integriteitscheck en node --check groen")
    print(f"INFO: {len(ids)} statische IDs, allemaal uniek")
    print("LET OP: voer browser-smoke-v7_5_2.mjs uit voor runtime/WebGL/T0–T9m.")


if __name__ == "__main__":
    main()
