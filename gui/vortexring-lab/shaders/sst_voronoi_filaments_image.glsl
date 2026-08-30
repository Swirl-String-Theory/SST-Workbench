// SST Voronoi filaments — IMAGE tab
// Soft field from nearest particle; RGB strand tubes for MODE_STRANDS paths.
// Channels: iChannel0 = Buffer A, iChannel1 = Buffer B, iChannel2 = Audio (optional)
// UX knobs live in Common. Audio helpers are local (need iChannel2 + iTime).

float sstAudio(float x)
{
    float u = clamp(x, 0.0, 1.0);
    return max(texture(iChannel2, vec2(u, 0.25)).x, 0.0);
}

float sstAudioSmooth(float x)
{
    float u = clamp(x, 0.0, 1.0);
    float i0 = floor(u * FREQ_BINS) / FREQ_BINS;
    float i1 = min(i0 + 1.0 / FREQ_BINS, 1.0);
    float f = fract(u * FREQ_BINS);
    return mix(sstAudio(i0), sstAudio(i1), smoothstep(0.0, 1.0, f));
}

float sstBand(float live, float fb)
{
#if AUDIO_FALLBACK
    return max(live, AUDIO_FB_FLOOR + fb * (0.5 + 0.5 * sin(iTime * (1.1 + fb))));
#else
    return live;
#endif
}

void sstBands(out float bass, out float mid, out float high)
{
    bass = sstBand(sstAudioSmooth(AUDIO_BASS_X), AUDIO_FB_BASS);
    mid  = sstBand(sstAudioSmooth(AUDIO_MID_X),  AUDIO_FB_MID);
    high = sstBand(sstAudioSmooth(AUDIO_HIGH_X), AUDIO_FB_HIGH);
}

float pathBand(int pathId)
{
    float x = mix(AUDIO_BASS_X, AUDIO_HIGH_X, pathFreqX(pathId));
    float fb = mix(AUDIO_FB_BASS, AUDIO_FB_HIGH, pathFreqX(pathId));
    return sstBand(sstAudioSmooth(x), fb);
}

vec3 shiftHue(vec3 col, float dh)
{
    float a = dh * TAU;
    float ca = cos(a), sa = sin(a);
    mat3 m = mat3(
        ca + (1.0 - ca) / 3.0,
        (1.0 - ca) / 3.0 - sqrt(1.0 / 3.0) * sa,
        (1.0 - ca) / 3.0 + sqrt(1.0 / 3.0) * sa,
        (1.0 - ca) / 3.0 + sqrt(1.0 / 3.0) * sa,
        ca + (1.0 - ca) / 3.0,
        (1.0 - ca) / 3.0 - sqrt(1.0 / 3.0) * sa,
        (1.0 - ca) / 3.0 - sqrt(1.0 / 3.0) * sa,
        (1.0 - ca) / 3.0 + sqrt(1.0 / 3.0) * sa,
        ca + (1.0 - ca) / 3.0
    );
    return clamp(m * col, 0.0, 1.0);
}

vec3 pathColor(int pathId, float phase, float mid, float pBand)
{
    vec3 base = pathAt(pathId).particle.color;
    float h = fract(phase * 0.5 + iTime * 0.05);
    vec3 mate = mix(base, base * 1.15, 0.25 + 0.25 * sin(h * TAU));
    float dh = HUE_AUDIO * (0.5 * mid + 0.5 * pBand);
    return shiftHue(mate, dh);
}

float ringBand(float d, float width)
{
    float h = max(width, 0.5) * 0.5;
    return smoothstep(h + 1.5, h, d);
}

// Closest t on a filament (STRAND_SAMPLES samples) + distance in pixels.
void nearestOnPath(vec2 px, int pathId, out float tBest, out float dBest)
{
    dBest = 1e9;
    tBest = 0.0;
    for (int i = 0; i < STRAND_SAMPLES; i++)
    {
        float t = float(i) / float(STRAND_SAMPLES);
        float d = loopDist(px, filamentPath(t, pathId));
        if (d < dBest)
        {
            dBest = d;
            tBest = t;
        }
    }
}

vec3 rgbStrandColor(float t, float d, float widthPx, float pBand, vec3 mate, float phase)
{
    float w = widthPx * (1.0 + 0.35 * pBand);
    float band = ringBand(d, w);
    float a = (t * TAU - phase * TAU) * STRAND_WAVE;
    vec3 chase = vec3(
        0.5 + 0.5 * sin(a),
        0.5 + 0.5 * sin(a + TAU / 3.0),
        0.5 + 0.5 * sin(a + 2.0 * TAU / 3.0)
    );
    return band * chase * mate;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    sstRes = iResolution.xy;
    float bass, mid, high;
    sstBands(bass, mid, high);

    vec3 col = BG_COL;

    int id0 = int(texture(iChannel0, fragCoord / sstRes).x);
    if (id0 < 0 || id0 >= PARTICLE_COUNT) id0 = 0;
    vec4 h0 = readParticle(iChannel1, id0);

    int pathId = pathOfParticle(id0);
    FilamentPath fp0 = pathAt(pathId);
    float pBand = pathBand(pathId);

    if (fp0.mode == MODE_PARTICLES)
    {
        float dist = max(loopDist(fragCoord, h0.xy), 0.5);
        float distEff = dist / max(fp0.particle.size, 0.05);
        float glow = (GLOW_BASE + GLOW_BASS * bass) / distEff;
        glow = clamp(glow, 0.0, GLOW_MAX);

        float ph = phaseOfParticle(id0);
        vec3 mate = pathColor(pathId, ph, mid, pBand);

        int id1 = int(texture(iChannel0, fragCoord / sstRes).y);
        if (id1 >= 0 && id1 < PARTICLE_COUNT)
        {
            float d1 = max(loopDist(fragCoord, readParticle(iChannel1, id1).xy), 0.5);
            float edge = smoothstep(0.0, EDGE_BASE + EDGE_HIGH * high, abs(dist - d1));
            mate *= EDGE_MIX_LO + EDGE_MIX_HI * edge;
        }

        col += mate * glow * (COL_MID + COL_MID_AUDIO * mix(mid, pBand, 0.4));
        col += mate * pow(glow * COL_HIGH_POW, 2.0) * (COL_HIGH_BASE + COL_HIGH_AUDIO * high);
    }

    for (int i = 0; i < NUM_PATHS; i++)
    {
        FilamentPath fp = pathAt(i);
        if (fp.mode != MODE_STRANDS)
            continue;
        float tBest, dBest;
        nearestOnPath(fragCoord, i, tBest, dBest);
        float widthPx = max(fp.strandWidth, 0.002) * max(fp.particle.size, 0.05) * sstRes.y;
        float pathPh = readParticle(iChannel1, pathPhaseIndex(i)).x;
        col += rgbStrandColor(tBest, dBest, widthPx, pathBand(i), fp.particle.color, pathPh);
    }

    vec2 uv = (fragCoord - 0.5 * sstRes) / sstRes.y;
    col *= 1.0 - VIGNETTE * dot(uv, uv);
    col = pow(max(col, 0.0), vec3(GAMMA));
    fragColor = vec4(col, 1.0);
}
