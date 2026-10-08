from __future__ import annotations

"""Pytest bootstrap for thin SST falsifier instances.

Pytest imports test modules before ``run_instance.py`` executes.  Thin instances do
not vendor/install the shared framework, so tests that import ``sst_falsifier``
must resolve the same relative ``.sst_framework_root`` contract as the runtime.
"""

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
    env = os.environ.get("SST_FALSIFIER_FRAMEWORK_ROOT")
    if env:
        candidates.append(Path(env).expanduser())

    if LOCATOR.exists():
        raw = LOCATOR.read_text(encoding="utf-8").strip()
        if raw:
            p = Path(raw)
            candidates.append(p if p.is_absolute() else ROOT / p)

    for parent in [ROOT, *ROOT.parents]:
        templates = parent / "06_templates"
        family = templates / "SST_Falsifier_Framework"
        if family.is_dir():
            candidates.extend(
                sorted(
                    [p for p in family.glob("SST_Falsifier_Framework_v*") if p.is_dir()],
                    key=_version_key,
                    reverse=True,
                )
            )
    seen: set[str] = set()
    out: list[Path] = []
    for c in candidates:
        try:
            r = c.resolve()
        except OSError:
            r = c
        k = os.path.normcase(str(r))
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def _bootstrap_framework() -> Path:
    try:
        import sst_falsifier  # noqa: F401
        return Path(sst_falsifier.__file__).resolve().parent.parent
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
        "Could not locate SST_Falsifier_Framework for pytest collection.\n"
        "Set SST_FALSIFIER_FRAMEWORK_ROOT or place the canonical framework under "
        "SST-Workbench\\06_templates\\SST_Falsifier_Framework.\n"
        "Attempted:\n  - " + "\n  - ".join(attempted)
    )


FRAMEWORK_ROOT = _bootstrap_framework()
