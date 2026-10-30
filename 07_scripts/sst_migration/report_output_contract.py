"""Bind a migrated adapter to existing qualified framework reporting/packaging.

All scientific TeX contract/results generation, PDF compilation, run reservation,
locking and ZIP creation are provided by sst_falsifier. This module supplies the
adapter's data tables/plot and the requested underscore output naming policy.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys


def bind_results(root, out, summary, run_id, adapter):
    """Provide actual adapter artifacts at the framework's canonical input names."""
    from sst_falsifier.source_registry import resolve_source_contract
    from sst_falsifier.util import write_json
    raw = out / 'measurement'
    for name in ['GATE_LEDGER.json', 'GEOMETRY_RESULTS.json', 'PARITY_RESULTS.json', 'SELECTED_SEEDS.json']:
        shutil.copy2(raw / name, out / name)
    env = adapter.read(raw / 'ENVIRONMENT.json')
    write_json(out / 'ENVIRONMENT_PUBLIC.json', env)
    backend = {'schema': 'SST-BACKEND-MANIFEST-2', 'python': env['python'], 'numpy': env['numpy'],
               'actual_backend': env['native_backend'], 'native_binary_sha256': env['native_pin']['binary_sha256'],
               'native_cpp_sha256': env['native_pin']['cpp_sha256'], 'native_rebuilt': False,
               'authority': 'GEOMETRY_KERNEL_ONLY', 'physical_qualification': 'UNRESOLVED', 'gpu_used': False}
    write_json(out / 'BACKEND_MANIFEST.json', backend)
    sources = resolve_source_contract(root / 'source_contract.json', root=adapter.WORKBENCH)
    write_json(out / 'SOURCE_MANIFEST.json', sources)
    fixed = dict(summary, run_id=run_id, measurement_run_id=summary['run_id'], version='v0.4.1')
    write_json(out / 'RUN_SUMMARY.json', fixed)
    axes = {k: fixed[k] for k in ['migration_gate', 'execution_gate', 'scientific_gate', 'scientific_status_promoted']}
    write_json(out / 'GATE_AXES.json', axes)
    ledger = adapter.read(out / 'GATE_LEDGER.json')
    report_data = {'run_id': run_id, 'science_contract_sha256': adapter.digest(root / 'science_contract.json'),
                   'gates': ledger['records'], 'gate_axes': axes, 'results': adapter.read(out / 'GEOMETRY_RESULTS.json'),
                   'parity': adapter.read(out / 'PARITY_RESULTS.json'), 'missing_evidence': fixed['missing_scientific_evidence']}
    write_json(out / 'REPORT_DATA.json', report_data)
    plot_data = [{'topology_id': row['seed']['topology_id'], 'carrier_id': row['seed']['carrier_id'],
                  'N': [m['resampled_points'] for m in row['metrics_by_resolution']],
                  'length_native': [m['length_units'] for m in row['metrics_by_resolution']],
                  'writhe': [m['writhe_midpoint'] for m in row['metrics_by_resolution']]} for row in report_data['results']]
    write_json(out / 'PLOT_DATA.json', plot_data)
    return report_data


