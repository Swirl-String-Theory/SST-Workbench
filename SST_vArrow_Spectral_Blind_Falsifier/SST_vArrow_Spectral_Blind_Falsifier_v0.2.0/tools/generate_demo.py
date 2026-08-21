from pathlib import Path
import numpy as np, pandas as pd

root=Path(__file__).resolve().parents[1]
out=root/"campaigns"/"demo_spectrum"; out.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(42)
# Deliberately non-target synthetic speed; validates estimator without leaking the unblind target.
v_demo=8.0e5
rows=[]
for sample,res in [("demo_N300",300),("demo_N600",600),("demo_N1200",1200)]:
    k=np.arange(1,21)*2.5e7
    omega=v_demo*k*(1+rng.normal(0,0.003,len(k))) + 1.5e10
    power=np.exp(-np.arange(len(k))/10)+0.05
    df=pd.DataFrame({"k_rad_m":k,"omega_rad_s":omega,"power":power})
    fn=f"{sample}.csv"; df.to_csv(out/fn,index=False)
    rows.append({"sample_id":sample,"family_id":"demo_family","topology":"BLINDED_A","resolution_n":res,"input_type":"spectrum_csv","path":fn,"core_radius_m":1.0e-15})
pd.DataFrame(rows).to_csv(out/"manifest.csv",index=False)
print(out)
