"""Tests for sst_knot_catalog (matches GLSL torusKnot formula)."""

from __future__ import annotations

import math

import pytest

from sst_knot_catalog import (
    BRAID_K,
    BRAID_N_STRANDS,
    CLASSIC_TREFOIL_SCALE,
    COPRIME_CATALOGUE,
    BG_COL,
    KIND_CIRCLE,
    KIND_CINQUE,
    KIND_CUSTOM,
    KIND_L41,
    KIND_L52,
    KIND_L112,
    KIND_T34,
    KIND_T69,
    KIND_T615,
    KIND_T621,
    KIND_TREFOIL,
    MODE_PARTICLES,
    MODE_STRANDS,
    LOG_SPIRAL_EPS,
    NESTED_BRAID_LEAVES,
    NESTED_BRAID_STRETCH,
    PHI,
    STRETCH_BASS,
    SWIRL_CLOCK_BEADS,
    TORUS_R,
    TORUS_r,
    TREFOIL_R0,
    TREFOIL_r_SCALE,
    TWOPI,
    VORONOI_BASE_SCALE,
    VORONOI_CIRCLE_RAD,
    VORONOI_NUM_PATHS,
    VORONOI_PARTICLE_COUNT,
    accumulate_path_phase,
    apply_bass_stretch,
    braid_chirality_side,
    braid_phases,
    braid_strand_point,
    catalogue_with_chirality,
    chirality_flip,
    circle_path_2d,
    classic_trefoil_point,
    coprime_pairs,
    domain_twist_windings,
    gcd,
    is_coprime,
    is_unknot,
    linking_proxy,
    log_spiral_plane,
    nested_braid_point,
    particle_glow_dist,
    path_phase_index,
    path_freq_x,
    path_phase_speed,
    path_stereo_width,
    rgb_strand_chase,
    strand_width_px,
    voronoi_path_particle,
    kind_spec,
    phi_chirality_sign,
    phi_log_scale,
    resolve_voronoi_kind,
    spiral_arm_phase,
    torus_knot_path_2d,
    torus_knot_point,
    torus_knot_polyline,
    twisted_ladder_path_2d,
    voronoi_filament_path,
    voronoi_filament_paths,
    voronoi_path_draw,
    voronoi_path_knot,
    voronoi_path_layout,
    voronoi_path_of_particle,
    voronoi_path_torus,
)


def test_gcd_basic():
    assert gcd(2, 3) == 1
    assert gcd(4, 6) == 2
    assert gcd(15, 25) == 5
    assert gcd(-2, 3) == 1


def test_is_coprime_catalogue():
    for p, q in COPRIME_CATALOGUE:
        assert is_coprime(p, q)
        assert not is_unknot(p, q)


def test_non_coprime_means_linked_components():
    # gcd=d>1 => d linked components (research-track note)
    assert gcd(4, 6) == 2
    assert not is_coprime(4, 6)


def test_chirality_flip():
    assert chirality_flip(2, 3) == (2, -3)
    assert chirality_flip(2, -3) == (2, 3)


def test_linking_proxy_sign_tracks_chirality():
    assert linking_proxy(2, 3) == 6
    assert linking_proxy(2, -3) == -6


def test_unknot_detection():
    assert is_unknot(5, 1)
    assert is_unknot(1, 7)
    assert not is_unknot(2, 3)


def test_torus_knot_closed():
    # phi=0 and phi=2π coincide for integer p,q
    a = torus_knot_point(2, 3, 0.0)
    b = torus_knot_point(2, 3, TWOPI)
    assert math.isclose(a[0], b[0], abs_tol=1e-9)
    assert math.isclose(a[1], b[1], abs_tol=1e-9)
    assert math.isclose(a[2], b[2], abs_tol=1e-9)


def test_torus_knot_matches_glsl_trefoil_sample():
    # Spot-check T(2,3) at known angles against the GLSL formula
    phi = math.pi / 3.0
    p, q, R, r = 2.0, 3.0, TORUS_R, TORUS_r
    cq, sq = math.cos(q * phi), math.sin(q * phi)
    cp, sp = math.cos(p * phi), math.sin(p * phi)
    expected = ((R + r * cq) * cp, (R + r * cq) * sp, r * sq)
    got = torus_knot_point(p, q, phi)
    assert all(math.isclose(g, e, abs_tol=1e-12) for g, e in zip(got, expected))


