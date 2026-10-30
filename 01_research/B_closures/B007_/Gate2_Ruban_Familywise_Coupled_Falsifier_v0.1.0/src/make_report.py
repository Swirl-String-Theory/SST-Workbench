"""Generate provenance-grounded scientific PDF after the four numerical gates."""
from pathlib import Path
import csv,hashlib,json,sys,argparse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,KeepTogether
R=Path(__file__).resolve().parents[1]
O=R/(R.name+'-outputs')

def main():
 global O
 p=argparse.ArgumentParser();p.add_argument('--extended',action='store_true');args=p.parse_args()
 if args.extended:O=O/'extended'
 ledger=json.loads((O/'G0_G4_ASSESSMENT.json').read_text())
 winners=list(csv.DictReader((O/'G3_family_winners_holdout.csv').open()))
 couples=list(csv.DictReader((O/'G4_coupled_summary.csv').open()))
 doc=SimpleDocTemplate(str(O/'FALSIFIER_REPORT.pdf'),pagesize=(21*cm,29.7*cm),leftMargin=2.1*cm,rightMargin=2.1*cm,topMargin=1.8*cm,bottomMargin=1.8*cm)
 ss=getSampleStyleSheet();ss.add(ParagraphStyle(name='ReportTitleSST',parent=ss['Title'],fontName='Helvetica-Bold',fontSize=18,leading=23,textColor=colors.HexColor('#14385a'),spaceAfter=16))
 ss.add(ParagraphStyle(name='ReportBodySST',parent=ss['BodyText'],leading=14,spaceAfter=10))
 ss.add(ParagraphStyle(name='ReportSmallSST',parent=ss['BodyText'],fontSize=8,leading=11))
 flow=[]
 def para(s,style='ReportBodySST'):flow.append(Paragraph(s,ss[style]))
 def heading(s):flow.append(Spacer(1,8));para(s,'Heading2')
 def table(data,widths=None):
  t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([
   ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe9f5')),
   ('GRID',(0,0),(-1,-1),.3,colors.HexColor('#bdcad6')),
   ('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f9')]),
   ('FONTSIZE',(0,0),(-1,-1),8),('LEFTPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]));flow.append(t)
 para('Gate 2 - Family-Wise Ruban / Coupled Euler Falsifier','ReportTitleSST')
 para('Version 0.1.0 | Four sequential gates | Scientific verdict: <b>G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM</b>')
 heading('Question and model boundary')
 para('Can a closed finite-core trefoil and a self-consistently moving background vortex network form a common relative equilibrium of the 3D incompressible Euler equations? This report distinguishes reduced filament screening from periodic finite-core Fourier Euler tests. No fixed background force is used in the physical coupling case.')
 heading('Execution summary')
 table([['Stage','Count','Meaning'],['G1 geometry',str(ledger['G1']),'Geometry schema only'],['G2 screening',str(ledger['G2']),'Nominal + perturbed reduced filament runs'],['G3 representatives',str(ledger['G3']),'One per embedding; independent N checks'],['G4 coupled Euler',str(ledger['G4']),'Living background loop(s); fixed-U holdout']],[3.4*cm,2.3*cm,11*cm])
 heading('G3: rank per family - numerical proxy only')
 tab=[['Rank','Family','B0','Residual','256-to-512 difference']]
 for r in winners:
  tab.append([r['ranking_by_filament_proxy'],r['embedding'],f"{float(r['B0']):.3f}",f"{float(r['g2_stability_proxy']):.5f}",f"{float(r['n256_to_512_absolute_difference']):.2g}"])
 table(tab,[1.5*cm,3*cm,1.6*cm,3.3*cm,7.3*cm])
 heading('G4: periodic Fourier Euler holdout (shared kernel)')
 tab=[['Seed','Background','Train R*','Holdout R*','Filter error']]
 for r in couples:
  tab.append([r['seed_id'].replace('_N512',''),r['background'],f"{float(r['Rstar_training']):.3g}",f"{float(r['Rstar_holdout']):.3g}",f"{float(r['projection_error_training']):.3g}"])
 table(tab,[5.1*cm,3.1*cm,2.6*cm,2.7*cm,3.2*cm])
 heading('Gates and stop criteria')
 para('<b>G1 PASS limited:</b> exactly 84 geometries with verified SHA-256 source fingerprints. Not a proof of geometric reach or perturbation knot isotopy.')
 para('<b>G2 PASS limited:</b> screening was actually performed, but regularized point/segment filament induction is not the full Euler system; small drift is not stability.')
 para('<b>G3 PASS limited:</b> provisional ranking and 128/256/512 curve sampling checks. Holdout uses the same mathematical regularization, so it is not independent-backend parity.')
 para('<b>G4 NUMERIC PREFLIGHT BLOCKED / UNRESOLVED:</b> no numerical root-finder has produced a nontrivial field with independently convergent zero residual. Spectral filter corrections are over 50 percent in the initial coarse runs. The 3x3 and 5x5 closed return-loop arrays have near-contact geometry (sampled minimum 0.019 and 0.0019, respectively; 2*sigma=0.24) and are NOT valid disjoint-core candidates. Source Gaussian cores are not compactly supported. The periodic cube allows continuous axial translation but not arbitrary continuous rotation. Material isotopy, common final time convergence, and domain independence remain open.')
 heading('Exact provenance and reproducibility')
 para('E010 v0.3.5 analytical seed-family archive SHA256: <font size="7">'+ledger['source_sha256']+'</font>')
 para('The archive index and every original/perturbed XYZ file were SHA-256 checked before running. The catalog ID is intentionally left unassigned until the current SST-Workbench index is consulted. The full machine-readable dataset, source and per-file manifest accompany this report.')
 heading('Decision')
 para('<b>STOP: no relative Euler equilibrium has been certified.</b> Continue by independently qualifying the core width against the spatial grid, checking full-field component residuals at increasing fixed-U resolution, and implementing a domain-symmetry-correct finite-core coupled equilibrium solver. Only then pursue a nontrivial candidate and time-evolution verification.')
 def foot(canvas,doc):
  canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey);canvas.drawString(2.1*cm,1.15*cm,'Gate 2 v0.1.0 - DEVELOPMENT - no physical stability claim');canvas.drawRightString(18.9*cm,1.15*cm,str(doc.page));canvas.restoreState()
 doc.build(flow,onFirstPage=foot,onLaterPages=foot)
 # update output manifest after last generated artifact, excluding itself
 manifest={p.relative_to(O).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(O.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
 (O/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 print('PDF report:',O/'FALSIFIER_REPORT.pdf')
if __name__=='__main__':main()
