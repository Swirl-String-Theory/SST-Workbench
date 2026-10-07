from pathlib import Path
from a055_spectrum.atlas import load_atlas
from a055_spectrum.geometry import build_embedding
from a055_spectrum.backend import measure,native_available
ROOT=Path(__file__).resolve().parents[1]

def test_native_parity():
    if not native_available(): return
    a={x["id"]:x for x in load_atlas(ROOT)}
    for top in ("5_2","L6a4"):
        g=build_embedding(a[top],32,"parity",0)
        p=measure(g,0.03,True); n=measure(g,0.03,False)
        for k in ["total_length","bend_energy","min_distance","contact_ratio","neumann_energy","writhe","linking_strength","linking_residual"]:
            d=max(1.0,abs(p[k]),abs(n[k]))
            assert abs(p[k]-n[k])/d < 5e-10
