#!/usr/bin/env python3

"""Static integrity validator for vortexring-lab v7.5.5.



Checks v7.5.4 stretch-gate base plus border edge-drawer layout and help-hover UX:

compact info icons, fixed hover balloons, unique static DOM IDs, and node --check.

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

    ap.add_argument("html", nargs="?", default="vortexring-lab-v7_5_5.html")

    args = ap.parse_args()

    path = pathlib.Path(args.html)

    if not path.is_file():

        fail(f"bestand niet gevonden: {path}")

    text = path.read_text(encoding="utf-8")



    required = {

        "meta version": '<meta name="vortexlab-version" content="7.5.5">',

        "meta base": '<meta name="vortexlab-base" content="7.5.4">',

        "runtime version": "const APP_VERSION='7.5.5';",

        "runtime base": "const APP_BASE_VERSION='7.5.4';",

        "patch edge drawers": "edge-drawers,sidebar-help-hover",

        "edge layout init": "function initEdgeLayout()",

        "edge layout schedule": "function scheduleEdgeLayout()",

        "edge drawer class": "edge-drawer",

        "edge layout class": "edge-layout",

        "edge bottom": 'id="edgeBottom"',
        "model tabs": 'class="model-tabs"',
        "model tab btn": "model-tab-btn",
        "model tab init": "function initModelTabs()",

        "edge top": 'id="edgeTop"',

        "edge left": 'id="edgeLeft"',

        "edge right": 'id="edgeRight"',

        "edge storage": "vortexlab.edgeDrawer.v1",

        "help scan root": "function scanHelpRoot(root)",

        "help overview dock": "scanHelpRoot(document.getElementById('quickControlsDock'))",

        "help hover init": "function initSidebarHelpHover()",

        "help button class": ".info-help-btn",

        "help balloon": "help-balloon",

        "help balloon id": "helpBalloon",

        "Planck constant": "const PLANCK_LENGTH=1.616255e-35;",

        "scale probe state": "scaleProbe:R_HORN_SST,",

        "gap ratios helper": "function gapRatios(minGap)",

        "advance candidate": "function advanceFilamentCandidate(dt,endTime)",

        "scale probe UI": 'id="scaleProbeRow"',

        "string medium": 'data-med="string"',

        "string preset": 'value="string">🧵 String-theorie schaalprobe',

        "stab gap label": "g_a = d_min/a_sim",

        "selftest T11": "T11 a_probe passief + string-probe contract",

        "selftest T12": "T12 Taylor-forcing uitsluitend solo + contactgelokaliseerd",

        "selftest T13": "T13 Canon Γ₀ + diagnostiek serialiseerbaar",

        "stretch gate": "stretchGateEnabled",

        "topology guard": "topologyGuard:true",

        "BEM model": "const BEM_SOURCE_MODEL='neumann-source-panel-mfs-v1';",

        "ModelLog schema": "schema:'vortexlab-model-log/0.2'",

        "ACN early declaration": "const ACN=ACNpass; // direct na de exacte passage",

        "organize quick controls": "function organizeQuickControls()",

    }

    for name, marker in required.items():

        if marker not in text:

            fail(f"marker ontbreekt: {name}")



    forbidden = {

        "old runtime 7.5.4": "const APP_VERSION='7.5.4';",

        "old base 7.5.3": "const APP_BASE_VERSION='7.5.3';",

        "spread layout init": "function initSpreadLayout()",

        "model dock": 'id="modelDock"',

        "diagnose dock": 'id="diagnoseDock"',

        "run dock": 'id="runDock"',

        "model dock col": "model-dock-col",

        "favorites dock": "favoriteControlsBody",

        "favorite mirrors": "syncFavoriteMirrors",

        "favorite pin": "favorite-pin",

        "old RCORE": "RCORE_SST",

        "old physical a alias": "P.aPhys",

        "old sAPhys": "sAPhys",

        "BEL byte": "\x07",

        "replacement char": "\ufffd",

    }

    for name, marker in forbidden.items():

        if marker in text:

            fail(f"verboden marker: {name}")



    markup = text.split("<script", 1)[0]

    ids = re.findall(r"\bid=[\"']([^\"']+)[\"']", markup)

    duplicates = [key for key, count in collections.Counter(ids).items() if count > 1]

    if duplicates:

        fail(f"dubbele statische IDs: {duplicates}")



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



    print(f"VALIDATOR: PASS ({len(ids)} unieke IDs)")

    print("LET OP: voer daarnaast ?selftest=1 en browser-smoke-v7_5_5.mjs uit")





if __name__ == "__main__":

    main()

