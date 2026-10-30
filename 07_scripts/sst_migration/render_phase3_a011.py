"""Standalone PDF from fixed A011 v0.4.0 evidence; never reruns measurements."""
from pathlib import Path
import hashlib
import json
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / '01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.4.0/1_Maxwell_SST_Kinetic_Falsifier_v0.4.0-outputs'


def read(name):
    return json.loads((RESULT / name).read_text(encoding='utf-8'))


def main():
    summary = read('RUN_SUMMARY.json')
    env = read('ENVIRONMENT.json')
    source = read('SOURCE_PROVENANCE.json')
    ledger = read('GATE_LEDGER.json')['records']
    seeds = read('SELECTED_SEEDS.json')['seeds']
    results = read('GEOMETRY_RESULTS.json')
    parity = read('PARITY_RESULTS.json')
    tests = read('TEST_RESULTS.json')
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 9.5
    styles['Normal'].leading = 13
    styles['Heading1'].fontSize = 18
    styles['Heading1'].leading = 22
    styles['Heading2'].fontSize = 12
    styles.add(ParagraphStyle('Digest', parent=styles['Normal'], fontName='Courier', fontSize=7, leading=10))
    story = []
    def text(value, style='Normal'):
        story.append(Paragraph(escape(str(value)), styles[style]))
        story.append(Spacer(1, 2.5*mm))
    def page(title):
        if story:
            story.append(PageBreak())
        text(title, 'Heading1')
    def heading(title, content):
        text(title, 'Heading2')
        text(content)
    def table(headers, rows, widths):
        data = [[Paragraph(escape(str(v)), styles['Normal']) for v in row] for row in [headers] + rows]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eeeeee')), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LINEBELOW', (0,0), (-1,0), 0.5, colors.grey), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 5)]))
        story.append(t)
        story.append(Spacer(1, 4*mm))

    page('A011 v0.4.0 - gecontroleerde migratie')
    text('SST-Workbench Framework v1.0.10 | Phase 3A / 3B', 'Heading2')
    text('26 oktober 2026 | ' + summary['run_id'])
    heading('Besluit', 'Frameworkbron: PASS (112/112). A011-migratie: PASS_GEOMETRY_ADAPTER. Begrensde uitvoering: PASS_BOUNDED_GEOMETRY_SMOKE. Wetenschappelijke status: UNRESOLVED_MISSING_PHYSICAL_INPUTS. Geen nieuwe fysische kwalificatie of statuspromotie.')
    heading('Uitvoering', f"Eerst {tests['counts_passed']['framework_targeted_tests']} gerichte frameworktests en {tests['counts_passed']['a011_tests']} A011-tests, alle geslaagd. Daarna drie toegelaten PKLSA-curves van elk 300 bronpunten, op N=64 en N=128. CPU, een thread, geen GPU, geen willekeurige selectie, geen reveal. Meetduur circa {summary['duration_seconds']:.2f} seconden; proceslimiet 120 seconden.")
    heading('Uitvoeromgeving', env['python'] + '; numpy ' + env['numpy'] + '; ' + env['platform'])
    text('Python: ' + env['executable'])
    text('Native: ' + env['native_backend']['version'] + '. Bestaande cp314-module uit v0.3.1 byte-identiek overgenomen; geen nieuwe compilerbuild. Broncode en het historische buildstamp zijn gecontroleerd.')
    heading('Gekwalificeerde frameworkbron', 'De gecontroleerde CANONICAL_FROZEN-distributie is apart uitgepakt in een hashgebonden, alleen-lezen bronmap. De volledige broninventaris wordt voor elke adapterrun opnieuw gecontroleerd. De oude lokale frameworkvariant en manifesten zijn behouden.')
    text('Framework ZIP SHA-256: ' + summary['framework_distribution_sha256'], 'Digest')
    text('Framework bronboom SHA-256: ' + summary['framework_source_tree_sha256'], 'Digest')
    text('Framework PACKAGE_MANIFEST SHA-256: ' + source['framework_source']['manifest_sha256'], 'Digest')
    text('A011 bronboom SHA-256: ' + source['source_tree_sha256'], 'Digest')
    text('A011 bron-ZIP SHA-256: ' + source['source_archive_sha256'], 'Digest')
    text('Geometrieprotocol SHA-256: ' + summary['protocol_bundle_sha256'], 'Digest')

    page('1. Seeds, bronhashes en geometrie')
    text('Selectie vooraf vastgelegd: representatieve 0_1, 3_1 en 4_1; daarna de lexicografisch eerste toegelaten enkelvoudige VECT-curve met maximaal 4096 bronpunten. Geen selectie op gemeten score, gewenst SST-resultaat of verwachte winnaar.')
    for seed, result in zip(seeds, results):
        text(seed['topology_id'] + ' | ' + seed['carrier_id'], 'Heading2')
        text('Raw SHA-256: ' + seed['raw_sha256'], 'Digest')
        text('Geometrie SHA-256: ' + seed['geometry_sha256'], 'Digest')
        levels = result['metrics_by_resolution']
        text('N=64: L=' + format(levels[0]['length_units'], '.9g') + ', mean curvature=' + format(levels[0]['curvature_mean'], '.9g') + ', midpoint Wr=' + format(levels[0]['writhe_midpoint'], '.9g'))
        text('N=128: L=' + format(levels[1]['length_units'], '.9g') + ', mean curvature=' + format(levels[1]['curvature_mean'], '.9g') + ', midpoint Wr=' + format(levels[1]['writhe_midpoint'], '.9g'))
    heading('Betekenis en eenheden', 'De ongewijzigde v0.3.1-routines bepalen arclength-resampling, polygonlengte, discrete kromming en midpoint-writhe. Broncoordinaateenheden blijven behouden; er is geen gekalibreerde SI-lengteschaal. Writhe is dimensieloos. De twee resoluties zijn gevoeligheidsdiagnostiek en vormen geen convergentiebewijs.')
    text('Admission-contract SHA-256: ' + summary['admission_contract_sha256'], 'Digest')
    text('Exacte bronpaden, descriptorpaden, resoluties en gebruikte native-kernelprobes staan in SELECTED_SEEDS.json. Hun bytes en parsed geometry zijn voor de meting en voor succesvolle publicatie opnieuw gecontroleerd.')

    page('2. Gates en foutdiagnostiek')
    table(['Gate', 'Waargenomen status', 'Kwalificatie'], [[r['gate_id'], r['status'], r['qualification']] for r in ledger], [15*mm, 80*mm, 80*mm])
    heading('Pariteit met oorspronkelijke toleranties', 'Snelheid: rtol=1e-11 en atol=1e-12. Writhe- en afstandsverschil: absoluut <1e-11. Deze grenzen zijn ongewijzigd uit v0.3.1 overgenomen. Alle zes seed/resolutiecombinaties slagen.')
    text('Maximaal absoluut snelheidsverschil: ' + format(max(r['velocity_max_abs_delta'] for r in parity), '.12g'))
    text('Maximaal writhe-verschil: ' + format(max(r['writhe_abs_delta'] for r in parity), '.12g') + '; maximaal afstandsverschil: ' + format(max(r['distance_abs_delta'] for r in parity), '.12g'))
    text('Gamma=1, smoothing=0.05 en de vaste offset zijn dimensieloze softwareprobes in broncoordinaateenheden, geen onafhankelijke fysische snelheidsexperimenten.')
    heading('Fouten en beperkingen', 'Geen meet- of uitvoerfouten in de geslaagde smoke. NaN/Inf, ontbrekende bronnen, byte-afwijkingen, niet-toegelaten geometrie en ontbrekende native ABI leiden tot afbreken; bestaande resultaten worden geweigerd in plaats van overschreven. Tamper-/pad-/overwrite-/kwalificatie-regressies zijn onderdeel van de tests.')
    text('G5 is gemeten ondanks ontbrekende fysische prerequisites en blijft DIAGNOSTIC_ONLY; allows_dependent_claim=false. G3/G4/G7/G8 zijn niet fysisch uitgevoerd. G6 GPU is uit; G9 reveal is uitgesteld.')

    page('3. Wetenschappelijke grenzen en vervolg')
    heading('Ontbrekende bewijsstukken', 'De volgende invoer is niet geleverd of gekwalificeerd door deze tranche:')
    for missing in summary['missing_scientific_evidence']:
        text('- ' + missing)
    text('Geometrie-identiteit en softwarepariteit bewijzen geen fysische energie, zwaartekracht, thermodynamische sluiting, Euler- of Casimir-mechanisme. Er is geen parameterfit of nieuwe voorspelling uitgevoerd. Historische negatieve resultaten en alle voorgangers blijven behouden.')
    heading('Protocol en runner', 'De adapter gebruikt de echte v1.0.10 GateLedger.run_evaluators en protocolhashing. Dit is een eigen, gepreregistreerde geometrische runner; de volledige framework run_mode BLIND/REVEAL-pipeline en private-target FREEZE zijn niet uitgevoerd. Het bronmanifest en protocol leggen vast welke code, inputbeslissingen en grenzen zijn gebruikt.')
    heading('A054-vervolgbesluit: NO-GO voor onmiddellijke migratie', 'De frameworkbron is nu overdraagbaar gekwalificeerd. A054 zelf is niet gewijzigd of uitgevoerd. Eerst moeten P02 (expliciete A054-bronselectie) en de P04-voorwaarden voor de opvolger worden vastgelegd: v1.0.10-pin, E013-zelfhash en E011-bindingen tijdens runtime, plus exacte loaderpins. L2a1 heeft nog een provider; positieve cross-provider-claims blijven daar geblokkeerd. Dit is geen afwijzing van een latere gecontroleerde voorbereidende tranche.')
    heading('Archief en reproduceerbaarheid', 'Het versiegebonden resultaatarchief bevat dit zelfstandige PDF, de bron- en invoerhashes, geselecteerde seeds, omgeving, gates, geometrie-/pariteitsmetingen en test-/proceslogs. De naastliggende SHA-256-sidecar controleert het volledige ZIP. De ZIP-hash staat buiten dit PDF om een circulaire hashafhankelijkheid te voorkomen.')
    text('A011 bronmanifest SHA-256: ' + source['source_manifest_sha256'], 'Digest')
    text('Pre-report evidence manifest SHA-256: ' + hashlib.sha256((RESULT/'RESULT_EVIDENCE_MANIFEST.json').read_bytes()).hexdigest(), 'Digest')
    text('Geen wijzigingen aan A054/A065; geen volledige fysische campagne; Scheduled blijft uitgeschakeld. Afzonderlijke migratie-, uitvoerings- en wetenschappelijke statussen worden in de persistente wachtrij bewaard.')

    target = RESULT / 'A011_v0.4.0_Framework_v1.0.10_FALSIFIER_REPORT.pdf'
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(17*mm, 11*mm, 'SST-Workbench | A011 v0.4.0 | Geometry diagnostic only | 26-10-2026')
        canvas.drawRightString(193*mm, 11*mm, str(doc.page))
    with target.open('xb') as stream:
        SimpleDocTemplate(stream, pagesize=(210*mm, 297*mm), leftMargin=17*mm, rightMargin=17*mm, topMargin=16*mm, bottomMargin=20*mm).build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


if __name__ == '__main__':
    main()
