// SST Voronoi filaments — COMMON tab
// [BRIDGE] visualisation. Multi-pass: Buffer A = sites, Buffer B = particles, Image = field.
// Paste this into Shadertoy Common.
//
// IMPORTANT: Do NOT keep `#define res iResolution.xy` (or any macro alias to iResolution).
// That turns `sstRes = iResolution.xy` into an illegal write to a uniform and freezes the pass.
// Each Buffer/Image must set: sstRes = iResolution.xy;
//
// Default kit: 8 concentric Trefoils (R = TREFOIL_R0 * 1..8), paste rr character.
// Even paths = particles, odd = RGB strands. Chirality flip later via q = -q (no KIND_*_M).
// Ladder kinds L41..L112 = lab Lissajous — not IQ figure-8 GLSL.

#define PARTICLE_COUNT  1200
#define NUM_PATHS       8
#define PI              3.14159265
#define TAU             6.2831853
#define PHI_GOLD        1.61803398875

#define STRAND_SAMPLES  64
#define STRAND_WAVE     15.0

// Concentric Trefoil nest: (R_max + rr_max) * BASE_SCALE ≲ 0.45
#define TREFOIL_R0       0.22
#define TREFOIL_r_SCALE  0.30
#define BASE_SCALE       0.22
#define CIRCLE_RAD       0.55

// ============ MOTION UX ============
#define PHASE_JITTER     0.17
#define PATH_SPEED_BASE  0.02
#define PATH_SPEED_MID   0.04
#define ATTRACT_BASE     0.025
#define ATTRACT_BASS     0.04
#define REPEL_BASE       0.25
#define REPEL_HIGH       0.20
#define VMAX_BASE        1.0
#define VMAX_MID         0.8
#define DAMPING          1.003
#define NOISE_AMP        0.002
#define INIT_VEL_SPAN    2.0

// ============ AUDIO UX ============
#define AUDIO_FALLBACK   1
#define FREQ_BINS        16.0
#define AUDIO_BASS_X     0.05
#define AUDIO_MID_X      0.35
#define AUDIO_HIGH_X     0.75
#define AUDIO_WIDE_L     0.15
#define AUDIO_WIDE_R     0.85
#define AUDIO_FB_BASS    0.06
#define AUDIO_FB_MID     0.05
#define AUDIO_FB_HIGH    0.04
#define AUDIO_FB_FLOOR   0.08
#define STRETCH_BASS     0.35
#define STEREO_AMP       0.12
#define HUE_AUDIO        0.05

// ============ IMAGE UX ============
#define GLOW_BASE        18.0
#define GLOW_BASS        40.0
#define GLOW_MAX         8.0
#define EDGE_BASE        12.0
#define EDGE_HIGH        20.0
#define EDGE_MIX_LO      0.85
#define EDGE_MIX_HI      0.20
#define COL_MID          0.12
#define COL_MID_AUDIO    0.10
#define COL_HIGH_POW     0.15
#define COL_HIGH_BASE    0.20
#define COL_HIGH_AUDIO   0.50
#define VIGNETTE         0.35
#define GAMMA            0.92
#define BG_COL           vec3(0.0)
// =========================================

const int MODE_PARTICLES = 0;
const int MODE_STRANDS   = 1;

// Named kinds — IDs only. Geometry lives in kindSpec(). Flip later: q = -q.
const int KIND_CUSTOM  = 0;  // FilamentPath.p/q as T(p,q)
const int KIND_CIRCLE  = 1;
const int KIND_TREFOIL = 2;  // T(2,3)
const int KIND_CINQUE  = 3;  // T(2,5)
const int KIND_T34     = 4;
const int KIND_T35     = 5;
const int KIND_T45     = 6;
const int KIND_T56     = 7;
const int KIND_T69     = 8;
const int KIND_T615    = 9;
const int KIND_T621    = 10;
const int KIND_L41     = 11; // ladder 4_1, halfTwists=2
const int KIND_L52     = 12;
const int KIND_L61     = 13;
const int KIND_L72     = 14;
const int KIND_L81     = 15;
const int KIND_L92     = 16;
const int KIND_L101    = 17;
const int KIND_L112    = 18;

vec2 sstRes;

struct KindSpec {
    int   geom; // 0 torus, 1 circle, 2 ladder
    float p, q;
};

