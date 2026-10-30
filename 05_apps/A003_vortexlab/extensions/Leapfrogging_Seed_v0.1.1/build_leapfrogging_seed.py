#!/usr/bin/env python3
"""Reproducible two-coaxial-ring initial geometry; no time integration."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path

VERSION='v0.1.1'

def ring_points(radius,z,n):
    if n<12: raise ValueError('at least 12 points per ring required')
    return [(radius*math.cos(2*math.pi*i/n),radius*math.sin(2*math.pi*i/n),z)
            for i in range(n)]

def write_seed(out, radius=0.07, gap=0.03, gamma=0.002, core=0.0015, n=144):
    if radius<=0 or gap<=0 or gamma<=0 or core<=0 or gap<=3*core or radius<=3*core:
        raise ValueError('invalid dimensions or insufficient initial core clearance')
    out=Path(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f'Output not empty; refusing overwrite: {out}')
    out.mkdir(parents=True,exist_ok=True)
    components={"A":ring_points(radius,-gap/2,n),"B":ring_points(radius,gap/2,n)}
    records=[]
    for label,pts in components.items():
        xyz=out/f'leapfrog_ring_{label}_N{n}.xyz'
        xyz.write_text(''.join(f'{x:.17g} {y:.17g} {z:.17g}\n' for x,y,z in pts),encoding='utf-8')
        records.append({'component':label,'file':xyz.name,'n':n,'z':(-gap/2 if label=='A' else gap/2),
                        'orientation':'CCW_VIEWED_FROM_POSITIVE_Z','gamma_m2_per_s':gamma})
    # Native A003 XYZ-import uses blank lines as component separators.
    # These are TWO components of one simultaneous multi-filament scenario.
    combined=out/f'leapfrog_two_rings_N{n}.xyz'
    with combined.open('w',encoding='utf-8',newline='\n') as f:
        for label,pts in components.items():
            f.write(f'Component {label}:\n')
            for x,y,z in pts:
                f.write(f'{x:.17g} {y:.17g} {z:.17g}\n')
            f.write('\n')
    with (out/f'leapfrog_both_rings_N{n}.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['component','point_index','x_m','y_m','z_m'])
        for label,pts in components.items():
            for i,(x,y,z) in enumerate(pts):w.writerow([label,i,f'{x:.17g}',f'{y:.17g}',f'{z:.17g}'])
    manifest={
      'schema':'vortexlab-leapfrog-seed/1.0', 'version':VERSION,
      'scientific_status':'MATHEMATICAL_INITIAL_GEOMETRY_ONLY',
      'type':'two_closed_coaxial_unlinked_rings','topology':'two-component unlink (0_1 \\sqcup 0_1)',
      'note':'Two components in one interaction scenario do not constitute two independent topology seeds.',
      'unit_system':'SI','axis':'z','radius_m':radius,'axial_separation_m':gap,'core_radius_m':core,
      'gamma_each_m2_per_s':gamma,'circulation_signs':[1,1],'component_records':records,
      'nominal_dynamics':'regularized mutual Biot-Savart / inviscid zero-friction reference',
      'vortexlab_reference':'A003_vortexlab modular app: Import .xyz (session)',
      'native_combined_xyz':combined.name,
      'import_mode':'solo; all components; same circulation sign',
      'simulator_override_warning':'A003 rescales imported coordinates to P.R0 using their XY extent; set P.R0=0.070 m to preserve dimensions.',
      'expected_behavior':'LEAPFROGGING_CANDIDATE_NOT_PREVALIDATED',
      'no_claims':['no guaranteed repeated overtakes','no full Euler finite-core solution','no topology stability proof'],
    }
    (out/'SEED_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file()}
    (out/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in hashes.items()),encoding='utf-8')
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='leapfrog_custom_v0.1.1-outputs')
    p.add_argument('--radius',type=float,default=.07)
    p.add_argument('--gap',type=float,default=.03)
    p.add_argument('--gamma',type=float,default=.002)
    p.add_argument('--core',type=float,default=.0015)
    p.add_argument('--n',type=int,default=144)
    a=p.parse_args()
    m=write_seed(a.output,a.radius,a.gap,a.gamma,a.core,a.n)
    print(json.dumps({'path':str(Path(a.output).resolve()),'components':len(m['component_records']),
                      'points_per_component':a.n,'scientific_status':m['scientific_status']},indent=2))

if __name__=='__main__':main()
