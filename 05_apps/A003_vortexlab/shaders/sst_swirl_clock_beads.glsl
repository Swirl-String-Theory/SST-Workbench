// SST swirl-clock beads  —  [BRIDGE] visualisation only (not a proof)
// Image-tab. iChannel0 = Microphone or Audio.
// Still camera until mouse orbit; last mouse pose persists after release.
// 3-strand centre helix + radial ring; both roll one way. Original rewrite.

#define MAX_STEPS  72
#define MAX_DIST   12.0
#define SURF_EPS   0.01
#define N_BEADS    24.0
#define N_STRANDS  3.0
#define RING_R     0.6
#define HELIX_R    0.14
#define HELIX_TWIST 2.3
#define HELIX_DIR  1.0
#define BEAD_SEP   0.1
#define BEAD_STEP  0.16
#define CAM_DIST   2.8
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

void camRay(vec2 uv, float az, float el, float dist, out vec3 ro, out vec3 rd)
{
    float ca = cos(az), sa = sin(az);
    float ce = cos(el), se = sin(el);
    ro = vec3(sa * ce, se, ca * ce) * dist;
    vec3 ww = normalize(-ro);
    vec3 uu = normalize(cross(ww, vec3(0.0, 1.0, 0.0)));
    vec3 vv = cross(uu, ww);
    rd = normalize(uv.x * uu + uv.y * vv + 1.7 * ww);
}

// Returns distance; writes bead id into beadId
float mapBeads(vec3 p, float beadR, float twist, out float beadId)
{
    vec3 q = p;
    float halfSpan = (N_BEADS - 1.0) * 0.5 * BEAD_STEP;
    float hsec = TAU / N_STRANDS;

    // --- 3-strand helix along z (one-way roll) ---
    float pz = -p.z;
    float idl = clamp(round(pz / BEAD_STEP) * BEAD_STEP, -halfSpan, halfSpan);
    vec3 pl = p;
    pl.z = pz - idl;
    pl.xy *= rot2(-(idl * HELIX_TWIST + twist));
    float hr = length(pl.xy);
    float ha = atan(pl.x, pl.y);
    float hm = mod(ha + 8.0 * TAU, hsec) - 0.5 * hsec;
    float strand = floor(mod(ha + 8.0 * TAU, TAU) / hsec);
    pl.xy = vec2(sin(hm), cos(hm)) * hr;
    pl.y -= HELIX_R;
    float dHelix = length(pl) - beadR;

    // --- radial ring in xy (same roll sign as helix) ---
    float ang = atan(q.x, q.y);
    float sector = TAU / N_BEADS;
    float idr = floor(ang / sector) * sector;
    float m = mod(ang, sector) - 0.5 * sector;
    float rr = length(q.xy);
    vec3 pr;
    pr.xy = vec2(sin(m), cos(m)) * rr;
    pr.z = q.z;
    pr.y -= RING_R;
    pr.yz *= rot2(1.5 * idr + twist);
    pr.y = abs(pr.y) - BEAD_SEP;
    float dRad = length(pr) - beadR;

    if (dHelix < dRad)
    {
        beadId = (idl / BEAD_STEP) + 0.5 * (N_BEADS - 1.0)
               + strand * (N_BEADS / N_STRANDS);
        return dHelix;
    }
    beadId = idr / sector;
    return dRad;
}

float mapSimple(vec3 p, float beadR, float twist)
{
    float id;
    return mapBeads(p, beadR, twist, id);
}

vec3 calcNormal(vec3 p, float beadR, float twist)
{
    vec2 e = vec2(0.001, 0.0);
    return normalize(vec3(
        mapSimple(p + e.yxx, beadR, twist),
        mapSimple(p + e.xyx, beadR, twist),
        mapSimple(p + e.xxy, beadR, twist)
    ) - mapSimple(p, beadR, twist));
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
    float twist = HELIX_DIR * iTime * (0.40 + 0.50 * mid);
    float emit = 0.85 + 0.5 * high;

    float az, el;
    mouseOrbit(0.0, 0.22, az, el);
    vec3 ro, rd;
    camRay(uv, az, el, CAM_DIST, ro, rd);

    float t = 0.0;
    float beadId = 0.0;
    bool hit = false;
    for (int i = 0; i < MAX_STEPS; i++)
    {
        vec3 pos = ro + rd * t;
        float d = mapBeads(pos, beadR, twist, beadId);
        t += d;
        if (d < SURF_EPS) { hit = true; break; }
        if (t > MAX_DIST) break;
    }

    vec3 col = aetherBg(uv);
    if (hit)
    {
        vec3 pos = ro + rd * t;
        vec3 nor = calcNormal(pos, beadR, twist);
        vec3 mate = phaseColor(beadId);
        vec3 L = normalize(vec3(0.35, 0.75, 0.45));
        float dif = 0.45 + 0.55 * max(0.0, dot(nor, L));
        float spe = pow(max(0.0, dot(nor, normalize(L - rd))), 80.0);
        col = mate * dif * emit + spe * 0.55 * vec3(0.9, 0.95, 1.0);
    }

    col = pow(max(col, 0.0), vec3(0.95));
    fragColor = vec4(col, 1.0);
}
