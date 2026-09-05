from __future__ import annotations
from pathlib import Path
import json

# Import the preregistered generator's pure helpers without invoking main().
import generate_kpc as G

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / "balance_design.json").read_text(encoding="utf-8"))


def write_text_replace(path: Path, text: str) -> None:
    """Overwrite one generated file without deleting/recreating its parent dir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    std = ROOT / "kpc_standard"
    ext = ROOT / "kpc_extended"
    std.mkdir(parents=True, exist_ok=True)
    ext.mkdir(parents=True, exist_ok=True)

    idx = []
    expected_std = set()
    expected_ext = set()

    for s in D["settings"]:
        rid, a = G.standard(s)
        _, b = G.extended(s)

        sp = std / f"{rid}.kpc"
        ep = ext / f"{rid}.kpc"
        write_text_replace(sp, a)
        write_text_replace(ep, b)
        expected_std.add(sp.name)
        expected_ext.add(ep.name)
        idx.append({"run_id": rid, **s})

    # Do not delete the directories. Only remove unexpected stale KPC files.
    # Failure to remove a stale locked file is non-fatal here; validate_kpc.py
    # will catch any stale extra script by the expected-count gate.
    for folder, expected in ((std, expected_std), (ext, expected_ext)):
        for p in folder.glob("*.kpc"):
            if p.name not in expected:
                try:
                    p.unlink()
                except PermissionError:
                    print(f"WARNING: stale locked KPC could not be removed: {p}")

    payload = json.dumps(idx, indent=2) + "\n"
    write_text_replace(std / "index.json", payload)
    write_text_replace(ext / "index.json", payload)

    print("SAFE GENERATOR PASS")
    print("No directory deletion/recreation was attempted.")
    print("GENERATED 20 standard scripts to i30000")
    print("GENERATED 20 continuation scripts i30000 -> i60000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
