// SST T(p,q) swirl-clock  —  [BRIDGE] visualisation only (not a proof)
// Image-tab paste for Shadertoy. iChannel0 = Microphone or Audio.
// T(2,3)=3_1 trefoil default; coprime (p,q) cycle; q->-q = chirality.
// Tube = polyline capsules; twist stripes = core torsion along the loop.
// Audio: bass->core/glow, mid->twist, high->phase speed (topology unchanged).

#define MAX_STEPS  72
#define MAX_DIST   24.0
#define SURF_EPS   0.0015
#define SEGMENTS   64      // raise to 80 on fast GPUs
#define CORE_R     0.085
#define TORUS_R    1.15
#define TORUS_r    0.42
#define SPEED      0.08
#define TWIST      1.5
#define CLOCK_TICKS 24.0
#define PI         3.14159265
#define TAU        6.2831853
#define FREQ_BINS  16.0
#define AUDIO_FALLBACK 1

// --- audio (same as sst_audio.inc.glsl) ---
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
// --- end audio ---

vec3 torusKnot(float p, float q, float phi, float R, float rr)
{
    float cq = cos(q * phi), sq = sin(q * phi);
    float cp = cos(p * phi), sp = sin(p * phi);
    return vec3((R + rr * cq) * cp, (R + rr * cq) * sp, rr * sq);
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

float sdCapsule(vec3 p, vec3 a, vec3 b, float r)
{
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}

vec2 mapTube(vec3 pos, float p, float q, float coreR)
{
    float dMin = 1e5;
    float phiHit = 0.0;
    vec3 a = torusKnot(p, q, 0.0, TORUS_R, TORUS_r);
    for (int i = 1; i <= SEGMENTS; i++)
    {
        float t = float(i) / float(SEGMENTS);
        float phi = t * TAU;
        vec3 b = torusKnot(p, q, phi, TORUS_R, TORUS_r);
        float d = sdCapsule(pos, a, b, coreR);
        if (d < dMin)
        {
            dMin = d;
            float ha = length(pos - a);
            float hb = length(pos - b);
            phiHit = (ha < hb) ? phi - TAU / float(SEGMENTS) : phi;
        }
        a = b;
    }
    return vec2(dMin, phiHit);
}

float clockTicks(vec3 pos, float p, float q, float phi, float twistAmt, float phaseSpeed)
{
    vec3 cen = torusKnot(p, q, phi, TORUS_R, TORUS_r);
    vec3 tang = normalize(
        torusKnot(p, q, phi + 0.002, TORUS_R, TORUS_r) - cen);
    vec3 up = abs(tang.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 n0 = normalize(cross(tang, up));
    vec3 b0 = cross(tang, n0);
    float tw = TWIST * twistAmt * phi - phaseSpeed * iTime * TAU;
    float cs = cos(tw), sn = sin(tw);
    vec3 n = n0 * cs + b0 * sn;
    vec3 bi = -n0 * sn + b0 * cs;
    vec3 d = pos - cen;
    float ang = atan(dot(d, bi), dot(d, n));
    float ticks = abs(fract(ang / TAU * CLOCK_TICKS) - 0.5);
    return smoothstep(0.12, 0.02, ticks);
}

vec3 calcNormal(vec3 pos, float p, float q, float coreR)
{
    vec2 e = vec2(SURF_EPS, 0.0);
    return normalize(vec3(
        mapTube(pos + e.xyy, p, q, coreR).x - mapTube(pos - e.xyy, p, q, coreR).x,
        mapTube(pos + e.yxy, p, q, coreR).x - mapTube(pos - e.yxy, p, q, coreR).x,
        mapTube(pos + e.yyx, p, q, coreR).x - mapTube(pos - e.yyx, p, q, coreR).x
    ));
}

vec2 march(vec3 ro, vec3 rd, float p, float q, float coreR, float glowGain)
{
    float t = 0.0;
    float glow = 0.0;
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec3 pos = ro + rd * t;
        vec2 m = mapTube(pos, p, q, coreR);
        glow += exp(-8.0 * max(m.x, 0.0)) * 0.035 * glowGain;
        if (m.x < SURF_EPS)
            return vec2(t, m.y);
        t += clamp(m.x * 0.85, 0.01, 0.35);
        if (t > MAX_DIST) break;
    }
    return vec2(-glow, 0.0);
}

vec3 phaseColor(float phi, float phaseSpeed)
{
    float h = fract(phi / TAU - phaseSpeed * iTime);
    return mix(vec3(0.05, 0.45, 0.85), vec3(0.85, 0.12, 0.55),
               0.5 + 0.5 * sin(h * TAU));
}

vec3 aetherBg(vec3 rd, vec2 uv)
{
    float sky = 0.04 + 0.06 * (rd.y + 1.0);
    float vign = 1.0 - 0.35 * dot(uv, uv);
    return vec3(0.01, 0.02, 0.05) * sky * vign;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = (2.0 * fragCoord - iResolution.xy) / iResolution.y;

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);
    float coreR = CORE_R * (0.85 + 0.55 * bass);
    float twistAmt = 0.7 + 1.1 * mid;
    float phaseSpeed = SPEED * (0.7 + 1.4 * high);
    float glowGain = 0.8 + 1.2 * bass;

    vec2 pq = knotPQ();
    float p = pq.x, q = pq.y;

    float az = 0.15 * iTime;
    float el = 0.22;
    if (iMouse.z > 0.0)
    {
        az = 3.0 * PI * (iMouse.x / iResolution.x - 0.5);
        el = clamp(PI * (0.5 - iMouse.y / iResolution.y), -1.2, 1.2);
    }
    float ca = cos(az), sa = sin(az);
    float ce = cos(el), se = sin(el);
    vec3 ro = vec3(sa * ce, se, ca * ce) * 4.2;
    vec3 ta = vec3(0.0, 0.0, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.6 * ww);

    vec3 col = aetherBg(rd, uv);
    vec2 hit = march(ro, rd, p, q, coreR, glowGain);

    if (hit.x > 0.0)
    {
        vec3 pos = ro + rd * hit.x;
        vec3 nor = calcNormal(pos, p, q, coreR);
        float phi = hit.y;
        vec3 mate = phaseColor(phi, phaseSpeed);
        float ticks = clockTicks(pos, p, q, phi, twistAmt, phaseSpeed);
        mate = mix(mate, mate * 1.35 + vec3(0.15), ticks);

        float dif = clamp(0.55 + 0.45 * dot(nor, normalize(vec3(0.4, 0.8, 0.3))), 0.0, 1.0);
        float fre = pow(clamp(1.0 + dot(rd, nor), 0.0, 1.0), 2.0);
        col = mate * dif + fre * 0.25 * mate;
        col *= 0.9 + 0.25 * mid;
    }
    else
    {
        float g = -hit.x;
        col += phaseColor(iTime * phaseSpeed * TAU, phaseSpeed) * g * 0.9;
    }

    col = pow(max(col, 0.0), vec3(0.95));
    fragColor = vec4(col, 1.0);
}
