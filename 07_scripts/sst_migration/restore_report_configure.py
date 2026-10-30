"""Bind existing A011 science data to the existing framework report template API."""
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha
from phase3_prepare import create_json
from restore_report_prepare import FAMILY

DEST = FAMILY / 'A011-v0.4.1'


def main():
    sys.path.insert(0, str(DEST / 'src'))
    from maxwell_sst_falsifier.framework_v110 import qualified_framework
    qualified_framework(DEST)
    from sst_falsifier.report import latex_escape as e, assert_report
    from sst_falsifier.science_contract import assert_science_contract
    from sst_falsifier.source_registry import assert_source_contract
    science = read(DEST / 'science_contract.json')
    plan = read(DEST / 'config/geometry_smoke_v040.json')
    prefix = 'A011_Maxwell_SST_Kinetic_Falsifier'
    binding = ROOT / '07_scripts/sst_migration/report_output_contract.py'
    create_json(DEST / 'REPORT_OUTPUT_CONTRACT.json', {'schema': 'SST-MIGRATED-REPORT-OUTPUT-CONTRACT-1', 'output_prefix': prefix,
                'output_pattern': '<output_prefix>_<version>_outputs', 'publication': 'Parent directory; immutable run-ID PDF and ZIP plus SHA256',
                'binding': binding.relative_to(ROOT).as_posix(), 'binding_sha256': sha(binding), 'renderer': 'Qualified sst_falsifier.report; no alternate scientific PDF generator',
                'historical_reference': 'A011-v0.4.0 audited and preserved; correction in packaging-only v0.4.1'})
    sources = []
    for seed in plan['seeds']:
        sources.append({'source_id': seed['carrier_id'], 'catalog_id': 'E010', 'version': 'E010-v0.3.1/view-v0.3.4',
                        'relative_path': Path(seed['source_path']).relative_to(ROOT).as_posix(), 'role': 'admitted_geometry_diagnostic',
                        'independence_family': 'knotplot_relaxation', 'evidence_class': 'simulation', 'raw_sha256': seed['raw_sha256'],
                        'geometry_sha256': seed['geometry_sha256'], 'qualification': 'GEOMETRY_ONLY_NOT_PHYSICAL'})
    create_json(DEST / 'source_contract.json', {'schema': 'SST-SOURCE-CONTRACT-2', 'independent_unit': 'Exact admitted carrier; all selected sources share a KnotPlot provenance family, not independent physical replications',
                'sources': sources, 'allow_no_external_sources': False, 'parser_contract': 'Exact E010 source-native loader pinned by E010_SOURCE_PIN.json',
                'translator_contract': 'No source replacement, threshold fitting or physical scale inference; admitted source-native units retained',
                'replication_policy': {'require_explicit_evidence_class': True, 'min_independent_groups': 2, 'synthetic_controls_may_close_cross_source': False}})
    report = DEST / 'report'
    report.mkdir(exist_ok=True)
    lines = [r'\documentclass[10pt,a4paper]{article}', r'\usepackage[margin=20mm]{geometry}', r'\usepackage[T1]{fontenc}', r'\usepackage[utf8]{inputenc}',
             r'\usepackage{lmodern,amsmath,amssymb,booktabs,longtable,array,graphicx,xurl}', r'\usepackage[hidelinks]{hyperref}',
             r'\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}', r'\title{A011 --- Maxwell SST Kinetic Falsifier\\v0.4.1 Scientific Protocol and Falsifier Report}',
             r'\author{SST-Workbench}', r'\date{Framework v1.0.10; controlled geometry diagnostic tranche}', r'\begin{document}\maketitle']
    def section(marker, title, text):
        lines.extend(['% SST-REPORT-SECTION:' + marker, r'\section{' + title + '}', text])
    section('IDENTIFICATION', 'Identification, version and authority', 'A011 v0.4.1 is a packaging/report binding patch of the preserved v0.4.0 geometry pilot. It uses the byte-qualified SST Falsifier Framework v1.0.10. Equations, source geometry, parity thresholds and physical input requirements are unchanged. Scientific claims remain unresolved; software execution is not physical certification.')
    section('QUESTION', 'Research question and scientific objective', e(science['research_question']) + '\n\n' + e(science['objective']))
    section('HYPOTHESES', 'Null and alternative hypotheses; falsification criteria', r'\paragraph{$H_0$.} ' + e(science['null_hypothesis']) + r'\paragraph{$H_1$.} ' + e(science['alternative_hypothesis']))
    lines.append(r'\begin{itemize}')
    for criterion in science['falsification_criteria']:
        lines.append(r'\item ' + e(criterion['id'] + ': ' + criterion['criterion'] + ' Recorded consequence: ' + criterion['conclusion_if_met']))
    lines.append(r'\end{itemize}')
    section('ASSUMPTIONS', 'Assumptions, domain and edge cases', r'\begin{enumerate}' + '\n'.join(r'\item ' + e(s) for s in science['assumptions']) + r'\end{enumerate}')
    lines.append('Registered edge cases: ' + e('; '.join(science['edge_cases'])))
    section('SYMBOLS', 'Symbols, definitions, SI units and dimensional audit', r'\begin{longtable}{p{0.11\linewidth}p{0.31\linewidth}p{0.29\linewidth}p{0.18\linewidth}}\toprule Symbol & Definition & SI unit / scale & Dimensions\\\midrule')
    for sym in science['symbols']:
        lines.append('$' + sym['symbol'] + '$ & ' + ' & '.join(e(sym[k]) for k in ['meaning', 'si_unit', 'dimensions']) + r' \\')
    lines += [r'\bottomrule\end{longtable}', r'$v_{cpp,j}$ and $v_{py,j}$ are the corresponding native/reference kernel-test components in E2; $N$ counts resampled points. Curvature has inverse native-coordinate units. There is no independently calibrated SI length/time conversion. Gamma=1, smoothing=0.05 and the fixed probe offset are nondimensional software probes, not measured physical inputs.']
    section('EQUATIONS', 'Registered equations and code-to-mathematics mapping', r'\input{AUTO_SCIENCE_CONTRACT.tex}' + '\nOnly the equations registered in the inherited science contract are asserted here. Other inherited geometry diagnostics are defined by the cited implementation; no missing physical model is invented.')
    section('ALGORITHM', 'Algorithm, phases and execution order', r'\begin{enumerate}\item Verify qualified framework, frozen geometry protocol and report/output binding.\item Run targeted tests before any fresh bounded smoke.\item Rehash the three admitted carrier descriptors, source bytes, parsed geometry and qualification evidence.\item Apply the unchanged A011 resampling and geometry kernels at N=64 and N=128.\item Attempt independent implemented evaluators despite unavailable physical prerequisites; record raw outcomes and recursive qualification separately.\item Seal machine evidence; generate scientific TeX with the existing framework; compile the PDF; publish a unique ZIP and SHA-256 sidecar.\end{enumerate}')
    section('SOURCES', 'Sources, provenance and dataset qualification', r'Only the exact sources in source\_contract.json and the Phase 2 A011 admission ledger are used. Raw and parsed geometry hashes and prerequisite capability records are reverified. All three are numerical KnotPlot geometry sources, not independent physical replications. The complete current source manifest is included by the automatic results section. The qualified framework and E010 parser pins remain separate from scientific qualification.')
    section('GATES', 'Migration, execution and scientific gates', r'Migration, execution and scientific statuses are separate axes. G0/G1 verify protocol/source integrity; G2 measures finite geometry diagnostics. G5 measures actual native/reference parity but remains DIAGNOSTIC\_ONLY when G3/G4 physical prerequisites are unavailable. G3/G4/G7/G8 remain not executed for missing evidence. GPU G6 is disabled and reveal G9 is deferred. Exact current records, qualifications and allows-dependent-claim fields are generated directly from the machine ledger below.')
    section('NUMERICS', 'Numerical methods, tolerances and convergence criteria', r'Unchanged uniform polygon arclength resampling, discrete geometry diagnostics and FP64 kernels from A011 v0.3.1 are used. The frozen ladder is $N=64,128$. Native/reference velocity uses rtol=$10^{-11}$ and atol=$10^{-12}$; writhe and distance require absolute deltas $<10^{-11}$. No NaN/Inf, source drift or missing native module is replaced by a warning. These two resolutions expose sensitivity only: no spatial, time, solver or regularization convergence certificate is claimed. Missing physical error budgets remain unresolved.')
    section('BACKENDS', 'Backend manifest and authority', 'CPython 3.14/NumPy FP64 is the transparent reference. The inherited byte-pinned Windows cp314 C++17 kernel is used without rebuilding or silent fallback; its legacy backend version remains 0.3.1-cpp17. This is geometry-kernel implementation evidence only. No GPU, physical solver parity or independently authenticated compiler rebuild is claimed. Actual environment and binary/source hashes are rendered below.')
    section('BLINDNESS', 'Blind/reveal boundaries', 'No private target is opened, no expected winner is optimized and no reveal is performed. This is a nonrevealed geometry-diagnostic adapter run, not the complete private-target BLIND/REVEAL experiment. The generic framework automatic provenance uses BLIND for unrevealed output; in this report that label does not assert a completed physical blind campaign. No historical dataset seal or blind/reveal commitment is modified.')
    section('STATISTICS', 'Uncertainty, independence and statistical limits', 'The three representative topologies are fixed in advance; carrier ordering is lexicographic after exact admission and size filters. There is no random sample, fitted parameter, p-value or population-level significance claim. The common source lineage does not provide independent replication. Resolution differences, parity residuals and missing physical uncertainty are reported separately.')
    section('RESULTS', 'Automatic results, tables and diagnostic graphs', r'\input{AUTO_ADAPTER_RESULTS.tex}\input{AUTO_RESULTS.tex}')
    section('INTERPRETATION', 'Interpretation, falsification limits and unresolved claims', 'A finite geometry metric or kernel-parity PASS supports only the named implementation diagnostic. It does not establish an energy spectrum, thermodynamic closure, gravity, Euler/Casimir mechanism or new SST prediction. A parity or numerical failure is a failed software check, not independent physical falsification. Missing source calibration, held-out fields, energies, gaps, state counts and convergence evidence remain explicit. Historical negatives and prior runs are preserved.')
    section('REPRODUCIBILITY', 'Reproducibility and execution instructions', r'From this version directory on Windows execute \texttt{run\_all.cmd}; \texttt{run\_all.cmd SELFTEST} runs tests only. CPython 3.14, the pinned native binary and the qualified local framework/source paths are required. Scientific PDF generation uses the framework LaTeX compiler and fails closed if it cannot compile. Outputs use the declared catalog/family prefix and \texttt{\_outputs}; prior canonical output is retained under its run ID. PDF and ZIP publications are one directory above this version and include immutable run IDs. The adjacent SHA-256 verifies each ZIP. \texttt{LATEST\_RUN.json} is the only replaceable publication pointer; \texttt{PUBLICATIONS.jsonl} is append-only.')
    lines += [r'\section{References and primary reproducibility records}', r'\begin{enumerate}',
              r'\item \texttt{science\_contract.json}, original registered hypotheses, symbols, equations E1/E2 and code-to-equation steps.',
              r'\item \texttt{src/maxwell\_sst\_falsifier/geometry.py}, exact inherited geometric definitions; \texttt{native\_ext/fallback.py} and \texttt{cpp/native.cpp}, reference/native kernels.',
              r'\item \texttt{provenance/A011\_DATASET\_ADMISSION.json} and carrier decision ledger; exact E010 parser code pins and raw/geometry source hashes.',
              r'\item \texttt{preregistration/FROZEN\_PROTOCOL.json} and \texttt{FRAMEWORK\_SOURCE\_PIN.json}: byte-exact geometry protocol and qualified v1.0.10 source.',
              r'\item Current \texttt{GATE\_LEDGER.json}, \texttt{REPORT\_DATA.json},\\\texttt{SCIENCE\_EVIDENCE\_MANIFEST.json} and final \texttt{OUTPUT\_MANIFEST.json}.', r'\end{enumerate}', r'\end{document}']
    (report/'FALSIFIER_REPORT.tex').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    assert_report(report/'FALSIFIER_REPORT.tex', require_complete=True)
    assert_science_contract(DEST/'science_contract.json')
    assert_source_contract(DEST/'source_contract.json')
    shutil.copy2(DEST/'run_tests_v040.py', DEST/'run_tests.py')
    (DEST/'run_all.cmd').write_text('@echo off\nsetlocal\ncd /d "%~dp0"\nset "OMP_NUM_THREADS=1"\nset "OPENBLAS_NUM_THREADS=1"\nset "MKL_NUM_THREADS=1"\nset "PYTHONDONTWRITEBYTECODE=1"\npy -3.14 -B run_tests.py || exit /b 1\nif /i "%~1"=="SELFTEST" exit /b 0\nif not "%~1"=="" if /i not "%~1"=="BASIC" (echo Only BASIC or SELFTEST is authorized for this version. & exit /b 2)\npy -3.14 -B run_reported.py\nexit /b %ERRORLEVEL%\n', encoding='utf-8')
    (DEST/'README.md').write_text('# A011 v0.4.1 - scientific report/output binding restoration\n\nPackaging-only successor of immutable v0.4.0. No scientific equation, numerical threshold, source geometry, dataset seal or blind/reveal commitment was changed.\n\nRun `run_all.cmd` directly from this version folder. It runs tests, then only the registered three-source N=64/128 CPU geometry smoke, and renders the full scientific report through the existing qualified Framework v1.0.10 LaTeX report API. No alternate scientific PDF generator is used. `run_all.cmd SELFTEST` runs tests only. Other campaigns are refused.\n\nOutput prefix: `A011_Maxwell_SST_Kinetic_Falsifier`; current output: `./A011_Maxwell_SST_Kinetic_Falsifier_v0.4.1_outputs/`. Each rerun retains its predecessor directory under the original run ID. Scientific PDFs and ZIPs are published in `../` with immutable run IDs and SHA-256 sidecars. `LATEST_RUN.json` is a replaceable pointer; `PUBLICATIONS.jsonl` is append-only.\n\nThe report binds the unchanged science contract, frozen geometry protocol, exact source manifests, actual gate ledger, measured tables and diagnostic graphs. The G5 parity PASS remains diagnostic; physical claims stay unresolved. No full physical blind/reveal run is claimed.\n\nRequires the existing local workbench datasets/framework, CPython 3.14 + numpy/pytest/matplotlib, the inherited cp314 native binary, and pdflatex. Matplotlib is used only for scientific diagnostic plots and is available in the tested environment. The framework compiler is used for PDF generation. See `provenance/PARENT_V040_*` for unchanged predecessor protocol/source records.\n', encoding='utf-8')
    print('Configured full scientific template and standalone run_all.cmd; freeze after adapter tests are finalized.')


if __name__ == '__main__':
    main()
