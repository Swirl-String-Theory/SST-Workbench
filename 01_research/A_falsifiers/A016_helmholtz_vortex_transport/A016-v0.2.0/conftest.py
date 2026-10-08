from __future__ import annotations

"""Bootstrap the shared SST Falsifier Framework before pytest collection.

Thin falsifier instances reference, rather than vendor, the framework. Pytest imports
individual test modules before ``run_instance.py`` executes, so direct test imports of
``sst_falsifier`` need the same locator/autodiscovery contract at collection time.
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
            candidates.extend(
                sorted(
                    [p for p in templates.glob("SST_Falsifier_Framework_v*") if p.is_dir()],
                    key=_version_key,
                    reverse=True,
                )
            )
            candidates.append(family)

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
        "Set SST_FALSIFIER_FRAMEWORK_ROOT, regenerate this falsifier with the current "
        "framework, or place it under SST-Workbench\\06_templates\\SST_Falsifier_Framework.\n"
        "Attempted:\n  - " + "\n  - ".join(attempted)
    )


FRAMEWORK_ROOT = _bootstrap_framework()
