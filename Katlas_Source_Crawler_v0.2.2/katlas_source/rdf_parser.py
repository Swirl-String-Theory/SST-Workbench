from __future__ import annotations

from dataclasses import dataclass, field
import gzip
import re
from pathlib import Path
from typing import Iterable

_TRIPLE = re.compile(
    r'^<(?P<subject>[^>]+)>\s+<(?P<predicate>[^>]+)>\s+"(?P<value>(?:\\.|[^"\\])*)"\s*\.\s*$'
)

@dataclass
class RdfObject:
    subject_type: str
    katlas_id: str
    invariants: dict[str, list[str]] = field(default_factory=dict)
    raw_lines: list[str] = field(default_factory=list)


def _unescape_literal(value: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch != "\\" or i + 1 >= len(value):
            out.append(ch)
            i += 1
            continue
        esc = value[i + 1]
        if esc == "n": out.append("\n"); i += 2
        elif esc == "r": out.append("\r"); i += 2
        elif esc == "t": out.append("\t"); i += 2
        elif esc == '"': out.append('"'); i += 2
        elif esc == "\\": out.append("\\"); i += 2
        elif esc == "u" and i + 5 < len(value):
            out.append(chr(int(value[i+2:i+6], 16))); i += 6
        elif esc == "U" and i + 9 < len(value):
            out.append(chr(int(value[i+2:i+10], 16))); i += 10
        else:
            # Preserve unknown RDF/Mathematica escapes instead of corrupting them.
            out.append("\\" + esc); i += 2
    return "".join(out)


def iter_lines(path: Path) -> Iterable[str]:
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        yield from f


def parse_dataset(path: Path) -> tuple[dict[tuple[str, str], RdfObject], list[str]]:
    objects: dict[tuple[str, str], RdfObject] = {}
    rejected: list[str] = []
    for raw in iter_lines(path):
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue
        m = _TRIPLE.match(line)
        if not m:
            rejected.append(line)
            continue
        subject = m["subject"]
        predicate = m["predicate"]
        if ":" not in subject or ":" not in predicate:
            rejected.append(line)
            continue
        subject_type, katlas_id = subject.split(":", 1)
        pred_ns, pred_name = predicate.split(":", 1)
        if subject_type not in {"knot", "link"} or pred_ns != "invariant":
            continue
        key = (subject_type, katlas_id)
        obj = objects.setdefault(key, RdfObject(subject_type, katlas_id))
        obj.invariants.setdefault(pred_name, []).append(_unescape_literal(m["value"]))
        obj.raw_lines.append(line)
    return objects, rejected


def normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())

PRESENTATION_ALIASES = {
    "pd": {"pdpresentation", "planardiagrampresentation"},
    "gauss": {"gausscode", "gausspresentation"},
    "dt": {"dtcode", "dowkerthistlethwaitecode", "dowkerthistlethwaitepresentation"},
    "conway": {"conwaynotation"},
    "braid": {"braidword", "braidrepresentative", "minimumbraidrepresentative"},
    "morse": {"morselinkpresentation"},
    "arc": {"arcpresentation"},
}


def extract_presentations(invariants: dict[str, list[str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    by_norm = {normalized_key(k): v for k, v in invariants.items()}
    for canonical, aliases in PRESENTATION_ALIASES.items():
        values: list[str] = []
        for alias in aliases:
            values.extend(by_norm.get(alias, []))
        if values:
            # Stable de-duplication.
            out[canonical] = list(dict.fromkeys(values))
    return out
