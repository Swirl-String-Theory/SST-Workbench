from __future__ import annotations
import hashlib, json, secrets
from pathlib import Path
import numpy as np
from .io import save_xyz, load_xyz


def geometry_sha256(points):
    """SHA-256 of canonical little-endian float64 Nx3 geometry bytes."""
    p=np.asarray(points,dtype='<f8')
    return hashlib.sha256(p.tobytes(order='C')).hexdigest()


def _canonical_json_bytes(obj):
    """Human-readable JSON with explicit LF newlines, independent of host OS."""
    return json.dumps(obj,indent=2,ensure_ascii=False).encode('utf-8')


def make_blind_campaign(candidates, outdir, seed=None):
    """Write anonymous geometry files + private reveal manifest.

    candidates: iterable of (label, points, metadata)

    The reveal commitment is the SHA-256 of the exact bytes written to
    private/reveal.json. JSON files are written as UTF-8 bytes so Windows
    newline translation cannot change the committed payload.
    """
    out=Path(outdir); pub=out/'public'; priv=out/'private'
    pub.mkdir(parents=True,exist_ok=True); priv.mkdir(parents=True,exist_ok=True)
    items=list(candidates)
    if seed is None:
        seed = secrets.randbits(128)
    rng=np.random.default_rng(seed); order=rng.permutation(len(items))
    public=[]; reveal=[]
    for anon_i,src_i in enumerate(order):
        label,pts,meta=items[src_i]
        anon=f'C{anon_i+1:04d}'
        fn=f'{anon}.xyz'; save_xyz(pub/fn,pts)
        h=geometry_sha256(pts)
        public.append({'candidate_id':anon,'file':fn,'sha256':h})
        reveal.append({'candidate_id':anon,'source_label':label,'sha256':h,'metadata':meta})

    manifest_bytes=_canonical_json_bytes(public)
    reveal_bytes=_canonical_json_bytes(reveal)
    (pub/'manifest.json').write_bytes(manifest_bytes)
    (priv/'reveal.json').write_bytes(reveal_bytes)
    (priv/'blind_seed.txt').write_bytes((str(seed)+'\n').encode('ascii'))
    commitment=hashlib.sha256(reveal_bytes).hexdigest()
    (pub/'reveal_commitment.sha256').write_bytes((commitment+'\n').encode('ascii'))
    return commitment


def verify_blind_campaign(outdir, require_private=False):
    """Verify public geometry hashes and, when present, the private reveal.

    Geometry hashes are semantic hashes of parsed float64 coordinates rather
    than hashes of platform-dependent text-file bytes. The reveal commitment,
    in contrast, is intentionally a byte-for-byte hash of reveal.json.
    """
    out=Path(outdir); pub=out/'public'; priv=out/'private'
    manifest_path=pub/'manifest.json'
    commitment_path=pub/'reveal_commitment.sha256'
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest=json.loads(manifest_path.read_bytes().decode('utf-8'))

    geom=[]; geom_ok=True; seen=set()
    for item in manifest:
        cid=item['candidate_id']; fn=item['file']; expected=item['sha256']
        duplicate=cid in seen; seen.add(cid)
        path=pub/fn
        if not path.exists():
            actual=None; ok=False
        else:
            actual=geometry_sha256(load_xyz(path)); ok=(actual==expected and not duplicate)
        geom_ok = geom_ok and ok
        geom.append({'candidate_id':cid,'file':fn,'expected_sha256':expected,
                     'actual_sha256':actual,'duplicate_id':duplicate,'ok':ok})

    reveal_path=priv/'reveal.json'
    reveal_present=reveal_path.exists()
    commitment_present=commitment_path.exists()
    reveal_commitment_ok=None
    manifest_reveal_ok=None
    reveal_count=None
    commitment_expected=None
    commitment_actual=None

    if reveal_present:
        reveal_bytes=reveal_path.read_bytes()
        reveal=json.loads(reveal_bytes.decode('utf-8'))
        reveal_count=len(reveal)
        commitment_actual=hashlib.sha256(reveal_bytes).hexdigest()
        if commitment_present:
            commitment_expected=commitment_path.read_text(encoding='ascii').strip()
            reveal_commitment_ok=(commitment_actual==commitment_expected)
        rmap={x['candidate_id']:x for x in reveal}
        manifest_reveal_ok=(
            len(rmap)==len(reveal)==len(manifest) and
            all(x['candidate_id'] in rmap and x['sha256']==rmap[x['candidate_id']]['sha256']
                for x in manifest)
        )
    elif require_private:
        manifest_reveal_ok=False
        reveal_commitment_ok=False

    public_ok=geom_ok and len(seen)==len(manifest)
    private_ok=(not require_private and not reveal_present) or (
        reveal_present and bool(reveal_commitment_ok) and bool(manifest_reveal_ok)
    )
    return {
        'format':'SST-KNOT-GEOMETRY-CAMPAIGN-VERIFY-1.0',
        'candidate_count':len(manifest),
        'public_geometry_hashes_ok':public_ok,
        'reveal_present':reveal_present,
        'reveal_count':reveal_count,
        'manifest_reveal_hashes_ok':manifest_reveal_ok,
        'reveal_commitment_expected':commitment_expected,
        'reveal_commitment_actual':commitment_actual,
        'reveal_commitment_ok':reveal_commitment_ok,
        'pass':bool(public_ok and private_ok),
        'candidates':geom,
    }
