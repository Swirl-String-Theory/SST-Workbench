import argparse
from example_experiment.pipeline import run
p=argparse.ArgumentParser();p.add_argument("--config",default="configs/basic.json");p.add_argument("--out",default="SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0-outputs/basic")
a=p.parse_args();run(a.config,a.out)
