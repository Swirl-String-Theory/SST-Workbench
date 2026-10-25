from __future__ import annotations
from pathlib import Path
import gzip, re, numpy as np

_COLON_ID_RE = re.compile(r'^(\d+):(\d+):(\d+)$')
_HT_ID_RE = re.compile(r'^K(\d+)([an])(\d+)$', re.I)
_LINK_ID_RE = re.compile(r'^L(\d+)([an])(\d+)$', re.I)
_ATTR_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_.:-]*)\s*=\s*"([^"]*)"')
_RECORD_START_RE = re.compile(r'^\s*<(AB|HT|TL)\b([^>]*)>')
_COEFF_RE = re.compile(r'<Coeff\b([^>]*)/?>', re.I)
_STRING_RE = re.compile(r'<STRING\b([^>]*)>(.*?)</STRING\s*>', re.I | re.S)
_STRING_START_RE = re.compile(r'<STRING\b([^>]*)>', re.I)

# Production qualification may touch >2000 Gilbert topologies. Re-reading ten gzip
# catalogues for every topology would dominate runtime. The complete decompressed
# upstream source set is modest (~72 MiB in the canonical Workbench snapshot), so cache
# record-local raw text once per process and parse coefficient arrays only on demand.
_RAW_RECORD_CACHE: dict[str, list[tuple[str, dict, str]]] = {}
_HEADER_CACHE: dict[str, list[dict]] = {}
_CANONICAL_LOOKUP_CACHE: dict[str, dict[str, tuple[str, dict, str]]] = {}


def _attrs(text):
    return {k: v for k, v in _ATTR_RE.findall(text or '')}


def canonical_id_from_gilbert(record_id):
    """Map Brian Gilbert record IDs onto PKLSA canonical topology labels.

    Upstream conventions used by the archived Gilbert catalogues are:
      * Ideal.txt: C:1:i -> C_i
      * Ideal_11a/n: K11a1 / K11n1 -> 11a_1 / 11n_1
      * IdealLinks*: L2a1 / L10n3 -> retained LinkInfo/Knot Atlas label

    Colon records whose middle namespace is not 1 are intentionally left unmapped;
    PKLSA must not invent a topology relation for source-local/derived record IDs.
    """
    s = str(record_id or '').strip()
    m = _COLON_ID_RE.fullmatch(s)
    if m:
        crossings, namespace, index = map(int, m.groups())
        return f'{crossings}_{index}' if namespace == 1 else None
    m = _HT_ID_RE.fullmatch(s)
    if m:
        return f'{int(m.group(1))}{m.group(2).lower()}_{int(m.group(3))}'
    m = _LINK_ID_RE.fullmatch(s)
    if m:
        return f'L{int(m.group(1))}{m.group(2).lower()}{int(m.group(3))}'
    return None


def _read_record_texts(path):
    p = Path(path).resolve()
    key = str(p)
    cached = _RAW_RECORD_CACHE.get(key)
    if cached is not None:
        return cached

    opener = gzip.open if p.suffix.lower() == '.gz' else open
    records = []
    with opener(p, 'rt', encoding='utf-8', errors='strict') as f:
        active_tag = None
        header_attrs = None
        buf = []
        for line in f:
            if active_tag is None:
                m = _RECORD_START_RE.match(line)
                if not m:
                    continue
                active_tag = m.group(1).upper()
                header_attrs = _attrs(m.group(2))
                buf = [line[m.end():]]
                if re.search(fr'</{active_tag}\s*>', buf[0], re.I):
                    body = re.split(fr'</{active_tag}\s*>', buf[0], maxsplit=1, flags=re.I)[0]
                    records.append((active_tag, header_attrs, body))
                    active_tag = None; header_attrs = None; buf = []
                continue

            end_match = re.search(fr'</{active_tag}\s*>', line, re.I)
            if end_match:
                buf.append(line[:end_match.start()])
                records.append((active_tag, header_attrs, ''.join(buf)))
                active_tag = None
                header_attrs = None
                buf = []
            else:
                buf.append(line)

        if active_tag is not None:
            raise ValueError(f'unterminated Gilbert record <{active_tag}> in {p}')

    _RAW_RECORD_CACHE[key] = records
    return records


