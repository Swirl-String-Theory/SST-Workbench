from __future__ import annotations
import numpy as np
from .registry import KAtlasSnapshot, normalize_knot_id
from .braid import braid_closure, braid_closure_components, braid_permutation, permutation_cycles
from .geometry import classic_trefoil, figure8_s3, lissajous_7_4, resample_closed


def generate_topology_seed(knot_id: str, *, method: str='auto', n: int=512,
                           registry: KAtlasSnapshot|None=None, **kwargs) -> np.ndarray:
    """Generate an independent seed whose intended topology comes from the offline registry.

    These are topology-controlled seeds, not ideal/ropelength-minimizing shapes.
    """
    registry=registry or KAtlasSnapshot(); kid=normalize_knot_id(knot_id); ref=registry.get(kid)
    m=method.lower()
    if m=='auto':
        if kid=='3_1': m='classic'
        elif kid=='4_1': m='s3'
        elif kid=='7_4': m='lissajous'
        else: m='braid'
    if m=='classic' and kid=='3_1': return resample_closed(classic_trefoil(n=n),n)
    if m=='s3' and kid=='4_1': return resample_closed(figure8_s3(n=n,angle=float(kwargs.get('angle',0.35))),n)
    if m=='lissajous' and kid=='7_4': return resample_closed(lissajous_7_4(n=n),n)
    if m=='braid':
        if not ref.braid_word or not ref.braid_strands: raise ValueError(f'no braid in registry for {kid}')
        return braid_closure(ref.braid_strands,ref.braid_word,resample_n=n,
                             lane_spacing=float(kwargs.get('lane_spacing',1.0)),
                             crossing_height=float(kwargs.get('crossing_height',0.55)),
                             steps_per_crossing=int(kwargs.get('steps_per_crossing',32)))
    raise ValueError(f'method {method} is not available for {kid}')


def braid_reference_report(knot_id: str, registry: KAtlasSnapshot|None=None) -> dict:
    registry=registry or KAtlasSnapshot(); ref=registry.get(knot_id)
    if not ref.braid_word: return {'knot_id':ref.knot_id,'available':False}
    perm=braid_permutation(ref.braid_strands,ref.braid_word)
    cycles=permutation_cycles(perm)
    return {'knot_id':ref.knot_id,'available':True,'strands':ref.braid_strands,'word':list(ref.braid_word),
            'end_permutation':list(perm),'closure_cycles':cycles,'component_count':len(cycles),
            'expected_components':ref.components,'component_count_match':len(cycles)==ref.components}
