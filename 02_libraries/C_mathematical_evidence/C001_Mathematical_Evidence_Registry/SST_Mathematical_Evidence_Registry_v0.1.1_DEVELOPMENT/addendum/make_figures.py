"""Optional matplotlib plot regeneration; images are illustrative mathematical diagnostics."""
from pathlib import Path
import math,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from math_models import *
F=Path(__file__).resolve().parents[1]/'figures';F.mkdir(exist_ok=True)

fig,ax=plt.subplots(figsize=(7.4,3.55))
for name,gam in [('SST canon circulation (defined)',gamma_sst()),('Historical h/m_e prescription',gamma_h_over_me())]:
    spec=kelvin_spectrum(gam,2*math.pi*A0,R_C,10)
    ax.plot([x['m'] for x in spec],[x['hbar_omega_eV'] for x in spec],marker='o',label=name)
ax.set_yscale('log');ax.set_xlabel('Periodic mode index m (not PKLSA eigenmode)');ax.set_ylabel('hbar * omega (eV; conditional mapping)');ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout()
fig.savefig(F/'kelvin_contract_comparison.png',dpi=165);plt.close(fig)

fig,ax=plt.subplots(figsize=(7.4,3.55))
T=np.logspace(0,7,250)
for gap in [.001,.01,1.,500.]:
    ax.plot(T,[boson_heat_capacity_J_per_K(gap*E_CHARGE,float(t))/KB for t in T],label=f'Assumed gap {gap:g} eV')
ax.set_xscale('log');ax.set_yscale('log');ax.set_ylim(1e-20,2);ax.set_xlabel('Temperature T (K)');ax.set_ylabel('C/kB (one quantized harmonic mode)')
ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout()
fig.savefig(F/'conditional_bose_heat_capacity.png',dpi=165);plt.close(fig)

fig,ax=plt.subplots(figsize=(7.4,3.55))
ns=np.linspace(0,10,600)
samples=[transfer_state(t*1e-9,1.,1e9,9e9,1/(30e-9),.6) for t in ns]
for label,col in [('Swirl stored energy','E_swirl_J'),('Received mode energy','E_em_J'),('Accumulated loss','E_loss_J')]:
    ax.plot(ns,[x[col] for x in samples],label=label)
ax.set_xlabel('Time (ns)');ax.set_ylabel('Energy (J), toy parameters');ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout()
fig.savefig(F/'two_sector_energy_balance.png',dpi=165);plt.close(fig)
print('figures generated')
