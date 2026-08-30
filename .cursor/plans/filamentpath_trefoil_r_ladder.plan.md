---
name: FilamentPath trefoil R-ladder
overview: Concentric 8× Trefoil kit (paste R/r character, nested like the braid-rings image), FilamentPath refactor, per-path audio (bass stretch, slight hue, mono→wide), plus optional twisted-ladder kinds.
todos:
  - id: filament-struct
    content: Introduce FilamentPath + PATHS[] (or pathAt) in Common; remove PATH*_ macro spam
    status: pending
  - id: concentric-kit
    content: "Default from paste: all Trefoil; off=0; R nested TREFOIL_R0*(1..8); keep paste rr character; fit canvas"
    status: pending
  - id: audio-per-path
    content: "Buffer B/Image: bass radial stretch; slight hue; path0 mono / high paths stereo-wide"
    status: pending
  - id: ladder-glsl
    content: Add KIND_L41..L112 + twistedLadderPath2D; wire filamentPath geom=2
    status: pending
  - id: catalog-tests
    content: Mirror kit + audio helpers in sst_knot_catalog.py + pytest
    status: pending
  - id: readme-kit-h
    content: Document concentric Trefoil kit + audio UX; restate no IQ 4_1 GLSL
    status: pending
isProject: true
---

# Concentric Trefoils + per-path audio

## Locked decisions

### 1. Kit = paste kinds/R-character, layout = image (concentric)

- All 8 paths `KIND_TREFOIL` (as in your paste).
- **Layout like the image:** all `off = (0,0)`, `scale = 1.0` — nested around one centre, clear gaps between rings.
- **Nest radii:** `R[i] = TREFOIL_R0 * float(i + 1)` for `i = 0..7`, with `TREFOIL_R0` chosen so `(R_max + rr_max) * BASE_SCALE ≲ 0.45`.
- **Tube character from paste:** keep your `rr` sequence `(0.42, 0.42, 0.38, 0.0, 0.40, 0.40, 0.36, 0.0)`, scaled by a single `TREFOIL_r_SCALE` (~0.25–0.35) so inner rings stay thinner / readable like the reference.
- Drop the paste’s spread `OFFX/OFFY/SCALE` (those fight the concentric look).

### 2. Audio / EQ per path

| Effect | Behaviour |
|--------|-----------|
| **Bass → vortex stretch** | After `filamentPath`, radial stretch about canvas centre: `tar = centre + (tar - centre) * (1.0 + STRETCH_BASS * bass)`. Same stretch factor for all paths (global bass pulse). |
| **Hue** | In Image `pathColor`: small shift `h += HUE_AUDIO * (0.5*mid + 0.5*pathBand)` (`HUE_AUDIO` ~0.03–0.06). |
| **Mono path 0 / wide high paths** | `width = float(pathId) / float(NUM_PATHS - 1)` → 0 on path 0, 1 on path 7. Path 0: attract to single `tar` (mono). Higher paths: `stereo = sstAudioSmooth(AUDIO_WIDE_L) - sstAudioSmooth(AUDIO_WIDE_R)`; `tar.x += width * STEREO_AMP * stereo * sstRes.y`. High paths also weight `pathBand` toward high freqs for phase speed / attract. |

New Common knobs: `STRETCH_BASS`, `HUE_AUDIO`, `STEREO_AMP`, `AUDIO_WIDE_L`, `AUDIO_WIDE_R` (e.g. 0.15 / 0.85).

### 3. Still in scope

- `struct FilamentPath` + `PATHS[]` / `pathAt()`; remove `PATH*_` spam.
- Ladder kinds `KIND_L41`…`KIND_L112` + original `twistedLadderPath2D` (lab Lissajous — **not** IQ 4₁).
- Python mirror + pytest; README kit H note.

## Files

- [sst_voronoi_filaments_common.glsl](GUI/vortexring-lab/shaders/sst_voronoi_filaments_common.glsl)
- [sst_voronoi_filaments_bufferB.glsl](GUI/vortexring-lab/shaders/sst_voronoi_filaments_bufferB.glsl)
- [sst_voronoi_filaments_image.glsl](GUI/vortexring-lab/shaders/sst_voronoi_filaments_image.glsl)
- [sst_knot_catalog.py](GUI/vortexring-lab/shaders/sst_knot_catalog.py) + tests
- [shaders/README.md](GUI/vortexring-lab/shaders/README.md)

## Verify

```bash
cd GUI/vortexring-lab/shaders && python -m pytest test_sst_knot_catalog.py -v
```
