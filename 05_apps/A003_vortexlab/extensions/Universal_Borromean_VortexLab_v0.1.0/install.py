#!/usr/bin/env python3
"""Safe additive installer for modular VortexLab apps/web. Never touches solver/data."""
from __future__ import annotations
import argparse,hashlib,shutil,sys
from pathlib import Path
SELF=Path(__file__).resolve().parent
FILES=[Path('apps/web/borromean.html'),Path('apps/web/src/borromean-builder.js'),Path('apps/web/src/borromean-page.js'),Path('apps/web/styles/borromean.css')]
LINK='<a id="bUniversalBorromean" href="./borromean.html" title="Drie onafhankelijk selecteerbare knopen op Borromeaanse drager" style="display:inline-flex;align-items:center;padding:4px 10px;border:1px solid var(--line);border-radius:5px;background:#13233A;color:#CFE8FF;text-decoration:none;font:inherit;font-size:11px;">Borromean Builder</a>'
CAT='<a href="./borromean.html">Borromean Builder</a>'
def shab(b):return hashlib.sha256(b).hexdigest()
def inject(filedata:bytes,anchor:bytes,addition:bytes):
    if addition in filedata:return filedata
    if filedata.count(anchor)!=1:raise RuntimeError('Navigation anchor missing or ambiguous')
    return filedata.replace(anchor,anchor+b'\n      '+addition,1)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True,help='.../05_apps/A003_vortexlab');p.add_argument('--check',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
 root=a.root.resolve();web=root/'apps/web';req=[web/'index.html',web/'catalog.html',web/'src/catalog-geometry.js',web/'data/ideal_knots_data.js',web/'data/fourier_knots_data.js',web/'data/knotplot_knots_data.js',web/'data/twist_knot_data.js',web/'vendor/three.min.js']
 missing=[x for x in req if not x.is_file()]
 if missing:raise FileNotFoundError('Missing VortexLab modular files: '+str(missing))
 oldindex=(web/'index.html').read_bytes();oldcat=(web/'catalog.html').read_bytes()
 newindex=oldindex
 # Insert before the exact existing catalog control. Anchor is a short, unique byte sequence.
 anchor=b'      <a id="bCatalog"'
 if LINK.encode() not in oldindex:
  if oldindex.count(anchor)!=1:raise RuntimeError('index.html catalog navigation not uniquely found')
  newindex=oldindex.replace(anchor,b'      '+LINK.encode()+b'\n'+anchor,1)
 anchor=b'<a href="./index.html">'
 if CAT.encode() not in oldcat:
  if oldcat.count(anchor)!=1:raise RuntimeError('catalog.html navigation anchor not uniquely found')
  newcat=oldcat.replace(anchor,CAT.encode()+b'\n      '+anchor,1)
 else:newcat=oldcat
 for rel in FILES:
  src=SELF/rel;dst=root/rel
  if dst.exists() and dst.read_bytes()!=src.read_bytes():raise FileExistsError('Modified extension file already exists; refuse overwrite: '+str(dst))
 print('CHECK PASS: VortexLab modular sources exist; all extension targets safe.')
 print('Nav: index.html',shab(oldindex),'→',shab(newindex),'catalog.html',shab(oldcat),'→',shab(newcat))
 print('New files:',*(str(x) for x in FILES),sep='\n - ')
 if not a.apply:print('No changes made. To install, rerun with --apply.');return
 for path,srcdata,newdata in [(web/'index.html',oldindex,newindex),(web/'catalog.html',oldcat,newcat)]:
  if srcdata!=newdata:
   bak=path.with_name(path.name+'.pre-universal-borromean-v0.1.0.bak')
   if bak.exists() and bak.read_bytes()!=srcdata:raise FileExistsError('Refuse to replace a different navigation backup '+str(bak))
 # All preflights finished, now copy & add links.
 for rel in FILES:
  dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():shutil.copy2(SELF/rel,dst)
 for path,srcdata,newdata in [(web/'index.html',oldindex,newindex),(web/'catalog.html',oldcat,newcat)]:
  if srcdata!=newdata:
   bak=path.with_name(path.name+'.pre-universal-borromean-v0.1.0.bak')
   if not bak.exists():bak.write_bytes(srcdata)
   path.write_bytes(newdata)
 print('APPLY PASS: Open apps/web/borromean.html (or click Borromean Builder).')
if __name__=='__main__':
 try:main()
 except Exception as exc:print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(2)
