from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent/"demo_knots";out.mkdir(exist_ok=True)
# Circle control
for name,p,q in [("circle",1,1),("trefoil",2,3)]:
    t=np.linspace(0,2*np.pi,320,endpoint=False)
    if name=="circle": xyz=np.c_[4*np.cos(t),4*np.sin(t),np.zeros_like(t)]
    else:
        R,r=3.0,1.0
        xyz=np.c_[(R+r*np.cos(q*t))*np.cos(p*t),(R+r*np.cos(q*t))*np.sin(p*t),r*np.sin(q*t)]
    np.savetxt(out/f"{name}.txt",xyz,fmt="%.17g")
print(out)
