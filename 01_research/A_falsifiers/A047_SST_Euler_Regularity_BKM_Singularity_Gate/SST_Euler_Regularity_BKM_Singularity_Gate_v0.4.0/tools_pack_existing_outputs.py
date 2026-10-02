from pathlib import Path
import json
from sst_bkm.campaign import NAME,VERSION,create_archives
ROOT=Path(__file__).resolve().parent
OUT=ROOT/f'{NAME}_{VERSION}-outputs'
required=[OUT/'BLIND'/'run_manifest.json',OUT/'BLIND'/'S00_parent_blind_selection.json',OUT/'BLIND'/'final_assessment.json',OUT/'REVEALED'/'S00_parent_selection_reveal.json',OUT/'REVEALED'/'e010_pklsa_v031_provenance.json']
missing=[str(p) for p in required if not p.is_file()]
if missing: raise SystemExit('Existing v0.4.0 output is incomplete; missing: '+'; '.join(missing))
archives=create_archives(ROOT,OUT,OUT/'REVEALED')
print(json.dumps({'status':'PACKED_EXISTING_OUTPUTS','output':str(OUT),'archives':archives},indent=2))
