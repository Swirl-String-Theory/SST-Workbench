#!/usr/bin/env python3
"""F005 source-native ZIP preflight, Python stdlib only. Never modifies raw archives."""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile
from collections import Counter

VERSION = "0.1.0"
EXPECTED = {
    "DATASET.zip": {"md5": "0cf4dc4f3a93d7898c3da72b921dce7c", "doi": "10.5281/zenodo.15223412"},
    "sloshing_zenodo_package_v1.0.0.zip": {"md5": "0c2e91f4556c7b9fd57c12721d165f95", "doi": "10.5281/zenodo.20039757"},
}
ROBOT_FILES = {"input_train.npy", "output_train.npy", "trajectory_metadata.csv", "time_vector.csv", "load_dataset.py"}
ROBOT_MAX_TOTAL = 1_500_000_000
ROBOT_MAX_FILE = 800_000_000


def fingerprint(file: Path):
    md5 = hashlib.md5(usedforsecurity=False)
    sha = hashlib.sha256()
    with file.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def safe_member(info: zipfile.ZipInfo):
    name = info.filename.replace("\\", "/")
    parts = PurePosixPath(name).parts
    if not name or name.startswith("/") or ".." in parts or re.match(r"^[A-Za-z]:", name):
        return False
    if info.flag_bits & 1:
        return False  # encrypted
    mode = info.external_attr >> 16
    if stat.S_IFMT(mode) == stat.S_IFLNK:
        return False
    return True


def classify(names):
    lower_basenames = {PurePosixPath(n).name.lower() for n in names}
    if {"input_train.npy", "output_train.npy"} <= lower_basenames:
        return "ROBOT_SLOSHING"
    if any("nobody" in n.lower().replace("_", "") for n in names) and any("floatingbody" in n.lower().replace("_", "") for n in names):
        return "ROLL_TANK_SLOSHING"
    return "UNKNOWN"


def inspect_zip(file: Path, manifest_dir: Path, hash_enabled=False):
    result = {"archive": str(file.resolve()), "filename": file.name, "bytes": file.stat().st_size,
              "status": "UNINSPECTED", "source_identity": "UNVERIFIED", "hash_verified": False}
    try:
        with zipfile.ZipFile(file, "r", allowZip64=True) as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos if not i.is_dir()]
            warnings = []
            bad = [i.filename for i in infos if not safe_member(i)]
            if bad:
                warnings.append(f"{len(bad)} unsafe/encrypted entries; extraction is prohibited for these")
            if len(set(i.filename for i in infos)) != len(infos):
                warnings.append("duplicate member paths found")
            count = Counter(PurePosixPath(n).suffix.lower() or "[no extension]" for n in names)
            group = classify(names)
            result.update(status="ZIP_CENTRAL_DIRECTORY_OK", dataset_class=group,
                          member_count=len(infos), file_count=len(names),
                          uncompressed_bytes=sum(i.file_size for i in infos),
                          unsafe_entries=len(bad), warnings=warnings,
                          extensions=dict(count.most_common()),
                          NoBody_candidates=sum("nobody" in n.lower().replace("_", "") for n in names),
                          FloatingBody_candidates=sum("floatingbody" in n.lower().replace("_", "") for n in names))
            # Prefer source-identification by data signatures. Name alone does NOT verify provenance.
            manifest_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", file.name) + "_members.csv"
            manifest_path = manifest_dir / manifest_name
            with manifest_path.open("w", encoding="utf-8", newline="") as m:
                wr = csv.writer(m)
                wr.writerow(["path", "uncompressed_bytes", "compressed_bytes", "crc32", "zip_timestamp", "safe_to_extract"])
                for info in infos:
                    if not info.is_dir():
                        wr.writerow([info.filename, info.file_size, info.compress_size, f"{info.CRC:08x}", str(info.date_time), safe_member(info)])
            result["manifest_csv"] = str(manifest_path.resolve())
            if group == "ROLL_TANK_SLOSHING":
                candidates = [i for i in infos if not i.is_dir() and "nobody" in i.filename.lower().replace("_", "")]
                priority_ext = {".csv":0,".xml":1,".txt":2,".mat":3,".npz":4,".npy":5,".mp4":6,".avi":7}
                candidates.sort(key=lambda i: (priority_ext.get(PurePosixPath(i.filename).suffix.lower(),10),i.file_size,i.filename))
                result["sample_NoBody_members_to_inspect"] = [{"path":i.filename,"bytes":i.file_size} for i in candidates[:12]]
            if group == "ROBOT_SLOSHING":
                result["robot_files_found"] = sorted(ROBOT_FILES & {PurePosixPath(n).name.lower() for n in names})
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, MemoryError) as e:
        result.update(status="ZIP_HEADER_FAIL", error=f"{type(e).__name__}: {e}")
        return result
    ref = EXPECTED.get(file.name)
    if ref:
        result["expected_md5"] = ref["md5"]
        result["source_doi_candidate"] = ref["doi"]
    if hash_enabled:
        md5, sha = fingerprint(file)
        result["md5"] = md5
        result["sha256"] = sha
        if ref:
            result["hash_verified"] = md5 == ref["md5"]
            result["source_identity"] = "ZENODO_MD5_MATCH" if result["hash_verified"] else "ZENODO_MD5_MISMATCH"
        else:
            result["source_identity"] = "SHA256_RECORDED_ORIGINAL_NAME_UNRECOGNIZED"
    return result


