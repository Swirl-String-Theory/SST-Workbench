from __future__ import annotations
import argparse,json,os,shutil,sys
from pathlib import Path
import numpy as np

FRAMEWORK=Path(__file__).resolve().parents[1]
if str(FRAMEWORK) not in sys.path: sys.path.insert(0,str(FRAMEWORK))
from sst_falsifier.backend_contract import parity_gate,require_backend,relative_l2
from sst_falsifier.backends import python_ref,cpp_pybind
from sst_falsifier import sycl_worker


def _circle(n=192):
    t=np.linspace(0,2*np.pi,n,endpoint=False);p=np.column_stack((np.cos(t),np.sin(t),np.zeros_like(t)))
    u=np.linspace(-.85,.85,48);q=np.column_stack((.31*np.cos(2.7*u),.27*np.sin(1.9*u),u));return p,q

def _trefoil(n=240):
    t=np.linspace(0,2*np.pi,n,endpoint=False);R,r=1.0,.32
    p=np.column_stack(((R+r*np.cos(3*t))*np.cos(2*t),(R+r*np.cos(3*t))*np.sin(2*t),r*np.sin(3*t)))
    u=np.linspace(0,2*np.pi,64,endpoint=False);q=np.column_stack((.22*np.cos(u),.17*np.sin(2*u),.45*np.sin(u)));return p,q

def _near_core_ring(n=160):
    t=np.linspace(0,2*np.pi,n,endpoint=False);p=np.column_stack((np.cos(t),np.sin(t),.08*np.sin(3*t)))
    u=np.linspace(0,2*np.pi,40,endpoint=False);q=np.column_stack((.91*np.cos(u),.91*np.sin(u),.03*np.cos(2*u)));return p,q

def _prepare_runtime():
    dst=FRAMEWORK/"build"/"backend_selftest_instance"
    if dst.exists():shutil.rmtree(dst)
    (dst/"native"/"cpp").mkdir(parents=True,exist_ok=True);(dst/"native_ext").mkdir(parents=True,exist_ok=True)
    for name in ("native.cpp","sycl_worker.cpp"):shutil.copy2(FRAMEWORK/"instance_template"/"native"/"cpp"/name,dst/"native"/"cpp"/name)
    (dst/"native_ext"/"__init__.py").write_text("",encoding="utf-8");return dst

def _finite_stats(a):
    a=np.asarray(a,dtype=np.float64);return {"shape":list(a.shape),"finite":bool(np.isfinite(a).all()),"l2_norm":float(np.linalg.norm(a)),"max_abs":float(np.max(np.abs(a))) if a.size else 0.0,"sum":float(np.sum(a))}

def _improvement(fp32_err,dd32_err):return float(fp32_err/max(dd32_err,1e-30))

def _directional_stress(runtime,h=3e-4):
    p,q=_circle(96);q=q[:12]
    d=np.column_stack((np.linspace(.2,.7,len(q)),np.linspace(-.3,.4,len(q)),np.linspace(.5,-.1,len(q))));d=d/np.linalg.norm(d,axis=1,keepdims=True)
    gamma,core=.73,.035
    rp=python_ref.biot_savart(p,q+h*d,gamma=gamma,core=core);rm=python_ref.biot_savart(p,q-h*d,gamma=gamma,core=core);ref=(rp-rm)/(2*h)
    fp_p,_=sycl_worker.biot_savart(runtime,p,q+h*d,gamma=gamma,core=core,precision="fp32");fp_m,_=sycl_worker.biot_savart(runtime,p,q-h*d,gamma=gamma,core=core,precision="fp32");fp=(fp_p-fp_m)/(2*h)
    dd_p,_=sycl_worker.biot_savart(runtime,p,q+h*d,gamma=gamma,core=core,precision="dd32");dd_m,_=sycl_worker.biot_savart(runtime,p,q-h*d,gamma=gamma,core=core,precision="dd32");dd=(dd_p-dd_m)/(2*h)
    ef=relative_l2(fp,ref);ed=relative_l2(dd,ref)
    return {"kind":"query_directional_finite_difference","h":h,"python_stats":_finite_stats(ref),"fp32_relative_l2":ef,"dd32_relative_l2":ed,"dd32_improvement_vs_fp32":_improvement(ef,ed)}


