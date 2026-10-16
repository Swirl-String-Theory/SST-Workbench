"""A genuinely different upstream *geometry* and separate C++ RK4 dynamics lane.

Strict qualification boundary: independent numerical provider != independent physical
Euler evolution. Source Fremlin must match the registered E010 byte hash and a
frozen per-run provider manifest, never inferred from carrier labels alone.
"""
from __future__ import annotations
import hashlib,json,math,os,shutil,subprocess,tempfile
from pathlib import Path
from .pklsa import load_geometry
from .provider_manifest import verify as verify_manifest
from .dynamics import rms_difference
from .security import readjson

def run_native(executable,points,steps,eps,T,gamma):
    src=f'{len(points)} {eps:.17g} {gamma:.17g} {T:.17g} {steps}\n'+''.join(' '.join(f'{x:.17g}' for x in p)+'\n' for p in points)
    cp=subprocess.run([str(executable)],input=src,text=True,capture_output=True,timeout=120)
    if cp.returncode:raise RuntimeError(f'PROVIDER_NATIVE_RETURN_{cp.returncode}: {cp.stderr[:300]}')
    rows=[tuple(map(float,r.split())) for r in cp.stdout.splitlines() if r.strip()]
    if len(rows)!=len(points) or any(len(r)!=3 or not all(math.isfinite(c) for c in r) for r in rows):
        raise RuntimeError('PROVIDER_NATIVE_BAD_SHAPE_OR_NONFINITE')
    return rows

def verify(root):
    root=Path(root)
    manifest=verify_manifest(root)
    conf=readjson(root/'preregistration'/'QUALIFICATION_V032.json')
    report={'schema':'A065-FREMLIN-DYNAMIC-LANE-V032-1','source_family':'fremlin_fourier',
      'carrier_id':manifest['carrier_id'],'geometry_evidence':manifest['status'],
      'provider_manifest_sha256':manifest['manifest_sha256'],
      'status':'UNRESOLVED','physical_euler_status':'NOT_CERTIFIED',
      'independence_scope':'Independent E010 geometry family + independent C++17 implementation of SAME reduced filament ODE',
      'not_independent_physical_model':True}
    if manifest['status']!='PASS_RAW_HASH_AND_XYZ_PARSER_ONLY':
        report['reason']='Authentic Fremlin raw source missing, altered or unparseable; no fabricated substitute'
        return report
    raw=Path(manifest['resolved_path'])
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=conf['provider_t0_raw_sha256']:
        report.update(status='FAIL_RAW_HASH_CHANGED');return report
    points=load_geometry(raw)
    if len(points)!=118:report.update(status='UNRESOLVED_UNEXPECTED_N',observed_points=len(points));return report
    compiler=os.environ.get('CXX','g++')
    if not shutil.which(compiler):
        report.update(status='UNRESOLVED_CXX_COMPILER_UNAVAILABLE',compiler=compiler);return report
    code=root/'native/fremlin_propagator.cpp'
    report['cpp_source_sha256']=hashlib.sha256(code.read_bytes()).hexdigest()
    spec=(conf['epsilon'],conf['T'],conf['gamma'])
    with tempfile.TemporaryDirectory(prefix='a065_fremlin_native_') as td:
        exe=Path(td)/('fremlin.exe' if os.name=='nt' else 'fremlin')
        cmd=[compiler,'-std=c++17','-O2',str(code),'-o',str(exe)]
        build=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        if build.returncode:
            report.update(status='FAIL_CPP_BUILD',error=build.stderr[-1000:]);return report
        try:
            # Independently generated time trajectories, not replays of KnotPlot's RK4 outputs.
            finals={n:run_native(exe,points,n,*spec) for n in conf['provider_steps']}
            reduced=points[::2]
            reduced_final=run_native(exe,reduced,8,*spec)
        except Exception as exc:
            report.update(status='FAIL_CPP_EXECUTION',reason=str(exc));return report
    disp=rms_difference(points,finals[16])
    temporal=rms_difference(finals[8],finals[16])/max(disp,1e-14)
    spatial=rms_difference(reduced_final,finals[16][::2])/max(rms_difference(reduced,reduced_final),1e-14)
    temporal4=rms_difference(finals[4],finals[8])/max(rms_difference(points,finals[8]),1e-14)
    # Source bytes are not bundled by default, and *real* native snapshots are hashed individually.
    snapshots={'t0':hashlib.sha256(json.dumps(points,sort_keys=True).encode()).hexdigest(),
               't_final_n118_step4':hashlib.sha256(json.dumps(finals[4]).encode()).hexdigest(),
               't_final_n118_step8':hashlib.sha256(json.dumps(finals[8]).encode()).hexdigest(),
               't_final_n118_step16':hashlib.sha256(json.dumps(finals[16]).encode()).hexdigest(),
               't_final_n59_step8':hashlib.sha256(json.dumps(reduced_final).encode()).hexdigest()}
    temporal_ok=temporal<=conf['temporal_threshold'] and temporal4<=conf['temporal_threshold']
    spatial_ok=spatial<=conf['threshold']
    report.update(status='SIMULATION_QUALIFIED' if temporal_ok and spatial_ok else 'SIMULATION_NUMERICAL_FAIL',
                  backend='C++17 actual executed binary, FP64',compiler=compiler,
                  node_count=118,source_raw_sha256=manifest['observed_raw_sha256'],
                  time_refinement={'4_vs_8':temporal4,'8_vs_16':temporal},
                  spatial_refinement={'59_vs_118':spatial},
                  temporal_gate='PASS' if temporal_ok else 'FAIL',
                  spatial_gate='PASS' if spatial_ok else 'FAIL',
                  trajectory_sha256=snapshots,
                  trajectory_sample_t0=[list(x) for x in points[:3]],
                  trajectory_sample_t_final=[list(x) for x in finals[16][:3]],
                  note='Physical Euler PDE, stability and material response still unqualified regardless of status')
    return report
