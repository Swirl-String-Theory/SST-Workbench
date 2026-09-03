// SST Voronoi filaments — BUFFER A
// Nearest / second-nearest particle indices per pixel (jump-flood style).
// Channels: iChannel0 = Buffer A (self), iChannel1 = Buffer B (particles)
// Live UI state lives in Buffer B extra texels — this pass stays a site field.

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    sstRes = iResolution.xy;
    vec2 p = fragCoord;
    vec4 c = texture(iChannel0, p / sstRes);

    float seed = hash11(float(iFrame) * 0.32147 + fragCoord.x * 0.13 + fragCoord.y * 0.07);
    float stepPx = exp2(float((iFrame * 2) % 5));

    // Init
    if (iFrame == 0)
    {
        int a = int(floor(float(PARTICLE_COUNT) * hash11(seed + 1.1)));
        int b = int(floor(float(PARTICLE_COUNT) * hash11(seed + 2.2)));
        if (b == a) b = (a + 1) % PARTICLE_COUNT;
        fragColor = vec4(float(a), float(b), 0.0, 1.0);
        return;
    }

    int best0 = int(c.x);
    int best1 = int(c.y);
    if (best0 < 0 || best0 >= PARTICLE_COUNT)
        best0 = int(floor(float(PARTICLE_COUNT) * seed));
    if (best1 < 0 || best1 >= PARTICLE_COUNT || best1 == best0)
        best1 = (best0 + 1 + int(seed * 7.0)) % PARTICLE_COUNT;

    float d0 = loopDist(p, readParticle(iChannel1, best0).xy);
    float d1 = loopDist(p, readParticle(iChannel1, best1).xy);

    // Neighbour + random candidate passes
    for (int pass = 0; pass < 5; pass++)
    {
        int cand = best0;
        if (pass < 4)
        {
            vec2 o = p;
            if (pass == 0) o += vec2(stepPx, 0.0);
            if (pass == 1) o += vec2(0.0, stepPx);
            if (pass == 2) o -= vec2(stepPx, 0.0);
            if (pass == 3) o -= vec2(0.0, stepPx);
            cand = int(texture(iChannel0, o / sstRes).x);
        }
        else
        {
            cand = int(floor(float(PARTICLE_COUNT) * hash11(seed + 3.3 + float(pass))));
        }
        if (cand < 0 || cand >= PARTICLE_COUNT) continue;

        float d = loopDist(p, readParticle(iChannel1, cand).xy);
        if (d < d0)
        {
            best1 = best0; d1 = d0;
            best0 = cand;  d0 = d;
        }
        else if (cand != best0 && d < d1)
        {
            best1 = cand; d1 = d;
        }

        // Also try neighbour's second site
        if (pass < 4)
        {
            vec2 o = p;
            if (pass == 0) o += vec2(stepPx, 0.0);
            if (pass == 1) o += vec2(0.0, stepPx);
            if (pass == 2) o -= vec2(stepPx, 0.0);
            if (pass == 3) o -= vec2(0.0, stepPx);
            int cand2 = int(texture(iChannel0, o / sstRes).y);
            if (cand2 >= 0 && cand2 < PARTICLE_COUNT && cand2 != best0)
            {
                float d2 = loopDist(p, readParticle(iChannel1, cand2).xy);
                if (d2 < d1) { best1 = cand2; d1 = d2; }
            }
        }
    }

    if (best1 == best0)
        best1 = (best0 + 1) % PARTICLE_COUNT;

    fragColor = vec4(float(best0), float(best1), 0.0, 1.0);
}
