"""A075 CLI options: declared per-run selection, no secret or unreported overrides."""
import argparse
import json
from pathlib import Path
from experiment.science import profile_plan

def parse(argv):
    p=argparse.ArgumentParser(description='A075 3D Euler + Framework v1.0.10')
    p.add_argument('mode',nargs='?',choices=['FREEZE','BASIC','EXTENDED','FULL','PREVIEW','SELFTEST','REPORT_ONLY','REVEAL','REVEAL_IF_ALLOWED','GPU_PROBE'],default='BASIC')
    p.add_argument('--grid',type=int,help='base grid N, N^3 voxels')
    p.add_argument('--grid-up',type=int,help='spatial refinement grid N_up^3')
    p.add_argument('--dt',type=float,help='base absolute timestep; half-step also executed')
    p.add_argument('--t-end',type=float,help='physical final time, equal for both refinements')
    p.add_argument('--threads',type=int,default=12,help='SciPy FFT workers (default 12)')
    p.add_argument('--backend',choices=['cpu-scipy-fft','cpu-numpy-reference','cpp-hybrid','arc-xpu','torch-cpu-reference'],default='cpu-scipy-fft')
    p.add_argument('--backends',help='comma-separated py,cpp,gpu; backend-matrix mode')
    p.add_argument('--require-all-backends',action='store_true',help='fail closed before any physics run if a backend is absent')
    p.add_argument('--adaptive',dest='adaptive',action='store_true',default=True)
    p.add_argument('--fixed-dt',dest='adaptive',action='store_false')
    p.add_argument('--cfl',type=float,dest='cfl_target',default=0.15)
    p.add_argument('--max-core-shift',type=float,default=0.15)
    p.add_argument('--max-vorticity-turn',type=float,default=0.12)
    p.add_argument('--dt-min',type=float,default=1e-6)
    p.add_argument('--gpu-precision',choices=['fp32','fp64'],default='fp32')
    p.add_argument('--diagnostic-stride',type=int,default=2)
    p.add_argument('--knots',help='comma separated subset of 0_1,3_1,5_2,6_1')
    p.add_argument('--max-ram-gb',type=float,default=16.0)
    p.add_argument('--allow-expensive',action='store_true')
    p.add_argument('--plan',action='store_true',help='no compute / no framework changes')
    args=p.parse_args(argv)
    overrides={k:getattr(args,k) for k in ('grid','grid_up','dt','t_end','threads','backend','max_ram_gb','allow_expensive','adaptive','cfl_target','max_core_shift','max_vorticity_turn','dt_min','gpu_precision','diagnostic_stride','require_all_backends')}
    if args.knots:overrides['knots']=args.knots.split(',')
    if args.backends:overrides['backends']=[s.strip() for s in args.backends.split(',')]
    if args.mode in ('BASIC','EXTENDED','FULL','PREVIEW'):
        resolved=profile_plan(args.mode,overrides)
    else:
        if any(getattr(args,k) is not None for k in ('grid','grid_up','dt','t_end','knots')):
            p.error('scientific options only permitted for BASIC, EXTENDED, FULL or PREVIEW; FREEZE commits the allowed policy from science_contract.json')
        resolved=None
    return args,overrides,resolved