def write_adapter_tables(out, data):
    from sst_falsifier.report import latex_escape as esc, latex_breakable as wrap
    lines = [r'\subsection*{Separate migration, execution and scientific axes}',
             r'\begin{longtable}{p{0.25\linewidth}p{0.68\linewidth}}\toprule Axis & Actual status\\\midrule']
    for key, val in data['gate_axes'].items():
        lines.append(wrap(key) + ' & ' + wrap(val) + r' \\')
    lines += [r'\bottomrule\end{longtable}', r'\subsection*{Measured geometry and resolution sensitivity}',
              r'\begin{longtable}{p{0.15\linewidth}rrrr}\toprule Topology & N & Native length & Mean curvature & Midpoint writhe\\\midrule']
    for row in data['results']:
        for m in row['metrics_by_resolution']:
            lines.append(' & '.join([esc(row['seed']['topology_id']), str(m['resampled_points']), f"{m['length_units']:.10g}", f"{m['curvature_mean']:.10g}", f"{m['writhe_midpoint']:.10g}"]) + r' \\')
    lines += [r'\bottomrule\end{longtable}', r'Two registered levels expose sensitivity; they do not establish convergence or physical calibration.',
              r'\begin{figure}[htbp]\centering\includegraphics[width=\linewidth]{figures/geometry_sensitivity.pdf}\caption{Actual N=64 and N=128 measurements from PLOT\_DATA.json. Native lengths have no calibrated SI scale; writhe is dimensionless. No fitted trend or continuum extrapolation.}\end{figure}',
              r'\subsection*{Actual native/reference comparisons}',
              r'\begin{longtable}{p{0.15\linewidth}rrrr}\toprule Carrier topology & N & Velocity max abs & Writhe abs & Distance abs\\\midrule']
    lookup = {r['seed']['carrier_id']: r['seed']['topology_id'] for r in data['results']}
    for row in data['parity']:
        lines.append(' & '.join([esc(lookup[row['carrier_id']]), str(row['resolution']), f"{row['velocity_max_abs_delta']:.5g}", f"{row['writhe_abs_delta']:.5g}", f"{row['distance_abs_delta']:.5g}"]) + r' \\')
    lines += [r'\bottomrule\end{longtable}', r'\subsection*{Exact gate execution and claim authority}',
              r'\begin{longtable}{p{0.08\linewidth}p{0.28\linewidth}p{0.34\linewidth}p{0.19\linewidth}}\toprule Gate & Execution & Qualification & Allows dependent claim\\\midrule']
    for gate in data['gates']:
        lines.append(' & '.join(wrap(gate[k]) for k in ['gate_id', 'execution_status', 'qualification', 'allows_dependent_claim']) + r' \\')
    lines += [r'\bottomrule\end{longtable}', r'\subsection*{Missing scientific evidence}', r'\begin{itemize}']
    lines += [r'\item ' + esc(item) for item in data['missing_evidence']]
    lines += [r'\end{itemize}']
    (out / 'report/AUTO_ADAPTER_RESULTS.tex').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def plot_measurements(out, data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plots = out / 'report/figures'
    plots.mkdir(parents=True)
    figure, axes = plt.subplots(1, 2, figsize=(9, 3.0), constrained_layout=True)
    for row in data:
        label = row['topology_id']
        axes[0].plot(row['N'], row['length_native'], marker='o', label=label)
        axes[1].plot(row['N'], row['writhe'], marker='o', label=label)
    axes[0].set(xlabel='Resampled polygon points N', ylabel='Length [native coordinate unit]', title='Registered length sensitivity')
    axes[1].set(xlabel='Resampled polygon points N', ylabel='Midpoint writhe [1]', title='Registered writhe sensitivity')
    for ax in axes:
        ax.set_xticks([64, 128])
        ax.grid(alpha=.2)
        ax.legend(title='Topology', fontsize=8)
    figure.savefig(plots / 'geometry_sensitivity.pdf')
    plt.close(figure)


def run(root):
    sys.path.insert(0, str(root / 'src'))
    from maxwell_sst_falsifier import framework_v110 as adapter
    adapter.qualified_framework(root)
    adapter.verify_protocol(root)
    pin = adapter.read(root / 'REPORT_OUTPUT_CONTRACT.json')
    if adapter.digest(Path(__file__)) != pin['binding_sha256']:
        raise adapter.AdmissionError('Shared report/output binding changed')
    from sst_falsifier.output_policy import instance_lock, reserve_blind_output
    from sst_falsifier.report import assert_report, write_auto_science_tex, write_auto_results_tex, publish_instance_report
    from sst_falsifier.outputs import make_science_evidence_manifest, make_output_manifest, deterministic_zip, verify_output_manifest, verify_science_evidence_manifest
    from sst_falsifier.util import write_json
    prefix, version = pin['output_prefix'], adapter.read(root / 'project.json')['version']
    out = root / f'{prefix}_{version}_outputs'
    if out.resolve().parent != root.resolve():
        raise ValueError('Output root must remain directly inside this falsifier version')
    cfg = {'project': {'name': prefix, 'version': version}}
    with instance_lock(root):
        rid, previous = reserve_blind_output(root, out, cfg, 'GEOMETRY_SMOKE')
        try:
            summary = adapter.run(root, out / 'measurement')
            data = bind_results(root, out, summary, rid, adapter)
            report = out / 'report'
            report.mkdir()
            source_template = root / 'report/FALSIFIER_REPORT.tex'
            assert_report(source_template, require_complete=True)
            shutil.copy2(source_template, report / 'FALSIFIER_REPORT.tex')
            write_auto_science_tex(root, report / 'AUTO_SCIENCE_CONTRACT.tex')
            # Exact machine evidence is sealed before any report or PDF generation.
            make_science_evidence_manifest(out, out / 'SCIENCE_EVIDENCE_MANIFEST.json')
            write_auto_results_tex(root, out, report / 'AUTO_RESULTS.tex')
            write_adapter_tables(out, data)
            plot_measurements(out, adapter.read(out / 'PLOT_DATA.json'))
            pdf = root.parent / f'{prefix}_{version}__{rid}_FALSIFIER_REPORT.pdf'
            rendered = publish_instance_report(root, report / 'FALSIFIER_REPORT.tex', destination=pdf, strict=True, engine='pdflatex')
            shutil.copy2(pdf, report / 'FALSIFIER_REPORT.pdf')
            write_json(out / 'REPORT_RENDER_BLIND.json', rendered)
            okay, detail = verify_science_evidence_manifest(out, out / 'SCIENCE_EVIDENCE_MANIFEST.json')
            if not okay:
                raise RuntimeError(str(detail))
            make_output_manifest(out, out / 'OUTPUT_MANIFEST.json')
            okay, detail = verify_output_manifest(out, out / 'OUTPUT_MANIFEST.json')
            if not okay:
                raise RuntimeError(str(detail))
            archive = root.parent / f'{prefix}_{version}_outputs__{rid}.zip'
            packed = deterministic_zip(out, archive)
            with archive.with_suffix('.zip.sha256').open('x', encoding='ascii') as stream:
                stream.write(packed['sha256'] + '  ' + archive.name + '\n')
            record = {'schema': 'SST-REPORT-OUTPUT-PUBLICATION-1', 'run_id': rid, 'version': version, 'output_prefix': prefix,
                      'output_root': str(out), 'archived_previous': str(previous) if previous else None,
                      'report_pdf': str(pdf), 'report_sha256': adapter.digest(pdf), 'archive': packed,
                      'gate_axes': data['gate_axes'], 'report_contract': 'PASS', 'packaging_contract': 'PASS',
                      'ledger_sha256': adapter.digest(out/'GATE_LEDGER.json'), 'published_utc': datetime.now(timezone.utc).isoformat()}
            journal = root / 'PUBLICATIONS.jsonl'
            with journal.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record) + '\n')
            from preflight import atomic
            atomic(root / 'LATEST_RUN.json', record)
            return record
        except BaseException as error:
            write_json(out / 'REPORT_OUTPUT_ERROR.json', {'run_id': rid, 'error': type(error).__name__+': '+str(error), 'report_contract': 'FAIL', 'scientific_status_promoted': False})
            raise
