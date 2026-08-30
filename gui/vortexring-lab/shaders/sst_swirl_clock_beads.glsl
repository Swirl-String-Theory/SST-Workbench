// SST swirl-clock beads  —  [BRIDGE] visualisation only (not a proof)
// Image-tab. iChannel0 = Microphone or Audio.
// Linear stack + radial ring of beads (clock ticks); nearest wins.
// n = 24 swirl-clock bins. Original rewrite (not a golf fork).

#define MAX_STEPS  72
#define MAX_DIST   6.0
#define SURF_EPS   0.01
#define N_BEADS    24.0
#define RING_R     0.6
#define BEAD_SEP   0.1
#define BEAD_STEP  0.16
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

vec3 phaseColor(float id)
{
    float h = fract(id / N_BEADS - SPEED * iTime);
    return mix(vec3(0.05, 0.45, 0.85), vec3(0.85, 0.12, 0.55),
               0.5 + 0.5 * sin(h * TAU));
}

mat2 rot2(float a)
{
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}

// Returns distance; writes bead id into beadId
float mapBeads(vec3 p, float beadR, float spin, out float beadId)
{
    p.y += 0.08 * sin(iTime * 2.7);
    p.z -= 2.2;
    p.xz *= rot2(spin);

    vec3 q = p;
    float halfSpan = (N_BEADS - 1.0) * 0.5 * BEAD_STEP;

    // --- linear stack along z ---
    float pz = -p.z;
    float idl = clamp(round(pz / BEAD_STEP) * BEAD_STEP, -halfSpan, halfSpan);
    vec3 pl = p;
    pl.z = pz - idl;
    pl.yx *= rot2(idl * 2.3 + iTime * 5.0);
    pl.y = abs(pl.y) - BEAD_SEP;
    float dLin = length(pl) - beadR;

    // --- radial ring in xy ---
    float ang = atan(q.x, q.y);
    float sector = TAU / N_BEADS;
    float idr = floor(ang / sector) * sector;
    float m = mod(ang, sector) - 0.5 * sector;
    float rr = length(q.xy);
    vec3 pr;
    pr.xy = vec2(sin(m), cos(m)) * rr;
    pr.z = q.z;
    pr.y -= RING_R;
    pr.yz *= rot2(1.5 * idr + iTime * 5.0);
    pr.y = abs(pr.y) - BEAD_SEP;
    float dRad = length(pr) - beadR;

    if (dLin < dRad)
    {
        beadId = (idl / BEAD_STEP) + 0.5 * (N_BEADS - 1.0);
        return dLin;
    }
    beadId = idr / sector;
    return dRad;
}

float mapSimple(vec3 p, float beadR, float spin)
{
    float id;
    return mapBeads(p, beadR, spin, id);
}

vec3 calcNormal(vec3 p, float beadR, float spin)
{
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        mapSimple(p + e.yxx, beadR, spin),
        mapSimple(p + e.xyx, beadR, spin),
        mapSimple(p + e.xxy, beadR, spin)
    ) - mapSimple(p, beadR, spin));
}

vec3 aetherBg(vec2 uv)
{
    float vign = 1.0 - 0.35 * length(uv);
    return vec3(0.01, 0.02, 0.05) * (0.9 + 0.2 * vign);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 R = iResolution.xy;
    vec2 uv = (fragCoord - 0.5 * R) / R.y;

    float bass = sstBand(sstBass(), 0.06);
    float mid  = sstBand(sstMid(),  0.05);
    float high = sstBand(sstHigh(), 0.04);
    float beadR = 0.065 * (0.85 + 0.55 * bass);
    float spin = iTime * (0.25 + 0.55 * mid);
    float emit = 0.85 + 0.5 * high;

    if (iMouse.z > 0.0)
        spin = (iMouse.x / R.x - 0.5) * TAU;

    vec3 rd = normalize(vec3(uv, 1.0));
    vec3 ro = vec3(0.0);

    float t = 0.0;
    float beadId = 0.0;
    bool hit = false;
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec3 pos = ro + rd * t;
        float d = mapBeads(pos, beadR, spin, beadId);
        t += d;
        if (d < SURF_EPS) { hit = true; break; }
        if (t > MAX_DIST) break;
    }

    vec3 col = aetherBg(uv);
    if (hit)
    {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos, beadR, spin);
        vec3 mate = phaseColor(beadId);
        vec3 L = normalize(vec3(cos(iTime * 2.0), sin(iTime), 0.4));
        float dif = 0.45 + 0.55 * max(0.0, dot(nor, L));
        float spe = pow(max(0.0, dot(nor, normalize(L - rd))), 80.0);
        col = mate * dif * emit + spe * 0.55 * vec3(0.9, 0.95, 1.0);
    }

    col = pow(max(col, 0.0), vec3(0.95));
    fragColor = vec4(col, 1.0);
}
