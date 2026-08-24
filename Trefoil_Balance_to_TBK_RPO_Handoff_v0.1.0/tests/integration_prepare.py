from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile
import numpy as np

SRC=Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory() as td:
    ws=Path(td)/"SST-Workbench"; ws.mkdir()
    pkg=ws/SRC.name; shutil.copytree(SRC,pkg)
    broot=ws/"KnotPlot/Trefoil_Balance_Point_Campaign_v0.1.0"
    out=broot/"out"; out.mkdir(parents=True)
    design=json.loads((pkg/"reference/Trefoil_Balance_Point_Campaign_v0.1.0_balance_design.json").read_text())
    (broot/"balance_design.json").write_text(json.dumps(design,indent=2))
    n=300
    u=np.linspace(0,2*np.pi,n,endpoint=False)
    base=np.c_[np.cos(3*u)+2*np.cos(2*u), np.sin(3*u)-2*np.sin(2*u), -np.sin(3*u)]
    # Deterministic synthetic responses; not physics.
    sidx={s["id"]:i for i,s in enumerate(design["settings"])}
    for vi,v in enumerate(design["variants"]):
        for s in design["settings"]:
            k=sidx[s["id"]]
            for it in [0,25,100,500,1000,4000,10000]:
                rate=(k-4.5)*1e-5 + vi*2e-6
                scale=1.0 + rate*it/100.0
                a=base*scale
                np.savetxt(out/f"{v['id']}__{s['id']}_i{it:05d}.txt",a,fmt="%.17g")
    env=os.environ.copy()
    cp=subprocess.run([sys.executable,"bridge.py","prepare"],cwd=pkg,env=env,text=True,capture_output=True,timeout=60)
    print(cp.stdout,end="")
    if cp.returncode:
        print(cp.stderr); raise SystemExit(cp.returncode)
    for mode in ["selected","core","full_balance","all20"]:
        r=pkg/"prepared"/mode
        assert (r/"SELECTION_LOCK.json").is_file()
        pub=json.loads((r/"PUBLIC_ENTRIES.json").read_text())
        prv=json.loads((r/"PRIVATE_PROVENANCE.json").read_text())
        assert pub and prv
        for e in pub:
            assert set(e)=={"source","kind","topology_class","canonical_id","input_file","raw_sha256"}
            assert e["source"].startswith("BALX_")
            assert "K31" not in e["source"] and "T23" not in e["source"]
        assert len(list((r/"canonical_300").glob("*.txt")))==len(pub)
    assert len(json.loads((pkg/"prepared/core/PUBLIC_ENTRIES.json").read_text()))==8
    assert len(json.loads((pkg/"prepared/full_balance/PUBLIC_ENTRIES.json").read_text()))==10
    assert len(json.loads((pkg/"prepared/all20/PUBLIC_ENTRIES.json").read_text()))==20
    cp=subprocess.run([sys.executable,"bridge.py","verify-lock","--mode","selected"],cwd=pkg,text=True,capture_output=True,timeout=20)
    print(cp.stdout,end="")
    assert cp.returncode==0
    print("SYNTHETIC PREPARE INTEGRATION PASS")
