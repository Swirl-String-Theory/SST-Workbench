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
    unicode_tex = {
        "↔": r"\ensuremath{\leftrightarrow}", "→": r"\ensuremath{\rightarrow}",
        "←": r"\ensuremath{\leftarrow}", "≤": r"\ensuremath{\leq}",
        "≥": r"\ensuremath{\geq}", "±": r"\ensuremath{\pm}",
        "×": r"\ensuremath{\times}", "−": r"\ensuremath{-}",
        "∞": r"\ensuremath{\infty}", "≈": r"\ensuremath{\approx}",
        "≠": r"\ensuremath{\neq}", "∇": r"\ensuremath{\nabla}",
        "∂": r"\ensuremath{\partial}", "∈": r"\ensuremath{\in}",
        "α": r"\ensuremath{\alpha}", "β": r"\ensuremath{\beta}",
        "γ": r"\ensuremath{\gamma}", "δ": r"\ensuremath{\delta}",
        "Δ": r"\ensuremath{\Delta}", "φ": r"\ensuremath{\varphi}",
        "θ": r"\ensuremath{\theta}", "μ": r"\ensuremath{\mu}",
        "ρ": r"\ensuremath{\rho}", "σ": r"\ensuremath{\sigma}",
        "τ": r"\ensuremath{\tau}", "ω": r"\ensuremath{\omega}",
        "Ω": r"\ensuremath{\Omega}", "π": r"\ensuremath{\pi}",
        "κ": r"\ensuremath{\kappa}", "λ": r"\ensuremath{\lambda}",
        "ε": r"\ensuremath{\epsilon}", "°": r"\ensuremath{^\circ}",
        "↻": r"\ensuremath{\circlearrowright}", "↺": r"\ensuremath{\circlearrowleft}",
        "–": "--", "—": "---", "“": "``", "”": "''", "’": "'",
    }
    return "".join(unicode_tex.get(ch, repl.get(ch, ch)) for ch in s)


def latex_breakable(value: Any) -> str:
    """Safely permit wrapping long opaque gate IDs and machine-generated text."""
    raw = str(value)
    if len(raw) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in raw):
        return r"\allowbreak{}".join(raw[i:i+12] for i in range(0,64,12))
    return (latex_escape(value).replace(r"\_", r"\_\allowbreak{}")
            .replace("/", r"/\allowbreak{}").replace("-", r"-\allowbreak{}"))


