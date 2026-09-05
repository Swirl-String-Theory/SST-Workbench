from pathlib import Path
import shutil
from datetime import datetime
ROOT=Path(__file__).resolve().parent
stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
dest=ROOT/'archive'/f'pre_fresh_{stamp}'
moved=[]
for name in ('out','logs','analysis'):
    p=ROOT/name
    if p.exists() and any(p.iterdir()):
        dest.mkdir(parents=True,exist_ok=True); shutil.move(str(p),str(dest/name)); moved.append(name)
    p.mkdir(parents=True,exist_ok=True)
print('Archived:',', '.join(moved) if moved else 'nothing', '->',dest)
