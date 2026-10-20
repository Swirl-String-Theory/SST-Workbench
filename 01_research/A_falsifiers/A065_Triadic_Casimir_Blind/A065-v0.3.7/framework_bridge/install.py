"""Generate and execute a *genuine* SST Falsifier Framework v1.0.7 instance.

Never vendors, reimplements or modifies the frozen runtime. Calls its real
`tools/new_falsifier.py`, pins the generated instance, runs FREEZE and FULL.
The separate always-PDF renderer is invoked by triadic.entrypoint afterward.
"""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,traceback
from pathlib import Path


def _discover_framework(root):
    env=os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT','').strip()
    # An explicit override is authoritative and fail-closed; never silently
    # discover a different framework if it is invalid.
    paths=[Path(env)] if env else []
    if not env:
        wb=os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench')
        paths.append(Path(wb)/'06_templates'/'SST_Falsifier_Framework'/'SST_Falsifier_Framework_v1.0.7')
        for p in [root,*root.parents]:
            paths.append(p/'06_templates'/'SST_Falsifier_Framework'/'SST_Falsifier_Framework_v1.0.7')
    for p in paths:
        if (p/'sst_falsifier'/'__init__.py').is_file() and (p/'tools'/'new_falsifier.py').is_file():
            frozen=p/'CANONICAL_FREEZE.json'
            try:
                status=json.loads(frozen.read_text(encoding='utf-8'))
                if status.get('version')=='1.0.7' and status.get('status')=='CANONICAL_FROZEN':
                    return p.resolve()
            except (OSError,ValueError):
                pass
    return None


def _write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def patch_cpu_gate_plan(plan:dict)->dict:
    """Instance-only pre-freeze DAG change; never mutates canonical framework."""
    by_id={g['gate_id']:g for g in plan['gates']}
    by_id['G3']['requires']=['G1','G10']  # v0.3.4: numerical eligibility; G2 still records FAIL.
    by_id['G5']['requires']=['G1']
    by_id['G5']['question']='Does actual C++17 FP64 filament velocity match Python at 75/150/300? Kernel-only evidence, not full solver certification.'
    by_id['G8']['requires']=['G3','G5']
    by_id['G8']['question']='Are physical PKLSA Euler, material, surface and independent-provider closure requirements met?'
    if 'G10' not in by_id:
        plan['gates'].append({'gate_id':'G10','question':'Does refined KnotPlot spatial RK4 filament discretization pass 150/300 and 300/600 with fixed epsilon?', 'requires':['G1'],'enabled':True})
    if 'G11' not in by_id:
        plan['gates'].append({'gate_id':'G11','question':'Does authentic Fremlin C++17 provider satisfy source, spatial and time checks (simulation only)?', 'requires':['G1'],'enabled':True})
    if 'G12' not in by_id:
        plan['gates'].append({'gate_id':'G12','question':'Are historical Fourier and torus XYZ inputs hash-valid and analytically consistent?', 'requires':['G1'],'enabled':True})
    if 'G13' not in by_id:
        plan['gates'].append({'gate_id':'G13','question':'Do both historical geometries satisfy preregistered reduced filament ODE resolution and C++ Python parity?', 'requires':['G12'],'enabled':True})
    if 'G14' not in by_id:
        plan['gates'].append({'gate_id':'G14','question':'Were epsilon sensitivity diagnostics recorded without fitting physical claims?', 'requires':['G12'],'enabled':True})
    for gid,question,requires in [
        ('G15','Are direct-analytic historical 600/1200/2400/4800 XYZ hash and nesting controls valid?',['G1']),
        ('G16','Do BOTH historical trefoils meet 1 percent spatial convergence at baseline epsilon 0.12, 600 to 4800?',['G15']),
        ('G17','Are all three precommitted finite-core epsilon scans and complete 4800 point diagnostics recorded?',['G15']),
        ('G18','Does native C++17 RK4 meet temporal convergence at 1200/4800 and Python spot parity?',['G15'])]:
        if gid not in by_id:
            plan['gates'].append({'gate_id':gid,'question':question,'requires':requires,'enabled':True})
    for gid,question,requires in [
        ('G19','Does the on-run analytic trefoil generator reproduce sealed XYZ and its arclength parameters?',['G1']),
        ('G20','Are N-dependent segment-to-epsilon ratios computed and declared without fitting a physical core?',['G19']),
        ('G21','Do fresh formula-generated N1200/2400/4800 trefoils converge at fixed epsilon 0.06 in native RK4?',['G19'])]:
        if gid not in {g['gate_id'] for g in plan['gates']}:
            plan['gates'].append({'gate_id':gid,'question':question,'requires':requires,'enabled':True})
    for gid,question,requires in [
      ('G22','Do the synthetic finite-vorticity source invariants, preregistration and immutable legacy seals verify?',['G1']),
      ('G23','Can profile-conditional finite core width a be independently recovered from Gamma and cross-sectional enstrophy?',['G22']),
      ('G24','Does one slope-matched Rosenhead epsilon predict held-out swirl AND pressure-gradient fields within 5 percent?',['G23']),
      ('G25','Do distinct legitimate kernel-equivalence mappings imply materially distinct epsilon values (nonuniqueness diagnostic)?',['G23']),
      ('G26','Does an actually compiled C++17 FP64 radial-kernel path match Python, kernel-only?',['G22']),
      ('G27','Is a measured, independent full-PKLSA transverse vorticity core and separate held-out force/velocity provider qualified?',['G22'])]:
        if gid not in {g['gate_id'] for g in plan['gates']}:
            plan['gates'].append({'gate_id':gid,'question':question,'requires':requires,'enabled':True})
    return plan

