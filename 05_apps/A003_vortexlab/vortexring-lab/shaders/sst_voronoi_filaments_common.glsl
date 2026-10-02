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
//
// Live UI: collapsed header top-left. Click to expand (Motion / Look / Path tabs).
// Slider state is stored in Buffer B texels after particles + path phases.
// Buffer A stays a Voronoi site field. Image draws the overlay.

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

// === SST UI PRESET (paste EXP export here; used on Buffer B init / Reset) ===
// Shadertoy cannot write the system clipboard — open MENU > EXP, read values, paste below.
#define PRESET_SL_SCALE     0.22
#define PRESET_SL_SPEED     1.00
#define PRESET_SL_ATTRACT   0.025
#define PRESET_SL_REPEL     0.25
#define PRESET_SL_STRETCH   0.35
#define PRESET_SL_STEREO    0.12
#define PRESET_SL_GLOW      18.0
#define PRESET_SL_VIGNETTE  0.35
#define PRESET_SL_GAMMA     0.92
#define PRESET_SL_STRAND    0.012
#define PRESET_SL_HUEAUD    0.05
#define PRESET_SL_AUDIOFB   1.0
#define PRESET_SL_DISCS     0.0
// path fields: size, speed, hue(0..1), mode(0=particles,1=strands)
#define PRESET_P0_SIZE 0.75
#define PRESET_P0_SPEED 0.70
#define PRESET_P0_HUE   0.583
#define PRESET_P0_MODE  0.0
#define PRESET_P1_SIZE 0.83
#define PRESET_P1_SPEED 0.82
#define PRESET_P1_HUE   0.902
#define PRESET_P1_MODE  1.0
#define PRESET_P2_SIZE 0.91
#define PRESET_P2_SPEED 0.94
#define PRESET_P2_HUE   0.439
#define PRESET_P2_MODE  0.0
#define PRESET_P3_SIZE 0.99
#define PRESET_P3_SPEED 1.06
#define PRESET_P3_HUE   0.078
#define PRESET_P3_MODE  1.0
#define PRESET_P4_SIZE 1.07
#define PRESET_P4_SPEED 1.18
#define PRESET_P4_HUE   0.694
#define PRESET_P4_MODE  0.0
#define PRESET_P5_SIZE 1.15
#define PRESET_P5_SPEED 1.30
#define PRESET_P5_HUE   0.512
#define PRESET_P5_MODE  1.0
#define PRESET_P6_SIZE 1.23
#define PRESET_P6_SPEED 1.42
#define PRESET_P6_HUE   0.976
#define PRESET_P6_MODE  0.0
#define PRESET_P7_SIZE 1.31
#define PRESET_P7_SPEED 1.54
#define PRESET_P7_HUE   0.078
#define PRESET_P7_MODE  1.0
// === end SST UI PRESET ===

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

// Euclidean only — no toroidal wrap (avoids mirrored ghosts at canvas edges).
float loopDist(vec2 a, vec2 b)
{
    return length(a - b);
}

