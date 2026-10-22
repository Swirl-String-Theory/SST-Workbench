#!/usr/bin/env python3
"""Repair interrupted A006 ForceGrid 0.5.0c installations safely.

Never deletes runtime data, regenerates an existing plan, or overwrites a modified
force_grid_v050c.py. Supports dry-run, idempotent apply and guarded rollback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE / 'payload' / 'force_grid_v050c.py'
MOD = Path('tools/force_grid_v050c.py')
SEED = Path('Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz')
PLAN = Path('Output/qualification_v050c/PLAN.json')
OUT = Path('Output/qualification_v050c')
BACKUP = Path('patch_backups/v050c1_RUNNER_RECOVERY')
FGDISP = 'if /I "%~1"=="FORCEGRID" goto forcegrid'
FQDISP = 'if /I "%~1"=="FORCEQUAL" goto forcequal'
FG_BLOCK = ':forcegrid\npy -3 tools\\force_grid_v050c.py %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n'
FQ_BLOCK = ':forcequal\npy -3 tools\\force_qualification_v050b.py %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n'
RC_BEGIN = '% >>> A006_FORCEGRID_v050c_ALIASES_BEGIN'
RC_END = '% <<< A006_FORCEGRID_v050c_ALIASES_END'


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_text(p: Path) -> str:
    return p.read_text(encoding='utf-8-sig')


def write_text(p: Path, value: str):
    p.write_bytes(value.encode('utf-8'))


def inspect(root: Path) -> dict:
    for name in ('run_all.cmd', 'knotplotrc.kps', 'tools/selection_v050.py'):
        if not (root / name).is_file():
            raise RuntimeError(f'Incompatible A006 root: missing {name}')
    if not (root / SEED).is_file():
        raise RuntimeError(f'Expected 5_5_6 v0.5.0a seed is missing: {SEED}')
    cmd, rc = load_text(root / 'run_all.cmd'), load_text(root / 'knotplotrc.kps')
    if not cmd.lstrip().lower().startswith('@echo off') or ':usage' not in cmd or 'selection_v050.py' not in cmd:
        raise RuntimeError('Unexpected run_all.cmd structure: no automatic patch')
    if cmd.count('FORCEGRID') > 1 or cmd.count(':forcegrid\n') > 1:
        raise RuntimeError('Duplicate ForceGrid route detected: manual review required')
    mod = (root / MOD)
    if mod.exists() and sha(mod) != sha(PAYLOAD):
        raise RuntimeError('ForceGrid module differs from supplied v0.5.0c; do not replace modified code')
    grid_route = FGDISP in cmd
    grid_label = bool(re.search(r'^:forcegrid\s*$', cmd, flags=re.M|re.I))
    if grid_route != grid_label:
        raise RuntimeError('Incomplete ForceGrid dispatch label/branch; manual review required')
    if grid_route and FG_BLOCK not in cmd:
        raise RuntimeError('ForceGrid dispatch exists but target command differs; manual review required')
    fq_mod = (root / 'tools/force_qualification_v050b.py').is_file()
    fq_route = FQDISP in cmd
    fq_label = bool(re.search(r'^:forcequal\s*$', cmd, flags=re.M|re.I))
    if fq_route != fq_label:
        raise RuntimeError('Incomplete ForceQual dispatch label/branch; manual review required')
    if fq_route and FQ_BLOCK not in cmd:
        raise RuntimeError('Existing ForceQual dispatch differs; manual review required')
    alias_start = RC_BEGIN in rc
    alias_end = RC_END in rc
    if alias_start != alias_end:
        raise RuntimeError('Incomplete ForceGrid aliases block; do not blindly append')
    # Read fixed names straight from source to avoid depending on its package import.
    import ast
    tree = ast.parse(PAYLOAD.read_text(encoding='utf-8'))
    aliases = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'ALIASES':
            aliases = ast.literal_eval(node.value)
    if not aliases or len(aliases) != 14:
        raise RuntimeError('Unexpected bundled alias contract')
    if alias_start:
        for v in aliases.values():
            if not re.search(r'^\s*alias\s+' + re.escape(v) + r'\s+',rc,re.I|re.M):
                raise RuntimeError(f'ForceGrid aliases block lacks {v}')
    else:
        for v in aliases.values():
            if re.search(r'^\s*alias\s+' + re.escape(v) + r'\s+',rc,re.I|re.M):
                raise RuntimeError(f'Alias {v} already exists outside managed block; manual review required')
    plan_path = root / PLAN
    if plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        if plan.get('seed_sha256') != sha(root / SEED) or len(plan.get('arms',{})) != 14:
            raise RuntimeError('Existing plan does not match fixed seed and 14 arms')
        for arm, vals in plan['arms'].items():
            f = root / vals['script']
            if not f.is_file() or sha(f) != vals['script_sha256']:
                raise RuntimeError('Existing planned script absent/modified: '+str(f))
    elif (root / OUT).exists():
        raise RuntimeError('ForceGrid output exists without PLAN.json; preserve it and inspect manually')
    # A prior installer marker must never be overwritten or edited by the recovery.
    return {
        'grid_module': 'VALID' if mod.is_file() else 'MISSING',
        'grid_dispatch': 'VALID' if grid_route else 'MISSING',
        'grid_aliases': 'VALID' if alias_start else 'MISSING',
        'grid_plan': 'VALID' if plan_path.is_file() else 'MISSING',
        'forcequal_module': 'PRESENT' if fq_mod else 'ABSENT',
        'forcequal_dispatch': 'VALID' if fq_route else 'MISSING',
        'forcequal_can_repair': fq_mod and not fq_route,
        'run_all_sha256': sha(root/'run_all.cmd'),
        'knotplotrc_sha256': sha(root/'knotplotrc.kps'),
        'aliases': aliases,
    }


def transform(root: Path, state: dict):
    cmd, rc = load_text(root/'run_all.cmd'), load_text(root/'knotplotrc.kps')
    newcmd, newrc = cmd, rc
    if state['grid_dispatch'] == 'MISSING':
        anchor = 'cd /d "%~dp0"'
        if newcmd.count(anchor) != 1 or newcmd.count(':usage\n') != 1:
            raise RuntimeError('Cannot locate unique dispatch insertion anchors')
        newcmd = newcmd.replace(anchor,anchor+'\n'+FGDISP,1)
        newcmd = newcmd.replace(':usage\n',FG_BLOCK+':usage\n',1)
    if state['forcequal_can_repair']:
        anchor = 'cd /d "%~dp0"'
        if newcmd.count(anchor) != 1 or newcmd.count(':usage\n') != 1:
            raise RuntimeError('Cannot locate ForceQual insertion anchors')
        newcmd = newcmd.replace(anchor,anchor+'\n'+FQDISP,1)
        newcmd = newcmd.replace(':usage\n',FQ_BLOCK+':usage\n',1)
    if state['grid_aliases'] == 'MISSING':
        aliases = state['aliases']
        newrc = newrc.rstrip()+'\n\n'+RC_BEGIN+'\n'
        newrc += '\n'.join('alias '+short+' "read Output/qualification_v050c/scripts/FQ_'+arm+'.kps"' for arm,short in aliases.items())+'\n'+RC_END+'\n'
    return newcmd, newrc


def apply(root: Path):
    state = inspect(root)
    changes = [v for v in ('grid_module','grid_dispatch','grid_aliases','grid_plan') if state[v] == 'MISSING']
    if state['forcequal_can_repair']:
        changes.append('forcequal_dispatch')
    if not changes:
        print('ALREADY HEALTHY: no changes made; FORCEGRID TEST/PLAN/BUILD/ANALYZE available')
        return
    back = root / BACKUP
    if back.exists():
        raise RuntimeError(f'Recovery backup already exists: {back}; do not overwrite previous recovery')
    newcmd,newrc=transform(root,state)
    # Validate source code and fixed seed BEFORE writing anything to project.
    import importlib.util
    spec=importlib.util.spec_from_file_location('fg_recovery_module',PAYLOAD)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.selftest(root)
    # Back up exact original files unconditionally.
    back.mkdir(parents=True,exist_ok=False)
    shutil.copy2(root/'run_all.cmd',back/'run_all.cmd')
    shutil.copy2(root/'knotplotrc.kps',back/'knotplotrc.kps')
    old_mod_exists=(root/MOD).exists()
    try:
        if not old_mod_exists:
            (root/MOD).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(PAYLOAD,root/MOD)
        if state['grid_plan']=='MISSING':
            module.prepare(root)
        if newcmd!=load_text(root/'run_all.cmd'):
            write_text(root/'run_all.cmd',newcmd)
        if newrc!=load_text(root/'knotplotrc.kps'):
            write_text(root/'knotplotrc.kps',newrc)
        after=inspect(root)
        if not all(after[k]=='VALID' for k in ('grid_module','grid_dispatch','grid_aliases','grid_plan')):
            raise RuntimeError('Postinstall verification failed')
        meta = {'version':'v0.5.0c1','status':'REPAIRED','changed':changes,
                'before':{k:state[k] for k in state if k!='aliases'},
                'after':{k:after[k] for k in after if k!='aliases'},
                'module_created':not old_mod_exists}
        (back/'RECOVERY.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
        print('REPAIRED:',', '.join(changes))
        print('Now run: run_all.cmd FORCEGRID TEST')
        print('Then:    run_all.cmd FORCEGRID PLAN')
        if not (root/'tools/force_qualification_v050b.py').is_file():
            print('NOTE: FORCEQUAL is not installed here; use FORCEGRID (includes its six original arms).')
    except Exception:
        shutil.copy2(back/'run_all.cmd',root/'run_all.cmd')
        shutil.copy2(back/'knotplotrc.kps',root/'knotplotrc.kps')
        if not old_mod_exists:
            (root/MOD).unlink(missing_ok=True)
        print('Restored runner/RC after failure; any newly staged output retained for inspection.',file=sys.stderr)
        raise


def rollback(root: Path):
    back=root/BACKUP
    meta_path=back/'RECOVERY.json'
    if not meta_path.is_file():raise RuntimeError('No recovery manifest found')
    meta=json.loads(meta_path.read_text(encoding='utf-8'))
    for k,path in (('run_all_sha256','run_all.cmd'),('knotplotrc_sha256','knotplotrc.kps')):
        if sha(root/path)!=meta['after'][k]:
            raise RuntimeError('File changed since repair; refusing rollback: '+path)
    shutil.copy2(back/'run_all.cmd',root/'run_all.cmd')
    shutil.copy2(back/'knotplotrc.kps',root/'knotplotrc.kps')
    # Keep new module and all outputs: never delete user data.
    print('ROLLBACK: original run_all.cmd and knotplotrc.kps restored. Geometry/outputs untouched.')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',type=Path,default=Path('.'))
    opts=p.add_mutually_exclusive_group(required=True)
    opts.add_argument('--check',action='store_true')
    opts.add_argument('--apply',action='store_true')
    opts.add_argument('--rollback',action='store_true')
    opts.add_argument('--selftest',action='store_true')
    a=p.parse_args()
    if a.selftest:
        print('PASS: recovery installer source loads');return
    root=a.base.resolve()
    if a.check:
        s=inspect(root)
        print(json.dumps({k:v for k,v in s.items() if k!='aliases'},indent=2))
    elif a.apply:apply(root)
    elif a.rollback:rollback(root)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('REPAIR REFUSED:',exc,file=sys.stderr)
        raise SystemExit(2)
