#!/usr/bin/env python3
"""sst_provenance -- content-addressed manifests for SST-Workbench upstream data.

Why three hash levels
---------------------
A gzip container embeds an mtime and an OS byte, so re-compressing the same
bytes gives a different file hash.  Hashing the container is therefore useless
as an identity.  Conversely, moving a CRLF file through git, a text editor or
a Python `open()` in text mode can rewrite every line ending without changing
a single number.  So we record:

  sha256_container : the artifact exactly as it sits on disk (.gz/.zip/.csv).
                     Reproducible only if nobody recompresses it.
  sha256_payload   : the decompressed bytes, exactly as upstream serves them.
                     This is the citable identity of the dataset.
  sha256_canonical : payload with CR/CRLF -> LF, trailing whitespace stripped
                     per line, exactly one terminating LF.  Survives platform
                     transfer; use this to compare two copies for *content*.

Record-level index
------------------
For Fourier record files (<AB Id=...>, <TL Id=...>) the manifest also stores a
per-record canonical hash.  That lets a manuscript cite the provenance of one
knot rather than of a five-megabyte file, and lets `compare` prove that e.g.
record 3:1:1 is unchanged between two differently-edited copies.

Usage
-----
  sst_provenance.py init   <upstream_dir> -o MANIFEST.json [--source SOURCE.md]
  sst_provenance.py verify <upstream_dir> -m MANIFEST.json
  sst_provenance.py compare <fileA> <fileB>          # record-level diff
  sst_provenance.py cite <MANIFEST.json> <record_id> # one-line citation stub
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import fnmatch
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "sst-provenance/1"
RECORD_RE = re.compile(rb'<(AB|TL|HT)\s+Id="([^"]+)"')
DATA_RE = re.compile(rb'<DATA\s+([^>]*)>')
ATTR_RE = re.compile(rb'(\w+)="([^"]*)"')


# --------------------------------------------------------------------------- #
# hashing
# --------------------------------------------------------------------------- #
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonicalise(data: bytes) -> bytes:
    """CR/CRLF -> LF, strip trailing whitespace per line, one terminating LF."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    lines = [ln.rstrip() for ln in data.split(b"\n")]
    while lines and lines[-1] == b"":
        lines.pop()
    return b"\n".join(lines) + b"\n"


def eol_profile(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    cr = data.count(b"\r") - crlf
    lf = data.count(b"\n") - crlf
    present = [n for n, c in (("CRLF", crlf), ("CR", cr), ("LF", lf)) if c]
    return "+".join(present) or "none"


# --------------------------------------------------------------------------- #
# container handling
# --------------------------------------------------------------------------- #
def gzip_header(path: Path) -> dict:
    """Original filename and mtime stored inside a gzip container.

    KnotAtlas serves .gz files whose header still carries the 2016 upload
    timestamps; that is independent evidence of retrieval provenance and is
    worth recording even though it is not cryptographic.
    """
    raw = path.read_bytes()
    if raw[:2] != b"\x1f\x8b":
        return {}
    flg = raw[3]
    mtime = int.from_bytes(raw[4:8], "little")
    i = 10
    if flg & 4:
        i += 2 + int.from_bytes(raw[i:i + 2], "little")
    name = None
    if flg & 8:
        j = raw.index(b"\x00", i)
        name = raw[i:j].decode("latin-1")
    return {
        "stored_filename": name,
        "stored_mtime_utc": (
            datetime.fromtimestamp(mtime, timezone.utc).isoformat() if mtime else None
        ),
    }


def payloads(path: Path) -> list[tuple[str, bytes]]:
    """Return [(member_name, payload_bytes)] for a file on disk."""
    if path.suffix == ".gz":
        return [(path.name[:-3], gzip.decompress(path.read_bytes()))]
    if path.suffix == ".zip":
        out = []
        with zipfile.ZipFile(path) as z:
            for info in sorted(z.infolist(), key=lambda i: i.filename):
                if not info.is_dir():
                    out.append((info.filename, z.read(info)))
        return out
    return [(path.name, path.read_bytes())]


# --------------------------------------------------------------------------- #
# record index
# --------------------------------------------------------------------------- #
def dataset_header(payload: bytes) -> dict:
    """The <DATA Title=... Author=... Date=...> line that these files carry.

    This is the authoritative attribution for the dataset and should be quoted
    in any manuscript that uses it, in preference to a guessed citation.
    """
    m = DATA_RE.search(payload[:4096])
    if not m:
        return {}
    return {k.decode("latin-1"): v.decode("latin-1") for k, v in ATTR_RE.findall(m.group(1))}


def record_index(payload: bytes) -> dict:
    """Per-record canonical hashes for <AB>/<TL> Fourier record files."""
    text = payload
    matches = list(RECORD_RE.finditer(text))
    if not matches:
        return {}
    index = {}
    for k, m in enumerate(matches):
        start = m.start()
        end = matches[k + 1].start() if k + 1 < len(matches) else len(text)
        rid = m.group(2).decode("latin-1")
        index[rid] = sha256(canonicalise(text[start:end]))
    return index


def describe(path: Path, root: Path, with_records: bool) -> dict:
    raw = path.read_bytes()
    entry = {
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "bytes": len(raw),
        "sha256_container": sha256(raw),
        "members": [],
    }
    entry.update(gzip_header(path))
    for name, data in payloads(path):
        member = {
            "member": name,
            "bytes": len(data),
            "sha256_payload": sha256(data),
            "sha256_canonical": sha256(canonicalise(data)),
            "eol": eol_profile(data),
            "bom": data.startswith(b"\xef\xbb\xbf"),
        }
        hdr = dataset_header(data)
        if hdr:
            member["dataset_header"] = hdr
        if with_records:
            idx = record_index(data)
            if idx:
                member["record_count"] = len(idx)
                member["records"] = idx
        entry["members"].append(member)
    return entry


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def iter_init_files(root: Path, include: list[str] | None) -> list[Path]:
    """All files under root, optionally filtered by basename/path glob patterns."""
    files = [p for p in root.rglob("*") if p.is_file() and p.name != "MANIFEST.json"]
    if include:
        kept = []
        for p in files:
            rel = str(p.relative_to(root)).replace("\\", "/")
            if any(fnmatch.fnmatch(p.name, pat) or fnmatch.fnmatch(rel, pat) for pat in include):
                kept.append(p)
        files = kept
    return sorted(files)


def cmd_init(args) -> int:
    root = Path(args.directory).resolve()
    files = iter_init_files(root, args.include or None)
    manifest = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": root.name,
        "source_note": args.source,
        "artifacts": [describe(p, root, not args.no_records) for p in files],
    }
    Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n")
    n = sum(len(a["members"]) for a in manifest["artifacts"])
    print(f"wrote {args.output}: {len(manifest['artifacts'])} artifacts, {n} payload members")
    return 0