def main():
    ap=argparse.ArgumentParser(description="Cross-backend numerical parity selftest for SST Falsifier Framework.")
    ap.add_argument("--cpp-tol",type=float,default=1e-10);ap.add_argument("--sycl-fp32-tol",type=float,default=5e-4);ap.add_argument("--dd32-tol",type=float,default=1e-8);ap.add_argument("--dd32-jac-tol",type=float,default=2e-6);ap.add_argument("--dd32-min-improvement",type=float,default=20.0)
    ap.add_argument("--allow-sycl-fp32",action="store_true");ap.add_argument("--force-build",action="store_true");ap.add_argument("--skip-cpp",action="store_true");ap.add_argument("--skip-sycl",action="store_true");ap.add_argument("--skip-dd32",action="store_true")
    ap.add_argument("--json",default=str(FRAMEWORK/"build"/"BACKEND_SELFTEST.json"));args=ap.parse_args()
    if args.allow_sycl_fp32:os.environ["SST_SYCL_ALLOW_FP32"]="1"
    runtime=_prepare_runtime();scenarios=[("circle",*_circle(),1.23456789,.041),("trefoil",*_trefoil(),-.731,.057),("near_core_ring",*_near_core_ring(),.9375,.026)]
    report={"schema":"SST-BACKEND-PARITY-SELFTEST-2","framework_version":"1.0.3","precision_policy":{"dd32":"FP32x2/double-single; not IEEE FP64; nominal ~48 significand bits; binary32 exponent range","confirmatory":"Python/C++ FP64"},"tolerances":{"cpp_vs_python_relative_l2":args.cpp_tol,"sycl_fp32_vs_python_relative_l2":args.sycl_fp32_tol,"sycl_dd32_vs_python_relative_l2":args.dd32_tol,"sycl_dd32_directional_relative_l2":args.dd32_jac_tol,"sycl_dd32_min_improvement_vs_fp32":args.dd32_min_improvement},"backends":{},"scenarios":[]}
    all_pass=True
    cpp_ready=not args.skip_cpp
    if cpp_ready:
        try:
            _,b=cpp_pybind.load(runtime,force_build=args.force_build,require=True,verbose=True);report["backends"]["cpp"]={"available":True,"build":b.to_dict()}
        except Exception as e:cpp_ready=False;report["backends"]["cpp"]={"available":False,"error":f"{type(e).__name__}: {e}"};all_pass=False
    else:report["backends"]["cpp"]={"available":False,"skipped":True}
    sycl_ready=not args.skip_sycl
    if sycl_ready:
        info=sycl_worker.worker_info(runtime,start=False);sycl_ready=bool(info.get("available"));report["backends"]["sycl"]=info
        if not sycl_ready:all_pass=False
    else:report["backends"]["sycl"]={"available":False,"skipped":True}

    for name,points,queries,gamma,core in scenarios:
        ref=python_ref.biot_savart(points,queries,gamma=gamma,core=core);row={"name":name,"n_filament_points":int(len(points)),"n_queries":int(len(queries)),"gamma":float(gamma),"core":float(core),"python":{"backend":"python-numpy-fp64","precision":"float64","stats":_finite_stats(ref)}}
        if cpp_ready:
            try:
                val,res=cpp_pybind.biot_savart(runtime,points,queries,gamma=gamma,core=core,require=True);require_backend(res,accepted_actual=["openmp","serial"],authority="CERTIFICATION",precision="float64");p=parity_gate(val,ref,args.cpp_tol);row["cpp"]={"backend_result":res.to_dict(),"stats":_finite_stats(val),"parity_vs_python":p};all_pass &= bool(p["pass"])
            except Exception as e:row["cpp"]={"error":f"{type(e).__name__}: {e}","pass":False};all_pass=False
        else:row["cpp"]={"skipped":args.skip_cpp,"available":False}
        if sycl_ready:
            try:
                fp,res=sycl_worker.biot_savart(runtime,points,queries,gamma=gamma,core=core,precision="fp32");require_backend(res,accepted_actual=["sycl-worker-fp32"],authority="SCREENING_ONLY",precision="float32");pf=parity_gate(fp,ref,args.sycl_fp32_tol);row["sycl_fp32"]={"backend_result":res.to_dict(),"stats":_finite_stats(fp),"parity_vs_python":pf};all_pass &= bool(pf["pass"])
                if not args.skip_dd32:
                    dd,dres=sycl_worker.biot_savart(runtime,points,queries,gamma=gamma,core=core,precision="dd32");require_backend(dres,accepted_actual=["sycl-worker-dd32"],authority="SCREENING_ONLY",precision="dd32-fp32x2");pd=parity_gate(dd,ref,args.dd32_tol);imp=_improvement(pf["relative_l2"],pd["relative_l2"]);ok=bool(pd["pass"] and imp>=args.dd32_min_improvement);row["sycl_dd32"]={"backend_result":dres.to_dict(),"stats":_finite_stats(dd),"parity_vs_python":pd,"improvement_vs_fp32":imp,"pass":ok};all_pass &= ok
            except Exception as e:row["sycl_error"]={"error":f"{type(e).__name__}: {e}","pass":False};all_pass=False
        else:row["sycl"]={"skipped":args.skip_sycl,"available":False}
        report["scenarios"].append(row)

    if sycl_ready and not args.skip_dd32:
        try:
            stress=_directional_stress(runtime);stress["tolerance"]=args.dd32_jac_tol;stress["min_improvement"]=args.dd32_min_improvement;stress["pass"]=bool(stress["dd32_relative_l2"]<=args.dd32_jac_tol and stress["dd32_improvement_vs_fp32"]>=args.dd32_min_improvement);report["dd32_directional_stress"]=stress;all_pass &= stress["pass"]
        except Exception as e:report["dd32_directional_stress"]={"pass":False,"error":f"{type(e).__name__}: {e}"};all_pass=False
    sycl_worker.shutdown_worker(runtime);report["overall_pass"]=bool(all_pass)
    out=Path(args.json);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("SST backend parity selftest v2");print("==============================");print(f"C++ backend available : {report['backends']['cpp'].get('available',False)}");print(f"SYCL backend available: {report['backends']['sycl'].get('available',False)}")
    for row in report["scenarios"]:
        print(f"\n[{row['name']}]\n  Python norm: {row['python']['stats']['l2_norm']:.16e}")
        p=row.get("cpp",{}).get("parity_vs_python");print(f"  C++ FP64 : rel-L2 {p['relative_l2']:.6e} <= {p['tolerance']:.6e} : {'PASS' if p['pass'] else 'FAIL'}" if p else "  C++ FP64 : UNAVAILABLE/FAIL")
        p=row.get("sycl_fp32",{}).get("parity_vs_python");print(f"  SYCL FP32: rel-L2 {p['relative_l2']:.6e} <= {p['tolerance']:.6e} : {'PASS' if p['pass'] else 'FAIL'}" if p else "  SYCL FP32: UNAVAILABLE/FAIL")
        d=row.get("sycl_dd32",{});p=d.get("parity_vs_python");print(f"  SYCL DD32: rel-L2 {p['relative_l2']:.6e} <= {p['tolerance']:.6e}; improvement {d['improvement_vs_fp32']:.3e}x : {'PASS' if d['pass'] else 'FAIL'}" if p else ("  SYCL DD32: SKIP" if args.skip_dd32 else "  SYCL DD32: UNAVAILABLE/FAIL"))
    if "dd32_directional_stress" in report:
        d=report["dd32_directional_stress"];print("\n[DD32 directional finite-difference stress]");print(f"  DD32 rel-L2: {d.get('dd32_relative_l2',float('nan')):.6e} <= {args.dd32_jac_tol:.6e}");print(f"  improvement: {d.get('dd32_improvement_vs_fp32',0):.3e}x >= {args.dd32_min_improvement:.1f}x : {'PASS' if d.get('pass') else 'FAIL'}")
    print(f"\nReport: {out}\nOVERALL: {'PASS' if all_pass else 'FAIL'}");return 0 if all_pass else 1

if __name__=="__main__":raise SystemExit(main())
