from __future__ import annotations
from pathlib import Path

MARKER = ".sst_framework_root"

def find_framework_root(start: Path, expected_version: str | None = None) -> Path:
    """Walk upward to the exact framework root marker.

    This avoids depth-sensitive ``parents[N]`` logic in nested Workbench paths.
    If ``expected_version`` is supplied the marker must contain that version.
    """
    p = Path(start).resolve()
    if p.is_file():
        p = p.parent
    for candidate in (p, *p.parents):
        marker = candidate / MARKER
        if not marker.exists():
            continue
        text = marker.read_text(encoding="utf-8", errors="replace").strip()
        if expected_version and expected_version not in text:
            raise RuntimeError(
                f"framework marker found at {candidate}, but version does not match {expected_version}: {text}"
            )
        return candidate
    raise FileNotFoundError(f"could not locate {MARKER} from {start}")
