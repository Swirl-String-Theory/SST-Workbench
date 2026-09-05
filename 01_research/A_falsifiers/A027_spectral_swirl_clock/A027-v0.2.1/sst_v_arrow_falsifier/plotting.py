from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def plot_outdir(outdir):
    outdir=Path(outdir)
    report=json.loads((outdir/"blind_results.json").read_text())
    for s in report["samples"]:
        p=outdir/f"spectrum_{s['sample_id']}.csv"
        if not p.exists(): continue
        df=pd.read_csv(p)
        model=s["models"]["linear"]["params"]
        x=np.linspace(df.abs_k_rad_m.min(),df.abs_k_rad_m.max(),300)
        y=model["intercept_rad_s"]+model["v_m_s"]*x
        fig=plt.figure(figsize=(7,5)); ax=fig.add_subplot(111)
        ax.scatter(df.abs_k_rad_m,df.omega_rad_s,s=20)
        ax.plot(x,y)
        ax.set_xlabel(r"$|k|$ [rad m$^{-1}$]")
        ax.set_ylabel(r"$\omega$ [rad s$^{-1}$]")
        ax.set_title(f"Blind dispersion: {s['sample_id']}")
        fig.tight_layout(); fig.savefig(outdir/f"dispersion_{s['sample_id']}.png",dpi=180); plt.close(fig)
