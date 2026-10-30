"""Configure the admitted successor; preserve all parent scientific settings."""
import ast
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
from preflight import ROOT, read, sha, atomic
from a054_prepare import OUT, TARGET, E010


def replace_function(text,name,replacement):
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=text.splitlines(True)
    lines[node.lineno-1:node.end_lineno]=[replacement+'\n']
    return ''.join(lines)


def main():
    p=TARGET/'a054_state/pklsa.py'
    text=p.read_text(encoding='utf-8')
    text=replace_function(text,'load_cross_manifest', '''def load_cross_manifest(path: str | Path) -> dict:
    from .admission import read, validate_manifest
    root = Path(__file__).resolve().parents[1]
    return validate_manifest(path, root.parents[3], read(root/'admission/RUNTIME_PINS.json'))['manifest']''')
    text=replace_function(text,'locate_e010', '''def locate_e010(workbench: Path):
    from .admission import read, verify_loader, workspace_path
    root = Path(__file__).resolve().parents[1]
    pins = read(root/'admission/RUNTIME_PINS.json')
    return verify_loader(workbench,pins), workspace_path(workbench,pins['e010_production'])''')
    p.write_text(text,encoding='utf-8')
    # Tests now exercise the mandatory external binding rather than accepting a dummy selection.
    (TARGET/'tests/test_e013_manifest.py').write_text('''from pathlib import Path
import pytest
from a054_state.pklsa import load_cross_manifest
from a054_state.admission import AdmissionError
ROOT=Path(__file__).resolve().parents[1]
def test_accepts_frozen_current_e013_binding():
 assert len(load_cross_manifest(ROOT/'admission/CROSS_CARRIER_MANIFEST.json')['carriers'])==5
def test_rejects_unregistered_selection(tmp_path):
 p=tmp_path/'manifest.json';p.write_text('{}')
 with pytest.raises(AdmissionError,match='external binding'):load_cross_manifest(p)
def test_rejects_missing_manifest(tmp_path):
 with pytest.raises(AdmissionError,match='missing'):load_cross_manifest(tmp_path/'missing.json')
''',encoding='utf-8')
    pins=read(TARGET/'admission/RUNTIME_PINS.json')
    pins['e010_release']={'path':str((E010/'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs/RELEASE.json').relative_to(ROOT)),
                          'sha256':sha(E010/'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs/RELEASE.json')}
    atomic(TARGET/'admission/RUNTIME_PINS.json',pins)
    contract=read(TARGET/'science_contract.json')
    # New implementation commitment for new code; inherited hypotheses/equations/thresholds remain identical.
    sys.path.insert(0,str(TARGET))
    from a054_state.commitment import compute_implementation_bundle
    bundle,rows=compute_implementation_bundle(TARGET)
    contract['implementation_commitment']['bundle_sha256']=bundle
    atomic(TARGET/'science_contract.json',contract)
    atomic(TARGET/'data/IMPLEMENTATION_MANIFEST.json',{'schema':'A054-IMPLEMENTATION-MANIFEST-1','bundle_sha256':bundle,'files':rows})
    (TARGET/'run_all.cmd').write_text('''@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
if not "%~2"=="" set "SST_WORKBENCH_ROOT=%~2"
py -3.14 -B -m pytest tests -q -p no:cacheprovider
if errorlevel 1 exit /b 1
if /I "%~1"=="SELFTEST" exit /b 0
if not "%~1"=="" if /I not "%~1"=="ADMISSION_SMOKE" (
  echo [STOP] Only SELFTEST and ADMISSION_SMOKE are authorized. No FULL, CERTIFY or REVEAL.
  exit /b 2
)
py -3.14 -B run_migration.py
exit /b %ERRORLEVEL%
''',encoding='utf-8')
    (TARGET/'run_instance.py').write_text('''from pathlib import Path
import subprocess,sys
if __name__=='__main__':
 raise SystemExit(subprocess.call(['cmd.exe','/d','/c',str(Path(__file__).with_name('run_all.cmd')),*sys.argv[1:]],cwd=Path(__file__).parent))
''',encoding='utf-8')
    (TARGET/'run_migration.py').write_text('''from pathlib import Path
import sys
sys.dont_write_bytecode=True
from a054_state.migration import run
if __name__=='__main__':
 import json
 print(json.dumps(run(Path(__file__).resolve().parent),indent=2))
''',encoding='utf-8')
    # The old full pipeline stays in the source for review, with the new namespace.
    p=TARGET/'experiment/pipeline.py'
    p.write_text(p.read_text(encoding='utf-8').replace('return root/f"{p[\'name\']}_{p[\'version\']}-outputs"','return root/f"A054_{p[\'name\']}_{p[\'version\']}_outputs"'),encoding='utf-8')
    plan=read(TARGET/'gate_plan.json')
    for g in plan['gates']:g['question']=g['question'].replace('v0.5.1','v0.6.0')
    atomic(TARGET/'gate_plan.json',plan)
    sources=[]
    for row in read(TARGET/'admission/CROSS_CARRIER_MANIFEST.json')['carriers']:
        sources.append({'source_id':row['carrier_id'],'catalog_id':'E011','version':'v0.3.0',
          'relative_path':Path(row['source_locator']['source_path']).relative_to(ROOT).as_posix(),'role':'Admitted geometry; static authority only',
          'evidence_class':'simulation','independence_family':row['provider_group'],'raw_sha256':row['raw_sha256']})
    atomic(TARGET/'source_contract.json',{'schema':'SST-SOURCE-CONTRACT-2','independent_unit':'E011 provider anchor, not physical replication; BASIC contains one provider per topology','sources':sources})
    template=TARGET/'report/FALSIFIER_REPORT.tex'
    tex=template.read_text(encoding='utf-8').replace('\\usepackage{amsmath,amssymb,booktabs,longtable,array,hyperref}',
        '\\usepackage{amsmath,amssymb,booktabs,longtable,array,graphicx,hyperref}\n\\DeclareUnicodeCharacter{2218}{\\ensuremath{\\circ}}')
    tex=tex.replace('profile \\texttt{multilibrary\\_gpu}.','registered profile \\texttt{multilibrary\\_gpu}; this execution uses only the bounded ADMISSION\\_SMOKE lane.')
    tex=tex.replace('\\section{Identification}', '\\section{Identification}\nThis v0.6.0 software migration preserves the parent scientific hypotheses and numerical thresholds. It does not execute state selection, Hessian, ringdown, native parity or reveal. The public migration protocol is frozen separately from any future complete blind campaign.\n')
    tex=tex.replace('Every E013 carrier is reloaded from exact source bytes and evaluated with one constrained objective',
        'The registered full algorithm reloads carriers and evaluates one constrained objective')
    tex=tex.replace('C++/pybind11 OpenMP FP64 certifies the common line-energy kernel at relative-L2',
        'The registered C++/pybind11 OpenMP FP64 parity criterion for the common line-energy kernel is relative-L2')
    tex=tex.replace('Framework SYCL/DD32 remains SCREENING\\_ONLY.','Framework SYCL/DD32 remains SCREENING\\_ONLY. Neither native parity nor GPU screening was executed in this admission smoke.')
    tex=tex.replace('\\section{Symbols}', '\\section{Symbols}\nAll hatted lengths, deformation coordinates and the comparison Hamiltonian are dimensionless under the registered reach normalization. No calibrated SI length, time, energy or physical dissipation is inferred.\n')
    tex=tex.replace('\\section{Results}', '\\section{Results}\n\\input{AUTO_MIGRATION_AXES.tex}\n')
    start=tex.index('Run \\texttt{run\\_00\\_install.cmd}')
    end=tex.index('\\begin{thebibliography}',start)
    tex=tex[:start]+r'''From this version directory run \texttt{run\_all.cmd SELFTEST} or \texttt{run\_all.cmd ADMISSION\_SMOKE}. CPython 3.14, NumPy, matplotlib, pytest and pdflatex are required, together with this Workbench's exact pinned framework, E010 parser and E011 sources. FULL, CERTIFY and REVEAL are blocked. The successor is disabled for global E013 discovery to preserve the enabled historical member without duplicates. Per-run parent PDFs and ZIPs are immutable; earlier output trees retain their run IDs.
'''+tex[end:]
    template.write_text(tex,encoding='utf-8')
    (TARGET/'MIGRATION_SCOPE.md').write_text('''# A054-v0.6.0 controlled migration

Explicitly admitted v0.5.1 source ZIP; Framework v1.0.10 qualified source; fresh E013 BASIC selection from current E011 anchors. Local ADMISSION_SMOKE checks five exact geometry payloads and runtime bindings. It does not execute the state selector, Hessians, ringdown, physical campaign, native parity or reveal.

Scientific hypotheses, numerical configuration files, native kernels and parent commitments are preserved. Only the new version's implementation commitment is recalculated. Global E013 discovery stays disabled for this successor; historical enabled v0.5.1 is untouched.

Run run_all.cmd SELFTEST or run_all.cmd ADMISSION_SMOKE from this directory. Full modes remain blocked pending a separately reviewed budget and scientific execution release. Source paths and hashes are in admission/RUNTIME_PINS.json. Old results and private materials are not copied.
''',encoding='utf-8')
    print('A054 adapter and report binding configured; seal only after remaining files are complete.')


if __name__=='__main__':main()
