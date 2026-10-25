// SST Voronoi filaments — BUFFER B
// Particles: xy = position, zw = velocity. Attracted to multi knot/link paths.
// Channels: iChannel0 = Buffer A, iChannel1 = Buffer B (self)
// Optional: iChannel2 = Audio (Mic) — AUDIO_* UX knobs live in Common.
// Audio helpers must live HERE (not in Common): Common has no iChannel2/iTime.
//
// Per-path audio: bass → radial vortex stretch; path0 mono / high paths stereo-wide;
// pathBand from spectrum slice drives phase speed + attract.
// Live UI texels start at PARTICLE_COUNT + NUM_PATHS (after path phases).

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

float sstBand(float live, float fb, float useFb)
{
    float wob = AUDIO_FB_FLOOR + fb * (0.5 + 0.5 * sin(iTime * (1.1 + fb)));
    if (useFb > 0.5)
        return max(live, wob);
    return live;
}

void sstBands(out float bass, out float mid, out float high, float useFb)
{
    bass = sstBand(sstAudioSmooth(AUDIO_BASS_X), AUDIO_FB_BASS, useFb);
    mid  = sstBand(sstAudioSmooth(AUDIO_MID_X),  AUDIO_FB_MID, useFb);
    high = sstBand(sstAudioSmooth(AUDIO_HIGH_X), AUDIO_FB_HIGH, useFb);
}

float pathBand(int pathId, float useFb)
{
    float x = mix(AUDIO_BASS_X, AUDIO_HIGH_X, pathFreqX(pathId));
    float fb = mix(AUDIO_FB_BASS, AUDIO_FB_HIGH, pathFreqX(pathId));
    return sstBand(sstAudioSmooth(x), fb, useFb);
}

vec2 applyBassStretch(vec2 tar, float bass, float stretch)
{
    vec2 centre = sstRes * 0.5;
    return centre + (tar - centre) * (1.0 + stretch * bass);
}

