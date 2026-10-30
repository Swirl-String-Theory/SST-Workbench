"""Create a transparent, source-audited mathematical control report. Requires reportlab."""
from pathlib import Path
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent
out=ROOT/(ROOT.name+'-outputs')
data=json.loads((out/'GATE_LEDGER.json').read_text(encoding='utf-8'))
source=json.loads((out/'DATASET_E011_READONLY.json').read_text(encoding='utf-8'))
file=ROOT.parent/(ROOT.name+'_FALSIFIER_REPORT.pdf')
fontpath=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('DVS',str(fontpath)))
pdfmetrics.registerFont(TTFont('DVS-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='CoverTitleS',fontName='DVS-Bold',fontSize=20,leading=25,textColor=HexColor('#183c50'),spaceAfter=11))
styles.add(ParagraphStyle(name='SectionS',fontName='DVS-Bold',fontSize=12,leading=16,textColor=HexColor('#006f80'),spaceBefore=12,spaceAfter=6))
styles.add(ParagraphStyle(name='SubsectionS',fontName='DVS-Bold',fontSize=10,leading=14,textColor=HexColor('#183c50'),spaceBefore=8,spaceAfter=4))
styles.add(ParagraphStyle(name='BodyS',fontName='DVS',fontSize=8.6,leading=13.5,spaceAfter=6))
styles.add(ParagraphStyle(name='SmallS',fontName='DVS',fontSize=7.5,leading=11,spaceAfter=4))
styles.add(ParagraphStyle(name='TinyS',fontName='DVS',fontSize=6.75,leading=9))
styles.add(ParagraphStyle(name='CodeS',fontName='DVS',fontSize=8,leading=12,textColor=HexColor('#253749'),spaceBefore=3,spaceAfter=3))

p=lambda text,sty='BodyS':Paragraph(text,styles[sty])
S=[]
S.append(p('SST Topological Transport Certificate', 'CoverTitleS'))
S.append(p('Frozen-in transport, heliciteit en reconnection | STTC v0.1.0', 'SectionS'))
S.append(p('<b>Datum:</b> 29 oktober 2026 &nbsp;&nbsp; <b>Beslissing:</b> PASS_ANALYTIC_CONTROL_ONLY &nbsp;&nbsp; <b>Fysische conclusies:</b> NOT_EVALUATED', 'BodyS'))
S.append(p('Afgebakend zelfstandig prototype op basis van <i>Frozen-In Gravitational Fields</i> en <i>Reconnection of Gravitational Fields</i>. Er zijn geen bestaande SST-Workbench-falsifiers, catalogi of beschermde bronbestanden gewijzigd.','BodyS'))
S.append(p('1. Kernconcept (klassieke Euler-vloeistof)', 'SectionS'))
for line in [
'∂t v + (v·∇)v = −∇p/ρf,   ∇·v = 0,   ω = ∇×v',
'β = d(vᵢ dxⁱ);   (∂t + Lᵥ)β = 0',
'B = p/ρf + |v|²/2;   𝒜 = vᵢ dxⁱ − B dt;   ℱ = d𝒜',
'U = ∂t + vⁱ ∂ᵢ:   iᵤℱ = 0 ⇒ Lᵤℱ = 0',
'r = ∂t v − v×ω + ∇B;   ∂t ω = ∇×(v×ω) + ∇×r',
'dHω/dt = 2∫(r·ω)dV   (geen netto heliciteitsgrensflux).'
]: S.append(p(line,'CodeS'))
S.append(p('De exacte overeenkomst betreft <b>Lie-transport van tweevormen</b>. De tetrad-geïndexeerde gravitationele velden van de publicaties zijn niet bewezen identiek aan de fysieke vloeistofvorticiteit. De 3D Euler-vloeistof verklaart hiermee niet automatisch zwaartekracht.', 'BodyS'))
S.append(p('2. Wat betekent een niet-ideaal residu?', 'SectionS'))
S.append(p('Een lokale afwijking r ≠ 0 of ∇×r ≠ 0 is niet voldoende voor reconnection. Als r = ζ×ω + ∇χ met een geschikte <b>globaal gladde</b> ζ en χ, is transport door w = v + ζ mogelijk. Veldlijnconnectiviteit vereist een afzonderlijke 3D-topologietest; gladheid en niet-singulier transport moeten aantoonbaar zijn.', 'BodyS'))
S.append(p('Een exact negatief controlevoorbeeld is een viskeus afnemend Arnold–Beltrami–Childress-veld (ABC). Daarbij neemt heliciteit af, hoewel de richting van alle vorticiteitslijnen ongewijzigd blijft. Het voorbeeld ligt buiten de inviscide SST-hoofdaanname en wordt uitsluitend als detectorcontrole gebruikt.', 'BodyS'))
S.append(p('3. Testdekking en uitsluiting', 'SectionS'))
S.append(p('<b>20/20 manufactured analytical controls:</b> PASS. Dit zijn code-, algebra-, convergentie- en analytische baselinetests. Geen native C++- of volledig 3D-Euler-knooptest is uitgevoerd.', 'BodyS'))
S.append(p('<b>Wel getest:</b> spectrale ABC-curl/divergentie, onafhankelijke ruimtelijke eindige-differentieconvergentie, viskeuze heliciteitsbalans, vierde-orde RK4-temporele convergentie, gladde inductieslippage, Hopf-linking na affiene deformatiematrix, kinematische trefoil-Cauchy-flux en Minkowski-tetradrepresentatie.', 'BodyS'))
S.append(p('<b>Niet getest:</b> dynamische E011/E010-seeds, volledige finite-core Euler-dynamica, oneindige topologische persistentie, ruimtelijke/finiete-kernconvergentie voor echte knopen, Borromeaanse Milnor-invarianten, gravitationele voorspellingen of universele SST-klokken.', 'BodyS'))
S.append(PageBreak())
S.append(p('4. Reproduceerbaar testresultaat', 'SectionS'))
D=data['diagnostics']
metrics=[
('Analytische checks',str(len(data['tests']))+' / '+str(len(data['tests']))+' PASS'),
('Spectraal Beltrami-curl residu','%.3g'%next(x['value'] for x in data['tests'] if x['check']=='BELTRAMI_spectral_curl_residual')),
('Ruimtelijke convergentie', '3.9769 en 3.9942 (orde 2)'),
('RK4 temporele convergentie','16.4226 en 16.2098 (orde 4)'),
('ABC H(0)', '%.9f (dimensieloos)'%D['ABC_H0']),
('ABC H(0.7), viscositeit 0.1', '%.9f (dimensieloos)'%D['ABC_Ht']),
('Hopf Gauss-linking initieel','%.12f'%D['hopf_initial_link']),
('Hopf linking na det F=1','%.12f'%D['hopf_affine_link']),
('Trefoil Cauchy-fluxrelatiefout','%.3g'%D['trefoil']['max_flux_relative_error']),
('Minkowski vlakheid: metriekfout','%.3g'%D['flat_tetrad']['metric_error']),
]
def tab(rows,widths,header=True):
 t=Table([[p(str(c),'SmallS') for c in row] for row in rows], colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e6f0f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),0.7,HexColor('#b2cad5')),('LINEBELOW',(0,1),(-1,-1),0.24,HexColor('#d4e1e7')),('LEFTPADDING',(0,0),(-1,-1),7)]))
 return t
