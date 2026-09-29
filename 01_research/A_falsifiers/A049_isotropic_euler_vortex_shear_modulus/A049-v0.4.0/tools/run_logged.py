from pathlib import Path
import argparse
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument("--log", required=True)
p.add_argument("command", nargs=argparse.REMAINDER)
a = p.parse_args()
cmd = a.command
if cmd and cmd[0] == "--":
    cmd = cmd[1:]
if not cmd:
    raise SystemExit("no command")
log = Path(a.log)
log.parent.mkdir(parents=True, exist_ok=True)
with log.open("w", encoding="utf-8", errors="replace") as f:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        sys.stdout.write(line)
        f.write(line)
    rc = proc.wait()
raise SystemExit(rc)
