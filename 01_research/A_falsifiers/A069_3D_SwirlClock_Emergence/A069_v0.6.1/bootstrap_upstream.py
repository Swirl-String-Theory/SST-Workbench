"""Install byte-pinned public A069-v0.5.0 sources for local diagnostic only."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import sys
root=Path(__file__).resolve().parent
src=root/'upstream'/'v0.5.0_SOURCE_PUBLIC_PINNED.zip'
EXPECTED='bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e'
if hashlib.sha256(src.read_bytes()).hexdigest()!=EXPECTED:sys.exit('FAIL: v0.5.0 public source SHA mismatch')
out=root/'upstream_runtime'
with ZipFile(src) as z:
    expected='A069_3D_SwirlClock_Emergence/A069-v0.5.0/'
    for item in z.namelist():
        if not item.startswith(expected) or '..' in Path(item).parts or Path(item).is_absolute():
            sys.exit('FAIL: unsafe upstream ZIP member')
    if not z.testzip() is None:sys.exit('FAIL: corrupt upstream public source')
    z.extractall(out)
print(out/'A069_3D_SwirlClock_Emergence'/'A069-v0.5.0')
