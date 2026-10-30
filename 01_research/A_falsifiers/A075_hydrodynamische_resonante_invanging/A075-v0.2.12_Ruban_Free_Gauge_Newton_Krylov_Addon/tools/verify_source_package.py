"""Read-only SOURCE_FILE_MANIFEST.json verification for v0.2.12."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'SOURCE_FILE_MANIFEST.json').read_text())
if manifest.get('schema')!='A075-v0.2.12-SOURCE-MANIFEST-1':
    raise SystemExit('SOURCE_MANIFEST_SCHEMA_MISMATCH')
entries=manifest.get('files',[])
if len(entries)!=manifest.get('file_count') or not entries:
    raise SystemExit('SOURCE_MANIFEST_COUNT_MISMATCH')
for e in entries:
    path=(root/e['path']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise SystemExit('MISSING_OR_UNSAFE '+e['path'])
    if path.stat().st_size != e['size_bytes']:
        raise SystemExit('SOURCE_SIZE_MISMATCH '+e['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=e['sha256']:
        raise SystemExit('SHA_MISMATCH '+e['path'])
print('SOURCE_PACKAGE_VERIFIED',len(entries),'files')
