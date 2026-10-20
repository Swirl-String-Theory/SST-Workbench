from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether
out=Path(__file__).with_name('F005_v0.4.0_Audit_and_v0.4.1_Repair.pdf')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleF',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=colors.HexColor('#183447'),spaceAfter=13))
styles.add(ParagraphStyle(name='HeadF',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=11.5,leading=16,spaceBefore=11,spaceAfter=7,textColor=colors.HexColor('#1B435B')))
styles.add(ParagraphStyle(name='BodyF',parent=styles['BodyText'],fontName='Helvetica',fontSize=9.3,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='TinyF',parent=styles['BodyText'],fontSize=8,leading=11))
doc=SimpleDocTemplate(str(out),pagesize=(210*mm,297*mm),leftMargin=19*mm,rightMargin=19*mm,topMargin=18*mm,bottomMargin=18*mm)
story=[]
def p(t,style='BodyF'):story.append(Paragraph(t,styles[style]))
p('F005 | v0.4.0 audit and v0.4.1 repair','TitleF')
p('19 October 2026 | Development audit, not physical validation')
p('1. Grounded diagnosis','HeadF')
p('The submitted v0.4.0 run did not calculate any free-run metrics. The waveform-family candidate generator crossed its hard cap <b>before scoring</b>, and the code then blocked the independent validation forecast.')
rows=[['Gate / observation','User-run value','Interpretation'],['Trajectories examined','9,822','Input inventory read'],['P5b candidate pairs','150,001 / 150,000 max','Hard cap exceeded'],['P5b scored','0','No near-match conclusions'],['Large fingerprint buckets','8 skipped','Review incomplete'],['P6a','BLOCKED','No forecast errors'],['Holdout outputs','Not accessed','Separation retained']]
t=Table(rows,colWidths=[61*mm,49*mm,62*mm],repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7EEF3')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#102F45')),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#B5C8D3')),('GRID',(0,1),(-1,-1),.3,colors.HexColor('#D7DFE4')),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8.2),('LEADING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
story.append(t)
p('2. Minimal v0.4.1 patch','HeadF')
p('The patch performs a complete SHA-256 scan of exact input-signal duplicates, then performs a reproducible, capped <b>approximate</b> morphology screen. It samples dense buckets rather than skipping them without review. The approximate search is never reported as exhaustive.')
p('Crucially, <b>P5b remains REVIEW</b>, while P6a is allowed to run on STANDARD_VALIDATION only, explicitly labeled <b>DEVELOPMENT_CONDITIONAL_FREE_RUN_FAMILY_REVIEW_OPEN</b>. No TEST/OOD elevations are used.')
p('3. Reproducible test contract','HeadF')
p('Frozen ARX(2): A=1.9856661039519918, B=-0.9908696423084401, C=-1.118156917616826; dt=0.004 s. Anchors: 0.004, 1.5, 2.8 s. Horizons: 0.1, 0.5, 1, 2, 3 s. Forcing is a known future exogenous acceleration; elevations only seed the first two points.')
p('Compare each terminal-horizon RMSE against persistence and two-point linear extrapolation. No refit, no test/OOD reveal, no Euler or PKLSA claim.')
p('4. Software verification and remaining gates','HeadF')
p('Eight synthetic unit and integration tests passed, including holdout-output-access rejection, deterministic bounded candidate screening, detected exact duplicates, and an end-to-end PDF/CSV development run. <b>The user\'s 9,822 trajectories were not available in this environment</b>; v0.4.1 experimental results remain pending local execution.')
p('Family independence requires source-defined family IDs and a group-disjoint holdout. The present fixed candidate partition remains NON-BLIND. P7 (PKLSA) NOT RUN; P8 physical SST conclusions UNRESOLVED.')
p('5. Local invocation','HeadF')
p('<font face="Courier">run_all_v041.cmd</font> from the existing F005 root; outputs are written to <font face="Courier">outputs/f005_free_run_family_v0.4.1/</font>. Keep existing v0.4.0 folders and source archives unchanged.')
p('Sources: user-uploaded F005 v0.4.0 report/summary; L. Ljung, System Identification: Theory for the User, 2nd ed. (1999); P. G. Saffman, Vortex Dynamics (1992), doi:10.1017/CBO9780511624063.','TinyF')
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#5F7080'));c.drawString(19*mm,11*mm,'F005 v0.4.1 DEVELOPMENT - no SST certification');c.drawRightString(191*mm,11*mm,str(d.page))
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(out)
