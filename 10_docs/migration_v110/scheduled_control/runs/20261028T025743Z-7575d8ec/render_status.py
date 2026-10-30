"""Technical status only; never replaces a scientific falsifier report."""
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
import hashlib
import json
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak

OUT=Path(__file__).resolve().parent


def main():
    data=json.loads((OUT/'CHECKS.json').read_text())
    geometry=json.loads((OUT/'GEOMETRY_VERIFICATION.json').read_text())
    hashes=json.loads((OUT/'INPUT_HASHES.json').read_text())
    styles=getSampleStyleSheet()
    styles['Normal'].fontSize=9;styles['Normal'].leading=12
    styles['Heading1'].fontSize=18;styles['Heading1'].leading=22
    styles['Heading2'].fontSize=12;styles['Heading2'].leading=16
    styles.add(ParagraphStyle('Hash',fontName='Courier',fontSize=7.7,leading=10,spaceAfter=6))
    story=[]
    def text(s,style='Normal'):
        story.extend([Paragraph(escape(str(s)),styles[style]),Spacer(1,1.5*mm)])
    def page(s):
        if story:story.append(PageBreak())
        text(s,'Heading1')
    def digest(s,value):
        text(s,'Heading2')
        story.append(Paragraph('<br/>'.join(escape(value[i:i+32]) for i in range(0,len(value),32)),styles['Hash']))
    page('SST-Workbench | Dagelijkse controle')
    text('A054-v0.6.0 - 28 oktober 2026','Heading2')
    text('Run-ID: '+data['run_id'])
    text('Trigger UTC: '+data['trigger_utc'])
    text('Start UTC: '+data['started_utc'])
    text('Tijdzone: Europe/Amsterdam. Bestaande dagelijkse planning: 04:00. Het werkelijke triggermoment staat hierboven exact vastgelegd; de nominale planning is niet als uitvoertijd verondersteld.')
    text('Status: '+data['status'],'Heading2')
    text('De bestaande A054-migratie blijft intact. Alleen voorbereidend bron-, geometrie- en archiefonderzoek is verricht. Er is geen nieuwe falsifierversie aangemaakt en geen wetenschappelijke evaluator, reveal, native berekening of campagne gestart.')
    for key,value in data['gate_axes'].items():text(key+': '+str(value))
    text('Ongewijzigde blokkades','Heading2')
    for item in data['blockers']:text(item)
    text('Volgende concrete actie','Heading2')
    text('Afzonderlijk begrensd native-pariteits-/state-selectionbudget en protocol beoordelen. Onafhankelijke providerdekking blijft nodig voor wetenschappelijke closure. De algemene campagnevrijgave en pilot_validated blijven false. De bronregel voor lokale/Drive-bestanden is al geautoriseerd en veroorzaakt geen nieuwe toestemmingsvraag.')
    text('Uitvoeromgeving','Heading2')
    env=data['environment']
    text(env['python']);text(env['platform']);text('NumPy: '+str(env.get('numpy','niet bereikt')))
    text('Werkmap: '+env['cwd'])
    page('Integriteit en bestaande bronpins')
    for row in data['checks']:
        text(row['check']+': '+row['status'],'Heading2')
        if 'files' in row:text('Gecontroleerde A054-bronbestanden: '+str(row['files']))
        if 'manifest_entries' in row:text('Gekwalificeerde frameworkvermeldingen: '+str(row['manifest_entries']))
        if 'carriers' in row:text('Carriers: '+str(row['carriers'])+'; gepinde E010-parserbestanden: '+str(row['loader_files']))
    text('In totaal zijn '+str(len(hashes))+' bestanden met pad, omvang, gelezen SHA-256 en eventuele verwachte SHA-256 vastgelegd in INPUT_HASHES.json. De ruwe bestanden en parsed geometrie van alle vijf toegelaten carriers zijn opnieuw gecontroleerd. De bestaande E013-binding en E011-ankers zijn onveranderd.')
    for suffix,label in [('STATIC_READY_INDEX.json','E011 static index'),('STATIC_READY_PROVIDER_ANCHORS.jsonl','E011 provider anchors'),('CROSS_CARRIER_MANIFEST.json','A054 E013 common carrier binding')]:
        match=next((r for r in hashes if r['path'].endswith(suffix)),None)
        if match:digest(label,match['sha256'])
    digest('Volledig gelezen hashregister',hashlib.sha256((OUT/'INPUT_HASHES.json').read_bytes()).hexdigest())
    text('Stopcriteria','Heading2')
    text('Een onverwachte bron-, manifest-, code-, dataset- of uitvoerafwijking stopt de verwerking. Historische manifesten, resultaten en commitments worden niet aangepast. Een bestaande run-lock sluit overlap uit. Alleen de eigen lock wordt vrijgegeven nadat de rapportage is afgerond.')
    if data['errors']:
        text('Werkelijke fouten','Heading2')
        for error in data['errors']:text(error['type']+': '+error['message'])
    else:text('Fouten: geen. Reeds bekende wetenschappelijke beperkingen zijn ongewijzigd.')
    page('Geometrie, resultaten en hervatting')
    for row in geometry:
        text(row['topology_id']+' | '+row['provider_group']+' | '+row['status'],'Heading2')
        text(row['static_seed_id']+' | '+row['carrier_id']+' | bronpunten: '+str(row['source_points']))
        value=row['geometry_sha256']
        story.append(Paragraph('<br/>'.join(value[i:i+32] for i in range(0,len(value),32)),styles['Hash']))
    text('Nieuwe atlas als broncontext','Heading2')
    text('E010-v0.4.0 is beschikbaar als gecombineerde atlas met 11.757 records. Bronpins, ZIP/PDF en index zijn opnieuw gehasht. A054 blijft aan zijn bestaande E010/E011/E013-contract gebonden. Research-seeds geven geen extra onafhankelijke providerdekking en geen wetenschappelijke vrijgave.')
    text('Bestaande wetenschappelijke resultaten','Heading2')
    text('PDF, resultaten-ZIP, bronarchief, SHA-256-sidecar, outputmanifest en science-evidence-manifest zijn opnieuw gecontroleerd. Rapportdata en gate-ledger stemmen overeen. De wetenschappelijke status blijft NOT_RUN; deze controle produceert geen nieuw wetenschappelijk resultaat.')
    text('Centrale registratie','Heading2')
    text('CHECKS.json en GEOMETRY_VERIFICATION.json bewaren deze controle. Na visuele PDF-controle wordt result.json vastgelegd en verwijst de wachtrij atomair naar dit checkpoint. Een vorige wachtrijsnapshot en append-only uitvoerlog blijven beschikbaar. Andere falsifierjobs worden niet gewijzigd.')
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8)
        canvas.drawString(21*mm,12*mm,'SST-Workbench | Scheduled A054 status | Geen wetenschappelijke promotie')
        canvas.drawRightString(189*mm,12*mm,str(doc.page))
    pdf=OUT/'A054_Scheduled_Status.pdf'
    assert not pdf.exists()
    SimpleDocTemplate(str(pdf),pagesize=(210*mm,297*mm),leftMargin=21*mm,rightMargin=21*mm,topMargin=19*mm,bottomMargin=22*mm,
      title='A054 scheduled integrity control 2026-10-28',author='SST-Workbench').build(story,onFirstPage=footer,onLaterPages=footer)
    print(str(pdf))


if __name__=='__main__':main()
