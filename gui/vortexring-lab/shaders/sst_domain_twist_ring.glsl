// SST domain-twist ring  —  [BRIDGE] visualisation only (not a proof)
// Image-tab paste. iChannel0 = Microphone or Audio.
// Core idea: double polar unwrap + shear + mod lobes (domain SDF), not a mesh braid.
// (p,q) sets winding scales; sign(q) flips shear (chirality). Original rewrite.

#define MAX_STEPS  80
#define MAX_DIST   40.0
#define SURF_EPS   0.0015
#define RING_R     1.5
#define LOBE_R     1.0
#define MOD_CELL   0.2
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

// Same as sst_knot_catalog.domain_twist_windings
vec3 domainTwistWindings(float p, float q)
{
    float w1 = 0.15 + 0.05 * abs(p);
    float w2 = 0.25 + 0.08 * abs(q);
    float shear = (q < 0.0) ? -1.0 : 1.0;
    return vec3(w1, w2, shear);
}

vec3 rotAxis(vec3 p, vec3 a, float t)
{
    a = normalize(a);
    return mix(a * dot(p, a), p, cos(t)) + sin(t) * cross(p, a);
}

// Returns SDF; writes unwrap phase into inout uPhase for colouring
float mapTwist(vec3 p, float w1, float w2, float shear, float tubeR, float lobeContrast, out float uPhase)
{
    p.zx = vec2(atan(p.z, p.x) / PI * w1, length(p.zx) - RING_R);
    p.xy = vec2(atan(p.x, p.y) / PI * w2, length(p.xy) - LOBE_R);
    p.x += shear * p.z;
    uPhase = p.x;
    float cell = MOD_CELL * (1.1 - 0.35 * lobeContrast);
    p.x = mod(p.x + 0.5 * cell, cell) - 0.5 * cell;
    vec2 g = vec2(5.0, 1.0);
    return length(p.xy * g) - tubeR;
}

float mapOnly(vec3 p, float w1, float w2, float shear, float tubeR, float lobeContrast)
{
    float ph;
    return mapTwist(p, w1, w2, shear, tubeR, lobeContrast, ph);
}

vec3 calcNormal(vec3 p, float w1, float w2, float shear, float tubeR, float lobeContrast)
{
    vec2 e = vec2(SURF_EPS, 0.0);
    return normalize(vec3(
        mapOnly(p + e.xyy, w1, w2, shear, tubeR, lobeContrast) -
        mapOnly(p - e.xyy, w1, w2, shear, tubeR, lobeContrast),
        mapOnly(p + e.yxy, w1, w2, shear, tubeR, lobeContrast) -
        mapOnly(p - e.yxy, w1, w2, shear, tubeR, lobeContrast),
        mapOnly(p + e.yyx, w1, w2, shear, tubeR, lobeContrast) -
        mapOnly(p - e.yyx, w1, w2, shear, tubeR, lobeContrast)
    ));
}

vec2 march(vec3 ro, vec3 rd, float w1, float w2, float shear, float tubeR, float lobeContrast, float glowGain)
{
    float t = 0.0;
    float glow = 0.0;
    float ph = 0.0;
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec3 pos = ro + rd * t;
        float d = mapTwist(pos, w1, w2, shear, tubeR, lobeContrast, ph);
        glow += exp(-6.0 * max(d, 0.0)) * 0.028 * glowGain;
        if (d < SURF_EPS)
            return vec2(t, ph);
        t += clamp(d * 0.85, 0.01, 0.4);
        if (t > MAX_DIST) break;
    }
    return vec2(-glow, ph);
}

vec3 phaseColor(float uPhase, float phaseSpeed)
{
    float h = fract(uPhase * 2.5 - phaseSpeed * iTime);
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

    vec2 pq = knotPQ();
    vec3 w = domainTwistWindings(pq.x, pq.y);
    float w1 = w.x, w2 = w.y, shear = w.z;

    float tubeR = 0.28 * (0.85 + 0.55 * bass);
    float lobeContrast = 0.55 + 0.9 * high;
    float rotGain = 0.7 + 1.2 * mid;
    float glowGain = 0.75 + 1.2 * bass;
    float phaseSpeed = SPEED * (0.7 + 1.3 * high);

    float az = 0.1 * iTime * rotGain;
    float el = 0.18;
    if (iMouse.z > 0.0)
    {
        az = 3.0 * PI * (iMouse.x / iResolution.x - 0.5);
        el = clamp(PI * (0.5 - iMouse.y / iResolution.y), -1.1, 1.1);
    }
    float ca = cos(az), sa = sin(az);
    float ce = cos(el), se = sin(el);
    vec3 ro = vec3(sa * ce, se, ca * ce) * 6.0;
    vec3 ta = vec3(0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 1.7 * ww);

    // Object spin (mid-driven), separate from camera
    float spin = iTime * (0.12 + 0.55 * mid);
    // Apply inverse rot to ray so map stays in object space
    // Simpler: rotate query point inside map via pre-rot of ro/rd
    vec3 axisY = vec3(0.0, 1.0, 0.0);
    vec3 axisX = vec3(1.0, 0.0, 0.0);
    ro = rotAxis(ro, axisX, spin * 0.15);
    rd = rotAxis(rd, axisX, spin * 0.15);
    ro = rotAxis(ro, axisY, spin);
    rd = rotAxis(rd, axisY, spin);

    vec3 col = aetherBg(rd, uv);
    vec2 hit = march(ro, rd, w1, w2, shear, tubeR, lobeContrast, glowGain);

    if (hit.x > 0.0)
    {
        vec3 pos = ro + rd * hit.x;
        vec3 nor = calcNormal(pos, w1, w2, shear, tubeR, lobeContrast);
        vec3 mate = phaseColor(hit.y, phaseSpeed);

        float dif = clamp(0.55 + 0.45 * dot(nor, normalize(vec3(0.4, 0.85, 0.3))), 0.0, 1.0);
        float fre = pow(clamp(1.0 + dot(rd, nor), 0.0, 1.0), 2.0);
        float ao = clamp(mapOnly(pos + nor * 0.35, w1, w2, shear, tubeR, lobeContrast) / 0.35, 0.25, 1.0);
        col = (mate * dif + fre * 0.22 * mate) * ao;
        col *= 0.9 + 0.25 * mid;

        vec3 li = normalize(vec3(0.5, 0.9, 0.4));
        float spe = pow(clamp(dot(reflect(rd, nor), li), 0.0, 1.0), 12.0);
        col += spe * 0.35 * mate;
    }
    else
    {
        col += phaseColor(iTime * phaseSpeed, phaseSpeed) * (-hit.x) * 0.9;
    }

    col = pow(max(col, 0.0), vec3(0.95));
    fragColor = vec4(col, 1.0);
}
