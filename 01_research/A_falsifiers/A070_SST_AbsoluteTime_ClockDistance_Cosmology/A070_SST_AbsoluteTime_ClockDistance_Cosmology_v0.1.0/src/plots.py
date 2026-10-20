from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
f=ROOT/'results'/'clock_distance.csv'; a=np.genfromtxt(f,delimiter=',',names=True)
fig,ax=plt.subplots(figsize=(8,4.5));x=a['local_tau_Gyr']
ax.plot(x,a['fixed_absolute_distance'],label='Euclidean fixed separation')
ax.plot(x,a['fixed_radar_distance'],label='Radar distance, local clock')
ax.plot(x,a['fixed_rod_count_distance'],label='Rod-count distance, vortex core')
ax.set(xlabel='Local Swirl-Clock time (Gyr)',ylabel='Distance / original absolute separation',title='Clock and rod closure in affine Euler control')
ax.grid(alpha=0.25);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(ROOT/'figures'/'clock_rod.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4.5));ax.plot(x,a['z_radar_distance'],label='Radial direction z');ax.plot(x,a['x_radar_distance'],label='Transverse direction x');ax.set(xlabel='Local Swirl-Clock time (Gyr)',ylabel='Radar distance / initial distance',title='Incompressibility preserves volume, not isotropic separation');ax.grid(alpha=0.25);ax.legend();fig.tight_layout();fig.savefig(ROOT/'figures'/'anisotropy.png',dpi=180);plt.close(fig)
b=np.genfromtxt(ROOT/'results'/'optical_distance.csv',delimiter=',',names=True)
fig,axs=plt.subplots(2,1,figsize=(8,6),sharex=True)
axs[0].plot(b['redshift'],b['required_tau_constructed'],'o-',label='Opacity required to exactly mimic LCDM')
axs[0].plot(b['redshift'],b['tau_linear_training_fit'],'x--',label='One-parameter law, low-z trained')
axs[0].set(ylabel='Optical depth (dimensionless)',title='EdS luminosity distances vs LCDM synthetic benchmark');axs[0].legend(fontsize=8);axs[0].grid(alpha=.25)
axs[1].axhline(0,linewidth=.9);axs[1].plot(b['redshift'],b['mag_residual_1par'],'o-');axs[1].axhline(.02,linestyle=':',linewidth=.9);axs[1].axhline(-.02,linestyle=':',linewidth=.9);axs[1].set(xlabel='Redshift z',ylabel='Residual (mag)');axs[1].grid(alpha=.25);fig.tight_layout();fig.savefig(ROOT/'figures'/'opacity_holdout.png',dpi=180);plt.close(fig)
