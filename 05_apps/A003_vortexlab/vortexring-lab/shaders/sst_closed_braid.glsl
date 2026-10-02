// SST closed braid 3₁  —  [BRIDGE] visualisation only (not a proof)
// Image-tab paste. iChannel0 = Microphone or Audio.
// Three helical strands on a closed ring. Chirality side=±1 (~2s).
// Audio: bass->strand radius, mid->spin/phase, high->emissive pulse.

#define MAX_STEPS  80
#define MAX_DIST   20.0
#define SURF_EPS   0.0012
#define SEGMENTS   72
#define RING_R     1.35
#define BRAID_R    0.28
#define STRAND_R   0.09
#define BRAID_K    2.0
#define N_STRANDS  3
#define SPEED      0.08
#define TWIST      1.5
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

vec3 braidStrandPoint(float t, float k, float phase, float side)
{
    float ang = t;
    vec3 c = vec3(RING_R * cos(ang), 0.0, RING_R * sin(ang));
    vec3 N = vec3(cos(ang), 0.0, sin(ang));
    vec3 B = vec3(0.0, 1.0, 0.0);
    float a = side * (k * t + phase);
    return c + N * (BRAID_R * cos(a)) + B * (BRAID_R * sin(a));
}

float chiralitySide()
{
    return (mod(iTime, 4.0) < 2.0) ? 1.0 : -1.0;
}

float sdCapsule(vec3 p, vec3 a, vec3 b, float r)
{
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}

vec3 mapBraid(vec3 pos, float side, float strandR)
{
    float dMin = 1e5;
    float phiHit = 0.0;
    float strandHit = 0.0;

    for (int s = 0; s < N_STRANDS; s++)
    {
        float phase = TAU * float(s) / float(N_STRANDS);
        vec3 a = braidStrandPoint(0.0, BRAID_K, phase, side);
        for (int i = 1; i <= SEGMENTS; i++)
        {
            float t = TAU * float(i) / float(SEGMENTS);
            vec3 b = braidStrandPoint(t, BRAID_K, phase, side);
            float d = sdCapsule(pos, a, b, strandR);
            if (d < dMin)
            {
                dMin = d;
                float ha = length(pos - a);
                float hb = length(pos - b);
                phiHit = (ha < hb) ? t - TAU / float(SEGMENTS) : t;
                strandHit = float(s);
            }
            a = b;
        }
    }
    return vec3(dMin, phiHit, strandHit);
}

float twistStripe(vec3 pos, float phi, float phase, float side, float phaseSpeed)
{
    vec3 cen = braidStrandPoint(phi, BRAID_K, phase, side);
    vec3 tang = normalize(
        braidStrandPoint(phi + 0.01, BRAID_K, phase, side) - cen);
    vec3 up = abs(tang.y) < 0.9 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
    vec3 n0 = normalize(cross(tang, up));
    vec3 b0 = cross(tang, n0);
    float tw = TWIST * phi * side - phaseSpeed * iTime * TAU;
    float cs = cos(tw), sn = sin(tw);
    vec3 n = n0 * cs + b0 * sn;
    vec3 bi = -n0 * sn + b0 * cs;
    vec3 d = pos - cen;
    float ang = atan(dot(d, bi), dot(d, n));
    float ticks = abs(fract(ang / TAU * 12.0) - 0.5);
    return smoothstep(0.14, 0.03, ticks);
}

vec3 calcNormal(vec3 pos, float side, float strandR)
{
    vec2 e = vec2(SURF_EPS, 0.0);
    return normalize(vec3(
        mapBraid(pos + e.xyy, side, strandR).x - mapBraid(pos - e.xyy, side, strandR).x,
        mapBraid(pos + e.yxy, side, strandR).x - mapBraid(pos - e.yxy, side, strandR).x,
        mapBraid(pos + e.yyx, side, strandR).x - mapBraid(pos - e.yyx, side, strandR).x
    ));
}

vec3 marchHit(vec3 ro, vec3 rd, float side, float strandR, float glowGain)
{
    float t = 0.0;
    float glow = 0.0;
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec3 pos = ro + rd * t;
        vec3 m = mapBraid(pos, side, strandR);
        glow += exp(-7.0 * max(m.x, 0.0)) * 0.03 * glowGain;
        if (m.x < SURF_EPS)
            return vec3(t, m.y, m.z);
        t += clamp(m.x * 0.8, 0.008, 0.3);
        if (t > MAX_DIST) break;
    }
    return vec3(-glow, 0.0, 0.0);
}

vec3 phaseColor(float phi, float strand, float phaseSpeed)
{
    float h = fract(phi / TAU - phaseSpeed * iTime + strand * 0.08);
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
    float side = chiralitySide();

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);
    float strandR = STRAND_R * (0.85 + 0.6 * bass);
    float phaseSpeed = SPEED * (0.7 + 1.3 * mid);
    float glowGain = 0.75 + 1.3 * high;
    float emit = 0.85 + 0.45 * high;

    float az = 0.12 * iTime * (0.85 + 0.4 * mid);
    float el = 0.35;
    if (iMouse.z > 0.0)
    {
        az = 3.0 * PI * (iMouse.x / iResolution.x - 0.5);
        el = clamp(PI * (0.5 - iMouse.y / iResolution.y), -1.1, 1.1);
    }
    float ca = cos(az), sa = sin(az);
    float ce = cos(el), se = sin(el);
    vec3 ro = vec3(sa * ce, se, ca * ce) * 4.5;
    vec3 ta = vec3(0.0, 0.0, 0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.55 * ww);

    vec3 col = aetherBg(rd, uv);
    vec3 hit = marchHit(ro, rd, side, strandR, glowGain);

    if (hit.x > 0.0)
    {
        vec3 pos = ro + rd * hit.x;
        vec3 nor = calcNormal(pos, side, strandR);
        float phi = hit.y;
        float strand = hit.z;
        float phase = TAU * strand / float(N_STRANDS);
        vec3 mate = phaseColor(phi, strand, phaseSpeed);
        float ticks = twistStripe(pos, phi, phase, side, phaseSpeed);
        mate = mix(mate, mate * 1.3 + vec3(0.12), ticks);

        float dif = clamp(0.55 + 0.45 * dot(nor, normalize(vec3(0.35, 0.85, 0.25))), 0.0, 1.0);
        float fre = pow(clamp(1.0 + dot(rd, nor), 0.0, 1.0), 2.0);
        col = (mate * dif + fre * 0.22 * mate) * emit;
    }
    else
    {
        col += phaseColor(iTime * phaseSpeed * TAU, 0.0, phaseSpeed) * (-hit.x) * 0.85;
    }

    col = pow(max(col, 0.0), vec3(0.95));
    fragColor = vec4(col, 1.0);
}
