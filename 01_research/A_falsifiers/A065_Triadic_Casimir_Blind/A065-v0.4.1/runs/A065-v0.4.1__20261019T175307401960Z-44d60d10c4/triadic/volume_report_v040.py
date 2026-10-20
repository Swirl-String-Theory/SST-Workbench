"""Conservative PDF report: numerical outcomes without physical PKLSA promotion."""
from __future__ import annotations
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def write_report(root,result):
    root=Path(root);out=root/'reports'/'VOLUME_EULER_V040_REPORT.pdf'
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError('V040_REPORT_ALREADY_EXISTS')
    c=canvas.Canvas(str(out),pagesize=A4)
    W,H=A4; y=H-46
    def line(v='',size=9,gap=15,bold=False):
        nonlocal y
        if y<65:
            c.showPage();y=H-52
        c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
        c.drawString(42,y,str(v)[:112]);y-=gap
    line('A065-v0.4.0  |  A003 volume and numerical Euler campaign',15,26,True)
    line('Result: '+result['status'],11,19,True)
    line('Scope: periodic 3D Euler IVP from an ASSUMED Gaussian filament initialization.',9)
    line('Not a source-native PKLSA Euler provider; no independent physical pressure holdout.',9,24)
    line('Precommit SHA-256: '+result['prereg_sha256'],7,20)
    line('Gates',12,20,True)
    for gid,st in result['gates'].items():line(gid+'   '+st)
    line('',9,13)
    tg=result['periodic_euler_solver_control']
    line('Independent solver numerical control: Taylor-Green',11,21,True)
    d=tg['audit'];line('Grid %s  T = %.5g  dt = %.5g  RK4 steps %s'%(tg['grid_n'],d['T'],d['dt'],d['steps']))
    line('Relative energy drift = %.4g'%d['relative_energy_drift'])
    line('div(u) RMS = %.4g'%d['div_u_rms'])
    line('RK4 dt-halving relative u difference = %.4g'%tg['temporal_u_relative'])
    line('Control outcome = '+tg['outcome'],9,23)
    if result['source_missing']:
        line('A003 ORIGINAL SOURCE NOT AVAILABLE HERE',11,20,True)
        line('Missing: '+result['source_missing'])
        line('The 48/64/96 A003 claim has NOT been executed. Use the original atlas on Windows.',9,24)
    for sid,item in result['geometries'].items():
        line('Source: '+sid,11,20,True)
        line('Verified A003 XYZ SHA-256 '+item['geometry_sha256'],8)
        line('Fixed: Gamma=1; Gaussian a=0.55; L=12; 200 source nodes; T=0.02',9)
        for v in item['records']:
            line('N=%s: admitted sections=%s; Euler energy drift %.3g; divergence %.3g'%(
                v['n'],v['section_admitted_count'],v['euler']['relative_energy_drift'],v['euler']['div_u_rms']))
        for p in item['grid_pairs']:
            line('%d -> %d, source omega %.3f%%, u %.3f%%, p %.3f%%'%(
                *p['grids'],100*p['source_field_relative']['omega'],100*p['source_field_relative']['u'],
                100*p['source_field_relative']['p']))
            line('      Euler omega %.3f%%, u %.3f%%, p %.3f%%'%(
                (100*p['euler_field_relative']['omega']),(100*p['euler_field_relative']['u']),
                (100*p['euler_field_relative']['p'])))
        line('VOLUME %s; EULER NUMERICS %s; PRESSURE GRID %s'%(
            item['volume_pass'],item['euler_numerics_pass'],item['pressure_grid_pass']),9,20)
    line('Interpretation',11,19,True)
    line('G38 and G42 test discretization consistency, not the correctness of Gaussian core physics.',9)
    line('G39 and G40 qualify Euler numerical time stepping, not the physical initial condition.',9)
    line('G41 remains UNRESOLVED until a separately provenance-certified PKLSA Euler source',9)
    line('and an independently derived/measured physical velocity/pressure field are provided.',9)
    c.save();return str(out)