vec2 applyStereoWidth(vec2 tar, int pathId, float amp)
{
    float width = pathStereoWidth(pathId);
    if (width < 1e-6)
        return tar; // path 0 = mono
    float stereo = sstAudioSmooth(AUDIO_WIDE_L) - sstAudioSmooth(AUDIO_WIDE_R);
    tar.x += width * amp * stereo * sstRes.y;
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

vec4 uiInitSlot(int slot)
{
    vec4 d = vec4(0.0);
    if (slot == UI_SLOT_HEAD)
    {
        d.x = 0.0;
        d.y = -1.0;
        d.z = 0.0;
        d.w = 0.0;
        return d;
    }
    if (slot == UI_SLOT_META)
        return vec4(0.0);
    if (slot >= UI_SLOT_SL0 && slot < UI_SLOT_SL0 + UI_N_SL)
        return vec4(uiSliderDefault(slot - UI_SLOT_SL0), 0.0, 0.0, 1.0);
    if (slot >= UI_SLOT_PATH && slot < UI_SLOT_COUNT)
    {
        int rel = slot - UI_SLOT_PATH;
        int pathId = rel / UI_PATH_FIELDS;
        int field = rel - pathId * UI_PATH_FIELDS;
        return vec4(uiPathFieldDefault(pathId, field), 0.0, 0.0, 1.0);
    }
    return d;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    sstRes = iResolution.xy;
    int id = textToIndex(fragCoord);

    float useFb = uiLive(iChannel1, SL_AUDIOFB);
    float bass, mid, high;
    sstBands(bass, mid, high, useFb);

    // Extra texels: one integrated phase per path (read by particles next frame).
    if (id >= PARTICLE_COUNT && id < PARTICLE_COUNT + NUM_PATHS)
    {
        int pathId = id - PARTICLE_COUNT;
        float speed = pathPhaseSpeed(mid, pathBand(pathId, useFb), pathAtUi(iChannel1, pathId).particle.speed);
        float prev = (iFrame == 0) ? 0.0 : texture(iChannel1, fragCoord / sstRes).x;
        fragColor = vec4(accumulatePathPhase(prev, sstDelta(), speed), 0.0, 0.0, 1.0);
        return;
    }

    // Live UI state (header / sliders / per-path fields).
    if (id >= uiTexelIndex(0) && id < uiTexelIndex(UI_SLOT_COUNT))
    {
        int slot = id - uiTexelIndex(0);
        vec4 prevH = (iFrame == 0) ? uiInitSlot(UI_SLOT_HEAD) : uiLoad(iChannel1, UI_SLOT_HEAD);
        vec4 prevM = (iFrame == 0) ? uiInitSlot(UI_SLOT_META) : uiLoad(iChannel1, UI_SLOT_META);
        int open = int(prevH.x + 0.5);
        int tab = int(prevM.x + 0.5);
        int expOn = int(prevM.y + 0.5);
        int expPage = int(clamp(prevM.z, 0.0, float(UI_EXP_PAGES - 1)) + 0.5);
        int sel = int(clamp(prevH.w, 0.0, float(NUM_PATHS - 1)) + 0.5);
        int drag = int(prevH.y);
        bool down = iMouse.z > 0.0;
        bool click = down && prevH.z < 0.5;
        vec2 mp = iMouse.xy;
        int hit = uiHit(mp, open, tab, sel, expOn);

        if (slot == UI_SLOT_HEAD)
        {
            vec4 h = prevH;
            if (click && hit == HIT_HEADER)
                h.x = (open > 0) ? 0.0 : 1.0;
            if (click && hit == HIT_EXPORT && open < 1)
                h.x = 1.0; // EXP forces the panel open
            if (click && hit == HIT_PATH_PRV)
                h.w = float((sel + NUM_PATHS - 1) % NUM_PATHS);
            if (click && hit == HIT_PATH_NXT)
                h.w = float((sel + 1) % NUM_PATHS);
            if (click && hit >= HIT_SL0)
                h.y = float(hit);
            else if (click && hit >= HIT_PF0 && hit < HIT_PF0 + 3)
                h.y = float(hit);
            if (!down)
                h.y = -1.0;
            h.z = down ? 1.0 : 0.0;
            fragColor = h;
            return;
        }
        if (slot == UI_SLOT_META)
        {
            vec4 m = prevM;
            if (click && hit == HIT_TAB0) { m.x = 0.0; m.y = 0.0; }
            if (click && hit == HIT_TAB1) { m.x = 1.0; m.y = 0.0; }
            if (click && hit == HIT_TAB2) { m.x = 2.0; m.y = 0.0; }
            if (click && hit == HIT_EXPORT)
                m.y = (expOn > 0) ? 0.0 : 1.0;
            if (click && hit == HIT_EXP_PRV)
                m.z = float((expPage + UI_EXP_PAGES - 1) % UI_EXP_PAGES);
            if (click && hit == HIT_EXP_NXT)
                m.z = float((expPage + 1) % UI_EXP_PAGES);
            fragColor = m;
            return;
        }
        if (slot >= UI_SLOT_SL0 && slot < UI_SLOT_SL0 + UI_N_SL)
        {
            int sl = slot - UI_SLOT_SL0;
            float v = (iFrame == 0) ? uiSliderDefault(sl) : uiLoad(iChannel1, slot).x;
            if (click && hit == HIT_RESET)
                v = uiSliderDefault(sl);
            if (sl == SL_AUDIOFB)
            {
                if (click && hit == HIT_SL0 + SL_AUDIOFB)
                    v = (v > 0.5) ? 0.0 : 1.0;
            }
            else
            {
                bool mine = (hit == HIT_SL0 + sl) || (down && drag == HIT_SL0 + sl);
                if (down && mine)
                {
                    int row = 0;
                    if (tab == UI_TAB_MOTION)
                    {
                        if (sl == SL_SPEED) row = 1;
                        else if (sl == SL_ATTRACT) row = 2;
                        else if (sl == SL_REPEL) row = 3;
                        else if (sl == SL_STRETCH) row = 4;
                        else if (sl == SL_STEREO) row = 5;
                    }
                    else
                    {
                        if (sl == SL_DISCS) row = 1;
                        else if (sl == SL_GAMMA) row = 2;
                        else if (sl == SL_STRAND) row = 3;
                        else if (sl == SL_HUEAUD) row = 4;
                    }
                    float y0 = UI_HDR_H + UI_TAB_H;
                    float t = uiBoxT(mp, vec2(UI_TRACK_X, y0 + float(row) * UI_ROW_H + UI_TRACK_Y), vec2(UI_TRACK_W, UI_TRACK_H));
                    v = uiMixSlider(sl, t);
                }
            }
            fragColor = vec4(v, 0.0, 0.0, 1.0);
            return;
        }
        if (slot >= UI_SLOT_PATH && slot < UI_SLOT_COUNT)
        {
            int rel = slot - UI_SLOT_PATH;
            int pathId = rel / UI_PATH_FIELDS;
            int field = rel - pathId * UI_PATH_FIELDS;
            float v = (iFrame == 0) ? uiPathFieldDefault(pathId, field) : uiLoad(iChannel1, slot).x;
            if (click && hit == HIT_RESET)
                v = uiPathFieldDefault(pathId, field);
            if (pathId == sel)
            {
                if (field == PF_MODE)
                {
                    if (click && hit == HIT_MODE_P) v = 0.0;
                    if (click && hit == HIT_MODE_S) v = 1.0;
                }
                else
                {
                    bool mine = (hit == HIT_PF0 + field) || (down && drag == HIT_PF0 + field);
                    if (down && mine)
                    {
                        int row = 2 + field;
                        float y0 = UI_HDR_H + UI_TAB_H;
                        float t = uiBoxT(mp, vec2(UI_TRACK_X, y0 + float(row) * UI_ROW_H + UI_TRACK_Y), vec2(UI_TRACK_W, UI_TRACK_H));
                        v = uiMixPathField(field, t);
                    }
                }
            }
            fragColor = vec4(v, 0.0, 0.0, 1.0);
            return;
        }
        fragColor = vec4(0.0);
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
        vec2 pos = filamentPath(fract(ph), pathId, iChannel1);
        vec2 vel = (vec2(hash11(float(id) + 1.3), hash11(float(id) + 2.7)) - 0.5) * INIT_VEL_SPAN;
        fragColor = vec4(pos, vel);
        return;
    }

    int nbr = int(texture(iChannel0, c.xy / sstRes).y);
    if (nbr < 0 || nbr >= PARTICLE_COUNT) nbr = (id + 1) % PARTICLE_COUNT;
    vec4 p1 = readParticle(iChannel1, nbr);

    float repel = uiLive(iChannel1, SL_REPEL);
    c.zw += safeInvert(loopRel(c.xy, p1.xy)) * (repel + REPEL_HIGH * high);
    c.zw /= DAMPING;

    int pathId = pathOfParticle(id);
    float pBand = pathBand(pathId, useFb);
    float pathPh = readParticle(iChannel1, pathPhaseIndex(pathId)).x;
    float ph = fract(phaseOfParticle(id) + pathPh);
    vec2 tar = filamentPath(ph, pathId, iChannel1);
    tar = applyBassStretch(tar, bass, uiLive(iChannel1, SL_STRETCH));
    tar = applyStereoWidth(tar, pathId, uiLive(iChannel1, SL_STEREO));
    float attract = uiLive(iChannel1, SL_ATTRACT) + ATTRACT_BASS * mix(bass, pBand, 0.5);
    c.zw += safeNormalize(tar - c.xy) * attract;

    float vmax = (VMAX_BASE + VMAX_MID * mid) * max(pathAtUi(iChannel1, pathId).particle.speed, 0.15);
    float sp = length(c.zw);
    if (sp > vmax) c.zw *= vmax / sp;

    c.xy += c.zw;
    // No toroidal wrap — particles that leave the canvas are clipped, not mirrored.

    c.z += (hash11(float(id) + float(iFrame) * 0.01) - 0.5) * NOISE_AMP;
    c.w += (hash11(float(id) * 1.7 + float(iFrame) * 0.02) - 0.5) * NOISE_AMP;

    fragColor = c;
}
