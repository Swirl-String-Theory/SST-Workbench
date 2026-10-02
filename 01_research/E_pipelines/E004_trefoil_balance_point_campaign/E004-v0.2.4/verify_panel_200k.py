from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))
def xyz(p):
    a=[]
    for l in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        v=[]
        for x in l.replace(","," ").split():
            try:v.append(float(x))
            except:pass
        if len(v)>=3:a.append(v[:3])
    return np.asarray(a,float)
def L(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def R(a):
    b=a-a.mean(0);return float(np.sqrt(np.mean(np.sum(b*b,axis=1))))
rows=[]
for s in D["panel"]:
    rr=f"XQHP__{s['id']}"
    a=xyz(ROOT/"out"/f"{rr}_i000000.txt");b=xyz(ROOT/"out"/f"{rr}_i200000.txt")
    dl=L(b)/L(a)-1;dr=R(b)/R(a)-1;e=.5*(dl+dr)
    rows.append({"id":s["id"],"t":s["t"],"E":e,"dL":dl,"dRg":dr})
cross=[]
for a,b in zip(rows[:-1],rows[1:]):
    if a["E"]==0 or a["E"]*b["E"]<0:
        f=0 if a["E"]==0 else -a["E"]/(b["E"]-a["E"])
        cross.append(a["t"]+f*(b["t"]-a["t"]))
ok=bool(cross)
payload={"format":"TREFOIL-V024-PANEL-200K-BRACKET-1.0","overall":"PASS" if ok else "FAIL","crossings":cross,"rows":rows}
(ROOT/"analysis/PANEL_200K_BRACKET.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
print("200K EXTENDED PANEL BRACKET",payload["overall"],"crossings",cross)
raise SystemExit(0 if ok else 5)
