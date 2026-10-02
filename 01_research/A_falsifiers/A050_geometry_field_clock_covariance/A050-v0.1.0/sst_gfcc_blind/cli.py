import argparse, json
from pathlib import Path
from .runner import run_campaign

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config/default.json")
    ap.add_argument("--out",default="SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs")
    ns=ap.parse_args()
    r=run_campaign(ns.config,ns.out)
    print(json.dumps({k:r[k] for k in ["stage","blind","verdict","qualified_family_count","family_count","divergence_gate","resolution_gate","resolution_exponent_span"]},indent=2))
if __name__=="__main__": main()