def extract_robot(result, root: Path, output: Path):
    source = Path(result["archive"])
    if result.get("status") != "ZIP_CENTRAL_DIRECTORY_OK" or result.get("dataset_class") != "ROBOT_SLOSHING":
        raise ValueError(f"Archive not validated as ROBOT_SLOSHING: {source.name}")
    dest = output / "data" / "robot_sloshing" / "raw_extracted"
    dest.mkdir(parents=True, exist_ok=True)
    taken = {}
    total = 0
    with zipfile.ZipFile(source, "r") as zf:
        for member in zf.infolist():
            base = PurePosixPath(member.filename).name.lower()
            if base not in ROBOT_FILES:
                continue
            if not safe_member(member):
                raise ValueError(f"Unsafe entry {member.filename}")
            if base in taken:
                raise ValueError(f"Duplicate requested basename {base}")
            if member.file_size > ROBOT_MAX_FILE or total + member.file_size > ROBOT_MAX_TOTAL:
                raise ValueError("Refusing unexpectedly large robot extraction")
            path = dest / PurePosixPath(member.filename).name
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite existing file: {path}")
            tmp = path.with_suffix(path.suffix + ".tmp")
            import shutil
            try:
                with zf.open(member) as src, tmp.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=2 * 1024 * 1024)
                if tmp.stat().st_size != member.file_size:
                    raise IOError("Extracted byte count mismatch")
                tmp.rename(path)
            finally:
                if tmp.exists():
                    tmp.unlink()
            taken[base] = {"path": str(path.resolve()), "bytes": member.file_size, "zip_path": member.filename}
            total += member.file_size
    if not {"input_train.npy","output_train.npy"} <= set(taken):
        raise ValueError("Missing required NPY arrays in robot archive")
    (dest / "extraction_manifest.json").write_text(json.dumps({"source_archive":str(source.resolve()),"extracted":taken,
        "note":"Extracted datasets do not become independent measurements; source is preserved."},indent=2),encoding="utf-8")
    return taken


def main(argv=None):
    p=argparse.ArgumentParser(description="F005 safe ZIP inventory; full 50 GB data is never unpacked")
    p.add_argument("--root", type=Path, default=Path("."), help="F005 instance root; sources/ must exist")
    p.add_argument("--out", type=Path, default=None, help="Output dir, default <root>/outputs/data_preflight_v0.1.0")
    p.add_argument("--verify-hashes", action="store_true", help="Stream every ZIP in full; may take minutes for 50 GB")
    p.add_argument("--extract-robot", action="store_true", help="Extract ONLY selected files from recognized small robot ZIP")
    args=p.parse_args(argv)
    root=args.root.resolve()
    sources=root/"sources"
    if not sources.is_dir():
        p.error(f"Missing {sources}; run from the F005 instance root")
    files=sorted(sources.rglob("*.zip"),key=lambda f:(f.stat().st_size,f.name))
    if not files:
        p.error(f"No ZIP files found under {sources}")
    output=(args.out or (root/"outputs"/"data_preflight_v0.1.0")).resolve()
    if sources == output or sources in output.parents:
        p.error("Output must not be inside sources/")
    output.mkdir(parents=True, exist_ok=True)
    manifest_dir=output/"manifests"
    manifest_dir.mkdir(exist_ok=True)
    results=[inspect_zip(f,manifest_dir,args.verify_hashes) for f in files]
    extracted={}
    error=None
    if args.extract_robot:
        robots=[r for r in results if r.get("dataset_class")=="ROBOT_SLOSHING" and r.get("status")=="ZIP_CENTRAL_DIRECTORY_OK"]
        if len(robots)!=1:
            error=f"Need exactly one recognized robot archive, found {len(robots)}"
        else:
            try: extracted=extract_robot(robots[0],root,output)
            except (OSError,ValueError,zipfile.BadZipFile) as e: error=f"Extraction failed: {type(e).__name__}: {e}"
    doc={"tool_version":VERSION,"created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
         "root":str(root),"archives":results,"robot_extracted":extracted,"extraction_error":error,
         "scientific_status":"SOURCE_PREFLIGHT_ONLY_NOT_A_PHYSICAL_FALSIFIER"}
    (output/"preflight_report.json").write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["# F005 sloshing archive preflight", "",f"Sources: `{sources}`", "",
           "**Status:** SOURCE PREFLIGHT ONLY. No SST/PKLSA validation.",""]
    for r in results:
        lines += [f"## `{r['filename']}`",f"- Archive size: {r['bytes']:,} bytes",f"- Type: `{r.get('dataset_class','UNKNOWN')}`",
                  f"- ZIP header: `{r['status']}`",f"- Entries: {r.get('file_count','n/a')}",
                  f"- Hash identity: `{r.get('source_identity','UNVERIFIED')}`",f"- Warnings: {', '.join(r.get('warnings',[])) or 'none'}",""]
        for item in r.get("sample_NoBody_members_to_inspect",[])[:6]:
            lines.append(f"  - Candidate NoBody: `{item['path']}` ({item['bytes']:,} B)")
        lines.append("")
    if error: lines += [f"**Extraction error:** `{error}`",""]
    lines += ["Next: use the small robot data for a locked baseline; choose a single NoBody run from the 49.9-GB archive after reviewing its manifest.",
             "Do not classify these as Kelvin/inertial-wave vortex data."]
    (output/"SUMMARY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    for r in results:
        print(f"{r['filename']}: {r['status']} {r.get('dataset_class')} {r.get('file_count',0)} files")
    print(f"Report: {output / 'SUMMARY.md'}")
    if error:
        print(error,file=sys.stderr)
        return 2
    if any(r['status']!="ZIP_CENTRAL_DIRECTORY_OK" for r in results):
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
