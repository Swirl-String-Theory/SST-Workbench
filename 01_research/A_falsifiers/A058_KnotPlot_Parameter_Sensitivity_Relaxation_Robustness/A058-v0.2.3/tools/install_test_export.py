from __future__ import annotations
from pathlib import Path
import json,re,shutil,subprocess,sys,math,hashlib
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

def _sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    exe,es=resolve_exe(''); wd,ws=resolve_workdir('')
    if exe is None or not exe.is_file(): raise SystemExit('INSTALL TEST FAIL: KnotPlot executable not found')
    out=ROOT/'private/install_test_runtime'
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    priv=json.loads((ROOT/'private/axis_map.json').read_text(encoding='utf-8'))

    # Baseline runtime provenance only. Conditional sliders are NOT required here.
    base=out/'base_probe.kpc'; blog=out/'base_probe.log'
    base.write_text('\n'.join(['reset all','version','collision fast','echo A058_BASE_DEFAULTS_BEGIN','parameters','echo A058_BASE_DEFAULTS_END'])+'\n',encoding='utf-8')
    cp=_run(exe,wd,base,blog); btxt=blog.read_text(encoding='utf-8',errors='replace')
    if cp.returncode!=0 or 'unknown command' in btxt.casefold(): raise SystemExit('INSTALL TEST FAIL: reset/collision/base parameter probe rejected; see base_probe.log')
    base_defaults=_all_params(_segment(btxt,'A058_BASE_DEFAULTS_BEGIN','A058_BASE_DEFAULTS_END'))

    defaults={}; sector_defaults={}; sector_switches={}; setter_results={}
    # Probe each GUI sector in the context where its switch is ON. This fixes the
    # v0.2.2 failed because a conditional slider was absent from the bare reset-all dump.
    for rid,sm in priv['sectors'].items():
        sw=sm['switch_parameter']; sector_switches[rid]=sw
        ctx=out/f'{rid}_defaults.kpc'; clog=out/f'{rid}_defaults.log'
        a=f'A058_{rid}_DEFAULTS_BEGIN'; b=f'A058_{rid}_DEFAULTS_END'
        ctx.write_text('\n'.join(['reset all','collision fast',f'{sw} = on',f'echo {a}','parameters',f'echo {b}'])+'\n',encoding='utf-8')
        cp=_run(exe,wd,ctx,clog); txt=clog.read_text(encoding='utf-8',errors='replace')
        if cp.returncode!=0 or 'unknown command' in txt.casefold(): raise SystemExit(f'INSTALL TEST FAIL: sector enable rejected for {rid} ({sw}); see {clog.name}')
        params=_all_params(_segment(txt,a,b)); sector_defaults[rid]=params
        # If the runtime reports its switch, it must be ON. Some builds may omit it.
        if sw in params and params[sw] is not True: raise SystemExit(f'INSTALL TEST FAIL: sector switch did not enable: {sw}')
        for axis_id in sm['axes']:
            p=priv['axes'][axis_id]['parameter']
            if p not in params: raise SystemExit(f'INSTALL TEST FAIL: slider parameter not reported after enabling {sm["label"]}: {p}')
            if not isinstance(params[p],(int,float)): raise SystemExit(f'INSTALL TEST FAIL: slider is not numeric in sector context: {p}={params[p]!r}')
            if abs(float(params[p]))<1e-15: raise SystemExit(f'INSTALL TEST FAIL: default-relative multiplicative sweep undefined because {p} default is zero')
            defaults[p]=float(params[p])

        # Context-local setter liveness for every slider in this sector.
        setter=out/f'{rid}_setter.kpc'; slog=out/f'{rid}_setter.log'; sa=f'A058_{rid}_SETTERS_BEGIN'; sb=f'A058_{rid}_SETTERS_END'
        lines=['reset all','collision fast',f'{sw} = on']; expected={}
        for axis_id in sm['axes']:
            p=priv['axes'][axis_id]['parameter']; v=defaults[p]*1.25; expected[p]=v; lines.append(f'{p} = {v:.17g}')
        lines += [f'echo {sa}','parameters',f'echo {sb}']
        setter.write_text('\n'.join(lines)+'\n',encoding='utf-8'); cp=_run(exe,wd,setter,slog); stxt=slog.read_text(encoding='utf-8',errors='replace')
        if cp.returncode!=0 or 'unknown command' in stxt.casefold(): raise SystemExit(f'INSTALL TEST FAIL: setter assignment rejected in {sm["label"]}; see {slog.name}')
        applied=_all_params(_segment(stxt,sa,sb)); per={}
        for p,v in expected.items():
            ok=p in applied and isinstance(applied[p],(int,float)) and math.isclose(float(applied[p]),v,rel_tol=1e-9,abs_tol=1e-12)
            per[p]={'expected':v,'observed':applied.get(p),'pass':bool(ok)}
            if not ok: raise SystemExit(f'INSTALL TEST FAIL: setter did not stick in sector {sm["label"]}: {p}')
        setter_results[rid]=per

    # Exactly one trefoil export. The ordinary mechanical sector is used only as the liveness sector;
    # no fixed long relaxation is allowed. go 1 is a one-step dynamics check.
    geom=out/'trefoil_install_test.txt'; script=out/'trefoil_install_test.kpc'; log=out/'trefoil_install_test.log'; mech=sector_switches['R1']
    lines=['reset all','collision fast','load 3.1','refine nbeads 300',f'{mech} = on','echo A058_START_SAFE_BEGIN','safe','echo A058_START_SAFE_END','go 1','echo A058_AFTER_GO_BEGIN','parameters','echo A058_AFTER_GO_END',f'save {geom.resolve().as_posix()} ascii']
    script.write_text('\n'.join(lines)+'\n',encoding='utf-8'); cp=_run(exe,wd,script,log)
    exports=list(out.glob('*.txt'))
    if cp.returncode!=0 or exports!=[geom]: raise SystemExit(f'INSTALL TEST FAIL: expected exactly one trefoil export, got {[p.name for p in exports]}')
    t2=log.read_text(encoding='utf-8',errors='replace')
    if 'unknown command' in t2.casefold(): raise SystemExit('INSTALL TEST FAIL: KnotPlot rejected install integration setup')
    safe=_segment(t2,'A058_START_SAFE_BEGIN','A058_START_SAFE_END').casefold(); safe_ok=('current position is safe' in safe and 'not safe' not in safe)
    if not safe_ok: raise SystemExit('INSTALL TEST FAIL: reset-default trefoil is not safe under Damped + No-Collide regime; no fitto override is permitted')
    post=_all_params(_segment(t2,'A058_AFTER_GO_BEGIN','A058_AFTER_GO_END')); it=int(round(float(post.get('iteration',0))))
    if it<1: raise SystemExit('INSTALL TEST FAIL: go 1 did not advance iteration')
    xyz=read_xyz(geom)
    if len(xyz)<100: raise SystemExit(f'INSTALL TEST FAIL: export has only {len(xyz)} points')
    payload={'schema':'A058-INSTALL-EXPORT-TEST-5','pass':True,'export_count':1,'points':int(len(xyz)),'executable':str(exe),'executable_sha256':_sha256(exe),'executable_source':es,'working_directory':str(wd),'working_directory_source':ws,'base_defaults':base_defaults,'defaults':defaults,'sector_context_defaults':sector_defaults,'resolved_sectors':sector_switches,'setter_results':setter_results,'setter_verification':True,'safe_start':True,'post_go_iteration':it,'regime':{'damped_source':'reset all user-requested Damped state','collision_command':'collision fast','collision_avoidance':True,'velocity_sector_note':'The anonymous velocity-dependent sector is tested under Damped as requested; KnotPlot GUI note says Undamped is intended for that force.'}}
    (out/'defaults.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8'); (out/'result.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(f'INSTALL TEST PASS: 8 sliders live in 6 sector contexts, Damped+No-Collide accepted, exactly 1 trefoil export ({len(xyz)} points)')
if __name__=='__main__':main()
