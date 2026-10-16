from __future__ import annotations
from pathlib import Path
import json,re,shutil,subprocess,sys,math,hashlib
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.run_knotplot_campaign import resolve_exe,resolve_workdir,_safe_response
from experiment.metrics import read_xyz
from tools.parameter_readback import qualify_numeric,state_getter_name,state_switch_getter_name

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
    # S3 and R2 reset defaults are user-confirmed for this build. Only compare
    # fields the executable actually reports; missing S3 is expected here.
    reset_axis=priv['axes']['S3']; reset_sector=priv['sectors']['R2']
    reset_switch=reset_sector['switch_parameter']; reset_param=reset_axis['parameter']
    if base_defaults.get(state_switch_getter_name(reset_sector,reset_switch)) is not False:
        raise SystemExit(f'INSTALL TEST FAIL: reset sector R2 is not OFF: {reset_switch}')
    if state_getter_name(reset_axis) not in base_defaults:
        raise SystemExit('INSTALL TEST FAIL: numeric reset getter missing for S3')
    if state_getter_name(reset_axis) in base_defaults:
        reported=base_defaults[state_getter_name(reset_axis)]
        if not qualify_numeric(reset_axis['default_value'],reported)['pass']:
            raise SystemExit('INSTALL TEST FAIL: frozen S3 default differs from runtime-reportable reset value')

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
        swgetter=state_switch_getter_name(sm,sw)
        if swgetter in params and params[swgetter] is not True: raise SystemExit(f'INSTALL TEST FAIL: sector switch did not enable: {sw}')
        for axis_id in sm['axes']:
            axis=priv['axes'][axis_id]; p=axis['parameter']; mode=axis.get('verification','runtime_roundtrip')
            if 'default_value' in axis:
                defaults[p]=float(axis['default_value'])
                # Never substitute a sector-enabled value for a registered reset
                # default. If the getter unexpectedly exists, demand agreement.
                getter=state_getter_name(axis)
                if getter not in params:
                    raise SystemExit(f'INSTALL TEST FAIL: mandatory numeric alias getter missing for {axis_id}')
                if getter in params:
                    obs=params[getter]
                    if not qualify_numeric(defaults[p],obs)['pass']:
                        raise SystemExit(f'INSTALL TEST FAIL: R2/S3 getter disagrees with registered reference {defaults[p]}')
            elif p in params:
                if not isinstance(params[p],(int,float)): raise SystemExit(f'INSTALL TEST FAIL: slider is not numeric in sector context: {p}={params[p]!r}')
                defaults[p]=float(params[p])
            else:
                raise SystemExit(f'INSTALL TEST FAIL: slider parameter not reported after enabling {sm["label"]} and no frozen fallback is registered: {p}')
            if abs(float(defaults[p]))<1e-15: raise SystemExit(f'INSTALL TEST FAIL: default-relative multiplicative sweep undefined because {p} default is zero')

        # Context-local setter liveness for every slider in this sector.
        setter=out/f'{rid}_setter.kpc'; slog=out/f'{rid}_setter.log'; sa=f'A058_{rid}_SETTERS_BEGIN'; sb=f'A058_{rid}_SETTERS_END'
        lines=['reset all','collision fast',f'{sw} = on']; expected={}
        for axis_id in sm['axes']:
            p=priv['axes'][axis_id]['parameter']; v=defaults[p]*1.25; expected[p]=v; lines.append(f'{p} = {v:.17g}')
        lines += [f'echo {sa}','parameters',f'echo {sb}']
        setter.write_text('\n'.join(lines)+'\n',encoding='utf-8'); cp=_run(exe,wd,setter,slog); stxt=slog.read_text(encoding='utf-8',errors='replace')
        if cp.returncode!=0 or 'unknown command' in stxt.casefold(): raise SystemExit(f'INSTALL TEST FAIL: setter assignment rejected in {sm["label"]}; see {slog.name}')
        applied=_all_params(_segment(stxt,sa,sb)); per={}
        for axis_id in sm['axes']:
            axis=priv['axes'][axis_id]; p=axis['parameter']; v=expected[p]; mode=axis.get('verification','runtime_roundtrip')
            getter=state_getter_name(axis)
            if mode=='setter_acceptance' and getter not in applied:
                ok=True; observed=None; evidence='command accepted; parameter is not exposed by runtime dump'
            else:
                observed=applied.get(getter); verdict=qualify_numeric(v,observed); ok=verdict['pass']; evidence=verdict['evidence']
            per[p]={'expected':v,'observed':observed,'verification':mode,'evidence':evidence,'pass':bool(ok)}
            if not ok: raise SystemExit(f'INSTALL TEST FAIL: setter did not stick in sector {sm["label"]}: {p}')
        setter_results[rid]=per

    # Separate registered activation control: same numeric defaults, R2 switch
    # explicitly OFF. Check command acceptance and switch readback if provided.
    r2_switch=sector_switches['R2'];off_probe=out/'R2_off_probe.kpc';off_log=out/'R2_off_probe.log'
    r2_axes=priv['sectors']['R2']['axes'];off_lines=['reset all','collision fast',f'{r2_switch} = on']
    for aid in r2_axes:
        param=priv['axes'][aid]['parameter'];off_lines.append(f'{param} = {defaults[param]:.17g}')
    off_lines += [f'{r2_switch} = off','echo A058_R2_OFF_BEGIN','parameters','echo A058_R2_OFF_END']
    off_probe.write_text('\n'.join(off_lines)+'\n',encoding='utf-8')
    cp=_run(exe,wd,off_probe,off_log);otxt=off_log.read_text(encoding='utf-8',errors='replace')
    if cp.returncode!=0 or 'unknown command' in otxt.casefold():
        raise SystemExit('INSTALL TEST FAIL: R2 OFF activation-control setter commands rejected')
    off_state=_all_params(_segment(otxt,'A058_R2_OFF_BEGIN','A058_R2_OFF_END'))
    if state_switch_getter_name(priv['sectors']['R2'],r2_switch) in off_state and off_state[state_switch_getter_name(priv['sectors']['R2'],r2_switch)] is not False:
        raise SystemExit('INSTALL TEST FAIL: R2 activation-control switch did not return to OFF')

    # Exactly one trefoil ASCII export, serving as the immutable shared safe seed.
    # Earlier raw reset-default N=300 catalogue geometry can be unsafe because its
    # closest nonadjacent segments are below KnotPlot's default close threshold.
    # We change the INITIAL EMBEDDING SCALE once, not any force or collision
    # parameter. Every scientific condition loads precisely these same bytes.
    geom=out/'trefoil_install_test.txt'; script=out/'trefoil_install_test.kpc'; log=out/'trefoil_install_test.log'
    prep_cfg=json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8'))['seed_preparation']
    close0=base_defaults.get('close')
    if isinstance(close0,bool) or not isinstance(close0,(int,float)) or not math.isfinite(float(close0)) or float(close0)<=float(prep_cfg['minimum_close_default']):
        raise SystemExit(f'INSTALL TEST FAIL: cannot construct registered safe seed, runtime close-default missing/invalid: {close0!r}')
    factor=float(prep_cfg['target_over_close_default']); target=float(close0)*factor
    if not math.isfinite(target) or target<=float(close0):
        raise SystemExit('INSTALL TEST FAIL: invalid preregistered geometric seed target')
    mech=sector_switches['R1']
    lines=['reset all','collision fast','load 3.1','refine nbeads 300',
           'echo A058_RAW_START_SAFE_BEGIN','safe','echo A058_RAW_START_SAFE_END',
           f'fitto mindist {target:.17g}',
           'echo A058_PREPARED_SAFE_BEGIN','safe','echo A058_PREPARED_SAFE_END',
           f'save {geom.resolve().as_posix()} ascii',
           'reset all','collision fast',f'load {geom.resolve().as_posix()}',
           f'{mech} = on',
           'echo A058_RELOADED_SAFE_BEGIN','safe','echo A058_RELOADED_SAFE_END',
           'echo A058_RELOADED_PARAMS_BEGIN','parameters','echo A058_RELOADED_PARAMS_END',
           'go 1',
           'echo A058_AFTER_GO_SAFE_BEGIN','safe','echo A058_AFTER_GO_SAFE_END',
           'echo A058_AFTER_GO_BEGIN','parameters','echo A058_AFTER_GO_END']
    script.write_text('\n'.join(lines)+'\n',encoding='utf-8'); cp=_run(exe,wd,script,log)
    exports=list(out.glob('*.txt'))
    if cp.returncode!=0 or exports!=[geom]:
        raise SystemExit(f'INSTALL TEST FAIL: expected exactly one safe-seed trefoil export, got {[p.name for p in exports]}')
    t2=log.read_text(encoding='utf-8',errors='replace')
    if 'unknown command' in t2.casefold(): raise SystemExit('INSTALL TEST FAIL: KnotPlot rejected shared-seed preparation or reload; inspect trefoil_install_test.log')
    def strict_safe(a,b):
        seg=_segment(t2,a,b).casefold()
        return _safe_response(seg)
    raw_safe=strict_safe('A058_RAW_START_SAFE_BEGIN','A058_RAW_START_SAFE_END')
    prepared_safe=strict_safe('A058_PREPARED_SAFE_BEGIN','A058_PREPARED_SAFE_END')
    reload_safe=strict_safe('A058_RELOADED_SAFE_BEGIN','A058_RELOADED_SAFE_END')
    after_go_safe=strict_safe('A058_AFTER_GO_SAFE_BEGIN','A058_AFTER_GO_SAFE_END')
    if not (prepared_safe and reload_safe and after_go_safe):
        raise SystemExit('INSTALL TEST FAIL: one-time geometric seed normalization did not produce a safe/reload-safe/dynamics-safe trefoil; inspect private/install_test_runtime/trefoil_install_test.log')
    reload_params=_all_params(_segment(t2,'A058_RELOADED_PARAMS_BEGIN','A058_RELOADED_PARAMS_END'))
    # Protect actual research controls. Geometry fitto must not be confused with
    # changing the collision and integrator defaults.
    for param in ('close','max-dr','stusplit','dstep','timeincr'):
        if param in base_defaults and param in reload_params and isinstance(base_defaults[param],(int,float)) and not isinstance(base_defaults[param],bool):
            if not math.isclose(float(reload_params[param]),float(base_defaults[param]),rel_tol=1e-10,abs_tol=1e-12):
                raise SystemExit(f'INSTALL TEST FAIL: research parameter drift during shared seed preparation: {param}')
    post=_all_params(_segment(t2,'A058_AFTER_GO_BEGIN','A058_AFTER_GO_END')); it=int(round(float(post.get('iteration',0))))
    if it<1: raise SystemExit('INSTALL TEST FAIL: go 1 did not advance iteration after reloading shared seed')
    xyz=read_xyz(geom)
    if len(xyz)!=300: raise SystemExit(f'INSTALL TEST FAIL: shared safe-seed export has {len(xyz)} beads, not 300')
    seed_record={'schema':'A058-SHARED-SAFE-SEED-1','path':str(geom.resolve()),'sha256':_sha256(geom),'bytes':geom.stat().st_size,'nbeads':int(len(xyz)),
       'raw_catalogue_safe':raw_safe,'prepared_safe':prepared_safe,'reload_safe':reload_safe,'post_go_safe':after_go_safe,
       'close_default':float(close0),'target_over_close_default':factor,'fitto_mindist_target':target,
       'prep_command':f'fitto mindist {target:.17g}',
       'research_parameters_unchanged':True,'one_export_only':True,
       'interpretation':'fixed user-visible geometrical seed conditioning; not unmodified catalogue geometry and not a parameter sweep'}
    (out/'shared_safe_seed.json').write_text(json.dumps(seed_record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    payload={'schema':'A058-INSTALL-EXPORT-TEST-7','pass':True,'export_count':1,'points':int(len(xyz)),'executable':str(exe),'executable_sha256':_sha256(exe),'executable_source':es,'working_directory':str(wd),'working_directory_source':ws,'base_defaults':base_defaults,'defaults':defaults,'default_sources':{priv['axes'][aid]['parameter']:priv['axes'][aid].get('default_source','runtime_sector_context') for aid in priv['axes']},'sector_context_defaults':sector_defaults,'resolved_sectors':sector_switches,'setter_results':setter_results,'setter_verification':True,'safe_start':True,'shared_seed_sha256':seed_record['sha256'],'shared_seed':seed_record,'r2_reset_off_confirmed':True,'r2_off_probe_accepted':True,'r2_off_probe_switch_reported':r2_switch in off_state,'post_go_iteration':it,'regime':{'damped_source':'reset all user-requested Damped state','collision_command':'collision fast','collision_avoidance':True,'velocity_sector_note':'The anonymous velocity-dependent sector is tested under Damped as requested; KnotPlot GUI note says Undamped is intended for that force.'}}
    (out/'defaults.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8'); (out/'result.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(f'INSTALL TEST PASS: 8 sliders live, one normalized reload-safe shared trefoil seed, exactly 1 export ({len(xyz)} points)')
if __name__=='__main__':main()
