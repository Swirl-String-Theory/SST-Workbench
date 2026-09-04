from __future__ import annotations

from pathlib import Path
import csv, hashlib, json, struct
import numpy as np

from .geometry import normalize_components, split_components


def atlas_rows(atlas_root):
    root = Path(atlas_root)
    p = root / 'manifests' / 'CANDIDATES_FULL.csv'
    with p.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def atlas_summary(atlas_root):
    rows = atlas_rows(atlas_root)
    fams = sorted({r['family'] for r in rows})
    return {
        'candidate_count': len(rows),
        'family_count': len(fams),
        'candidates_per_family': sorted({sum(1 for r in rows if r['family']==f) for f in fams}),
    }


def _bundle_path(root: Path, row):
    family = row['family'].replace('.', 'p')
    return root / 'families' / f"{int(row['family_index']):02d}_{family}.npz"


def load_candidate(atlas_root, row_or_id):
    root = Path(atlas_root)
    if isinstance(row_or_id, str):
        rows = atlas_rows(root)
        row = next((r for r in rows if r['candidate_id'] == row_or_id), None)
        if row is None:
            raise KeyError(row_or_id)
    else:
        row = dict(row_or_id)
    z = np.load(_bundle_path(root, row), allow_pickle=False)
    pts = np.asarray(z['points'][int(row['variant_index'])], dtype=float)
    return row, [np.asarray(c, float) for c in pts]


def normalized_candidate(atlas_root, row_or_id, n_total):
    row, comps = load_candidate(atlas_root, row_or_id)
    X, offs = normalize_components(comps, int(n_total))
    return row, X, offs


def next_index_from_offsets(offsets, n):
    nxt = np.full(int(n), -1, dtype=np.int32)
    for ci in range(len(offsets)-1):
        a, b = int(offsets[ci]), int(offsets[ci+1])
        if b-a < 3:
            continue
        nxt[a:b-1] = np.arange(a+1, b, dtype=np.int32)
        nxt[b-1] = a
    return nxt


def write_xyz(path, points, offsets, header=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    comps = split_components(np.asarray(points, float), np.asarray(offsets, dtype=np.int64))
    with path.open('w', encoding='utf-8', newline='\n') as f:
        if header:
            f.write('# ' + str(header).replace('\n', ' ') + '\n')
        for ci, C in enumerate(comps):
            if ci:
                f.write('\ncomponent\n')
            for x, y, z in C:
                f.write(f'{x:.17g} {y:.17g} {z:.17g}\n')
    return path


def opaque_token(secret_hex: str, candidate_id: str, prefix='G'):
    h = hashlib.sha256((secret_hex + '|' + candidate_id).encode('utf-8')).hexdigest()[:16]
    return f'{prefix}_{h}'


# Raw binary protocol for gpu/sycl_funnel.cpp.
# Header: magic[8], uint32 version, uint32 K, uint32 N, double core, double cfl.
# Each candidate: id[24], points[N,3] float64, next[N] int32.
GPU_MAGIC = b'SSTGPU40'
GPU_VERSION = 1
GPU_ID_BYTES = 24


def write_gpu_batch(path, records, n_total, core, cfl):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    K = len(records); N = int(n_total)
    with path.open('wb') as f:
        f.write(struct.pack('<8sIIIdd', GPU_MAGIC, GPU_VERSION, K, N, float(core), float(cfl)))
        for rec in records:
            oid = rec['opaque_id'].encode('ascii')
            if len(oid) >= GPU_ID_BYTES:
                raise ValueError('opaque id too long')
            f.write(oid + b'\0' * (GPU_ID_BYTES-len(oid)))
            X = np.asarray(rec['points'], dtype='<f8')
            offs = np.asarray(rec['offsets'], dtype=np.int64)
            if X.shape != (N,3):
                raise ValueError(f'expected {(N,3)}, got {X.shape}')
            nxt = next_index_from_offsets(offs, N).astype('<i4')
            f.write(X.tobytes(order='C'))
            f.write(nxt.tobytes(order='C'))
    return path


def read_gpu_batch(path):
    path = Path(path)
    out=[]
    with path.open('rb') as f:
        magic, ver, K, N, core, cfl = struct.unpack('<8sIIIdd', f.read(struct.calcsize('<8sIIIdd')))
        if magic != GPU_MAGIC or ver != GPU_VERSION:
            raise ValueError('GPU batch format mismatch')
        for _ in range(K):
            oid=f.read(GPU_ID_BYTES).split(b'\0',1)[0].decode('ascii')
            X=np.frombuffer(f.read(N*3*8),dtype='<f8').reshape(N,3).copy()
            nxt=np.frombuffer(f.read(N*4),dtype='<i4').copy()
            out.append({'opaque_id':oid,'points':X,'next':nxt})
    return {'K':K,'N':N,'core':core,'cfl':cfl,'records':out}
