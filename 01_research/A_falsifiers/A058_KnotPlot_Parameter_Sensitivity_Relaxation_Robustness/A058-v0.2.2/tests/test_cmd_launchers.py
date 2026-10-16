from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_cmd_launchers_start_cleanly():
    for p in ROOT.glob('*.cmd'):
        b=p.read_bytes();assert b.startswith(b'@echo off'),p.name
