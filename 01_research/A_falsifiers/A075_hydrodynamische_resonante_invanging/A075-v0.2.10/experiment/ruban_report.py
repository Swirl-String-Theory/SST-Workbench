"""Versioned, per-run PDF scientific diagnostic report (not a Framework gate)."""
from __future__ import annotations
import csv
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_deposition_report(out,qualification):
    out=Path(out)
    path=out/'A075-v0.2.9_RUBAN_DEPOSITION_REPORT.pdf'
    # Built-in Helvetica fallback for Windows, no bundled font redistribution.
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='A075Title',fontName='Helvetica-Bold',fontSize=17,leading=22,spaceAfter=12,textColor=colors.HexColor('#1a3653')))
    styles.add(ParagraphStyle(name='A075Head',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceBefore=10,spaceAfter=5,textColor=colors.HexColor('#1a3653')))
    styles.add(ParagraphStyle(name='A075Body',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=7))
    styles.add(ParagraphStyle(name='A075Small',fontName='Helvetica',fontSize=7.4,leading=10))
    P=lambda text:Paragraph(text,styles['A075Body'])
    H=lambda text:Paragraph(text,styles['A075Head'])
    doc=SimpleDocTemplate(str(path),pagesize=(210*mm,297*mm),leftMargin=17*mm,rightMargin=17*mm,
        topMargin=17*mm,bottomMargin=17*mm,title='A075-v0.2.9 Ruban Deposition Falsifier Diagnostic')
    story=[Paragraph('A075-v0.2.9 | Ruban Depositie',styles['A075Title']),
        P('<b>Falsifierdiagnostiek - Framework v1.1.0 - DEVELOPMENT ONLY</b>'),
        H('Onderzoeksvraag en nulhypothese'),
        P('Is de exact gereconstrueerde Ruban T(2,3)-geometrie bij B0=0.154 als eindig-brede, '
          'driedimensionale Euler-vorticiteit ruimtelijk voldoende opgelost om een zinvolle dynamische stabiliteitstest toe te laten?'),
        P('<b>H0:</b> zonder voldoende opgeloste torusdoorsnede, Gaussian-kern, initiele veldconvergentie '
          'en onafhankelijke topologietoets is stabiliteit niet gekwalificeerd. '
          '<b>H1:</b> een resolutie-gekwalificeerd beginveld kan doorgaan naar afzonderlijke dynamische tests; '
          'dit is nog geen bewijs van stabiele materiele knopen.'),
        H('Exacte model- en brondefinities'),
        P('Ruban: R0=1, B0=77/500, delta=1/20 en Lambda=7/5+ln(200)/2. '
          'De analytische controle gebruikt B0=8/25. Beide worden met dezelfde circulatie Gamma=2*pi, '
          'periodieke box, Euler-Gaussbreedte sigma en Euler-operator geinitialiseerd. '
          'Rubans filament-delta is niet de Euler-sigma. De ongepubliceerde auteursverstoring wordt niet gereconstrueerd.'),
        H('Methodologie en code-naar-wiskunde'),
        P('Het Euler-veld volgt uit wolk-in-cel-depositie van een gesloten polygonale circulatielijn, '
          'Fourierprojectie naar divergentievrije vorticiteit, Gaussische smoothing en Biot-Savart-inversie. '
          'Gemeten worden E=0.5*rho*integral(|u|^2 dV), '
          'Z=0.5*integral(|curl(u)|^2 dV), spectrale randfractie, projectie- en smoothingratio, '
          'en lokale vorticiteitsrug-offsets. Modelschalen zijn niet atomair gekalibreerd.'),
        H('Resultaten van deze specifieke run')]
    rows=list(csv.DictReader((out/'INITIAL_FIELD_MATRIX.csv').open()))
    tdata=[['Case','N','L','sigma','r0/dx','sigma/dx','E(0)','Z(0)']]
    for r in rows:
        tdata.append([('Ruban' if r['case']=='ruban' else 'B0=.32'),r['grid'],r['box'],r['sigma'],
           f"{float(r['rminor_cells']):.3f}",f"{float(r['sigma_cells']):.3f}",
           f"{float(r['energy']):.4f}",f"{float(r['enstrophy']):.4f}"])
    widths=[25*mm,13*mm,15*mm,18*mm,20*mm,24*mm,27*mm,26*mm]
    t=Table(tdata,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1a3653')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f5f8')]),
        ('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
    story.append(t)
    story.append(H('Kwalificatie en stopcriteria'))
    story.append(P('De voorgestelde screeningsdrempels zijn r0/dx >= 4, sigma/dx >= 3, '
                   'sigma/r0 <= 0.5 en minder dan 1% beginenergieverschil tussen opeenvolgende roosters. '
                   'Minimaal drie ruimtelijke niveaus en afzonderlijke kern-, tijd- en boxvariatie zijn vereist '
                   'voor latere fysische kwalificatie. Een geslaagde screening is nooit automatisch G12=PASS.'))
    count=sum(bool(x['all_three_geometric_ratios_satisfied']) for x in qualification['resolution_screening'])
    story.append(P(f'Van de {len(rows)} beginveldconfiguraties voldoen {count} aan alle drie de voorgestelde geometrische ratio-drempels. '
                   'Dit is geen topologie- of stabiliteitsclaim.'))
    story.append(P('<b>Gate ledger:</b> standalone diagnostiek uitgevoerd; Framework FREEZE/BASIC/FULL: '
                   'NOT_EXECUTED; fysieke Euler-stabiliteit en topologiebehoud: UNRESOLVED.'))
    figs=sorted(out.glob('*_xz_compare.png'))
    if figs:
        story.append(PageBreak())
        story.append(H('Vorticiteitsdoorsneden uit het werkelijke beginveld'))
        for f in figs[:4]:
            story.append(P(f.stem.replace('_',' ')))
            story.append(Image(str(f),width=166*mm,height=85*mm))
            story.append(Spacer(1,5*mm))
    story.append(H('Reproduceerbaarheid en volgende stappen'))
    story.append(P('Per-case JSON, ruwe NumPy-doorsneden, matrix-CSV, optionele marker- en veldrugtrajecten '
                   'en dit PDF-rapport zijn opgenomen in het versiearchief met SHA-256. '
                   'Eerst de depositie met hogere N en lagere sigma onderzoeken, daarna vaste-eindtijd '
                   'tijd-/ruimteverfijning, en pas na afzonderlijke topologiekwalificatie lange runs.'))
    def footer(c,d):
        c.saveState();c.setFont('Helvetica',7);c.setFillColor(colors.HexColor('#5c7182'))
        c.drawString(17*mm,11*mm,'A075-v0.2.9 | DIAGNOSTIC_ONLY | PHYSICAL_STABILITY_UNRESOLVED')
        c.drawRightString(193*mm,11*mm,f'Page {d.page}')
        c.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return path