def test_chirality_mirror_z_sign():
    # Negating q flips the z component (sq -> -sq at same phi)
    phi = 0.7
    _, _, z_plus = torus_knot_point(2, 3, phi)
    _, _, z_minus = torus_knot_point(2, -3, phi)
    assert math.isclose(z_plus, -z_minus, abs_tol=1e-12)


def test_polyline_length_and_closure():
    pts = torus_knot_polyline(2, 3, n=64)
    assert len(pts) == 64
    # First point equals the closed-loop sample at phi=0
    assert pts[0] == torus_knot_point(2, 3, 0.0)


def test_polyline_rejects_tiny_n():
    with pytest.raises(ValueError):
        torus_knot_polyline(2, 3, n=1)


def test_coprime_pairs_filter():
    pairs = coprime_pairs(5, 5)
    assert (2, 3) in pairs
    assert (4, 4) not in pairs
    assert (2, 4) not in pairs


def test_catalogue_with_chirality_length():
    cat = catalogue_with_chirality()
    assert len(cat) == 2 * len(COPRIME_CATALOGUE)
    assert cat[0] == (2, 3)
    assert cat[len(COPRIME_CATALOGUE)] == (2, -3)


def test_log_spiral_plane_matches_glsl_formula():
    x, y, p, q = 0.4, -0.25, 2.0, 3.0
    rho = math.hypot(x, y)
    theta = math.atan2(y, x)
    lg = math.log(max(rho, LOG_SPIRAL_EPS))
    expected = (lg - 0.5 * p * theta, lg - 0.5 * q * theta)
    got = log_spiral_plane(x, y, p, q)
    assert all(math.isclose(g, e, abs_tol=1e-12) for g, e in zip(got, expected))


def test_log_spiral_chirality_flips_q_arm():
    x, y = 0.3, 0.2
    _, v_plus = log_spiral_plane(x, y, 2.0, 3.0)
    _, v_minus = log_spiral_plane(x, y, 2.0, -3.0)
    # q in the v-arm: flipping q flips the -0.5*q*theta term
    theta = math.atan2(y, x)
    assert math.isclose(v_plus - v_minus, -0.5 * 6.0 * theta, abs_tol=1e-12)


def test_spiral_arm_phase_in_unit_interval():
    ph = spiral_arm_phase(1.3, arms=2.0, phase=0.1)
    assert 0.0 <= ph < 1.0


def test_spiral_arm_phase_rejects_zero_arms():
    with pytest.raises(ValueError):
        spiral_arm_phase(0.5, arms=0.0)


def test_braid_phases_three_strands():
    ph = braid_phases(3)
    assert len(ph) == 3
    assert math.isclose(ph[0], 0.0)
    assert math.isclose(ph[1], TWOPI / 3.0)
    assert math.isclose(ph[2], 2.0 * TWOPI / 3.0)


def test_braid_phases_rejects_empty():
    with pytest.raises(ValueError):
        braid_phases(0)


def test_braid_strand_matches_glsl_formula():
    t, k, phase, side = 0.7, BRAID_K, TWOPI / 3.0, 1.0
    ring_r, braid_r = 1.35, 0.28
    ang = t
    cx = ring_r * math.cos(ang)
    cz = ring_r * math.sin(ang)
    nx, nz = math.cos(ang), math.sin(ang)
    a = side * (k * t + phase)
    ox = braid_r * math.cos(a)
    oy = braid_r * math.sin(a)
    expected = (cx + nx * ox, oy, cz + nz * ox)
    got = braid_strand_point(t, k, phase, side)
    assert all(math.isclose(g, e, abs_tol=1e-12) for g, e in zip(got, expected))


def test_braid_closed_periodicity():
    # t=0 and t=2π coincide for integer k
    a = braid_strand_point(0.0, BRAID_K, 0.0, 1.0)
    b = braid_strand_point(TWOPI, BRAID_K, 0.0, 1.0)
    assert all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))