S.append(tab([('Controle','Waarde')]+metrics,[85*mm,85*mm]))
S.append(p('De ABC-heliciteit is berekend op het dimensieloze periodieke domein (2π)³. De niet-ideale afname is een <b>negatieve reconnection-controle</b>, geen aanwijzing voor topologische verandering.', 'SmallS'))
S.append(p('5. Werkelijk E011-bronarchief: statische controle', 'SectionS'))
S.append(p('<b>Bron:</b> E011/SKLSA v0.3.0, uit de gekoppelde Google Drive-projectmap. Het archief is read-only gebruikt.', 'BodyS'))
S.append(p('<b>SHA-256:</b> '+source['archive_sha256'], 'SmallS'))
S.append(p('<b>Eigen sidecar-hashcontrole:</b> '+('PASS' if source['external_sha256_verified'] else 'NOT_DONE')+'; ZIP-CRC en interne releasecontractcontrole: '+source['status']+'.', 'BodyS'))
S.append(p('<b>Omvang:</b> 47 provider-ankers, 431 primaire STATIC_READY-seeds, 45 geselecteerde topologieën. Dit zijn geen tijdafhankelijke Euler-trajecten.', 'BodyS'))
S.append(tab([
('Topologie','Gilbert Wr','KnotPlot Wr','E011 abs(Wr)-consensus'),
('3₁','−3.418353','+3.410598','AGREEMENT_STRONG'),
('5₂','+4.545653','+4.683738','AGREEMENT_STRONG'),
('6₁','−1.113694','+1.372473','AGREEMENT_WEAK'),
],[26*mm,37*mm,37*mm,70*mm]))
S.append(p('Het teken van Wr is afhankelijk van oriëntatie-/spiegelconventies; bronverschillen zijn geen bewijs voor fysieke pariteits- of chiraliteitsdynamica. Vooral 6₁ vereist een brongevoeligheidscontrole.', 'SmallS'))
S.append(PageBreak())
S.append(p('6. Exacte aansluiting op bestaande families', 'SectionS'))
rows=[('Familie','Werkende input of audit','Nieuwe read-only adapter'),
('A016-v0.2.2','P0–P2 Cauchy, H0–H4, X0','STTC_KELVIN; geen drempelwijziging'),
('A007-v0.4.0-alpha.1','linking, topo-sectoren','STTC_LINK; Milnor blijft TODO'),
('A037-v0.3.3','PC02 heliciteits-/pariteitscontrole','STTC_HELICITY_BALANCE'),
('A038-v0.5.1','PC04, operator-split remap','STTC_MATERIAL_TRAJECTORY'),
('A047 (inventaris)','Euler-/BKM-regulariteit','STTC_REGULARITY_PRECHECK'),
('E010/E011','geometriebron, STATIC_READY','STTC_SOURCE_ADMISSION'),
('A060-v0.3.0','post-run evidence-samenvoeging','STTC_EVIDENCE_JOIN')]
S.append(tab(rows,[45*mm,61*mm,64*mm]))
S.append(p('Geen bestaande tests zijn overschreven. De adapter sluit aan op resultaatvelden en source hashes; voor een echte koppeling ontbreken nu kwalificerende tijdtrajecten en gevalideerde native backendconvergentie.', 'BodyS'))
S.append(p('7. Vervolgtest met falsifieerbare stopcriteria', 'SectionS'))
for title,text in [
('G0 — Input/admissie','Exacte bronhashes, geometriecomponenten, units, BC, E011 carrier status en compiler/numerieke kernel vastleggen; inconsistentie => BLOCKED.'),
('G1 — Ring','Anker voor circulatie, flux en heliciteit; gescheiden ruimtelijke, temporele en kernconvergentie.'),
('G2 — Vrije trefoil','Echte finite-core evolutie van 3₁; volledig Euler-residu, materiaaltransport, writhe/twist en identiteitsbehoud.'),
('G3 — Achtergrond','Dezelfde trefoil met één en meerdere volledig teruggekoppelde achtergrondfilamenten; geen statisch geforceerde achtergrond.'),
('G4 — Discreet/continu','Roosterafstand d en circulatie Γ vergelijken met uniforme Ω=Γ/(2d²); gemiddelde vorticiteit is niet lokale equivalentie.'),
('G5 — Falsificatie','Indien echte 3D-linkidentiteit convergent verandert onder gladdere, nominale Euler-evolutie: controleer model/finiteness of falsify assumptions. Bij ontbrekende convergentie: UNRESOLVED, nooit PASS.')
]:
 S.append(p('<b>'+title+'</b> — '+text,'SmallS'))
