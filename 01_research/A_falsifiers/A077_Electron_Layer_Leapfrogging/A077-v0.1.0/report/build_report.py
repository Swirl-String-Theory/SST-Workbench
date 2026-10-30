"""Make full LaTeX report from frozen text + generated result facts without mutation."""
import argparse,json,subprocess,tempfile,shutil,sys
from pathlib import Path

def latex_escape(s):
 return str(s).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('&',r'\&').replace('%',r'\%')

def build(root):
 root=Path(root).resolve();p=root/'report'/'FALSIFIER_REPORT.tex'
 output=root/'electron_layer_leapfrogging_v0.1.0-outputs'
 evidence=output/'RUN_SUMMARY.json'
 with tempfile.TemporaryDirectory(prefix='sst-report-') as tmp:
  t=Path(tmp);shutil.copy2(p,t/p.name)
  if evidence.exists():
   d=json.loads(evidence.read_text())
   same=d['scenarios']['same']['stats'];opp=d['scenarios']['opposite']['stats'];cpp=d.get('C++_CLI_comparison',{})
   notes=[r'\begin{center}\begin{tabular}{ll}\toprule Observation & Result\\\midrule',
    r'Same-sign geometric rank swaps & %d\\'%same['crossing_count'],
    r'Opposite-sign geometric rank swaps & %d\\'%opp['crossing_count'],
    r'Angular quadrature relative difference & %.3g\\'%d['refinement']['spatial_last_rel_error'],
    r'RK4 time refinement relative difference & %.3g\\'%d['refinement']['temporal_last_rel_error'],
    r'Native C++17 CLI L2 parity (if run) & %s\\'%(('%.3g'%cpp['relative_L2']) if cpp.get('executed') else 'NOT EXECUTED'),
    r'Physical spin-$1/2$ gate & UNRESOLVED\\',r'\bottomrule\end{tabular}\end{center}',
    r'Every reported rank exchange is geometrical only; no discrete energies, plasma jets or spinor dynamics were computed.']
   (t/'AUTO_RESULTS.tex').write_text('\n'.join(notes))
   try:
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    pts=json.loads((output/'same_trajectory.json').read_text())
    y=np.array(pts['r_z_normalized']);x=np.array(pts['t_normalized'])
    f,ax=plt.subplots(figsize=(8,3));ax.plot(x,y[:,1],label='ring 1');ax.plot(x,y[:,3],label='ring 2')
    ax.set_xlabel('dimensionless absolute time $t/t_0$');ax.set_ylabel('$z/R_0$')
    ax.legend();f.tight_layout();f.savefig(t/'ring_tracks.pdf');f.savefig(output/'ring_tracks.png',dpi=120);plt.close(f)
   except Exception as e:print('plot unavailable:',e,file=sys.stderr)
  try:
   subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','FALSIFIER_REPORT.tex'],cwd=t,capture_output=True,text=True,check=True,timeout=90)
   subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','FALSIFIER_REPORT.tex'],cwd=t,capture_output=True,text=True,check=True,timeout=90)
  except Exception as exc:
   print('PDF generation FAILED; see TeX source',exc)
   if (t/'FALSIFIER_REPORT.log').exists():print((t/'FALSIFIER_REPORT.log').read_text()[-3500:])
   raise
  dest=root.parent/(root.name+'_FALSIFIER_REPORT.pdf')
  if dest.exists():dest=root.parent/(root.name+'_FALSIFIER_REPORT_2.pdf')
  shutil.copy2(t/'FALSIFIER_REPORT.pdf',dest)
  return dest

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a=ap.parse_args()
 print(build(a.root))
