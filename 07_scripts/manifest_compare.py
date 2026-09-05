"""Compare scientific manifests for SP10: ignore provenance noise, catch quantity drift."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

# Keys whose values are allowed (and expected) to differ after a move.
IGNORE_KEY_RE = re.compile(
    r"(?i)^(timestamp|created_at|updated_at|mtime|run_id|run_uuid|uuid|"
    r"hostname|user|cwd|workdir|working_dir|absolute_path|abs_path|"
    r"pack_path|source_path|output_path|path|paths|file|filepath|"
    r"git_sha|git_commit|elapsed|duration|wall_time|started_at|finished_at)$"
)

PATHISH_RE = re.compile(r"(?i)(/|\\|[A-Za-z]:\\|users[/\\]|workspace[/\\])")


def is_ignored_key(key: str) -> bool:
    return bool(IGNORE_KEY_RE.match(str(key).strip()))


def is_pathish(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) < 4:
        return False
    return bool(PATHISH_RE.search(value))


def extract_quantities(
    payload: Any,
    *,
    prefix: str = "",
) -> dict[str, Any]:
    """Flatten a JSON-like structure into comparable scientific quantities."""
    out: dict[str, Any] = {}

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                key_s = str(key)
                child = f"{path}.{key_s}" if path else key_s
                if is_ignored_key(key_s):
                    continue
                if is_pathish(value):
                    continue
                walk(value, child)
            return
        if isinstance(node, list):
            # Keep short numeric vectors; skip huge opaque lists.
            if node and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in node):
                if len(node) <= 64:
                    out[path or "list"] = list(node)
                return
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
            return
        if isinstance(node, bool) or node is None:
            out[path] = node
            return
        if isinstance(node, (int, float)):
            out[path] = node
            return
        if isinstance(node, str):
            if is_pathish(node):
                return
            # Keep short categorical labels / gate statuses.
            if len(node) <= 120:
                out[path] = node

    walk(payload, prefix)
    return out


def load_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        return {"_root": data}
    return data


def _close(a: Any, b: Any, *, rtol: float, atol: float) -> bool:
    if type(a) is not type(b) and not (
        isinstance(a, (int, float)) and isinstance(b, (int, float))
    ):
        return a == b
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=rtol, abs_tol=atol)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_close(x, y, rtol=rtol, atol=atol) for x, y in zip(a, b))
    return a == b


def compare_quantities(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    rtol: float = 0.0,
    atol: float = 0.0,
) -> list[str]:
    """Return human-readable diffs. Empty list means scientific match."""
    diffs: list[str] = []
    keys = sorted(set(left) | set(right))
    for key in keys:
        if key not in left:
            diffs.append(f"missing in left: {key}={right[key]!r}")
            continue
        if key not in right:
            diffs.append(f"missing in right: {key}={left[key]!r}")
            continue
        if not _close(left[key], right[key], rtol=rtol, atol=atol):
            diffs.append(f"{key}: {left[key]!r} != {right[key]!r}")
    return diffs


def compare_manifest_files(
    left: Path,
    right: Path,
    *,
    rtol: float = 0.0,
    atol: float = 0.0,
) -> list[str]:
    return compare_quantities(
        extract_quantities(load_manifest(left)),
        extract_quantities(load_manifest(right)),
        rtol=rtol,
        atol=atol,
    )
