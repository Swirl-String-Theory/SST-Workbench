// SST Voronoi filaments — IMAGE tab
// Soft field from nearest particle; RGB strand tubes for MODE_STRANDS paths.
// Channels: iChannel0 = Buffer A, iChannel1 = Buffer B, iChannel2 = Audio (optional)
// UX knobs live in Common + live Buffer B UI. Audio helpers are local (need iChannel2 + iTime).

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

vec3 pathColor(int pathId, float phase, float mid, float pBand, float hueAud, sampler2D ui)
{
    vec3 base = pathAtUi(ui, pathId).particle.color;
    float h = fract(phase * 0.5 + iTime * 0.05);
    vec3 mate = mix(base, base * 1.15, 0.25 + 0.25 * sin(h * TAU));
    float dh = hueAud * (0.5 * mid + 0.5 * pBand);
    return shiftHue(mate, dh);
}

float ringBand(float d, float width)
{
    float h = max(width, 0.5) * 0.5;
    return smoothstep(h + 1.5, h, d);
}

// Closest t on a filament (STRAND_SAMPLES samples) + distance in pixels.
void nearestOnPath(vec2 px, int pathId, sampler2D ui, out float tBest, out float dBest)
{
    dBest = 1e9;
    tBest = 0.0;
    for (int i = 0; i < STRAND_SAMPLES; i++)
    {
        float t = float(i) / float(STRAND_SAMPLES);
        float d = loopDist(px, filamentPath(t, pathId, ui));
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

// 5x7 bitmap: ch 0-9 digits, 10-35 A-Z, 36 space, 37 -, 38 ., 39 <, 40 >, 41 /
int uiGlyphCol(int ch, int col)
{
    int a = 0, b = 0, c = 0, d = 0, e = 0;
    if (ch == 0) { a = 62; b = 65; c = 65; d = 65; e = 62; }
    else if (ch == 1) { a = 0; b = 66; c = 127; d = 64; e = 0; }
    else if (ch == 2) { a = 98; b = 81; c = 73; d = 73; e = 70; }
    else if (ch == 3) { a = 34; b = 73; c = 73; d = 73; e = 54; }
    else if (ch == 4) { a = 24; b = 20; c = 18; d = 127; e = 16; }
    else if (ch == 5) { a = 39; b = 69; c = 69; d = 69; e = 57; }
    else if (ch == 6) { a = 62; b = 73; c = 73; d = 73; e = 48; }
    else if (ch == 7) { a = 1; b = 113; c = 9; d = 5; e = 3; }
    else if (ch == 8) { a = 54; b = 73; c = 73; d = 73; e = 54; }
    else if (ch == 9) { a = 6; b = 73; c = 73; d = 73; e = 62; }
    else if (ch == 10) { a = 126; b = 17; c = 17; d = 17; e = 126; } // A
    else if (ch == 11) { a = 127; b = 73; c = 73; d = 73; e = 54; }
    else if (ch == 12) { a = 62; b = 65; c = 65; d = 65; e = 34; }
    else if (ch == 13) { a = 127; b = 65; c = 65; d = 34; e = 28; }
    else if (ch == 14) { a = 127; b = 73; c = 73; d = 73; e = 65; }
    else if (ch == 15) { a = 127; b = 9; c = 9; d = 9; e = 1; }
    else if (ch == 16) { a = 62; b = 65; c = 73; d = 73; e = 58; }
    else if (ch == 17) { a = 127; b = 8; c = 8; d = 8; e = 127; }
    else if (ch == 18) { a = 0; b = 65; c = 127; d = 65; e = 0; }
    else if (ch == 19) { a = 32; b = 64; c = 65; d = 63; e = 1; }
    else if (ch == 20) { a = 127; b = 8; c = 20; d = 34; e = 65; }
    else if (ch == 21) { a = 127; b = 64; c = 64; d = 64; e = 64; }
    else if (ch == 22) { a = 127; b = 2; c = 12; d = 2; e = 127; }
    else if (ch == 23) { a = 127; b = 4; c = 8; d = 16; e = 127; }
    else if (ch == 24) { a = 62; b = 65; c = 65; d = 65; e = 62; }
    else if (ch == 25) { a = 127; b = 9; c = 9; d = 9; e = 6; }
    else if (ch == 26) { a = 62; b = 65; c = 81; d = 33; e = 94; }
    else if (ch == 27) { a = 127; b = 9; c = 25; d = 41; e = 70; }
    else if (ch == 28) { a = 38; b = 73; c = 73; d = 73; e = 50; }
    else if (ch == 29) { a = 1; b = 1; c = 127; d = 1; e = 1; }
    else if (ch == 30) { a = 63; b = 64; c = 64; d = 64; e = 63; }
    else if (ch == 31) { a = 15; b = 48; c = 64; d = 48; e = 15; }
    else if (ch == 32) { a = 127; b = 32; c = 24; d = 32; e = 127; }
    else if (ch == 33) { a = 99; b = 20; c = 8; d = 20; e = 99; }
    else if (ch == 34) { a = 7; b = 8; c = 112; d = 8; e = 7; }
    else if (ch == 35) { a = 97; b = 81; c = 73; d = 69; e = 67; } // Z
    else if (ch == 37) { a = 8; b = 8; c = 8; d = 8; e = 8; }
    else if (ch == 38) { a = 0; b = 96; c = 96; d = 0; e = 0; }
    else if (ch == 39) { a = 8; b = 20; c = 34; d = 65; e = 0; }
    else if (ch == 40) { a = 0; b = 65; c = 34; d = 20; e = 8; }
    else if (ch == 41) { a = 64; b = 32; c = 16; d = 8; e = 4; }
    int g = a;
    if (col == 1) g = b;
    if (col == 2) g = c;
    if (col == 3) g = d;
    if (col == 4) g = e;
    return g;
}

float uiChar(vec2 px, vec2 loc, int ch, float sc)
{
    vec2 a = uiToScreen(loc);
    vec2 b = uiToScreen(loc + vec2(6.0, 8.0) * sc);
    vec2 mn = min(a, b), mx = max(a, b);
    if (px.x < mn.x || px.x >= mx.x || px.y < mn.y || px.y >= mx.y)
        return 0.0;
    vec2 t = (px - mn) / max(mx - mn, vec2(1e-4));
    t.y = 1.0 - t.y;
    int cx = int(floor(t.x * 6.0));
    int cy = int(floor(t.y * 8.0));
    if (cx < 0 || cx > 4 || cy < 0 || cy > 6)
        return 0.0;
    int bits = uiGlyphCol(ch, cx);
    float p = pow(2.0, float(cy));
    return (mod(floor(float(bits) / p), 2.0) > 0.5) ? 1.0 : 0.0;
}

float uiText5(vec2 px, vec2 loc, float sc, int c0, int c1, int c2, int c3, int c4)
{
    float m = 0.0;
    if (c0 >= 0) m = max(m, uiChar(px, loc, c0, sc));
    if (c1 >= 0) m = max(m, uiChar(px, loc + vec2(6.0 * sc, 0.0), c1, sc));
    if (c2 >= 0) m = max(m, uiChar(px, loc + vec2(12.0 * sc, 0.0), c2, sc));
    if (c3 >= 0) m = max(m, uiChar(px, loc + vec2(18.0 * sc, 0.0), c3, sc));
    if (c4 >= 0) m = max(m, uiChar(px, loc + vec2(24.0 * sc, 0.0), c4, sc));
    return m;
}

float uiWord(vec2 px, vec2 loc, int w)
{
    float lg = UI_FONT_LG;
    float md = UI_FONT_MD;
    if (w == 0) return uiText5(px, loc, lg, 28, 28, 29, -1, -1); // SST
    if (w == 1) return uiText5(px, loc, lg, 22, 14, 23, 30, -1); // MENU
    if (w == 2) return uiText5(px, loc, lg, 22, 24, 29, -1, -1); // MOT
    if (w == 3) return uiText5(px, loc, lg, 21, 24, 24, 20, -1); // LOOK
    if (w == 4) return uiText5(px, loc, lg, 25, 10, 29, 17, -1); // PATH
    if (w == 5) return uiText5(px, loc, md, 28, 12, 21, -1, -1); // SCL
    if (w == 6) return uiText5(px, loc, md, 28, 25, 13, -1, -1); // SPD
    if (w == 7) return uiText5(px, loc, md, 10, 29, 29, -1, -1); // ATT
    if (w == 8) return uiText5(px, loc, md, 27, 14, 25, -1, -1); // REP
    if (w == 9) return uiText5(px, loc, md, 28, 29, 27, -1, -1); // STR
    if (w == 10) return uiText5(px, loc, md, 28, 29, 14, -1, -1); // STE
    if (w == 11) return uiText5(px, loc, md, 16, 21, 32, -1, -1); // GLW
    if (w == 12) return uiText5(px, loc, md, 13, 24, 29, -1, -1); // DOT
    if (w == 13) return uiText5(px, loc, md, 16, 10, 22, -1, -1); // GAM
    if (w == 14) return uiText5(px, loc, md, 32, 18, 13, -1, -1); // WID
    if (w == 15) return uiText5(px, loc, md, 17, 30, 14, -1, -1); // HUE
    if (w == 16) return uiText5(px, loc, md, 10, 30, 13, -1, -1); // AUD
    if (w == 17) return uiText5(px, loc, md, 24, 23, -1, -1, -1); // ON
    if (w == 18) return uiText5(px, loc, md, 24, 15, 15, -1, -1); // OFF
    if (w == 19) return uiText5(px, loc, md, 25, 10, 27, 29, -1); // PART
    if (w == 20) return uiText5(px, loc, md, 28, 29, 27, 23, -1); // STRN
    if (w == 21) return uiText5(px, loc, md, 27, 28, 29, -1, -1); // RST
    if (w == 22) return uiText5(px, loc, md, 28, 18, 35, 14, -1); // SIZE
    if (w == 23) return uiText5(px, loc, md, 14, 33, 25, -1, -1); // EXP
    if (w == 24) return uiText5(px, loc, md, 25, 10, 16, 14, -1); // PAGE
    if (w == 25) return uiText5(px, loc, md, 25, 27, 14, 28, -1); // PRES
    if (w == 26) return uiText5(px, loc, md, 14, 29, -1, -1, -1); // ET
    if (w == 27) return uiText5(px, loc, md, 31, 18, 16, -1, -1); // VIG
    return 0.0;
}

float uiFill(vec2 px, vec2 loc, vec2 sz)
{
    return uiInBox(px, loc, sz) ? 1.0 : 0.0;
}

float uiDigits(vec2 px, vec2 loc, float v)
{
    float av = abs(v);
    int whole = int(floor(av + 1e-4));
    int frac1 = int(floor(fract(av) * 10.0 + 1e-4));
    int frac2 = int(floor(fract(av * 10.0) * 10.0 + 1e-4));
    whole = clamp(whole, 0, 99);
    frac1 = clamp(frac1, 0, 9);
    frac2 = clamp(frac2, 0, 9);
    float sc = UI_FONT_SM;
    float m = 0.0;
    if (whole >= 10)
    {
        m = uiChar(px, loc, whole / 10, sc);
        m = max(m, uiChar(px, loc + vec2(4.0, 0.0), whole - (whole / 10) * 10, sc));
        m = max(m, uiChar(px, loc + vec2(7.6, 0.0), 38, sc));
        m = max(m, uiChar(px, loc + vec2(10.2, 0.0), frac1, sc));
    }
    else
    {
        m = uiChar(px, loc, whole, sc);
        m = max(m, uiChar(px, loc + vec2(4.0, 0.0), 38, sc));
        m = max(m, uiChar(px, loc + vec2(6.8, 0.0), frac1, sc));
        m = max(m, uiChar(px, loc + vec2(10.4, 0.0), frac2, sc));
    }
    return m;
}

void uiDrawSlider(vec2 px, float y, float t, vec3 accent, inout vec3 col, inout float a)
{
    float track = uiFill(px, vec2(UI_TRACK_X, y + UI_TRACK_Y), vec2(UI_TRACK_W, UI_TRACK_H));
    col = mix(col, vec3(0.18, 0.20, 0.24), track);
    a = max(a, track);
    float knx = UI_TRACK_X + (UI_TRACK_W - 10.0) * clamp(t, 0.0, 1.0);
    float kn = uiFill(px, vec2(knx, y + UI_TRACK_Y - 3.0), vec2(10.0, UI_TRACK_H + 6.0));
    col = mix(col, accent, kn);
    a = max(a, kn);
}

void uiDrawExpLine(vec2 px, float y, int labelWord, float v, inout vec3 col)
{
    col = mix(col, vec3(0.70, 0.78, 0.88), uiWord(px, vec2(8.0, y + 4.0), labelWord));
    col = mix(col, vec3(0.95, 0.92, 0.55), uiDigits(px, vec2(90.0, y + 4.0), v));
}

vec3 uiOverlay(vec2 px, vec3 src, sampler2D ui)
{
    vec4 head = uiLoad(ui, UI_SLOT_HEAD);
    vec4 meta = uiLoad(ui, UI_SLOT_META);
    int open = int(head.x + 0.5);
    int tab = int(meta.x + 0.5);
    int expOn = int(meta.y + 0.5);
    int expPage = int(clamp(meta.z, 0.0, float(UI_EXP_PAGES - 1)) + 0.5);
    int sel = int(clamp(head.w, 0.0, float(NUM_PATHS - 1)) + 0.5);
    if (!uiInPanel(px, open, expOn))
        return src;

    float pw = uiPanelW(expOn);
    vec3 col = vec3(0.07, 0.08, 0.10);
    float a = uiFill(px, vec2(0.0), vec2(pw, uiPanelH(open, expOn)));
    col = mix(col, vec3(0.12, 0.16, 0.22), uiFill(px, vec2(0.0), vec2(pw, UI_HDR_H)));
    float txt = max(uiWord(px, vec2(8.0, 8.0), 0), uiWord(px, vec2(48.0, 8.0), 1));
    col = mix(col, vec3(0.75, 0.85, 1.0), txt);
    // EXP button
    col = mix(col, mix(vec3(0.20), vec3(0.35, 0.45, 0.20), expOn > 0 ? 1.0 : 0.0), uiFill(px, vec2(pw - 78.0, 4.0), vec2(50.0, 26.0)));
    col = mix(col, vec3(0.95), uiWord(px, vec2(pw - 70.0, 8.0), 23));
    float chev = uiChar(px, vec2(pw - 22.0, 8.0), open > 0 ? 37 : 40, UI_FONT_LG);
    col = mix(col, vec3(0.9), chev);

    if (open > 0)
    {
        float y0 = UI_HDR_H + UI_TAB_H;
        vec3 ac = vec3(0.35, 0.70, 0.95);
        if (expOn > 0)
        {
            col = mix(col, vec3(0.16, 0.18, 0.14), uiFill(px, vec2(0.0, UI_HDR_H), vec2(pw, UI_TAB_H)));
            col = mix(col, vec3(0.90, 0.85, 0.45), uiWord(px, vec2(8.0, UI_HDR_H + 6.0), 25));
            col = mix(col, vec3(0.90, 0.85, 0.45), uiWord(px, vec2(48.0, UI_HDR_H + 6.0), 26));
            col = mix(col, vec3(0.22), uiFill(px, vec2(8.0, y0 + 3.0), vec2(28.0, 18.0)));
            col = mix(col, vec3(0.90), uiChar(px, vec2(14.0, y0 + 5.0), 39, UI_FONT_MD));
            col = mix(col, vec3(0.22), uiFill(px, vec2(pw - 36.0, y0 + 3.0), vec2(28.0, 18.0)));
            col = mix(col, vec3(0.90), uiChar(px, vec2(pw - 30.0, y0 + 5.0), 40, UI_FONT_MD));
            col = mix(col, vec3(0.80), uiWord(px, vec2(120.0, y0 + 5.0), 24));
            col = mix(col, vec3(0.95), uiChar(px, vec2(170.0, y0 + 5.0), expPage, UI_FONT_LG));

            float yBase = y0 + UI_ROW_H;
            if (expPage == 0)
            {
                // Live slider values → paste as PRESET_SL_* in Common
                for (int i = 0; i < 13; i++)
                {
                    if (i >= int(UI_EXP_ROWS) - 1) break;
                    float y = yBase + float(i) * UI_ROW_H;
                    int sl = i;
                    int lw = 5;
                    if (sl == SL_SCALE) lw = 5;
                    else if (sl == SL_SPEED) lw = 6;
                    else if (sl == SL_ATTRACT) lw = 7;
                    else if (sl == SL_REPEL) lw = 8;
                    else if (sl == SL_STRETCH) lw = 9;
                    else if (sl == SL_STEREO) lw = 10;
                    else if (sl == SL_GLOW) lw = 11;
                    else if (sl == SL_VIGNETTE) lw = 27;
                    else if (sl == SL_GAMMA) lw = 13;
                    else if (sl == SL_STRAND) lw = 14;
                    else if (sl == SL_HUEAUD) lw = 15;
                    else if (sl == SL_AUDIOFB) lw = 16;
                    else lw = 12; // DISCS / DOT
                    uiDrawExpLine(px, y, lw, uiLive(ui, sl), col);
                }
            }
            else
            {
                // Paths page 1 → P0..P3, page 2 → P4..P7
                int base = (expPage == 1) ? 0 : 4;
                for (int pi = 0; pi < 4; pi++)
                {
                    int pathId = base + pi;
                    float y = yBase + float(pi) * UI_ROW_H * 2.5;
                    col = mix(col, vec3(0.85), uiChar(px, vec2(8.0, y + 4.0), 25, UI_FONT_MD)); // P
                    col = mix(col, vec3(0.85), uiChar(px, vec2(20.0, y + 4.0), pathId, UI_FONT_MD));
                    col = mix(col, vec3(0.75), uiDigits(px, vec2(50.0, y + 4.0), uiPathRaw(ui, pathId, PF_SIZE)));
                    col = mix(col, vec3(0.75), uiDigits(px, vec2(120.0, y + 4.0), uiPathRaw(ui, pathId, PF_SPEED)));
                    col = mix(col, vec3(0.75), uiDigits(px, vec2(190.0, y + 4.0), uiPathRaw(ui, pathId, PF_HUE)));
                    col = mix(col, vec3(0.75), uiDigits(px, vec2(260.0, y + 4.0), uiPathRaw(ui, pathId, PF_MODE)));
                    col = mix(col, vec3(0.45), uiWord(px, vec2(50.0, y + UI_ROW_H), 22));
                    col = mix(col, vec3(0.45), uiWord(px, vec2(120.0, y + UI_ROW_H), 6));
                    col = mix(col, vec3(0.45), uiWord(px, vec2(190.0, y + UI_ROW_H), 15));
                    col = mix(col, vec3(0.45), uiWord(px, vec2(260.0, y + UI_ROW_H), 19));
                }
            }
        }
        else
        {
        float tw = UI_PANEL_W / 3.0;
        for (int t = 0; t < 3; t++)
        {
            vec2 loc = vec2(float(t) * tw, UI_HDR_H);
            float on = (tab == t) ? 1.0 : 0.0;
            col = mix(col, mix(vec3(0.10), vec3(0.20, 0.28, 0.36), on), uiFill(px, loc, vec2(tw - 1.0, UI_TAB_H)));
            col = mix(col, vec3(0.85), uiWord(px, loc + vec2(10.0, 6.0), 2 + t));
        }
        if (tab == UI_TAB_MOTION)
        {
            for (int row = 0; row < 6; row++)
            {
                int sl = uiMotionSlider(row);
                float y = y0 + float(row) * UI_ROW_H;
                col = mix(col, vec3(0.80), uiWord(px, vec2(8.0, y + 5.0), 5 + row));
                float t01 = (uiLive(ui, sl) - uiSliderMin(sl)) / max(uiSliderMax(sl) - uiSliderMin(sl), 1e-4);
                uiDrawSlider(px, y, t01, ac, col, a);
                col = mix(col, vec3(0.75), uiDigits(px, vec2(UI_DIGIT_X, y + 5.0), uiLive(ui, sl)));
            }
        }
        else if (tab == UI_TAB_LOOK)
        {
            for (int row = 0; row < 5; row++)
            {
                int sl = uiLookSlider(row);
                float y = y0 + float(row) * UI_ROW_H;
                col = mix(col, vec3(0.80), uiWord(px, vec2(8.0, y + 5.0), 11 + row));
                float t01 = (uiLive(ui, sl) - uiSliderMin(sl)) / max(uiSliderMax(sl) - uiSliderMin(sl), 1e-4);
                uiDrawSlider(px, y, t01, ac, col, a);
                col = mix(col, vec3(0.75), uiDigits(px, vec2(UI_DIGIT_X, y + 5.0), uiLive(ui, sl)));
            }
            float y = y0 + 5.0 * UI_ROW_H;
            col = mix(col, vec3(0.80), uiWord(px, vec2(8.0, y + 5.0), 16));
            float on = uiLive(ui, SL_AUDIOFB);
            col = mix(col, mix(vec3(0.25), vec3(0.15, 0.45, 0.28), on), uiFill(px, vec2(UI_TRACK_X, y + 3.0), vec2(96.0, 18.0)));
            col = mix(col, vec3(0.95), uiWord(px, vec2(UI_TRACK_X + 18.0, y + 5.0), on > 0.5 ? 17 : 18));
        }
        else
        {
            float y = y0;
            col = mix(col, vec3(0.80), uiWord(px, vec2(8.0, y + 5.0), 4));
            col = mix(col, vec3(0.22), uiFill(px, vec2(UI_TRACK_X, y + 3.0), vec2(28.0, 18.0)));
            col = mix(col, vec3(0.90), uiChar(px, vec2(UI_TRACK_X + 6.0, y + 5.0), 39, UI_FONT_MD));
            col = mix(col, vec3(0.22), uiFill(px, vec2(210.0, y + 3.0), vec2(28.0, 18.0)));
            col = mix(col, vec3(0.90), uiChar(px, vec2(216.0, y + 5.0), 40, UI_FONT_MD));
            col = mix(col, vec3(0.85), uiChar(px, vec2(148.0, y + 5.0), sel, UI_FONT_LG));

            y = y0 + UI_ROW_H;
            col = mix(col, vec3(0.80), uiWord(px, vec2(8.0, y + 5.0), 6));
            float modeS = uiPathRaw(ui, sel, PF_MODE);
            col = mix(col, mix(vec3(0.30, 0.45, 0.70), vec3(0.16), modeS < 0.5 ? 0.0 : 1.0), uiFill(px, vec2(UI_TRACK_X, y + 3.0), vec2(62.0, 18.0)));
            col = mix(col, vec3(0.95), uiWord(px, vec2(UI_TRACK_X + 6.0, y + 5.0), 19));
            col = mix(col, mix(vec3(0.16), vec3(0.30, 0.55, 0.40), modeS > 0.5 ? 1.0 : 0.0), uiFill(px, vec2(158.0, y + 3.0), vec2(72.0, 18.0)));
            col = mix(col, vec3(0.95), uiWord(px, vec2(164.0, y + 5.0), 20));

            for (int field = 0; field < 3; field++)
            {
                y = y0 + float(2 + field) * UI_ROW_H;
                int ww = 22;
                if (field == 1) ww = 6;
                if (field == 2) ww = 15;
                col = mix(col, vec3(0.80), uiWord(px, vec2(8.0, y + 5.0), ww));
                float v = uiPathRaw(ui, sel, field);
                float t01 = (v - uiPathFieldMin(field)) / max(uiPathFieldMax(field) - uiPathFieldMin(field), 1e-4);
                vec3 accent = ac;
                if (field == 2) accent = hsvRgb(v, 0.8, 0.95);
                uiDrawSlider(px, y, t01, accent, col, a);
                col = mix(col, vec3(0.75), uiDigits(px, vec2(UI_DIGIT_X, y + 5.0), v));
            }
            y = y0 + 5.0 * UI_ROW_H;
            col = mix(col, vec3(0.40, 0.18, 0.16), uiFill(px, vec2(UI_TRACK_X, y + 3.0), vec2(96.0, 18.0)));
            col = mix(col, vec3(0.95), uiWord(px, vec2(UI_TRACK_X + 18.0, y + 5.0), 21));
        }
        } // end !expOn
    }

    return mix(src, col, clamp(a * 0.94, 0.0, 0.94));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    sstRes = iResolution.xy;
    float useFb = uiLive(iChannel1, SL_AUDIOFB);
    float bass, mid, high;
    sstBands(bass, mid, high, useFb);

    vec3 col = BG_COL;

    int id0 = int(texture(iChannel0, fragCoord / sstRes).x);
    if (id0 < 0 || id0 >= PARTICLE_COUNT) id0 = 0;
    vec4 h0 = readParticle(iChannel1, id0);

    int pathId = pathOfParticle(id0);
    FilamentPath fp0 = pathAtUi(iChannel1, pathId);
    float pBand = pathBand(pathId, useFb);
    float glowBase = uiLive(iChannel1, SL_GLOW);
    float vig = uiLive(iChannel1, SL_VIGNETTE);
    float gam = uiLive(iChannel1, SL_GAMMA);
    float hueAud = uiLive(iChannel1, SL_HUEAUD);
    float discs = clamp(uiLive(iChannel1, SL_DISCS), 0.0, 1.0);

    if (fp0.mode == MODE_PARTICLES)
    {
        float dist = max(loopDist(fragCoord, h0.xy), 0.5);
        // Finite glow radius — beyond this the pixel stays BG_COL (no 1/r wash).
        float rMax = max(48.0, 90.0 * max(fp0.particle.size, 0.05) + 0.35 * glowBase);
        if (dist <= rMax)
        {
            float distEff = dist / max(fp0.particle.size, 0.05);
            float glow = (glowBase + GLOW_BASS * bass) / distEff;
            glow = clamp(glow, 0.0, GLOW_MAX);
            float win = smoothstep(rMax, rMax * 0.35, dist);
            glow *= win;

            float ph = phaseOfParticle(id0);
            vec3 mate = pathColor(pathId, ph, mid, pBand, hueAud, iChannel1);

            int id1 = int(texture(iChannel0, fragCoord / sstRes).y);
            if (id1 >= 0 && id1 < PARTICLE_COUNT)
            {
                float d1 = max(loopDist(fragCoord, readParticle(iChannel1, id1).xy), 0.5);
                float edge = smoothstep(0.0, EDGE_BASE + EDGE_HIGH * high, abs(dist - d1));
                mate *= EDGE_MIX_LO + EDGE_MIX_HI * edge;
            }

            // DOT fades body and high — 0 = no particle field (strands only).
            vec3 body = mate * glow * (COL_MID + COL_MID_AUDIO * mix(mid, pBand, 0.4));
            vec3 hi = mate * pow(glow * COL_HIGH_POW, 2.0) * (COL_HIGH_BASE + COL_HIGH_AUDIO * high);
            col += (body + hi) * discs;
        }
    }

    for (int i = 0; i < NUM_PATHS; i++)
    {
        FilamentPath fp = pathAtUi(iChannel1, i);
        if (fp.mode != MODE_STRANDS)
            continue;
        float tBest, dBest;
        nearestOnPath(fragCoord, i, iChannel1, tBest, dBest);
        float widthPx = max(fp.strandWidth, 0.002) * max(fp.particle.size, 0.05) * sstRes.y;
        float pathPh = readParticle(iChannel1, pathPhaseIndex(i)).x;
        col += rgbStrandColor(tBest, dBest, widthPx, pathBand(i, useFb), fp.particle.color, pathPh);
    }

    vec2 uv = (fragCoord - 0.5 * sstRes) / sstRes.y;
    col *= 1.0 - vig * dot(uv, uv);
    col = pow(max(col, 0.0), vec3(gam));
    col = uiOverlay(fragCoord, col, iChannel1);
    fragColor = vec4(col, 1.0);
}
