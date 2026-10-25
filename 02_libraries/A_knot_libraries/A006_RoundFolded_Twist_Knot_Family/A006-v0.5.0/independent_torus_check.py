import numpy as np
R=0.01; eps=0.001; gamma=1e-7; a=1e-5
N=1536; npnt=480

def geometry(p,q):
 t=2*np.pi*np.arange(N)/N
 if p==1 and q==1: return np.stack([R*np.cos(t),R*np.sin(t),np.zeros_like(t)],axis=1)
 ra=R+eps*np.cos(q*t)
 return np.stack([ra*np.cos(p*t),ra*np.sin(p*t),eps*np.sin(q*t)],axis=1)

def obs(c,r,z=0):
 ph=np.arange(npnt)*2*np.pi/npnt
 X=np.stack([r*np.cos(ph),r*np.sin(ph),np.full_like(ph,z)],axis=1)
 md=(c+np.roll(c,-1,axis=0))/2; dl=np.roll(c,-1,axis=0)-c
 result=np.zeros_like(X)
 for j in range(0,len(X),60):
  d=X[j:j+60,None,:]-md[None,:,:]
  k=(d*d).sum(axis=2)+a*a
  u=np.cross(dl[None,:,:],d)/k[:,:,None]**1.5
  result[j:j+60]=(gamma/(4*np.pi))*u.sum(axis=1)
 u_phi=-result[:,0]*np.sin(ph)+result[:,1]*np.cos(ph)
 return np.array([2*np.pi*r*np.mean(u_phi)/gamma,np.std(u_phi),np.mean(u_phi), np.max(np.abs(u_phi))])
print('R',R,'eps',eps,'Gamma',gamma,'a',a,'N',N,'Nphi',npnt)
for name,p,q in [('ring',1,1),('torus unknot T(1,3)',1,3),('trefoil T(2,3)',2,3),('torus unknot T(3,1)',3,1)]:
 c=geometry(p,q)
 for r in [0.0095,0.01,0.0105,0.013]:
  m=obs(c,r)
  print(f'{name:23} rho={r:.4f} Q={m[0]: .8f} phi_mean={m[2]: .7g} m/s phi_std={m[1]:.7g} m/s')
