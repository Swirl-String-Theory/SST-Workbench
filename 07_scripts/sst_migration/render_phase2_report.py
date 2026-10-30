"""Create a Phase 2 report from fixed JSON evidence; no scientific recomputation."""
from pathlib import Path
import json
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '10_docs/migration_v110/phase2_20261026'


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def main():
    gates = read('gate_overview.json')
    fw = read('framework_integrity.json')
    registry = read('registry_reconciliation.json')
    providers = read('a054_provider_dependencies.json')
    patches = read('required_patches.json')['patches']
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'Helvetica'
    styles['Normal'].fontSize = 9.5
    styles['Normal'].leading = 13
    styles['Heading1'].fontSize = 18
    styles['Heading1'].leading = 22
    styles['Heading2'].fontSize = 12
    styles['Heading2'].leading = 15
    styles.add(ParagraphStyle('Digest', parent=styles['Normal'], fontName='Courier', fontSize=7, leading=10))
    story = []
    def text(content, style='Normal'):
        story.append(Paragraph(escape(str(content)), styles[style]))
        story.append(Spacer(1, 2.3 * mm))
    def page(title):
        if story:
            story.append(PageBreak())
        text(title, 'Heading1')
    def sub(title, content):
        text(title, 'Heading2')
        text(content)

    page('SST-Workbench - Phase 2')
    text('Framework v1.0.10 | Integrity & Admission Qualification', 'Heading2')
    text('Uitgevoerd op 26 oktober 2026. Broncontrole, metadataherstel en datasettoelating; geen volledige wetenschappelijke campagne.')
    sub('Besluit: drie pilots blijven geblokkeerd', 'Er zijn geen nieuwe falsifierversiemappen aangemaakt. Scheduled blijft uitgeschakeld. Historische manifesten en wetenschappelijke resultaten zijn niet gewijzigd. De bestaande wachtrij bevat nieuwe Phase 2-bewijsverwijzingen; haar vorige toestand is apart bewaard.')
    sub('Opgelost', 'De verzegelde RC2-distributie is teruggevonden en gecontroleerd. Alle 4.497 PKLSA-carrierrecords hebben overeenkomende ruwe en geometriehashes. Alle 47 E011-providerankers en 13 historische E013-manifesten sluiten aan. A011-geometrie/native pariteit en A065-datasetseals zijn gericht gecontroleerd.')
    sub('Nog nodig', 'De geinstalleerde frameworkbron en twee pilotpakketten hebben verklaarde byte-afwijkingen. A054 vereist daarnaast een v1.0.10-pin en sterkere runtime-manifestcontrole. Iedere opvolger vereist nog een afzonderlijke bronselectie, commitmentcontrole en begrensde smoketest. Fysische toelating blijft apart.')
    for check in gates['checks']:
        text(check['id'] + ': ' + check['status'])

    page('1. Authentieke frameworkbron')
    text('De RC2-ZIP is gekoppeld aan de bestaande CANONICAL_FREEZE.json via een exacte SHA-256. Dit is lokale herkomstverificatie tegen de freeze; er is geen onafhankelijke uitgevershandtekening geclaimd.')
    text('RC2-distributie: ' + fw['archive_path'])
    text('SHA-256: ' + fw['archive_actual_sha256'], 'Digest')
    text(str(len(fw['archive_entries'])) + ' interne manifestvermeldingen gecontroleerd: alle overeenkomend. De CANONICAL_FROZEN-ZIP heeft daarnaast 112 overeenkomende manifestvermeldingen.')
    text('CANONICAL_FROZEN-ZIP SHA-256: ' + fw['canonical_archive_sha256'], 'Digest')
    sub('DD32_FP32X2.md: afwijking verklaard, bytes niet hersteld', 'De lokale Markdown gebruikt $$ in plaats van de verzegelde LaTeX-delimiters en heeft een andere afsluitende newline. Formules, grenzen en numerieke kernels zijn daarmee niet veranderd. De exacte bytes blijven verschillend; het historische manifest is niet aangepast.')
    text('Verzegeld document: ' + fw['sealed_document_sha256'], 'Digest')
    text('Geinstalleerd document: ' + fw['installed_document_sha256'], 'Digest')
    text('Bewijs: framework_integrity.json, framework/DD32_FP32X2.diff en beide documentkopieen.')
    sub('Aanvullende pilotbroncontrole', 'Lokale Downloads-ZIPs voor A054-v0.5.1 en A065-v0.4.3 hebben intern respectievelijk 59 en 159 overeenkomende manifestvermeldingen. Hun ZIP-hashes, lokale varianten en verschillen zijn bewaard. Voor deze ZIPs was geen vooraf vertrouwde onafhankelijke distributiedigest beschikbaar.')
    text('A054: FALSIFICATION_PLAN.md en README.md verschillen alleen in formule-delimiters/EOF. A065: README_V043.md en docs/QUALIFICATION_V031.md hebben hetzelfde type opmaakverschil; triadic/report_tex.py verschilt uitsluitend door CRLF/LF. Dit verklaart de verschillen, maar vervangt de vereiste expliciete bronselectie niet.')

    page('2. Registratie en geometrie-integriteit')
    sub('73 canonieke A-families', 'De 75 fysieke familielocaties zijn teruggebracht tot 73 canonieke catalogusidentiteiten, zonder locaties te verwijderen of te verplaatsen. Er zijn 25 FAMILY.yaml-bestanden aangemaakt en 7 bestaande bestanden aangevuld. De A-secties van beide indices zijn gesynchroniseerd; andere domeinen en onderzoeksgroepen zijn structureel behouden.')
    text('A059...Falsifier2 blijft een aparte archieflocatie: dezelfde BLIND-ZIP, maar een afwijkende PDF blijft behouden. A067...BLIND is een byte-identieke duplicaatlocatie (33 bestanden). Geen van beide krijgt een tweede canonieke identiteit.')
    text('Nieuw geinventariseerde releases krijgen NOT_EVALUATED. Voor 25 families blijft een canonical-latest-keuze open, waaronder de reeds bestaande onversioneerde A003. Zeven familiegroepen hebben nog suffix-/werk-/rapportmappen die apart beoordeeld moeten worden. De exacte paden staan in P08 en registry_reconciliation.json.')
    sub('Volledige carrierh a s h-controle'.replace('h a s h', 'hash'), 'De audit omvat alle 2.227 productietopologiemappen, met 4.497 carrierrecords en 2.282 verschillende ruwe bronbestanden. Alle ruwe hashes en opnieuw berekende PKLSA-GEOMETRY-SHA256-v1-geometriehashes komen overeen. De bronbestanden zijn aan het einde opnieuw gehasht: nul wijzigingen.')
    text('Binnen de actieve view liggen 2.312 van deze records, verdeeld over 42 topologieen. De historische verdeling van 6 PASS en 36 FAIL blijft behouden. Deze topologiestatussen zijn niet opnieuw berekend of gepromoveerd.')
    text('De originele source-native E010-loader en zijn codehashes zijn vastgelegd. Er is geen Biot-Savart-, Euler-, high-resolution- of andere wetenschappelijke campagne gestart.')
    text('Bewijs: geometry_hashes.jsonl, geometry_integrity.json, source_stability.json en registry_before/.')

    page('3. Expliciete toelating per pilot')
    sub('A011 - geometrie en pariteit', 'Vier bestaande gerichte tests slagen met Python 3.14.3 en de aanwezige C++17-module: VECT/import-resampling, modeprojectie, rigide decompositie en Python/native pariteit. Er is niet opnieuw gebouwd. Bestaande toleranties zijn behouden: snelheid rtol=1e-11, atol=1e-12; writhe en afstand absoluut 1e-11.')
    a011 = read('A011_DATASET_ADMISSION.json')
    text(f"Het contract laat {a011['admitted_geometry_records']} records toe voor een geometrische diagnose en sluit {a011['rejected_geometry_records']} uit. Vereist: ruwe/geometriehashes overeenkomend, eindige coordinaten, bestaande literature_hard_gate_pass=true en L/Wr/kappa_rms als RESOLVED. Dit is een nieuw expliciet toelatingsvoorstel voor een toekomstige opvolger; geen wijziging aan historische wetenschappelijke gates.")
    text('Energie, zwaartekracht en thermodynamische sluiting vereisen afzonderlijke onafhankelijke fysische invoer. Een genormaliseerde curve levert geen fysische SI-lengteschaal.')
    sub('A054 - E013/E011-providers', 'Alle 47 providerankers en 13 historische manifesten zijn geverifieerd; slechts A054-v0.5.1 is momenteel enabled. Zes gerichte schema-, contract- en commitmenttests slagen. De lokale frameworklocator wijst echter nog naar v1.0.6. De runtime-loader controleert nog niet de E013-zelfhash en actuele E011-index/ankerbindingen.')
    text('E013 BASIC bevat een provider per topologie; dit kan uitvoering toetsen, maar geen cross-provider-sluiting. FULL/CERTIFY bevatten twee providers voor de zes geselecteerde knopen, maar slechts een voor L2a1. L2a1 blijft daarom uitgesloten van positieve cross-provider-claims zolang een tweede onafhankelijke bron ontbreekt.')
    sub('A065 - blind-seals en bestaande v1.0.10-bridge', 'D01/D02/D03: alle zeven datasetbestanden, seal-zelfhashes en globale koppelingen kloppen. De Fremlin-bron heeft overeenkomende ruwe en geometriehashes. Drie gerichte statische bridge-/precommit-tests slagen; de bestaande bridge pint al v1.0.10. Private targets zijn niet geopend en er is geen reveal uitgevoerd.')
    text('Historische filamenten en synthetische A003/Gaussian-volumes blijven geometrie-/methodediagnostiek. Fysische Euler/PKLSA-, kracht- en Casimir-claims blijven unresolved. De drie byte-afwijkingen in het actuele bronmanifest vereisen nog expliciete bronselectie.')

    for title, group in [('4. Benodigde patches - bron en adapters', patches[:5]), ('5. Benodigde patches - blind, invoer en wachtrij', patches[5:])]:
        page(title)
        for patch in group:
            text(patch['id'] + ' | ' + patch['kind'], 'Heading2')
            text('Stage: ' + patch['stage'])
            text(patch['action'])
            text('Acceptance: ' + patch['acceptance'])
        text('Exacte bestaande en toekomstige doelpaden, open canonical-latest-ID s en onbesliste mapnamen staan in REQUIRED_PATCHES.md en required_patches.json. Geen toekomstige versiemap is aangemaakt.')

    page('6. Validatie, grenzen en vervolg')
    text('25 gerichte tests slagen: 4 A011, 6 A054, 3 A065 statische checks, 8 queue/evidence-regressies en 4 bestaande hierarchy-buildertests. De tests kwalificeren de beschreven software- en integriteitscontroles, niet een volledige gemigreerde uitvoering of een wetenschappelijke hypothese.')
    for pilot, doc in gates['pilots'].items():
        text(pilot + ': migration=BLOCKED; migrated execution=NOT_RUN; science=NOT_RUN.', 'Heading2')
        text('Opgelost: ' + '; '.join(doc['resolved']))
        text('Open: ' + '; '.join(doc['remaining']))
    text('De persistente queue.json blijft scheduling_enabled=false en pilot_validated=false. Bestaande Phase 1-resultaten en PDF s zijn hashgecontroleerd en behouden. Alleen de mutable wachtrij is aangevuld; haar vorige SHA-256 en exacte vorige inhoud zijn bewaard. Het oude artefactmanifest is niet herschreven.')
    text('Vervolg: werk eerst bronselectie/integriteit en de genoemde pilotvoorwaarden af. Pas daarna kan een nieuwe sibling-versie worden aangemaakt en een afzonderlijke begrensde smoketest worden gepland. Volledige campagnes en Scheduled blijven buiten deze fase.')
    text('Machineleesbare hoofdbron: gate_overview.json. Toelatingscontracten: A011_DATASET_ADMISSION.json, A054_DATASET_ADMISSION.json en A065_DATASET_ADMISSION.json. Alle evidencepaden zijn relatief aan phase2_20261026/.')

    target = OUT / 'SST_Framework_v1.0.10_Phase2_Integrity_Admission_Report.pdf'
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(17*mm, 11*mm, 'SST-Workbench | Phase 2 | 26-10-2026 | geen wetenschappelijke statuspromotie')
        canvas.drawRightString(193*mm, 11*mm, str(doc.page))
    with target.open('xb') as stream:
        SimpleDocTemplate(stream, pagesize=(210*mm, 297*mm), leftMargin=17*mm, rightMargin=17*mm, topMargin=16*mm, bottomMargin=20*mm).build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


if __name__ == '__main__':
    main()
