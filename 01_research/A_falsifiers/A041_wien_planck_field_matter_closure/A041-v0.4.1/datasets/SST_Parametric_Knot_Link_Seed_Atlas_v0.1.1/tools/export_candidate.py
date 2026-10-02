import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pklsa.atlas import write_xyz
p=argparse.ArgumentParser(); p.add_argument('candidate_id'); p.add_argument('output'); a=p.parse_args(); print(write_xyz(a.candidate_id,a.output))
