from __future__ import annotations

from pathlib import Path
import os
import re
import sys

ROOT = Path(__file__).resolve().parent
LOCATOR = ROOT / ".sst_framework_root"


def _version_key(path: Path) -> tuple[int, int, int]:
    m = re.search(r"_v(\d+)\.(\d+)\.(\d+)$", path.name)
    return tuple(map(int, m.groups())) if m else (-1, -1, -1)


def _candidate_frameworks() -> list[Path]:
    candidates: list[Path] = []

    # 1) Explicit user/CI override always wins.
    env = os.environ.get("SST_FALSIFIER_FRAMEWORK_ROOT")
    if env:
        candidates.append(Path(env).expanduser())

    # 2) Relative locator written by tools/new_falsifier.py.
    #    The path is relative to the generated falsifier instance, so moving
    #    the entire SST-Workbench tree preserves the relationship.
    if LOCATOR.exists():
        raw = LOCATOR.read_text(encoding="utf-8").strip()
        if raw:
            p = Path(raw)
            candidates.append(p if p.is_absolute() else (ROOT / p))

    # 3) Workbench-root autodiscovery. This also repairs older generated
    #    instances that do not yet have .sst_framework_root.
    for parent in [ROOT, *ROOT.parents]:
        templates = parent / "06_templates"
        if templates.is_dir():
            # Canonical SST-Workbench layout:
            #   06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_vX.Y.Z
            family = templates / "SST_Falsifier_Framework"
            nested_versioned = sorted(
                [p for p in family.glob("SST_Falsifier_Framework_v*") if p.is_dir()]
                if family.is_dir() else [],
                key=_version_key,
                reverse=True,
            )
            candidates.extend(nested_versioned)

            # Compatibility with the earlier flat 06_templates layout.
            flat_versioned = sorted(
                [p for p in templates.glob("SST_Falsifier_Framework_v*") if p.is_dir()],
                key=_version_key,
                reverse=True,
            )
            candidates.extend(flat_versioned)
            candidates.append(family)


    # Preserve precedence while removing duplicates.
    seen: set[str] = set()
    out: list[Path] = []
    for c in candidates:
        try:
            resolved = c.resolve()
        except OSError:
            resolved = c
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            out.append(resolved)
    return out


def _load_framework() -> Path | None:
    try:
        import sst_falsifier  # noqa: F401
        return None
    except ImportError:
        pass

    attempted: list[str] = []
    for candidate in _candidate_frameworks():
        attempted.append(str(candidate))
        if (candidate / "sst_falsifier" / "__init__.py").is_file():
            sys.path.insert(0, str(candidate))
            import sst_falsifier  # noqa: F401
            return candidate

    raise RuntimeError(
        "Could not locate SST_Falsifier_Framework.\n"
        "Set SST_FALSIFIER_FRAMEWORK_ROOT, regenerate this falsifier with the patched "
        "new_falsifier.py, or place it under SST-Workbench\\06_templates\\SST_Falsifier_Framework.\n"
        "Attempted:\n  - " + "\n  - ".join(attempted)
    )


_load_framework()
from sst_falsifier.runner import run_mode

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "BASIC"
    raise SystemExit(run_mode(ROOT, mode))
