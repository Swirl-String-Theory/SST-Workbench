from pathlib import Path
import csv,numpy as np

def make_demo(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=True); rows=[]; n=180; t=np.linspace(0,2*np.pi,n,endpoint=False)
    # Smooth 3D QHP trefoil-like manifold. This is ingestion/manifold plumbing only; no PASS expectation is encoded.
    for q in (-.2,0.,.2):
      for h in (-.15,0.,.15):
       for p in (-.1,0.,.1):
        R=2+(.15*q)*np.cos(t)+.05*h*np.cos(2*t); x=(R+np.cos(3*t)) * np.cos(2*t); y=(R+np.cos(3*t))*np.sin(2*t); z=(1+.2*p)*np.sin(3*t)+.08*h*np.sin(t); X=np.c_[x,y,z]
        fn=f'demo_q{q:+.2f}_h{h:+.2f}_p{p:+.2f}.txt'.replace('+','').replace('-','m').replace('.','p'); np.savetxt(root/fn,X,fmt='%.12g'); rows.append({'file':fn,'family':'demo_trefoil','q':q,'h':h,'p':p,'replicate':0})
    with (root/'qhp_metadata.csv').open('w',newline='',encoding='utf-8') as f: wr=csv.DictWriter(f,fieldnames=['file','family','q','h','p','replicate']); wr.writeheader(); wr.writerows(rows)
    return len(rows)
