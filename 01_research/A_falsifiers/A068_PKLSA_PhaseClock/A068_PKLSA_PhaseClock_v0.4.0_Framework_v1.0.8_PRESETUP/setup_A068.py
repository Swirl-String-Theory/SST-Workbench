"""A068 v0.4.0 one-command setup. Scientific overlay remains byte-identical.

Requires an existing, user-installed SST Falsifier Framework v1.0.8.
Never touches v0.2.0, private commitments, or any frozen scientific protocol.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CATALOG = "A068"
NAME = "PKLSA_PhaseClock"
VERSION = "v0.4.0"
DEFAULT_WORKBENCH = Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))
FREEZE_MARKER = Path('preregistration/FROZEN_PROTOCOL.json')
PLACEHOLDERS = ('REPLACE_BEFORE_FREEZE', r'\SSTTODO{', 'TODO_SCIENCE', '<<FILL')
SECTIONS = ('IDENTIFICATION','QUESTION','HYPOTHESES','ASSUMPTIONS','SYMBOLS',
            'EQUATIONS','ALGORITHM','SOURCES','GATES','NUMERICS','BACKENDS',
            'BLINDNESS','STATISTICS','RESULTS','INTERPRETATION','REPRODUCIBILITY')


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def loadj(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify_distribution() -> dict:
    manifest = loadj(HERE / 'BUNDLE_MANIFEST.json')
    checks = []
    for item in manifest['files']:
        path = HERE / item['path']
        if not path.is_file(): raise RuntimeError(f'Incomplete distribution: {item["path"]}')
        actual = digest(path)
        if actual != item['sha256']: raise RuntimeError(f'Distribution SHA256 mismatch: {item["path"]}')
        checks.append(item['path'])
    extra_overlay = set(p.relative_to(HERE).as_posix() for p in (HERE/'overlay').rglob('*') if p.is_file()) - set(checks)
    if extra_overlay: raise RuntimeError(f'Unregistered science-overlay file(s): {sorted(extra_overlay)}')
    return {'manifest_verified':len(checks),'overlay_files':sum(x.startswith('overlay/') for x in checks)}


def verify_science(root: Path) -> dict:
    sci = loadj(root/'science_contract.json')
    source = loadj(root/'source_contract.json')
    plan = loadj(root/'gate_plan.json')
    blind = loadj(root/'blind_policy.json')
    tex = (root/'report/FALSIFIER_REPORT.tex').read_text(encoding='utf-8')
    for f in (root/'science_contract.json',root/'source_contract.json',root/'gate_plan.json',root/'blind_policy.json'):
        content = f.read_text(encoding='utf-8')
        bad = [token for token in PLACEHOLDERS if token in content]
        if bad: raise RuntimeError(f'Unfilled preregistration field in {f}: {bad}')
    bad = [token for token in PLACEHOLDERS if token in tex]
    if bad: raise RuntimeError(f'Unfilled LaTeX preregistration field: {bad}')
    for section in SECTIONS:
        if f'SST-REPORT-SECTION:{section}' not in tex:
            raise RuntimeError(f'Report missing registered section: {section}')
    if sci.get('schema')!='SST-SCIENCE-CONTRACT-2': raise RuntimeError('Science contract schema mismatch')
    if source.get('schema')!='SST-SOURCE-CONTRACT-2': raise RuntimeError('Source contract schema mismatch')
    if plan.get('schema')!='SST-GATE-PLAN-2': raise RuntimeError('Gate-plan schema mismatch')
    if blind.get('schema')!='SST-BLIND-POLICY-2': raise RuntimeError('Blind-policy schema mismatch')
    required=('research_question','objective','null_hypothesis','alternative_hypothesis',
              'assumptions','symbols','equations','observables','steps','falsification_criteria')
    if any(not sci.get(key) for key in required): raise RuntimeError('Science contract empty required field')
    ids = [e['id'] for e in sci['equations']]
    if len(ids)!=len(set(ids)): raise RuntimeError('Duplicate equation ID')
    for e in sci['equations']:
        if any(not e.get(key) for key in ('id','purpose','latex','inputs','outputs','dimensional_check')):
            raise RuntimeError('Incomplete registered equation')
    gates = plan.get('gates',[])
    gate_ids=[g['gate_id'] for g in gates]
    if len(gate_ids)!=len(set(gate_ids)) or set(gate_ids)!={f'G{i}' for i in range(10)}:
        raise RuntimeError('Missing/duplicate gate IDs')
    byid={g['gate_id']:g for g in gates}
    for step in sci['steps']:
        if not step.get('operation') or not step.get('formula_refs') or not step.get('gate'):
            raise RuntimeError('Incomplete science step')
        if not set(step['formula_refs'])<=set(ids) or step['gate'] not in byid:
            raise RuntimeError(f'Unknown equation/gate referenced in step {step["id"]}')
    for gate in gates:
        if not set(gate.get('requires',[]))<=set(gate_ids):raise RuntimeError('Unknown gate dependency')
    visiting,visited=set(),set()
    def visit(n):
        if n in visiting: raise RuntimeError('Gate DAG cycle')
        if n in visited: return
        visiting.add(n)
        for dep in byid[n].get('requires',[]): visit(dep)
        visiting.remove(n);visited.add(n)
    for name in gate_ids:visit(name)
    sources=source.get('sources',[])
    if not sources or any(not all(x.get(k) for k in ('source_id','role','version','relative_path','independence_family','evidence_class','provenance_family')) for x in sources):
        raise RuntimeError('Source provenance incomplete')
    if not source.get('independent_unit') or not source.get('replication_policy',{}).get('min_independent_groups',0)>=2:
        raise RuntimeError('Independent source definition incomplete')
    if any(s['evidence_class']=='experimental' for s in sources):
        raise RuntimeError('Unqualified experimental source promoted')
    if len(set(s['provenance_family'] for s in sources))!=1:
        raise RuntimeError('Unregistered independent provider promoted')
    if blind['reveal_requires_gate']!='G8' or not blind.get('block_reveal_on_unresolved'):
        raise RuntimeError('Non-fail-closed reveal policy detected')
    if not (root/'experiment/pipeline.py').is_file(): raise RuntimeError('No real scientific pipeline')
    if VERSION not in tex: raise RuntimeError('Report version mismatch')
    return {'placeholder_fields':0,'report_sections':len(SECTIONS), 'registered_equations':len(ids),
            'registered_gates':len(gates),'sources':len(sources),
            'experimental_sources':0,'actual_provider_families':1,'reveal_fail_closed':True,
            'note':'Only structural/math-register consistency is checked; physical proof remains UNRESOLVED.'}


def verify_instance_source_matches_overlay(target: Path):
    for path in sorted((HERE/'overlay').rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(HERE/'overlay')
        installed=target/rel
        if not installed.is_file() or digest(path)!=digest(installed):
            raise RuntimeError(f'Existing instance diverged from distributed science overlay: {rel}. No overwrite; use a new scientific version.')


def verify_private(target:Path):
    p=target/'private'
    for name in ('REVEAL_NONCE.bin','OPAQUE_ID_KEY.bin'):
        f=p/name
        if not f.is_file() or f.stat().st_size<32:
            raise RuntimeError(f'Missing/short private key or nonce: {name}')
    for name in ('reveal.json','blind_forbidden_terms.txt'):
        if not (p/name).is_file(): raise RuntimeError(f'Missing framework-generated private file: {name}')
    mapping=loadj(p/'reveal.json')
    if mapping.get('schema')!='SST-PRIVATE-REVEAL-2':
        raise RuntimeError('Invalid private reveal schema')
    return {'local_private_material':'PRESENT_NOT_EXPORTED', 'mapping_has_targets':bool(mapping.get('targets'))}


def write_instance_readme_if_template(target:Path, already_frozen:bool)->str:
    readme=target/'README.md'
    if already_frozen:return 'PRESERVED_ALREADY_FROZEN'
    text=readme.read_text(encoding='utf-8') if readme.is_file() else ''
    generic=('Generated by SST Falsifier Framework' in text and
             'REPLACE_BEFORE_FREEZE' in text)
    if not text or generic:
        shutil.copy2(HERE/'INSTANCE_README.md',readme)
        return 'REPLACED_GENERATED_TEMPLATE' if generic else 'CREATED'
    if digest(readme)==digest(HERE/'INSTANCE_README.md'):
        return 'ALREADY_A068_SPECIFIC'
    # Never replace a user-edited README.
    return 'CUSTOM_README_PRESERVED'


def run_checked(cmd:list[str],cwd:Path,label:str):
    print(f'[{label}] {cmd} (cwd={cwd})', flush=True)
    subprocess.run(cmd,cwd=str(cwd),check=True)


def freeze_on_windows(target:Path):
    if os.name!='nt':
        raise RuntimeError('Official .cmd FREEZE runs only on Windows. The package can still be tested on Linux.')
    runall=target/'run_all.cmd'
    if not runall.is_file():raise RuntimeError('Official generated run_all.cmd missing')
    # cmd.exe ensures calling the official script with its own cwd and environment.
    run_checked(['cmd.exe','/d','/c','call',str(runall),'FREEZE'],target,'OFFICIAL-v1.0.8-FREEZE')
    marker=target/FREEZE_MARKER
    if not marker.is_file():raise RuntimeError('FREEZE command returned 0 but FROZEN_PROTOCOL.json was not created')
    return loadj(marker)


def main():
    parser=argparse.ArgumentParser(description='A068 0.4.0 presetup: install, validate, and perform official local FREEZE')
    parser.add_argument('--workbench-root',type=Path,default=DEFAULT_WORKBENCH)
    parser.add_argument('--verify-only',action='store_true',help='Only verify distribution and any installed instance; no writes')
    parser.add_argument('--no-freeze',action='store_true',help='Install and validate; leave FREEZE to a manual user command')
    parser.add_argument('--skip-tests',action='store_true',help='Skip scientific regression tests (not recommended)')
    args=parser.parse_args()
    verify_distribution()
    report=verify_science(HERE/'overlay')
    print('[PACKAGE VALID] A068-specific contracts present; no science placeholders.',flush=True)
    wb=args.workbench_root.resolve()
    framework=wb/'06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.8'
    target=wb/'01_research/A_falsifiers/A068_PKLSA_PhaseClock/A068-v0.4.0'
    if not framework.joinpath('tools/new_falsifier.py').is_file():
        raise RuntimeError(f'Official v1.0.8 framework is not installed: {framework}')
    if not target.exists():
        if args.verify_only:
            print(f'[NOT INSTALLED] {target}\nDistribution validation successful; --verify-only made no changes.');return 0
        # Official instance generator and overlay logic imported from the unchanged v0.4.0 package.
        from install_A068_v0_4_0 import install
        install(wb)
        print('[NEW INSTANCE] Official v1.0.8 generator used.',flush=True)
    elif not target.is_dir():
        raise RuntimeError(f'Instance target is not a folder: {target}')
    pin=target/'.sst_framework_root'
    if not pin.is_file() or (target/pin.read_text(encoding='utf-8').strip()).resolve()!=framework.resolve():
        raise RuntimeError('Missing or incorrect v1.0.8 relative framework pin')
    verify_instance_source_matches_overlay(target)
    verify_science(target)
    private=verify_private(target)
    frozen=(target/FREEZE_MARKER).is_file()
    print(f'[VERIFIED] 1-5 preconfigured; G3 physical status remains UNRESOLVED; private material: {private["local_private_material"]}',flush=True)
    if args.verify_only:
        print(f'[VERIFY-ONLY] FROZEN={frozen}; no files changed');return 0
    if frozen:
        print(f'[ALREADY FROZEN] Existing {FREEZE_MARKER}; no files or keys changed. Ready for BASIC/FULL/CERTIFY.');return 0
    changed=write_instance_readme_if_template(target,already_frozen=False)
    print(f'[README] {changed}',flush=True)
    if not args.skip_tests:
        run_checked([sys.executable,'-m','pytest','-q','tests'],target,'A068 REGRESSION TESTS')
    if args.no_freeze:
        print('[PREFLIGHT COMPLETE, UNFROZEN] Run run_all.cmd FREEZE from the instance to freeze.',flush=True)
        return 0
    frozen_data=freeze_on_windows(target)
    print(json.dumps({'status':'FROZEN','instance':str(target),'frozen_schema':frozen_data.get('schema'),
        'freeze_file':str(target/FREEZE_MARKER),'science_status':'NUMERICAL_EULER_MODEL_ONLY; PHYSICAL_G3_UNRESOLVED'},indent=2),flush=True)
    print('Ready: run_all.cmd BASIC  /  run_all.cmd FULL  /  run_all.cmd CERTIFY',flush=True)
    print('REVEAL_IF_ALLOWED remains blocked until science gates qualify; do not bypass.',flush=True)
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (RuntimeError,subprocess.CalledProcessError) as e:
        print(f'[FAIL-CLOSED] {type(e).__name__}: {e}',file=sys.stderr)
        raise SystemExit(2)
