from __future__ import annotations
from pathlib import Path
import json, shutil, sys, traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework, verify_bundled_framework
FRAMEWORK=load_framework()
from sst_falsifier.protocol import assert_frozen
from sst_falsifier.blind import assert_blind_tree
from sst_falsifier.runner import run_mode
from sst_falsifier.outputs import make_output_manifest, pack_blind, pack_revealed
from .common import OUTPUT_NAME, PHASE_SLUGS, output_root, verify_source_archive, implementation_verify, write_json, read_json
from .phase_runner import main as run_phase

PHASES=list(PHASE_SLUGS)

def export_gate_folders(revealed: bool=False) -> dict:
    out=output_root(ROOT)
    ledger_path=out/('GATE_LEDGER_REVEALED.json' if revealed and (out/'GATE_LEDGER_REVEALED.json').is_file() else 'GATE_LEDGER.json')
    if not ledger_path.is_file(): return {'pass':False,'reason':f'missing {ledger_path.name}'}
    led=read_json(ledger_path); gate_root=out/'GATES'
    if gate_root.exists(): shutil.rmtree(gate_root)
    gate_root.mkdir(parents=True)
    rows=[]
    for rec in led.get('records',[]):
        gid=rec.get('gate_id') or rec.get('gate')
        if not gid: continue
        d=gate_root/gid; d.mkdir(parents=True,exist_ok=True)
        write_json(d/'GATE.json',rec)
        rows.append({'gate_id':gid,'status':rec.get('status'),'folder':str(d.relative_to(out)).replace('\\','/')})
    write_json(gate_root/'INDEX.json',{'schema':'A059-GATE-FOLDER-INDEX-1','authoritative_ledger':ledger_path.name,'gates':rows})
    return {'pass':True,'authoritative_ledger':ledger_path.name,'gate_count':len(rows)}

def verify_package() -> dict:
    return {'framework':verify_bundled_framework(),'source':verify_source_archive(ROOT),'implementation':implementation_verify(ROOT)}

def finalize_manifest_and_zip(revealed: bool=False):
    out=output_root(ROOT)
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    z=ROOT.parent/f'{OUTPUT_NAME}_{"REVEALED" if revealed else "BLIND"}.zip'
    (pack_revealed if revealed else pack_blind)(out,z) if revealed else pack_blind(ROOT,out,z)
    return z

def clean_blind_outputs():
    out=output_root(ROOT)
    if out.exists(): shutil.rmtree(out)
    for suffix in ('_BLIND.zip','_REVEALED.zip'):
        p=ROOT.parent/f'{OUTPUT_NAME}{suffix}'
        if p.exists(): p.unlink()

def run_blind() -> int:
    package=verify_package()
    if not (package['framework'].get('pass') and package['source'].get('pass') and package['implementation'].get('pass')):
        print(json.dumps(package,indent=2)); return 2
    assert_frozen(ROOT,ROOT/'preregistration'/'FROZEN_PROTOCOL.json'); assert_blind_tree(ROOT)
    clean_blind_outputs()
    phase_rows=[]
    for pid in PHASES:
        print(f'\n=== {pid} {PHASE_SLUGS[pid]} ===')
        try: rc=run_phase([pid])
        except Exception as exc:
            rc=1; print(f'phase launcher exception: {type(exc).__name__}: {exc}')
        # Phase scientific FAIL/UNRESOLVED normally still returns rc=0; launch/runtime errors are recorded and we continue.
        phase_rows.append({'phase_id':pid,'slug':PHASE_SLUGS[pid],'launcher_rc':rc})
    print('\n=== FRAMEWORK FULL FINALIZATION ===')
    rc=run_mode(ROOT,'FULL')
    gates=export_gate_folders(False)
    out=output_root(ROOT)
    write_json(out/'RUN_ALL_SUMMARY.json',{'schema':'A059-RUN-ALL-SUMMARY-1','mode':'BLIND','nonblocking':True,'phase_launches':phase_rows,'gate_export':gates,'framework_full_rc':rc})
    z=finalize_manifest_and_zip(False)
    print(f'\nBLIND complete: {out}\nBLIND package: {z}')
    return int(rc)

def run_reveal() -> int:
    out=output_root(ROOT)
    if not (out/'RUN_SUMMARY.json').is_file():
        print('No completed blind run found. Run run_all.cmd BLIND first.'); return 2
    rc=run_mode(ROOT,'REVEAL_IF_ALLOWED')
    revealed=(out/'RUN_SUMMARY_REVEALED.json').is_file()
    if revealed:
        from .reveal_analysis import main as reveal_analysis
        reveal_analysis()
    gates=export_gate_folders(revealed)
    write_json(out/'RUN_ALL_REVEAL_SUMMARY.json',{'schema':'A059-RUN-ALL-REVEAL-SUMMARY-1','revealed':revealed,'gate_export':gates,'framework_reveal_rc':rc})
    z=finalize_manifest_and_zip(revealed)
    print(f'\nReveal stage complete. package: {z}')
    return int(rc)

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv); mode=(argv[0] if argv else 'BLIND').upper()
    if mode in {'BLIND','FULL'}: return run_blind()
    if mode in {'REVEAL','REVEAL_IF_ALLOWED'}: return run_reveal()
    if mode=='ALL':
        rc=run_blind()
        if rc!=0: print('Blind launcher/finalization returned nonzero; continuing to reveal was not attempted.'); return rc
        return run_reveal()
    if mode=='VERIFY':
        p=verify_package(); print(json.dumps(p,indent=2)); return 0 if all(x.get('pass') for x in p.values()) else 1
    print('Usage: run_all.cmd [BLIND|REVEAL|ALL|VERIFY]'); return 2

if __name__=='__main__': raise SystemExit(main())
