from pathlib import Path
import numpy as np

def circle(n=512,R=4.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.column_stack([R*np.cos(t),R*np.sin(t),np.zeros_like(t)])
def trefoil(n=800):
    t=np.linspace(0,2*np.pi,n,endpoint=False);x=np.sin(t)+2*np.sin(2*t);y=np.cos(t)-2*np.cos(2*t);z=-np.sin(3*t);return np.column_stack([x,y,z])
def generate(root:Path):
    root.mkdir(parents=True,exist_ok=True);np.save(root/'synthetic_circle.npy',circle());np.save(root/'synthetic_trefoil.npy',trefoil())
