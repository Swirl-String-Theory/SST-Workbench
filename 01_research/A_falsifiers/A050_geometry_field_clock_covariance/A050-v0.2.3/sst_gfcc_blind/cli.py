import os
# Independent trajectories are parallelized at the process level. Avoid nested BLAS/OpenMP oversubscription.
for _k in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_k,"1")

import argparse, json
from .runner import run_campaign

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config/default.json")
    ap.add_argument("--out",default="SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.3-outputs")
    ap.add_argument("--workers",type=int,default=None)
    ap.add_argument("--no-resume",action="store_true")
    a=ap.parse_args()
    r=run_campaign(a.config,a.out,workers=a.workers,resume=not a.no_resume)
    print(json.dumps({k:v for k,v in r.items() if k not in ("trajectories","amplitude_summary")},indent=2,default=str))
if __name__=="__main__": main()