def validate_report(path: str | Path, *, require_complete: bool = True) -> list[str]:
    import re
    source = Path(path).read_text(encoding='utf-8')
    errors=[]
    pattern=re.compile(r'(?m)^\s*%\s*SST-REPORT-SECTION:([A-Z_]+)\b')
    matches=list(pattern.finditer(source))
    found={m.group(1) for m in matches}
    for marker in REQUIRED_SECTION_MARKERS:
        if marker not in found: errors.append(f'missing report section marker: {marker}')
    if require_complete:
        for token in REPORT_PLACEHOLDERS:
            if token in source:errors.append(f'report placeholder remains: {token}')
        # A comment containing a marker is not itself scientific content.
        for i,m in enumerate(matches):
            name=m.group(1)
            if name not in REQUIRED_SECTION_MARKERS:continue
            end=matches[i+1].start() if i+1<len(matches) else len(source)
            body=source[m.end():end]
            body='\n'.join(line for line in body.splitlines() if not line.lstrip().startswith('%')).strip()
            if len(body)<70 or not re.search(r'\\(?:sub)*section\*?\{',body):
                errors.append(f'report section lacks substantial content/section heading: {name}')
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
    evidence=_load_optional(out/"SCIENCE_EVIDENCE_MANIFEST.json")
    run_identity=_load_optional(out/"RUN_ID.json")
    matrix=_load_optional(out/"AUTO_BACKEND_MATRIX.json")
    lines=[r"% AUTO-GENERATED. Do not edit.", r"\subsection*{Automatic run provenance}", r"\begin{longtable}{p{0.28\linewidth}p{0.64\linewidth}}",
           r"\toprule", r"Field & Recorded value \\", r"\midrule"]
    rows=[
        ("Run ID",run_identity.get("run_id","unavailable")),
        ("Run phase",("REVEALED" if (out/"RUN_SUMMARY_REVEALED.json").exists() else "BLIND")),
        ("2-of-3 backend execution",matrix.get("status","NOT_EXECUTED")),
        ("Executed backend categories", ", ".join(matrix.get("executed_backend_categories",[])) or "none"),
        ("GPU provider",matrix.get("policy",{}).get("selected_gpu_provider","unknown")),
        ("Protocol bundle SHA-256 (byte exact)", frozen.get("bundle_sha256","unavailable")),
        ("Portable protocol diagnostic SHA-256", frozen.get("portable_bundle_sha256", "unavailable")),
        ("Framework schema", frozen.get("schema","unavailable")),
        ("Python", env.get("python","unavailable")),
        ("Platform", env.get("platform","unavailable")),
        ("Science evidence SHA-256", evidence.get("manifest_sha256", "unavailable")),
        ("Final output manifest", "See OUTPUT_MANIFEST.json (finalized after PDF and report metadata)"),
    ]
    for a,b in rows: lines.append(f"{latex_escape(a)} & {latex_breakable(b)} \\\\")
    lines += [r"\bottomrule", r"\end{longtable}", r"\subsubsection*{Gate ledger}", r"\begingroup\small\setlength{\tabcolsep}{3pt}\begin{longtable}{p{0.07\linewidth}p{0.19\linewidth}p{0.31\linewidth}p{0.29\linewidth}}", r"\toprule", r"Gate & Status & Question & Reason \\", r"\midrule"]
    for rec in ledger.get("records", []):
        gate = latex_breakable(rec.get("gate_id", ""))
        status = latex_breakable(rec.get("status", ""))
        question = latex_breakable(rec.get("question", ""))
        reason = latex_breakable(rec.get("reason", ""))
        row = (r"{\ttfamily\scriptsize " + gate + "} & "
               + r"{\ttfamily\footnotesize " + status + "} & "
               + question + " & " + reason + " " + "\\\\")
        lines.append(row)
    lines += [r"\bottomrule",r"\end{longtable}\endgroup"]
    lines += [r"\subsubsection*{Scientific qualification (separate from measured gate outcomes)}",
              r"\begingroup\small\setlength{\tabcolsep}{3pt}\begin{longtable}{p{0.13\linewidth}p{0.37\linewidth}p{0.38\linewidth}}",
              r"\toprule", r"Gate & Evidence qualification & Blocking prerequisites \\", r"\midrule"]
    for rec in ledger.get("records",[]):
        q=latex_breakable(rec.get("qualification", "LEGACY_UNCLASSIFIED"))
        blockers=latex_breakable(", ".join(rec.get("blocked_by",[])) or "none")
        lines.append(latex_breakable(rec.get("gate_id","")) + " & " + q + " & " + blockers + " " + "\\\\")
    lines += [r"\bottomrule",r"\end{longtable}\endgroup"]
    import textwrap
    def wrapped_json(obj: dict) -> str:
        # Display-only wrapping; exact JSON remains in machine-readable manifest files.
        lines = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True).splitlines()
        return "\n".join("\n".join(textwrap.wrap(line, width=77, drop_whitespace=False,
                    replace_whitespace=False, break_long_words=True, break_on_hyphens=False) or [""])
                          for line in lines)
    lines += [r"\subsubsection*{Backend manifest}",
              r"\begingroup\footnotesize\begin{verbatim}", wrapped_json(backend),
              r"\end{verbatim}\endgroup", r"\subsubsection*{Source manifest}",
              r"\begingroup\footnotesize\begin{verbatim}", wrapped_json(src),
              r"\end{verbatim}\endgroup"]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines)+"\n", encoding="utf-8")


