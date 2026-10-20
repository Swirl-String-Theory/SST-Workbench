"""Fail-closed discrete 3D GP vortex-line tracking on a periodic cubic grid.

Find integer phase winding on oriented XY, YZ and ZX faces and construct the
oriented dual 1-complex. Every valid, isolated closed lattice filament has
one incoming and one outgoing oriented dual edge at each visited dual node.

This detects lattice closed components, NOT an ambient-isotopy knot type.
It does not certify GP reconnection, Euler vortex frozen-in transport, KAM,
or a knot-internal clock phase. Periodic net fluxes are permitted only if the
complex field is well-defined and its face fields give the measured flux.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np

ORIENTED_FACES = ((0, 1, 2, "xy"), (1, 2, 0, "yz"), (2, 0, 1, "zx"))


def windings(psi: np.ndarray) -> dict[str, np.ndarray]:
    a = np.asarray(psi)
    if a.ndim != 3 or any(n < 8 for n in a.shape):
        raise ValueError("3D complex cubic field, >=8 cells per axis required")
    if len(set(a.shape)) != 1 or not np.iscomplexobj(a):
        raise ValueError("cubic complex grid required")
    if not np.all(np.isfinite(a)):
        raise ValueError("nonfinite complex GP field")
    if np.any(np.abs(a) == 0):
        raise ValueError("field has exact zeros at grid vertices; winding ambiguous")
    unit = a / np.abs(a)
    link = [np.angle(np.conjugate(unit)*np.roll(unit, -1, axis=k)) for k in range(3)]
    out = {}
    for i,j,normal,name in ORIENTED_FACES:
        circulation = link[i] + np.roll(link[j],-1,axis=i) - np.roll(link[i],-1,axis=j) - link[j]
        n = np.rint(circulation/(2*np.pi)).astype(np.int16)
        if np.max(np.abs(n)) > 1:
            raise ValueError("multi-quantum plaquette; underresolved core")
        if np.max(np.abs(circulation-2*np.pi*n)) > 3.e-11:
            raise ValueError("noninteger face phase winding")
        out[name] = n
    return out


def component_diagnostics(psi: np.ndarray) -> dict:
    """Return integer-dual-graph diagnostics with explicit certification guard."""
    w=windings(psi); n=psi.shape[0]
    # Edge XY cell at (a,b,c) crosses +z from dual cube (a,b,c-1) to (a,b,c).
    # Similarly YZ crosses +x, ZX crosses +y.
    adjacency=defaultdict(list)
    signed_face_counts={}
    edge_count=0
    flux_direction=[0,0,0]
    oriented_edges=[]
    for i,j,normal,name in ORIENTED_FACES:
        indices=np.argwhere(w[name] != 0)
        positive=int(np.sum(w[name] > 0)); negative=int(np.sum(w[name] < 0))
        signed_face_counts[name]={"positive":positive,"negative":negative,"total":int(len(indices))}
        for idx in indices:
            p=tuple(int(v) for v in idx)
            left=list(p);left[normal]=(left[normal]-1)%n
            a=tuple(left);b=p;sign=int(w[name][p])
            # Orient physical dual edge by the 2pi winding sign.
            if sign<0:a,b=b,a
            oriented_edges.append((a,b,normal,sign))
            adjacency[a].append(edge_count)
            adjacency[b].append(edge_count)
            flux_direction[normal]+=sign
            edge_count+=1
    counts=defaultdict(int)
    oriented_in=defaultdict(int);oriented_out=defaultdict(int)
    for a,b,ax,sign in oriented_edges:
        oriented_out[a]+=1;oriented_in[b]+=1
    for node,v in adjacency.items():counts[len(v)]+=1
    defects=[node for node in adjacency if (len(adjacency[node])!=2 or oriented_in[node]!=1 or oriented_out[node]!=1)]
    visited=set();components=[]
    for node in sorted(adjacency):
        if node in visited:continue
        pending=[node];visited.add(node);nodes=[];c_edges=set()
        while pending:
            current=pending.pop();nodes.append(current)
            for e in adjacency[current]:
                c_edges.add(e)
                a,b,_,_=oriented_edges[e]
                other=b if a==current else a
                if other not in visited:visited.add(other);pending.append(other)
        is_simple=all(len(adjacency[v])==2 and oriented_in[v]==1 and oriented_out[v]==1 for v in nodes)
        homology=[0,0,0]
        if is_simple:
            for ei in c_edges:
                _,_,axis,sign=oriented_edges[ei]
                homology[axis]+=sign
            # A winding closed filament must wrap through integer multiples of n lattice steps.
            if any(v % n != 0 for v in homology):
                is_simple=False
            else:
                homology=[int(v//n) for v in homology]
        components.append({"vertices":len(nodes),"edges":len(c_edges),
                           "simple_oriented_cycle":bool(is_simple),
                           "periodic_homology":homology if is_simple else None})
    total_oriented_charge=[int(x) for x in flux_direction]
    # For a periodic single-valued complex scalar field, net vorticity flux through
    # homologous periodic 2-tori should sum zero. Record failure, do not silently fix.
    return {
       "schema":"A069-V060-DUAL-PLAQUETTE-GRAPH-1",
       "grid_n":int(n),"face_counts":signed_face_counts,
       "total_edges":edge_count,"degree_distribution":dict(sorted(counts.items())),
       "junction_or_orientation_defects":len(defects),"component_count":len(components),
       "components":sorted(components,key=lambda c:-c['edges']),
       "signed_face_flux":total_oriented_charge,
       "graph_consistent":bool(len(defects)==0 and all(c['simple_oriented_cycle'] for c in components)),
       "knot_type_certified":False,"physical_reconnection_certified":False,
       "physical_clock_frequency":None,"status":"GEOMETRIC_LATTICE_DIAGNOSTIC_ONLY"
    }


def compare_snapshots(before: np.ndarray,after: np.ndarray)->dict:
    """No topology claim solely from changes of component counts or plaquettes."""
    x=component_diagnostics(before);y=component_diagnostics(after)
    return {"schema":"A069-V060-SNAPSHOT-COMPARISON-1",
            "before_components":x['component_count'],"after_components":y['component_count'],
            "before_edges":x['total_edges'],"after_edges":y['total_edges'],
            "before_defects":x['junction_or_orientation_defects'],
            "after_defects":y['junction_or_orientation_defects'],
            "status":"UNRESOLVED_TOPOLOGY",
            "why":"Changes in lattice vorticity plaquettes do not prove reconnection or knot-type change",
            "requires":["multi-resolution connected centerlines","ambient isotopy tracking",
                        "continuous in-time vortex zeros","minimum separation / self-contact",
                        "independent time and space convergence"]}
