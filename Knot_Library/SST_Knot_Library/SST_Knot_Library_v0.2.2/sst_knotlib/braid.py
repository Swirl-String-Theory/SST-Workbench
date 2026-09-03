from __future__ import annotations
import math
from typing import Iterable, List, Sequence
import numpy as np
from .geometry import resample_closed


def _smoothstep01(s: np.ndarray) -> np.ndarray:
    return s*s*(3.0-2.0*s)


def braid_permutation(strands: int, word: Sequence[int]) -> tuple[int, ...]:
    """Return end lane of each start label for an Artin braid word.

    Generator +i or -i both exchange lanes i-1 and i; sign affects over/under only.
    """
    n=int(strands)
    if n < 2: raise ValueError('strands must be >=2')
    lane_occupant=list(range(n))
    for g in word:
        i=abs(int(g))-1
        if i < 0 or i+1 >= n: raise ValueError(f'invalid generator {g} for {n} strands')
        lane_occupant[i], lane_occupant[i+1] = lane_occupant[i+1], lane_occupant[i]
    end_lane=[None]*n
    for lane,label in enumerate(lane_occupant): end_lane[label]=lane
    return tuple(int(x) for x in end_lane)


def permutation_cycles(p: Sequence[int]) -> list[list[int]]:
    n=len(p); seen=[False]*n; cycles=[]
    for i in range(n):
        if seen[i]: continue
        cyc=[]; j=i
        while not seen[j]:
            seen[j]=True; cyc.append(j); j=int(p[j])
        cycles.append(cyc)
    return cycles


def _closure_path(x: float, y_end: float, closure_height: float, closure_margin: float,
                  n: int, lane_rank: int, n_lanes: int) -> np.ndarray:
    """Cubic Bezier outside the open braid, at fixed x lane.

    Lane-dependent z height keeps closure arcs disjoint. The path runs from y_end to 0.
    """
    zc=closure_height*(1.0 + 0.12*(lane_rank-(n_lanes-1)/2.0))
    P0=np.array([x,y_end,0.0])
    P1=np.array([x,y_end+closure_margin,zc])
    P2=np.array([x,-closure_margin,zc])
    P3=np.array([x,0.0,0.0])
    s=np.linspace(0.0,1.0,max(4,int(n)),endpoint=False)[:,None]
    return (1-s)**3*P0 + 3*(1-s)**2*s*P1 + 3*(1-s)*s**2*P2 + s**3*P3


def braid_closure_components(strands: int, word: Sequence[int], *,
                             lane_spacing: float = 1.0,
                             crossing_height: float = 0.55,
                             steps_per_crossing: int = 32,
                             closure_steps: int = 80,
                             closure_margin: float | None = None,
                             closure_height: float | None = None,
                             resample_n: int | None = 512) -> list[np.ndarray]:
    """Construct a smooth-ish polygonal geometric closure of an Artin braid.

    This is an independent geometry generator, not an ideal-knot solver. It is intended as
    a topology-controlled seed/control family. Convention: positive generator places the
    strand entering from the lower-numbered lane at +z during the crossing.
    """
    n=int(strands); word=[int(g) for g in word]
    if n<2 or not word: raise ValueError('need >=2 strands and non-empty braid word')
    m=len(word); spc=max(8,int(steps_per_crossing))
    lanes=(np.arange(n,dtype=float)-(n-1)/2.0)*float(lane_spacing)
    total_y=float(m)
    if closure_margin is None: closure_margin=max(1.5,0.35*total_y)
    if closure_height is None: closure_height=max(2.5*crossing_height,1.25*n*lane_spacing)

    lane_occupant=list(range(n))
    trajectories=[[] for _ in range(n)]
    # Include exact starts once.
    for label in range(n): trajectories[label].append(np.array([lanes[label],0.0,0.0]))

    for k,g in enumerate(word):
        idx=abs(g)-1
        if idx<0 or idx+1>=n: raise ValueError(f'invalid generator {g} for {n} strands')
        left_label=lane_occupant[idx]; right_label=lane_occupant[idx+1]
        s=np.linspace(0.0,1.0,spc,endpoint=False)[1:]  # start already present
        sm=_smoothstep01(s)
        bump=np.sin(math.pi*s)
        y=k+s
        # Determine lane of each label during this event.
        for label in range(n):
            lane=lane_occupant.index(label)
            if label==left_label:
                x=lanes[idx]*(1-sm)+lanes[idx+1]*sm
                z=np.sign(g)*crossing_height*bump
            elif label==right_label:
                x=lanes[idx+1]*(1-sm)+lanes[idx]*sm
                z=-np.sign(g)*crossing_height*bump
            else:
                x=np.full_like(s,lanes[lane]); z=np.zeros_like(s)
            for xx,yy,zz in zip(x,y,z): trajectories[label].append(np.array([xx,yy,zz]))
        # end event at exact lane positions
        lane_occupant[idx],lane_occupant[idx+1]=lane_occupant[idx+1],lane_occupant[idx]
        for lane,label in enumerate(lane_occupant): trajectories[label].append(np.array([lanes[lane],float(k+1),0.0]))

    traj=[np.asarray(x,float) for x in trajectories]
    end_lane=braid_permutation(n,word)
    cycles=permutation_cycles(end_lane)
    comps=[]
    for cyc in cycles:
        pieces=[]
        for label in cyc:
            pieces.append(traj[label][:-1])
            lane=end_lane[label]
            pieces.append(_closure_path(lanes[lane],total_y,float(closure_height),float(closure_margin),closure_steps,lane,n))
        comp=np.vstack(pieces)
        # Recenter to reduce arbitrary closure offset; preserve topology.
        comp-=comp.mean(axis=0)
        if resample_n:
            ncomp=max(64,int(resample_n))
            comp=resample_closed(comp,ncomp)
        comps.append(comp)
    return comps


def braid_closure(strands: int, word: Sequence[int], **kwargs) -> np.ndarray:
    comps=braid_closure_components(strands,word,**kwargs)
    if len(comps)!=1:
        raise ValueError(f'braid closure has {len(comps)} components, not a knot')
    return comps[0]
