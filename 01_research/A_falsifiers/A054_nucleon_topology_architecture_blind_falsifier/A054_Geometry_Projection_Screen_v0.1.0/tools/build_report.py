"""Generate the public PDF/Markdown report from the machine-readable FULL results."""
from __future__ import annotations
import collections, csv, hashlib, json, pathlib, statistics, secrets
from datetime import datetime, timezone
from report_fonts import register_portable_fonts
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'FULL';OUT.mkdir(exist_ok=True)
rows=[json.loads(x) for x in (OUT/'ROWS.jsonl').read_text().splitlines() if x.strip()]
sumry=json.loads((OUT/'RUN_SUMMARY.json').read_text())
prereg=json.loads((ROOT/'preregistration.json').read_text())
if sumry.get('completeness')!='FULL_CORPUS' or len(rows)!=50:
    raise SystemExit('Refusing publication of incomplete FULL campaign')
rows_by_arm={k:[a['arms'][k] for a in rows] for k in ('native','uniform300_no_relax')}
media=lambda key,arm:statistics.median(float(a[key]) for a in rows_by_arm[arm])
source_kinds=collections.Counter(a['source_kind'] for a in rows)
conv=[(x['case'],arm,x['arms'][arm]['hessian']['last_pair_rel_l2'],x['arms'][arm]['gradient']['stationarity']) for x in rows for arm in rows_by_arm if x['arms'][arm]['hessian'].get('converged')]
overlay=[json.loads(x) for x in (ROOT/'results'/'REFERENCE_OVERLAYS.jsonl').read_text().splitlines() if x.strip()]

# Avoid any ambiguity: not a scientific/physical verdict, only numerical screening.
ledger={
 'schema':'A054-GEOMETRY-DIAGNOSTIC-GATE-LEDGER-1',
 'framework':'SST_Falsifier_Framework_v1.0.7 external canonical; screening harness is standalone, not a framework-certified instance',
 'entries':[
 {'gate':'S0','name':'Source and parse integrity','status':'PASS','metrics':{'cases':len(rows),'expected':50,'source_errors':len(sumry['errors'])}},
 {'gate':'S1','name':'Projected objective idempotence','status':'NUMERICAL_DRIFT_OBSERVED','metrics':{'arms_over_threshold':sumry['projector_nonidempotent_arms_threshold_1e-10'],'total_arms':100,'diagnostic_threshold':1e-10}},
 {'gate':'S2','name':'Constrained Hessian numeric convergence','status':'98_UNRESOLVED_2_DIAGNOSTIC_CONVERGED','metrics':{'total_arms':100,'diagnostic_converged':2,'threshold':0.25}},
 {'gate':'S3','name':'Stationarity/line-search/ringdown state selection','status':'NOT_RUN_NOT_ADMITTED','metrics':{'stationarity_registered_limit':0.1}},
 {'gate':'S4','name':'Independent upstream provider and A057 transfer','status':'BLOCKED_NOT_QUALIFIED','metrics':{'qualified_independent_providers':0,'A057_transfers':0}}
 ]}