struct ParticleConfig {
    float size;   // particle glow / strand thickness scale
    vec3  color;  // particle mate / strand tint
    float speed;  // phase-speed multiplier (>= 0), both modes
};

struct FilamentPath {
    int   kind;
    float p, q;
    float R, rr;
    vec2  off;
    float scale;
    int   mode;
    ParticleConfig particle;
    float strandWidth;
};

// Only map: named kind → geom / p / q. CUSTOM is handled by the caller.
// Field assigns only — Shadertoy/ANGLE rejects struct constructors and `?:` on structs.
KindSpec kindSpec(int named)
{
    KindSpec ks;
    ks.geom = 0;
    ks.p = 0.0;
    ks.q = 0.0;
    if (named == KIND_CIRCLE)  { ks.geom = 1; ks.p = 0.0; ks.q = 0.0; return ks; }
    if (named == KIND_TREFOIL) { ks.p = 2.0; ks.q = 3.0; return ks; }
    if (named == KIND_CINQUE)  { ks.p = 2.0; ks.q = 5.0; return ks; }
    if (named == KIND_T34)     { ks.p = 3.0; ks.q = 4.0; return ks; }
    if (named == KIND_T35)     { ks.p = 3.0; ks.q = 5.0; return ks; }
    if (named == KIND_T45)     { ks.p = 4.0; ks.q = 5.0; return ks; }
    if (named == KIND_T56)     { ks.p = 5.0; ks.q = 6.0; return ks; }
    if (named == KIND_T69)     { ks.p = 6.0; ks.q = 9.0; return ks; }
    if (named == KIND_T615)    { ks.p = 6.0; ks.q = 15.0; return ks; }
    if (named == KIND_T621)    { ks.p = 6.0; ks.q = 21.0; return ks; }
    if (named == KIND_L41)     { ks.geom = 2; ks.p = 2.0; ks.q = 1.0; return ks; }
    if (named == KIND_L52)     { ks.geom = 2; ks.p = 3.0; ks.q = 1.0; return ks; }
    if (named == KIND_L61)     { ks.geom = 2; ks.p = 4.0; ks.q = 1.0; return ks; }
    if (named == KIND_L72)     { ks.geom = 2; ks.p = 5.0; ks.q = 1.0; return ks; }
    if (named == KIND_L81)     { ks.geom = 2; ks.p = 6.0; ks.q = 1.0; return ks; }
    if (named == KIND_L92)     { ks.geom = 2; ks.p = 7.0; ks.q = 1.0; return ks; }
    if (named == KIND_L101)    { ks.geom = 2; ks.p = 8.0; ks.q = 1.0; return ks; }
    if (named == KIND_L112)    { ks.geom = 2; ks.p = 9.0; ks.q = 1.0; return ks; }
    return ks;
}

// Paste rr (0.42, 0.42, 0.38, 0, 0.40, 0.40, 0.36, 0) × TREFOIL_r_SCALE
// R = TREFOIL_R0 * (1..8). Even = particles, odd = RGB strands.
// Every path (both modes) has its own ParticleConfig size / color / speed.
FilamentPath pathAt(int pathId)
{
    int id = pathId % NUM_PATHS;
    float R = TREFOIL_R0 * float(id + 1);
    float rrRaw = 0.00;
    if (id == 0) rrRaw = 0.42;
    else if (id == 1) rrRaw = 0.42;
    else if (id == 2) rrRaw = 0.38;
    else if (id == 3) rrRaw = 0.00;
    else if (id == 4) rrRaw = 0.40;
    else if (id == 5) rrRaw = 0.40;
    else if (id == 6) rrRaw = 0.36;
    FilamentPath fp;
    fp.kind = KIND_TREFOIL;
    fp.p = 0.0;
    fp.q = 0.0;
    fp.R = R;
    fp.rr = rrRaw * TREFOIL_r_SCALE;
    fp.off = vec2(0.0);
    fp.scale = 1.0;
    fp.mode = MODE_PARTICLES;
    if ((id % 2) != 0) fp.mode = MODE_STRANDS;
    fp.particle.size = 0.75 + 0.08 * float(id);
    fp.particle.speed = 0.70 + 0.12 * float(id);
    fp.particle.color = vec3(0.95, 0.55, 0.20);
    if (id == 0) fp.particle.color = vec3(0.05, 0.45, 0.85);
    if (id == 1) fp.particle.color = vec3(0.85, 0.12, 0.55);
    if (id == 2) fp.particle.color = vec3(0.20, 0.75, 0.55);
    if (id == 3) fp.particle.color = vec3(0.95, 0.55, 0.20);
    if (id == 4) fp.particle.color = vec3(0.45, 0.35, 0.95);
    if (id == 5) fp.particle.color = vec3(0.20, 0.85, 0.90);
    if (id == 6) fp.particle.color = vec3(0.95, 0.25, 0.35);
    fp.strandWidth = 0.012;
    return fp;
}

