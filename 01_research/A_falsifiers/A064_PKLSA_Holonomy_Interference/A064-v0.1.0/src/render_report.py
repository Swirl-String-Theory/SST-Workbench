from __future__ import annotations
from pathlib import Path
import json
import csv
import sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'

def produce():
    r=json.loads((OUT/'run_results.json').read_text(encoding='utf-8'))
    pdf=OUT/'A064-v0.1.0_FALSIFIER_REPORT.pdf'
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TtlA',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=17,leading=21,spaceAfter=10))
    styles.add(ParagraphStyle(name='BodyA',parent=styles['BodyText'],fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=6))
    styles.add(ParagraphStyle(name='SmallA',parent=styles['BodyText'],fontName='Helvetica',fontSize=7.8,leading=10.5))
    styles.add(ParagraphStyle(name='HeadA',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=12,leading=15,spaceBefore=14,spaceAfter=6))
    styles.add(ParagraphStyle(name='MonoA',parent=styles['BodyText'],fontName='Courier',fontSize=8,leading=12,spaceAfter=7))
    def p(t,sty='BodyA'):
        return Paragraph(t,styles[sty])
    doc=SimpleDocTemplate(str(pdf),pagesize=(210*mm,297*mm),rightMargin=18*mm,leftMargin=18*mm,topMargin=19*mm,bottomMargin=18*mm)
    story=[]
    story.append(p('A064 | PKLSA Holonomy &amp; Interference Falsifier','TtlA'))
    story.append(p('v0.1.0 numerical pilot — 13 October 2026 | Qualification: GEOMETRY ONLY'))
    story.append(p('<b>Scientific boundary.</b> This report evaluates numerical Gauss linking / normalized filament circulation for registered KnotPlot geometry. It does <b>not</b> measure interference, infer a physical phase connection, prove Euler stability, or validate SST particle claims.'))
    sm=r['summary']
    story.append(p(f'<b>Computed result:</b> {sm["passed_required_gates"]} required numerical gates PASS, {sm["failed_required_gates"]} FAIL; {sm["unresolved_science_gates"]} qualification gates UNRESOLVED. Only one source provider.'))
    story.append(p('1. Method and analytic references','HeadA'))
    story.append(p('For disjoint oriented polygonal curves C_i and C_j, compute the Gauss integral with order-2 and order-4 tensor-product Gauss–Legendre quadrature:'))
    story.append(p('Lk(Ci,Cj) = (1 / 4pi) double_integral [ (dri x drj) . (ri-rj) / |ri-rj|^3 ].','MonoA'))
    story.append(p('If a filament produces an ideal incompressible inviscid Biot–Savart velocity with circulation Gamma, the circulation of that velocity along a disjoint closed test curve equals Gamma times the signed linking number. A finite regulator a modifies the denominator to (distance^2+a^2)^(3/2) and generally breaks exact integer quantization.'))
    story.append(p('The simulated interference baseline is P_toy = [1+cos(2pi q Lk)]/2 at the <b>assigned</b> q=1/2, not a derived SST coupling. All topological length coordinates are in native KnotPlot units, not metres.'))
    story.append(p('2. Verified source geometries','HeadA'))
    story.append(p('Source: registered PKLSA_KnotPlot_Native_Census v0.1.2 (SHA-256 checked), with E010 v0.3.1 release metadata. The v0.3.1 campaign has full_campaign_gate_pass=false, publication_ready_geometry_layer=false; its catalogue identity admission does not imply individual topology or dynamic certification.'))
    rows=[['Dataset / probe','Comp.','Gauss Lk','Integer error','P_toy']]
    for rec in r['records']:
        if rec['source'].startswith('synthetic'):continue
        rows.append([rec['source']+(' ('+str(rec['component_i'])+'-'+str(rec['component_j'])+')' if rec.get('component_i') is not None else ''),rec['kind'].replace('designed_meridian_probe','meridian')[:18],f'{rec["orderN"]:+.9f}',f'{rec["integer_error"]:.2e}',f'{rec["toy_probability"]:.3g}'])
    tbl=Table(rows,colWidths=[52*mm,38*mm,31*mm,30*mm,23*mm],repeatRows=1,hAlign='LEFT')
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#20304a')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),7.1),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('BOTTOMPADDING',(0,0),(-1,0),7),('TOPPADDING',(0,0),(-1,0),7),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#cdd6df')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(tbl)
    story.append(Spacer(1,3*mm))
    story.append(p('The three knot rows use <b>constructed meridians</b>. Every non-degenerate filament has a locally linked meridian: this verifies integration but <b>does not distinguish knot types</b>. Link 6.3.3 provides three distinct component pairs with signs +1, -1, +1. It is <b>not</b> treated as the Borromean L6a4 reference.'))
    story.append(p('3. Negative controls and numerical audit','HeadA'))
    story.append(p('Synthetic Hopf-link: absolute linking 1. Synthetic two separated circles: linking 0. Orientation reversal flips sign; simultaneous translation and cyclic start-point shifts preserve linking. Order 2 vs order 4 and regulator values 0, 0.025, 0.05 times the minimum input segment length are archived.'))
    story.append(p('4. Unresolved physical qualification','HeadA'))
    for g in r['gates']:
        if g['status']=='UNRESOLVED':story.append(p('<b>'+g['id']+'</b>: '+str(g['detail']).replace('&','&amp;'),'SmallA'))
    story.append(p('5. Next mandatory qualification experiment','HeadA'))
    story.append(p('Replace the assigned Z2 representation by a phase connection derived from the finite-core Euler / Kelvin linearized mode dynamics. Independently specify modes, dispersion, field normalization and initial conditions before calculating phase. Then compare the predicted time-resolved modal transfer with zero-connection and random-phase controls, across at least two independent PKLSA providers and mesh/core convergence.'))
    story.append(p('6. Sources','HeadA'))
    story.append(p('Saner et al. (2026), Nature Physics, doi:10.1038/s41567-026-03400-6; Gauss (1833), Zur mathematischen Theorie der electrodynamischen Wirkungen; Moffatt (1969), J. Fluid Mech. 35, 117–129, doi:10.1017/S0022112069000991; PKLSA native census v0.1.2 and E010 v0.3.1, source metadata in archive.','SmallA'))
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey)
        canvas.drawString(18*mm,12*mm,'A064-v0.1.0 | numeric pilot, not SST validation');canvas.drawRightString(192*mm,12*mm,f'{doc.page}');canvas.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print('Wrote',pdf)
    return pdf

if __name__=='__main__':produce()
