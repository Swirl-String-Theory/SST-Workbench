from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_public_tree_has_no_forbidden_terms():
    terms=[x.strip().casefold() for x in (ROOT/"private/blind_forbidden_terms.txt").read_text().splitlines() if x.strip()]
    suffixes={".py",".json",".md",".txt",".toml",".cmd",".cpp",".h",".hpp",".tex",".csv"}
    hits=[]
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in suffixes: continue
        rel=p.relative_to(ROOT)
        if any(part.casefold() in {"private","revealed","reveal_private"} for part in rel.parts): continue
        text=p.read_text(errors="ignore").casefold()
        for term in terms:
            if term in text: hits.append((rel.as_posix(),term))
    assert hits==[]
