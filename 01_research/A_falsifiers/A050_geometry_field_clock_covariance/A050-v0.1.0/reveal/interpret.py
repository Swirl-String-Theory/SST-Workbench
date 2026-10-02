import csv, json, sys
from pathlib import Path

def main():
    out=Path(sys.argv[1] if len(sys.argv)>1 else "SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs")
    result=json.loads((out/"blind_results.json").read_text())
    rows=[]
    with open(out/"scaling_results.csv",newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    lines=["# Revealed interpretation", "", f"Blind verdict: `{result['verdict']}`", "", "The blind run measured the following size-averaging exponents:", ""]
    for r in rows:
        lines.append(f"- {r['family']}: scalar={float(r['pressure_exponent']):.4f}, direct-vector={float(r['velocity_exponent']):.4f}, shuffled-null={float(r['null_exponent']):.4f}")
    lines += ["", "External reference comparison (not used by the blind verdict):", "", "- a three-dimensional short-range independent-cell limit gives finite-volume variance approximately proportional to R^-3;", "- a scalar field with sufficiently long-ranged inverse-distance covariance gives a much slower approximately R^-1 finite-volume suppression in a spherical-volume asymptotic regime.", "", "These are structural benchmarks only. Agreement does not establish an SST time mapping or an absolute physical scale."]
    (out/"revealed_interpretation.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))
if __name__=="__main__": main()
