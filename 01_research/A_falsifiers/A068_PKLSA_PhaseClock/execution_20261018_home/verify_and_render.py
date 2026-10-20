"""Audit immutable run artifacts and render presentation-only report copies."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import textwrap
import zipfile

HERE = Path(__file__).resolve().parent
FAMILY = HERE.parent
ROOT = FAMILY / 'A068-v0.3.0'
FW = FAMILY.parents[2] / '06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.8'
sys.path.insert(0, str(FW))
from sst_falsifier.protocol import assert_frozen
from sst_falsifier.runner import reveal_eligibility
from sst_falsifier.config import load_instance_config

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

frozen = assert_frozen(ROOT, ROOT/'preregistration/FROZEN_PROTOCOL.json')
cfg = load_instance_config(ROOT)
result = {'framework_version': '1.0.8', 'protocol_hash': frozen['bundle_sha256'], 'runs': {}}
artifacts = []
for mode in ('BASIC', 'FULL', 'CERTIFY'):
    summary = read(HERE / f'{mode}.run_summary.json')
    run_id = summary['run_id']
    out = ROOT / 'PKLSA_PhaseClock_v0.3.0-outputs'
    if read(out/'RUN_ID.json')['run_id'] != run_id:
        out = out.with_name(out.name+'__'+run_id)
    ledger = read(out/'GATE_LEDGER.json')
    backend = read(out/'BACKEND_MANIFEST.json')
    archive = FAMILY / f'PKLSA_PhaseClock_v0.3.0-outputs__{run_id}_BLIND.zip'
    manifest = read(out/'OUTPUT_MANIFEST.json')
    for item in manifest['files']:
        assert digest(out/item['relpath']) == item['sha256'], (mode, item['relpath'])
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            parts = {p.lower() for p in Path(name).parts}
            assert not parts & {'private','revealed','reveal_private'}, name
            assert Path(name).name not in {'OPAQUE_ID_KEY.bin','REVEAL_NONCE.bin','reveal.json'}
            assert hashlib.sha256(z.read(name)).hexdigest() == digest(out/name), name
    decision = reveal_eligibility(ROOT, cfg, out, frozen)
    assert decision['eligible'] is False
    result['runs'][mode] = {
        'run_id': run_id, 'output': str(out),
        'gates': {r['gate_id']:r['status'] for r in ledger['records']},
        'reveal_eligibility': decision, 'backend': backend,
        'output_manifest_verified': True, 'archive_content_verified': True,
        'private_material_absent_from_archive': True,
    }
    artifacts.append(archive)
    official_pdf = FAMILY / f'A068-v0.3.0__{run_id}_BLIND_FALSIFIER_REPORT.pdf'
    artifacts.append(official_pdf)
    # Copy rendered report inputs, never edit frozen or sealed source artifacts.
    presentation = HERE / f'{mode}_readable'
    presentation.mkdir(exist_ok=True)
    for source in (out/'report').glob('*.tex'):
        shutil.copy2(source, presentation/source.name)
    auto_path = presentation/'AUTO_RESULTS.tex'
    auto = auto_path.read_text(encoding='utf-8')
    start = auto.index(r'\begin{longtable}{llll}')
    end = auto.index(r'\end{longtable}', start) + len(r'\end{longtable}')
    table = auto[start:end].replace(
        r'\begin{longtable}{llll}',
        r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}'
        r'\begin{longtable}{p{0.045\linewidth}p{0.19\linewidth}p{0.32\linewidth}p{0.34\linewidth}}'
    ).replace(r'NOT\_RUN\_PREREQUISITE', r'NOT\_\allowbreak RUN\_\allowbreak PREREQUISITE')
    table += r'\endgroup'
    auto = auto[:start] + table + auto[end:]
    chunks = re.split(r'(\\begin\{verbatim\}.*?\\end\{verbatim\})', auto, flags=re.S)
    for i, chunk in enumerate(chunks):
        if chunk.startswith(r'\begin{verbatim}'):
            body = chunk[len(r'\begin{verbatim}'): -len(r'\end{verbatim}')]
            wrapped = '\n'.join('\n'.join(textwrap.wrap(line, width=88, replace_whitespace=False,
                                drop_whitespace=False, break_on_hyphens=False)) if line else ''
                                for line in body.splitlines())
            chunks[i] = r'\begingroup\footnotesize\begin{verbatim}'+'\n'+wrapped+'\n'+r'\end{verbatim}\endgroup'
        else:
            chunks[i] = re.sub(r'(?<![A-Za-z0-9])[0-9a-f]{64}(?![A-Za-z0-9])',
                       lambda m: r'\allowbreak '.join(m[0][j:j+8] for j in range(0,64,8)), chunk)
    auto = ''.join(chunks)
    auto_path.write_text(auto, encoding='utf-8')
    for _ in range(2):
        cp = subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','FALSIFIER_REPORT.tex'],
                            cwd=presentation, capture_output=True, text=True)
        (presentation/'compile_console.log').write_text(cp.stdout+cp.stderr, encoding='utf-8')
        assert cp.returncode == 0, mode
    readable = HERE / f'A068_v0.3.0_{mode}_READABLE.pdf'
    shutil.copy2(presentation/'FALSIFIER_REPORT.pdf', readable)
    artifacts.append(readable)
    result['runs'][mode]['readable_pdf'] = str(readable)
    print(mode, result['runs'][mode]['gates'], flush=True)

# Old canonical output was renamed by official v1.0.8 archival, not overwritten.
prior_id = '20261017T234952991721Z-9a72fd48'
missing, changed, relocated = [], [], 0
for item in read(HERE/'prior_files_sha256.json'):
    p = FAMILY/item['path']
    if item['path'].replace('\\','/').startswith('A068-v0.3.0/PKLSA_PhaseClock_v0.3.0-outputs/'):
        p = FAMILY/item['path'].replace('PKLSA_PhaseClock_v0.3.0-outputs',
                                       'PKLSA_PhaseClock_v0.3.0-outputs__'+prior_id, 1)
        relocated += 1
    if not p.is_file(): missing.append(item['path'])
    elif digest(p) != item['sha256']: changed.append(item['path'])
result['preservation'] = {'prior_files':len(read(HERE/'prior_files_sha256.json')),
                          'archived_files':relocated,'missing':missing,'changed':changed}
assert not missing and not changed, result['preservation']
(HERE/'ARTIFACTS_SHA256.txt').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in artifacts), encoding='ascii')
(HERE/'VERIFICATION_AND_GATES.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('All prior files preserved; manifests, archives and reveal withholding verified.', flush=True)
