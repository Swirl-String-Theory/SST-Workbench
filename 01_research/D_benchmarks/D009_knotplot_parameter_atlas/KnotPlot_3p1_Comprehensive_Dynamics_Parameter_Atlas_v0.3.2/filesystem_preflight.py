from pathlib import Path
import tempfile, sys

ROOT=Path(__file__).resolve().parent

required=[
    ROOT/"out"/"probe",
    ROOT/"out"/"extended",
    ROOT/"logs"/"probe",
    ROOT/"logs"/"extended",
    ROOT/"runtime_kpc"/"probe",
    ROOT/"runtime_kpc"/"extended",
    ROOT/"analysis",
    ROOT/"archive",
]

for p in required:
    p.mkdir(parents=True,exist_ok=True)

failed=[]
for p in required:
    probe=p/".write_probe.tmp"
    try:
        probe.write_text("ok\n",encoding="ascii")
        if not probe.is_file() or probe.stat().st_size==0:
            failed.append(str(p))
    except Exception as e:
        failed.append(f"{p}: {e}")
    finally:
        try:
            probe.unlink()
        except Exception:
            pass

print("FILESYSTEM PREFLIGHT")
print("="*72)
for p in required:
    print(f"{'PASS' if str(p) not in failed else 'FAIL'}  {p}")

if failed:
    print("\nFAILED:")
    for x in failed: print(" ",x)
    raise SystemExit(2)

print("\nFILESYSTEM PREFLIGHT PASS")
