// SST audio helpers — paste into Image tab (or keep as workbench reference).
// Shadertoy: set iChannel0 to Microphone or Audio.
// FFT sampling pattern (not a fork of any visualizer scene).
// #define AUDIO_FALLBACK 1  — keep motion when Channel0 is silent.

#ifndef FREQ_BINS
#define FREQ_BINS 16.0
#endif

#ifndef AUDIO_FALLBACK
#define AUDIO_FALLBACK 1
#endif

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
float sstLevel() { return (sstBass() + sstMid() + sstHigh()) / 3.0; }

// Effective band with optional fallback so demos still move without mic/track
float sstBand(float live, float fbAmp)
{
#if AUDIO_FALLBACK
    float fb = 0.08 + fbAmp * (0.5 + 0.5 * sin(iTime * (1.2 + fbAmp)));
    return max(live, fb);
#else
    return live;
#endif
}