int pathDrawMode(int pathId)
{
    return pathAt(pathId).mode;
}

int textToIndex(vec2 p)
{
    return int((p.x - 0.5) + (p.y - 0.5) * sstRes.x);
}

vec2 indexToText(int n)
{
    return vec2(float(n % int(sstRes.x)), float(n / int(sstRes.x))) + 0.5;
}

float loopDist(vec2 a, vec2 b)
{
    vec2 d = a - b;
    d -= round(d / sstRes) * sstRes;
    return length(d);
}

vec2 loopRel(vec2 a, vec2 b)
{
    vec2 d = a - b;
    return d - round(d / sstRes) * sstRes;
}

vec2 safeNormalize(vec2 p)
{
    float L = length(p);
    return L > 1e-6 ? p / L : vec2(0.0);
}

vec2 safeInvert(vec2 p)
{
    float L = length(p);
    return L > 1e-6 ? p / (L * L) : vec2(0.0);
}

float hash11(float x)
{
    return fract(sin(x * 127.1) * 43758.5453);
}

vec2 torusKnotPath2D(float t, float p, float q, float R, float rr, float scale)
{
    float phi = t * TAU;
    float cq = cos(q * phi);
    float cp = cos(p * phi), sp = sin(p * phi);
    return vec2((R + rr * cq) * cp, (R + rr * cq) * sp) * scale;
}

vec2 circlePath2D(float t, vec2 center, float rad)
{
    float a = t * TAU;
    return center + rad * vec2(cos(a), sin(a));
}

// Original SST Lissajous ladder (lab figure8 / twist52 style) — not IQ figure-8 GLSL.
vec2 twistedLadderPath2D(float t, float halfTwists, float side, float R, float rr, float scale)
{
    float a = t * TAU;
    float k = halfTwists;
    float w = floor(k * 0.5) + 1.0;
    float rad = R + rr * cos(k * a);
    vec2 xy = rad * vec2(cos(w * a), sin(w * a));
    xy += side * rr * 0.35 * vec2(0.0, sin(2.0 * k * a));
    return xy * scale;
}

vec2 filamentPath(float t, int pathId)
{
    float unit = sstRes.y * BASE_SCALE;
    FilamentPath fp = pathAt(pathId);
    KindSpec ks;
    if (fp.kind == KIND_CUSTOM)
    {
        ks.geom = 0;
        ks.p = fp.p;
        ks.q = fp.q;
    }
    else
        ks = kindSpec(fp.kind);

    vec2 center = sstRes * 0.5 + fp.off * unit;
    float sizeScale = fp.scale;

    if (ks.geom == 1)
        return circlePath2D(t, center, CIRCLE_RAD * fp.R * unit * sizeScale);

    float scale = unit * sizeScale;
    if (ks.geom == 2)
        return twistedLadderPath2D(t, ks.p, ks.q, fp.R, fp.rr, scale) + center;

    return torusKnotPath2D(t, ks.p, ks.q, fp.R, fp.rr, scale) + center;
}

int pathOfParticle(int id)
{
    return id % NUM_PATHS;
}

float phaseOfParticle(int id)
{
    return float(id / NUM_PATHS) / float(max(PARTICLE_COUNT / NUM_PATHS, 1));
}

vec4 readParticle(sampler2D ch, int id)
{
    return texture(ch, indexToText(id) / sstRes);
}

float pathFreqX(int pathId)
{
    float n = float(max(NUM_PATHS - 1, 1));
    return float(pathId % NUM_PATHS) / n;
}

float pathStereoWidth(int pathId)
{
    return pathFreqX(pathId);
}

// Buffer B stores integrated path phase in texels after the particle block.
int pathPhaseIndex(int pathId)
{
    return PARTICLE_COUNT + (pathId % NUM_PATHS);
}
