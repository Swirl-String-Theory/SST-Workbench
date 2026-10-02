#!/usr/bin/env python3
"""
Compare three trefoil geometry sources used in SSTcore:
1. Brian Gilbert ideal.txt AB entry 3:1:1
2. KnotPlot converted Fourier/AB entry 3:1:1
3. Fremlin Fourier-series trefoils

Outputs CSV and Markdown side-by-side metrics.
"""
import re, zipfile, math
from pathlib import Path
import numpy as np
import pandas as pd

N = 4096
N_DIST = 2048
IDEAL_L = 16.371637

# Canon constants for optional linear mass baseline comparison
c = 299792458.0
h = 6.62607015e-34
m_e = 9.1093837139e-31  # CODATA 2022 rounded
r_c = 1.40897017e-15
rho_m = 3.8934358266918687e18
lambda_c = h / (m_e * c)
M0_prefactor = 2 * math.pi**3 * rho_m * (r_c**5) / (lambda_c**2)  # kg per Ltot

def parse_ab_coeffs_text(text, target_id):
    m = re.search(r'<AB\s+[^>]*Id="' + re.escape(target_id) + r'"[^>]*>(.*?)</AB>', text, re.S)
    if not m:
        raise ValueError(f'AB {target_id} not found')
    block = m.group(0)
    header = re.search(r'<AB\s+([^>]*)>', block)
    attrs = {}
    if header:
        for k, v in re.findall(r'(\w+)="([^"]*)"', header.group(1)):
            attrs[k] = v
    coeffs = []
    for cm in re.finditer(r'<Coeff\s+([^>]*)/>', block):
        attr = dict(re.findall(r'(\w+)="([^"]*)"', cm.group(1)))
        i = int(attr['I'])
        A = np.array([float(x) for x in attr['A'].split(',')], dtype=float)
        B = np.array([float(x) for x in attr['B'].split(',')], dtype=float)
        coeffs.append((i, A, B))
    coeffs.sort(key=lambda x: x[0])
    return attrs, coeffs

def parse_fseries(text):
    coeffs = []
    i = 1
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('%') or s.startswith('#'):
            continue
        vals = [float(x) for x in s.split()[:6]]
        if len(vals) == 6:
            ax, bx, ay, by, az, bz = vals
            coeffs.append((i, np.array([ax, ay, az], float), np.array([bx, by, bz], float)))
            i += 1
    return coeffs

def eval_curve(coeffs, n=N):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    r = np.zeros((n, 3), float)
    rp = np.zeros((n, 3), float)
    rpp = np.zeros((n, 3), float)
    for k, A, B in coeffs:
        kt = k * t
        co = np.cos(kt)[:, None]
        si = np.sin(kt)[:, None]
        r += co * A + si * B
        rp += (-k * si) * A + (k * co) * B
        rpp += (-(k*k) * co) * A + (-(k*k) * si) * B
    return t, r, rp, rpp

def approximate_contact_diameter(coeffs, rel_arc_exclusion=0.075, n=N_DIST):
    # Approximate nonlocal contact diameter by excluding pairs nearby along arclength.
    # rel_arc_exclusion=0.075 gives ~1.23 arclength units for the ideal trefoil and recovers D≈1.
    _, r, _, _ = eval_curve(coeffs, n)
    seg = np.linalg.norm(np.roll(r, -1, axis=0) - r, axis=1)
    L = float(seg.sum())
    cum = np.concatenate([[0.0], np.cumsum(seg)])[:-1]
    excl = rel_arc_exclusion * L
    min_d2 = np.inf
    for start in range(0, n, 256):
        rb = r[start:start+256]
        d2 = np.sum((rb[:, None, :] - r[None, :, :])**2, axis=2)
        ds = np.abs(cum[start:start+256, None] - cum[None, :])
        ds = np.minimum(ds, L - ds)
        d2[ds < excl] = np.inf
        val = float(np.nanmin(d2))
        if val < min_d2:
            min_d2 = val
    return float(math.sqrt(min_d2)), excl

