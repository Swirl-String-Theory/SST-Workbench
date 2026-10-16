from __future__ import annotations
from pathlib import Path
import json,re,shutil,subprocess,sys,math
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.run_knotplot_campaign import resolve_exe,resolve_workdir
from experiment.metrics import read_xyz

def _run(exe,wd,script:Path,log:Path):
    with script.open('rb') as inp,log.open('wb') as out:
        return subprocess.run([str(exe),'-stdin','-nographics'],cwd=wd,stdin=inp,stdout=out,stderr=subprocess.STDOUT)

def _segment(text,a,b):
    i=text.find(a); j=text.find(b,i+len(a))
    if i<0 or j<0: raise RuntimeError(f'missing log markers {a}/{b}')
    return text[i+len(a):j]

def _all_params(seg):
    out={}
    for m in re.finditer(r'(?mi)^\s*([A-Za-z0-9_-]+)\s*=\s*([^\r\n]+)',seg):
        name=m.group(1).strip(); raw=m.group(2).strip(); low=raw.casefold()
        if low in {'on','true','yes'}: val=True
        elif low in {'off','false','no'}: val=False
        else:
            try: val=float(raw.split()[0])
            except ValueError: val=raw
        out[name]=val
    return out

def _resolve(params,candidates,label):
    lut={k.casefold():k for k in params}
    for c in candidates:
        if c.casefold() in lut:return lut[c.casefold()]
    raise RuntimeError(f'no runtime parameter found for sector {label}; candidates={candidates}')

def main():
    exe,es=resolve_exe(''); wd,ws=resolve_workdir('')
    if exe is None or not exe.is_file(): raise SystemExit('INSTALL TEST FAIL: KnotPlot executable not found')
    out=ROOT/'private/install_test_runtime'
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    priv=json.loads((ROOT/'private/axis_map.json').read_text(encoding='utf-8'))
    probe=out/'parameter_probe.kpc'; plog=out/'parameter_probe.log'
    probe.write_text('\n'.join(['reset all','version','collision fast','echo A058_DEFAULTS_BEGIN','parameters','echo A058_DEFAULTS_END','collision','echo A058_COLLISION_DONE'])+'\n',encoding='utf-8')
    cp=_run(exe,wd,probe,plog)
    txt=plog.read_text(encoding='utf-8',errors='replace')
    if cp.returncode!=0 or 'unknown command' in txt.casefold(): raise SystemExit('INSTALL TEST FAIL: reset/collision/default probe rejected; see parameter_probe.log')
    defaults=_all_params(_segment(txt,'A058_DEFAULTS_BEGIN','A058_DEFAULTS_END'))
    sliders={a:m['parameter'] for a,m in priv['axes'].items()}
    for a,p in sliders.items():
        if p not in defaults: raise SystemExit(f'INSTALL TEST FAIL: slider parameter not reported by runtime: {p}')
        if not isinstance(defaults[p],(int,float)): raise SystemExit(f'INSTALL TEST FAIL: slider is not numeric: {p}={defaults[p]!r}')
        if abs(float(defaults[p]))<1e-15: raise SystemExit(f'INSTALL TEST FAIL: default-relative multiplicative sweep undefined because {p} default is zero')
    resolved={r:_resolve(defaults,m['candidates'],m['label']) for r,m in priv['sectors'].items()}
    # One setter-liveness run, no exports.
    setter=out/'setter_probe.kpc'; slog=out/'setter_probe.log'; lines=['reset all','collision fast']
    expected={}
    for rid,name in resolved.items(): lines.append(f'{name} = on')
    for a,p in sliders.items():
        d=float(defaults[p]); v=d*1.25; expected[p]=v; lines.append(f'{p} = {v:.17g}')
    lines += ['echo A058_SETTERS_BEGIN','parameters','echo A058_SETTERS_END']
    setter.write_text('\n'.join(lines)+'\n',encoding='utf-8'); cp=_run(exe,wd,setter,slog); stxt=slog.read_text(encoding='utf-8',errors='replace')
    if cp.returncode!=0 or 'unknown command' in stxt.casefold(): raise SystemExit('INSTALL TEST FAIL: slider/sector assignment rejected; see setter_probe.log')
    applied=_all_params(_segment(stxt,'A058_SETTERS_BEGIN','A058_SETTERS_END'))
    for p,v in expected.items():
        if p not in applied or not math.isclose(float(applied[p]),v,rel_tol=1e-9,abs_tol=1e-12): raise SystemExit(f'INSTALL TEST FAIL: setter did not stick: {p}')
    for rid,name in resolved.items():
        if applied.get(name) is not True: raise SystemExit(f'INSTALL TEST FAIL: sector did not enable: {name}')
    # Exactly one trefoil export; no fixed long relaxation. go 1 is only a dynamics-liveness check.
    geom=out/'trefoil_install_test.txt'; script=out/'trefoil_install_test.kpc'; log=out/'trefoil_install_test.log'
    elec=resolved['R0']; lines=['reset all','collision fast','load 3.1','refine nbeads 300',f'{elec} = on','echo A058_START_SAFE_BEGIN','safe','echo A058_START_SAFE_END','go 1','echo A058_AFTER_GO_BEGIN','parameters','echo A058_AFTER_GO_END',f'save {geom.resolve().as_posix()} ascii']
    script.write_text('\n'.join(lines)+'\n',encoding='utf-8'); cp=_run(exe,wd,script,log)
    exports=list(out.glob('*.txt'))
    if cp.returncode!=0 or exports!=[geom]: raise SystemExit(f'INSTALL TEST FAIL: expected exactly one trefoil export, got {[p.name for p in exports]}')
    t2=log.read_text(encoding='utf-8',errors='replace')
    if 'unknown command' in t2.casefold(): raise SystemExit('INSTALL TEST FAIL: KnotPlot rejected install integration setup')
    safe=_segment(t2,'A058_START_SAFE_BEGIN','A058_START_SAFE_END').casefold(); safe_ok=('current position is safe' in safe and 'not safe' not in safe)
    if not safe_ok: raise SystemExit('INSTALL TEST FAIL: reset-default trefoil is not safe under No-Collide regime; no fitto override is permitted in v0.2.2')
    post=_all_params(_segment(t2,'A058_AFTER_GO_BEGIN','A058_AFTER_GO_END')); it=int(round(float(post.get('iteration',0))))
    if it<1: raise SystemExit('INSTALL TEST FAIL: go 1 did not advance iteration')
    xyz=read_xyz(geom)
    if len(xyz)<100: raise SystemExit(f'INSTALL TEST FAIL: export has only {len(xyz)} points')
    payload={'schema':'A058-INSTALL-EXPORT-TEST-4','pass':True,'export_count':1,'points':int(len(xyz)),'executable':str(exe),'executable_source':es,'working_directory':str(wd),'working_directory_source':ws,'defaults':defaults,'resolved_sectors':resolved,'setter_verification':True,'safe_start':True,'post_go_iteration':it,'regime':{'damped_source':'reset all documented default','collision_command':'collision fast','collision_avoidance':True}}
    (out/'defaults.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8'); (out/'result.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(f'INSTALL TEST PASS: 7 sliders live, 5 sectors resolvable, Damped+No-Collide setup accepted, exactly 1 trefoil export ({len(xyz)} points)')
if __name__=='__main__':main()
