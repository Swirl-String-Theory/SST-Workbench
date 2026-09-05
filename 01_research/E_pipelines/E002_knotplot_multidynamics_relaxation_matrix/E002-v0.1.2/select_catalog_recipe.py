from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidate',required=True); ap.add_argument('--approve',action='store_true'); ap.add_argument('--reason',default=''); a=ap.parse_args()
    design=json.loads((ROOT/'matrix_design.json').read_text()); e=next((x for x in design['entries'] if x['candidate']==a.candidate),None)
    if not e: raise SystemExit(f'unknown candidate: {a.candidate}')
    if e.get('history'): raise SystemExit('annealing history cannot be reduced automatically to one static catalog recipe; edit catalog_recipe.json explicitly')
    if a.approve and not a.reason.strip(): raise SystemExit('--reason is required with --approve')
    d={'schema_version':1,'recipe_id':f"FROM_{a.candidate}",'approved_for_catalog':bool(a.approve),'selected_from_candidate':a.candidate,'selection_basis':a.reason or 'Unapproved candidate seed','parameters':e['recipe']}
    (ROOT/'catalog_recipe.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8'); print(json.dumps(d,indent=2))
if __name__=='__main__': main()
