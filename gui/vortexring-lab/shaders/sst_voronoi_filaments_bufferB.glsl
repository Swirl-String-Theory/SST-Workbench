// SST Voronoi filaments — BUFFER B
// Particles: xy = position, zw = velocity. Attracted to multi knot/link paths.
// Channels: iChannel0 = Buffer A, iChannel1 = Buffer B (self)
// Optional: iChannel2 = Audio (Mic) — AUDIO_* UX knobs live in Common.
// Audio helpers must live HERE (not in Common): Common has no iChannel2/iTime.
//
// Per-path audio: bass → radial vortex stretch; path0 mono / high paths stereo-wide;
// pathBand from spectrum slice drives phase speed + attract.

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

vec2 applyBassStretch(vec2 tar, float bass)
{
    vec2 centre = sstRes * 0.5;
    return centre + (tar - centre) * (1.0 + STRETCH_BASS * bass);
}

vec2 applyStereoWidth(vec2 tar, int pathId)
{
    float width = pathStereoWidth(pathId);
    if (width < 1e-6)
        return tar; // path 0 = mono
    float stereo = sstAudioSmooth(AUDIO_WIDE_L) - sstAudioSmooth(AUDIO_WIDE_R);
    tar.x += width * STEREO_AMP * stereo * sstRes.y;
    return tar;
}

float pathPhaseSpeed(float mid, float pBand, float pathSpeed)
{
    return max(pathSpeed, 0.0) * (PATH_SPEED_BASE + PATH_SPEED_MID * mix(mid, pBand, 0.65));
}

float sstDelta()
{
    return max(iTimeDelta, 1.0 / 120.0);
}

// Integrate phase; never rewind when speed drops (unlike iTime * speed).
float accumulatePathPhase(float prev, float dt, float speed)
{
    return fract(prev + max(dt, 0.0) * max(speed, 0.0));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    sstRes = iResolution.xy;
    int id = textToIndex(fragCoord);

    float bass, mid, high;
    sstBands(bass, mid, high);

    // Extra texels: one integrated phase per path (read by particles next frame).
    if (id >= PARTICLE_COUNT && id < PARTICLE_COUNT + NUM_PATHS)
    {
        int pathId = id - PARTICLE_COUNT;
        float speed = pathPhaseSpeed(mid, pathBand(pathId), pathAt(pathId).particle.speed);
        float prev = (iFrame == 0) ? 0.0 : texture(iChannel1, fragCoord / sstRes).x;
        fragColor = vec4(accumulatePathPhase(prev, sstDelta(), speed), 0.0, 0.0, 1.0);
        return;
    }

    if (id >= PARTICLE_COUNT)
    {
        fragColor = vec4(0.0);
        return;
    }

    vec4 c = texture(iChannel1, fragCoord / sstRes);

    if (iFrame == 0)
    {
        int pathId = pathOfParticle(id);
        float ph = phaseOfParticle(id) + hash11(float(id) * PHASE_JITTER);
        vec2 pos = filamentPath(fract(ph), pathId);
        vec2 vel = (vec2(hash11(float(id) + 1.3), hash11(float(id) + 2.7)) - 0.5) * INIT_VEL_SPAN;
        fragColor = vec4(pos, vel);
        return;
    }

    // Neighbour from Voronoi field at our pixel (second site pushes us)
    int nbr = int(texture(iChannel0, c.xy / sstRes).y);
    if (nbr < 0 || nbr >= PARTICLE_COUNT) nbr = (id + 1) % PARTICLE_COUNT;
    vec4 p1 = readParticle(iChannel1, nbr);

    // Soft repulsion
    c.zw += safeInvert(loopRel(c.xy, p1.xy)) * (REPEL_BASE + REPEL_HIGH * high);
    c.zw /= DAMPING;

    // Attract to own filament path (bass stretch + mono/wide)
    int pathId = pathOfParticle(id);
    float pBand = pathBand(pathId);
    float pathPh = readParticle(iChannel1, pathPhaseIndex(pathId)).x;
    float ph = fract(phaseOfParticle(id) + pathPh);
    vec2 tar = filamentPath(ph, pathId);
    tar = applyBassStretch(tar, bass);
    tar = applyStereoWidth(tar, pathId);
    float attract = ATTRACT_BASE + ATTRACT_BASS * mix(bass, pBand, 0.5);
    c.zw += safeNormalize(tar - c.xy) * attract;

    // Speed clamp
    float vmax = (VMAX_BASE + VMAX_MID * mid) * max(pathAt(pathId).particle.speed, 0.15);
    float sp = length(c.zw);
    if (sp > vmax) c.zw *= vmax / sp;

    c.xy += c.zw;
    c.xy -= floor(c.xy / sstRes) * sstRes;

    // Tiny noise
    c.z += (hash11(float(id) + float(iFrame) * 0.01) - 0.5) * NOISE_AMP;
    c.w += (hash11(float(id) * 1.7 + float(iFrame) * 0.02) - 0.5) * NOISE_AMP;

    fragColor = c;
}
