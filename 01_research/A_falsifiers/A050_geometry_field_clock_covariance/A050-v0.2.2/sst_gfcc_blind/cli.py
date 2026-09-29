import argparse, json
from pathlib import Path
from .runner import run_campaign


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',default='config/default.json')
    ap.add_argument('--out',default='SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.2-outputs')
    a=ap.parse_args()
    r=run_campaign(a.config,a.out)
    print(json.dumps({k:v for k,v in r.items() if k!='families'},indent=2))
if __name__=='__main__': main()
