\
from __future__ import annotations
from pathlib import Path
import json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.run_knotplot_campaign import resolve_exe,resolve_workdir
from experiment.metrics import read_xyz

def main():
    exe,es=resolve_exe(''); wd,ws=resolve_workdir('')
    if exe is None or not exe.is_file(): raise SystemExit('INSTALL TEST FAIL: KnotPlot executable not found')
    out=ROOT/'private/install_test_runtime'
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    geom=out/'trefoil_install_test.txt'; script=out/'trefoil_install_test.kpc'; log=out/'trefoil_install_test.log'
    priv=json.loads((ROOT/'private/axis_map.json').read_text(encoding='utf-8'))
    pars=[m['parameter'] for m in priv['axes'].values()]
    lines=['reset all','load 3.1','refine nbeads 300','version',*[f'parameters {q}' for q in pars],f'save {geom.resolve().as_posix()} ascii']
    script.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    with script.open('rb') as inp,log.open('wb') as o:
        cp=subprocess.run([str(exe),'-stdin','-nographics'],cwd=wd,stdin=inp,stdout=o,stderr=subprocess.STDOUT)
    exports=list(out.glob('*.txt'))
    if cp.returncode!=0: raise SystemExit(f'INSTALL TEST FAIL: KnotPlot exit={cp.returncode}')
    if exports!=[geom]: raise SystemExit(f'INSTALL TEST FAIL: expected exactly one trefoil export, found {[p.name for p in exports]}')
    xyz=read_xyz(geom)
    if len(xyz)<100: raise SystemExit(f'INSTALL TEST FAIL: trefoil export has only {len(xyz)} usable points')
    meta={'schema':'A058-INSTALL-EXPORT-TEST-1','pass':True,'export_count':1,'points':int(len(xyz)),'executable':str(exe),'executable_source':es,'working_directory':str(wd),'working_directory_source':ws}
    (out/'result.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(f'INSTALL TEST PASS: exactly 1 trefoil ASCII export, {len(xyz)} points')
if __name__=='__main__':main()