def _merge_additive(src: Path, dst: Path) -> dict:
    """Merge instance-owned additions into generated framework scaffold.

    Never delete or overwrite generator-owned material. Existing, byte-identical
    files are accepted; a different existing file is a hard error. All copies
    use exclusive creation and ignore runtime artifacts.
    """
    src, dst = Path(src), Path(dst)
    if not src.is_dir():
        raise FileNotFoundError(f'Instance source directory missing: {src}')
    counters = {'created': 0, 'identical': 0}
    ignored = {'__pycache__', '.pytest_cache', '.venv', 'build', 'dist'}
    for original in sorted(src.rglob('*')):
        rel = original.relative_to(src)
        if any(part in ignored for part in rel.parts) or original.suffix.lower() in ('.pyc', '.pyd', '.dll', '.exe'):
            continue
        if original.is_symlink():
            raise RuntimeError(f'INSTANCE_MERGE_REFUSES_SYMLINK: {original}')
        if original.is_dir():
            (dst / rel).mkdir(parents=True, exist_ok=True)
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not target.is_file():
                raise RuntimeError(f'INSTANCE_MERGE_FILE_TYPE_CONFLICT: {target}')
            src_digest=hashlib.sha256(original.read_bytes()).digest()
            dst_digest=hashlib.sha256(target.read_bytes()).digest()
            if src_digest!=dst_digest:
                raise RuntimeError(f'INSTANCE_MERGE_REFUSES_OVERWRITE: {target}')
            counters['identical'] += 1
            continue
        with original.open('rb') as inp, target.open('xb') as out:
            shutil.copyfileobj(inp, out)
        counters['created'] += 1
    return counters


