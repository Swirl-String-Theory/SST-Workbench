#!/usr/bin/env python3
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


def require(text: str, marker: str, name: str) -> None:
    if marker not in text:
        fail(f"marker ontbreekt: {name}")


def forbid(text: str, marker: str, name: str) -> None:
    if marker in text:
        fail(f"verboden marker aanwezig: {name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Statische integriteitscheck voor vortexring-lab v7.4.2 (merge v7.4.1 ⊕ SST-bundel r1)")
    ap.add_argument("html", nargs="?", default="vortexring-lab-v7.4.2.html")
    args = ap.parse_args()
    path = pathlib.Path(args.html)
    if not path.is_file():
        fail(f"bestand niet gevonden: {path}")
    text = path.read_text(encoding="utf-8")

    required = {
        "title": "<title>Superfluïde vortexlab v7.4.2",
        "meta version": '<meta name="vortexlab-version" content="7.4.2">',
        "meta base": '<meta name="vortexlab-base" content="7.4.1">',
        "runtime version": "const APP_VERSION='7.4.2';",
        "runtime base": "const APP_BASE_VERSION='7.4.1';",
        "ModelLog schema": "schema:'vortexlab-model-log/0.2'",
        "geometric diagnostics panel": '<details class="coll" id="collDiagnostics">',
        "Omega zero guard": "if(om<=1e-12)return NaN; // χ_Ω is mathematically undefined at Ω=0",
        "GP panel": 'id="gpDeltaPanel"',
        "capacity UI note": 'id="accCapacityNote"',
        "bundle HUD row": 'id="rowOmegas"',
        "bundle panel": 'id="sstBundlePanel"',
        "bundle state": "bundleFlowCoupling:false",
        "bundle velocity": "function bundleVelocityAt(x,y,z)",
        "exclusive guard": "bundelveldkoppeling en Ω_wall legacy-koppeling zijn exclusief",
        "T9 tests": "T9a–e — SST bundel-researchtrack",
        "runtime guard": "window.addEventListener('unhandledrejection'",
    }
    for name, marker in required.items():
        require(text, marker, name)

    forbidden = {
        "old v7.4.1 runtime": "const APP_VERSION='7.4.1';",
        "old v7.4.1 meta": '<meta name="vortexlab-version" content="7.4.1">',
        "wrong base": '<meta name="vortexlab-base" content="7.4">',
        "BEL byte": "\x07",
        "replacement character": "\ufffd",
    }
    for name, marker in forbidden.items():
        forbid(text, marker, name)

    # Static markup IDs only; JavaScript template strings are not DOM nodes.
    markup = text.split("<script", 1)[0]
    ids = re.findall(r"\bid=[\"']([^\"']+)[\"']", markup)
    duplicates = [key for key, count in collections.Counter(ids).items() if count > 1]
    if duplicates:
        fail(f"dubbele statische IDs: {duplicates}")
    if ids.count("quickControlsDock") != 1:
        fail(f"verwacht exact één OVERZICHT-dock, gevonden {ids.count('quickControlsDock')}")
    if ids.count("gpDeltaSel") != 1:
        fail(f"verwacht exact één GP-Δ-select, gevonden {ids.count('gpDeltaSel')}")

    scripts = re.findall(r"<script(?:\\s[^>]*)?>(.*?)</script>", text, re.S)
    if not scripts:
        fail("geen inline script gevonden")
    js = scripts[-1]
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(js)
        js_path = pathlib.Path(handle.name)
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

    print("PASS: statische v7.4.2-integriteitscheck en node --check groen")
    print(f"INFO: {len(ids)} statische IDs, allemaal uniek")
    print("LET OP: voer daarnaast ?selftest=1 en een browser-smoke van minstens 10 frames uit")


if __name__ == "__main__":
    main()

