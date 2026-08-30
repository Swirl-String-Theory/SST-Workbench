# SST Shadertoy shaders (vortexring-lab)

**Label:** `[BRIDGE]` visualisation — not a numerical certificate, not SSTcore.

Workbench archive of **original** GLSL Image-tab shaders you paste back onto [shadertoy.com](https://www.shadertoy.com/). We do not publish for you.

| File | Role |
|------|------|
| [`sst_torus_knot_swirl.glsl`](sst_torus_knot_swirl.glsl) | **3D** T(p,q) vortex tube + twist stripes + audio |
| [`sst_log_spiral_swirl.glsl`](sst_log_spiral_swirl.glsl) | **2D** log-spiral companion + audio |
| [`sst_closed_braid.glsl`](sst_closed_braid.glsl) | **3D** closed 3-strand braid + audio |
| [`sst_domain_twist_ring.glsl`](sst_domain_twist_ring.glsl) | **3D** domain-deform twist ring + audio |
| [`sst_trefoil_ribbon.glsl`](sst_trefoil_ribbon.glsl) | **3D** T(2,3) Frenet ribbon + audio |
| [`sst_swirl_clock_beads.glsl`](sst_swirl_clock_beads.glsl) | **3D** linear+radial swirl-clock beads + audio |
| [`sst_phi_log_spiral.glsl`](sst_phi_log_spiral.glsl) | **2D** φ log-polar fractal + audio |
| [`sst_voronoi_filaments_*.glsl`](sst_voronoi_filaments_common.glsl) | **Multi-pass** Voronoi particles on multi knot/link paths + audio |
| [`sst_nested_braid_tree.glsl`](sst_nested_braid_tree.glsl) | **3D** nested 3×3×3 braid tree fly-through + audio |
| [`sst_audio.inc.glsl`](sst_audio.inc.glsl) | Shared FFT helpers (also inlined in each Image tab) |
| [`sst_knot_catalog.py`](sst_knot_catalog.py) | Shared geometry helpers |
| [`test_sst_knot_catalog.py`](test_sst_knot_catalog.py) | pytest |

```bash
cd GUI/vortexring-lab/shaders
python -m pytest test_sst_knot_catalog.py -v
```

## Pairing

Same SST look (cyan→magenta). Tube, spiral, domain-twist, and φ-spiral share the coprime `(p,q)` catalogue (~2s dwell). Closed braid / trefoil ribbon stay **T(2,3)** with chirality flip. Beads = **24** swirl-clock ticks. Nested braid tree = **27** (3×3×3) leaves. Image-tab kits react to **iChannel0** audio (Voronoi uses iChannel2).

## Audio (all kits)

1. In Shadertoy, set **Channel 0** to **Microphone** or **Audio** (mp3).
2. FFT is read at `texture(iChannel0, vec2(freq, 0.25)).x` (same idea as typical Shadertoy audio visualizers; not a fork of any halo/line scene).
3. With no signal, `AUDIO_FALLBACK` keeps a gentle sine so the shader still moves.
4. Mapping:

| Band | Tube | Spiral | Braid | Domain-twist | Ribbon | Beads | Phi-spiral | Nested-braid |
|------|------|--------|-------|--------------|--------|-------|------------|--------------|
| Bass | core radius + glow | zoom + tick brightness | strand radius | tube radius + glow | ribbon width/thickness | bead radius | curve thickness / bright | leaf radius |
| Mid | twist intensity | spin rate | camera/phase spin | object rotation | twist amplitude | spin | rotation speed | nest spin |
| High | phase scroll speed | arm contrast | emissive pulse | lobe contrast / phase | specular | emissive | layer contrast | leaf highlight |

Reference helpers: [`sst_audio.inc.glsl`](sst_audio.inc.glsl) (already inlined in each `.glsl`).


## SST mapping

| Layer | SST reading |
|-------|-------------|
| Isotropic `T(p,q)` centreline (3D) | Torus-filament family; **T(2,3) = Rolfsen 3₁** |
| Tube `CORE_R` | Vortex-core thickness ε |
| Phase colour | Swirl-clock / closed-loop phase |
| Twist stripes (3D) | Core torsion along the loop (visual only) |
| Log-spiral arms `h=(p,q)` (2D) | Poloidal/toroidal winding cue in the plane |
| Arm ticks (2D) | Discrete swirl-clock bins |
| Soft ring (2D) | Unknot / R≈const reference |
| Closed 3-strand braid (3D) | Braid-index visualisation for 3₁; `side=±1` chirality |
| Domain-twist ring (3D) | Double polar unwrap + shear + mod lobes; `(p,q)` windings |
| Trefoil ribbon (3D) | T(2,3) Frenet ribbon; twist in N/B; chirality ~2s |
| Swirl-clock beads (3D) | 24 linear + radial beads = discrete clock ticks |
| Phi log-spiral (2D) | φ-fractal log-polar layers; scale from `|p|`, chirality `sign(q)` |
| Voronoi filaments (multi-pass) | 8 concentric Trefoils; per-path particles vs RGB strands; FilamentPath sizes |
| Nested braid tree (3D) | 3×3×3 hierarchical curve_transform; 27 leaves; chirality ~2s |
| `q → −q` / braid `side` / shear sign | Chirality flip |

**3₁ vs 4₁:** torus family only. Canon hyperbolic **4₁** is out of scope. IQ’s figure-8 Shadertoy (2021) is all-rights-reserved — **link only, never copy or alter**.

## Licences

- **These GLSL / Python files:** original SST workbench code. On Shadertoy, use a licence you own (CC BY-NC-SA is fine).
- **IQ figure-8 (2021):** do not fork, paste, or host altered.
- **Twisted-ladder / compact log-spiral / portal-braid / domain-deform / ribbon / bead / φ-golf / nested-braid shaders:** idea only. No code paste; original rewrite.

---

## Publish kit A — 3D tube

1. New blank shader — **not** a fork.
2. Paste [`sst_torus_knot_swirl.glsl`](sst_torus_knot_swirl.glsl) into Image.
3. **Channel 0 → Microphone or Audio.** No Common/Buffer needed. `#define SEGMENTS 64` (try `80` on fast GPUs).

**Title**

```text
SST T(p,q) swirl-clock
```

**Tags**

```text
knot, torus, raymarching, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Closed vortex filament as an isotropic torus knot T(p,q).
Default family starts at T(2,3) = trefoil (Rolfsen 3₁).
The cycle walks coprime (p,q), then chirality flips q → −q.

• Tube = polyline capsules along the centreline (vortex core).
• Colour = phase along the loop (swirl-clock).
• Twisted cross-section stripes = core torsion along a closed loop
  (inspired by closed-loop torsion / twisted-ladder domain deformation;
  original code, not a fork).

Companion: 2D log-spiral swirl-plane with the same (p,q) cycle.

No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse: orbit. Auto: slow camera + ~2s knot dwell.
Channel 0: mic/audio drives core pulse, twist, phase speed.
```

---

## Publish kit B — 2D log-spiral

1. New blank shader — **not** a fork of golf/log-spiral shaders.
2. Paste [`sst_log_spiral_swirl.glsl`](sst_log_spiral_swirl.glsl) into Image.
3. **Channel 0 → Microphone or Audio.**

**Title**

```text
SST log-spiral swirl-clock
```

**Tags**

```text
spiral, logpolar, knot, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

2D swirl-plane companion to “SST T(p,q) swirl-clock”.
Log-polar map with spiral arms h=(p,q) from the same coprime
catalogue (T(2,3)=3₁ default, then chirality q → −q).

• Arm ticks = swirl-clock bins along poloidal/toroidal windings.
• Soft ring = unknot / R≈const reference.
• Colour = phase (same cyan→magenta family as the tube shader).

Inspired by log-polar spiral-arm visuals; original code, not a fork.

No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse X: spin. Auto: slow rotation + ~2s (p,q) dwell.
Channel 0: mic/audio drives zoom, spin, arm contrast.
```

---

## Publish kit C — closed braid 3₁

1. New blank shader — **not** a fork of portal-braid shaders.
2. Paste [`sst_closed_braid.glsl`](sst_closed_braid.glsl) into Image.
3. **Channel 0 → Microphone or Audio.** `#define SEGMENTS 72` (raise on fast GPUs).

**Title**

```text
SST closed braid 3₁
```

**Tags**

```text
braid, knot, raymarching, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Closed 3-strand helical braid on a ring — braid-index / trefoil (3₁) sphere.
No portal tunnel: the strands close on themselves.

• Three phases 0, 2π/3, 4π/3; braid frequency k=2.
• Colour = phase along the loop (cyan→magenta, same family as the tube).
• Twist stripes = core torsion cue; side=±1 flips chirality every ~2s.

Companions: T(p,q) tube and log-spiral swirl-plane.

Original code (braid-core idea only; not a fork).
No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse: orbit. Auto: slow camera + chirality flip.
Channel 0: mic/audio drives strand thickness, spin, emissive pulse.
```

---

## Publish kit D — domain-twist ring

1. New blank shader — **not** a fork of compact domain-deform golf shaders.
2. Paste [`sst_domain_twist_ring.glsl`](sst_domain_twist_ring.glsl) into Image.
3. **Channel 0 → Microphone or Audio.**

**Title**

```text
SST domain-twist ring
```

**Tags**

```text
domain, twist, knot, raymarching, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Closed swirl as a domain-deformed ring: double polar unwrap,
shear twist, and mod lobes (swirl-clock bins). Winding scales
follow the same coprime (p,q) catalogue as the tube/spiral;
sign(q) flips shear = chirality.

• Colour = unwrap phase (cyan→magenta).
• Audio: bass→tube/glow, mid→spin, high→lobe contrast.

Companions: T(p,q) tube, log-spiral plane, closed braid 3₁.

Original rewrite (domain-deform idea only; not a fork).
No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse: orbit. Auto: slow camera + ~2s (p,q) dwell.
Channel 0: mic/audio.
```

---

## Publish kit E — trefoil ribbon

1. New blank shader — **not** a fork of ribbon/trefoil golf scenes.
2. Paste [`sst_trefoil_ribbon.glsl`](sst_trefoil_ribbon.glsl) into Image.
3. **Channel 0 → Microphone or Audio.**

**Title**

```text
SST trefoil ribbon
```

**Tags**

```text
trefoil, ribbon, knot, raymarching, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

T(2,3) trefoil as a twisted Frenet ribbon (rounded-box cross-section).
Coarse+fine nearest-t search along the centreline.
Chirality flips twist/z every ~2s.

• Colour = phase along the loop (cyan→magenta).
• Audio: bass→width/thickness, mid→twist amplitude, high→specular.

Companions: tube, spiral, braid, domain-twist, beads.

Original rewrite (ribbon idea only; not a fork).
No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse: orbit. Channel 0: mic/audio.
```

---

## Publish kit F — swirl-clock beads

1. New blank shader — **not** a fork of conta/bead golf shaders.
2. Paste [`sst_swirl_clock_beads.glsl`](sst_swirl_clock_beads.glsl) into Image.
3. **Channel 0 → Microphone or Audio.**

**Title**

```text
SST swirl-clock beads
```

**Tags**

```text
beads, clock, swirl, raymarching, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Discrete swirl-clock: 24 beads in a linear stack and a radial ring;
nearest layout wins. Phase colour per bead id.

• Audio: bass→radius, mid→spin, high→emissive.

Companions: tube, spiral, braid, domain-twist, ribbon.

Original rewrite (linear∪radial bead idea only; not a fork).
No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse X: spin. Channel 0: mic/audio.
```

---

## Publish kit G — phi log-spiral

1. New blank shader — **not** a fork of φ/log-polar golf shaders.
2. Paste [`sst_phi_log_spiral.glsl`](sst_phi_log_spiral.glsl) into Image.
3. **Channel 0 → Microphone or Audio.**

**Title**

```text
SST phi log-spiral
```

**Tags**

```text
phi, golden, logpolar, spiral, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Self-similar swirl-clock: log-polar map iterated with the golden
ratio φ = (1+√5)/2. Four layers composited in cyan→magenta.
Scale follows |p| from the coprime (p,q) catalogue; sign(q) flips
rotation (chirality).

Companion to “SST log-spiral swirl-clock” ((p,q) arms) — this one
is the φ-fractal kaleidoscope.

• Audio: bass→curve thickness, mid→spin, high→layer contrast.

Original rewrite (φ log-polar idea only; not a fork).
No Biot–Savart, no mass formula, no hyperbolic 4₁ here.

Mouse X: rotation offset. Channel 0: mic/audio.
```

---

## Publish kit H — Voronoi filaments (multi-buffer)

**Not** a single Image paste. Create a new Shadertoy with **Common + Buffer A + Buffer B + Image**.

### Paste checklist (Common resolution)

1. In **Common**, delete any `#define res iResolution.xy` (or similar). Keep `vec2 sstRes;` only.
2. Paste **all four** files (Common + Buffer A + Buffer B + Image). Each pass starts with `sstRes = iResolution.xy;`.
3. If you see `can't modify a uniform "iResolution"`, the old `#define res …` is still in Common — remove it and re-paste Common.
4. If the image is frozen with no compile error, `sstRes` was never assigned (still `(0,0)`) — re-paste the three passes.
5. If you see `'? : '`, Common used a struct ternary/constructor — this tree uses field assigns only. Re-paste Common.

### Files → tabs

| Tab | File |
|-----|------|
| Common | [`sst_voronoi_filaments_common.glsl`](sst_voronoi_filaments_common.glsl) |
| Buffer A | [`sst_voronoi_filaments_bufferA.glsl`](sst_voronoi_filaments_bufferA.glsl) |
| Buffer B | [`sst_voronoi_filaments_bufferB.glsl`](sst_voronoi_filaments_bufferB.glsl) |
| Image | [`sst_voronoi_filaments_image.glsl`](sst_voronoi_filaments_image.glsl) |

### Channel wiring

```text
Buffer A:  iChannel0 = Buffer A,  iChannel1 = Buffer B
Buffer B:  iChannel0 = Buffer A,  iChannel1 = Buffer B,  iChannel2 = Audio (Mic)
Image:     iChannel0 = Buffer A,  iChannel1 = Buffer B,  iChannel2 = Audio (Mic)
```

Set Buffer A/B to filter **Nearest**, wrap **Repeat** if available.

**Default kit (Common `pathAt`):** 8 concentric Trefoils, `off=0`,
`R = TREFOIL_R0 * (1..8)`, paste `rr` character × `TREFOIL_r_SCALE`.
Fits `(R_max + rr_max) * BASE_SCALE ≲ 0.45`. Even paths = particles, odd =
RGB strands. Per-path `ParticleConfig` (`size`, `color`, `speed`) and `strandWidth`
live on `FilamentPath`.
Kinds are `const int` (no `#define KIND_*`, no `_M`). Geometry is only in
`kindSpec()`. Flip later with `q = -q`. Ladder `KIND_L41`…`KIND_L112` =
lab Lissajous — **not** IQ 4₁ GLSL.

**Audio UX (Buffer B + Image):**
- bass → radial vortex stretch of all targets
- slight hue shift from mid + per-path spectrum band (particles)
- path 0 = mono attract; higher paths = stereo-wide (`AUDIO_WIDE_L` − `AUDIO_WIDE_R`)
- path phase is integrated (`dt * speed`), not `iTime * speed`, so audio dips do not reverse flow

**Title**

```text
SST Voronoi filaments (concentric trefoils)
```

**Tags**

```text
voronoi, particles, knot, trefoil, multipass, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Multi-pass swirl field: 8 concentric Trefoils (R = R0…8×R0). Even paths
are Voronoi particles; odd paths are RGB strand tubes. Black background.
FilamentPath holds mode, ParticleConfig (size/color/speed), strandWidth.
Every path — particles and strands — has its own particle config.

• Audio (iChannel2): bass→radial stretch/glow, mid→speed + slight hue,
  high→edge; path0 mono, outer paths stereo-wide.

Kinds: const int + kindSpec() (no KIND_*_M). Ladder L41…L112 = original
Lissajous — not IQ figure-8 GLSL. No hyperbolic 4₁ certificate.

Wire channels as in the workbench README kit H.
```

## Publish kit I — nested braid tree

**Channels**

```text
Image: iChannel0 = Microphone (or Audio)
```

**Title**

```text
SST nested braid tree (3×3×3)
```

**Tags**

```text
braid, nest, filament, raymarch, science, audio
```

**Description**

```text
[BRIDGE] visualisation — not a proof.

Hierarchical domain braid: three nested curve_transform
levels (3×3×3 = 27 leaves). Camera flies slowly along the
filament axis; chirality flips every ~2s.

• Cyan→magenta by leaf index (i*9+j*3+k)
• Audio: bass→leaf radius, mid→nest spin, high→leaf highlight
• Aether background; Image-tab only (no multi-buffer)

Original rewrite of nested curve_transform braid idea.
No portals, no IQ figure-8, no Biot–Savart / mass formula.
```

## Out of scope

- IQ figure-8 GLSL (any altered hosting)
- SSTcore / Biot–Savart in the GPU path
- Angular dashboard embed
- Quark / hyperbolic knot rendering
