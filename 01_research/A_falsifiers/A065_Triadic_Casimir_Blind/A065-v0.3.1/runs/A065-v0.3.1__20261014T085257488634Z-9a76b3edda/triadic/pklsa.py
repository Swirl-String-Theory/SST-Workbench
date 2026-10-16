"""Geometry-only PKLSA/KnotPlot trefoil bridge. No claims of Euler-time evolution.

The original 300-point geometry is vendored as a raw text file and hashed by D01.
The midpoint Biot-Savart segment quadrature is deliberately *dimensionless*:
Gamma=1 and a declared regularization epsilon; it does not select SST core constants.
"""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path


def load_geometry(path: Path):
    p=Path(path)
    out=[]
    for line in p.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):continue
        line=line.replace(',', ' ')
        terms=line.split()
        if len(terms)<3:continue
        try: v=tuple(float(t) for t in terms[:3])
        except ValueError: continue
        if not all(math.isfinite(t) for t in v):raise ValueError('nonfinite PKLSA coordinate')
        out.append(v)
    if len(out)<16: raise ValueError('PKLSA geometry must have >=16 points')
    if len({tuple(round(v,12) for v in pt) for pt in out})<16:raise ValueError('degenerate PKLSA point set')
    if math.dist(out[0],out[-1])<1e-11:out.pop()
    return out


def geometry_stats(points):
    n=len(points); ls=[math.dist(points[i],points[(i+1)%n]) for i in range(n)]
    length=sum(ls); centroid=[sum(p[j] for p in points)/n for j in range(3)]
    rms=math.sqrt(sum(sum((p[j]-centroid[j])**2 for j in range(3)) for p in points)/n)
    return {'points':n,'closed_by_periodic_index':True,'perimeter':length,'rms_radius':rms,'relative_segment_spread':(max(ls)-min(ls))/(length/n),'last_to_first_segment':ls[-1]}


def velocity(points,probe,epsilon=0.12):
    # Piecewise straight centerline, 1/(4*pi) regularized Biot-Savart.
    # epsilon is chosen ex ante from numeric geometry scale, NOT from Casimir targets.
    x,y,z=probe; ox=oy=oz=0.0
    for i,p in enumerate(points):
        q=points[(i+1)%len(points)]
        sx=q[0]-p[0];sy=q[1]-p[1];sz=q[2]-p[2]
        rx=x-(p[0]+q[0])/2;ry=y-(p[1]+q[1])/2;rz=z-(p[2]+q[2])/2
        inv=((rx*rx+ry*ry+rz*rz+epsilon*epsilon)**1.5)
        ox+=(sy*rz-sz*ry)/inv;oy+=(sz*rx-sx*rz)/inv;oz+=(sx*ry-sy*rx)/inv
    return (ox/(4*math.pi),oy/(4*math.pi),oz/(4*math.pi))


def grad_velocity(points,probe,eps=0.12,h=0.03):
    grads=[[0.0]*3 for _ in range(3)]
    for j in range(3):
        p=list(probe);p[j]+=h
        q=list(probe);q[j]-=h
        vplus=velocity(points,p,eps);vminus=velocity(points,q,eps)
        for i in range(3):grads[i][j]=(vplus[i]-vminus[i])/(2*h)
    return grads


def field_metrics(points,probe,eps=0.12):
    u=velocity(points,probe,eps);g=grad_velocity(points,probe,eps)
    w=[g[2][1]-g[1][2],g[0][2]-g[2][0],g[1][0]-g[0][1]]
    S=[[0.5*(g[i][j]+g[j][i]) for j in range(3)] for i in range(3)]
    w2=sum(v*v for v in w);s2=sum(v*v for row in S for v in row)
    return {'probe':list(probe),'velocity':list(u),'divergence_residual':sum(g[i][i] for i in range(3)),
            'vorticity_squared':w2,'strain_squared':s2,'pressure_poisson_source_over_density':0.5*w2-s2}


def bridge(root):
    base=Path(root)/'data'/'D01_EULER'/'pklsa'
    source=json.loads((base/'source.json').read_text(encoding='utf-8'))
    raw=base/source['source_file'];actual_hash=hashlib.sha256(raw.read_bytes()).hexdigest()
    if actual_hash!=source['raw_sha256']:raise RuntimeError('PKLSA source raw SHA256 mismatch')
    pts=load_geometry(raw)
    # Three subsets of the SAME upstream provider. These are resolution controls,
    # explicitly never treated as independent providers.
    probes=[(0,0,0),(0,0,2),(2,0,0),(0,2,0),(0.4,0.2,0.3)]
    levels={75:pts[::4],150:pts[::2],300:pts}
    rows=[]; diffs=[]
    for probe in probes:
        results={n:velocity(levels[n],probe) for n in (75,150,300)}
        v300=results[300]
        rel=math.dist(results[150],v300)/max(1e-14,math.sqrt(sum(t*t for t in v300)))
        diffs.append(rel)
        rows.append({'probe':list(probe),'velocity_75':list(results[75]),'velocity_150':list(results[150]),
                     'velocity_300':list(v300),'refinement_150_to_300':rel,
                     'local_first_derivatives':field_metrics(pts,probe)})
    return {'dataset_id':'PKLSA_TREFOIL_GEOMETRY','source':source,'stats':geometry_stats(pts),
            'regularization_epsilon_dimensionless':0.12,'quadrature':'regularized finite straight midpoint segments',
            'max_refinement_error':max(diffs),'fields':rows,
            'source_provider_count':1,
            'physics_status':'GEOMETRY_DIAGNOSTIC_ONLY; no Euler evolution, no wall boundary conditions, no independent cross-provider validation'}
