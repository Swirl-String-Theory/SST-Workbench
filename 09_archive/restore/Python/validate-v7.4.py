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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", nargs="?", default="vortexring-lab-v7.4.html")
    args = ap.parse_args()
    path = pathlib.Path(args.html)
    if not path.is_file():
        fail(f"bestand niet gevonden: {path}")
    text = path.read_text(encoding="utf-8")

    required = {
        'meta version': '<meta name="vortexlab-version" content="7.4">',
        'runtime version': "const APP_VERSION='7.4';",
        'base version': "const APP_BASE_VERSION='7.3.1';",
        'ACN early declaration': 'const ACN=ACNpass; // direct na de exacte passage',
        'diag safe builder': 'ModelLog.logDiag(buildDiagRecord(Wr,Lk,ACN,sA))',
        'ModelLog schema': "schema:'vortexlab-model-log/0.2'",
        'drop counters': 'const dropped={actions:0,steps:0,events:0};',
        'global change capture': "document.addEventListener('change'",
        'global click capture': "document.addEventListener('click'",
        'safe radius floor': 'const A_SIM_INPUT_FLOOR=1e-18;',
        'contact floor': 'const CONTACT_ULP_FACTOR=64;',
        'single overview dock': '<div class="quick-controls-title">OVERZICHT</div>',
        'runtime guard': "window.addEventListener('unhandledrejection'",
    }
    for name, marker in required.items():
        if marker not in text:
            fail(f"marker ontbreekt: {name}")

    forbidden = {
        'oude ACN crash-hook': "ModelLog.logEvent('diag',{t:tPhys,Wr,Lk,ACN",
        'tweede overzichtcontainer': 'id="collOverview"',
        'oude log schema': "schema:'vortexlab-model-log/0.1'",
        'oude runtime version': "const APP_VERSION='7.3.1';",
        'BEL byte': '\x07',
        'replacement char': '\ufffd',
    }
    for name, marker in forbidden.items():
        if marker in text:
            fail(f"verboden marker aanwezig: {name}")

    # Alleen statische markup-IDs; JS-template strings worden niet als DOM-node geteld.
    markup = text.split('<script', 1)[0]
    ids = re.findall(r'\bid=["\']([^"\']+)["\']', markup)
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup:
        fail(f"dubbele statische IDs: {dup}")

    scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', text, re.S)
    if not scripts:
        fail('geen inline script gevonden')
    js = scripts[-1]
    with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as f:
        f.write(js)
        js_path = pathlib.Path(f.name)
    try:
        proc = subprocess.run(['node', '--check', str(js_path)], text=True, capture_output=True)
    except FileNotFoundError:
        fail('Node.js ontbreekt; voer node --check handmatig uit')
    finally:
        try:
            js_path.unlink()
        except OSError:
            pass
    if proc.returncode:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        fail('JavaScript-syntaxis ongeldig')

    acn_pos = text.find('const ACN=ACNpass; // direct na de exacte passage')
    diag_pos = text.find('ModelLog.logDiag(buildDiagRecord(Wr,Lk,ACN,sA))')
    if not (0 <= acn_pos < diag_pos):
        fail('ACN wordt niet vóór de diaghook gedeclareerd')

    print('PASS: statische v7.3.1-integriteitscheck en node --check groen')
    print('LET OP: voer daarnaast de browsertest uit uit CURSOR-patch-instructies-v7.3.1.md')


if __name__ == '__main__':
    main()
