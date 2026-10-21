#!/usr/bin/env python3
"""Generate *manual* KnotPlot preparation and finite-budget scripts.

Scripts are NOT run automatically. No default dynamics or slider parameters are
inferred. Requires a recorded local runtime calibration of close and max-dr.
Only one-time preparation uses fitto mindist (per A058-v0.2.10); production
script reloads a physically distinct saved seed for which go-1 safety was
verified on the user's KnotPlot installation.
"""
import argparse, csv,hashlib,json
from pathlib import Path

def main():
    a=argparse.ArgumentParser()
    a.add_argument('release',type=Path)
    a.add_argument('--runtime',type=Path,required=True,
                   help='Local JSON with knotplot_version, close, max_dr, parameters_dump_sha256, host')
    a.add_argument('--emit-production',action='store_true',
                   help='Only after manual preconditioning & go-1 safety check')
    z=a.parse_args()
    cfg=json.loads(z.runtime.read_text())
    for field in ('knotplot_version','host','close','max_dr','parameters_dump_sha256'):
        if not cfg.get(field):raise SystemExit(f'Missing runtime calibration field {field}')
    close=float(cfg['close']);md=float(cfg['max_dr'])
    if not (0<md<close):raise SystemExit('Reject unsafe max_dr >= close')
    if len(cfg['parameters_dump_sha256'])!=64:raise SystemExit('Expected actual SHA256 of parameter dump')
    with (z.release/'manifest.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    scripts=z.release/'kpc_calibrated';scripts.mkdir(exist_ok=True)
    for r in rows:
        if r['status']!='STATIC_QA_PASS':continue
        key=r['id'];path=r['knotplot_locd']
        # One-time preparation and separate go-1 check, followed by explicit manual QA.
        # No parameter value is set. Fitting happens once before any production run.
        prep=('reset all\n'+f'load {path}\n'+'collision fast\n'+
              'parameters\n'+f'fitto mindist {1.05*close:.12g}\n'+
              f'save checkpoints/{key}_prepared.txt ascii\n'+
              f'coords checkpoints/{key}_prepared_coords.txt\n'+
              'go 1\n'+f'coords checkpoints/{key}_after_go1.txt\n'+
              'length\n')
        (scripts/f'{key}__01_PREP_AND_ONE_STEP.kpc').write_text(prep)
        if z.emit_production:
            # Deliberately staged not a single, blindly running 32768 script.
            # Must first verify 01 prep, saved file reloading, clearance and drift.
            rel=('reset all\n'+f'load checkpoints/{key}_prepared.txt\n'+
                 'collision fast\nparameters\n'+
                 'go 32\n'+f'coords checkpoints/{key}_i00032.txt\n'+
                 'go 96\n'+f'coords checkpoints/{key}_i00128.txt\n'+
                 'go 384\n'+f'coords checkpoints/{key}_i00512.txt\n'+
                 'go 1536\n'+f'coords checkpoints/{key}_i02048.txt\n')
            (scripts/f'{key}__02_512_2048_DIAGNOSTIC_ONLY.kpc').write_text(rel)
    note={'runtime_record_sha256':hashlib.sha256(z.runtime.read_bytes()).hexdigest(),
          'close_runtime':close,'max_dr_runtime':md,
          'generated_for':len(rows),'production_scripts_emitted':bool(z.emit_production),
          'manually_qualified_in_KnotPlot':False,
          'recommendation':'NO go until source roundtrip, 3D collision and manual preconditioning safety checks pass',
          'physics':'NONE','interpretation':'finite-iteration geometry only'}
    (scripts/'UNQUALIFIED.json').write_text(json.dumps(note,indent=2)+'\n')
    print('Campaign scripts written to',scripts,'-- manual execution required; no software run claimed')
if __name__=='__main__': main()
