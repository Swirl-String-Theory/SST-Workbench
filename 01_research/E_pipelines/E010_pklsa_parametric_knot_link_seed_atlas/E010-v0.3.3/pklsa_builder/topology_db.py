from __future__ import annotations
from pathlib import Path
import json, re, zipfile, gzip
from .hashing import sha256_file

_KNOT_ROLFSEN_RE = re.compile(r'^(\d{1,2})[._](\d+)$', re.I)
_KNOT_HT_RE = re.compile(r'^K?(\d{1,2})([an])_?(\d+)$', re.I)
_LINK_RE = re.compile(r'^L(\d{1,2})([an])_?(\d+)(?:\{[^{}]+\})?$', re.I)

_KNOT_PRIMARY_FIELDS = (
    'name', 'knot_atlas', 'ht_name', 'knot_name', 'dt_name', 'classical_conway_name', 'rolfsen_name'
)
_LINK_PRIMARY_FIELDS = (
    'name_unoriented', 'knot_atlas', 'link_name', 'name'
)

_DATABASE_BUNDLE_CACHE = {}


def norm_header(s):
    s = str(s or '').strip().lower()
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    return s


def canonicalize_knot_label(v):
    s = str(v or '').strip().replace(' ', '')
    m = _KNOT_HT_RE.fullmatch(s)
    if m:
        return f"{int(m.group(1))}{m.group(2).lower()}_{int(m.group(3))}"
    m = _KNOT_ROLFSEN_RE.fullmatch(s)
    if m:
        return f"{int(m.group(1))}_{int(m.group(2))}"
    return None


def canonicalize_link_label(v):
    s = str(v or '').strip().replace(' ', '')
    m = _LINK_RE.fullmatch(s)
    if not m:
        return None
    return f"L{int(m.group(1))}{m.group(2).lower()}{int(m.group(3))}"


def _canonicalize(v, kind):
    return canonicalize_knot_label(v) if kind == 'knot' else canonicalize_link_label(v)


def _labelish(v, kind='knot'):
    return _canonicalize(v, kind) is not None


def _choose_header(sheet, max_rows=20):
    best = None
    for r in range(min(sheet.nrows, max_rows)):
        vals = [str(sheet.cell_value(r, c)).strip() for c in range(sheet.ncols)]
        nz = [x for x in vals if x]
        if not nz:
            continue
        score = len(set(nz)) + 3 * sum(
            any(k in norm_header(x) for k in ('knot', 'link', 'name', 'pd', 'gauss', 'braid', 'dt', 'dowker'))
            for x in nz
        )
        if best is None or score > best[0]:
            best = (score, r, vals)
    if best is None:
        raise ValueError('no header row')
    return best[1], best[2]


def _open_xls(path):
    try:
        import xlrd
    except Exception as e:
        raise RuntimeError('xlrd>=2.0.1 is required for KnotInfo/LinkInfo legacy .xls integration') from e
    p = Path(path)
    if p.suffix.lower() == '.zip':
        with zipfile.ZipFile(p) as z:
            names = [n for n in z.namelist() if n.lower().endswith('.xls') and not n.startswith('__MACOSX/')]
            if len(names) != 1:
                raise ValueError('expected one .xls in archive')
            data = z.read(names[0])
        return xlrd.open_workbook(file_contents=data), names[0]
    return xlrd.open_workbook(str(p), on_demand=True), p.name


def _preferred_candidates(row: dict, kind: str):
    """Return only topology labels from semantically named database fields.

    Legacy KnotInfo/LinkInfo workbooks contain many numeric ranks and floating values.
    Those must never become aliases merely because they look like ``1.0`` or ``2.0``.
    """
    fields = _KNOT_PRIMARY_FIELDS if kind == 'knot' else _LINK_PRIMARY_FIELDS
    out = []
    seen = set()
    for rank, field in enumerate(fields):
        if field not in row:
            continue
        raw = str(row[field]).strip()
        canonical = _canonicalize(raw, kind)
        if not canonical:
            continue
        key = (raw, canonical)
        if key in seen:
            continue
        seen.add(key)
        out.append({'priority': rank, 'field': field, 'raw': raw, 'canonical': canonical})
    return out


def _notation_label_candidates(row: dict, kind: str):
    # These fields can establish same-row alias relations, but never select a row from
    # arbitrary numeric cells. Keep the set deliberately explicit.
    names = set(_KNOT_PRIMARY_FIELDS if kind == 'knot' else _LINK_PRIMARY_FIELDS)
    for key in row:
        kl = key.lower()
        if any(token in kl for token in ('rolfsen', 'thistle', 'knot_atlas', 'ht_name', 'knot_name', 'link_name')):
            names.add(key)
    out = []
    for key in sorted(names):
        if key not in row:
            continue
        raw = str(row[key]).strip()
        canonical = _canonicalize(raw, kind)
        if canonical:
            out.append((key, raw, canonical))
    return out


