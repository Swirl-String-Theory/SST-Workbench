from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from sst_link_suite.parser import parse_ideal_links, DEFAULT_TARGETS


def chunks(values, size):
    for i in range(0, len(values), size):
        yield list(values[i:i+size])


parser = argparse.ArgumentParser(
    description="Chunked, resumable native campaign runner for ideal links."
)
parser.add_argument("--preset", choices=["quick", "full", "max"], default="full")
parser.add_argument("--output", default=None)
parser.add_argument("--all-database", action="store_true")
parser.add_argument("--ids", nargs="*")
parser.add_argument("--chunk-size", type=int, default=None)
parser.add_argument("--chunk-timeout-s", type=float, default=180.0)
parser.add_argument("--single-link-retries", type=int, default=2)
parser.add_argument("--no-resume", action="store_true")
parser.add_argument("--force-python", action="store_true")
parser.add_argument("--allow-python-fallback", action="store_true")
parser.add_argument("--skip-build", action="store_true")
parser.add_argument("--force-build", action="store_true")
parser.add_argument("--build-verbose", action="store_true")
parser.add_argument("--native-threads", type=int, default=None)
args = parser.parse_args()

input_path = ROOT / "data" / "idealLinks.txt"
config_path = ROOT / "configs" / f"{args.preset}.json"
output = Path(args.output) if args.output else ROOT / f"outputs_{args.preset}"
output.mkdir(parents=True, exist_ok=True)

all_links = parse_ideal_links(input_path)
if args.ids:
    selected_ids = list(args.ids)
elif args.all_database:
    selected_ids = list(all_links)
else:
    selected_ids = list(DEFAULT_TARGETS)
missing = [link_id for link_id in selected_ids if link_id not in all_links]
if missing:
    raise SystemExit(f"Unknown link IDs: {missing}")

chunk_size = args.chunk_size
if chunk_size is None:
    chunk_size = len(selected_ids) if args.preset == "quick" else 8
if chunk_size < 1:
    raise SystemExit("--chunk-size must be >= 1")
if args.chunk_timeout_s <= 0:
    raise SystemExit("--chunk-timeout-s must be > 0")
if args.single_link_retries < 0:
    raise SystemExit("--single-link-retries must be >= 0")

env = os.environ.copy()
env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
if args.native_threads is not None:
    if args.native_threads < 1:
        raise SystemExit("--native-threads must be >= 1")
    env["SST_NATIVE_MAX_THREADS"] = str(args.native_threads)

ledger = {
    "suite_version": "0.3.4.1",
    "preset": args.preset,
    "python_executable": sys.executable,
    "selected_ids": selected_ids,
    "initial_chunk_size": chunk_size,
    "chunk_timeout_s": args.chunk_timeout_s,
    "chunks": [],
}
started = time.time()
chunk_counter = 0
parity_available = (output / "native_audit.json").exists()
force_build_pending = bool(args.force_build)


def write_ledger():
    ledger["wall_elapsed_s"] = time.time()-started
    (output / "chunk_ledger.json").write_text(
        json.dumps(ledger, indent=2), encoding="utf-8"
    )


def build_command(chunk_ids, no_resume, skip_parity):
    command = [
        sys.executable, "-m", "sst_link_suite.cli", "run",
        "--input", str(input_path),
        "--output", str(output),
        "--config", str(config_path),
        "--ids", *chunk_ids,
        "--defer-report",
    ]
    if no_resume:
        command.append("--no-resume")
    if args.force_python:
        command.append("--force-python")
    elif not args.allow_python_fallback:
        command.append("--require-native")
    if args.skip_build:
        command.append("--skip-native-build")
    global force_build_pending
    if force_build_pending:
        command.append("--force-native-build")
        force_build_pending = False
    if args.build_verbose:
        command.append("--build-verbose")
    if args.native_threads is not None:
        command += ["--native-threads", str(args.native_threads)]
    if skip_parity:
        command.append("--skip-parity")
    return command


def run_chunk(chunk_ids, first_attempt_no_resume=False, depth=0):
    global chunk_counter, parity_available
    chunk_counter += 1
    ordinal = chunk_counter
    attempts = 1 + (args.single_link_retries if len(chunk_ids) == 1 else 0)
    for attempt in range(1, attempts+1):
        skip_parity = parity_available
        command = build_command(
            chunk_ids,
            no_resume=first_attempt_no_resume and attempt == 1,
            skip_parity=skip_parity,
        )
        indent = "  " * depth
        print(
            f"{indent}[chunk {ordinal}, attempt {attempt}] {len(chunk_ids)} links: "
            + " ".join(chunk_ids),
            flush=True,
        )
        chunk_started = time.time()
        timed_out = False
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=env, check=False,
                timeout=args.chunk_timeout_s,
            )
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = 124
            print(
                f"{indent}  timeout after {args.chunk_timeout_s:g}s",
                flush=True,
            )
        metadata_path = output / "run_metadata.json"
        chunk_metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists() else {}
        )
        if (output / "native_audit.json").exists():
            try:
                parity_available = bool(json.loads(
                    (output / "native_audit.json").read_text(encoding="utf-8")
                ).get("ok"))
            except Exception:
                parity_available = False
        row = {
            "chunk_index": ordinal,
            "attempt": attempt,
            "depth": depth,
            "ids": chunk_ids,
            "returncode": returncode,
            "timed_out": timed_out,
            "elapsed_s": time.time()-chunk_started,
            "campaign_elapsed_s": chunk_metadata.get("elapsed_s"),
            "completed_ids": chunk_metadata.get("completed_ids", []),
            "failures": chunk_metadata.get("failures", []),
        }
        ledger["chunks"].append(row)
        write_ledger()
        if returncode == 0:
            return True
        if len(chunk_ids) == 1 and attempt < attempts:
            print(f"{indent}  retrying {chunk_ids[0]}", flush=True)
            continue
        break

    if len(chunk_ids) > 1:
        midpoint = len(chunk_ids)//2
        left, right = chunk_ids[:midpoint], chunk_ids[midpoint:]
        print(f"{'  '*depth}  splitting failed/timed-out chunk", flush=True)
        return (
            run_chunk(left, first_attempt_no_resume=False, depth=depth+1)
            and run_chunk(right, first_attempt_no_resume=False, depth=depth+1)
        )
    return False


for initial_chunk in chunks(selected_ids, chunk_size):
    if not run_chunk(initial_chunk, first_attempt_no_resume=args.no_resume):
        write_ledger()
        raise SystemExit(1)

write_ledger()
rebuild = [
    sys.executable, "-m", "sst_link_suite.cli", "rebuild-report",
    "--input", str(input_path),
    "--output", str(output),
    "--config", str(config_path),
    "--ids", *selected_ids,
]
try:
    completed = subprocess.run(
        rebuild, cwd=ROOT, env=env, check=False,
        timeout=max(120.0, args.chunk_timeout_s),
    )
except subprocess.TimeoutExpired:
    print("Final report rebuild timed out.", flush=True)
    raise SystemExit(124)
raise SystemExit(completed.returncode)
