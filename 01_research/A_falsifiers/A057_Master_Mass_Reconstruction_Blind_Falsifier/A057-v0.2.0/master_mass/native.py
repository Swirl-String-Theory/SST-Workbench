from __future__ import annotations
from pathlib import Path
import importlib,subprocess,sys

def build_and_import(root: Path):
    ext=root/'native_ext'
    subprocess.run([sys.executable,'setup.py','build_ext','--inplace'],cwd=ext,check=True)
    if str(ext) not in sys.path:sys.path.insert(0,str(ext))
    return importlib.import_module('mm_native')
