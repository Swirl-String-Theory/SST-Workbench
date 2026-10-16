"""A062 standalone scientific diagnostics. Does not claim to execute the frozen framework."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, platform, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path
import numpy as np
from . import models as m

ROOT=Path(__file__).resolve().parent.parent
NAME="A062_SST_Microgravity_Force_Gradient_v0.1.0"
OUT=ROOT/(NAME+"-outputs")
LOCK=ROOT/"preregistration"/"STANDALONE_PROTOCOL_SHA256.json"
SOURCE_FILES=["inputs/article_public_summary.json","science_contract.json","source_contract.json",
              "gate_plan.json","falsifier.toml","blind_policy.json","microgravity/models.py",
              "microgravity/runner.py","native/gradient.cpp","report/FALSIFIER_REPORT.tex",
              "experiment/pipeline.py","tests/test_science.py",".sst_framework_root",
              "framework_bootstrap.py","run_instance.py","inputs/s41565-026-02298-8.pdf"]


def digest(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p:Path,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
def protocol_manifest():return {f:digest(ROOT/f) for f in SOURCE_FILES}


def freeze():
    sha=protocol_manifest()
    if LOCK.exists():
        old=json.loads(LOCK.read_text())
        if old["files"]!=sha:
            raise RuntimeError("Protocol already frozen, changed files detected. Bump version; do NOT refreeze in place")
        print("STANDALONE FREEZE unchanged:",old["bundle_sha256"])
        return
    proof=hashlib.sha256(json.dumps(sha,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    write_json(LOCK,{"schema":"A062-STANDALONE-COMMIT-1","framework_certification":False,
                     "files":sha,"bundle_sha256":proof,
                     "warning":"Does not replace CANONICAL_FROZEN v1.0.7 FREEZE. Public article benchmark is not a private holdout."})
    print("STANDALONE FREEZE:",proof)


def verify_freeze():
    if not LOCK.exists():raise RuntimeError("Run FREEZE first; no protocol lock found")
    d=json.loads(LOCK.read_text()); h=protocol_manifest()
    if h!=d["files"]:raise RuntimeError("Protocol hash mismatch. Fails closed")
    return d["bundle_sha256"]


def native_compile() -> tuple[Path|None,str]:
    cc=next((c for c in ('g++','clang++') if shutil.which(c)),None)
    OUT.mkdir(exist_ok=True)
    exe=OUT/('gradient_native.exe' if os.name=='nt' else 'gradient_native')
    if cc:
        cmd=[cc,'-O3','-std=c++17',str(ROOT/'native'/'gradient.cpp'),'-o',str(exe)]
    elif shutil.which('cl'):
        cmd=['cl','/nologo','/O2','/std:c++17',str(ROOT/'native'/'gradient.cpp'),'/Fe:'+str(exe)]
    else:return None,"No C++ compiler found; no silent Python certification"
    proc=subprocess.run(cmd,capture_output=True,text=True,cwd=OUT)
    if proc.returncode or not exe.exists():
        return None, 'Native compilation failed: '+proc.stdout[-500:]+proc.stderr[-500:]
    return exe,cc or 'cl'


def local_selftest():
    cmd=[sys.executable,'-m','unittest','discover','-s','tests','-v']
    p=subprocess.run(cmd,cwd=ROOT)
    return p.returncode


def run(mode):
    bundle=verify_freeze()
    inp=json.loads((ROOT/'inputs'/'article_public_summary.json').read_text())
    OUT.mkdir(exist_ok=True)
    ms=inp['source_mass_kg'];mt=inp['test_mass_kg'];r=inp['distance_m'];d=inp['source_drive_displacement_m']
    # Compare both first-order and exact one-sided amplitude. Paper rounds 1.4 um and F.
    fn=m.newton_force(ms,mt,r)
    gn=m.newton_gradient(ms,mt,r)
    delta=gn*d
    delta_exact=m.newton_modulation_exact(ms,mt,r,d)
    static=m.newton_force(inp['reported_static_source_mass_kg'],mt,inp['reported_static_distance_m'])
    a=0.003  # Explicit mm-scale surrogate. NOT r_c.
    data={"schema":"A062-SCIENCE-RESULTS-1","mode":mode,"framework_certification":False,
          "profile":"standalone_python_fp64","protocol_sha256":bundle,"reference_G_m3_kg_1_s_2":m.G_REF,
          "article_measurement_evidence":"published rounded summary, not raw data",
          "newton":{"static_force_N":fn,"modulation_gradient_N_per_m":gn,"linear_delta_force_N":delta,
                    "one_sided_exact_delta_force_N":delta_exact,"figure4_static_force_1p5kg_N":static,
                    "paper_reported_delta_force_N":inp['reported_delta_force_N'],
                    "paper_reported_static_force_N":inp['reported_static_force_N'],
                    "relative_delta_discrepancy":abs(delta/inp['reported_delta_force_N']-1),
                    "central_gradient_finite_diff_N_per_m":m.finite_difference_newton(ms,mt,r)},
          "sst_candidate":{"family":"instantaneous_axisymmetric_Gaussian_divergence_free_Euler_pressure_source",
                          "not_a_PKLSA_knot":True,"coarse_grained_a_m":a,"canonical_core_r_c_m":m.R_CORE,
                          "canonical_rho_f_kg_m3":m.RHO_F,"canonical_vswirl_m_s":m.V_SWIRL,
                          "omega_s_inverse":m.vortex_omega(a),"kinetic_mass_equivalent_kg":m.energy_mass(a),
                          "observed_source_mass_kg":ms,"mass_ratio":m.energy_mass(a)/ms,
                          "predicted_mass_deficit_log10":np.log10(ms/m.energy_mass(a))},
          "dimensions":m.dims_consistency(),"computational_notes":[]}
    gates=[]
    def gate(name,status,value,criterion,explanation):
        gates.append({"id":name,"status":status,"value":value,"criterion":criterion,"explanation":explanation})
    gate('S0','PASS',bundle,'verifies all frozen files before evaluating physics','Local sha256 only; v1.0.7 certification not executed.')
    gate('S1','PASS' if data['newton']['relative_delta_discrepancy']<0.02 else 'FAIL',
        data['newton']['relative_delta_discrepancy'],'<0.02 relative discrepancy to rounded published Newton-calibrated force change',
        'Consistency/reproduction only, cannot measure G independently.')
    if mode in ('FULL','CERTIFY'):
        ns=[40,56,80]
    else:ns=[40,56]
    rs=np.asarray([0.03,0.038,0.042,0.054,0.065,0.08],dtype=np.float64)
    axes={}
    for axis in ('x','z'):
        per_n={}
        for n in ns:
            forces=np.asarray([m.pressure_force_component(float(R),axis,a=a,n=n) for R in rs],dtype=float)
            per_n[str(n)]=[float(x) for x in forces]
        last=np.array(per_n[str(ns[-1])]); previous=np.array(per_n[str(ns[-2])]);
        rel=np.max(np.abs(last-previous)/np.maximum(np.abs(last),1e-40))
        axes[axis]={"force_N_by_resolution":per_n,"farfield_slope":m.force_radial_exponent(rs,last),
                    "max_rel_refinement_change":float(rel),"distance_m":rs.tolist(),
                    "force_at_0p042_m_N":float(last[2]),
                    "force_ratio_to_newton_at_0p042_m":float(last[2]/fn)}
    data['sst_candidate']['pressure_force']=axes
    # Exact discrete cancellation is a diagnostic: infinitesimal core source is quadrupole-like.
    gr=m.quadrature_grid(a,ns[-1]); monopole=m.source_integral_monopole_discrete(gr)
    data['sst_candidate']['relative_pressure_source_monopole_integral']=float(abs(monopole)/ (float(np.sum(np.abs(gr[0]))*gr[4]**3)))
    refine=max(axes[q]['max_rel_refinement_change'] for q in axes)
    gate('S2','PASS' if refine<.005 and data['dimensions']['source_matches'] and data['dimensions']['force_matches'] else 'FAIL',
         float(refine),'<0.005 largest relative midpoint refinement change; pressure/force dimensional consistency',
         'Numerical qualification only. Not independent physical calibration.')
    mass_ratio=data['sst_candidate']['mass_ratio']
    gate('S3','PASS' if abs(mass_ratio-1)<.1 else 'FAIL',float(mass_ratio),'|m_E/m_source-1|<0.1, no fitted parameter',
         'Falsifies proposed E_kin/c^2 mass closure at a=3 mm with canonical rho_f and vmax; not generic SST.')
    worst_exp=max(abs(axes[k]['farfield_slope']-2) for k in axes)
    gate('S4','PASS' if worst_exp<=.2 else 'FAIL',float(worst_exp),'|fitted slope - 2| <= 0.2 for BOTH swirl-axis orientations',
         'The model must recover inverse-square force in far field; Newton comparator has exponent 2.')
    exe,toolchain=native_compile()
    native={'requested':mode=='CERTIFY','compiler':toolchain,'ran':exe is not None,'authority':'C++ FP64 solver-specific parity only; not v1.0.7 backend certification'}
    if exe:
        err=[]
        for ax in ('x','z'):
            for R in [0.038,0.042,0.08]:
                v=float(subprocess.check_output([str(exe),str(R),str(a),str(ns[-1]),ax],text=True).strip())
                ref=m.pressure_force_component(R,ax,a=a,n=ns[-1])
                err.append(abs(v-ref)/max(abs(ref),1e-40))
        native['max_relative_error']=max(err)
        gate('S5','PASS' if native['max_relative_error']<2e-8 else 'FAIL',native['max_relative_error'],
             'C++ FP64 native model parity relative error <2e-8','Separate numerical implementation, not proof of correct physical closure.')
    else:
        gate('S5','UNRESOLVED',None,'native C++ FP64 compiler and parity must execute',toolchain)
    data['native']=native
    gate('S6','UNRESOLVED',None,'independent calibrated distance sweep at >=4 separations with uncertainty covariance',
         'Article has a public single-distance primary setup and no supplied raw multi-distance experimental traces.')
    gate('S7','UNRESOLVED',None,'unique (or bounded) posterior for at least one SST constant independent of input canon',
         'Canon rho_f and vmax were input, so not identified; no free-mass mapping established.')
    gate('S8','UNRESOLVED',None,'>=2 independent measurement providers / source families',
         'Single article and analytic computation are not independent experimental replication.')
    gate('S9','UNRESOLVED',None,'v1.0.7 authorized reveal and check of privately held-out raw data',
         'No non-public holdout is bundled. Public benchmark is not a scientific blind reveal.')
    data['gate_status']={q['id']:q['status'] for q in gates}
    data['overall_science']='UNRESOLVED_FULL_SST; restricted Gaussian mass and scaling closures fail'
    data['computational_notes']=["Independent gates executed without short-circuit after FAIL.",
       "G3 and G4 are failures of a specified surrogate model, not established falsifications of SST.",
       "No measurement of G or F_gr_max is extracted from a Newton-calibrated figure caption.",
       "The Gaussian initial velocity is divergence-free but not a validated stationary Euler knot."]
    write_json(OUT/'SCIENCE_RESULTS.json',data)
    write_json(OUT/'GATE_LEDGER.json',{"schema":"A062-STANDALONE-GATES-1","not_framework_gate_ledger":True,
                                      "protocol_sha256":bundle,"continue_after_fail":True,"gates":gates})
    report(data,gates)
    write_json(OUT/'RUN_SUMMARY.json',{"status":"RESTRICTED_GAUSSIAN_CLOSURE_FAIL","mode":mode,"framework_certification":False,
                    "some_gates_unresolved":True,"note":"Standalone science only, not the v1.0.7 RUN_SUMMARY."})
    output_manifest={str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and p.name!='OUTPUT_MANIFEST.json'}
    write_json(OUT/'OUTPUT_MANIFEST.json',{"schema":"A062-LOCAL-OUTPUT-MANIFEST-1","files":output_manifest,"not_framework_manifest":True})
    archive=ROOT.parent/(NAME+'-outputs_BLIND.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for f in sorted(OUT.rglob('*')):
            if f.is_file():z.write(f,arcname=f.relative_to(ROOT))
    print('A062 science-only gate summary:')
    for q in gates:print('  ',q['id'],q['status'],q['value'])
    print('Output directory:',OUT)
    return data


def tex_escape(s):
    return s.replace('\\','\\textbackslash{}').replace('_','\\_').replace('%','\\%').replace('&','\\&')


def report(data,gates):
    # Provide a standalone LaTeX report and compile in a temporary directory to avoid stale auxiliaries.
    q=data['newton']; v=data['sst_candidate']; a=v['pressure_force'];
    def e(x):return f'{float(x):.7g}'
    lines=[r'\begin{tabular}{lll}',r'\hline',r'Gate & Status & Primary metric \\',r'\hline']
    for g in gates:
        val='---' if g['value'] is None else (e(g['value']) if isinstance(g['value'],(int,float)) else str(g['value'])[:16])
        lines.append("{} & {} & {} ".format(g["id"],g["status"],val) + r"\\")
    lines.extend([r'\hline',r'\end{tabular}'])
    vals={"FORCE":e(q['static_force_N']),"GRAD":e(q['modulation_gradient_N_per_m']),
      "DELTA":e(q['linear_delta_force_N']),"MASS":e(v['kinetic_mass_equivalent_kg']),
      "MRATIO":e(v['mass_ratio']),"SLOPEX":e(a['x']['farfield_slope']),"SLOPEZ":e(a['z']['farfield_slope']),
      "FX":e(a['x']['force_at_0p042_m_N']),"FZ":e(a['z']['force_at_0p042_m_N']),
      "REFINEX":e(a['x']['max_rel_refinement_change']),"REFINEZ":e(a['z']['max_rel_refinement_change']),
      "GATES":'\n'.join(lines),"HASH":data['protocol_sha256'][:16]}
    tpl=(ROOT/'report'/'FALSIFIER_REPORT.tex').read_text(encoding='utf8')
    metrics='\n'.join('\\renewcommand{\\A'+k+'}{'+str(v)+'}' for k,v in vals.items())+'\n'
    (OUT/'LOCAL_METRICS.tex').write_text(metrics,encoding='utf8')
    (OUT/'FALSIFIER_REPORT.tex').write_text(tpl,encoding='utf8')
    render={'latex_attempted':False,'pdf_generated':False,'error':None}
    pdf=ROOT.parent/(NAME+'_FALSIFIER_REPORT.pdf')
    command=shutil.which('pdflatex') or shutil.which('xelatex')
    if command:
        render['latex_attempted']=True
        try:
            with tempfile.TemporaryDirectory(prefix='a062_latex_') as temp:
                tem=Path(temp);shutil.copy2(OUT/'FALSIFIER_REPORT.tex',tem/'FALSIFIER_REPORT.tex');shutil.copy2(OUT/'LOCAL_METRICS.tex',tem/'LOCAL_METRICS.tex')
                for _ in range(2):
                    res=subprocess.run([command,'-interaction=nonstopmode','-halt-on-error','FALSIFIER_REPORT.tex'],cwd=tem,capture_output=True,text=True,timeout=70)
                    if res.returncode:raise RuntimeError(res.stdout[-1500:])
                shutil.copy2(tem/'FALSIFIER_REPORT.pdf',OUT/'FALSIFIER_REPORT.pdf')
                shutil.copy2(tem/'FALSIFIER_REPORT.pdf',pdf)
                render['pdf_generated']=True
        except Exception as exc:render['error']=str(exc)[-2000:]
    else:render['error']='LaTeX compiler unavailable; run locally with pdflatex to generate PDF.'
    write_json(OUT/'REPORT_RENDER.json',render)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',nargs='?',default='BASIC',choices=['FREEZE','BASIC','FULL','CERTIFY','SELFTEST'])
    args=p.parse_args(argv)
    if args.mode=='FREEZE':freeze();return 0
    if args.mode=='SELFTEST':return local_selftest()
    res=run(args.mode)
    if args.mode=='CERTIFY' and res['gate_status']['S5']!='PASS':return 4
    return 0
if __name__=='__main__':raise SystemExit(main())