(OUT/'GATE_LEDGER.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

csvrows=[]
for x in rows:
 for arm,r in x['arms'].items():
  csvrows.append({'case':x['case'],'arm':arm,'projector_drift':r['rel_energy_drift_P1_P2'],'edge_cv':r['edge']['edge_cv'],
    'hessian_error':r['hessian']['last_pair_rel_l2'],'converged':r['hessian']['converged'],'sigma':r['gradient']['stationarity']})

msg=f"""# A054 Geometry Projection Screen v0.1.0 - FULL result

**Datum:** 12 oktober 2026. **Status:** NUMERICAL SCREENING, NO A054 ADMISSION, NO A057 TRANSFER.

## Uitgevoerde dataset

- 50/50 bestaande KnotPlot-censusgeometrieën gelezen (20 knots, 16 links/unlinks, 14 torusconfiguraties).
- 2 geometrische armen per bron: `native` en `uniform300_no_relax` (deterministische polygonale booglengte-interpolatie, geen `ago`).
- S0/S1/S2 numeriek uitgevoerd op alle 100 armen, met 2 Bishop-Fourier-modi per component en A054-analyseresolutie circa 96 beads.
- 100/100 armen: herhaalde projectie P(P(X)) verandert geometrie >1e-10 (relatieve RMS-diagnose, geen fysische gate).
- 2/100 Hessiaanproeven voldoen aan de vaste numerieke convergentievoorwaarde 0.25 inclusief sign class; 98/100 niet.
- De 2 geslaagde Hessiaanproeven behoren **beide tot 8_17** (native en uniform300_no_relax), maar hun stationariteit sigma is respectievelijk {conv[0][3]:.6f} en {conv[1][3]:.6f}. De geregistreerde stationariteitsdrempel is sigma <= 0.1. Dus nul geadmitteerde SST-toestanden.
- 5 historische E013-providerseeds en 2 KnotPlot `ago`-exports zijn in een separaat referentiepanel numeriek vergeleken (zie REFERENCE_OVERLAYS.jsonl); ook dit zijn geen onafhankelijke bevestigingsproviders.

## Geometriesamenstelling

| Corpus | Aantal |
|---|---:|
| KnotPlot knot-labels | {source_kinds['knot']} |
| KnotPlot link- en unlink-labels | {source_kinds['link']} |
| KnotPlot torus T(p,q) | {source_kinds['torus']} |

## Mediaanvergelijking

| Metriek | Native | Uniform300 zonder relaxatie |
|---|---:|---:|
| Bead-afstand-CV | {media('edge','native') if False else statistics.median(x['edge']['edge_cv'] for x in rows_by_arm['native']):.6f} | {statistics.median(x['edge']['edge_cv'] for x in rows_by_arm['uniform300_no_relax']):.6f} |
| Relatieve projectie-energiedrift | {media('rel_energy_drift_P1_P2','native'):.6g} | {media('rel_energy_drift_P1_P2','uniform300_no_relax'):.6g} |
| Hessian rel-Frobenius error | {statistics.median(x['hessian']['last_pair_rel_l2'] for x in rows_by_arm['native']):.6f} | {statistics.median(x['hessian']['last_pair_rel_l2'] for x in rows_by_arm['uniform300_no_relax']):.6f} |

**Interpretatie:** gelijkmatiger bead-afstand is inderdaad gerealiseerd, maar levert op dit corpus geen globale Hessiaanreparatie op. Sommige individuele resultaten verbeteren, andere verslechteren. De niet-gladde reach/projection branch is kandidaat voor verder onderzoek, **niet bewezen primaire oorzaak**.

## Dekking nog niet volledig

- Twistladder 3 t/m 10 crossings aanwezig. Twistknoop met 11 crossings niet geverifieerd of aangeleverd.
- De 18 Knot Atlas prime links met maximaal 7 crossings zijn als doelen opgenomen, maar KnotPlot-inventaris (11 relevante link labels 2-7 crossings; 2 unlink-controls en 3 hogere labels) is nog niet één-op-één via invarianten aan de Atlas gekoppeld.
- Geen originele KnotPlot `refine nbeads 300` zonder `ago` uitgevoerd. `uniform300_no_relax` is een transparant Python-alternatief, *niet exact KnotPlot-refine*.
- Geen volledige toestandselectie, dynamische ringdown of onafhankelijke providerreplicatie uitgevoerd.

## Reproduceerbaarheid

`run_all.cmd TEST`, `run_all.cmd` (BASIC), `run_all.cmd FULL` (100 Hessiaanvarianten), `run_all.cmd RESUME`.
Bronnen in `inputs/`, bronhashes in `SOURCE_FILES_SHA256.json`, geanalyseerde rijen in `results/FULL/ROWS.jsonl` en `SCREEN_RESULTS.csv`.
Het geauthenticeerde Google Drive-bronarchief `falsifier_census_v0.1.0_output.zip` is opgenomen met exacte SHA-256 `{sumry['source_census_zip_sha256']}`. Het is niet hetzelfde archief als de eerdere `original_zip_sha256` uit `census_targets.json`; die twee hashes mogen niet worden verward.

## Frameworkkwalificatie

Numerieke thresholds (EPS=0.015, Hessian <=0.25, stationarity <=0.1) ontleend aan de frozen A054-configuratie; **framework-v1.0.7 runtime is niet ingebed en zijn 56 regressietests zijn niet opnieuw uitgevoerd.** De hier uitgevoerde 7 lokale unit/parity-tests zijn een ander niveau. Deze diagnostische run is geen officiële A054-v0.5.2 FULL/CERTIFY of BLIND-campagne.

## Bronverwijzingen

- KnotPlot census v0.1.0 (oorspronkelijke TXT/KPF, Google Drive SST-Workbench).
- A054 v0.5.1 `geometry.py`, `dynamics.py`, `energy.py`, `configs/basic.json` als rekencontract-referenties.
- Knot Atlas, *Link table - up to seven crossings* voor de lijst van 18 linkdoelen.
"""
# Never overwrite a previously published report. The current run's data stays fixed.
publication_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
md=OUT/f'FALSIFIER_REPORT__{publication_id}.md'
md.write_text(msg,encoding='utf8')

# PDF - compact, inspectable, no external font bundled.
font_info=register_portable_fonts()
print('REPORT_FONT',font_info['provider'])
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleDV',fontName='DVB',fontSize=17,leading=23,spaceAfter=15))
styles.add(ParagraphStyle(name='H1DV',fontName='DVB',fontSize=12,leading=17,spaceBefore=13,spaceAfter=7))
styles.add(ParagraphStyle(name='BodyDV',fontName='DV',fontSize=8.4,leading=12.8,spaceAfter=6))
styles.add(ParagraphStyle(name='SmallDV',fontName='DV',fontSize=7.4,leading=10.8,spaceAfter=4))
styles.add(ParagraphStyle(name='CellDV',fontName='DV',fontSize=7.6,leading=10.6))
styles.add(ParagraphStyle(name='CellBoldDV',fontName='DVB',fontSize=7.6,leading=10.6))
P=lambda t,style='BodyDV':Paragraph(t,styles[style])
S=[]
S+=[P('A054 - Geometry Projection Screen v0.1.0','TitleDV'),
    P('Numerieke FULL-screening  |  12 oktober 2026  |  Geen A057-overdracht','BodyDV'),
    P('<b>50</b> native geometrieën. <b>100</b> geometriearmen. <b>100</b> Hessiaanproeven. <b>2</b> numeriek convergent; <b>0</b> fysisch geadmitteerde toestanden.','BodyDV'),
    P('Uitgevoerde dataset','H1DV')]

def table(data,widths=None):
    A=Table([[P(str(c),'CellBoldDV' if ri==0 else 'CellDV') for c in row] for ri,row in enumerate(data)],colWidths=widths,hAlign='LEFT',repeatRows=1)
    A.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eff4')),
        ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#d3dce2')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9fa')]),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
    return A
S.append(table([['Bronfamilie','Geometrieën','Analysevarianten'],['Knopen','20','40'],['Links + unlinks','16','32'],['Torus T(p,q)','14','28'],['Totaal','50','100']],[78*mm,43*mm,43*mm]))
S += [P('Resultaat per gate','H1DV'),
 table([['Gate','Resultaat','Interpretatie'],
 ['S0','PASS','50/50 bronnen gelezen; ASCII/KPF in pakket aanwezig'],
 ['S1','100/100 niet-idempotent','Meetbare P²(X) - P(X), relatieve geometriegrens 1e-10'],
 ['S2','2/100 numeriek convergent','Hessiaanverschil <=25% en consistent eigenwaardeteken'],
 ['S3','Niet uitgevoerd','Geen selectie, geen nonlinear ringdown'],
 ['S4','Geblokkeerd','Provideronafhankelijkheid niet bevestigd; A057=0']],[21*mm,48*mm,96*mm]),
 P('De twee numeriek convergente gevallen behoren beide tot 8_17 (native en 300 beads). Hun stationariteit (~1,69) overschrijdt de geregistreerde grens 0,1. Dit kwalificeert <b>geen</b> stabiele SST-toestand.','BodyDV'),
 P('Mediaanvergelijking','H1DV'),
 table([['Metriek','Native','300 beads zonder ago'],
 ['Bead spacing CV',f"{statistics.median(x['edge']['edge_cv'] for x in rows_by_arm['native']):.4f}",f"{statistics.median(x['edge']['edge_cv'] for x in rows_by_arm['uniform300_no_relax']):.4f}"],
 ['Proj.-energiedrift',f"{media('rel_energy_drift_P1_P2','native'):.6g}",f"{media('rel_energy_drift_P1_P2','uniform300_no_relax'):.6g}"],
 ['Hessiaan rel. fout',f"{statistics.median(x['hessian']['last_pair_rel_l2'] for x in rows_by_arm['native']):.4f}",f"{statistics.median(x['hessian']['last_pair_rel_l2'] for x in rows_by_arm['uniform300_no_relax']):.4f}"]],[72*mm,41*mm,51*mm])]

S += [PageBreak(),P('Wetenschappelijke interpretatie','TitleDV'),
 P('De 300-bead-arm verkleint de mediaan van de bead-spacing-CV, maar de Hessiaanconvergentie wordt corpusbreed niet gerepareerd. De huidige projectie bevat afzonderlijke geometrische stappen (periodieke polygonale herbemonstering en reach-normalisatie). Extra projectie veroorzaakt drift zonder fysieke evolutie.','BodyDV'),
 P('Definitie van de diagnose','H1DV'),
 P('P = N ∘ R; U<sub>c</sub>(q;X) = H(P[X + δX(q)]). De geteste Hessiaan gebruikt epsilon 0,015, epsilon/2 en epsilon/4, en laat alleen een consistente eigenwaardetekenklasse met een relatief matrixverschil van maximaal 0,25 toe.','BodyDV'),
 P('De diagnostische projectietoets vergelijkt P(X), P²(X) en P³(X), zowel op geometrische RMS-afstand als relatieve energiedrift. De grens 1e-10 betreft de detectie van numeriek verschil en is geen canonieke SST-natuurkundige gate.','BodyDV'),
 P('Voorbeelden van convergentie','H1DV')]
examples=['KNOT_3p1','KNOT_4p1','KNOT_5p2','KNOT_6p1','KNOT_8p17','TORUS_2p3','LINK_2p2p1','TORUS_6p21']
data=[['Geometrie','Native Hessiaan','300-bead Hessiaan','Toelating']]
for id_ in examples:
 row=next(a for a in rows if a['case']==id_)
 a=row['arms']['native']['hessian'];b=row['arms']['uniform300_no_relax']['hessian']
 data.append([id_,f"{100*a['last_pair_rel_l2']:.1f}%",f"{100*b['last_pair_rel_l2']:.1f}%",'NEE'])
S.append(table(data,[42*mm,45*mm,46*mm,31*mm]))
S.extend([P('Afzonderlijke historische controles','H1DV'),
 P('Ook 5 bevroren E013-referentiedragers en 2 KnotPlot-exports met build-script-relaxatie zijn op dezelfde diagnostische wijze gemeten. Hun vergelijking staat in REFERENCE_OVERLAYS.jsonl. Zij mogen niet als onafhankelijke bewijsbronnen worden geteld.','BodyDV'),
 P('Ontbrekende dekking','H1DV'),
 P('De twistladder door 10 kruisingen is aanwezig; het 11-kruisingenlid is niet met een gevalideerde KnotInfo/DT-naam aangeleverd. De 18 prime-links t/m 7 kruisingen zijn als doel geregistreerd, maar de KnotPlot-labels zijn nog niet tegen deze Atlas-identiteiten gevalideerd. De 50-delige census mag daarom niet worden beschreven als 18/18 gevalideerde Atlas-links.','BodyDV')])
S += [PageBreak(),P('Provenance, reproduceerbaarheid en grenzen','TitleDV'),
 P('1. Herkomst: KnotPlot census v0.1.0, zoals in Google Drive opgeslagen. Alle 50 native XYZ-TXT bestanden plus originele KPF-bestanden zijn in het bronarchief opgenomen. De ZIP-SHA-256 is '+sumry['source_census_zip_sha256']+'.','BodyDV'),
 P('2. De historische census-records verwijzen daarnaast naar een oorspronkelijke script-ZIP met een andere SHA-256. Dat is niet dezelfde bytestring als het hier gebruikte, geauthenticeerde outputarchief. Deze hashes blijven afzonderlijk geregistreerd.','BodyDV'),
 P('3. Numeriek: de energie-kernel, tangent/curvature/reach-regels en Bishop-modusconstructie zijn gecontroleerd tegen de bevroren A054 v0.5.1-referentiecode op meerdere een- en meercomponentgevallen. Verschillen waren nul of op FP64-afrondingsniveau.','BodyDV'),
 P('4. Framework: SST Falsifier Framework v1.0.7 is de canonieke bevroren referentie, maar de hier gebruikte harness is een zelfstandige diagnostische runner. De framework-v1.0.7 runtime en zijn 56 regressietests zijn NIET opnieuw uitgevoerd. De lokale screening heeft 7 unit- en pariteitstests met PASS.','BodyDV'),
 P('5. Geen KnotPlot-runtime gebruikt bij generatie van uniform300: die arm is uitsluitend deterministische booglengte-interpolatie in Python, zonder relaxatie. Ook is geen A054-optimizer uitgevoerd in deze screening.','BodyDV'),
 P('6. Geen fysieke stabiliteitspretenties: Hessiaan van deze gereduceerde surrogate is geen bewijs van vortex-Euler-stabiliteit. Er zijn geen onafhankelijke providers, geen ringdown-admissies en geen A057-handoffs.','BodyDV'),
 P('Run-commando’s (Windows)','H1DV'),
 P('<b>run_all.cmd TEST</b> - lokale unit/pariteitstests.<br/><b>run_all.cmd</b> - BASIC-pilot.<br/><b>run_all.cmd FULL</b> - alle 50 cases, beide armen, volledige gereduceerde Hessiaan.<br/><b>run_all.cmd RESUME</b> - hervat bestaande FULL-checkpoints.','BodyDV'),
 P('Data-artifacten','H1DV'),
 P('results/FULL/SCREEN_RESULTS.csv (100 armregels); ROWS.jsonl (alle numerieke schalen); RUN_SUMMARY.json; GATE_LEDGER.json; REFERENCE_OVERLAYS.jsonl. SHA256SUMS.txt documenteert de package-inhoud.','BodyDV'),
 P('Bronnen','H1DV'),
 P('KnotPlot census v0.1.0; A054 v0.5.1 geometry/dynamics/energy en BASIC-config; Knot Atlas, Link table - up to seven crossings (https://katlas.org/wiki/Link_table_-_up_to_seven_crossings).','SmallDV')]

def footer(c,doc):
 c.saveState();w,h=A4;c.setFont('DV',7.6);c.setFillColor(colors.HexColor('#66717b'))
 c.drawString(22*mm,13*mm,'SST-Workbench  |  A054 Geometry Diagnostic  |  v0.1.0')
 c.drawRightString(w-22*mm,13*mm,str(doc.page));c.restoreState()

pdf=OUT/f'A054_Geometry_Projection_Screen_v0.1.0__{publication_id}_FALSIFIER_REPORT.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=22*mm,rightMargin=22*mm,topMargin=20*mm,bottomMargin=21*mm,title='A054 Geometry Projection Screen v0.1.0',author='SST-Workbench diagnostic')
doc.build(S,onFirstPage=footer,onLaterPages=footer)
print('CREATED',pdf,'rows',len(rows),'overlays',len(overlay))
# Index is intentionally mutable metadata; published PDFs and Markdown are immutable.
(OUT/'REPORT_LATEST.json').write_text(json.dumps({
 'schema':'A054-REPORT-PUBLICATION-1', 'publication_id':publication_id,
 'pdf':pdf.name,'markdown':md.name,'font_provider':font_info['provider'],
 'source_protocol_sha256':sumry.get('protocol_sha256'),
 'source_census_sha256':sumry.get('source_census_zip_sha256'),
 'source_row_count':len(rows),'reference_overlays':len(overlay),
},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