def _configure(root,instance):
    # Framework generator creates native/ and preregistration/ itself. An
    # additive, collision-checked merge is mandatory; bare copytree fails on
    # Windows with WinError 183 and dirs_exist_ok would silently overwrite.
    for folder in ('data','seals','triadic','native','preregistration'):
        _merge_additive(root/folder,instance/folder)
    shutil.copy2(root/'framework_bridge'/'pipeline.py',instance/'experiment'/'pipeline.py')
    # Commit one provider observation. Both paths verify exactly these bytes.
    provider_in=root/'outputs'/'PROVIDER_MANIFEST.json'
    if not provider_in.is_file():
        raise RuntimeError('Missing run provider manifest before official instance creation')
    (instance/'outputs').mkdir(exist_ok=True)
    shutil.copy2(provider_in,instance/'outputs'/'PROVIDER_MANIFEST.json')
    # The official resolver defaults to a Workbench root; for this portable
    # instance, independently sealed source paths are instance-relative.
    launch=instance/'run_instance.py'
    s=launch.read_text(encoding='utf-8')
    s=s.replace('ROOT = Path(__file__).resolve().parent','ROOT = Path(__file__).resolve().parent\nimport os\nos.environ["SST_WORKBENCH_ROOT"] = str(ROOT)')
    launch.write_text(s,encoding='utf-8')
    toml=instance/'falsifier.toml'
    s=toml.read_text(encoding='utf-8').replace('pdf_required = false','pdf_required = true')
    # A missing native LaTeX PDF is a hard failure in strict FRAMEWORK/FULL.
    # The companion portable PDF is independently regenerated by entrypoint.
    toml.write_text(s,encoding='utf-8')
    symbols=[{'symbol':'u','meaning':'Material velocity','si_unit':'m/s','dimensions':'L/T'},
             {'symbol':'omega','meaning':'Material vorticity','si_unit':'1/s','dimensions':'1/T'},
             {'symbol':'p','meaning':'Euler pressure','si_unit':'Pa','dimensions':'M/(L T^2)'}]
    eqs=[{'id':'E1','purpose':'Incompressible Euler kinematics','latex':r'\\nabla\\cdot\\mathbf u=0,\\quad\\boldsymbol\\omega=\\nabla\\times\\mathbf u','inputs':['u'],'outputs':['omega'],'dimensional_check':'divergence and vorticity both inverse seconds'},
         {'id':'E2','purpose':'Pressure Poisson source','latex':r'\\nabla^2p=\\rho_M(\\frac12|\\omega|^2-||S||_F^2)','inputs':['u','omega','p'],'outputs':['p'],'dimensional_check':'kg/(m^3 s^2) on each side'},
         {'id':'E3','purpose':'Regularized geometric velocity diagnostic','latex':r'\\mathbf u(\\mathbf x)=\\frac{1}{4\\pi}\\sum_j\\frac{\\Delta\\mathbf X_j\\times(\\mathbf x-\\mathbf X_{j+1/2})}{(|\\mathbf x-\\mathbf X_{j+1/2}|^2+\\varepsilon^2)^{3/2}}','inputs':['centerline'],'outputs':['u'],'dimensional_check':'dimensionless Gamma=1 geometry diagnostic'}]
    # LaTeX inputs must contain actual single-backslash command sequences.
    for e in eqs:e['latex']=e['latex'].replace('\\\\','\\')
    science={'schema':'SST-SCIENCE-CONTRACT-2',
      'research_question':'Does a preregistered triadic clock/stress geometry pilot satisfy its analytic controls while independent physical coupling gates remain unresolved?',
      'objective':'Independently verify three dataset seals, analytic Euler/gauge/sheet controls and one sourced KnotPlot trefoil finite-core geometric response without importing target force.',
      'null_hypothesis':'No independently qualified source-specific physical two-surface response is established by the present geometry and toy models.',
      'alternative_hypothesis':'Independently qualified PKLSA Euler motion, boundary conditions and microscopic link coupling produce held-out physical predictions.',
      'assumptions':['The 300-node KnotPlot trefoil is real geometric source material, not a fluid-time solution.',
                     'Dimensionless circulation and regularization are diagnostic choices, not calibrated SST constants.',
                     'The scalar sheet reflection model is a toy control, not actual metal response.',
                     'Fremlin A006 raw geometry is external; its separately compiled C++17 time evolution is a testable ODE simulation, not independent Euler-PDE validation.'],
      'symbols':symbols,'equations':eqs,
      'observables':[{'id':'O1','definition':'Three independent source SHA256 seals','equation_refs':['E1'],'unit':'1'},
                     {'id':'O2','definition':'Geometry-convergence and Poisson diagnostic residuals','equation_refs':['E2','E3'],'unit':'1'}],
      'steps':[{'id':'S1','operation':'Verify all three source seals before any scientific result is evaluated','formula_refs':['E1'],'gate':'G1'},
               {'id':'S2','operation':'Evaluate analytic Euler controls and preregistered trefoil geometry resolution scan','formula_refs':['E2','E3'],'gate':'G2'},
               {'id':'S3','operation':'Withhold physical Casimir claims without independent providers, wall dynamics, and atom-link normalization','formula_refs':['E3'],'gate':'G3'}],
      'falsification_criteria':[{'id':'F1','criterion':'Any source seal mismatch invalidates the run','conclusion_if_met':'INVALID'},
                                {'id':'F2','criterion':'Any preregistered analytic benchmark fails its tolerance','conclusion_if_met':'FAIL'},
                                {'id':'F3','criterion':'A physical claim cannot be substantiated without two independent dynamic upstream providers','conclusion_if_met':'UNRESOLVED'}],
      'edge_cases':['Irrotational, nonuniform-clock synthetic flow','decoupled zero-force sheet','missing second provider','unchanged physical results under pure gauge relabeling'],
      'predictions':['Precommitted reference identities and finite geometric velocity fields, no target Casimir amplitude.']}
    # Bind supplemental precommit into the canonical v1.0.7 protocol bundle,
    # even though the framework's DEFAULT_PROTOCOL_FILES is immutable.
    qbytes=(root/'preregistration'/'QUALIFICATION_V032.json').read_bytes()
    rbytes=(root/'preregistration'/'ROUTING_V033.json').read_bytes()
    rhash=hashlib.sha256(rbytes).hexdigest()
    qhash=hashlib.sha256(qbytes).hexdigest()
    source_cpp_hash=hashlib.sha256((root/'native'/'fremlin_propagator.cpp').read_bytes()).hexdigest()
    histbytes=(root/'preregistration'/'HISTORICAL_V034.json').read_bytes()
    histhash=hashlib.sha256(histbytes).hexdigest()
    science['assumptions'].append('v0.3.2 preregistration SHA256=' + qhash + '; 600 nodes cubic-interpolated from N300')
    science['assumptions'].append('v0.3.3 preregistered routing SHA256=' + rhash + '; G3 requires G1+G10; G2 historical FAIL retained; physical verdict unresolved')
    science['assumptions'].append('Optional Fremlin C++17 independent simulation kernel SHA256=' + source_cpp_hash)
    science['assumptions'].append('v0.3.4 historical geometry preregistration SHA256=' + histhash + '; source class historical initial geometry only; no core calibration')
    hi_hash=hashlib.sha256((root/'preregistration/HIGHRES_V035.json').read_bytes()).hexdigest()
    science['assumptions'].append('v0.3.5 high-resolution preregistration SHA256=' + hi_hash + '; direct analytic N2400/N4800 coordinates, original source seals preserved, numerical only')
    science['steps'].extend([
        {'id':'S10','operation':'Verify direct parametric XYZ N600 to N4800 hashes and nesting','formula_refs':['E3'],'gate':'G15'},
        {'id':'S11','operation':'Independent fixed-core 1 percent spatial convergence at baseline epsilon=0.12 across BOTH historical trefoils','formula_refs':['E3'],'gate':'G16'},
        {'id':'S12','operation':'Report eps 0.06 0.12 0.24 numerical core sensitivity without physical force normalization','formula_refs':['E3'],'gate':'G17'},
        {'id':'S13','operation':'Check C++17 1200 and 4800 time step refinement and Python N150 parity','formula_refs':['E3'],'gate':'G18'}])
    science['falsification_criteria'].append({'id':'F8','criterion':'New source hash or precommitted v0.3.5 numerical rule changed','conclusion_if_met':'INVALID'})
    science['steps'].append({'id':'S7','operation':'Audit historical Fourier and torus XYZ hash and analytic geometry','formula_refs':['E3'],'gate':'G12'})
    science['steps'].append({'id':'S8','operation':'Compare reduced vortex filament RK4 spatial/time resolution on independent geometric seeds','formula_refs':['E3'],'gate':'G13'})
    science['steps'].append({'id':'S9','operation':'Report fixed core regularization sensitivity without physical force interpretation','formula_refs':['E3'],'gate':'G14'})
    science['falsification_criteria'].append({'id':'F7','criterion':'Historic XYZ bytes, source formulas or extra-scientific parameters change from precommit','conclusion_if_met':'INVALID'})
    science['steps'].append({'id':'S4','operation':'Verify fixed-core 150/300/600 convergence, separately retaining original G2 failures',
                             'formula_refs':['E3'],'gate':'G10'})
    science['steps'].append({'id':'S6','operation':'Evaluate G3 only after precommitted G1+G10 and temporal/analytic guard; retain G2=FAIL and physical UNRESOLVED',
                             'formula_refs':['E1','E2','E3'],'gate':'G3'})
    science['steps'].append({'id':'S5','operation':'Verify exact Fremlin raw hash and native C++ time-series refinement; never infer real Euler solution',
                             'formula_refs':['E3'],'gate':'G11'})
    science['falsification_criteria'].append({'id':'F4','criterion':'Changing the v0.3.2 preregistered epsilon, T, gamma or spatial tolerance invalidates the run',
                                               'conclusion_if_met':'INVALID'})
    science['falsification_criteria'].append({'id':'F6','criterion':'Unexpected analytic failure, changed protected source, G10/time failure or routing prereg mismatch blocks G3 execution',
                                               'conclusion_if_met':'NOT_RUN_PREREQUISITE'})
    science['falsification_criteria'].append({'id':'F5','criterion':'Missing or hash-mismatched Fremlin source cannot qualify G11 as PASS',
                                               'conclusion_if_met':'UNRESOLVED'})
    genhash=hashlib.sha256((root/'preregistration/GENERATED_V036.json').read_bytes()).hexdigest()
    science['assumptions'].append('v0.3.7 generated-geometry preregistration SHA256='+genhash+'; fixed dimensionless epsilon=0.06, formula regenerated coordinates and native RK4 numerical only')
    science['steps'].extend([
      {'id':'S19','operation':'Regenerate 2015 parametric trefoils inside falsifier, hash-check vs pinned XYZ and original generator','formula_refs':['E3'],'gate':'G19'},
      {'id':'S20','operation':'Measure mean segment length divided by fixed regularization epsilon at each resolution without fitting','formula_refs':['E3'],'gate':'G20'},
      {'id':'S21','operation':'Test native C++ RK4 fine-mesh spatial convergence for regenerated trefoils at epsilon=0.06','formula_refs':['E3'],'gate':'G21'}])
    science['falsification_criteria'].append({'id':'F19','criterion':'Original analytic seed / pinned generator mismatch, changed generator preregistration or unexpected additional source','conclusion_if_met':'INVALID'})
    science['falsification_criteria'].append({'id':'F21','criterion':'Any regenerated-geometry N1200/N2400 or N2400/N4800 comparison fails 1 percent at fixed epsilon=0.06','conclusion_if_met':'FAIL'})
    fc_hash=hashlib.sha256((root/'preregistration/FINITE_CORE_V037.json').read_bytes()).hexdigest()
    science['assumptions'].append('A065 v0.3.7 finite-core methodological synthetic cross-sections only; prereg SHA256='+fc_hash+'; G22-G27 cannot promote physical core, Euler or Casimir closure')
    science['equations'].extend([
        {'id':'E4','purpose':'Profile-dependent cross-sectional enstrophy inverse','latex':r'Z_G=\Gamma^2/(2\pi a^2),\quad Z_R=\Gamma^2/(\pi a^2)','inputs':['Gamma','Z'],'outputs':['a'],'dimensional_check':'Gamma^2/Z = L^2 for SI cross-section'},
        {'id':'E5','purpose':'Rosenhead regularization swirl and steady radial pressure balance','latex':r'v_{RM}=\Gamma r/(2\pi(r^2+\varepsilon^2)),\quad \partial_r p=\rho v_\theta^2/r','inputs':['Gamma','r','epsilon','rho'],'outputs':['velocity','radial_pressure_gradient'],'dimensional_check':'pressure gradient M/(L^2 T^2)'}])
    science['steps'].extend([{'id':'S'+str(i),'operation':desc,'formula_refs':['E4','E5'],'gate':'G'+str(i)} for i,desc in [(22,'Verify precommitted finite-core analytic source'),(23,'Invert independently specified Gamma and Z'),(24,'Hold out vortex and pressure-gradient comparisons, no cutoff refit'),(25,'Test mapping nonuniqueness'),(26,'Verify native FP64 kernel parity'),(27,'Keep physical core unqualified without external vorticity cross section')]])
    science['falsification_criteria'].append({'id':'F24','criterion':'Any held-out velocity or pressure-gradient Rosenhead RMS exceeds 5 percent','conclusion_if_met':'FAIL_REPRESENTABILITY'})
    _write_json(instance/'science_contract.json',science)
    source={'schema':'SST-SOURCE-CONTRACT-2','independent_unit':'Upstream geometry production family, never numerical subsample',
            'sources':[{'source_id':a,'catalog_id':cat,'version':'v0.3.7','relative_path':path,'role':role,
                        'independence_family':fam,'provenance_family':fam,'evidence_class':ec,'override_path':None}
                       for (a,cat,path,role,fam,ec) in [
                        ('D01','A046','data/D01_EULER/cases.json','analytic_control','synthetic-euler','synthetic_control'),
                        ('PKLSA','E010','data/D01_EULER/pklsa/trefoil_KnotPlot_relaxed_N300.txt','geometry_diagnostic','knotplot-relaxed-3_1','simulation'),
                        ('D02','CANON','data/D02_CLOCK_LINK/single_surface.json','toy_control','synthetic-link','synthetic_control'),
                        ('D03','CANON','data/D03_TWO_SURFACE/conditions.json','heldout_control','synthetic-sheet','synthetic_control')]],
            'parser_contract':'PKLSA 3 numeric float coordinates per row; closed periodic centerline, raw hash verified',
            'translator_contract':'Regularized dimensionless segment Biot-Savart, no physical wall or atom-link parameter inference',
            'allow_no_external_sources':False,
            'replication_policy':{'require_explicit_evidence_class':True,'min_independent_groups':2,'synthetic_controls_may_close_cross_source':False}}
    _write_json(instance/'source_contract.json',source)
    # The canonical framework's autogenerated TeX table uses verbatim gate
    # questions. Older gate-plan labels contain Unicode arrows not recognized
    # by pdfLaTeX (e.g. CPU<->GPU). Sanitize labels *before* FREEZE in the new
    # instance; never modify the canonical framework's frozen template.
    gatepath=instance/'gate_plan.json'
    plan=json.loads(gatepath.read_text(encoding='utf-8'))
    for gate in plan['gates']:
        question=gate['question']
        for before,after in [('↔',' to '),('→',' to '),('≤',' <= '),('≥',' >= '),('–','-'),('—','-')]:
            question=question.replace(before,after)
        gate['question']=question
    # Corrected PRE-FREEZE, INSTANCE-LOCAL CPU DAG.
    plan=patch_cpu_gate_plan(plan)
    _write_json(gatepath,plan)
    # Pre-freeze report: the 16 official section markers are all required.
    sections=[('IDENTIFICATION','Instance identity','A065-v0.3.7 versioned Triadic-Casimir research instance.'),
     ('QUESTION','Research question',science['research_question']),('HYPOTHESES','Null and alternative hypotheses',science['null_hypothesis']),
     ('ASSUMPTIONS','Explicit assumptions','Time-dependent regularized filament RK4 is exploratory and is not full Euler closure.'),
     ('SYMBOLS','Definitions','u material velocity; omega=curl u; S symmetric strain.'),
     ('EQUATIONS','Analytical equations','The official AUTO_SCIENCE_CONTRACT fragment records frozen equations.'),
     ('ALGORITHM','Scientific algorithm','Verify three seals; compute controls; evaluate trefoil diagnostic.'),
     ('SOURCES','Dataset provenance','D01 D02 D03, KnotPlot N300, external Fremlin and separate 2015 historical Fourier and torus geometric seeds. No historical geometry is physical PKLSA evidence.'),
     ('GATES','Independent gates','G12-G14 remain historical tests; G15-G18 separately qualify direct N600-N4800 geometries and reduced ODE, independent of physical G3. No physical conclusions.'),
     ('NUMERICS','Numerical controls','Dimensionless finite-segment Biot-Savart and finite-difference derivatives.'),
     ('BACKENDS','Backend authority','CPU profile enables strict C++ gate; G3 may be evaluated but physical validation remains unresolved.'),
     ('BLINDNESS','Blindness and integrity','All three dataset SHA256 seals checked; reveal comparator not used in blind kernel.'),
     ('STATISTICS','Statistics','Geometry subsamples are not independent upstream providers.'),
     ('RESULTS','Result status','Read dynamic AUTO_RESULTS fragment; no target-matched force.'),
     ('INTERPRETATION','Scientific interpretation','Physical Casimir force and gravitation remain unvalidated.'),
     ('REPRODUCIBILITY','Reproduction','Run native FREEZE and FULL via the installation bridge.')]
    raw=[r'\\documentclass[10pt,a4paper]{article}',r'\\usepackage[margin=18mm]{geometry}',r'\\usepackage{amsmath,amssymb,booktabs,longtable,hyperref}',r'\\title{Triadic Casimir --- PKLSA v0.3.5 Framework Report}',r'\\author{SST Workbench / Unregistered instance}',r'\\begin{document}',r'\\maketitle']
    for marker,title,content in sections:
        raw.append('%% SST-REPORT-SECTION:'+marker)
        raw.append(r'\\section{'+title+'}')
        raw.append(content.replace('_',r'\\_'))
        if marker=='EQUATIONS':raw.append(r'\\input{AUTO_SCIENCE_CONTRACT.tex}')
        if marker=='RESULTS':raw.append(r'\\input{AUTO_RESULTS.tex}')
    raw.append(r'\\end{document}')
    (instance/'report'/'FALSIFIER_REPORT.tex').write_text(('\n'.join(raw)+'\n').replace('\\\\','\\'),encoding='utf-8')
    # No-reveal guard: opening physical comparator after unresolved physical gate is blocked.
    policy=instance/'blind_policy.json';d=json.loads(policy.read_text(encoding='utf-8'))
    d['block_reveal_on_unresolved']=True
    d['reveal_requires_gate']='G3'
    d['reveal_requires_gate_status']=['PASS','FAIL']
    _write_json(policy,d)
    (instance/'private'/'blind_forbidden_terms.txt').write_text('REVEAL_ONLY_TARGET\n',encoding='utf-8')
    _write_json(instance/'private'/'reveal.json',{'schema':'SST-REVEAL-DATA-2','external_physical_target':'NOT_INCLUDED','note':'No physical amplitude or model-derived surface response'} )