def cmd_verify(args) -> int:
    root = Path(args.directory).resolve()
    manifest = json.loads(Path(args.manifest).read_text())
    if manifest.get("schema") != SCHEMA:
        print(f"FAIL  unknown schema {manifest.get('schema')!r}", file=sys.stderr)
        return 2
    failures, checked = 0, 0
    for art in manifest["artifacts"]:
        path = root / art["path"]
        if not path.exists():
            print(f"FAIL  missing        {art['path']}")
            failures += 1
            continue
        raw = path.read_bytes()
        container_ok = sha256(raw) == art["sha256_container"]
        got = {m: d for m, d in payloads(path)}
        for member in art["members"]:
            checked += 1
            data = got.get(member["member"])
            if data is None:
                print(f"FAIL  missing member {art['path']}::{member['member']}")
                failures += 1
                continue
            if sha256(data) == member["sha256_payload"]:
                tag = "OK   " if container_ok else "OK*  "
            elif sha256(canonicalise(data)) == member["sha256_canonical"]:
                tag = "EOL  "
            else:
                tag = "FAIL "
                failures += 1
            print(f"{tag} {art['path']}::{member['member']}")
    print()
    print(f"{checked} members checked, {failures} failures")
    print("  OK   payload byte-identical")
    print("  OK*  payload identical, container recompressed (expected for .gz)")
    print("  EOL  content identical after line-ending normalisation -- NOT citable as the original")
    return 1 if failures else 0


def cmd_compare(args) -> int:
    a = payloads(Path(args.file_a))[0][1]
    b = payloads(Path(args.file_b))[0][1]
    print(f"A {args.file_a}: {len(a)} bytes, eol={eol_profile(a)}")
    print(f"B {args.file_b}: {len(b)} bytes, eol={eol_profile(b)}")
    print(f"payload identical   : {sha256(a) == sha256(b)}")
    print(f"canonical identical : {sha256(canonicalise(a)) == sha256(canonicalise(b))}")
    ia, ib = record_index(a), record_index(b)
    if not ia and not ib:
        return 0
    only_a, only_b = sorted(set(ia) - set(ib)), sorted(set(ib) - set(ia))
    changed = sorted(r for r in set(ia) & set(ib) if ia[r] != ib[r])
    print(f"records: A={len(ia)} B={len(ib)}  only-A={len(only_a)} only-B={len(only_b)} changed={len(changed)}")
    for label, ids in (("only in A", only_a), ("only in B", only_b), ("changed", changed)):
        if ids:
            print(f"  {label}: {', '.join(ids[:20])}{' ...' if len(ids) > 20 else ''}")
    return 0


def cmd_cite(args) -> int:
    manifest = json.loads(Path(args.manifest).read_text())
    for art in manifest["artifacts"]:
        for member in art["members"]:
            h = (member.get("records") or {}).get(args.record_id)
            if h:
                print(f"record   {args.record_id}")
                print(f"file     {art['path']}::{member['member']}")
                print(f"payload  sha256:{member['sha256_payload']}")
                print(f"record   sha256:{h}")
                hdr = member.get("dataset_header") or {}
                if hdr:
                    print(f"dataset  {hdr.get('Title')} -- {hdr.get('Author')} ({hdr.get('Date')})")
                print(f"upstream {art.get('stored_filename')} mtime {art.get('stored_mtime_utc')}")
                print(f"note     {manifest.get('source_note')}")
                return 0
    print(f"record {args.record_id!r} not found in manifest", file=sys.stderr)
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("init", help="build a manifest for a directory")
    q.add_argument("directory")
    q.add_argument("-o", "--output", default="MANIFEST.json")
    q.add_argument("--source", default=None, help="free-text provenance note")
    q.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="GLOB",
        help="only hash files whose path matches this glob (repeatable; e.g. *.gz)",
    )
    q.add_argument("--no-records", action="store_true", help="skip per-record hashing")
    q.set_defaults(func=cmd_init)

    q = sub.add_parser("verify", help="check a directory against a manifest")
    q.add_argument("directory")
    q.add_argument("-m", "--manifest", default="MANIFEST.json")
    q.set_defaults(func=cmd_verify)

    q = sub.add_parser("compare", help="record-level diff of two record files")
    q.add_argument("file_a")
    q.add_argument("file_b")
    q.set_defaults(func=cmd_compare)

    q = sub.add_parser("cite", help="print a citation stub for one record")
    q.add_argument("manifest")
    q.add_argument("record_id")
    q.set_defaults(func=cmd_cite)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
