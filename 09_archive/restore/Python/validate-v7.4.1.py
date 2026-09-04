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
    ap = argparse.ArgumentParser(description="Statische integriteitscheck voor vortexring-lab v7.4.1")
    ap.add_argument("html", nargs="?", default="vortexring-lab-v7.4.1.html")
    args = ap.parse_args()
    path = pathlib.Path(args.html)
    if not path.is_file():
        fail(f"bestand niet gevonden: {path}")
    text = path.read_text(encoding="utf-8")

    required = {
        "title": "<title>Superfluïde vortexlab v7.4.1",
        "meta version": '<meta name="vortexlab-version" content="7.4.1">',
        "meta base": '<meta name="vortexlab-base" content="7.4">',
        "runtime version": "const APP_VERSION='7.4.1';",
        "runtime base": "const APP_BASE_VERSION='7.4';",
        "current patch provenance": "geometric-diagnostics,dimensionless-hud-guards,gp-delta-state,capacity-indicator",
        "ACN early declaration": "const ACN=ACNpass; // direct na de exacte passage",
        "safe diag builder": "ModelLog.logDiag(buildDiagRecord(Wr,Lk,ACN,sA))",
        "ModelLog schema": "schema:'vortexlab-model-log/0.2'",
        "ModelLog GP state": "gpDelta:DELTA.gp",
        "geometric diagnostics panel": '<details class="coll" id="collDiagnostics">',
        "geometric diagnostics label": "<summary>GEOMETRISCHE DIAGNOSTIEK</summary>",
        "geometric score formula": "katex.render('\\\\widehat{\\\\mathcal S}(K)='",
        "dV excluded from score": "∂V is uitsluitend een domeinvisualisatie en wordt niet bij de score opgeteld",
        "dimensionless HUD label": "|χ_Ω| · Ro_z · a/R",
        "Omega zero guard": "if(om<=1e-12)return NaN; // χ_Ω is mathematically undefined at Ω=0",
        "dimensionless helper": "function dimensionlessDiagnostics(sA,vzRel)",
        "relative orientation helper": "function relativeCarrierOrientationSign()",
        "relative orientation label": "relatieve oriëntatie s_A·s_B",
        "GP panel in model/core": 'id="gpDeltaPanel"',
        "GP setter": "function setGpDelta(value,{reset=true,log=true}={})",
        "GP semantic event": "ModelLog.logEvent('gp-delta-change'",
        "capacity CSS": ".stability-target.stab-capacity",
        "capacity status": "function capacityStatusFromScore(v)",
        "performance warmup": "function resetPerformanceMeasurement(warmupMs=900)",
        "capacity separated from score": ")/0.92;",
        "capacity UI note": 'id="accCapacityNote"',
        "new selftest Omega guard": "T0e dimensieloze Ω=0-guard",
        "new selftest GP state": "T0f GP-Δ state/UI gesynchroniseerd",
        "new selftest diagnostics": "T0g geometrische diagnostiek aanwezig",
        "new selftest orientation": "T0h relatieve drageroriëntatie",
        "runtime guard": "window.addEventListener('unhandledrejection'",
    }
    for name, marker in required.items():
        require(text, marker, name)

    forbidden = {
        "old browser title": "<title>Superfluïde vortexlab v7.3.1",
        "old version": "const APP_VERSION='7.4';",
        "old base": "const APP_BASE_VERSION='7.3.1';",
        "wrong meta base": '<meta name="vortexlab-base" content="7.3">',
        "old energy panel": "ENERGIE E_eff",
        "old energy formula": "\\mathcal{E}_{\\rm eff}[K]",
        "old energy panel id": 'id="collEnergy"',
        "loose GP panel": 'id="collGpDelta"',
        "pseudo repulsion claim": "Biot-Savart Afstoting",
        "pseudo pressure barrier claim": "drukbarrière die reconnectie voorkomt",
        "pseudo Hopf stability claim": "Hopf Stabiliteit",
        "old GP direct window check": "window.ModelLog&&ModelLog.logUser",
        "performance inside numerical score": "+0.08*perfScore",
        "old ACN crash hook": "ModelLog.logEvent('diag',{t:tPhys,Wr,Lk,ACN",
        "old log schema": "schema:'vortexlab-model-log/0.1'",
        "second overview container": 'id="collOverview"',
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

    # GP panel must be structurally inside subCore, before its closing details tag.
    subcore_start = text.find('<details class="subcoll" id="subCore"')
    gp_pos = text.find('id="gpDeltaPanel"')
    next_subcoll = text.find('<details class="subcoll"', subcore_start + 1)
    if not (0 <= subcore_start < gp_pos < next_subcoll):
        fail("GP-Δ-paneel staat niet binnen MODEL/KERN (subCore)")

    # Sidebar tabs must use the diagnostic panel, not the old energy panel.
    require(text, "const ids=['collStabilityParams','collDiagnostics','collRun'];", "diagnostic sidebar tab")
    require(text, "const labels=['MODEL','DIAGNOSE','RUN'];", "diagnostic sidebar label")

    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", text, re.S)
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

    acn_pos = text.find("const ACN=ACNpass; // direct na de exacte passage")
    diag_pos = text.find("ModelLog.logDiag(buildDiagRecord(Wr,Lk,ACN,sA))")
    if not (0 <= acn_pos < diag_pos):
        fail("ACN wordt niet vóór de diaghook gedeclareerd")

    print("PASS: statische v7.4.1-integriteitscheck en node --check groen")
    print(f"INFO: {len(ids)} statische IDs, allemaal uniek")
    print("LET OP: voer daarnaast ?selftest=1 en een browser-smoke van minstens 10 frames uit")


if __name__ == "__main__":
    main()
