// SST nested braid tree  —  [BRIDGE] visualisation only (not a proof)
// Image-tab. iChannel0 = Microphone or Audio.
// Hierarchical 3×3×3 curve_transform braid (27 leaves). Original rewrite.

#define MAX_STEPS  72
#define SURF_EPS   0.012
#define STRETCH    1.5
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

float chiralitySide()
{
    return (mod(iTime, 4.0) < 2.0) ? 1.0 : -1.0;
}

// Same as sst_knot_catalog.nested_braid_point
vec3 nestedBraidPoint(float t, float phase, float stretch, float side)
{
    float sn = sin(t + phase);
    float cs = cos(t + phase);
    return vec3(cs, t * stretch, side * sn * cs);
}

float nearestOnCurve(vec3 p, float phase, float stretch, float side)
{
    float t = p.y / stretch;
    for (int i = 0; i < 12; i++)
    {
        float sn = sin(t + phase);
        float cs = cos(t + phase);
        vec3 q = nestedBraidPoint(t, phase, stretch, side);
        // Analytic-ish gradient of |q-p|^2 w.r.t. t
        float dt = 2.0 * (
            sn * (p.x - cs)
            + side * (sn * sn - cs * cs) * (p.z - side * sn * cs)
            - stretch * (p.y - stretch * t)
        );
        t -= dt * 0.1;
    }
    return t;
}

float approxLen(float t, float phase, float stretch)
{
    return t * (pow(stretch * 2.2, 1.8) + 9.9) / 10.0
         - sin((t + phase) * 2.0) * 0.1 * ((0.95 - cos(2.0 * (t + phase))) * 0.83)
         + sin(phase * 2.0) * 0.095;
}

vec3 curveTransform(vec3 p, float phase, float stretch, float radius, float targetRadius, float side)
{
    float t = nearestOnCurve(p, phase, stretch, side);
    float l = approxLen(t, phase, stretch);
    vec3 pp = nestedBraidPoint(t, phase, stretch, side);
    float sn = sin(t + phase);
    float cs = cos(t + phase);
    vec3 ny = normalize(vec3(-sn, stretch, side * (cs * cs - sn * sn)));
    vec3 nz = vec3(0.0, 0.0, 1.0);
    vec3 nx = normalize(cross(ny, nz));
    nz = normalize(cross(nx, ny));
    float scale = (1.0 + targetRadius) / radius;
    return vec3(dot(p - pp, nx), l, dot(p - pp, nz)) * scale;
}

vec3 leafColor(float index, float pulse)
{
    float h = fract(index / 27.0 + iTime * SPEED);
    vec3 base = mix(vec3(0.05, 0.45, 0.85), vec3(0.85, 0.12, 0.55),
                    0.5 + 0.5 * sin(h * TAU));
    float hi = smoothstep(2.0, 0.0, abs(index - pulse));
    return mix(base, vec3(0.95, 0.75, 0.35), hi * 0.55);
}

// Returns rgb + distance
vec4 mapTree(vec3 p, float side, float leafR, float nestSpin, float pulse)
{
    p = p.yxz;
    vec4 res = vec4(0.0, 0.0, 0.0, 1e3);
    float stretch = STRETCH;

    for (int i = 0; i < 3; i++)
    {
        float fi = float(i);
        vec3 pp = curveTransform(p, TAU * 2.0 / 3.0 * fi, stretch, 0.45, 0.55, side);
        if (length(pp.xz) > 2.0)
        {
            float d = length(pp.xz);
            if (d < res.w) res = vec4(0.02, 0.04, 0.08, d);
            continue;
        }

        float f = nestSpin + fi * PI / 3.0;
        for (int j = 0; j < 3; j++)
        {
            float fj = float(j);
            vec3 ppp = curveTransform(pp, TAU * 2.0 / 3.0 * fj + f, stretch, 0.55, 0.55, side);
            if (length(ppp.xz) > 2.0)
            {
                float d = length(ppp.xz);
                if (d < res.w) res = vec4(0.02, 0.04, 0.08, d);
                continue;
            }

            for (int k = 0; k < 3; k++)
            {
                float fk = float(k);
                vec3 q = curveTransform(ppp, TAU * 2.0 / 3.0 * fk + f / 0.2, stretch, 0.55, 0.3, side);
                float index = fi * 9.0 + fj * 3.0 + fk;
                vec3 col = leafColor(index, pulse);
                float d = length(q.xz) - leafR;
                if (d < res.w) res = vec4(col, d);
            }
        }
    }
    res.w *= 0.04;
    return res;
}

vec3 calcNormal(vec3 pos, float side, float leafR, float nestSpin, float pulse)
{
    vec2 e = vec2(1.0, -1.0) * 0.5773 * 0.025;
    return normalize(
        e.xyy * mapTree(pos + e.xyy, side, leafR, nestSpin, pulse).w +
        e.yyx * mapTree(pos + e.yyx, side, leafR, nestSpin, pulse).w +
        e.yxy * mapTree(pos + e.yxy, side, leafR, nestSpin, pulse).w +
        e.xxx * mapTree(pos + e.xxx, side, leafR, nestSpin, pulse).w
    );
}

vec3 aetherBg(vec3 rd, vec2 uv)
{
    float sky = 0.04 + 0.05 * (rd.y + 1.0);
    return vec3(0.01, 0.02, 0.05) * sky * (1.0 - 0.3 * dot(uv, uv));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 uv = fragCoord / iResolution.xy;
    vec2 ratio = iResolution.xy / iResolution.y;
    vec2 puv = (uv - 0.5) * ratio;

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);

    float side = chiralitySide();
    float leafR = 0.75 * (0.85 + 0.45 * bass);
    float nestSpin = iTime * (0.5 + 0.9 * mid);
    float pulse = (0.5 + 0.5 * sin(iTime * (0.04 + 0.08 * high))) * 27.0;
    float emit = 0.85 + 0.45 * high;

    vec3 dir = normalize(vec3(puv, -1.0));
    // Slow fly-along (SST-60); mouse overrides look slightly
    float fly = iTime * 0.08;
    vec3 origin = vec3(fly, 0.0, 4.0);
    if (iMouse.z > 0.0)
    {
        float ax = (iMouse.x / iResolution.x - 0.5) * 1.2;
        float ay = (0.5 - iMouse.y / iResolution.y) * 0.8;
        dir.xy += vec2(ax, ay);
        dir = normalize(dir);
    }

    vec3 col = aetherBg(dir, puv);
    float t = 0.0;
    vec3 pos = origin;
    vec4 hit = vec4(-1.0);
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec4 h = mapTree(pos, side, leafR, nestSpin, pulse);
        pos += dir * h.w;
        t += h.w;
        if (h.w < SURF_EPS)
        {
            hit = vec4(h.rgb, t);
            break;
        }
        if (pos.z < -40.0) break;
    }

    if (hit.w > 0.0)
    {
        vec3 n = calcNormal(origin + dir * hit.w, side, leafR, nestSpin, pulse);
        vec3 L = normalize(vec3(0.6, 0.8, 0.4));
        float dif = clamp(dot(n, L), 0.0, 1.0) * 0.75 + 0.25;
        float spe = pow(max(0.0, dot(n, normalize(L - dir))), 32.0) * high;
        col = hit.rgb * dif * emit + spe * 0.4 * hit.rgb;
    }

    col = pow(max(col, 0.0), vec3(0.95));
    fragColor = vec4(col, 1.0);
}
