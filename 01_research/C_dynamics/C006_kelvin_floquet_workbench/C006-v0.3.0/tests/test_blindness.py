from pathlib import Path


def test_no_fine_structure_target_literal_in_solver_sources():
    root=Path(__file__).resolve().parents[1]
    forbidden=['7.297352','137.035','137.036']
    files=list((root/'sst_kelvin_workbench').glob('*.py'))+[root/'cpp'/'native.cpp']
    hits=[]
    for p in files:
        text=p.read_text(encoding='utf-8',errors='ignore')
        for f in forbidden:
            if f in text: hits.append((p.name,f))
    assert hits == []
