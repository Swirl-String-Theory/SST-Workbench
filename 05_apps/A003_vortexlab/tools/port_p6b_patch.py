#!/usr/bin/env python3
"""Port P6b discrete-continuum patch onto a MODIFIED A003 tree (installer baselines will not match)."""
from __future__ import annotations
import re, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / ".patch_staging_P6b"
PAYLOAD = STAGING / "payload"


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"MISSING hook {label}: {old[:120]!r}")
    c = text.count(old)
    if c != 1:
        raise SystemExit(f"AMBIGUOUS hook {label}: count={c}")
    return text.replace(old, new, 1)


def main() -> None:
    if not STAGING.is_dir():
        raise SystemExit("missing .patch_staging_P6b")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / ".A003_P6b_backups" / f"port_{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    files = [
        "apps/web/src/legacy/vortexlab-runtime.js",
        "apps/web/twist-flow/twist-flow.js",
        "apps/web/twist-flow/twist-flow.css",
        "apps/web/twist-flow/index.html",
    ]
    for rel in files:
        src = ROOT / rel
        dest = backup / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    print("backup", backup)

    payload_rt = (PAYLOAD / "apps/web/src/legacy/vortexlab-runtime.js").read_text(encoding="utf-8")
    m = re.search(r"// A003 Twist Flow P6b:.*?^}\)\(\);\n", payload_rt, re.M | re.S)
    if not m:
        raise SystemExit("kernel block not found in payload runtime")
    kernel = m.group(0)

    rt_path = ROOT / "apps/web/src/legacy/vortexlab-runtime.js"
    rt = rt_path.read_text(encoding="utf-8")
    if "vlDiscrete" in rt:
        raise SystemExit("vlDiscrete already present; abort")

    anchor = "let Y=null, fils=[], ghostFil=null, tPhys=0, phi=0, bundlePhi=0, paused=false;\n"
    if anchor not in rt:
        raise SystemExit("Y declaration anchor missing")
    rt = rt.replace(anchor, anchor + "\n" + kernel + "\n", 1)

    rt = must_replace(
        rt,
        "function velAll(Yv,OUT){\n  const lia=(P.inter==='lia');\n  return velocityCore(Yv,allFils(),OUT,lia);\n}",
        "function velAll(Yv,OUT){\n  const lia=(P.inter==='lia');\n  const u=velocityCore(Yv,allFils(),OUT,lia);\n  return vlDiscrete.active()?Math.max(u,vlDiscrete.knotDerivative(Yv,allFils(),OUT)):u;\n}",
        "velAll",
    )
    rt = must_replace(
        rt,
        "function rk4Step(dt){\n  if(nativeSolverAdmissible()){",
        "function rk4Step(dt){\n  if(vlDiscrete.active())return vlDiscrete.advance(dt);\n  if(nativeSolverAdmissible()){",
        "rk4Step",
    )
    rt = must_replace(
        rt,
        "function dtCFL(){\n  const lm=lminAll();",
        "function dtCFL(){\n  const lm=vlDiscrete.active()?Math.min(lminAll(),vlDiscrete.minSegment()):lminAll();",
        "dtCFL-lm",
    )
    rt = must_replace(
        rt,
        "  const speedBound=Math.max(1e-12,lastUmax,prescribedKinematicSpeedBound());\n  dt=Math.min(dt,0.25*lm/speedBound);\n  const stretchRate=stretchProfileCharacteristicRate();",
        "  const speedBound=Math.max(1e-12,lastUmax,prescribedKinematicSpeedBound());\n  dt=Math.min(dt,0.25*lm/speedBound);\n  if(vlDiscrete.active()){const b=vlDiscrete.report();dt=Math.min(dt,0.1*b.spacing/speedBound,0.1/Math.max(1e-12,Math.abs(b.omega)));}\n  const stretchRate=stretchProfileCharacteristicRate();",
        "dtCFL-discrete",
    )
    rt = must_replace(
        rt,
        "function evalsPerStep(){\n  let tot=0;for(const f of dynamicFils())tot+=f.N;",
        "function evalsPerStep(){\n  if(vlDiscrete.active()){const b=vlDiscrete.report().vertices;return 4*(b+dynamicFils().reduce((n,f)=>n+f.N,0))**2;}\n  let tot=0;for(const f of dynamicFils())tot+=f.N;",
        "evalsPerStep",
    )
    rt = must_replace(
        rt,
        '  K3=new Float64Array(Y.length);K4=new Float64Array(Y.length);TT=new Float64Array(Y.length);\n  tPhys=0;phi=0;bundlePhi=0;flagged="";warned=false;lastUmax=1e-9;',
        '  K3=new Float64Array(Y.length);K4=new Float64Array(Y.length);TT=new Float64Array(Y.length);\n  vlDiscrete.setup();\n  tPhys=0;phi=0;bundlePhi=0;flagged="";warned=false;lastUmax=1e-9;',
        "resetState-setup",
    )
    rt = must_replace(
        rt,
        "  if(bundleFlowActive()){\n    const ub=bundleExteriorVelocityAt(x,y,z);ux+=ub.ux;uy+=ub.uy;uz+=ub.uz;\n  }\n  return {ux,uy,uz};\n}\nfunction backgroundVelocityForFilamentPoint",
        "  if(bundleFlowActive()){\n    const ub=bundleExteriorVelocityAt(x,y,z);ux+=ub.ux;uy+=ub.uy;uz+=ub.uz;\n  }\n  if(vlDiscrete.active()){const db=vlDiscrete.fieldVelocity(x,y,z);ux+=db.ux;uy+=db.uy;uz+=db.uz;}\n  return {ux,uy,uz};\n}\nfunction backgroundVelocityForFilamentPoint",
        "backgroundVelocityAt",
    )
    rt = must_replace(
        rt,
        "function topologyClearance(){\n  const active=fils.filter(f=>!f.ghost);let g=Infinity;\n  for(const f of active)g=Math.min(g,dminSelf(f));\n  for(let i=0;i<active.length;i++)for(let j=i+1;j<active.length;j++)\n    g=Math.min(g,Math.sqrt(pairGapExact2(active[i],active[j],g*g)));\n  return g;\n}",
        "function topologyClearance(){\n  const active=fils.filter(f=>!f.ghost);let g=Infinity;\n  for(const f of active)g=Math.min(g,dminSelf(f));\n  for(let i=0;i<active.length;i++)for(let j=i+1;j<active.length;j++)\n    g=Math.min(g,Math.sqrt(pairGapExact2(active[i],active[j],g*g)));\n  return vlDiscrete.active()?Math.min(g,vlDiscrete.minDistance(Y)):g;\n}",
        "topologyClearance",
    )
    rt = must_replace(
        rt,
        "function transientContactWithinStep(signedDtFull,lia){\n  if(!P.topologyGuard||!Ypre)return null;\n  const fullState=Y.slice(),fullK4=K4.slice(),fullUmax=lastUmax;\n  const sgn=Math.sign(signedDtFull)||1,full=Math.abs(signedDtFull),tStart=tPhys;\n  let lo=0,hi=NaN,event=null;\n  for(let k=1;k<=TOPOLOGY_SWEEP_SAMPLES;k++){\n    const f=k/TOPOLOGY_SWEEP_SAMPLES;Y.set(Ypre);advanceFilamentCandidate(sgn*full*f,tStart+sgn*full*f);\n    const e=contactEvent(false);if(e&&!e.warn){hi=f;lo=(k-1)/TOPOLOGY_SWEEP_SAMPLES;event=e;break;}\n  }\n  if(!event){Y.set(fullState);K4.set(fullK4);lastUmax=fullUmax;return null;}\n  for(let it=0;it<18&&(hi-lo)>1e-6;it++){\n    const mid=.5*(lo+hi);Y.set(Ypre);advanceFilamentCandidate(sgn*full*mid,tStart+sgn*full*mid);\n    const e=contactEvent(false);if(e&&!e.warn){hi=mid;event=e;}else lo=mid;\n  }\n  Y.set(Ypre);lastUmax=advanceFilamentCandidate(sgn*full*lo,tStart+sgn*full*lo);\n  return {dt:sgn*full*lo,event:Object.assign({},event,{msg:'⛔ topology guard: tijdelijk contact binnen de RK4-stap gevonden; gestopt aan de veilige zijde. Geen doorsnijding of reconnectie toegepast.'})};\n}",
        "function transientContactWithinStep(signedDtFull,lia){\n  if(!P.topologyGuard||!Ypre)return null;\n  const fullState=Y.slice(),fullBg=vlDiscrete.fullSnapshot(),fullK4=K4.slice(),fullUmax=lastUmax;\n  const sgn=Math.sign(signedDtFull)||1,full=Math.abs(signedDtFull),tStart=tPhys;\n  let lo=0,hi=NaN,event=null;\n  for(let k=1;k<=TOPOLOGY_SWEEP_SAMPLES;k++){\n    const f=k/TOPOLOGY_SWEEP_SAMPLES;Y.set(Ypre);vlDiscrete.restore();advanceFilamentCandidate(sgn*full*f,tStart+sgn*full*f);\n    const e=contactEvent(false);if(e&&!e.warn){hi=f;lo=(k-1)/TOPOLOGY_SWEEP_SAMPLES;event=e;break;}\n  }\n  if(!event){Y.set(fullState);vlDiscrete.restoreFull(fullBg);K4.set(fullK4);lastUmax=fullUmax;return null;}\n  for(let it=0;it<18&&(hi-lo)>1e-6;it++){\n    const mid=.5*(lo+hi);Y.set(Ypre);vlDiscrete.restore();advanceFilamentCandidate(sgn*full*mid,tStart+sgn*full*mid);\n    const e=contactEvent(false);if(e&&!e.warn){hi=mid;event=e;}else lo=mid;\n  }\n  Y.set(Ypre);vlDiscrete.restore();lastUmax=advanceFilamentCandidate(sgn*full*lo,tStart+sgn*full*lo);\n  return {dt:sgn*full*lo,event:Object.assign({},event,{msg:'⛔ topology guard: tijdelijk contact binnen de RK4-stap gevonden; gestopt aan de veilige zijde. Geen doorsnijding of reconnectie toegepast.'})};\n}",
        "transientContact",
    )
    rt = must_replace(
        rt,
        "    if(pairGapExact2(fils[ii],fils[jj],Infinity)<d2Contact){\n      if(lia&&!P.topologyGuard)return{warn:true,msg:'⚠ componenten binnen contactdrempel: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'+suffix};\n      return{warn:false,msg:'⛔ componentcontact bereikt; gestopt vóór doorsnijding. Geen reconnectie toegepast.'+suffix};\n    }\n  }\n  return null;\n}\n// v7.2: first-hit-bisectie.",
        "    if(pairGapExact2(fils[ii],fils[jj],Infinity)<d2Contact){\n      if(lia&&!P.topologyGuard)return{warn:true,msg:'⚠ componenten binnen contactdrempel: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'+suffix};\n      return{warn:false,msg:'⛔ componentcontact bereikt; gestopt vóór doorsnijding. Geen reconnectie toegepast.'+suffix};\n    }\n  }\n  const dc=vlDiscrete.contact();if(dc)return dc;\n  return null;\n}\n// v7.2: first-hit-bisectie.",
        "contactEvent",
    )
    rt = must_replace(
        rt,
        "  return bisectHitTime(signedDtFull,dt=>{\n    Y.set(Ypre);lastUmax=advanceFilamentCandidate(dt,tStart+dt);\n  },()=>{",
        "  return bisectHitTime(signedDtFull,dt=>{\n    Y.set(Ypre);vlDiscrete.restore();lastUmax=advanceFilamentCandidate(dt,tStart+dt);\n  },()=>{",
        "bisectFirstHit",
    )
    rt = must_replace(
        rt,
        "      Ypre.set(Y); // snapshot voor first-hit en transient-contact guard\n      lastUmax=advanceFilamentCandidate(signedDt,tPhys+signedDt);\n      if(!Number.isFinite(lastUmax)||!window.VortexLabFluidQualification?.allFinitePositions(Y)){\n        Y.set(Ypre);lastUmax=1e-9;stepDebt=0;",
        "      Ypre.set(Y);vlDiscrete.snapshot(); // snapshot voor first-hit en transient-contact guard\n      lastUmax=advanceFilamentCandidate(signedDt,tPhys+signedDt);\n      if(!Number.isFinite(lastUmax)||!window.VortexLabFluidQualification?.allFinitePositions(Y)||!vlDiscrete.isFinite()){\n        Y.set(Ypre);vlDiscrete.restore();lastUmax=1e-9;stepDebt=0;",
        "loop-snapshot",
    )
    rt = must_replace(
        rt,
        "        gapAfter=topologyClearance();const dmax=maxStateDisplacement(Ypre,Y);",
        "        gapAfter=topologyClearance();const dmax=Math.max(maxStateDisplacement(Ypre,Y),vlDiscrete.active()?vlDiscrete.maxDisplacementFromBefore():0);",
        "loop-dmax",
    )
    rt = must_replace(
        rt,
        "      if(!Number.isFinite(dtApplied)||!window.VortexLabFluidQualification?.allFinitePositions(Y)){\n        Y.set(Ypre);stepDebt=0;\n        setFlag('⛔ De contact-bisectie leverde niet-eindige coördinaten/tijd op; toestand teruggezet.');",
        "      if(!Number.isFinite(dtApplied)||!window.VortexLabFluidQualification?.allFinitePositions(Y)||!vlDiscrete.isFinite()){\n        Y.set(Ypre);vlDiscrete.restore();stepDebt=0;\n        setFlag('⛔ De contact-bisectie leverde niet-eindige coördinaten/tijd op; toestand teruggezet.');",
        "loop-bisect-finite",
    )
    rt = must_replace(
        rt,
        "  frame++;\n  const w=canvas.clientWidth,h=canvas.clientHeight;\n  if(canvas.width!==w||canvas.height!==h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}\n  updCam();renderer.render(scene,camera);\n}",
        "  frame++;\n  vlDiscrete.render();\n  const w=canvas.clientWidth,h=canvas.clientHeight;\n  if(canvas.width!==w||canvas.height!==h){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}\n  updCam();renderer.render(scene,camera);\n}",
        "render",
    )
    rt = must_replace(
        rt,
        "  tracerCount:tracerCount(), solverFrame:String(P.solverFrame)\n});",
        "  tracerCount:tracerCount(), solverFrame:String(P.solverFrame),discreteBundle:vlDiscrete.report()\n});",
        "diagnostics",
    )
    if "bundleBEMQuality:P.bundleBEMQuality," in rt and "discreteBundle:vlDiscrete.report()" not in rt:
        # only first modellog occurrence intended
        rt = rt.replace(
            "bundleBEMQuality:P.bundleBEMQuality,",
            "bundleBEMQuality:P.bundleBEMQuality,discreteBundle:vlDiscrete.report(),",
            1,
        )

    rt_path.write_text(rt, encoding="utf-8", newline="\n")
    print("runtime hooks applied; vlDiscrete refs =", rt.count("vlDiscrete"))

    for rel in (
        "apps/web/twist-flow/twist-flow.js",
        "apps/web/twist-flow/twist-flow.css",
        "apps/web/twist-flow/index.html",
    ):
        shutil.copy2(PAYLOAD / rel, ROOT / rel)
        print("copied", rel)

    docs = ROOT / "docs" / "patches"
    docs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STAGING / "README_NL.md", docs / "P6b_discrete_continuum_README_NL.md")
    shutil.copy2(STAGING / "manifest.json", docs / "P6b_discrete_continuum_manifest.json")
    shutil.copy2(
        STAGING / "source" / "discrete_bundle_kernel.js",
        ROOT / "apps/web/src/legacy/discrete_bundle_kernel.js",
    )
    test_src = (STAGING / "tests" / "test_discrete.js").read_text(encoding="utf-8")
    test_src = test_src.replace(
        "path.join(__dirname,'..','source','discrete_bundle_kernel.js')",
        "path.join(__dirname,'..','apps','web','src','legacy','discrete_bundle_kernel.js')",
    )
    (ROOT / "tools" / "test-p6b-discrete.js").write_text(test_src, encoding="utf-8", newline="\n")
    note = (
        "# P6b port note\n\n"
        "Official `install_patch.py --apply` refused because local sources were MODIFIED_OR_UNKNOWN\n"
        f"(backup of pre-port tree: `{backup.as_posix()}`).\n"
        "This port inserts the payload discrete kernel + solver hooks into the current runtime and\n"
        "replaces Twist Flow UI files with the P6b payload versions.\n"
    )
    (docs / "P6b_PORT_NOTE.md").write_text(note, encoding="utf-8")
    print("DONE")


if __name__ == "__main__":
    main()
