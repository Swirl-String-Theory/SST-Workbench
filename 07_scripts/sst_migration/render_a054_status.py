"""Separate technical status PDF; scientific PDFs use the qualified framework."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'10_docs/migration_v110/a054_controlled_20261026'


def main():
    result=json.loads((OUT/'RESULT.json').read_text())
    gates=json.loads((OUT/'gate_overview.json').read_text())
    source=json.loads((OUT/'SOURCE_ADMISSION.json').read_text())
    schedule=json.loads((OUT/'SCHEDULE_RESUMED.json').read_text())
    latest=result['latest']
    target=Path(result['technical_report'])
    assert not target.exists()
    styles=getSampleStyleSheet()
    styles['Normal'].fontSize=10;styles['Normal'].leading=14
    styles['Heading1'].fontSize=18;styles['Heading1'].leading=23
    styles['Heading2'].fontSize=12;styles['Heading2'].leading=16
    styles.add(ParagraphStyle('Digest',fontName='Courier',fontSize=8,leading=11,spaceAfter=5))
    story=[]
    def text(s,style='Normal'):
        story.extend([Paragraph(escape(str(s)),styles[style]),Spacer(1,2.8*mm)])
    def page(title):
        if story:story.append(PageBreak())
        text(title,'Heading1')
    def section(title,body):text(title,'Heading2');text(body)
    def digest(label,value):
        text(label,'Heading2');story.append(Paragraph('<br/>'.join(escape(value[i:i+32]) for i in range(0,len(value),32)),styles['Digest']))
    page('A054-v0.6.0 | Gecontroleerde migratie')
    text('SST-Workbench - Framework v1.0.10','Heading2')
    text('Technisch statusrapport. Gebruikersopdracht van 26 oktober 2026; uitvoeringstijden en run-ID worden in UTC bewaard. Dit document vervangt het wetenschappelijke falsifierrapport niet.')
    section('Resultaat','De begrensde softwaremigratie en bron-/geometriesmoketest zijn geslaagd. A054-v0.5.1 is behouden. A054-v0.6.0 heeft een zelfstandige Windows-ingang en een tien pagina\'s tellend wetenschappelijk protocol-/falsifierrapport met de daadwerkelijk uitgevoerde gates.')
    for name,value in latest['gate_axes'].items():text(name+': '+str(value))
    section('Scheduled hervat','De bestaande terugkerende taak is ACTIVE en blijft gekoppeld aan dezelfde Work-chat. Het bestaande tijdstip is dagelijks 04:00 Europe/Amsterdam. Maximaal een falsifier per uitvoering; een exclusieve run-lock voorkomt overlap. De algemene campagnevrijgave en pilot_validated blijven gesloten.')
    section('Lokale toegang','Project: C:\\workspace\\projects\\SST-Workbench. Uitvoering via CPython 3.14 met NumPy, pytest en matplotlib, en PDF-compilatie via pdflatex. Geen nieuwe dependency of native rebuild nodig voor deze toelatingssmoke.')
    page('1. Bron- en datasettoelating')
    section('P02: expliciete bronselectie','De gebruiker heeft de oorspronkelijke v0.5.1-ZIP expliciet toegelaten voor een begrensde softwaremigratie. Alle 59 interne manifestvermeldingen en de ZIP-CRC zijn gecontroleerd. Er is geen onafhankelijke uitgevershandtekening beschikbaar; die beperking blijft zichtbaar. Private bronentries zijn uitsluitend gehasht, niet geinterpreteerd of overgenomen.')
    digest('Toegelaten oorspronkelijke bron-ZIP',source['archive_sha256'])
    section('Framework','Alle 112 bestanden van de eerder gekwalificeerde schone v1.0.10-bron sluiten aan op de bestaande bronpin. De bewaarde lokale documentvariant wordt niet als runtimebron gebruikt.')
    section('P04: runtimecontrole','Verplichte externe manifestpin, E013-zelfhash, geselecteerd aantal, E011-index en providerankers, unieke seed-joins, source-locator-joins, ruwe bronhashes en parsed geometriehashes worden gecontroleerd. De exacte E010-v0.3.1-parser en zijn 23 Python-bestanden plus productierelease zijn gepind.')
    section('Nieuwe E013-binding','De bestaande E013-selector heeft vijf actuele BASIC-carriers geselecteerd: 3_1, 5_2, 6_1, 4_1 en L2a1. Vier knopen hebben 4096 bronpunten; de link heeft twee componenten met samen 8192 punten. Er is een nieuwe lokale member-binding voor A054-v0.6.0 op stage 30.')
    section('Geen dubbele campagneleden','De nieuwe v0.6.0 is disabled voor globale E013-discovery. Het historische ingeschakelde v0.5.1-contract is ongewijzigd. De lokale, expliciete toelatingssmoke gebruikt alleen v0.6.0.')
    page('2. Tests, rapport en archief')
    section('Definitieve verificatie','Twee opeenvolgende zelfstandige run_all.cmd ADMISSION_SMOKE-uitvoeringen slaagden met elk 36 tests. De bron-, migratie-, uitvoerings-, rapportage-, packaging- en herhaalbaarheidsgates zijn afzonderlijk geregistreerd. De wetenschappelijke gate blijft NOT_RUN.')
    for row in gates['final_runs']:text('Run '+row['run_id']+' | PDF '+str(row['pages'])+' pagina\'s | exacte ledger-overeenkomst: PASS')
    section('Wetenschappelijk rapport','De bestaande frameworkgenerator levert wetenschapstekst en automatische resultaten. Alle 16 protocolmarkeringen zijn aanwezig, met hypothesen, symbolen/eenheden, negen geregistreerde vergelijkingen, codekoppelingen, numeriek protocol, bronmanifest, afzonderlijke gates, grafiek, interpretatie, referenties en uitvoerinstructies. De tien gerenderde pagina\'s zijn visueel gecontroleerd.')
    section('Inhoudscontrole','REPORT_DATA stemt exact overeen met de gate-ledger; bronmanifestpaden bestaan en hebben de toegelaten hashes. Framework-TeX is exact reproduceerbaar. ZIP-CRC, alle payloadhashes, SHA-256-sidecar en de bytegelijkheid van ingebedde/gepubliceerde PDF zijn geverifieerd. Eerdere publicaties en outputmappen blijven behouden.')
    section('Behouden diagnostiek','Een eerste concept had onjuist gebonden rapportbronpaden; dat is hersteld en met regressietests afgedekt. Een herhaaltest stopte terecht doordat veranderlijke publicatieverwijzingen in het conceptprotocol waren meegepind. Deze zijn uitgesloten en met een regressietest afgedekt. De conceptbronnen, protocollen, rapporten en foutlog zijn behouden; historische manifesten zijn niet aangepast.')
    page('3. Grenzen en volgende concrete stap')
    section('Wetenschappelijke uitvoer niet verricht','State selection, stationariteit, Hessian-convergentie, ringdown, C++/Python-pariteit, GPU-screening en reveal zijn niet uitgevoerd als wetenschappelijke gates. De beperkte numerieke unit tests gelden niet als verse wetenschappelijke campagne.')
    section('Providerbeperking','BASIC bevat een provider per geselecteerde topologie. Onafhankelijke providerconvergentie kan hiermee niet sluiten; de bekende L2a1-beperking blijft bestaan. STATIC_READY is geen DYNAMICS_READY of fysieke SST-certificering.')
    section('Volgende stap','Review een afzonderlijk begrensd budget en protocol voor native pariteit en state-selectiondiagnostiek. Beoordeel onafhankelijke providerdekking voordat enige cross-provider-claim kan worden gekwalificeerd. Een volledige campagne, wetenschappelijke statuspromotie of reveal vereist aparte vrijgave. Scheduled mag intussen alleen de reeds toegelaten controles/herstelwerkzaamheden uitvoeren.')
    digest('Definitief wetenschappelijk PDF',latest['report_sha256'])
    digest('Definitief resultaten-ZIP',latest['archive']['sha256'])
    digest('Nieuwe bronarchief-ZIP',result['source_archive_sha256'])
    text('Machineleesbare onderbouwing: a054_controlled_20261026/gate_overview.json en RESULT.json. De persistente wachtrij is atomair bijgewerkt; alle andere falsifierjobs, A011-uitvoer en A065-familiegegevens blijven behouden.')
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#CAD2DF'));canvas.line(22*mm,16*mm,188*mm,16*mm)
        canvas.setFont('Helvetica',8);canvas.drawString(22*mm,12*mm,'SST-Workbench | Technisch migratiestatusrapport | A054-v0.6.0')
        canvas.drawRightString(188*mm,12*mm,str(doc.page))
    SimpleDocTemplate(str(target),pagesize=(210*mm,297*mm),leftMargin=22*mm,rightMargin=22*mm,topMargin=20*mm,bottomMargin=22*mm,
        title='A054-v0.6.0 Controlled Migration Status',author='SST-Workbench').build(story,onFirstPage=footer,onLaterPages=footer)
    print(str(target))


if __name__=='__main__':main()