def _record_header(tag, header_attrs, text):
    string_attrs = [_attrs(x) for x in _STRING_START_RE.findall(text)]
    canonical = canonical_id_from_gilbert(header_attrs.get('Id'))
    raw_l = header_attrs.get('L')
    if raw_l not in (None, ''):
        reference_length = float(raw_l)
    else:
        lengths = [float(a['L']) for a in string_attrs if a.get('L') not in (None, '')]
        reference_length = sum(lengths) if lengths else None
    return {
        'tag': tag,
        'attrs': header_attrs,
        'canonical_id': canonical,
        'reference_length': reference_length,
        'component_count': max(1, len(string_attrs)),
    }


def iter_gilbert_record_headers(path):
    """Yield lightweight record metadata without allocating coefficient arrays."""
    key = str(Path(path).resolve())
    headers = _HEADER_CACHE.get(key)
    if headers is None:
        headers = [_record_header(tag, attrs, text) for tag, attrs, text in _read_record_texts(path)]
        _HEADER_CACHE[key] = headers
    yield from headers


def _parse_coefficients(text):
    out = []
    for raw in _COEFF_RE.findall(text or ''):
        a = _attrs(raw)
        if not {'I', 'A', 'B'} <= set(a):
            continue
        I = int(a['I'])
        A = np.fromstring(a['A'], sep=',', dtype=float)
        B = np.fromstring(a['B'], sep=',', dtype=float)
        if A.shape != (3,) or B.shape != (3,):
            raise ValueError('Gilbert Coeff must contain 3-vectors A and B')
        out.append((I, A, B))
    return out


def _parse_record(tag, header_attrs, text):
    record = {'tag': tag, 'attrs': header_attrs, 'components': []}
    string_matches = list(_STRING_RE.finditer(text))
    if string_matches:
        for m in string_matches:
            comp = {'attrs': _attrs(m.group(1)), 'coeff': _parse_coefficients(m.group(2))}
            if comp['coeff']:
                record['components'].append(comp)
    elif _STRING_START_RE.search(text):
        # Historical Ideal_11n opens <STRING> but omits </STRING> before </HT>.
        m = _STRING_START_RE.search(text)
        comp = {'attrs': _attrs(m.group(1)), 'coeff': _parse_coefficients(text[m.end():])}
        if comp['coeff']:
            record['components'].append(comp)
    else:
        coeff = _parse_coefficients(text)
        if coeff:
            record['components'].append({'attrs': {}, 'coeff': coeff})

    header = _record_header(tag, header_attrs, text)
    record.update({k: header[k] for k in ('canonical_id', 'reference_length', 'component_count')})
    record['coeff'] = record['components'][0]['coeff'] if len(record['components']) == 1 else []
    return record


def iter_gilbert_records(path):
    """Yield fully parsed AB/HT/TL records without requiring global XML validity."""
    for tag, attrs, text in _read_record_texts(path):
        yield _parse_record(tag, attrs, text)


def find_gilbert_record(path, canonical_id):
    key = str(Path(path).resolve())
    lookup = _CANONICAL_LOOKUP_CACHE.get(key)
    if lookup is None:
        lookup = {}
        for raw, header in zip(_read_record_texts(path), iter_gilbert_record_headers(path)):
            cid = header.get('canonical_id')
            if cid:
                lookup[cid] = raw
        _CANONICAL_LOOKUP_CACHE[key] = lookup
    raw = lookup.get(canonical_id)
    if raw is None:
        raise KeyError(f'{canonical_id} not found in {path}')
    return _parse_record(*raw)


def _sample_coefficients(coeff, n):
    t = np.linspace(0, 2 * np.pi, int(n), endpoint=False)
    out = np.zeros((int(n), 3), float)
    for I, A, B in coeff:
        if I == 0:
            # Brian Gilbert/Knot Atlas convention: constant Fourier term is A_0/2.
            out += 0.5 * A[None, :]
        else:
            out += np.cos(I * t)[:, None] * A[None, :] + np.sin(I * t)[:, None] * B[None, :]
    return out


def sample_gilbert_components(record, n=4096):
    comps = record.get('components') or []
    if not comps and record.get('coeff'):
        comps = [{'attrs': {}, 'coeff': record['coeff']}]
    if not comps:
        raise ValueError('Gilbert record contains no Fourier components')
    return [_sample_coefficients(comp['coeff'], n) for comp in comps]


def sample_gilbert_record(record, n=4096):
    """Backward-compatible sampler for a single-component Gilbert record."""
    comps = sample_gilbert_components(record, n=n)
    if len(comps) != 1:
        raise ValueError('multi-component Gilbert record; use sample_gilbert_components')
    return comps[0]
