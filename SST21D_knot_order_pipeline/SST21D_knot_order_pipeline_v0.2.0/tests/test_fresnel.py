from pathlib import Path
import zipfile
import numpy as np

from sst21d.fresnel import (
    SourceFile, parse_fseries_file, parse_short_file, evaluate_fseries,
    infer_harmonic_origin, scan_fresnel_source,
)


def test_zero_precision_styles_are_equivalent():
    a = SourceFile('3_1/knot.3_1a.fseries', b'% test\n0.000 0.000 0.000 0.000 0.000 0.000\n1 0 0 1 0 0\n')
    b = SourceFile('3_1/knot.3_1b.fseries', b'% test\n0.000000 0.000000 0.000000 0.000000 0.000000 0.000000\n1 0 0 1 0 0\n')
    pa, pb = parse_fseries_file(a), parse_fseries_file(b)
    assert np.array_equal(pa.coefficients, pb.coefficients)
    assert pa.zero_token_styles != pb.zero_token_styles


def test_paired_short_resolves_all_zero_first_harmonic_as_j1():
    # j=1 row is exactly zero; j=2 and j=3 make a nondegenerate closed curve.
    text = b'% no explicit constant row\n0 0 0 0 0 0\n1 0 0 1 0 0\n0.2 0 0 0 0.3 0\n'
    fs = parse_fseries_file(SourceFile('x/knot.x.fseries', text))
    points = evaluate_fseries(fs, 96, harmonic_origin=1)
    short_text = ('% paired\n' + '\n'.join('%.12g %.12g %.12g' % tuple(p) for p in points) + '\n').encode()
    sh = parse_short_file(SourceFile('x/knot.x.short', short_text))
    decision = infer_harmonic_origin(fs, sh, compare_samples=64)
    assert decision.harmonic_origin == 1
    assert decision.status == 'RESOLVED'
    assert decision.rmsd_j1 < decision.rmsd_j0


def test_explicit_constant_term_comment_resolves_j0():
    fs = parse_fseries_file(SourceFile(
        'x/knot.x.fseries',
        b'% constant term set to 0.\n0 0 0 0 0 0\n1 0 0 1 0 0\n'
    ))
    decision = infer_harmonic_origin(fs, None)
    assert decision.harmonic_origin == 0
    assert decision.method == 'EXPLICIT_CONSTANT_TERM_COMMENT'


def test_short_accepts_three_columns():
    sh = parse_short_file(SourceFile('x/knot.x.short', b'% x\n0 0 0\n1 0 0\n0 1 0\n'))
    assert sh.points.shape == (3, 3)



def test_fortran_d_exponent_and_signed_zero():
    fs = parse_fseries_file(SourceFile(
        'x/knot.x.fseries',
        b'% test\n-0.000000 0.0 0 0 0 0\n1.0D+00 0 0 1.0d+00 0 0\n'
    ))
    assert fs.coefficients[0, 0] == 0.0
    assert fs.coefficients[1, 0] == 1.0
    assert '-0.000000' in fs.zero_token_styles

def test_bundled_archive_inventory():
    archive = Path(__file__).parents[1] / 'data' / 'Fresnel_FourierSeries.zip'
    scan = scan_fresnel_source(archive)
    assert scan['fseries_count'] == 78
    assert scan['short_count'] == 76
    assert scan['paired_count'] == 73
    assert scan['parse_error_count'] == 0
    assert all(r['origin_status'] == 'RESOLVED' for r in scan['rows'] if r['fseries_present'])
