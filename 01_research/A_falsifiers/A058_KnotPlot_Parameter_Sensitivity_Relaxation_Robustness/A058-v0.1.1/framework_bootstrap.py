from __future__ import annotations

"""Resolve and load the shared SST Falsifier Framework deterministically.

Precedence is intentionally fail-closed:
1. explicit ``SST_FALSIFIER_FRAMEWORK_ROOT`` override;
2. generated ``.sst_framework_root`` locator;
3. legacy Workbench autodiscovery under the canonical nested ``06_templates`` family.

If an explicit override or locator exists but is invalid, discovery stops with an error.
An already importable/editable ``sst_falsifier`` installation is never allowed to override
an explicit pin.
"""

from pathlib import Path
import importlib
import os
import re
import sys

ROOT = Path(__file__).resolve().parent
LOCATOR = ROOT / ".sst_framework_root"


class FrameworkBootstrapError(RuntimeError):
    pass


def _version_key(path: Path) -> tuple[int, int, int]:
    m = re.search(r"_v(\d+)\.(\d+)\.(\d+)$", path.name)
    return tuple(map(int, m.groups())) if m else (-1, -1, -1)


def _require_framework_root(candidate: Path, source: str) -> Path:
    try:
        resolved = candidate.expanduser().resolve()
    except OSError as exc:
        raise FrameworkBootstrapError(f"Invalid {source} framework path {candidate!s}: {exc}") from exc
    marker = resolved / "sst_falsifier" / "__init__.py"
    if not marker.is_file():
        raise FrameworkBootstrapError(
            f"{source} points to an invalid SST Falsifier Framework root: {resolved}\n"
            f"Missing: {marker}"
        )
    return resolved


def resolve_framework_root() -> Path:
    # 1) Explicit user/CI override is authoritative. Invalid means fail closed.
    env = os.environ.get("SST_FALSIFIER_FRAMEWORK_ROOT", "").strip()
    if env:
        return _require_framework_root(Path(env), "SST_FALSIFIER_FRAMEWORK_ROOT")

    # 2) Generated locator is authoritative when present. Invalid/empty means fail closed.
    if LOCATOR.exists():
        raw = LOCATOR.read_text(encoding="utf-8").strip()
        if not raw:
            raise FrameworkBootstrapError(f"Framework locator is empty: {LOCATOR}")
        p = Path(raw)
        candidate = p if p.is_absolute() else ROOT / p
        return _require_framework_root(candidate, ".sst_framework_root")

    # 3) Compatibility only for legacy instances that predate the locator.
    attempted: list[str] = []
    for parent in [ROOT, *ROOT.parents]:
        family = parent / "06_templates" / "SST_Falsifier_Framework"
        if not family.is_dir():
            continue
        versioned = sorted(
            [p for p in family.glob("SST_Falsifier_Framework_v*") if p.is_dir()],
            key=_version_key,
            reverse=True,
        )
        for candidate in versioned:
            attempted.append(str(candidate))
            marker = candidate / "sst_falsifier" / "__init__.py"
            if marker.is_file():
                return candidate.resolve()

    raise FrameworkBootstrapError(
        "Could not locate SST_Falsifier_Framework.\n"
        "Set SST_FALSIFIER_FRAMEWORK_ROOT, regenerate the falsifier so it has a valid "
        ".sst_framework_root locator, or place the framework under "
        "SST-Workbench\\06_templates\\SST_Falsifier_Framework\\SST_Falsifier_Framework_vX.Y.Z.\n"
        "Legacy autodiscovery attempted:\n  - " + ("\n  - ".join(attempted) if attempted else "<none>")
    )


def load_framework() -> Path:
    framework = resolve_framework_root()
    framework_s = str(framework)

    # Make the pinned root first and remove duplicate textual copies.
    sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p or ".")) != os.path.normcase(framework_s)]
    sys.path.insert(0, framework_s)

    # A stale editable/global framework may already have been imported by a launcher/plugin.
    # Remove it so the authoritative pin is actually enforced.
    for name in list(sys.modules):
        if name == "sst_falsifier" or name.startswith("sst_falsifier."):
            del sys.modules[name]
    importlib.invalidate_caches()

    module = importlib.import_module("sst_falsifier")
    actual = Path(module.__file__).resolve().parent.parent
    if actual != framework:
        raise FrameworkBootstrapError(
            f"Pinned framework import mismatch: expected {framework}, imported {actual}"
        )
    return framework
