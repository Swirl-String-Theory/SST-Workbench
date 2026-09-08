from pathlib import Path
import importlib.util
import subprocess
import sys


def _native_self_test(root: Path) -> int:
    code = r"""
import numpy as np
from native_ext._native import biot_savart_velocity
n=32
t=np.linspace(0.0,2.0*np.pi,n,endpoint=False)
x=np.column_stack((3.0*np.cos(t),3.0*np.sin(t),np.zeros_like(t)))
v=np.asarray(biot_savart_velocity(x,2.0*np.pi,1.0))
assert v.shape == x.shape
assert np.isfinite(v).all()
assert float(np.linalg.norm(v)) > 0.0
print('[SST-EFT-NATIVE] import/kernel self-test PASS')
"""
    return subprocess.call([sys.executable, '-c', code], cwd=root)


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        import native_ext._native  # noqa: F401
        print('[SST-EFT-NATIVE] native extension already available')
        return _native_self_test(root)
    except Exception:
        pass

    cmd = [sys.executable, 'setup.py', 'build_ext', '--inplace', '--force']
    print('[SST-EFT-NATIVE] compile:', ' '.join(cmd))
    rc = subprocess.call(cmd, cwd=root)
    if rc != 0:
        return rc
    return _native_self_test(root)


if __name__ == '__main__':
    raise SystemExit(main())
