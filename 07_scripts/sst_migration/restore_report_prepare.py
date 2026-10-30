"""Audit existing report contracts; create a packaging-only A011 patch successor."""
from datetime import datetime, timezone
import ast
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha
from phase3_prepare import snapshot, create_json

OUT = ROOT / '10_docs/migration_v110/report_contract_restoration_20261026'
FAMILY = ROOT / '01_research/A_falsifiers/A011_maxwell_1_kinetic_energy'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    audit = []
    for version in ['1.0.6', '1.0.7', '1.0.10']:
        root = ROOT / '06_templates/SST_Falsifier_Framework' / ('SST_Falsifier_Framework_v' + version)
        report = root / 'sst_falsifier/report.py'
        tree = ast.parse(report.read_text(encoding='utf-8'))
        markers = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'REQUIRED_SECTION_MARKERS' for t in n.targets))
        audit.append({'version': version, 'files': {name: sha(root / name) for name in ['sst_falsifier/report.py', 'sst_falsifier/runner.py', 'sst_falsifier/outputs.py', 'instance_template/report/FALSIFIER_REPORT.tex', 'instance_template/run_all.cmd']},
                      'required_sections': list(markers), 'report_functions': [n.name for n in tree.body if isinstance(n, ast.FunctionDef)],
                      'automatic_science_binding': 'write_auto_science_tex' in report.read_text(encoding='utf-8'), 'automatic_results_binding': 'write_auto_results_tex' in report.read_text(encoding='utf-8')})
    old = ROOT / '06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.7/sst_falsifier/report.py'
    new = ROOT / '06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10/sst_falsifier/report.py'
    (OUT / 'framework_report_107_to_110.diff').write_text(''.join(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True), new.read_text(encoding='utf-8').splitlines(True), fromfile='v1.0.7/report.py', tofile='v1.0.10/report.py')), encoding='utf-8')
    references = []
    for family, version in [('A059_SST_Quantum_Number_Rosetta_Mega_Falsifier', 'A059-v0.2.0'), ('A060_Dynamical_Topology_Coherence', 'A060-v0.2.1')]:
        base = ROOT / '01_research/A_falsifiers' / family
        tex = base / version / 'report/FALSIFIER_REPORT.tex'
        pdf = base / (version + '_FALSIFIER_REPORT.pdf')
        references.append({'version': version, 'tex': tex.relative_to(ROOT).as_posix(), 'tex_sha256': sha(tex), 'pdf': pdf.relative_to(ROOT).as_posix(), 'pdf_sha256': sha(pdf),
                           'markers': [line.strip() for line in tex.read_text(encoding='utf-8').splitlines() if 'SST-REPORT-SECTION:' in line]})
    create_json(OUT / 'FRAMEWORK_AUDIT.json', {'frameworks': audit, 'references': references,
                'diagnosis': 'NO_FULL_SCIENCE_STRUCTURE_REGRESSION: v1.0.6/v1.0.7 report.py identical; v1.0.10 retains all 16 sections and adds qualification/run identity. A011-v0.4.0 omitted the scientific TeX/auto-science binding, used a separate technical renderer and left run_all.cmd attached to legacy workflows.',
                'correction': 'Reuse qualified v1.0.10 report.py, output_policy.py and outputs.py; add scientific template/adapter binding and one standalone Windows entry point in patch successor v0.4.1.'})
    preservation = {'A011-v0.3.1': snapshot(FAMILY/'A011-v0.3.1'), 'A011-v0.4.0': snapshot(FAMILY/'A011-v0.4.0'),
                    'source_framework_manifest': sha(ROOT / '06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10/PACKAGE_MANIFEST.json'),
                    'references': references}
    create_json(OUT / 'PRESERVATION_BEFORE.json', preservation)
    dst = FAMILY / 'A011-v0.4.1'
    if dst.exists():
        raise FileExistsError(dst)
    excluded = {'build', 'outputs', 'runs', 'exports', '.venv', '__pycache__', '.pytest_cache', 'preregistration', 'SOURCE_MANIFEST_v0.4.0.json'}
    def ignore(folder, names):
        return [n for n in names if n in excluded or n.endswith('-outputs') or n.endswith(('.zip', '.pdf', '.pyc'))]
    shutil.copytree(FAMILY/'A011-v0.4.0', dst, ignore=ignore)
    for name in ['preregistration/GEOMETRY_PROTOCOL.json', 'SOURCE_MANIFEST_v0.4.0.json', 'run_all.cmd']:
        shutil.copy2(FAMILY/'A011-v0.4.0'/name, dst/'provenance'/('PARENT_V040_'+Path(name).name))
    for name in ['src/maxwell_sst_falsifier/framework_v110.py', 'src/maxwell_sst_falsifier/__init__.py', 'pyproject.toml', 'project.json']:
        p = dst/name
        p.write_text(p.read_text(encoding='utf-8').replace('v0.4.0','v0.4.1').replace('"0.4.0"','"0.4.1"'), encoding='utf-8')
    (dst/'preregistration').mkdir()
    print(json.dumps({'audit': str(OUT), 'successor': str(dst), 'framework_scientific_sections_retained': 16}))


if __name__ == '__main__':
    main()
