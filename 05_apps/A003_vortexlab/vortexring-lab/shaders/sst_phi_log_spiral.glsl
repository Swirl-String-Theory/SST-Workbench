// SST phi log-spiral  —  [BRIDGE] visualisation only (not a proof)
// Image-tab. iChannel0 = Microphone or Audio.
// Log-polar + golden-ratio (φ) fractal layers. Companion to sst_log_spiral_swirl
// (that one = (p,q) arms; this = φ self-similar kaleidoscope). Original rewrite.

#define PHI        1.61803398875  // (1+sqrt(5))/2 — match sst_knot_catalog.PHI
#define LAYERS     4
#define SPEED      0.08
#define PI         3.14159265
#define TAU        6.2831853
#define FREQ_BINS  16.0
#define AUDIO_FALLBACK 1

float sstAudio(float x)
{
    float u = clamp(x, 0.0, 1.0);
    return max(texture(iChannel0, vec2(u, 0.25)).x, 0.0);
}
float sstAudioSmooth(float x)
{
    float u = clamp(x, 0.0, 1.0);
    float i0 = floor(u * FREQ_BINS) / FREQ_BINS;
    float i1 = min(i0 + 1.0 / FREQ_BINS, 1.0);
    float f = fract(u * FREQ_BINS);
    return mix(sstAudio(i0), sstAudio(i1), smoothstep(0.0, 1.0, f));
}
float sstBass()  { return sstAudioSmooth(0.05); }
float sstMid()   { return sstAudioSmooth(0.35); }
float sstHigh()  { return sstAudioSmooth(0.75); }
float sstBand(float live, float fbAmp)
{
#if AUDIO_FALLBACK
    float fb = 0.08 + fbAmp * (0.5 + 0.5 * sin(iTime * (1.2 + fbAmp)));
    return max(live, fb);
#else
    return live;
#endif
}

vec2 knotPQ()
{
    float s = mod(iTime / 2.0, 12.0);
    if (s <  1.0) return vec2(2.0,  3.0);
    if (s <  2.0) return vec2(2.0,  5.0);
    if (s <  3.0) return vec2(3.0,  4.0);
    if (s <  4.0) return vec2(3.0,  5.0);
    if (s <  5.0) return vec2(4.0,  5.0);
    if (s <  6.0) return vec2(5.0,  6.0);
    if (s <  7.0) return vec2(2.0, -3.0);
    if (s <  8.0) return vec2(2.0, -5.0);
    if (s <  9.0) return vec2(3.0, -4.0);
    if (s < 10.0) return vec2(3.0, -5.0);
    if (s < 11.0) return vec2(4.0, -5.0);
    return vec2(5.0, -6.0);
}

// Same as sst_knot_catalog.phi_log_scale
float phiLogScale(float p)
{
    return 2.5 + 0.2 * abs(p);
}

mat2 rot2(float a)
{
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

vec3 phaseColor(float h)
{
    h = fract(h);
    return mix(vec3(0.05, 0.45, 0.85), vec3(0.85, 0.12, 0.55),
               0.5 + 0.5 * sin(h * TAU));
}

// One φ-log layer; returns iso-curve strength in [0,1]
float phiLayer(vec2 uv, float layer, float time, float scale, float chirality, float thick)
{
    float n = layer + 1.0;
    float T = time + (TAU / n);
    vec2 off = vec2(cos(T), sin(T));

    vec2 U = uv;
    U += off;
    U *= rot2(chirality * (time + layer * PI));
    U *= scale;
    U -= off;

    float rho = max(length(U), 1e-6);
    float ang = atan(U.y, U.x) / TAU;
    vec2 I = vec2(0.0, log2(rho));
    I.x = ceil(I.y) - ang;
    I.x *= PHI;
    I = fract(I);

    float p = pow(max(I.y, 1e-4), max(I.x, 1e-4));
    float edge = smoothstep(p - thick, p, I.y) - smoothstep(p, p + thick, I.y);
    float field = (I.x + I.y + edge) / 3.0;
    return clamp(field, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 R = iResolution.xy;
    vec2 uv = (2.0 * fragCoord - R) / R.y;

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);

    vec2 pq = knotPQ();
    float scale = phiLogScale(pq.x);
    float chirality = (pq.y < 0.0) ? -1.0 : 1.0;

    float rotSpeed = SPEED * TAU * (0.6 + 1.2 * mid);
    float time = iTime * rotSpeed / (SPEED * TAU); // mid scales effective time
    if (iMouse.z > 0.0)
        time += (iMouse.x / R.x - 0.5) * TAU;

    float thick = 0.015 + 0.025 * bass;
    float contrast = 0.7 + 0.9 * high;
    float bright = 0.75 + 0.55 * bass;

    vec3 col = vec3(0.01, 0.02, 0.05);
    for (int i = 0; i < LAYERS; i++)
    {
        float fi = float(i);
        float v = phiLayer(uv, fi, time, scale, chirality, thick);
        v = pow(v, mix(1.2, 0.75, contrast));
        vec3 layerCol = phaseColor(fi * 0.17 + time * SPEED + v * 0.3);
        // Weight layers: cyan-heavy, magenta-heavy, mix, soft white lift
        float w0 = (i == 0) ? 1.0 : 0.35;
        float w1 = (i == 1) ? 1.0 : 0.35;
        float w2 = (i >= 2) ? 0.85 : 0.25;
        col += layerCol * v * bright * (w0 * 0.45 + w1 * 0.35 + w2 * 0.25);
    }

    col *= 1.0 - 0.3 * dot(uv, uv);
    col = pow(max(col, 0.0), vec3(0.92));
    fragColor = vec4(col, 1.0);
}