def _latex_engine(preferred: str | None = None) -> tuple[str, list[str]] | None:
    """Return an available LaTeX command without shell indirection."""
    import shutil
    import os
    wanted = (preferred or os.getenv("SST_LATEX_ENGINE") or "auto").lower()
    if wanted not in {"auto", "latexmk", "pdflatex", "xelatex", "lualatex"}:
        raise ValueError(f"unsupported TeX engine: {wanted}")
    candidates = ["latexmk", "pdflatex", "xelatex", "lualatex"] if wanted == "auto" else [wanted]
    for engine in candidates:
        executable = shutil.which(engine)
        if executable:
            args = ["-pdf"] if engine == "latexmk" else []
            return executable, args + ["-interaction=nonstopmode", "-halt-on-error"]
    return None


def compile_report_pdf(tex_path: str | Path, destination_pdf: str | Path, *, strict: bool = False, engine: str | None = None) -> dict[str, Any]:
    """Compile a falsifier TeX report and publish a clean PDF outside the output tree.

    The TeX file is compiled with its own directory as the working directory so
    relative ``\\input`` references (AUTO_RESULTS.tex, etc.) resolve naturally.
    Auxiliary files are isolated in a temporary build directory.  When no TeX
    engine is installed, strict=False records a non-fatal SKIP; strict=True raises.
    """
    import shutil, subprocess, tempfile
    tex=Path(tex_path).resolve(); dest=Path(destination_pdf).resolve()
    if not tex.is_file():
        msg=f"report TeX not found: {tex}"
        if strict: raise FileNotFoundError(msg)
        return {"success":False,"status":"SKIP","error":msg,"tex":str(tex),"destination":str(dest)}
    eng=_latex_engine(engine)
    if eng is None:
        msg="no LaTeX engine found (latexmk or pdflatex)"
        if strict: raise RuntimeError(msg)
        return {"success":False,"status":"SKIP","error":msg,"tex":str(tex),"destination":str(dest)}
    exe,base=eng
    with tempfile.TemporaryDirectory(prefix="sst_report_") as td:
        build=Path(td)
        cmd=[exe,*base]
        if Path(exe).stem.lower()=="latexmk":
            cmd += [f"-outdir={build}",tex.name]
            passes=1
        else:
            cmd += [f"-output-directory={build}",tex.name]
            passes=2
        logs=[]
        for _ in range(passes):
            cp=subprocess.run(cmd,cwd=str(tex.parent),text=True,capture_output=True)
            logs.append((cp.stdout or "")+(cp.stderr or ""))
            if cp.returncode!=0:
                msg="LaTeX compilation failed\n"+logs[-1][-12000:]
                if strict: raise RuntimeError(msg)
                return {"success":False,"status":"FAIL","error":msg,"engine":exe,"tex":str(tex),"destination":str(dest)}
        built=build/(tex.stem+".pdf")
        if not built.is_file():
            msg=f"LaTeX engine returned success but PDF was not created: {built}"
            if strict: raise RuntimeError(msg)
            return {"success":False,"status":"FAIL","error":msg,"engine":exe,"tex":str(tex),"destination":str(dest)}
        dest.parent.mkdir(parents=True,exist_ok=True)
        # x-mode is atomic: existing report evidence must never be overwritten.
        with dest.open("xb") as dst_fh, built.open("rb") as src_fh:
            shutil.copyfileobj(src_fh,dst_fh)
        return {"success":True,"status":"PASS","engine":exe,"tex":str(tex),"destination":str(dest),"size_bytes":dest.stat().st_size}


def publish_instance_report(instance_root: str | Path, tex_path: str | Path, *,
                            strict: bool = False, destination: str | Path | None = None,
                            engine: str | None = None) -> dict[str, Any]:
    """Publish an immutable run-scoped PDF beside the instance folder.

    The framework runner always supplies a deterministic run+phase destination.
    Direct standalone callers without a destination receive a fresh unique suffix.
    """
    from .output_policy import new_run_id, report_path
    root=Path(instance_root).resolve()
    dest=Path(destination) if destination is not None else report_path(root,new_run_id(),"BLIND")
    return compile_report_pdf(tex_path,dest,strict=strict,engine=engine)
