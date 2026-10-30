"""Create-only intake and source pinning; never alters a parent release."""
from pathlib import Path
import hashlib, json, shutil, sys

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
FAMILY = ROOT / '01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas'
BASE = FAMILY / 'E010-v0.3.1'
HISTORY = BASE / 'E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs'
RUBAN = FAMILY / 'E010_Ruban_Torus_Dynamics_Family_v0.3.6-fine-outputs'
TARGET = FAMILY / 'E010-v0.4.0'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(p, d):
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, indent=2, sort_keys=True); f.write('\n')

def main():
    if TARGET.exists():
        raise FileExistsError(TARGET)
    print('Verifying original v0.3.6 manifest...', flush=True)
    expected_manifest = json.loads((AUDIT/'DRIVE_PROVENANCE.json').read_text())['manifest_sha256']
    assert sha(RUBAN/'MANIFEST_SHA256.txt') == expected_manifest
    ruban = {}
    for line in (RUBAN/'MANIFEST_SHA256.txt').read_text().splitlines():
        expected, rel = line.split(maxsplit=1); rel = rel.lstrip('*')
        p = (RUBAN/rel).resolve()
        assert p.is_relative_to(RUBAN.resolve()) and rel not in ruban
        assert sha(p) == expected, rel
        ruban[rel] = expected
    assert len(ruban) == 10169
    ruban['MANIFEST_SHA256.txt'] = expected_manifest
    print('Pinning all historical output files and original carriers...', flush=True)
    history = {p.relative_to(HISTORY).as_posix(): sha(p) for p in sorted(HISTORY.rglob('*')) if p.is_file()}
    carriers = []
    raw = {}
    for topo in sorted((HISTORY/'atlas').iterdir()):
        for area in ['sources', 'generated']:
            for p in sorted((topo/area).rglob('CAR_*.json')):
                doc = json.loads(p.read_text()); c = doc['carrier']; src = Path(c['source_path'])
                assert src.is_relative_to(ROOT), src
                rel = src.relative_to(ROOT).as_posix()
                if rel not in raw:
                    raw[rel] = sha(src)
                assert raw[rel] == c['raw_sha256'], rel
                carriers.append({'document': p.relative_to(HISTORY).as_posix(), 'carrier': c,
                                 'geometry_sha256': doc['geometry_sha256']})
    assert len(carriers) == len({r['carrier']['carrier_id'] for r in carriers}) == 4497
    frozen_modules = ['__init__.py', 'models.py', 'io_geometry.py', 'fseries.py', 'gilbert.py', 'hashing.py']
    source_code = {'pklsa_builder/'+name: sha(BASE/'pklsa_builder'/name) for name in frozen_modules}
    contract = {'schema': 'PKLSA-COMBINED-INTAKE-1', 'version': 'v0.4.0',
                'baseline_version': 'v0.3.1', 'ruban_version': 'v0.3.6',
                'history_relative': HISTORY.relative_to(ROOT).as_posix(),
                'ruban_relative': RUBAN.relative_to(ROOT).as_posix(),
                'history': history, 'ruban': ruban, 'raw_sources': raw, 'parent_code': source_code,
                'expected': {'historical_carriers': 4497, 'historical_topologies': 2227,
                             'nominal': 3630, 'perturbed': 3630, 'records': 11757,
                             'ruban_components': 10164, 'pending_scenarios': 54450}}
    write(AUDIT/'SOURCE_INTAKE.json', contract)
    write(AUDIT/'CARRIERS.json', carriers)
    TARGET.mkdir()
    for name in ['pklsa_builder', 'sst_pklsa', 'configs', 'tests']:
        (TARGET/name).mkdir()
    for name in frozen_modules:
        shutil.copyfile(BASE/'pklsa_builder'/name, TARGET/'pklsa_builder'/name)
    for name in ['SOURCE_INTAKE.json', 'CARRIERS.json', 'DRIVE_PROVENANCE.json']:
        shutil.copyfile(AUDIT/name, TARGET/'configs'/name)
    shutil.copyfile(AUDIT/'DRIVE_MANIFEST_SHA256.txt', TARGET/'configs/DRIVE_MANIFEST_SHA256.txt')
    write(AUDIT/'PREPARE_RESULT.json', {'status':'PASS_SOURCE_INTAKE', 'history_files':len(history),
          'raw_files':len(raw), 'ruban_manifest_entries':len(ruban)-1, 'carriers':len(carriers),
          'source_contract_sha256':sha(AUDIT/'SOURCE_INTAKE.json')})
    print(json.dumps({'status':'PASS_SOURCE_INTAKE','history_files':len(history),'raw_files':len(raw),'target':str(TARGET)}))

if __name__ == '__main__': main()
