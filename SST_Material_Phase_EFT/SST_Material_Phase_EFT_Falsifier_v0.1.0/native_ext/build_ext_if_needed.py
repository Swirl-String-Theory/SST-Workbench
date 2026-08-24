from pathlib import Path
import subprocess,sys
def main():
    try:
        import native_ext._native
        print("[SST-EFT-NATIVE] native extension already available"); return 0
    except Exception: pass
    root=Path(__file__).resolve().parents[1]; cmd=[sys.executable,"setup.py","build_ext","--inplace"]; print("[SST-EFT-NATIVE] compile:"," ".join(cmd)); return subprocess.call(cmd,cwd=root)
if __name__=="__main__": raise SystemExit(main())