S.append(p('8. Release-status en bronreferenties', 'SectionS'))
S.append(p('<b>RESEARCH_TRACK / UNASSESSED:</b> de gravitationele SST-interpretatie. <b>ORTHODOX:</b> Euler/Kelvin/Cauchy topologisch behoud onder gladheid. <b>DERIVED:</b> hierboven geteste kinematische en analytische controles.', 'BodyS'))
S.append(p('De framework v1.0.10-migratiedocumentatie van 26-10-2026 signaleert een bronmanifestafwijking en niet-gecertificeerde migratie. Geen nieuw catalogus-ID, familieversie of PASS-promotie volgt uit deze test.', 'BodyS'))
S.append(p('Asenjo, Winkler &amp; Comisso, <i>Frozen-In Gravitational Fields</i>, Phys. Rev. Lett. 136, 161401 (2026), doi:10.1103/6c4q-kx6f.', 'SmallS'))
S.append(p('Comisso &amp; Asenjo, <i>Reconnection of Gravitational Fields</i>, Phys. Rev. D 114, 084095 (2026), doi:10.1103/lmqy-pf9k.', 'SmallS'))
S.append(p('Newcomb (1958), <i>Motion of Magnetic Lines of Force</i>, Ann. Phys. 3, 347–385, doi:10.1016/0003-4916(58)90024-1. Moffatt (1969), <i>The Degree of Knottedness of Tangled Vortex Lines</i>, J. Fluid Mech. 35, 117–129, doi:10.1017/S0022112069000991.', 'SmallS'))


def footer(canvas,doc):
 canvas.saveState();canvas.setFont('DVS',7);canvas.setFillColor(HexColor('#617481'))
 canvas.drawString(20*mm,13*mm,'STTC v0.1.0  |  Analytical controls only  |  Not a physics certification')
 canvas.drawRightString(190*mm,13*mm,str(doc.page));canvas.restoreState()

SimpleDocTemplate(str(file),pagesize=(210*mm,297*mm),leftMargin=20*mm,rightMargin=20*mm,topMargin=18*mm,bottomMargin=19*mm,title='SST Frozen-In and Reconnection Bridge — Falsifier Report',author='STTC mathematical control suite').build(S,onFirstPage=footer,onLaterPages=footer)
print(str(file))
