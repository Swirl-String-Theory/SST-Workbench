import argparse
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--log", required=True)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
cmd = list(args.command)
if cmd and cmd[0] == "--":
    cmd = cmd[1:]
if not cmd:
    raise SystemExit("No command supplied")

log_path = Path(args.log)
log_path.parent.mkdir(parents=True, exist_ok=True)
with log_path.open("w", encoding="utf-8", errors="replace") as log:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        log.write(line)
        log.flush()
    rc = proc.wait()
    log.write(f"\n[exit_code] {rc}\n")
raise SystemExit(rc)
