import json, sys
from pathlib import Path

def main():
    root=Path(sys.argv[1])
    policy=Path(sys.argv[2])
    patterns=json.loads(policy.read_text(encoding="utf-8"))["patterns"]
    hits=[]
    for p in root.rglob("*"):
        if not p.is_file(): continue
        try: txt=p.read_text(encoding="utf-8",errors="ignore").lower()
        except Exception: continue
        for pat in patterns:
            if pat.lower() in txt:
                hits.append({"file":str(p.relative_to(root)),"pattern":pat})
    print(json.dumps({"root":str(root),"hit_count":len(hits),"hits":hits},indent=2))
    raise SystemExit(1 if hits else 0)
if __name__=="__main__": main()
