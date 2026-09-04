// SST trefoil ribbon  —  [BRIDGE] visualisation only (not a proof)
// Image-tab. iChannel0 = Microphone or Audio.
// T(2,3) centreline + Frenet frame + twisted rounded-box ribbon.
// One-way roll (no chirality flip). Mouse orbit persists after release.

#define MAX_STEPS  100
#define MAX_DIST   50.0
#define SURF_EPS   0.0015
#define COARSE     32
#define FINE       16
#define TREFOIL_S  0.55
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

// Same as sst_knot_catalog.classic_trefoil_point
vec3 classicTrefoil(float t, float scale)
{
    return vec3(
        sin(t) + 2.0 * sin(2.0 * t),
        cos(t) - 2.0 * cos(2.0 * t),
        -sin(3.0 * t)
    ) * scale;
}

float chiralitySide()
{
    return 1.0;
}

void mouseOrbit(float az0, float el0, out float az, out float el)
{
    az = az0;
    el = el0;
    // Shadertoy keeps iMouse.xy at the last drag after release; z>0 only while held.
    if (iMouse.x > 0.5 || iMouse.y > 0.5)
    {
        az = (iMouse.x / iResolution.x - 0.5) * TAU;
        el = clamp((0.5 - iMouse.y / iResolution.y) * PI, -1.15, 1.15);
    }
}

void getFrame(float t, float scale, float side, out vec3 p, out vec3 T, out vec3 N, out vec3 B)
{
    float eps = 0.01;
    p = classicTrefoil(t, scale);
    p.z *= side;
    vec3 pn = classicTrefoil(t + eps, scale); pn.z *= side;
    vec3 pp = classicTrefoil(t - eps, scale); pp.z *= side;
    T = normalize(pn - p);
    vec3 curv = pn - 2.0 * p + pp;
    N = normalize(cross(T, cross(curv, T)));
    if (dot(N, N) < 1e-6)
        N = normalize(cross(T, vec3(0.0, 1.0, 0.0)));
    B = normalize(cross(T, N));
}

float sdRoundedBox2D(vec2 p, vec2 b, float r)
{
    vec2 d = abs(p) - b + r;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;
}

float mapRibbon(vec3 p, float side, float halfW, float halfT, float twistAmp, out float hitT, out float twistW)
{
    float minDs = 1e10;
    float closestT = 0.0;
    for (int i = 0; i < COARSE; i++)
    {
        float t = float(i) / float(COARSE) * TAU;
        vec3 q = classicTrefoil(t, TREFOIL_S);
        q.z *= side;
        vec3 dV = p - q;
        float dSq = dot(dV, dV);
        if (dSq < minDs) { minDs = dSq; closestT = t; }
    }
    float stepT = TAU / float(COARSE);
    float startT = closestT - stepT;
    for (int i = 0; i <= FINE; i++)
    {
        float t = startT + float(i) * (stepT * 2.0 / float(FINE));
        vec3 q = classicTrefoil(t, TREFOIL_S);
        q.z *= side;
        vec3 dV = p - q;
        float dSq = dot(dV, dV);
        if (dSq < minDs) { minDs = dSq; closestT = t; }
    }

    vec3 cp, T, N, B;
    getFrame(closestT, TREFOIL_S, side, cp, T, N, B);
    float w = closestT * 3.0 - iTime * (0.70 + 0.90 * twistAmp);
    float ang = w;
    vec3 toP = p - cp;
    float u = dot(toP, N * cos(ang) + B * sin(ang));
    float v = dot(toP, B * cos(ang) - N * sin(ang));
    float d = sdRoundedBox2D(vec2(u, v), vec2(halfW, halfT), 0.015);
    hitT = closestT;
    twistW = sin(w);
    return d * 0.85;
}

float mapSimple(vec3 p, float side, float halfW, float halfT, float twistAmp)
{
    float ht, tw;
    return mapRibbon(p, side, halfW, halfT, twistAmp, ht, tw);
}

vec3 calcNormal(vec3 p, float side, float halfW, float halfT, float twistAmp)
{
    float d = mapSimple(p, side, halfW, halfT, twistAmp);
    vec2 e = vec2(0.002, 0.0);
    return normalize(vec3(
        d - mapSimple(p - e.xyy, side, halfW, halfT, twistAmp),
        d - mapSimple(p - e.yxy, side, halfW, halfT, twistAmp),
        d - mapSimple(p - e.yyx, side, halfW, halfT, twistAmp)
    ));
}

vec3 phaseColor(float t)
{
    float h = fract(t / TAU - SPEED * iTime);
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
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);
    float halfW = 0.18 * (0.85 + 0.5 * bass);
    float halfT = 0.028 * (0.85 + 0.45 * bass);
    float twistAmp = 0.55 + 0.9 * mid;
    float specGain = 0.8 + 1.4 * high;
    float side = chiralitySide();

    float az, el;
    mouseOrbit(0.0, 0.35, az, el);
    float ca = cos(az), sa = sin(az);
    float ce = cos(el), se = sin(el);
    vec3 ro = vec3(sa * ce, se, ca * ce) * 7.5;
    vec3 ta = vec3(0.0);
    vec3 ww = normalize(ta - ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    vec3 rd = normalize(uv.x * uu + uv.y * vv + 2.0 * ww);

    vec3 col = aetherBg(rd, uv);
    float tRay = 0.0;
    float hitT = 0.0;
    float twistW = 0.0;
    bool hit = false;
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec3 pos = ro + rd * tRay;
        float d = mapRibbon(pos, side, halfW, halfT, twistAmp, hitT, twistW);
        tRay += d;
        if (d < SURF_EPS) { hit = true; break; }
        if (tRay > MAX_DIST) break;
    }

    if (hit)
    {
        vec3 pos = ro + rd * tRay;
        vec3 nor = calcNormal(pos, side, halfW, halfT, twistAmp);
        vec3 mate = phaseColor(hitT);
        mate = mix(mate, mate * 1.15, 0.5 + 0.5 * twistW);

        vec3 l = normalize(vec3(0.5, 1.0, -0.4));
        float amb = 0.18;
        float dif = max(0.0, dot(nor, l)) * 0.85;
        float spe = pow(max(0.0, dot(nor, normalize(l - rd))), 48.0) * specGain;
        col = mate * (dif + amb) + vec3(0.9, 0.95, 1.0) * spe * 0.55;
        col *= 1.0 - tRay * 0.008;
    }

    col = clamp(col, 0.0, 1.0);
    col = pow(col, vec3(0.95));
    fragColor = vec4(col, 1.0);
}
