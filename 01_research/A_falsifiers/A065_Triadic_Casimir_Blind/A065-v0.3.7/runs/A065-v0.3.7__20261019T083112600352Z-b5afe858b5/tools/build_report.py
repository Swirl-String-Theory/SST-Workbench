"""Compatibility wrapper: create a new isolated run and standalone TeX/PDF."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from triadic.launch import main
if __name__=='__main__':raise SystemExit(main(['REPORT']))
