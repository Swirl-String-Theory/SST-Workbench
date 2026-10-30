"""Non-certifying source quality controls for imported three-component links.

No Milnor invariant, isotopy proof, exact reach, or physics claim is computed.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree
from .external_links import get_registry,normalized_parts,gauss_midpoint
from .filaments import resample,quotient_distance
from .coupled import pair_distance_preflight

def _edges_curve(parts):
    v=np.concatenate(parts)
    ds=[np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1) for x in parts]
    return {
        'component_polygon_lengths':[float(d.sum()) for d in ds],
        'point_counts':[int(len(x)) for x in parts],
        'finite':bool(np.isfinite(v).all()),
        'polygon_edge_minimum':[float(d.min()) for d in ds],
        'polygon_edge_maximum':[float(d.max()) for d in ds],
        'closure_edge_to_median':[float(d[-1]/np.median(d)) for d in ds],
        'total_polygonal_length':float(sum(d.sum() for d in ds))}

def qualify_imported(name):
    e=get_registry()[name]
    orig,meta=normalized_parts(name,'original')
    rec={'family':name,'sources':{},'pairwise_orientation_not_certified':True,
         'milnor_mu123':'UNRESOLVED','component_topologies':'LABELS_UNVERIFIED',
         'full_link_isotopy':'UNRESOLVED','finite_core_reach':'UNRESOLVED',
         'source_interpolation_warning':'Higher point count is polygon interpolation, not new source information',
         'physical_units':'NORMALIZED_COORDINATE_R0_EQ_1_NO_SI_CALIBRATION',
         'source_sha256_original':e['original_sha256'],'source_sha256_reference':e.get('reference_sha256')}
    for k in ('original','reference'):
        if not e.get(k):continue
        parts,info=normalized_parts(name,k)
        reduced=[resample(p,256) for p in parts]
        pre=pair_distance_preflight(reduced,sigma=0.0)
        g128=gauss_midpoint(parts,128);g256=gauss_midpoint(parts,256)
        rec['sources'][k]={
            'file':e[k],'source_sha256':e[k+'_sha256'],
            'geometry':_edges_curve(parts),'source_normalization':info,
            'sampled_segment_preflight_N256':pre,
            'pairwise_gauss_N128':g128,
            'pairwise_gauss_N256':g256,
            'gauss_resolution_max_delta':float(max(abs(a-b) for a,b in zip(g128,g256))),
            'pairwise_near_zero_heuristic':bool(max(abs(v) for v in g256)<0.05),
            'topology_status':'GAUSS_ONLY_MILNOR_AND_ISOTOPY_UNRESOLVED'}
    if e.get('reference'):
        ref,_=normalized_parts(name,'reference')
        a=[resample(x,256) for x in orig]
        b=[resample(x,256) for x in ref]
        # Re-indexing and phase can affect this pointwise diagnostic.
        # The sampled nearest-neighbour Hausdorff is label-independent.
        haus=[]
        for x,y in zip(a,b):
            haus.append(float(max(np.max(cKDTree(x).query(y)[0]),np.max(cKDTree(y).query(x)[0]))))
        rec['source_resolution_comparison']={
            'sampled_bidirectional_hausdorff_at_N256':haus,
            'maximum_sampled_hausdorff':max(haus),
            'interpretation':'GEOMETRIC_CROSS_SOURCE_PROXIMITY_NOT_INDEPENDENT_DYNAMICS_OR_TOPOLOGY',
            'reference_is_distinct_source':bool(e['original_sha256']!=e['reference_sha256'])}
    else:
        rec['source_resolution_comparison']={'status':'NO_INDEPENDENT_REFERENCE_SOURCE',
            'warning':'Upsampling from 33-38 source points is not source-resolution convergence'}
    return rec