def metrics(label, role, coeffs, reported_L=None, reported_D=None):
    _, r, rp, rpp = eval_curve(coeffs, N)
    speed = np.linalg.norm(rp, axis=1)
    L = float(speed.mean() * 2*np.pi)
    # exact closure of Fourier representation
    r0 = np.zeros(3)
    r2 = np.zeros(3)
    for k, A, B in coeffs:
        r0 += A
        r2 += A*np.cos(2*np.pi*k) + B*np.sin(2*np.pi*k)
    closure = float(np.linalg.norm(r0-r2))
    centroid = r.mean(axis=0)
    rms_radius = float(np.sqrt(np.mean(np.sum((r-centroid)**2, axis=1))))
    bbox_diag = float(np.linalg.norm(r.max(axis=0) - r.min(axis=0)))
    curv = np.linalg.norm(np.cross(rp, rpp), axis=1) / (np.linalg.norm(rp, axis=1)**3 + 1e-300)
    kmax = float(np.nanmax(curv))
    curv_radius_min = float(1.0/kmax)
    contact_D, contact_excl = approximate_contact_diameter(coeffs)
    rop_contact = L / contact_D if contact_D > 0 else float('nan')
    reported_rop = None
    if reported_L is not None and reported_D not in (None, 0):
        reported_rop = reported_L / reported_D
    # main comparison used for calculations: canonical ideal uses reported; non-canon should use contact-normalized proxy
    calc_Ltot = reported_rop if role == 'canon_ideal' and reported_rop else rop_contact
    return dict(
        source=label,
        role=role,
        harmonics=len(coeffs),
        reported_L=reported_L,
        reported_D=reported_D,
        reported_L_over_D=reported_rop,
        native_length=L,
        closure_gap=closure,
        rms_radius=rms_radius,
        bbox_diag=bbox_diag,
        kappa_max=kmax,
        min_curvature_radius=curv_radius_min,
        contact_diameter_approx=contact_D,
        contact_arc_exclusion=contact_excl,
        contact_normalized_L_over_D=rop_contact,
        Ltot_used_for_calc=calc_Ltot,
        mass_scale_factor_vs_ideal=calc_Ltot / IDEAL_L,
        raw_length_factor_vs_ideal=L / IDEAL_L,
        M0_baseline_kg=M0_prefactor * calc_Ltot,
    )

def main():
    curves = []
    ideal_txt = Path('/mnt/data/ideal.txt').read_text(errors='replace')
    attrs, coeffs = parse_ab_coeffs_text(ideal_txt, '3:1:1')
    curves.append(('Ideal Gilbert AB 3:1:1', 'canon_ideal', coeffs, float(attrs['L']), float(attrs['D'])))

    with zipfile.ZipFile('/mnt/data/Knotplot-knot_3.1.zip') as zp:
        kp_ab = zp.read('Knotplot-knot_3.1/knot_3.1_ideal.txt').decode('utf-8', 'replace')
        attrs, coeffs = parse_ab_coeffs_text(kp_ab, '3:1:1')
        curves.append(('KnotPlot converted AB 3:1:1', 'legacy_import', coeffs, float(attrs['L']), float(attrs['D'])))

    with zipfile.ZipFile('/mnt/data/Fremlin-Knot_FourierSeries_3_1.zip') as zp:
        for name, role in [('knot.3_1.fseries', 'analytic_test_default'),
                           ('knot.3_1p.fseries', 'analytic_test_p'),
                           ('knot.3_1u.fseries', 'analytic_test_torus_u')]:
            txt = zp.read('Fremlin-Knot_FourierSeries_3_1/' + name).decode('utf-8', 'replace')
            curves.append(('Fremlin ' + name, role, parse_fseries(txt), None, None))

    rows = [metrics(*c) for c in curves]
    df = pd.DataFrame(rows)
    csv_path = Path('/mnt/data/trefoil_three_sources_test_results.csv')
    df.to_csv(csv_path, index=False)

    main_cols = ['source','role','harmonics','reported_L_over_D','native_length','contact_diameter_approx',
                 'contact_normalized_L_over_D','Ltot_used_for_calc','mass_scale_factor_vs_ideal','raw_length_factor_vs_ideal','closure_gap']
    md = []
    md.append('# SSTcore trefoil source comparison\n')
    md.append('This compares the trefoil as represented by `ideal.txt`, the KnotPlot converted AB/Fourier source, and Fremlin Fourier-series sources.\n')
    md.append('Important: only the Gilbert `ideal.txt` entry is canon-ready for `L_K`, mass-functional and final benchmark use. KnotPlot and Fremlin are compatibility / analytic test sources unless explicitly normalized and labelled.\n')
    md.append(df[main_cols].to_markdown(index=False, floatfmt='.9g'))
    md.append('\n\n## Interpretation\n')
    md.append('- `reported_L_over_D` is trusted only for the Gilbert ideal source. The KnotPlot converted AB file carries `D=1` after conversion, but its native length is ~57 and should not be used as canon ropelength.\n')
    md.append('- `contact_normalized_L_over_D` uses an approximate nonlocal contact diameter. It is a diagnostic, not a theorem. It recovers the ideal trefoil near 16.37 and shows how non-ideal sources drift.\n')
    md.append('- `mass_scale_factor_vs_ideal` shows how any SST quantity linear in `Ltot` changes if that geometry is used in place of the canon ideal trefoil.\n')
    md.append('- The Fremlin default trefoil is close in raw length, but contact-normalized ropelength is about 4.3% high. KnotPlot is unsafe if used literally: raw length is ~3.48x the ideal source.\n')
    md_path = Path('/mnt/data/trefoil_three_sources_test_report.md')
    md_path.write_text('\n'.join(md), encoding='utf-8')
    print(df[main_cols].to_string(index=False))
    print(csv_path)
    print(md_path)

if __name__ == '__main__':
    main()
