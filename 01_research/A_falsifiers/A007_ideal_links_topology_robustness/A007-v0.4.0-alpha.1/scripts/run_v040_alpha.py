#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sst_link_suite.closure_robustness import scan_sector_closure,borromean_sector_diagnostic


def main() -> int:
    parser=argparse.ArgumentParser(description="v0.4.0-alpha closure-robustness scan over v0.3.2 per-link ledgers.")
    parser.add_argument("campaign_dir")
    parser.add_argument("--output",default="outputs_v040_alpha")
    parser.add_argument("--ids",nargs="*")
    parser.add_argument("--resolution",type=int,default=8)
    parser.add_argument("--max-gradient-norm",type=float,default=1.0)
    args=parser.parse_args()
    campaign=Path(args.campaign_dir); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    files=sorted((campaign/"per_link").glob("*.json"))
    if args.ids: files=[p for p in files if p.stem in set(args.ids)]
    summaries=[]; points=[]; triple=[]
    for path in files:
        data=json.loads(path.read_text(encoding="utf-8"))
        for sector in data["sector_results"]:
            summary,rows=scan_sector_closure(sector,args.resolution,args.max_gradient_norm)
            common={"link_id":data["link_id"],"common_name":data.get("common_name"),"signs":sector["sign_string"]}
            summaries.append({**common,**summary})
            points.extend([{**common,**row} for row in rows])
            diag=borromean_sector_diagnostic(data["link_id"],sector["signs"])
            if diag: triple.append({**common,**diag})
    pd.DataFrame(summaries).to_csv(out/"closure_robustness.csv",index=False)
    pd.DataFrame(points).to_csv(out/"closure_simplex_points.csv",index=False)
    pd.DataFrame(triple).to_csv(out/"borromean_triple_sector_ledger.csv",index=False)
    report=[
        "# v0.4.0-alpha.1 closure robustness", "",
        f"- links scanned: **{len(set(row['link_id'] for row in summaries))}**",
        f"- sectors scanned: **{len(summaries)}**",
        f"- simplex resolution: **{args.resolution}**", "",
        "This alpha asks whether stationarity/stability survives a region of closure-weight space or only a fine-tuned point.",
        "Diagonal-Hessian inputs remain screening-only. The Borromean cubic sector label is catalog/speculative and is not a computed Milnor integral.",
    ]
    (out/"V040_ALPHA_REPORT.md").write_text("\n".join(report),encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
