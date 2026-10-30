"""Human-readable diagnostic PDF, not the official SST Framework v1.1 report."""
from pathlib import Path
from xml.sax.saxutils import escape

SECTIONS=[
('01. Executive scientific verdict', 'This sidecar checks a narrowly defined question: can hidden conservative modes create observational memory and return energy when only one mode is measured? A synthetic benchmark validates the diagnostic, but does not certify a three-dimensional incompressible Euler field or an intrinsic SST Swirl Clock.'),
('02. Research question', 'At identical currently observed knot state, can the prior observed trajectory improve held-out predictions because omitted background vorticity modes contain physical state information? Is any inferred phase frequency dynamically qualified?'),
('03. Existing-family and novelty audit', 'A026 tests phase-feedback delay and Kelvin transport; A049 tests effective transverse rigidity; A068/A069 address phase clocks. This sidecar adds a matched-current-versus-history prediction comparison. It is not a replacement for, or a new certified version of, these families.'),
('04. Sources and provenance', 'Paper: Muruga, Ginot, Loos and Bechinger (2026), Nature Physics, doi:10.1038/s41567-026-03442-w. Closest project source: A026 v0.2.1 README and A049 v0.4.1 README. Every generated run records its input and code hashes; a new external provider must be independently qualified.'),
('05. Physics scope and assumptions', '3D incompressible inviscid Euler, no forcing, is the future target. Current executable proof is a two-mode linear, conservative Hamiltonian benchmark with SI-unit positions and a reference mass of 1 kg. No molecular viscosity, stochastic bath, Euler pressure solver or knot topology is represented in the executable benchmark.'),
('06. State-space and observables', 'Observable current features are x(t), xdot(t). History features are x(t-delay), xdot(t-delay). Oracle adds hidden y(t), ydot(t). Prediction target is x(t+horizon). A separate future Euler adapter must export a preregistered geometric scalar q and its true derivative, with independent trial IDs.'),
('07. Equations and dimensionality', 'Benchmark: xddot + omegaK^2*x + g*y=0; yddot + omegaB^2*y + g*x=0. Here [omega]=s^-1, [g]=s^-2. Energy E=m/2*(xdot^2+ydot^2+omegaK^2*x^2+omegaB^2*y^2+2*g*x*y) has units joule. Eliminating y yields a sinusoidal memory kernel, not a viscous constitutive law.'),
('08. Null, alternative and preregistered criteria', 'H0: with coupling g=0, past features do not improve future prediction beyond current position and velocity; upper 95% bootstrap limit on relative root-mean-square error gain must stay below 0.05. H1 synthetic: with g=2 s^-2, lower 95% gain bound must exceed 0.20. Euler science gates require new thresholds registered before exposure.'),
('09. Dataset and sampling', 'Each synthetic sample is one independently seeded complete trajectory, sampled at fixed observation time t=2.1 s, delay 0.65 s and horizon 0.75 s. Training and test are split by complete trajectory. Independent bootstrap resamples test trajectories. Target-only Gaussian measurement noise is included to avoid zero-error ratios.'),
('10. Comparison method', 'Fit ordinary least-squares predictions using train-only standardization: (i) current state, (ii) current plus history, and (iii) full-state oracle. Measure out-of-sample RMSE and improvement 1-RMSE_history/RMSE_current. Bootstrap 400 times on independent test trajectory IDs.'),
('11. Verification and negative controls', 'Check analytic energy invariance, decoupled null, coupled positive, duplicate trial rejection, non-finite rejection and minimum independent sample size. The synthetic positive cannot be used as Euler evidence. Future controls need shuffled history with matched current, stationary-history drift checks, and uncertainty under finite measurement resolution.'),
('12. Numerical qualification', 'For a real 3D Euler conclusion: independent spatial, temporal, finite-core and domain convergence at common final physical time; divergence/momentum, energy/helicity/circulation residuals and knot isotopy checks. A filament regularizer and spectral Gaussian core are not interchangeable. These tests are NOT EXECUTED here.'),
('13. Hidden-state test result', 'The data table and numerical decision ledger appear below. The result qualifies the algebraic numerical method only; it does not prove a background network restores a trefoil or sustains a clock.'),
('14. Swirl Clock test', 'Absolute time t_abs is the underlying evolution parameter. An operational phase clock requires a stable phase theta and measured Omega=dtheta/dt_abs. Only after demonstrable phase coherence, environmental perturbation controls and full converged dynamics may d tau/dt_abs=Omega/Omega_ref be evaluated. No clock law is inferred in this release.'),
('15. Falsifiers, confounders and status', 'Critical confounders: incomplete observation, noisy current state, remeshing, nonstationary sampling, shared trajectories across splits, numerical stabilization, and unresolved Euler core. Physical statuses remain UNRESOLVED / NOT EXECUTED, even if all synthetic smoke gates PASS.'),
('16. Reproduction, outputs and bibliography', 'Run run_all.cmd TEST followed by run_all.cmd BASIC. Run EULER only with source-audited NPZ independent trajectories. Output produces machine-readable gate ledgers, science report and SHA-256 archive. Citations: Muruga et al. (2026), DOI 10.1038/s41567-026-03442-w; Mori (1965), DOI 10.1143/PTP.33.423; Sagawa & Ueda (2012), DOI 10.1103/PhysRevE.85.021104.')]

