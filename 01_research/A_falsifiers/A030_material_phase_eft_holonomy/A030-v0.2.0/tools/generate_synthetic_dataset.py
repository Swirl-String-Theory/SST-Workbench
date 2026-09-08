from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parents[1]/'_synthetic_dataset'; out.mkdir(exist_ok=True)
for idx,(p,q) in enumerate([(2,3),(2,5),(3,4)]):
    n=420; t=np.linspace(0,2*np.pi,n,endpoint=False); R=3.; r=1.; x=np.column_stack([(R+r*np.cos(q*t))*np.cos(p*t),(R+r*np.cos(q*t))*np.sin(p*t),r*np.sin(q*t)]); np.savetxt(out/f'synthetic_{idx:02d}.txt',x,fmt='%.12e')
print(out)
