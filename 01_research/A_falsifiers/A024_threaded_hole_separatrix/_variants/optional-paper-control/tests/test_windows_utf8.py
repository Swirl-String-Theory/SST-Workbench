from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_unicode_report_roundtrip(tmp_path):
    text = "median Δp(active-null); ΔR²(1/r - 1/r²)"
    out = tmp_path / "CONCLUSIONS.md"
    out.write_text(text, encoding="utf-8")
    assert out.read_text(encoding="utf-8") == text


def test_all_path_text_io_in_src_declares_encoding():
    missing = []
    for py in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"read_text", "write_text"}:
                continue
            if not any(k.arg == "encoding" for k in node.keywords):
                missing.append(f"{py.relative_to(ROOT)}:{getattr(node, 'lineno', '?')}:{node.func.attr}")
    assert not missing, "Missing explicit encoding: " + ", ".join(missing)
