"""Verified E011 3_1 provider anchors; exact raw file provenance and no best-fit geometry."""
from __future__ import annotations
import gzip, hashlib, json, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

def _gilbert_coefficients(path:Path, record='3:1:1'):
    with gzip.open(path,'rb') as f:
        for _, element in ET.iterparse(f, events=('end',)):
            if element.tag!='AB':continue
            if element.attrib.get('Id')==record:
                coeff=[]
                for e in element.findall('Coeff'):
                    def vec(s):return np.fromstring(s,sep=',',dtype=np.float64)
                    a,b=vec(e.attrib['A']),vec(e.attrib['B'])
                    if a.size!=3 or b.size!=3:raise ValueError('Malformed Gilbert coefficient')
                    coeff.append((int(e.attrib['I']),a,b))
                if not coeff:raise ValueError('Empty Gilbert knot')
                return coeff
            element.clear()
    raise ValueError(f'Gilbert record {record} not found')

def gilbert_curve(path:Path, sample_count=4096):
    coeff=_gilbert_coefficients(path)
    t=np.arange(sample_count)*2*np.pi/sample_count
    p=np.zeros((sample_count,3),dtype=np.float64)
    for n,a,b in coeff:
        p += np.cos(n*t)[:,None]*a[None,:] + np.sin(n*t)[:,None]*b[None,:]
    return p

def vect_curve(path:Path):
    """Geomview VECT single closed component, negative vertex count denotes closure."""
    lines=[]
    for line in path.read_text(encoding='ascii').splitlines():
        s=line.split('#',1)[0].strip()
        if s:lines.append(s)
    if lines[0]!='VECT':raise ValueError('Missing VECT header')
    components,vertices,colors=map(int,lines[1].split()[:3])
    if components!=1 or vertices<24:raise ValueError('Only one well-sampled knot admitted')
    compvert=int(lines[2].split()[0]);
    if compvert!=-vertices:raise ValueError('VECT file must be closed')
    data=np.array([[float(v) for v in line.split()[:3]] for line in lines[4:4+vertices]])
    if data.shape!=(vertices,3) or not np.all(np.isfinite(data)):
        raise ValueError('Invalid XYZ vertices in VECT')
    return data

def arclength_resample(x:np.ndarray,n:int):
    if n<24:raise ValueError('Insufficient discretization')
    x=np.asarray(x,dtype=np.float64)
    if np.linalg.norm(x[0]-x[-1])<1e-12: x=x[:-1]
    cyc=np.vstack([x,x[:1]])
    dl=np.linalg.norm(np.diff(cyc,axis=0),axis=1)
    if np.any(dl<=0):raise ValueError('Repeated vertices')
    ss=np.r_[0,np.cumsum(dl)]
    targets=np.arange(n)*ss[-1]/n
    ans=np.stack([np.interp(targets,ss,cyc[:,d]) for d in range(3)],axis=1)
    return ans

def normalized_perimeter(x):
    x=x-np.mean(x,axis=0)
    perimeter=np.sum(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1))
    if perimeter<=0:raise ValueError('Degenerate knot')
    return x/perimeter

def polygon_impulse_area(x):
    return 0.5*np.cross(x,np.roll(x,-1,axis=0)).sum(axis=0)

def align_area_to_positive_z(x):
    a=polygon_impulse_area(x); z=a/np.linalg.norm(a)
    target=np.array([0.,0.,1.])
    v=np.cross(z,target); c=float(z@target)
    if np.linalg.norm(v)<1e-12:
        rot=np.eye(3) if c>0 else np.diag([1.,-1.,-1.])
    else:
        k=np.array([[0.,-v[2],v[1]],[v[2],0.,-v[0]],[-v[1],v[0],0.]])
        rot=np.eye(3)+k+k@k/(1+c)
    return x@rot.T

def winding_proxy(x):
    """Low-resolution polygonal Gauss integral estimate, orientation diagnostic only."""
    ds=np.roll(x,-1,axis=0)-x; m=x+0.5*ds
    r=m[:,None,:]-m[None,:,:]
    cross=np.cross(ds[:,None,:],ds[None,:,:]); denom=np.sum(r*r,axis=-1)**1.5
    np.fill_diagonal(denom,np.inf)
    return float(np.sum(np.einsum('ijk,ijk->ij',r,cross)/denom)/(4*np.pi))

def providers(n=128):
    pin=json.loads((ROOT/'inputs/e011/provider_pins.json').read_text())
    data=json.loads((ROOT/'inputs/e011/trefoil_STATIC_READY_SEEDSET.json').read_text())
    assert data['summary']['static_ready'] and data['summary']['primary_provider_count']>=2
    out={}
    for k in pin['provider_anchors']:
        group=k['provider'];p=ROOT/k['file']
        found=sha256(p)
        if found!=k['raw_sha256']:
            raise RuntimeError(f'E011 raw sha256 mismatch for {group}: expected {k["raw_sha256"]}, found {found}')
        if not k['seed_role']=='PRIMARY_REFERENCE' or k['evidence_class']!='UPSTREAM_INDEPENDENT':
            raise RuntimeError('Provider is not admissible independent primary reference')
        x=gilbert_curve(p) if group=='gilbert' else vect_curve(p)
        x=normalized_perimeter(align_area_to_positive_z(arclength_resample(x,n)))
        # area sign must remain positive after proper rotation
        if polygon_impulse_area(x)[2]<0:raise ValueError('Area alignment failure')
        out[group]={'x':x,'metadata':k,'raw_sha256':found,'sample_count':len(x),
            'polygon_perimeter':float(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1).sum()),
            'area':polygon_impulse_area(x).tolist(),'writhe_proxy':winding_proxy(x)}
    return out