def render_pdf(path, ledger, result):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
    except ImportError:
        return False
    path=Path(path)
    ss=getSampleStyleSheet()
    ss.add(ParagraphStyle(name='TitleSST',parent=ss['Title'],fontSize=17,leading=22,spaceAfter=14))
    ss.add(ParagraphStyle(name='SecSST',parent=ss['Heading2'],fontSize=10.3,leading=12.5,spaceBefore=11,spaceAfter=4,textColor=colors.HexColor('#244c71')))
    ss.add(ParagraphStyle(name='BodySST',parent=ss['BodyText'],fontSize=8.4,leading=12,spaceAfter=5))
    ss.add(ParagraphStyle(name='TinySST',parent=ss['BodyText'],fontSize=7.5,leading=10))
    story=[Paragraph('A026 Hidden-State Memory &amp; Backreaction',ss['TitleSST']),
        Paragraph('Independent research sidecar v0.1.0 - DEVELOPMENT ONLY / NOT AN EULER OR SWIRL CLOCK CERTIFICATION',ss['BodySST'])]
    for title,body in SECTIONS:
        story.append(Paragraph(escape(title),ss['SecSST']))
        story.append(Paragraph(escape(body),ss['BodySST']))
        if title.startswith('13.'):
            data=[['Case','RMSE current (m)','RMSE history (m)','Gain 95% CI']]
            for case,record in result.items():
                if isinstance(record,dict) and 'rmse_current_m' in record:
                    data.append([case, f"{record['rmse_current_m']:.4g}",f"{record['rmse_history_m']:.4g}",str([round(v,4) for v in record['ci95_gain']])])
            if len(data)>1:
                t=Table(data,repeatRows=1,colWidths=[85,100,100,116]);t.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8ef')),
                    ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#d0d8e0')),
                    ('FONTSIZE',(0,0),(-1,-1),7.4),('LEFTPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6)]))
                story.append(t)
            story.append(Spacer(1,6))
            for key,item in ledger['gates'].items():
                story.append(Paragraph(f"{escape(key)}: <b>{escape(item['status'])}</b> - {escape(item['reason'])}",ss['TinySST']))
    def foot(canvas,doc):
        canvas.saveState(); canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#737d87'))
        canvas.drawString(40,28,'A026-HSM v0.1.0 - synthetic research diagnostic, not certified SST physics')
        canvas.drawRightString(550,28,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=44,bottomMargin=45,title='A026 HSM Falsifier report')
    doc.build(story,onFirstPage=foot,onLaterPages=foot)
    return True
