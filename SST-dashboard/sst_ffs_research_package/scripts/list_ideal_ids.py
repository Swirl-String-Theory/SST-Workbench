#!/usr/bin/env python3
"""
list_ideal_ids.py

Small utility for Brian Gilbert ideal.txt files.

Usage:
    python scripts/list_ideal_ids.py data/ideal.txt --prefix 5:
    python scripts/list_ideal_ids.py data/ideal.txt --contains "3 2"
"""

from __future__ import annotations
import argparse
import re
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("ideal_file", type=Path)
    p.add_argument("--prefix", type=str, default=None)
    p.add_argument("--contains", type=str, default=None)
    args = p.parse_args()

    text = args.ideal_file.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(
        r'<AB\s+[^>]*Id="(?P<id>[^"]+)"[^>]*Conway="(?P<conway>[^"]*)"[^>]*L="(?P<L>[^"]*)"[^>]*D="(?P<D>[^"]*)"',
        flags=re.S,
    )

    print("Id,Conway,L,D")
    count = 0
    for m in pat.finditer(text):
        rid = m.group("id")
        conway = m.group("conway")
        if args.prefix and not rid.startswith(args.prefix):
            continue
        if args.contains and args.contains not in conway:
            continue
        print(f"{rid},{conway},{m.group('L')},{m.group('D')}")
        count += 1

    print(f"# rows={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
