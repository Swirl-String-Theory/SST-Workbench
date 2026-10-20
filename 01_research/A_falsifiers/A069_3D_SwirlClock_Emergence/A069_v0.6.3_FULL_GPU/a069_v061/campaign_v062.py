"""A069 v0.6.2 frozen DEVELOPMENT campaign preflight. No physical claims."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from math import ceil

BOX=10.0
MIN_CELLS=4.0
MAX_CURV_CORE=.30
MAX_GAP_RATIO=.30
# Geometry values are READ from the pinned v0.6.1 input JSON runs, rather than refitting.
# The runtime always recomputes these from full source geometry.
GEOMETRY_BASELINES={
    'A':{'d_screen':0.28411742649850696,'kappa_max':1.672964463951516},
    'B':{'d_screen':1.1365837826330705,'kappa_max':1.0231000798236332},
}

@dataclass(frozen=True)
class Case:
    case_id:str
    kind:str
    n:int
    xi:float
    box:float=BOX
    dt:float=.003
    steps:int=16
    segments:int=96
    tier:str='DIAGNOSTIC'
    notes:str=''

# Both historic knots at 160^3, with optional higher grids. A can only
# meet this screening protocol at N ~>= 470; choose 512, not 320.
CASES={c.case_id:c for c in [
    Case('A32_SMOKE','A',32,.08,steps=2,tier='DEVELOPMENT_SMOKE',notes='Tiny non-qualifying runner test'),
    Case('B48_SMOKE','B',48,.28,steps=2,tier='DEVELOPMENT_SMOKE',notes='Tiny non-qualifying runner test'),
    Case('A160','A',160,.08,notes='Required 160^3 Fourier A diagnostic: insufficient xi/dx'),
    Case('B160','B',160,.28,tier='PREQUALIFICATION',notes='Primary geometrically admissible Torus B pilot'),
    Case('B192','B',192,.28,tier='REFINEMENT',notes='Grid-only resolution refinement of B160'),
    Case('B256','B',256,.28,tier='REFINEMENT',notes='High-RAM grid-only refinement of B160'),
    Case('B192_CORE024','B',192,.24,tier='CORE_REFINEMENT',notes='Independent core-scale variation on B192; still a preflight'),
    Case('B256_CORE024','B',256,.24,tier='CORE_REFINEMENT',notes='Independent core-scale variation on B256; still a preflight'),
    Case('A320','A',320,.08,tier='DIAGNOSTIC',notes='Intermediate A grid: still fails >=4 cells/xi'),
    Case('A512','A',512,.08,tier='HIGH_MEMORY_RESEARCH',notes='First nominated geometry-compliant A grid; extremely costly'),
]}


def allowed_core_window(kind:str,n:int,box:float=BOX, geometry=None):
    """The complete interval that can satisfy all three preregistered gates."""
    g=geometry or GEOMETRY_BASELINES[kind]
    lower=MIN_CELLS*box/n
    upper=min(MAX_CURV_CORE/g['kappa_max'],MAX_GAP_RATIO*g['d_screen'])
    return {'xi_min_resolution':lower,'xi_max_geometry':upper,
            'feasible':lower<=upper,'first_possible_even_grid':2*ceil((MIN_CELLS*box/upper)/2),
            'not_a_certified_reach':True}


def screening(kind:str,n:int,xi:float,box:float=BOX,geometry=None):
    g=geometry or GEOMETRY_BASELINES[kind]
    metrics={'cells_per_xi':xi*n/box,'xi_times_kappa':xi*g['kappa_max'],
             'xi_over_nonlocal_gap':xi/g['d_screen']}
    gates={'resolution':metrics['cells_per_xi']>=MIN_CELLS,
           'curvature':metrics['xi_times_kappa']<=MAX_CURV_CORE,
           'nonlocal_separation':metrics['xi_over_nonlocal_gap']<=MAX_GAP_RATIO}
    return {'kind':kind,'n':n,'xi':xi,'box':box,'metrics':metrics,'gates':gates,
            'all_preconditions_met':all(gates.values()),
            'status':'PASS_GEOMETRY_SCREEN_ONLY' if all(gates.values()) else 'FAIL_CLOSED_GEOMETRY',
            'window':allowed_core_window(kind,n,box,g)}


def resource_forecast(n:int,available_bytes=None):
    """Conservative budgeting for 3D array copies during Numba solid angle + FFT.

    This is an estimate, not measured peak; the runner checks actual available
    system RAM and may refuse the allocation. Not a GPU/VRAM estimate.
    """
    vox=n**3
    array_mib=vox*16/2**20
    estimate=int(vox*650+1.5*(2**30))
    usable=None if available_bytes is None else int(max(0,available_bytes-1.0*(2**30)))
    return {'n':n,'voxels':vox,'complex128_array_mib':round(array_mib,1),
      'conservative_peak_gib':round(estimate/2**30,2),'available_gib':None if available_bytes is None else round(available_bytes/2**30,2),
      'fits_budget':None if usable is None else estimate<=usable,
      'forecast_only':True,'recommend_checkpoint':n>=160}


def case_payload(c:Case):
    return {'case':asdict(c),'screening_preview':screening(c.kind,c.n,c.xi,c.box),
            'forecast':resource_forecast(c.n),'physical_status':'UNRESOLVED'}