def test_braid_chirality_mirrors_y():
    t, phase = 1.1, 0.0
    _, y_plus, _ = braid_strand_point(t, BRAID_K, phase, side=1.0)
    _, y_minus, _ = braid_strand_point(t, BRAID_K, phase, side=-1.0)
    assert math.isclose(y_plus, -y_minus, abs_tol=1e-12)


def test_braid_chirality_side_cycle():
    assert braid_chirality_side(0.5) == 1.0
    assert braid_chirality_side(2.5) == -1.0
    assert braid_chirality_side(4.5) == 1.0


def test_braid_default_strand_count():
    assert BRAID_N_STRANDS == 3
    assert len(braid_phases()) == 3


def test_domain_twist_windings_positive_for_coprime():
    for p, q in COPRIME_CATALOGUE:
        w1, w2, shear = domain_twist_windings(float(p), float(q))
        assert w1 > 0.0 and w2 > 0.0
        assert shear == 1.0
        assert math.isclose(w1, 0.15 + 0.05 * p)
        assert math.isclose(w2, 0.25 + 0.08 * q)


def test_domain_twist_chirality_flips_shear():
    _, _, s_plus = domain_twist_windings(2.0, 3.0)
    _, _, s_minus = domain_twist_windings(2.0, -3.0)
    assert s_plus == 1.0
    assert s_minus == -1.0
    w1a, w2a, _ = domain_twist_windings(2.0, 3.0)
    w1b, w2b, _ = domain_twist_windings(2.0, -3.0)
    assert math.isclose(w1a, w1b)
    assert math.isclose(w2a, w2b)


def test_classic_trefoil_matches_glsl_formula():
    t = 1.1
    scale = CLASSIC_TREFOIL_SCALE
    expected = (
        (math.sin(t) + 2.0 * math.sin(2.0 * t)) * scale,
        (math.cos(t) - 2.0 * math.cos(2.0 * t)) * scale,
        (-math.sin(3.0 * t)) * scale,
    )
    got = classic_trefoil_point(t, scale)
    assert all(math.isclose(g, e, abs_tol=1e-12) for g, e in zip(got, expected))


def test_classic_trefoil_closed():
    a = classic_trefoil_point(0.0)
    b = classic_trefoil_point(TWOPI)
    assert all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))


def test_swirl_clock_beads_constant():
    assert SWIRL_CLOCK_BEADS == 24
    assert SWIRL_CLOCK_BEADS % 2 == 0


def test_phi_golden_ratio():
    assert math.isclose(PHI, (1.0 + 5.0 ** 0.5) / 2.0, abs_tol=1e-12)
    assert math.isclose(PHI, 1.61803398875, abs_tol=1e-9)


def test_phi_log_scale_matches_glsl():
    assert math.isclose(phi_log_scale(2.0), 2.5 + 0.2 * 2.0)
    assert math.isclose(phi_log_scale(-5.0), 2.5 + 0.2 * 5.0)
    assert phi_log_scale(3.0) > 0.0


def test_phi_chirality_sign():
    assert phi_chirality_sign(3.0) == 1.0
    assert phi_chirality_sign(-3.0) == -1.0
    assert phi_chirality_sign(0.0) == 1.0


def test_torus_knot_path_2d_matches_glsl():
    t, p, q, R, r, scale = 0.3, 2.0, 3.0, TORUS_R, TORUS_r, 1.0
    phi = t * TWOPI
    cq = math.cos(q * phi)
    cp = math.cos(p * phi)
    sp = math.sin(p * phi)
    expected = ((R + r * cq) * cp * scale, (R + r * cq) * sp * scale)
    got = torus_knot_path_2d(t, p, q, R, r, scale)
    assert all(math.isclose(g, e, abs_tol=1e-12) for g, e in zip(got, expected))


def test_torus_knot_path_2d_closed():
    a = torus_knot_path_2d(0.0, 2.0, 3.0)
    b = torus_knot_path_2d(1.0, 2.0, 3.0)
    assert all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))


def test_circle_path_2d_unit():
    x, y = circle_path_2d(0.0, (0.0, 0.0), 1.0)
    assert math.isclose(x, 1.0, abs_tol=1e-12)
    assert math.isclose(y, 0.0, abs_tol=1e-12)


