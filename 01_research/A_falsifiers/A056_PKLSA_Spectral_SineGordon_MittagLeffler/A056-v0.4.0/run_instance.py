from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from framework_bootstrap import load_framework

FRAMEWORK_ROOT = load_framework()

from sst_falsifier.outputs import make_output_manifest, pack_blind, pack_revealed
from sst_falsifier.report import latex_escape, publish_instance_report
from sst_falsifier.runner import run_mode
from sst_falsifier.util import write_json

OUT = ROOT / "A056_v0.4.0-outputs"
PREFIX = "A056_v0.4.0-outputs"


def _break_token(value, every: int = 16) -> str:
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
    """Page-safe presentation adapter; authoritative JSON remains unchanged."""
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
        _tex_row("Framework version", latex_escape(backend.get("framework_version", "1.0.6"))),
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
        ("Framework", backend.get("framework_version", "1.0.6")),
        ("Python reference", f"{pref.get('actual_backend', 'unavailable')} / {pref.get('precision', 'unavailable')} / {pref.get('authority', 'REFERENCE')}"),
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
    if mode in {"FREEZE", "SELFTEST"} or not OUT.exists():
        return
    tex = OUT / "report" / "FALSIFIER_REPORT.tex"
    if not tex.exists() or not _safe_auto_results(OUT):
        return
    render = publish_instance_report(ROOT, tex, strict=False)
    write_json(OUT / "REPORT_RENDER.json", render)
    make_output_manifest(OUT, OUT / "OUTPUT_MANIFEST.json")
    revealed = (OUT / "RUN_SUMMARY_REVEALED.json").exists()
    if revealed:
        pack_revealed(OUT, ROOT.parent / f"{PREFIX}_REVEALED.zip")
    else:
        pack_blind(ROOT, OUT, ROOT.parent / f"{PREFIX}_BLIND.zip")


if __name__ == "__main__":
    mode = (sys.argv[1] if len(sys.argv) > 1 else "BASIC").upper()
    rc = run_mode(ROOT, mode)
    _postprocess_report_and_package(mode)
    raise SystemExit(rc)
