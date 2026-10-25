// SST log-spiral swirl-clock  —  [BRIDGE] visualisation only (not a proof)
// 2D companion to sst_torus_knot_swirl.glsl. iChannel0 = Microphone or Audio.
// Spiral arms h=(p,q); same catalogue as the tube. Original code.
// Audio: bass->zoom/ticks, mid->spin, high->arm contrast.

#define SPEED       0.08
#define ARM_TICKS   18.0
#define RING_REF    0.55
#define PI          3.14159265
#define TAU         6.2831853
#define FREQ_BINS   16.0
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

vec3 phaseColor(float h)
{
    h = fract(h);
    return mix(vec3(0.05, 0.45, 0.85), vec3(0.85, 0.12, 0.55),
               0.5 + 0.5 * sin(h * TAU));
}

vec2 logSpiralPlane(vec2 xy, float p, float q)
{
    float rho = length(xy);
    float theta = atan(xy.y, xy.x);
    float u = log(max(rho, 1e-4)) - 0.5 * (p * theta);
    float v = log(max(rho, 1e-4)) - 0.5 * (q * theta);
    return vec2(u, v);
}

float armTicks(vec2 uv, float arms, float phase)
{
    float a = uv.x * arms - phase * arms;
    float slot = abs(fract(a) - 0.5);
    float pulse = smoothstep(0.18, 0.04, slot);
    float ridge = exp(-2.5 * abs(uv.y - uv.x));
    return pulse * ridge;
}

float softGrid(vec2 uv)
{
    vec2 f = abs(fract(uv) - 0.5);
    vec2 w = fwidth(uv);
    vec2 line = 1.0 - smoothstep(vec2(0.0), 1.5 * w, f);
    return 0.5 * (line.x + line.y);
}

float referenceRing(vec2 xy)
{
    float r = length(xy);
    float d = abs(r - RING_REF);
    return smoothstep(0.04, 0.0, d);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 R = iResolution.xy;
    vec2 uv = (2.0 * fragCoord - R) / R.y;

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);

    vec2 pq = knotPQ();
    float p = pq.x, q = pq.y;

    float ang = SPEED * iTime * TAU * (0.25 + 0.55 * mid);
    if (iMouse.z > 0.0)
        ang = (iMouse.x / R.x - 0.5) * TAU;

    float ca = cos(ang), sa = sin(ang);
    vec2 xy = mat2(ca, -sa, sa, ca) * uv;

    float zoom = 1.05 + 0.35 * bass + 0.1 * cos(SPEED * iTime * TAU);
    xy *= zoom;

    vec2 sp = logSpiralPlane(xy, p, q);

    float phase = SPEED * iTime * (0.7 + 1.2 * high);
    float tickGain = 0.7 + 1.4 * bass;
    float ticksP = armTicks(sp, abs(p), phase) * tickGain;
    float ticksQ = armTicks(vec2(sp.y, sp.x), abs(q), phase * 1.07) * tickGain;
    float contrast = 0.75 + 0.9 * high;
    float grid = softGrid(sp * 1.25) * 0.12 * contrast;
    float ring = referenceRing(xy) * (0.25 + 0.25 * mid);

    float quot = abs(sp.x) + abs(sp.y);
    float h = fract(atan(sp.y, sp.x) / TAU - phase);

    vec3 col = vec3(0.01, 0.02, 0.05);
    col += phaseColor(h) * (0.2 + 0.65 * (ticksP + ticksQ));
    col += phaseColor(h + 0.15) * grid;
    col += vec3(0.15, 0.35, 0.45) * ring;
    col *= 0.85 + 0.2 * cos(quot + phase * TAU) * contrast;

    col *= 1.0 - 0.35 * dot(uv, uv);
    col = pow(max(col, 0.0), vec3(0.92));

    fragColor = vec4(col, 1.0);
}
