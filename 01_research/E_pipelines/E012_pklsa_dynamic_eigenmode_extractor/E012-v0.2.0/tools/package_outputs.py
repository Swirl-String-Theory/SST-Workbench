from __future__ import annotations
import hashlib, shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
out=root/"outputs"
zip_base=root.parent/(root.name+"-outputs")
zip_path=Path(shutil.make_archive(str(zip_base),"zip",root_dir=out))
h=hashlib.sha256(zip_path.read_bytes()).hexdigest()
sha=zip_path.with_suffix(zip_path.suffix+".sha256")
sha.write_text(f"{h}  {zip_path.name}\n",encoding="utf-8")
print(zip_path)
print(sha)
