from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sst_link_suite.parser import parse_ideal_links, select_links


def main() -> int:
    parser = argparse.ArgumentParser(description="Process-isolated QM-readiness campaign.")
    parser.add_argument("--preset", choices=["quick", "full", "max"], default="quick")
    parser.add_argument("--output", default=None)
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--all-database", action="store_true")
    parser.add_argument("--native-threads", type=int, default=16)
    parser.add_argument("--retry", type=int, default=1)
    parser.add_argument("--force-python", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    input_path = ROOT / "data" / "idealLinks.txt"
    config_path = ROOT / "configs" / f"qm_{args.preset}.json"
    output = Path(args.output) if args.output else ROOT / f"outputs_qm_{args.preset}"
    links = select_links(parse_ideal_links(input_path), args.ids or None, args.all_database)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["SST_NATIVE_MAX_THREADS"] = str(args.native_threads)

    if not args.force_python:
        build = subprocess.run([
            sys.executable, "-m", "sst_link_suite.cli", "build-native", "--strict"
        ], cwd=ROOT, env=env)
        if build.returncode != 0:
            return build.returncode

    ledger = {"preset": args.preset, "output": str(output), "chunks": []}
    failed = []
    for number, link in enumerate(links, 1):
        command = [
            sys.executable, "-m", "sst_link_suite.qm_cli",
            "--input", str(input_path), "--output", str(output),
            "--config", str(config_path), "--ids", link.link_id,
            "--native-threads", str(args.native_threads),
        ]
        if args.force_python:
            command.append("--force-python")
        else:
            command += ["--require-native", "--skip-native-build"]
        if args.no_resume:
            command.append("--no-resume")
        returncode = 1
        attempts = 0
        for attempts in range(1, args.retry + 2):
            print(f"[{number}/{len(links)}] {link.link_id} attempt {attempts}", flush=True)
            returncode = subprocess.run(command, cwd=ROOT, env=env).returncode
            if returncode == 0:
                break
        ledger["chunks"].append({"link_id": link.link_id, "attempts": attempts, "returncode": returncode})
        if returncode != 0:
            failed.append(link.link_id)
        output.mkdir(parents=True, exist_ok=True)
        (output / "qm_chunk_ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    rebuild = [
        sys.executable, "-m", "sst_link_suite.qm_cli",
        "--input", str(input_path), "--output", str(output),
        "--config", str(config_path), "--rebuild-only",
    ]
    if args.all_database:
        rebuild.append("--all-database")
    elif args.ids:
        rebuild += ["--ids", *args.ids]
    returncode = subprocess.run(rebuild, cwd=ROOT, env=env).returncode
    if failed:
        print(f"Failed links: {failed}", file=sys.stderr)
        return 1
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
