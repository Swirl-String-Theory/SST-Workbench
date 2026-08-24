"""Convert source KnotPlot catalog scripts and lock them to an approved discovery recipe."""
from __future__ import annotations
import argparse,re
from pathlib import Path
from catalog_recipe_support import load_recipe, inject, recipe_hash
MATRIX_PREFIX="KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"
CHECKPOINT_RE=re.compile(r"^echo CHECKPOINT (?P<label>\S+)[ \t]*$",re.M)
SAVE_RE=re.compile(r"^save[ \t]+(?P<path>\S+)[ \t]*$",re.M)
NBEADS_RE=re.compile(r"^(?:nbeads|refine nbeads) (?P<n>\d+)[ \t]*$",re.M)
TORUS_RE=re.compile(r"^torus\s+\d+\s+\d+\s+(?P<n>\d+)\s*$",re.M)
TRIAL_RE=re.compile(r"^trial_(\d+)k$")
def checkpoint_name(old):
    if old=='analytic_D1': return 'i00000'
    m=TRIAL_RE.match(old)
    if not m: raise ValueError(f'Unrecognized checkpoint label: {old!r}')
    return f"i{int(m.group(1))*1000:05d}"
def catalog_id_from_path(p): return p.parent.name
def transform_kpc(text,catalog_id,recipe=None):
    # Target runtime explicitly asks for refine nbeads N.
    out=NBEADS_RE.sub(r"refine nbeads \g<n>",text)
    out=CHECKPOINT_RE.sub(lambda m:f"echo CHECKPOINT {checkpoint_name(m.group('label'))}",out)
    def repl(m):
        old=m.group('path'); stem=Path(old).stem
        for lab in ('analytic_D1',*[f'trial_{i:03d}k' for i in range(1,16)]):
            suf='_'+lab
            if stem.endswith(suf): new=stem[:-len(suf)]+'_'+checkpoint_name(lab); break
        else: raise ValueError(f'Cannot map {old}')
        base=f"{MATRIX_PREFIX}/catalog/{catalog_id}/{new}"
        return f"save {base}.k float\ncoords {base}.txt"
    out=SAVE_RE.sub(repl,out)
    if recipe is not None: out=inject(out,recipe)
    return out
def iter_source_kpc(knots_dir):
    return [p for p in sorted(knots_dir.glob('*/build_*.kpc')) if p.name!='build_effort_active.kpc' and p.name.startswith(('build_knot_','build_link_','build_torus_'))]
def bead_count_from_text(text):
    m=NBEADS_RE.search(text) or TORUS_RE.search(text)
    if not m: raise ValueError('No bead count')
    return int(m.group('n'))
def write_catalog(knots_dir,matrix_dir,recipe):
    out=[]
    for src in iter_source_kpc(knots_dir):
        cid=catalog_id_from_path(src); dd=matrix_dir/'catalog'/cid; dd.mkdir(parents=True,exist_ok=True); dest=dd/src.name
        conv=transform_kpc(src.read_text(encoding='utf-8'),cid,recipe); dest.write_text(conv,encoding='utf-8',newline='\n'); out.append((cid,bead_count_from_text(conv),dest))
    return out
def write_run_catalog(matrix_dir,entries):
    p=matrix_dir/'97_run_catalog.kpc'; p.write_text('% Generated catalog includes\n'+'\n'.join(f"< {MATRIX_PREFIX}/catalog/{cid}/{dest.name}" for cid,_,dest in entries)+'\n',encoding='utf-8'); return p
def write_catalog_txt(matrix_dir,entries,recipe):
    h=recipe_hash(recipe); lines=['Catalog generated from approved MultiDynamics recipe','================================================','',f"Recipe: {recipe['recipe_id']}",f'Recipe SHA256: {h}','', 'Checkpoint mapping: analytic_D1 -> i00000; trial_001k..015k -> i01000..i15000','', 'Entries:']
    lines += [f'  {cid:16s} nbeads={b:4d} {d.name}' for cid,b,d in entries]
    p=matrix_dir/'CATALOG.txt'; p.write_text('\n'.join(lines)+'\n',encoding='utf-8'); return p
def main(argv=None):
    ap=argparse.ArgumentParser(); here=Path(__file__).resolve().parent
    ap.add_argument('--knots-dir',type=Path,default=here.parent/'knots'); ap.add_argument('--matrix-dir',type=Path,default=here); ap.add_argument('--recipe',type=Path,default=here/'catalog_recipe.json'); ap.add_argument('--allow-provisional',action='store_true')
    a=ap.parse_args(argv); recipe=load_recipe(a.recipe,a.allow_provisional); entries=write_catalog(a.knots_dir,a.matrix_dir,recipe); write_run_catalog(a.matrix_dir,entries); write_catalog_txt(a.matrix_dir,entries,recipe); print(f"Wrote {len(entries)} recipe-locked catalog scripts. Recipe={recipe['recipe_id']} SHA={recipe_hash(recipe)}"); return 0
if __name__=='__main__': raise SystemExit(main())
