from __future__ import annotations
from pathlib import Path
import json
from typing import Any
from .util import read_json
from .science_contract import assert_science_contract

REQUIRED_SECTION_MARKERS = (
    "IDENTIFICATION", "QUESTION", "HYPOTHESES", "ASSUMPTIONS", "SYMBOLS", "EQUATIONS",
    "ALGORITHM", "SOURCES", "GATES", "NUMERICS", "BACKENDS", "BLINDNESS", "STATISTICS",
    "RESULTS", "INTERPRETATION", "REPRODUCIBILITY"
)
REPORT_PLACEHOLDERS = ("\\SSTTODO{", "<<FILL", "TODO_SCIENCE", "REPLACE_BEFORE_FREEZE")

class ReportContractError(RuntimeError):
    pass


def latex_escape(s: Any) -> str:
    s = str(s)
    repl = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(repl.get(ch, ch) for ch in s)


def validate_report(path: str | Path, *, require_complete: bool = True) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    errors=[]
    for marker in REQUIRED_SECTION_MARKERS:
        if f"SST-REPORT-SECTION:{marker}" not in text:
            errors.append(f"missing report section marker: {marker}")
    if require_complete:
        for token in REPORT_PLACEHOLDERS:
            if token in text:
                errors.append(f"report placeholder remains: {token}")
    return errors


def assert_report(path: str | Path, *, require_complete: bool = True) -> None:
    errors=validate_report(path, require_complete=require_complete)
    if errors:
        raise ReportContractError("report contract incomplete:\n- " + "\n- ".join(errors))


def _load_optional(path: Path) -> dict[str, Any]:
    try:
        return read_json(path) if path.exists() else {}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def write_auto_science_tex(instance_root: str | Path, out_path: str | Path) -> None:
    root=Path(instance_root)
    c=assert_science_contract(root / "science_contract.json")
    lines=[r"% AUTO-GENERATED. Do not edit; generated from frozen science_contract.json.",
           r"\subsection*{Machine-readable science contract}",
           r"\begin{description}",
           rf"\item[Research question] {latex_escape(c['research_question'])}",
           rf"\item[Objective] {latex_escape(c['objective'])}",
           rf"\item[$H_0$] {latex_escape(c['null_hypothesis'])}",
           rf"\item[$H_1$] {latex_escape(c['alternative_hypothesis'])}", r"\end{description}",
           r"\subsubsection*{Registered equations}"]
    for eq in c.get("equations", []):
        lines += [rf"\paragraph{{{latex_escape(eq['id'])}: {latex_escape(eq['purpose'])}}}",
                  r"\begin{equation}", str(eq["latex"]), r"\end{equation}",
                  rf"\noindent\textit{{Dimensional check:}} {latex_escape(eq['dimensional_check'])}\\"]
    lines += [r"\subsubsection*{Registered code-to-mathematics steps}", r"\begin{enumerate}"]
    for step in c.get("steps", []):
        refs=", ".join(step.get("formula_refs", []))
        lines.append(rf"\item \textbf{{{latex_escape(step['id'])}}} [{latex_escape(step['gate'])}; equations {latex_escape(refs)}]: {latex_escape(step['operation'])}")
    lines.append(r"\end{enumerate}")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines)+"\n", encoding="utf-8")


def write_auto_results_tex(instance_root: str | Path, out_root: str | Path, out_path: str | Path) -> None:
    root=Path(instance_root); out=Path(out_root)
    frozen=_load_optional(root/"preregistration"/"FROZEN_PROTOCOL.json")
    ledger=_load_optional(out/"GATE_LEDGER_REVEALED.json") if (out/"GATE_LEDGER_REVEALED.json").exists() else _load_optional(out/"GATE_LEDGER.json")
    env=_load_optional(out/"ENVIRONMENT_PUBLIC.json")
    backend=_load_optional(out/"BACKEND_MANIFEST.json")
    src=_load_optional(out/"SOURCE_MANIFEST.json")
    output=_load_optional(out/"OUTPUT_MANIFEST.json")
    lines=[r"% AUTO-GENERATED. Do not edit.", r"\subsection*{Automatic run provenance}", r"\begin{longtable}{p{0.28\linewidth}p{0.64\linewidth}}",
           r"\toprule", r"Field & Recorded value \\", r"\midrule"]
    rows=[
        ("Protocol bundle SHA-256", frozen.get("bundle_sha256","unavailable")),
        ("Framework schema", frozen.get("schema","unavailable")),
        ("Python", env.get("python","unavailable")),
        ("Platform", env.get("platform","unavailable")),
        ("Output manifest SHA-256", output.get("manifest_sha256","unavailable")),
    ]
    for a,b in rows: lines.append(f"{latex_escape(a)} & {latex_escape(b)} \\\\")
    lines += [r"\bottomrule", r"\end{longtable}", r"\subsubsection*{Gate ledger}", r"\begin{longtable}{llll}", r"\toprule", r"Gate & Status & Question & Reason \\", r"\midrule"]
    for rec in ledger.get("records",[]):
        lines.append("{} & {} & {} & {} \\\\".format(*(latex_escape(rec.get(k,"")) for k in ("gate_id","status","question","reason"))))
    lines += [r"\bottomrule", r"\end{longtable}", r"\subsubsection*{Backend manifest}", r"\begin{verbatim}", json.dumps(backend,indent=2,sort_keys=True), r"\end{verbatim}", r"\subsubsection*{Source manifest}", r"\begin{verbatim}", json.dumps(src,indent=2,sort_keys=True), r"\end{verbatim}"]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines)+"\n", encoding="utf-8")
