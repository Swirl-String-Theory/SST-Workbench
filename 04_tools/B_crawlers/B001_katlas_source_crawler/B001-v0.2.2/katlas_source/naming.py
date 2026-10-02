from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path

_ROLFSEN = re.compile(r"^(?P<c>\d+)_(?P<n>\d+)$")
_KNOT_HT = re.compile(r"^K(?P<c>\d+)(?P<f>[an])(?P<n>\d+)$")
_LINK_HT = re.compile(r"^L(?P<c>\d+)(?P<f>[an])(?P<n>\d+)$")

@dataclass(frozen=True)
class KatlasIdentity:
    katlas_id: str
    kind: str
    crossings: int
    ordinal: int
    family: str | None
    table_name: str


def parse_identity(subject_type: str, katlas_id: str) -> KatlasIdentity | None:
    """Parse exact Katlas identifiers.

    Identifier syntax is authoritative. This is intentional: the official
    Links.rdf.gz currently uses the RDF subject namespace ``knot:`` even for
    identifiers such as L2a1, L6n1, etc. Trusting subject_type alone would
    therefore discard the complete link table.
    """
    m = _LINK_HT.match(katlas_id)
    if m:
        fam = "alternating" if m["f"] == "a" else "nonalternating"
        return KatlasIdentity(
            katlas_id, "link", int(m["c"]), int(m["n"]), fam,
            "Thistlethwaite",
        )

    m = _KNOT_HT.match(katlas_id)
    if m:
        fam = "alternating" if m["f"] == "a" else "nonalternating"
        return KatlasIdentity(
            katlas_id, "knot", int(m["c"]), int(m["n"]), fam,
            "Hoste-Thistlethwaite",
        )

    m = _ROLFSEN.match(katlas_id)
    if m:
        return KatlasIdentity(
            katlas_id, "knot", int(m["c"]), int(m["n"]), None, "Rolfsen"
        )
    return None


def shard_name(ordinal: int, size: int = 50) -> str:
    start = ((ordinal - 1) // size) * size + 1
    end = start + size - 1
    return f"{start:04d}-{end:04d}"


def object_relpath(identity: KatlasIdentity, shard_from: int = 10, shard_size: int = 50) -> Path:
    base = Path("knots" if identity.kind == "knot" else "links") / f"{identity.crossings:02d}"
    if identity.crossings < shard_from:
        return base / identity.katlas_id

    if identity.kind == "knot" and identity.table_name == "Rolfsen":
        family = "rolfsen"
    else:
        family = identity.family or "unclassified"
    return base / family / shard_name(identity.ordinal, shard_size) / identity.katlas_id
