from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from native_ext.sycl_worker import build_worker, probe_worker


def main() -> int:
    ap = argparse.ArgumentParser(description="Build standalone sst_sycl_worker.exe")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    ok = build_worker(force=a.force, verbose=True)
    info = probe_worker(force_build=False, verbose=True) if ok else {"available": False, "error": "build_failed"}
    print(json.dumps(info, indent=2))
    return 0 if info.get("available") else (1 if a.strict else 0)


if __name__ == "__main__":
    raise SystemExit(main())
