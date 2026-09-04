from __future__ import annotations
import math
import numpy as np


def _circle_dist(a,b):
    d=abs(a-b)%1.0
    return min(d,1.0-d)

def contact_point_distance(p,q):
    # unordered contact endpoints on S1 x S1, compare with swap symmetry
    a,b=p; c,d=q
    x=math.hypot(_circle_dist(a,c),_circle_dist(b,d))
    y=math.hypot(_circle_dist(a,d),_circle_dist(b,c))
    return min(x,y)

def hausdorff_contact_map(P,Q):
    P=list(P);Q=list(Q)
    if not P and not Q:return 0.0
    if not P or not Q:return float("inf")
    def directed(A,B): return max(min(contact_point_distance(a,b) for b in B) for a in A)
    return max(directed(P,Q),directed(Q,P))
