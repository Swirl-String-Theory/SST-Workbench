"""Atlas discovery / selection / explicit create-only export for a generated instance."""
import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('instance');p.add_argument('action',choices=['verify','select','export'])
p.add_argument('--workbench');p.add_argument('--topology');p.add_argument('--embedding');p.add_argument('--collection');p.add_argument('--limit',type=int,default=10)
p.add_argument('--id',action='append',default=[]);p.add_argument('--output');p.add_argument('--allow-research',action='store_true')
a=p.parse_args();root=Path(a.instance).resolve()
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst_falsifier.pklsa_integration import check_atlas,select_ids,export_dataset
from sst_falsifier.config import load_instance_config
cfg=load_instance_config(root)
if a.workbench:
 import os;os.environ['SST_WORKBENCH_ROOT']=a.workbench
if a.action=='verify':result=check_atlas(root,cfg);ok=result['status']=='AVAILABLE'
elif a.action=='select':result={'ids':select_ids(root,cfg,topology=a.topology,embedding=a.embedding,
                            collection=a.collection,limit=a.limit,allow_research=a.allow_research)};ok=True
else:
 if not a.id or not a.output: p.error('export requires --id and --output')
 result=export_dataset(root,cfg,a.id,a.output,allow_research=a.allow_research);ok=True
print(json.dumps(result,indent=2,default=str));raise SystemExit(0 if ok else 4)
