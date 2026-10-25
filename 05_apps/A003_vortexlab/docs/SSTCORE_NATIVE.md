# SSTcore native accel (VortexLab companion)

## Wat dit is

De Biot–Savart / LIA / RK4-hotpath in de browser blijft beschikbaar als **JS-fallback**.
Optioneel versnelt een lokaal **Node physics-server** dezelfde filamentkernels via **`sst-core@0.8.36`** (N-API C++).

Dit is **CPU**-acceleratie. WebGL (Arc/NVIDIA) tekent alleen; GPU-wissel versnelt de solver niet.

## Vereisten (Windows)

1. **Node.js ≥ 20**
2. Voor native build van `sst-core` (als er geen bruikbare prebuild is):
   - Visual Studio Build Tools 2022 met workload **Desktop development with C++**
   - **CMake** ≥ 3.20 op PATH
3. Lokale SSTcore-repo (workspace sibling) of gepubliceerde `sst-core@^0.8.36`

## Install

Vanuit `05_apps/A003_vortexlab`:

```powershell
npm install
```

`package.json` linkt standaard `sst-core` via `file:../../../SSTcore`.
`npm install` runt `sst-core`'s `install-native.js` (prebuild → CMake Release → verify).

Controle:

```powershell
node -e "const s=require('sst-core'); console.log(s.version,s.isNative)"
npm run test:physics
```

## Starten

Alleen JS (ongewijzigd gedrag):

```powershell
npm start
```

Web + physics-server:

```powershell
npm run start:native
```

- Lab: `http://127.0.0.1:4173`
- Physics: `http://127.0.0.1:4174` (`GET /health`, `POST /filament/velocity`, `POST /filament/rk4`)

Optioneel: `SSTCORE_PHYSICS_URL` / `SSTCORE_PHYSICS_PORT` / `window.SSTCORE_PHYSICS_URL`.

In de UI: **Native SSTcore (physics :4174)**. Bij fout/timeout: JS-fallback. ModelLog events: `sstcore-native-toggle`, `sstcore-native-fallback`.

Native wordt alleen gebruikt wanneer er geen VL-externe overlays actief zijn (mutual friction, bundle/BEM, wall-Ω, stretch-profile, axiale drift). Anders blijft de JS-pad bit-identiek aan M1.

## Architectuur

```text
Browser VortexLab  --JSON-->  Node physics-server  -->  require('sst-core')
                                      |
                               computeFilamentVelocity / rk4Step
Browser  -timeout/fout->  JS velocityCore / rk4Step
```

Contracten: `@sst/vortexlab-contracts` (`PHYSICS_PROTOCOL_VERSION`, filament request/response schemas).