def test_voronoi_path_assignment():
    assert VORONOI_NUM_PATHS == 8
    assert VORONOI_PARTICLE_COUNT == 1200
    assert voronoi_path_of_particle(0) == 0
    assert voronoi_path_of_particle(1) == 1
    assert voronoi_path_of_particle(8) == 0
    assert len(voronoi_filament_paths()) == VORONOI_NUM_PATHS


def test_voronoi_path_rejects_zero_paths():
    with pytest.raises(ValueError):
        voronoi_path_of_particle(0, num_paths=0)


def test_voronoi_filament_path_centering():
    canvas = (800.0, 450.0)
    unit = canvas[1] * VORONOI_BASE_SCALE
    t = 0.25

    for path_id in range(VORONOI_NUM_PATHS):
        geom, p, q = voronoi_path_knot(path_id)
        ox, oy, size_scale = voronoi_path_layout(path_id)
        R, rr = voronoi_path_torus(path_id)
        center = (canvas[0] * 0.5 + ox * unit, canvas[1] * 0.5 + oy * unit)
        got = voronoi_filament_path(t, path_id, canvas)
        if geom == 1:
            expected = circle_path_2d(
                t, center, VORONOI_CIRCLE_RAD * R * unit * size_scale
            )
        elif geom == 2:
            scale = unit * size_scale
            kx, ky = twisted_ladder_path_2d(t, p, q, R, rr, scale)
            expected = (kx + center[0], ky + center[1])
        else:
            scale = unit * size_scale
            kx, ky = torus_knot_path_2d(t, p, q, R, rr, scale)
            expected = (kx + center[0], ky + center[1])
        assert all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(got, expected))


def test_voronoi_concentric_trefoil_kit():
    # All 8 paths = Trefoil, off=0, R = TREFOIL_R0 * (1..8), paste rr character
    for i in range(VORONOI_NUM_PATHS):
        assert voronoi_path_knot(i) == (0, 2.0, 3.0)
        assert voronoi_path_layout(i) == (0.0, 0.0, 1.0)
        R, rr = voronoi_path_torus(i)
        assert math.isclose(R, TREFOIL_R0 * float(i + 1), abs_tol=1e-12)
    assert voronoi_path_torus(0)[1] == pytest.approx(0.42 * TREFOIL_r_SCALE)
    assert voronoi_path_torus(3)[1] == pytest.approx(0.0)
    assert voronoi_path_torus(7)[1] == pytest.approx(0.0)
    # Largest ring still fits canvas height margin
    R_max, rr_max = voronoi_path_torus(7)
    assert (R_max + rr_max) * VORONOI_BASE_SCALE <= 0.45 + 1e-9
    assert voronoi_path_knot(8) == voronoi_path_knot(0)


def test_resolve_voronoi_kind_favorites():
    assert kind_spec(KIND_TREFOIL) == (0, 2.0, 3.0)
    assert resolve_voronoi_kind(KIND_CINQUE) == (0, 2.0, 5.0)
    assert resolve_voronoi_kind(KIND_T34) == (0, 3.0, 4.0)
    assert resolve_voronoi_kind(KIND_CIRCLE) == (1, 0.0, 0.0)
    assert resolve_voronoi_kind(KIND_CUSTOM, 7.0, -2.0) == (0, 7.0, -2.0)


def test_resolve_voronoi_kind_torus_links():
    # gcd(6,9)=gcd(6,15)=gcd(6,21)=3 → 3-component torus links
    assert resolve_voronoi_kind(KIND_T69) == (0, 6.0, 9.0)
    assert resolve_voronoi_kind(KIND_T615) == (0, 6.0, 15.0)
    assert resolve_voronoi_kind(KIND_T621) == (0, 6.0, 21.0)
    assert gcd(6, 9) == 3
    assert gcd(6, 15) == 3
    assert gcd(6, 21) == 3


def test_voronoi_filament_path_closed():
    canvas = (640.0, 360.0)
    for path_id in range(VORONOI_NUM_PATHS):
        a = voronoi_filament_path(0.0, path_id, canvas)
        b = voronoi_filament_path(1.0, path_id, canvas)
        assert all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))


