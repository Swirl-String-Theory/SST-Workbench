from __future__ import annotations
import argparse,csv,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("summary_json"); ap.add_argument("--out",required=True); args=ap.parse_args(); obj=json.loads(Path(args.summary_json).read_text(encoding="utf-8")); rows=obj.get("rows",[])
    lines=["# 5_Maxwell SST Reciprocal Falsifier — Unblinded Summary","",f"Cases: **{len(rows)}**",""]
    counts={k:sum(r.get("equilibrium_gate")==k for r in rows) for k in ("PASS","WARN","FAIL")}; lines.append(f"Equilibrium: PASS={counts['PASS']}, WARN={counts['WARN']}, FAIL={counts['FAIL']}")
    lines.append(f"Near-singular WARN: {sum(r.get('near_singular_gate')=='WARN' for r in rows)}")
    lines.append(f"Positive self-stress present: {sum(bool(r.get('positive_self_stress')) for r in rows)}")
    lines += ["","| case | RR residual | struts | rank | nullity | chi_KKT | sigma+/sigma_max | eq | singular |","|---|---:|---:|---:|---:|---:|---:|---|---|"]
    def fmt(x):
        if x is None:return ""
        if isinstance(x,float): return f"{x:.6g}"
        return str(x)
    for r in rows:
        lines.append("| {label} | {rr} | {st} | {rk} | {nu} | {chi} | {sr} | {eq} | {sg} |".format(label=r.get("label"),rr=fmt(r.get("rr_residual")),st=fmt(r.get("active_struts")),rk=fmt(r.get("rank")),nu=fmt(r.get("right_nullity")),chi=fmt(r.get("chi_kkt")),sr=fmt(r.get("sigma_ratio")),eq=r.get("equilibrium_gate") or "",sg=r.get("near_singular_gate") or ""))
    lines += ["","## Interpretation guard","","A failure of strict Maxwell reciprocity is not treated as a mechanical falsification. Maxwell explicitly distinguishes mechanical solvability from existence of a perfect reciprocal figure; redundant force diagrams may remain valid. The present package therefore tests equilibrium/rank/self-stress first and leaves strict dual-cell reciprocity as a separate geometric diagnostic.",""]
    Path(args.out).write_text("\n".join(lines),encoding="utf-8"); print(f"[5_Maxwell] report -> {args.out}")
if __name__=="__main__": main()