def run_framework(root):
    root=Path(root).resolve();framework=_discover_framework(root)
    if framework is None:
        return {'state':'FRAMEWORK_NOT_FOUND','detail':'Set SST_FALSIFIER_FRAMEWORK_ROOT to frozen v1.0.7, or install under C:\\workspace\\projects\\SST-Workbench\\06_templates\\SST_Falsifier_Framework\\SST_Falsifier_Framework_v1.0.7.'}
    instance=root/'FRAMEWORK_INSTANCE'/'A065-v0.3.7'
    log=root/'reports'/'FRAMEWORK_RUN.log';log.parent.mkdir(parents=True,exist_ok=True)
    localpy=framework/'.venv'/'Scripts'/'python.exe'
    exe=str(localpy) if localpy.exists() else sys.executable
    details=[]
    try:
        if not instance.exists():
            instance.parent.mkdir(parents=True,exist_ok=True)
            c=[exe,str(framework/'tools'/'new_falsifier.py'),'A065','Triadic_Casimir',str(instance),'--profile','cpu','--version','v0.3.7']
            x=subprocess.run(c,capture_output=True,text=True,timeout=120)
            details.append({'stage':'OFFICIAL_INSTANCE_GENERATOR','returncode':x.returncode,'output':x.stdout[-3000:],'error':x.stderr[-3000:]})
            if x.returncode:raise RuntimeError('Official new_falsifier.py failed: '+x.stderr[-1000:])
            _configure(root,instance)
        env=os.environ.copy();env['SST_FALSIFIER_FRAMEWORK_ROOT']=str(framework)
        env['SST_WORKBENCH_ROOT']=str(instance)
        for mode in ('FREEZE','FULL','REVEAL_IF_ALLOWED'):
            cp=subprocess.run([exe,str(instance/'run_instance.py'),mode],cwd=str(instance),env=env,capture_output=True,text=True,timeout=600)
            details.append({'stage':mode,'returncode':cp.returncode,'output':cp.stdout[-3500:],'error':cp.stderr[-3500:]})
            if cp.returncode:raise RuntimeError(f'Official framework {mode} failed; inspect reports/FRAMEWORK_RUN.log')
        # Record the actual native reporter status separately from successful
        # protocol/gate execution. The portable top-level PDF is guaranteed
        # by triadic.report_pdf after this function returns.
        out=instance/'Triadic_Casimir_v0.3.7-outputs'
        render=out/'REPORT_RENDER.json'
        native_report=json.loads(render.read_text(encoding='utf-8')) if render.exists() else {'status':'MISSING'}
        return {'state':'OFFICIAL_FRAMEWORK_EXECUTED','detail':'Canonical framework v1.0.7 executed in a new pinned v0.3.7 instance; physical G3 remains held.',
                'native_report':{'success':native_report.get('success',False),'status':native_report.get('status','UNKNOWN')},
                'framework_root':str(framework),'instance_path':str(instance),'stages':[d['stage'] for d in details]}
    except Exception as exc:
        return {'state':'OFFICIAL_FRAMEWORK_FAILED','detail':str(exc),'framework_root':str(framework),'instance_path':str(instance)}
    finally:
        log.write_text(json.dumps(details,indent=2)+'\n',encoding='utf-8')
