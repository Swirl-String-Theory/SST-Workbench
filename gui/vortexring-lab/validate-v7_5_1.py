#!/usr/bin/env python3
"""Static integrity validator for vortexring-lab v7.5.1.

Checks the v7.5 frame-refactor base plus the v7.5.1 SST horn/core scale
separation, finite-bundle field, filled-disk sampling, transport parity,
provenance and inline JavaScript syntax.
"""
from __future__ import annotations

import collections
import pathlib
import re
import subprocess
import sys
import tempfile

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "vortexring-lab-v7_5_1.html")
failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + ("  — " + detail if detail else ""))
    if not ok:
        failures.append(name)


if not SRC.is_file():
    print(f"FAIL  bestand ontbreekt: {SRC}")
    raise SystemExit(1)

html = SRC.read_text(encoding="utf-8")

# 1. Provenance
required = {
    "meta version": '<meta name="vortexlab-version" content="7.5.1">',
    "meta base": '<meta name="vortexlab-base" content="7.5">',
    "runtime version": "const APP_VERSION='7.5.1';",
    "runtime base": "const APP_BASE_VERSION='7.5';",
    "patch meta horn/core": "sst-horn-solid-core-separation",
    "patch meta finite bundle": "finite-bundle-field",
    "patch meta transport parity": "bundle-tracer-streamline-parity",
    "footer version": "v7.5.1 · basis v7.5",
}
for name, marker in required.items():
    check(name, marker in html)
check("title v7.5.1", bool(re.search(r"<title>[^<]*v7\.5\.1[^<]*</title>", html)))

# 2. SST semantic architecture
markers = [
    "const R_HORN_SST= 1.40897017e-15;",
    "const V_HORN_SST= 1.09384563e6;",
    "const OMEGA_COMPTON_SST = V_HORN_SST/R_HORN_SST;",
    "rCorePhysical:null,",
    "function resolvedFixedCoreRadius()",
    "function sstRankineProfileAtRadius(",
    "region:'solid-core'",
    "region:'irrotational-exterior'",
    "vorticity:0",
    'id="sRHorn"',
    'id="sRCorePhys"',
    "CANON v0.8.20 + RESEARCH TRACK",
    "P.core='vast';",
    "T0j SST R_horn/r_kern/a_sim gescheiden",
    "T0k vaste Rankine-kern sluit continu aan op 1/r-buitenveld",
]
for marker in markers:
    check("SST marker: " + marker[:68], marker in html)

forbidden = [
    "RCORE_SST",
    "OMEGA_CORE_SST",
    "omegaCorePhysical",
    "aPhys",
    "sAPhys",
    "vAPhys",
    "Kernmodel per Canon: GP/NLSE",
    "Voor \\(n=1\\) geldt canoniek \\(a=r_c\\)",
    "CANON v0.8.19",
]
for marker in forbidden:
    check("legacy/overclaim afwezig: " + marker, marker not in html, f"count={html.count(marker)}")

# 3. Finite bundle and common transport field
bundle_markers = [
    "const BUNDLE_SOURCE_MODEL='analytic-finite-closed-loop-limit';",
    "function bundleBaseRadius()",
    "function bundleRadiusAtZ(z)",
    "function bundleCirculationAtZ(z)",
    "function bundleVelocityProfileAt(",
    "om*Rb*Rb/Math.max(r2,1e-30)",
    "vorticity:inside?2*om:0",
    "function backgroundVelocityAt(x,y,z)",
    "function bundleSampleNormalized(i,n)",
    "Math.sqrt((j+0.5)/N)",
    "T9f eindige bundel continu + constante buiten-circulatie",
    "T9g gedeeld achtergrondveld voor alle transportpaden",
    "T9h gevulde-schijfsampling",
    "T9i bronprovenance gesloten-luslimiet",
]
for marker in bundle_markers:
    check("bundel marker: " + marker[:68], marker in html)

# Definition + velocityCore + stepTracers + fieldVelocityAt.
bg_calls = html.count("backgroundVelocityAt(")
check("gedeeld achtergrondveld heeft drie gebruikers", bg_calls >= 4, f"definition+calls={bg_calls}")
check("oude vortexschil-sampling afwezig", "const ang=2*Math.PI*i/target" not in html)
check("UI noemt filamenten, tracers en stroomlijnen", "filamenten, tracers en stroomlijnen" in html)
check("UI ontkent expliciete verre-knoopoplossing", "Verre knooplagen worden niet expliciet" in html)

# 4. v7.5 base guards and selftests preserved
for marker in [
    "solverFrame:'corot', displayFrame:'corot', bgFlow:'none',",
    "function bgWallInSolver()",
    "add('T8 frame-equivalentie E_frame<1e-6'",
    "add('T1b N-sweep 96/192/384",
    "add('T9a bundel fluxbehoud (parallel)'",
    "id=\"rowEpsRev\"",
    "id=\"rowGa\"",
    "schema:'vortexlab-model-log/0.2'",
    "const ACN=ACNpass; // direct na de exacte passage",
]:
    check("basis behouden: " + marker[:68], marker in html)
for banned in ["coRot", "bgOmegaCoupling", "bundleFlowCoupling"]:
    check("oude frame-id afwezig: " + banned, banned not in html, f"count={html.count(banned)}")

# 5. Static DOM IDs
markup = html.split("<script", 1)[0]
ids = re.findall(r'\bid=["\']([^"\']+)["\']', markup)
counts = collections.Counter(ids)
dupes = sorted(k for k, n in counts.items() if n > 1)
check("DOM-ids uniek", not dupes, f"{len(counts)} unieke ids" + (f"; dubbel={dupes}" if dupes else ""))

# 6. Inline JS syntax
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, re.S)
check("inline script aanwezig", bool(scripts))
if scripts:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as f:
        f.write(scripts[-1])
        js_path = pathlib.Path(f.name)
    try:
        proc = subprocess.run(["node", "--check", str(js_path)], text=True, capture_output=True)
        check("node --check", proc.returncode == 0, (proc.stderr or "groen").strip().splitlines()[0][:160] if proc.stderr else "groen")
    except FileNotFoundError:
        check("node --check", False, "Node.js ontbreekt")
    finally:
        js_path.unlink(missing_ok=True)

print()
if failures:
    print(f"VALIDATOR: FAIL ({len(failures)})")
    raise SystemExit(1)
print(f"VALIDATOR: PASS ({len(counts)} unieke IDs)")
print("LET OP: voer ook browser-smoke-v7_5_1.mjs uit; node --check is geen WebGL-runtimebewijs.")
