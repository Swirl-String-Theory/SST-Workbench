from __future__ import annotations
import argparse,json
from pathlib import Path
from .geometry import discover,inventory_record
from .common import dump_json

def main():
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--out',default='outputs/inventory.json');p.add_argument('--n',type=int,default=96);a=p.parse_args();rows=[];errs=[]
 for f in discover(a.root):
  try: rows.append(inventory_record(f,a.n))
  except Exception as e: errs.append({'path':str(f),'error':repr(e)})
 out={'format':'SST-WP-INVENTORY-2.1','root':str(Path(a.root).resolve()),'file_count':len(rows)+len(errs),'ok':len(rows),'errors':errs,'records':rows};dump_json(a.out,out);print(json.dumps({'file_count':out['file_count'],'ok':len(rows),'errors':len(errs),'out':a.out},indent=2))
if __name__=='__main__':main()
