"""T(p,q) / log-spiral / closed-braid helpers for SST Shadertoy GLSL.

[BRIDGE] visualisation catalogue — not a numerical certificate.
Hyperbolic 4_1 is out of scope here (no IQ figure-8 formula).
"""

from __future__ import annotations

import math
from typing import Iterable

# Same defaults as the GLSL #defines
TORUS_R = 1.15
TORUS_r = 0.42
TWOPI = 2.0 * math.pi
LOG_SPIRAL_EPS = 1e-4
CLASSIC_TREFOIL_SCALE = 0.55
SWIRL_CLOCK_BEADS = 24
PHI = (1.0 + 5.0 ** 0.5) / 2.0  # golden ratio — GLSL #define PHI
VORONOI_PARTICLE_COUNT = 1200
VORONOI_NUM_PATHS = 8
NESTED_BRAID_LEAVES = 27
NESTED_BRAID_STRETCH = 1.5

# Closed braid (sst_closed_braid.glsl)
BRAID_RING_R = 1.35
BRAID_R = 0.28
BRAID_K = 2.0
BRAID_N_STRANDS = 3

# Coprime (p, |q|) pairs used by the shader cycle (positive chirality half)
COPRIME_CATALOGUE: tuple[tuple[int, int], ...] = (
    (2, 3),
    (2, 5),
    (3, 4),
    (3, 5),
    (4, 5),
    (5, 6),
)


def gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def is_coprime(p: int, q: int) -> bool:
    return gcd(p, q) == 1


def chirality_flip(p: int, q: int) -> tuple[int, int]:
    """q -> -q (matter <-> antimatter visualisation convention)."""
    return (p, -q)


def linking_proxy(p: int, q: int) -> int:
    """Toroidal linking proxy p*q (sign tracks chirality). Not a full Lk proof."""
    return p * q


def is_unknot(p: int, q: int) -> bool:
    """T(p,±1) and T(±1,q) are unknots on a torus."""
    return abs(p) == 1 or abs(q) == 1


def torus_knot_point(
    p: float,
    q: float,
    phi: float,
    R: float = TORUS_R,
    r: float = TORUS_r,
) -> tuple[float, float, float]:
    """Isotropic T(p,q) on a torus — identical to GLSL torusKnot()."""
    cq = math.cos(q * phi)
    sq = math.sin(q * phi)
    cp = math.cos(p * phi)
    sp = math.sin(p * phi)
    return ((R + r * cq) * cp, (R + r * cq) * sp, r * sq)


def torus_knot_polyline(
    p: float,
    q: float,
    n: int = 64,
    R: float = TORUS_R,
    r: float = TORUS_r,
) -> list[tuple[float, float, float]]:
    if n < 2:
        raise ValueError("n must be >= 2")
    return [
        torus_knot_point(p, q, TWOPI * i / n, R, r) for i in range(n)
    ]


def coprime_pairs(p_max: int = 7, q_max: int = 7) -> list[tuple[int, int]]:
    """Positive coprime pairs with p,q >= 2 (excludes unknots T(*,1))."""
    out: list[tuple[int, int]] = []
    for p in range(2, p_max + 1):
        for q in range(2, q_max + 1):
            if is_coprime(p, q):
                out.append((p, q))
    return out


def catalogue_with_chirality(
    base: Iterable[tuple[int, int]] = COPRIME_CATALOGUE,
) -> list[tuple[int, int]]:
    """Shader cycle: each base pair then its chirality flip."""
    pairs: list[tuple[int, int]] = []
    for p, q in base:
        pairs.append((p, q))
    for p, q in base:
        pairs.append(chirality_flip(p, q))
    return pairs


def log_spiral_plane(
    x: float,
    y: float,
    p: float,
    q: float,
) -> tuple[float, float]:
    """Log-polar spiral plane — identical to GLSL logSpiralPlane()."""
    rho = math.hypot(x, y)
    theta = math.atan2(y, x)
    lg = math.log(max(rho, LOG_SPIRAL_EPS))
    u = lg - 0.5 * (p * theta)
    v = lg - 0.5 * (q * theta)
    return (u, v)


