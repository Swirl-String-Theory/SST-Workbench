"""Make diagnostic plots from existing JSON; plotting never changes gate statuses."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parents[1]
p=r/'A075_Hydrodynamische_Resonante_Invanging_v0.2.1-outputs'/'science'
fig,axs=plt.subplots(2,1,figsize=(8.5,7.5),sharex=True)
for kind in ('0_1','3_1'):
    a=json.loads((p/f'{kind}_base_case.json').read_text())['timeseries']
    b=json.loads((p/f'{kind}_control.json').read_text())['timeseries']
    x=np.array([z['t'] for z in a]); y=np.array([z['E_window']-v['E_window'] for z,v in zip(a,b)])
    axs[0].plot(x,y,label=kind)
    F=np.array([z['rhs_flux'] for z in a]);E=np.array([z['E_window'] for z in a]);
    rerr=(np.diff(E)-.5*np.diff(x)*(F[1:]+F[:-1]))
    axs[1].plot(x[1:],rerr,label=kind)
axs[0].set_ylabel('Window-excess kinetic energy [J]')
axs[0].set_title('PREVIEW: donor has NOT been verified to depart; these curves are NOT capture')
axs[1].set_ylabel('Per-interval flux-ledger residual [J]')
axs[1].set_xlabel('Absolute evolution parameter t [s]')
for ax in axs:ax.grid(True,alpha=.2);ax.legend()
fig.tight_layout()
fig.savefig(p/'PREVIEW_DIAGNOSTICS.png',dpi=150)
plt.close(fig)