def ingest_legacy_database(path, kind='knot'):
    if kind not in ('knot', 'link'):
        raise ValueError(f'unsupported topology database kind: {kind}')
    book, member = _open_xls(path)
    source = {'path': str(path), 'member': member, 'sha256': sha256_file(path), 'sheet_count': book.nsheets}
    records = []
    aliases = {}
    profiles = []
    for sname in book.sheet_names():
        sh = book.sheet_by_name(sname)
        if sh.nrows == 0 or sh.ncols == 0:
            continue
        hr, raw_headers = _choose_header(sh)
        headers = []
        seen = {}
        for i, h in enumerate(raw_headers):
            k = norm_header(h) or f'col_{i+1}'
            seen[k] = seen.get(k, 0) + 1
            if seen[k] > 1:
                k = f'{k}_{seen[k]}'
            headers.append(k)
        profiles.append({
            'sheet': sname, 'nrows': sh.nrows, 'ncols': sh.ncols,
            'header_row_1based': hr + 1, 'headers': headers,
        })
        for r in range(hr + 1, sh.nrows):
            vals = [sh.cell_value(r, c) for c in range(sh.ncols)]
            row = {headers[c]: vals[c] for c in range(len(headers)) if vals[c] not in ('', None)}
            if not row:
                continue
            candidates = _preferred_candidates(row, kind)
            if not candidates:
                continue
            primary_rec = min(candidates, key=lambda x: x['priority'])
            primary_raw = primary_rec['raw']
            primary = primary_rec['canonical']
            rec = {
                'kind': kind,
                'canonical_label': primary,
                'raw_primary_label': primary_raw,
                'primary_field': primary_rec['field'],
                'sheet': sname,
                'row_1based': r + 1,
                'notations': {},
                'notation_labels': {},
                'raw_fields': row,
            }
            for k, v in row.items():
                kl = k.lower()
                if 'pd' in kl and ('notation' in kl or kl == 'pd'):
                    rec['notations']['PD'] = v
                if 'gauss' in kl:
                    rec['notations']['Gauss'] = v
                if 'braid' in kl:
                    rec['notations']['Braid'] = v
                if 'dowker' in kl or re.search(r'(^|_)dt($|_)', kl):
                    rec['notations']['DT'] = v

            alias_values = {primary, primary_raw}
            for k, raw, canonical in _notation_label_candidates(row, kind):
                rec['notation_labels'][k] = raw
                alias_values.add(raw)
                alias_values.add(canonical)
            # Also retain all explicitly preferred valid label fields from this row.
            for c in candidates:
                alias_values.add(c['raw'])
                alias_values.add(c['canonical'])
            alias_values = {str(x) for x in alias_values if x}
            rec['aliases'] = sorted(alias_values)
            records.append(rec)
            for a in alias_values:
                aliases.setdefault(a, set()).add(primary)

    aliases_out = {a: sorted(v) for a, v in aliases.items()}
    return {'source': source, 'profiles': profiles, 'records': records, 'aliases': aliases_out}


def write_database_bundle(result, outdir, prefix):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    _DATABASE_BUNDLE_CACHE.pop((str(out.resolve()), prefix), None)
    with gzip.open(out / f'{prefix}_records.jsonl.gz', 'wt', encoding='utf-8') as f:
        for r in result['records']:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n')
    (out / f'{prefix}_aliases.json').write_text(
        json.dumps(result['aliases'], indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8'
    )
    (out / f'{prefix}_schema_profile.json').write_text(
        json.dumps({'source': result['source'], 'profiles': result['profiles'], 'record_count': len(result['records'])},
                   indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8'
    )


def _load_database_bundle(bundle_dir, prefix):
    out = Path(bundle_dir)
    key = (str(out.resolve()), prefix)
    cached = _DATABASE_BUNDLE_CACHE.get(key)
    if cached is not None:
        return cached
    alias_path = out / f'{prefix}_aliases.json'
    rec_path = out / f'{prefix}_records.jsonl.gz'
    if not alias_path.exists() or not rec_path.exists():
        return None
    aliases = json.loads(alias_path.read_text(encoding='utf-8'))
    by_canonical = {}
    with gzip.open(rec_path, 'rt', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            by_canonical.setdefault(r.get('canonical_label'), []).append(r)
    cached = {'aliases': aliases, 'by_canonical': by_canonical}
    _DATABASE_BUNDLE_CACHE[key] = cached
    return cached


def lookup_database_records(bundle_dir, prefix, label):
    """Lookup by canonical or same-row database alias using a cached bundle index."""
    bundle = _load_database_bundle(bundle_dir, prefix)
    if bundle is None:
        return []
    aliases = bundle['aliases']
    kind = 'link' if prefix == 'linkinfo' else 'knot'
    canonical_query = _canonicalize(label, kind)
    targets = set(aliases.get(label, []))
    if canonical_query:
        targets.update(aliases.get(canonical_query, []))
        targets.add(canonical_query)
    # Exact canonical labels remain valid even if an aliases file was minimized.
    targets.add(str(label))
    hits = []
    seen = set()
    for target in targets:
        for r in bundle['by_canonical'].get(target, []):
            rid = (r.get('sheet'), r.get('row_1based'), r.get('canonical_label'))
            if rid in seen:
                continue
            seen.add(rid)
            hits.append(r)
    return hits