def test_resolve_ladder_kinds():
    assert resolve_voronoi_kind(KIND_L41) == (2, 2.0, 1.0)
    assert resolve_voronoi_kind(KIND_L52) == (2, 3.0, 1.0)
    assert resolve_voronoi_kind(KIND_L112) == (2, 9.0, 1.0)


def test_voronoi_path_draw_modes_and_sizes():
    assert BG_COL == (0.0, 0.0, 0.0)
    for i in range(VORONOI_NUM_PATHS):
        mode, psz, sw = voronoi_path_draw(i)
        size, color, speed = voronoi_path_particle(i)
        assert mode == (MODE_PARTICLES if i % 2 == 0 else MODE_STRANDS)
        assert psz == pytest.approx(0.75 + 0.08 * i)
        assert size == pytest.approx(psz)
        assert speed == pytest.approx(0.70 + 0.12 * i)
        assert sw == pytest.approx(0.012)
        assert all(0.0 <= c <= 1.0 for c in color)
    assert voronoi_path_particle(0)[1] == pytest.approx((0.05, 0.45, 0.85))
    assert path_phase_speed(0.5, 0.5, 2.0) == pytest.approx(
        2.0 * path_phase_speed(0.5, 0.5, 1.0)
    )
    assert particle_glow_dist(10.0, 2.0) == pytest.approx(5.0)
    assert particle_glow_dist(10.0, 0.0) == pytest.approx(10.0 / 0.05)
    assert strand_width_px(0.012, 1.0, 720.0) == pytest.approx(0.012 * 720.0)
    assert strand_width_px(0.012, 0.0, 720.0) == pytest.approx(0.012 * 0.05 * 720.0)
    chase0 = rgb_strand_chase(0.0, 0.0)
    chase1 = rgb_strand_chase(0.0, 0.25)
    assert chase0 != pytest.approx(chase1)
    assert all(0.0 <= c <= 1.0 for c in chase0)


def test_twisted_ladder_path_closed():
    a = twisted_ladder_path_2d(0.0, 2.0, 1.0)
    b = twisted_ladder_path_2d(1.0, 2.0, 1.0)
    assert all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(a, b))


def test_accumulate_path_phase_never_rewinds():
    assert path_phase_index(0) == VORONOI_PARTICLE_COUNT
    assert path_phase_index(7) == VORONOI_PARTICLE_COUNT + 7
    a = accumulate_path_phase(0.4, 0.016, 0.06)
    b = accumulate_path_phase(a, 0.016, 0.02)  # speed drop must still go forward
    assert a > 0.4
    assert b > a or (a > 0.95 and b < 0.1)  # wrap is ok
    # iTime * speed would jump back: 10*0.06=0.6 vs 10.016*0.02≈0.20
    assert accumulate_path_phase(0.6, 0.016, 0.02) > 0.6


def test_path_audio_helpers():
    assert path_freq_x(0) == pytest.approx(0.0)
    assert path_freq_x(7) == pytest.approx(1.0)
    assert path_stereo_width(0) == pytest.approx(0.0)
    assert path_stereo_width(7) == pytest.approx(1.0)
    centre = (400.0, 225.0)
    tar = (500.0, 225.0)
    stretched = apply_bass_stretch(tar, 1.0, centre, stretch=STRETCH_BASS)
    assert stretched[0] > tar[0]
    assert math.isclose(stretched[1], tar[1], abs_tol=1e-12)


def test_nested_braid_leaves_count():
    assert NESTED_BRAID_LEAVES == 27
    assert NESTED_BRAID_LEAVES == 3 ** 3


def test_nested_braid_point_matches_glsl():
    t, phase, stretch, side = 1.2, 0.4, NESTED_BRAID_STRETCH, 1.0
    sn = math.sin(t + phase)
    cs = math.cos(t + phase)
    expected = (cs, t * stretch, side * sn * cs)
    got = nested_braid_point(t, phase, stretch, side)
    assert all(math.isclose(g, e, abs_tol=1e-12) for g, e in zip(got, expected))


def test_nested_braid_chirality_mirrors_z():
    t, phase = 0.8, 0.1
    _, _, z_plus = nested_braid_point(t, phase, side=1.0)
    _, _, z_minus = nested_braid_point(t, phase, side=-1.0)
    assert math.isclose(z_plus, -z_minus, abs_tol=1e-12)

