import argparse,json
from .transfer import main_run

def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',required=True); p.add_argument('--out',required=True); a=p.parse_args(); r=main_run(a.config,a.out); print(json.dumps({'stage':r['stage'],'blind':r['blind'],'version':r['version'],'verdict':r['verdict'],'modal_transfer_gate':r['modal_transfer_gate'],'temporal_memory_transfer_gate':r['temporal_memory_transfer_gate'],'spatial_gate':r['spatial_gate'],'divergence_gate':r['divergence_gate']},indent=2))
if __name__=='__main__': main()
