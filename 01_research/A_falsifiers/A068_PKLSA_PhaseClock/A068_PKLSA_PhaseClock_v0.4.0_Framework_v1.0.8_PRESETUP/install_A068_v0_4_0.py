"""Install the A068 v0.4.0 science overlay via OFFICIAL v1.0.8 generator.
Do not copy this overlay into the frozen framework itself.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def install(workbench:Path)->Path:
    wb=workbench.expanduser().resolve()
    framework=wb/'06_templates'/'SST_Falsifier_Framework'/'SST_Falsifier_Framework_v1.0.8'
    generator=framework/'tools'/'new_falsifier.py'
    if not generator.is_file() or not (framework/'instance_template').is_dir():
        raise SystemExit('ERROR: official local SST Falsifier Framework v1.0.8 tree is required; no imitation/fallback allowed.')
    target=wb/'01_research'/'A_falsifiers'/'A068_PKLSA_PhaseClock'/'A068-v0.4.0'
    if target.exists():
        raise SystemExit(f'ERROR: target already exists; refusing overwrite: {target}')
    target.parent.mkdir(parents=True,exist_ok=True)
    args=[sys.executable,str(generator),'A068','PKLSA_PhaseClock',str(target),'--profile','multilibrary_gpu','--version','v0.4.0']
    subprocess.run(args,check=True,cwd=framework)
    source=HERE/'overlay'
    for file in sorted(source.rglob('*')):
        if file.is_file():
            relative=file.relative_to(source)
            dest=target/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,dest)
    # Set scientific module dependencies while preserving official generated dependencies.
    req=target/'requirements.txt'
    prior=req.read_text(encoding='utf-8') if req.exists() else ''
    for dep in ('numpy>=1.24','scipy>=1.10','pytest>=7'):
        if dep.split('>')[0].lower() not in prior.lower(): prior+=f'\n{dep}\n'
    req.write_text(prior,encoding='utf-8')
    pin=(target/'.sst_framework_root').read_text(encoding='utf-8').strip()
    if (target/pin).resolve()!=framework.resolve():
        raise RuntimeError('Framework pin mismatch. Stop before FREEZE.')
    payload={'schema':'SST-A068-INSTALL-1','target':str(target),
             'framework_pin':pin,'framework_location':str(framework),
             'status':'DEVELOPMENT_UNFROZEN','note':'Run instance tests and verify framework; FREEZE only after final registration. Physical G3 is measured, never assumed; upstream source is geometry-only.'}
    (target/'INSTALL_CHECK.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8')
    print(json.dumps(payload,indent=2));return target

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--workbench-root',type=Path,required=True)
    install(p.parse_args().workbench_root)