vec2 loopRel(vec2 a, vec2 b)
{
    return a - b;
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

float uiLiveScale(sampler2D ch);
FilamentPath pathAtUi(sampler2D ui, int pathId);

vec2 filamentPath(float t, int pathId, sampler2D ui)
{
    float unit = sstRes.y * uiLiveScale(ui);
    FilamentPath fp = pathAtUi(ui, pathId);
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

// ============ LIVE UI (Buffer B texels) ============
// HEAD: x=open, y=dragId, z=prevMouseDown, w=selectedPath
// META: x=tab (0 motion, 1 look, 2 path)
#define UI_SLOT_HEAD     0
#define UI_SLOT_META     1
#define UI_SLOT_SL0      2
#define UI_N_SL          13
#define UI_SLOT_PATH     20
#define UI_PATH_FIELDS   4
#define UI_SLOT_COUNT    (UI_SLOT_PATH + NUM_PATHS * UI_PATH_FIELDS)

#define SL_SCALE     0
#define SL_SPEED     1
#define SL_ATTRACT   2
#define SL_REPEL     3
#define SL_STRETCH   4
#define SL_STEREO    5
#define SL_GLOW      6
#define SL_VIGNETTE  7
#define SL_GAMMA     8
#define SL_STRAND    9
#define SL_HUEAUD    10
#define SL_AUDIOFB   11
#define SL_DISCS     12

#define PF_SIZE   0
#define PF_SPEED  1
#define PF_HUE    2
#define PF_MODE   3

#define UI_TAB_MOTION 0
#define UI_TAB_LOOK   1
#define UI_TAB_PATH   2

#define HIT_NONE      0
#define HIT_HEADER    1
#define HIT_TAB0      2
#define HIT_TAB1      3
#define HIT_TAB2      4
#define HIT_RESET     5
#define HIT_PATH_PRV  6
#define HIT_PATH_NXT  7
#define HIT_MODE_P    8
#define HIT_MODE_S    9
#define HIT_EXPORT    10
#define HIT_EXP_PRV   11
#define HIT_EXP_NXT   12
#define HIT_SL0       100
#define HIT_PF0       200

#define UI_PANEL_W  310.0
#define UI_PANEL_W_EXP 420.0
#define UI_HDR_H    34.0
#define UI_TAB_H    26.0
#define UI_ROW_H    24.0
#define UI_MARGIN   10.0
#define UI_ROWS     6.0
#define UI_EXP_ROWS 12.0
#define UI_EXP_PAGES 3
#define UI_TRACK_X  90.0
#define UI_TRACK_W  150.0
#define UI_TRACK_Y  7.0
#define UI_TRACK_H  10.0
#define UI_DIGIT_X  248.0
#define UI_FONT_LG  1.45
#define UI_FONT_MD  1.25
#define UI_FONT_SM  1.05

int uiTexelIndex(int slot)
{
    return PARTICLE_COUNT + NUM_PATHS + slot;
}

vec4 uiLoad(sampler2D ch, int slot)
{
    return readParticle(ch, uiTexelIndex(slot));
}

float uiSliderRaw(sampler2D ch, int sl)
{
    return uiLoad(ch, UI_SLOT_SL0 + sl).x;
}

float uiPathRaw(sampler2D ch, int pathId, int field)
{
    return uiLoad(ch, UI_SLOT_PATH + (pathId % NUM_PATHS) * UI_PATH_FIELDS + field).x;
}

float uiSliderMin(int sl)
{
    if (sl == SL_SCALE) return 0.08;
    if (sl == SL_SPEED) return 0.0;
    if (sl == SL_ATTRACT) return 0.0;
    if (sl == SL_REPEL) return 0.0;
    if (sl == SL_STRETCH) return 0.0;
    if (sl == SL_STEREO) return 0.0;
    if (sl == SL_GLOW) return 4.0;
    if (sl == SL_VIGNETTE) return 0.0;
    if (sl == SL_GAMMA) return 0.55;
    if (sl == SL_STRAND) return 0.002;
    if (sl == SL_HUEAUD) return 0.0;
    if (sl == SL_DISCS) return 0.0;
    return 0.0;
}

float uiSliderMax(int sl)
{
    if (sl == SL_SCALE) return 0.42;
    if (sl == SL_SPEED) return 2.50;
    if (sl == SL_ATTRACT) return 0.10;
    if (sl == SL_REPEL) return 0.80;
    if (sl == SL_STRETCH) return 1.00;
    if (sl == SL_STEREO) return 0.40;
    if (sl == SL_GLOW) return 48.0;
    if (sl == SL_VIGNETTE) return 0.85;
    if (sl == SL_GAMMA) return 1.40;
    if (sl == SL_STRAND) return 0.040;
    if (sl == SL_HUEAUD) return 0.25;
    if (sl == SL_DISCS) return 1.0;
    return 1.0;
}

float uiSliderDefault(int sl)
{
    if (sl == SL_SCALE) return PRESET_SL_SCALE;
    if (sl == SL_SPEED) return PRESET_SL_SPEED;
    if (sl == SL_ATTRACT) return PRESET_SL_ATTRACT;
    if (sl == SL_REPEL) return PRESET_SL_REPEL;
    if (sl == SL_STRETCH) return PRESET_SL_STRETCH;
    if (sl == SL_STEREO) return PRESET_SL_STEREO;
    if (sl == SL_GLOW) return PRESET_SL_GLOW;
    if (sl == SL_VIGNETTE) return PRESET_SL_VIGNETTE;
    if (sl == SL_GAMMA) return PRESET_SL_GAMMA;
    if (sl == SL_STRAND) return PRESET_SL_STRAND;
    if (sl == SL_HUEAUD) return PRESET_SL_HUEAUD;
    if (sl == SL_AUDIOFB) return PRESET_SL_AUDIOFB;
    if (sl == SL_DISCS) return PRESET_SL_DISCS;
    return 0.0;
}

float uiPathFieldMin(int field)
{
    if (field == PF_SIZE) return 0.20;
    if (field == PF_SPEED) return 0.0;
    return 0.0;
}

float uiPathFieldMax(int field)
{
    if (field == PF_SIZE) return 2.00;
    if (field == PF_SPEED) return 2.50;
    return 1.0;
}

float rgbSat(vec3 c)
{
    float M = max(max(c.r, c.g), c.b);
    float m = min(min(c.r, c.g), c.b);
    return M < 1e-5 ? 0.0 : (M - m) / M;
}

float rgbVal(vec3 c)
{
    return max(max(c.r, c.g), c.b);
}

float rgbHue(vec3 c)
{
    float M = max(max(c.r, c.g), c.b);
    float m = min(min(c.r, c.g), c.b);
    float d = M - m;
    if (d < 1e-5)
        return 0.0;
    float h = 0.0;
    if (c.r >= c.g && c.r >= c.b)
        h = mod((c.g - c.b) / d, 6.0);
    else if (c.g >= c.b)
        h = (c.b - c.r) / d + 2.0;
    else
        h = (c.r - c.g) / d + 4.0;
    return fract(h / 6.0);
}

vec3 hsvRgb(float h, float s, float v)
{
    float H = fract(h) * 6.0;
    float i = floor(H);
    float f = H - i;
    float p = v * (1.0 - s);
    float q = v * (1.0 - s * f);
    float t = v * (1.0 - s * (1.0 - f));
    vec3 o = vec3(v, t, p);
    if (i < 0.5) o = vec3(v, t, p);
    else if (i < 1.5) o = vec3(q, v, p);
    else if (i < 2.5) o = vec3(p, v, t);
    else if (i < 3.5) o = vec3(p, q, v);
    else if (i < 4.5) o = vec3(t, p, v);
    else o = vec3(v, p, q);
    return clamp(o, 0.0, 1.0);
}

float uiPathFieldDefault(int pathId, int field)
{
    int id = pathId % NUM_PATHS;
    if (field == PF_SIZE)
    {
        if (id == 0) return PRESET_P0_SIZE;
        if (id == 1) return PRESET_P1_SIZE;
        if (id == 2) return PRESET_P2_SIZE;
        if (id == 3) return PRESET_P3_SIZE;
        if (id == 4) return PRESET_P4_SIZE;
        if (id == 5) return PRESET_P5_SIZE;
        if (id == 6) return PRESET_P6_SIZE;
        return PRESET_P7_SIZE;
    }
    if (field == PF_SPEED)
    {
        if (id == 0) return PRESET_P0_SPEED;
        if (id == 1) return PRESET_P1_SPEED;
        if (id == 2) return PRESET_P2_SPEED;
        if (id == 3) return PRESET_P3_SPEED;
        if (id == 4) return PRESET_P4_SPEED;
        if (id == 5) return PRESET_P5_SPEED;
        if (id == 6) return PRESET_P6_SPEED;
        return PRESET_P7_SPEED;
    }
    if (field == PF_HUE)
    {
        if (id == 0) return PRESET_P0_HUE;
        if (id == 1) return PRESET_P1_HUE;
        if (id == 2) return PRESET_P2_HUE;
        if (id == 3) return PRESET_P3_HUE;
        if (id == 4) return PRESET_P4_HUE;
        if (id == 5) return PRESET_P5_HUE;
        if (id == 6) return PRESET_P6_HUE;
        return PRESET_P7_HUE;
    }
    if (field == PF_MODE)
    {
        if (id == 0) return PRESET_P0_MODE;
        if (id == 1) return PRESET_P1_MODE;
        if (id == 2) return PRESET_P2_MODE;
        if (id == 3) return PRESET_P3_MODE;
        if (id == 4) return PRESET_P4_MODE;
        if (id == 5) return PRESET_P5_MODE;
        if (id == 6) return PRESET_P6_MODE;
        return PRESET_P7_MODE;
    }
    return 0.0;
}

bool uiReady(sampler2D ch)
{
    return uiSliderRaw(ch, SL_SCALE) > 0.01;
}

float uiLiveScale(sampler2D ch)
{
    float s = uiSliderRaw(ch, SL_SCALE);
    return s > 0.01 ? s : BASE_SCALE;
}

float uiLive(sampler2D ch, int sl)
{
    if (!uiReady(ch))
        return uiSliderDefault(sl);
    return uiSliderRaw(ch, sl);
}

FilamentPath pathAtUi(sampler2D ui, int pathId)
{
    FilamentPath fp = pathAt(pathId);
    if (!uiReady(ui))
        return fp;
    fp.particle.size = uiPathRaw(ui, pathId, PF_SIZE);
    fp.particle.speed = max(uiPathRaw(ui, pathId, PF_SPEED), 0.0) * max(uiLive(ui, SL_SPEED), 0.0);
    float h = uiPathRaw(ui, pathId, PF_HUE);
    fp.particle.color = hsvRgb(h, max(rgbSat(fp.particle.color), 0.55), max(rgbVal(fp.particle.color), 0.75));
    fp.strandWidth = uiLive(ui, SL_STRAND);
    fp.mode = MODE_PARTICLES;
    if (uiPathRaw(ui, pathId, PF_MODE) > 0.5)
        fp.mode = MODE_STRANDS;
    return fp;
}

float uiZoom()
{
    float need = UI_HDR_H + UI_TAB_H + UI_EXP_ROWS * UI_ROW_H + 8.0;
    return min(1.0, max(sstRes.y - 16.0, 40.0) / need);
}

vec2 uiToScreen(vec2 local)
{
    float z = uiZoom();
    return vec2(UI_MARGIN + local.x * z, sstRes.y - UI_MARGIN - local.y * z);
}

vec4 uiBox(vec2 loc, vec2 sz)
{
    vec2 a = uiToScreen(loc);
    vec2 b = uiToScreen(loc + sz);
    return vec4(min(a.x, b.x), min(a.y, b.y), max(a.x, b.x), max(a.y, b.y));
}

bool uiInBox(vec2 px, vec2 loc, vec2 sz)
{
    vec4 b = uiBox(loc, sz);
    return px.x >= b.x && px.x < b.z && px.y >= b.y && px.y < b.w;
}

float uiBoxT(vec2 px, vec2 loc, vec2 sz)
{
    vec4 b = uiBox(loc, sz);
    return clamp((px.x - b.x) / max(b.z - b.x, 1.0), 0.0, 1.0);
}

float uiPanelH(int open, int expOn)
{
    if (open < 1)
        return UI_HDR_H;
    if (expOn > 0)
        return UI_HDR_H + UI_TAB_H + UI_EXP_ROWS * UI_ROW_H + 6.0;
    return UI_HDR_H + UI_TAB_H + UI_ROWS * UI_ROW_H + 6.0;
}

float uiPanelW(int expOn)
{
    return expOn > 0 ? UI_PANEL_W_EXP : UI_PANEL_W;
}

bool uiInPanel(vec2 px, int open, int expOn)
{
    return uiInBox(px, vec2(0.0), vec2(uiPanelW(expOn), uiPanelH(open, expOn)));
}

int uiMotionSlider(int row)
{
    if (row == 0) return SL_SCALE;
    if (row == 1) return SL_SPEED;
    if (row == 2) return SL_ATTRACT;
    if (row == 3) return SL_REPEL;
    if (row == 4) return SL_STRETCH;
    return SL_STEREO;
}

int uiLookSlider(int row)
{
    if (row == 0) return SL_GLOW;
    if (row == 1) return SL_DISCS;
    if (row == 2) return SL_GAMMA;
    if (row == 3) return SL_STRAND;
    if (row == 4) return SL_HUEAUD;
    return SL_AUDIOFB;
}

int uiHit(vec2 px, int open, int tab, int sel, int expOn)
{
    if (sel < 0 || sel >= NUM_PATHS)
        return HIT_NONE;
    float pw = uiPanelW(expOn);
    // Header: left = collapse, right EXP button
    if (uiInBox(px, vec2(pw - 78.0, 4.0), vec2(50.0, 26.0)))
        return HIT_EXPORT;
    if (uiInBox(px, vec2(0.0, 0.0), vec2(pw - 80.0, UI_HDR_H)))
        return HIT_HEADER;
    if (uiInBox(px, vec2(0.0, 0.0), vec2(pw, UI_HDR_H)))
        return HIT_HEADER;
    if (open < 1)
        return HIT_NONE;

    if (expOn > 0)
    {
        float y0 = UI_HDR_H + UI_TAB_H;
        if (uiInBox(px, vec2(8.0, y0 + 3.0), vec2(28.0, 18.0)))
            return HIT_EXP_PRV;
        if (uiInBox(px, vec2(pw - 36.0, y0 + 3.0), vec2(28.0, 18.0)))
            return HIT_EXP_NXT;
        return HIT_NONE;
    }

    float tw = UI_PANEL_W / 3.0;
    if (uiInBox(px, vec2(0.0, UI_HDR_H), vec2(tw, UI_TAB_H)))
        return HIT_TAB0;
    if (uiInBox(px, vec2(tw, UI_HDR_H), vec2(tw, UI_TAB_H)))
        return HIT_TAB1;
    if (uiInBox(px, vec2(2.0 * tw, UI_HDR_H), vec2(tw, UI_TAB_H)))
        return HIT_TAB2;

    float y0 = UI_HDR_H + UI_TAB_H;
    for (int row = 0; row < 6; row++)
    {
        vec2 loc = vec2(UI_TRACK_X, y0 + float(row) * UI_ROW_H + UI_TRACK_Y);
        vec2 sz = vec2(UI_TRACK_W, UI_TRACK_H);
        if (tab == UI_TAB_MOTION)
        {
            if (uiInBox(px, loc, sz))
                return HIT_SL0 + uiMotionSlider(row);
        }
        else if (tab == UI_TAB_LOOK)
        {
            if (row == 5)
            {
                if (uiInBox(px, vec2(UI_TRACK_X, y0 + float(row) * UI_ROW_H + 3.0), vec2(96.0, 18.0)))
                    return HIT_SL0 + SL_AUDIOFB;
            }
            else if (uiInBox(px, loc, sz))
                return HIT_SL0 + uiLookSlider(row);
        }
        else
        {
            if (row == 0)
            {
                if (uiInBox(px, vec2(UI_TRACK_X, y0 + 3.0), vec2(28.0, 18.0)))
                    return HIT_PATH_PRV;
                if (uiInBox(px, vec2(210.0, y0 + 3.0), vec2(28.0, 18.0)))
                    return HIT_PATH_NXT;
            }
            else if (row == 1)
            {
                if (uiInBox(px, vec2(UI_TRACK_X, y0 + UI_ROW_H + 3.0), vec2(62.0, 18.0)))
                    return HIT_MODE_P;
                if (uiInBox(px, vec2(158.0, y0 + UI_ROW_H + 3.0), vec2(72.0, 18.0)))
                    return HIT_MODE_S;
            }
            else if (row == 5)
            {
                if (uiInBox(px, vec2(UI_TRACK_X, y0 + 5.0 * UI_ROW_H + 3.0), vec2(96.0, 18.0)))
                    return HIT_RESET;
            }
            else if (uiInBox(px, loc, sz))
                return HIT_PF0 + (row - 2);
        }
    }
    return HIT_NONE;
}

float uiMixSlider(int sl, float t)
{
    return mix(uiSliderMin(sl), uiSliderMax(sl), clamp(t, 0.0, 1.0));
}

float uiMixPathField(int field, float t)
{
    return mix(uiPathFieldMin(field), uiPathFieldMax(field), clamp(t, 0.0, 1.0));
}