def spiral_arm_phase(u: float, arms: float, phase: float = 0.0) -> float:
    """Fractional position along a spiral arm (0..1); used for clock ticks."""
    if arms == 0:
        raise ValueError("arms must be non-zero")
    a = u * abs(arms) - phase * abs(arms)
    return a - math.floor(a)


def braid_phases(n: int = BRAID_N_STRANDS) -> list[float]:
    """Strand phase offsets 2π i / n — identical to GLSL loop over N_STRANDS."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return [TWOPI * i / n for i in range(n)]


def braid_strand_point(
    t: float,
    k: float = BRAID_K,
    phase: float = 0.0,
    side: float = 1.0,
    ring_r: float = BRAID_RING_R,
    braid_r: float = BRAID_R,
) -> tuple[float, float, float]:
    """Closed-ring braid strand — identical to GLSL braidStrandPoint()."""
    ang = t
    cx = ring_r * math.cos(ang)
    cz = ring_r * math.sin(ang)
    nx, nz = math.cos(ang), math.sin(ang)
    a = side * (k * t + phase)
    ox = braid_r * math.cos(a)
    oy = braid_r * math.sin(a)
    return (cx + nx * ox, oy, cz + nz * ox)


def braid_chirality_side(time_sec: float) -> float:
    """~2s matter / antimatter flip — same as GLSL chiralitySide()."""
    return 1.0 if (time_sec % 4.0) < 2.0 else -1.0


def domain_twist_windings(p: float, q: float) -> tuple[float, float, float]:
    """(w1, w2, shear_sign) — identical to GLSL domainTwistWindings()."""
    w1 = 0.15 + 0.05 * abs(p)
    w2 = 0.25 + 0.08 * abs(q)
    shear_sign = -1.0 if q < 0.0 else 1.0
    return (w1, w2, shear_sign)


def classic_trefoil_point(
    t: float,
    scale: float = CLASSIC_TREFOIL_SCALE,
) -> tuple[float, float, float]:
    """Classic T(2,3) — identical to GLSL classicTrefoil()."""
    return (
        (math.sin(t) + 2.0 * math.sin(2.0 * t)) * scale,
        (math.cos(t) - 2.0 * math.cos(2.0 * t)) * scale,
        (-math.sin(3.0 * t)) * scale,
    )


def phi_log_scale(p: float) -> float:
    """Log-spiral zoom scale from |p| — identical to GLSL phiLogScale()."""
    return 2.5 + 0.2 * abs(p)


def phi_chirality_sign(q: float) -> float:
    """Rotation sign from q — identical to GLSL chirality from knotPQ()."""
    return -1.0 if q < 0.0 else 1.0


def torus_knot_path_2d(
    t: float,
    p: float,
    q: float,
    R: float = TORUS_R,
    r: float = TORUS_r,
    scale: float = 1.0,
) -> tuple[float, float]:
    """2D projection of isotropic T(p,q) — identical to GLSL torusKnotPath2D()."""
    phi = t * TWOPI
    cq = math.cos(q * phi)
    cp = math.cos(p * phi)
    sp = math.sin(p * phi)
    return ((R + r * cq) * cp * scale, (R + r * cq) * sp * scale)


def circle_path_2d(
    t: float,
    center: tuple[float, float] = (0.0, 0.0),
    rad: float = 1.0,
) -> tuple[float, float]:
    """Unknot / link component circle — identical to GLSL circlePath2D()."""
    a = t * TWOPI
    return (center[0] + rad * math.cos(a), center[1] + rad * math.sin(a))


def voronoi_path_of_particle(particle_id: int, num_paths: int = VORONOI_NUM_PATHS) -> int:
    """Which filament path a particle follows — identical to GLSL pathOfParticle()."""
    if num_paths < 1:
        raise ValueError("num_paths must be >= 1")
    return particle_id % num_paths


# Matches GLSL const int kinds (no KIND_*_M — flip later via q = -q).
KIND_CUSTOM = 0
KIND_CIRCLE = 1
KIND_TREFOIL = 2
KIND_CINQUE = 3
KIND_T34 = 4
KIND_T35 = 5
KIND_T45 = 6
KIND_T56 = 7
KIND_T69 = 8
KIND_T615 = 9
KIND_T621 = 10
KIND_L41 = 11
KIND_L52 = 12
KIND_L61 = 13
KIND_L72 = 14
KIND_L81 = 15
KIND_L92 = 16
KIND_L101 = 17
KIND_L112 = 18

MODE_PARTICLES = 0
MODE_STRANDS = 1

# named_kind -> (geom 0=torus/1=circle/2=ladder, p, q)
# For geom 2: p = halfTwists, q = side (±1).
VORONOI_KIND_TABLE: dict[int, tuple[int, float, float]] = {
    KIND_CIRCLE: (1, 0.0, 0.0),
    KIND_TREFOIL: (0, 2.0, 3.0),
    KIND_CINQUE: (0, 2.0, 5.0),
    KIND_T34: (0, 3.0, 4.0),
    KIND_T35: (0, 3.0, 5.0),
    KIND_T45: (0, 4.0, 5.0),
    KIND_T56: (0, 5.0, 6.0),
    KIND_T69: (0, 6.0, 9.0),
    KIND_T615: (0, 6.0, 15.0),
    KIND_T621: (0, 6.0, 21.0),
    KIND_L41: (2, 2.0, 1.0),
    KIND_L52: (2, 3.0, 1.0),
    KIND_L61: (2, 4.0, 1.0),
    KIND_L72: (2, 5.0, 1.0),
    KIND_L81: (2, 6.0, 1.0),
    KIND_L92: (2, 7.0, 1.0),
    KIND_L101: (2, 8.0, 1.0),
    KIND_L112: (2, 9.0, 1.0),
}

VORONOI_BASE_SCALE = 0.22
VORONOI_CIRCLE_RAD = 0.55
TREFOIL_R0 = 0.22
TREFOIL_r_SCALE = 0.30
# Paste rr character × TREFOIL_r_SCALE (matches GLSL pathAt).
_PASTE_RR = (0.42, 0.42, 0.38, 0.0, 0.40, 0.40, 0.36, 0.0)

_PARTICLE_COLORS: tuple[tuple[float, float, float], ...] = (
    (0.05, 0.45, 0.85),
    (0.85, 0.12, 0.55),
    (0.20, 0.75, 0.55),
    (0.95, 0.55, 0.20),
    (0.45, 0.35, 0.95),
    (0.20, 0.85, 0.90),
    (0.95, 0.25, 0.35),
    (0.95, 0.55, 0.20),
)


def _particle_cfg(i: int) -> tuple[float, tuple[float, float, float], float]:
    """(size, color, speed) — identical to GLSL pathAt particle defaults."""
    return (0.75 + 0.08 * float(i), _PARTICLE_COLORS[i], 0.70 + 0.12 * float(i))


def _path_spec_row(i: int) -> tuple[
    int, float, float, float, float, float, float, float,
    int, float, float, float, float, float, float,
]:
    psz, col, spd = _particle_cfg(i)
    return (
        KIND_TREFOIL,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        TREFOIL_R0 * float(i + 1),
        _PASTE_RR[i] * TREFOIL_r_SCALE,
        MODE_PARTICLES if i % 2 == 0 else MODE_STRANDS,
        psz,
        col[0],
        col[1],
        col[2],
        spd,
        0.012,
    )


# (kind, p, q, ox, oy, scale, R, rr, mode, psize, pr, pg, pb, pspeed, strandWidth)
VORONOI_PATH_SPECS: tuple[
    tuple[
        int, float, float, float, float, float, float, float,
        int, float, float, float, float, float, float,
    ],
    ...,
] = tuple(_path_spec_row(i) for i in range(VORONOI_NUM_PATHS))

# Audio UX mirrors (Common knobs)
STRETCH_BASS = 0.35
STEREO_AMP = 0.12
HUE_AUDIO = 0.05
BG_COL = (0.0, 0.0, 0.0)


def kind_spec(
    named: int,
    p_in: float = 0.0,
    q_in: float = 0.0,
) -> tuple[int, float, float]:
    """(geom, p, q) — identical to GLSL kindSpec() + CUSTOM branch."""
    if named == KIND_CUSTOM:
        return (0, p_in, q_in)
    if named in VORONOI_KIND_TABLE:
        return VORONOI_KIND_TABLE[named]
    return (0, p_in, q_in)


def resolve_voronoi_kind(
    named: int,
    p_in: float = 0.0,
    q_in: float = 0.0,
) -> tuple[int, float, float]:
    """Alias of kind_spec — kept for existing tests."""
    return kind_spec(named, p_in, q_in)


def twisted_ladder_path_2d(
    t: float,
    half_twists: float,
    side: float,
    R: float = TORUS_R,
    rr: float = TORUS_r,
    scale: float = 1.0,
) -> tuple[float, float]:
    """Original SST Lissajous ladder — identical to GLSL twistedLadderPath2D()."""
    a = t * TWOPI
    k = half_twists
    w = math.floor(k * 0.5) + 1.0
    rad = R + rr * math.cos(k * a)
    x = rad * math.cos(w * a)
    y = rad * math.sin(w * a)
    y += side * rr * 0.35 * math.sin(2.0 * k * a)
    return (x * scale, y * scale)


def path_freq_x(path_id: int, num_paths: int = VORONOI_NUM_PATHS) -> float:
    """Spectrum position 0..1 — identical to GLSL pathFreqX()."""
    n = max(num_paths - 1, 1)
    return float(path_id % num_paths) / float(n)


def path_stereo_width(path_id: int, num_paths: int = VORONOI_NUM_PATHS) -> float:
    """Mono at path 0 → full wide at last path — identical to GLSL pathStereoWidth()."""
    return path_freq_x(path_id, num_paths)


def apply_bass_stretch(
    tar: tuple[float, float],
    bass: float,
    centre: tuple[float, float],
    stretch: float = STRETCH_BASS,
) -> tuple[float, float]:
    """Radial vortex stretch about centre — identical to GLSL applyBassStretch()."""
    s = 1.0 + stretch * bass
    return (
        centre[0] + (tar[0] - centre[0]) * s,
        centre[1] + (tar[1] - centre[1]) * s,
    )


def _path_row(path_id: int) -> tuple:
    if not VORONOI_PATH_SPECS:
        raise ValueError("VORONOI_PATH_SPECS must be non-empty")
    return VORONOI_PATH_SPECS[path_id % len(VORONOI_PATH_SPECS)]


def voronoi_filament_paths() -> tuple[tuple[str, float, float], ...]:
    """Named multi knot/link catalogue used by Buffer B."""
    out: list[tuple[str, float, float]] = []
    for named, p_in, q_in, *_rest in VORONOI_PATH_SPECS:
        geom, p, q = kind_spec(named, p_in, q_in)
        if geom == 1:
            out.append(("unknot_circle", p, q))
        elif geom == 2:
            out.append((f"L({int(p)},{int(q)})", p, q))
        else:
            out.append((f"T({int(p)},{int(q)})", p, q))
    return tuple(out)


def voronoi_path_knot(path_id: int) -> tuple[int, float, float]:
    """(geom, p, q) — identical to GLSL filamentPath kind lookup."""
    named, p_in, q_in, *_rest = _path_row(path_id)
    return kind_spec(named, p_in, q_in)


def voronoi_path_layout(path_id: int) -> tuple[float, float, float]:
    """(offx, offy, scale) — identical to GLSL pathAt layout fields."""
    _n, _p, _q, ox, oy, sc, *_rest = _path_row(path_id)
    return (ox, oy, sc)


def voronoi_path_torus(path_id: int) -> tuple[float, float]:
    """(R, rr) — identical to GLSL pathAt torus fields."""
    row = _path_row(path_id)
    return (row[6], row[7])


def voronoi_path_draw(path_id: int) -> tuple[int, float, float]:
    """(mode, particleSize, strandWidth) — identical to GLSL pathAt draw fields."""
    row = _path_row(path_id)
    return (row[8], row[9], row[14])


def voronoi_path_particle(
    path_id: int,
) -> tuple[float, tuple[float, float, float], float]:
    """(size, color, speed) — identical to GLSL FilamentPath.particle."""
    row = _path_row(path_id)
    return (row[9], (row[10], row[11], row[12]), row[13])


def path_phase_speed(
    mid: float,
    p_band: float,
    path_speed: float,
    base: float = 0.02,
    mid_k: float = 0.04,
) -> float:
    """Audio-scaled phase speed — identical to GLSL pathPhaseSpeed()."""
    audio = base + mid_k * ((1.0 - 0.65) * mid + 0.65 * p_band)
    return max(path_speed, 0.0) * audio


def particle_glow_dist(dist: float, particle_size: float) -> float:
    """Effective glow distance — identical to GLSL dist / max(particleSize, 0.05)."""
    return dist / max(particle_size, 0.05)


def strand_width_px(
    strand_width: float,
    particle_size: float,
    res_y: float,
) -> float:
    """Strand tube width in pixels — identical to GLSL Image MODE_STRANDS."""
    return max(strand_width, 0.002) * max(particle_size, 0.05) * res_y


def rgb_strand_chase(
    t: float,
    phase: float,
    wave: float = 15.0,
) -> tuple[float, float, float]:
    """RGB chase along a strand — identical to GLSL rgbStrandColor chase."""
    a = (t * TWOPI - phase * TWOPI) * wave
    return (
        0.5 + 0.5 * math.sin(a),
        0.5 + 0.5 * math.sin(a + TWOPI / 3.0),
        0.5 + 0.5 * math.sin(a + 2.0 * TWOPI / 3.0),
    )


def path_phase_index(path_id: int, num_paths: int = VORONOI_NUM_PATHS) -> int:
    """Texel after the particle block — identical to GLSL pathPhaseIndex()."""
    if num_paths < 1:
        raise ValueError("num_paths must be >= 1")
    return VORONOI_PARTICLE_COUNT + (path_id % num_paths)


def accumulate_path_phase(prev: float, dt: float, speed: float) -> float:
    """Forward-only phase step — identical to GLSL accumulatePathPhase()."""
    return (prev + max(dt, 0.0) * max(speed, 0.0)) % 1.0


def voronoi_filament_path(
    t: float,
    path_id: int,
    canvas: tuple[float, float] = (800.0, 450.0),
) -> tuple[float, float]:
    """Pixel-space filament sample — identical to GLSL filamentPath()."""
    cx, cy = canvas
    unit = cy * VORONOI_BASE_SCALE
    geom, p, q = voronoi_path_knot(path_id)
    ox, oy, size_scale = voronoi_path_layout(path_id)
    R, rr = voronoi_path_torus(path_id)
    center = (cx * 0.5 + ox * unit, cy * 0.5 + oy * unit)
    if geom == 1:
        return circle_path_2d(
            t, center, VORONOI_CIRCLE_RAD * R * unit * size_scale
        )
    scale = unit * size_scale
    if geom == 2:
        x, y = twisted_ladder_path_2d(t, p, q, R, rr, scale)
    else:
        x, y = torus_knot_path_2d(t, p, q, R, rr, scale)
    return (x + center[0], y + center[1])


def nested_braid_point(
    t: float,
    phase: float = 0.0,
    stretch: float = NESTED_BRAID_STRETCH,
    side: float = 1.0,
) -> tuple[float, float, float]:
    """Open braid curve — identical to GLSL nestedBraidPoint()."""
    sn = math.sin(t + phase)
    cs = math.cos(t + phase)
    return (cs, t * stretch, side * sn * cs)
