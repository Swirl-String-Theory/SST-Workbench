from __future__ import annotations

from pathlib import Path
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parent
LOCATOR = ROOT / ".sst_framework_root"


def _version_key(path: Path):
    m = re.search(r"_v(\d+)\.(\d+)\.(\d+)$", path.name)
    return tuple(map(int, m.groups())) if m else (-1, -1, -1)


def _candidates():
    candidates = []
    env_root = os.environ.get("SST_FALSIFIER_FRAMEWORK_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    if LOCATOR.exists():
        raw = LOCATOR.read_text(encoding="utf-8").strip()
        if raw:
            p = Path(raw)
            candidates.append(p if p.is_absolute() else ROOT / p)
    for parent in [ROOT, *ROOT.parents]:
        family = parent / "06_templates" / "SST_Falsifier_Framework"
        if family.is_dir():
            candidates.extend(
                sorted(
                    [p for p in family.glob("SST_Falsifier_Framework_v*") if p.is_dir()],
                    key=_version_key,
                    reverse=True,
                )
            )
    return candidates


def _load_framework():
    try:
        import sst_falsifier  # noqa: F401
        return
    except ImportError:
        pass
    for p in _candidates():
        if (p / "sst_falsifier" / "__init__.py").is_file():
            sys.path.insert(0, str(p.resolve()))
            import sst_falsifier  # noqa: F401
            return
    raise RuntimeError(
        "SST Falsifier Framework v1.0.4 not found; set "
        "SST_FALSIFIER_FRAMEWORK_ROOT or install it at the canonical 06_templates path."
    )


_load_framework()

from sst_falsifier.outputs import make_output_manifest, pack_blind, pack_revealed
from sst_falsifier.report import latex_escape, publish_instance_report
from sst_falsifier.runner import run_mode
from sst_falsifier.util import write_json

GEN_OUT = ROOT / "A056_v0.2.3-outputs"
CAN_OUT = ROOT / "A056-v0.2.3-outputs"
GEN_PREFIX = "A056_v0.2.3-outputs"
CAN_PREFIX = "A056-v0.2.3-outputs"


def _break_token(value, every: int = 16) -> str:
    """Escape a long token and insert legal TeX wrap points without changing its value."""
    raw = str(value)
    chunks = [raw[i : i + every] for i in range(0, len(raw), every)] or [""]
    return r"\allowbreak{}".join(latex_escape(chunk) for chunk in chunks)


def _status_tex(value) -> str:
    return latex_escape(value).replace(r"\_", r"\_\allowbreak{}")


def _tex_row(*cells: str) -> str:
    return " & ".join(cells) + r" \\"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def _safe_auto_results(out: Path) -> bool:
    """Render run results in a page-safe form while preserving canonical JSON as authority.

    Framework v1.0.4 is not modified. The framework first writes its machine-generated
    AUTO_RESULTS.tex; this instance adapter replaces only that *generated output view* with
    wrapped tables. The authoritative JSON manifests remain byte-for-byte run artifacts.
    """
    auto = out / "report" / "AUTO_RESULTS.tex"
    if not auto.exists():
        return False

    frozen = _load_json(ROOT / "preregistration" / "FROZEN_PROTOCOL.json")
    ledger = _load_json(out / "GATE_LEDGER_REVEALED.json") or _load_json(out / "GATE_LEDGER.json")
    env = _load_json(out / "ENVIRONMENT_PUBLIC.json")
    backend = _load_json(out / "BACKEND_MANIFEST.json")
    source = _load_json(out / "SOURCE_MANIFEST.json")

    lines = [
        r"% AUTO-GENERATED A056 layout-safe view; authoritative JSON remains in output manifests.",
        r"\subsection*{Automatic run provenance}",
        r"\begin{longtable}{>{\raggedright\arraybackslash}p{0.30\linewidth}>{\raggedright\arraybackslash}p{0.62\linewidth}}",
        r"\toprule",
        _tex_row("Field", "Recorded value"),
        r"\midrule",
        _tex_row("Protocol bundle SHA-256", _break_token(frozen.get("bundle_sha256", "unavailable"))),
        _tex_row("Framework schema", latex_escape(frozen.get("schema", "unavailable"))),
        _tex_row("Framework version", latex_escape(backend.get("framework_version", "1.0.4"))),
        _tex_row("Python", latex_escape(env.get("python", "unavailable"))),
        _tex_row("Platform", latex_escape(env.get("platform", "unavailable"))),
        r"\bottomrule",
        r"\end{longtable}",
        r"\subsubsection*{Gate ledger}",
        r"\begin{longtable}{>{\raggedright\arraybackslash}p{0.045\linewidth}>{\raggedright\arraybackslash}p{0.175\linewidth}>{\raggedright\arraybackslash}p{0.365\linewidth}>{\raggedright\arraybackslash}p{0.245\linewidth}}",
        r"\toprule",
        _tex_row("Gate", "Status", "Question", "Reason"),
        r"\midrule",
    ]
    for rec in ledger.get("records", []):
        lines.append(
            _tex_row(
                latex_escape(rec.get("gate_id", "")),
                _status_tex(rec.get("status", "")),
                latex_escape(rec.get("question", "")),
                latex_escape(rec.get("reason", "")),
            )
        )
    lines += [r"\bottomrule", r"\end{longtable}", r"\subsubsection*{Backend summary}"]

    cpp = backend.get("cpp_certification") or {}
    native = cpp.get("native") or {}
    build = native.get("build") or {}
    gpu = backend.get("gpu_screening") or {}
    pref = backend.get("python_reference") or {}
    backend_rows = [
        ("A056 version", backend.get("a056_version", "unavailable")),
        ("Framework", backend.get("framework_version", "1.0.4")),
        (
            "Python reference",
            f"{pref.get('actual_backend', 'unavailable')} / {pref.get('precision', 'unavailable')} / {pref.get('authority', 'REFERENCE')}",
        ),
        ("C++ certification", f"{cpp.get('gate_status', 'unavailable')} / {cpp.get('authority', 'CERTIFICATION')}"),
        ("Native backend", build.get("actual_backend", native.get("available", "unavailable"))),
        ("Compiler", build.get("compiler", "unavailable")),
        ("Compiler version", build.get("compiler_version", "unavailable")),
        ("Build fingerprint SHA-256", build.get("fingerprint_sha256", "unavailable")),
        ("GPU screening", f"{gpu.get('gate_status', 'unavailable')} / {gpu.get('authority', 'SCREENING_ONLY')}"),
    ]
    lines += [
        r"\begin{longtable}{>{\raggedright\arraybackslash}p{0.30\linewidth}>{\raggedright\arraybackslash}p{0.62\linewidth}}",
        r"\toprule",
        _tex_row("Field", "Recorded value"),
        r"\midrule",
    ]
    for label, value in backend_rows:
        rendered = _break_token(value) if "SHA-256" in label else latex_escape(value)
        lines.append(_tex_row(latex_escape(label), rendered))
    lines += [r"\bottomrule", r"\end{longtable}", r"\subsubsection*{Source summary}"]

    lines += [
        r"\begin{longtable}{>{\raggedright\arraybackslash}p{0.18\linewidth}>{\raggedright\arraybackslash}p{0.18\linewidth}>{\raggedright\arraybackslash}p{0.20\linewidth}>{\raggedright\arraybackslash}p{0.27\linewidth}}",
        r"\toprule",
        _tex_row("Source", "Role", "Evidence", "Provenance family"),
        r"\midrule",
    ]
    for item in source.get("sources", []):
        lines.append(
            _tex_row(
                _status_tex(item.get("source_id", "")),
                _status_tex(item.get("role", "")),
                _status_tex(item.get("evidence_class", "")),
                _status_tex(item.get("provenance_family", "")),
            )
        )
    lines += [
        r"\bottomrule",
        r"\end{longtable}",
        r"\noindent Full machine-readable provenance is preserved in \code{BACKEND\_MANIFEST.json}, \code{SOURCE\_MANIFEST.json}, \code{ENVIRONMENT\_PUBLIC.json}, and \code{OUTPUT\_MANIFEST.json}.",
    ]
    auto.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def _postprocess_report_and_package(mode: str) -> None:
    """Repair generated report layout and refresh manifests/packages without touching v1.0.4."""
    if mode in {"FREEZE", "SELFTEST"}:
        return
    out = GEN_OUT if GEN_OUT.exists() else CAN_OUT
    tex = out / "report" / "FALSIFIER_REPORT.tex"
    if not (out.exists() and tex.exists()):
        return
    if not _safe_auto_results(out):
        return

    render = publish_instance_report(ROOT, tex, strict=False)
    write_json(out / "REPORT_RENDER.json", render)
    make_output_manifest(out, out / "OUTPUT_MANIFEST.json")
    if mode == "REVEAL":
        pack_revealed(out, ROOT.parent / f"{GEN_PREFIX}_REVEALED.zip")
    else:
        pack_blind(ROOT, out, ROOT.parent / f"{GEN_PREFIX}_BLIND.zip")


def _move(src: Path, dst: Path):
    if src.exists() and not dst.exists():
        src.replace(dst)


def _prepare():
    _move(CAN_OUT, GEN_OUT)
    for suffix in ("_BLIND.zip", "_REVEALED.zip"):
        _move(ROOT.parent / f"{CAN_PREFIX}{suffix}", ROOT.parent / f"{GEN_PREFIX}{suffix}")


def _finish():
    _move(GEN_OUT, CAN_OUT)
    for suffix in ("_BLIND.zip", "_REVEALED.zip"):
        _move(ROOT.parent / f"{GEN_PREFIX}{suffix}", ROOT.parent / f"{CAN_PREFIX}{suffix}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "BASIC"
    _prepare()
    try:
        rc = run_mode(ROOT, mode)
        _postprocess_report_and_package(mode.upper())
    finally:
        _finish()
    raise SystemExit(rc)
