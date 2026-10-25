/**
 * VortexLab Research Track helpers — VL01…VL08 scaffolding.
 * Passief: geen solverfeedback. Geladen vóór vortexlab-runtime.js.
 */
(function (global) {
  'use strict';

  const V_CHAR = typeof global.V_CHAR_SST === 'number' ? global.V_CHAR_SST : 2.99792458e8;
  const C2 = V_CHAR * V_CHAR;

  /** VL01 — signed local Swirl-Clock route from mutual samples and unit tangents. */
  function signedLocalSwirlClock(points, mutualVel, vStar, eHat) {
    const n = Math.floor(points.length / 3);
    if (!n || mutualVel.length < 3 * n) {
      return { ok: false, reason: 'empty-samples' };
    }
    const v0 = Number.isFinite(vStar) ? vStar : V_CHAR;
    let sum = 0, sumSq = 0, posLen = 0, negLen = 0, totLen = 0;
    let minS = Infinity, maxS = -Infinity, minAt = 0, maxAt = 0;
    const series = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const i0 = 3 * i, j0 = 3 * ((i + 1) % n);
      const dx = points[j0] - points[i0], dy = points[j0 + 1] - points[i0 + 1], dz = points[j0 + 2] - points[i0 + 2];
      const seg = Math.hypot(dx, dy, dz) || 1e-300;
      let ex, ey, ez;
      if (eHat && eHat.length >= 3 * n) {
        ex = eHat[i0]; ey = eHat[i0 + 1]; ez = eHat[i0 + 2];
      } else {
        const tl = Math.hypot(dx, dy, dz) || 1e-300;
        ex = dx / tl; ey = dy / tl; ez = dz / tl;
      }
      const ux = mutualVel[i0], uy = mutualVel[i0 + 1], uz = mutualVel[i0 + 2];
      const vx = v0 * ex + ux, vy = v0 * ey + uy, vz = v0 * ez + uz;
      const veff2 = vx * vx + vy * vy + vz * vz;
      const uPar = ux * ex + uy * ey + uz * ez;
      // signed contribution ~ parallel mutual vs intrinsic swirl direction
      const signed = uPar;
      series[i] = signed;
      sum += signed * seg;
      sumSq += signed * signed * seg;
      totLen += seg;
      if (signed >= 0) posLen += seg; else negLen += seg;
      if (signed < minS) { minS = signed; minAt = i; }
      if (signed > maxS) { maxS = signed; maxAt = i; }
      void veff2; // reserved for ln η(s) when c-gate is active
    }
    const mean = totLen > 0 ? sum / totLen : 0;
    const rms = totLen > 0 ? Math.sqrt(sumSq / totLen) : 0;
    return {
      ok: true,
      schema: 'vortexlab-signed-local-swirl-clock/1.0',
      signedMean: mean,
      rms,
      positiveArclengthFraction: totLen > 0 ? posLen / totLen : 0,
      negativeArclengthFraction: totLen > 0 ? negLen / totLen : 0,
      extrema: { min: minS, max: maxS, minIndex: minAt, maxIndex: maxAt },
      envelopeNote: 'RMS envelope blijft een aparte symmetrische diagnostic; deze route is signed.',
      seriesLength: n
    };
  }

  function signedParityCompare(a, b) {
    if (!a?.ok || !b?.ok) return { ok: false };
    const flip = Math.sign(a.signedMean) * Math.sign(b.signedMean);
    return {
      ok: true,
      meanProductSign: flip,
      abParityPass: flip < 0 || (Math.abs(a.signedMean) < 1e-30 && Math.abs(b.signedMean) < 1e-30)
    };
  }

  /** VL02 — preregistered distance / orientation matrix (holdouts frozen). */
  const DISTANCE_ORIENTATION_REGISTRY = Object.freeze([
    { id: 'dL_1.1', dOverLK: 1.1, offset: 0, tiltDeg: 0, orientation: 'co', mirror: false, holdout: false },
    { id: 'dL_1.25', dOverLK: 1.25, offset: 0, tiltDeg: 0, orientation: 'co', mirror: false, holdout: false },
    { id: 'dL_1.5', dOverLK: 1.5, offset: 0, tiltDeg: 0, orientation: 'co', mirror: false, holdout: false },
    { id: 'dL_2', dOverLK: 2, offset: 0, tiltDeg: 0, orientation: 'co', mirror: false, holdout: false },
    { id: 'dL_3', dOverLK: 3, offset: 0, tiltDeg: 0, orientation: 'co', mirror: false, holdout: true },
    { id: 'dL_4', dOverLK: 4, offset: 0, tiltDeg: 0, orientation: 'co', mirror: false, holdout: true },
    { id: 'dL_2_offset', dOverLK: 2, offset: 0.05, tiltDeg: 0, orientation: 'co', mirror: false, holdout: false },
    { id: 'dL_2_tilt15', dOverLK: 2, offset: 0, tiltDeg: 15, orientation: 'co', mirror: false, holdout: false },
    { id: 'dL_2_contra', dOverLK: 2, offset: 0, tiltDeg: 0, orientation: 'contra', mirror: false, holdout: false },
    { id: 'dL_2_mirror', dOverLK: 2, offset: 0, tiltDeg: 0, orientation: 'co', mirror: true, holdout: true }
  ]);

  /** VL03 — export rename map (canonical keys for verse JSON). */
  const OBSERVABLE_RENAME = Object.freeze({
    phaseLogRatio: 'rigidResponseLogRatio',
    omegaBody: 'omegaRigidCenterline',
    fieldLogMin: 'kinematicClockEnvelopeMin',
    fieldLogMax: 'kinematicClockEnvelopeMax',
    v_def: 'centerlineDeformationResidual'
  });

  function renameObservables(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    if (Array.isArray(obj)) return obj.map(renameObservables);
    const out = {};
    for (const [k, v] of Object.entries(obj)) {
      const nk = OBSERVABLE_RENAME[k] || k;
      out[nk] = renameObservables(v);
    }
    return out;
  }

  /** VL04 — discrete Bishop frame along a closed polygon. */
  function bishopFrame(points) {
    const n = Math.floor(points.length / 3);
    if (n < 4) return { ok: false, reason: 'N<4' };
    const T = new Float64Array(3 * n), N1 = new Float64Array(3 * n), N2 = new Float64Array(3 * n);
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      let tx = points[3 * j] - points[3 * i], ty = points[3 * j + 1] - points[3 * i + 1], tz = points[3 * j + 2] - points[3 * i + 2];
      const tl = Math.hypot(tx, ty, tz) || 1e-300;
      tx /= tl; ty /= tl; tz /= tl;
      T[3 * i] = tx; T[3 * i + 1] = ty; T[3 * i + 2] = tz;
    }
    // seed normal perpendicular to T0
    let ax = 1, ay = 0, az = 0;
    if (Math.abs(T[0]) > 0.9) { ax = 0; ay = 1; }
    let n1x = ay * T[2] - az * T[1], n1y = az * T[0] - ax * T[2], n1z = ax * T[1] - ay * T[0];
    let nl = Math.hypot(n1x, n1y, n1z) || 1e-300;
    n1x /= nl; n1y /= nl; n1z /= nl;
    N1[0] = n1x; N1[1] = n1y; N1[2] = n1z;
    N2[0] = T[1] * n1z - T[2] * n1y; N2[1] = T[2] * n1x - T[0] * n1z; N2[2] = T[0] * n1y - T[1] * n1x;
    for (let i = 0; i < n - 1; i++) {
      const t0x = T[3 * i], t0y = T[3 * i + 1], t0z = T[3 * i + 2];
      const t1x = T[3 * (i + 1)], t1y = T[3 * (i + 1) + 1], t1z = T[3 * (i + 1) + 2];
      // parallel transport N1 via projection
      let qx = N1[3 * i], qy = N1[3 * i + 1], qz = N1[3 * i + 2];
      const dot = qx * t1x + qy * t1y + qz * t1z;
      qx -= dot * t1x; qy -= dot * t1y; qz -= dot * t1z;
      nl = Math.hypot(qx, qy, qz) || 1e-300;
      qx /= nl; qy /= nl; qz /= nl;
      N1[3 * (i + 1)] = qx; N1[3 * (i + 1) + 1] = qy; N1[3 * (i + 1) + 2] = qz;
      N2[3 * (i + 1)] = t1y * qz - t1z * qy;
      N2[3 * (i + 1) + 1] = t1z * qx - t1x * qz;
      N2[3 * (i + 1) + 2] = t1x * qy - t1y * qx;
      void t0x; void t0y; void t0z;
    }
    // holonomy: angle between transported N1[n-1]→0 and N1[0]
    const hx = N1[3 * (n - 1)], hy = N1[3 * (n - 1) + 1], hz = N1[3 * (n - 1) + 2];
    let px = hx, py = hy, pz = hz;
    const t0x = T[0], t0y = T[1], t0z = T[2];
    const d = px * t0x + py * t0y + pz * t0z;
    px -= d * t0x; py -= d * t0y; pz -= d * t0z;
    nl = Math.hypot(px, py, pz) || 1e-300;
    px /= nl; py /= nl; pz /= nl;
    const holonomy = Math.atan2(
      px * N2[0] + py * N2[1] + pz * N2[2],
      px * N1[0] + py * N1[1] + pz * N1[2]
    );
    let maxOrth = 0;
    for (let i = 0; i < n; i++) {
      const tx = T[3 * i], ty = T[3 * i + 1], tz = T[3 * i + 2];
      const nx = N1[3 * i], ny = N1[3 * i + 1], nz = N1[3 * i + 2];
      maxOrth = Math.max(maxOrth, Math.abs(tx * nx + ty * ny + tz * nz));
    }
    return {
      ok: true,
      schema: 'vortexlab-bishop-frame/1.0',
      n,
      holonomyRad: holonomy,
      maxTangentNormalDot: maxOrth,
      omega0: null, // filled by caller with v↺*/r_c
      solverFeedback: false
    };
  }

  /** VL05 — finite-difference mutual velocity gradient along centerline. */
  function mutualVelocityGradient(points, mutualVel) {
    const n = Math.floor(points.length / 3);
    if (n < 4) return { ok: false };
    let maxAbsTr = 0, sumTtS = 0, sumWdotT = 0, wSum = 0;
    for (let i = 0; i < n; i++) {
      const im = (i + n - 1) % n, ip = (i + 1) % n;
      const ds = Math.hypot(
        points[3 * ip] - points[3 * im],
        points[3 * ip + 1] - points[3 * im + 1],
        points[3 * ip + 2] - points[3 * im + 2]
      ) || 1e-300;
      // directional derivative along tangent as proxy for G·t
      const dux = (mutualVel[3 * ip] - mutualVel[3 * im]) / ds;
      const duy = (mutualVel[3 * ip + 1] - mutualVel[3 * im + 1]) / ds;
      const duz = (mutualVel[3 * ip + 2] - mutualVel[3 * im + 2]) / ds;
      const tx = (points[3 * ip] - points[3 * im]) / ds;
      const ty = (points[3 * ip + 1] - points[3 * im + 1]) / ds;
      const tz = (points[3 * ip + 2] - points[3 * im + 2]) / ds;
      // incomplete G; report tangential stretch proxy t·(du/ds)
      const tSt = dux * tx + duy * ty + duz * tz;
      sumTtS += tSt * ds;
      // vorticity proxy from central differences in lab frame (weak)
      const wx = duy * tz - duz * ty;
      sumWdotT += (wx * tx) * ds;
      wSum += ds;
      maxAbsTr = Math.max(maxAbsTr, Math.abs(dux + duy + duz) * 0); // placeholder: full G needs 3D stencil
    }
    return {
      ok: true,
      schema: 'vortexlab-mutual-velocity-gradient/1.0',
      note: 'Centerline directional derivative only; full 3D G_ij requires off-curve stencil (VL05 design).',
      meanTangentStretch: wSum > 0 ? sumTtS / wSum : 0,
      meanOmegaExtDotT: wSum > 0 ? sumWdotT / wSum : 0,
      maxAbsTraceProxy: maxAbsTr,
      trGGate: 'INFO'
    };
  }

  /** VL06 — preregistered internal-phase candidates (frozen; no post-hoc 1/8π). */
  const INTERNAL_PHASE_CANDIDATES = Object.freeze([
    {
      id: 'ROT_OMEGA_EXT_DOT_T',
      formula: 'δθ̇_int = ω_ext · t̂',
      derivedFrom: 'VL05 external vorticity projection',
      freezeDate: '2026-10-23',
      postHocForbidden: true
    },
    {
      id: 'KELVIN_STRAIN_STUB',
      formula: 'δω_K = F_K(S,a_core,Γ,k) — requires finite-core profile',
      derivedFrom: 'pending finite-core profile ACK',
      freezeDate: '2026-10-23',
      enabled: false
    }
  ]);

  /** VL07 — confirmatory checklist (structure only until a law is frozen). */
  const CONFIRMATORY_CHECKLIST = Object.freeze([
    'continuumConvergence',
    'staticNull',
    'abParity',
    'chirality',
    'distanceHoldouts',
    'orientationHoldouts',
    'multiTopology',
    'aSimIndependence',
    'independentlyDerivedCoefficients'
  ]);

  /** VL08 — radiusDrive / runTheory defaults. */
  const ROSETTA_DEFAULTS = Object.freeze({
    radiusDrive: 'physical-only',
    runTheory: 'SST',
    classicalE2AliasOf: 'sstCore',
    planckInvariantSelftestId: 'T14'
  });

  function analyzeCarrierPair(raw) {
    if (!raw?.carriers?.A?.points || !raw?.carriers?.A?.fields?.mutual) {
      return { ok: false, reason: 'missing-carrier-fields' };
    }
    const out = { ok: true, schema: 'vortexlab-research-track-bundle/1.0', A: {}, B: {} };
    for (const which of ['A', 'B']) {
      const pts = raw.carriers[which].points;
      const mut = raw.carriers[which].fields.mutual;
      const signed = signedLocalSwirlClock(pts, mut, V_CHAR, null);
      const bishop = bishopFrame(pts);
      const grad = mutualVelocityGradient(pts, mut);
      if (bishop.ok) bishop.omega0 = V_CHAR / (typeof global.R_HORN_SST === 'number' ? global.R_HORN_SST : 1.40897017e-15);
      out[which] = { signedLocal: signed, bishop, gradient: grad };
    }
    out.abParity = signedParityCompare(out.A.signedLocal, out.B.signedLocal);
    out.distanceOrientationRegistry = DISTANCE_ORIENTATION_REGISTRY;
    out.internalPhaseCandidates = INTERNAL_PHASE_CANDIDATES;
    out.confirmatoryChecklist = CONFIRMATORY_CHECKLIST;
    out.rosettaDefaults = ROSETTA_DEFAULTS;
    return out;
  }

  global.VLResearchTrack = {
    signedLocalSwirlClock,
    signedParityCompare,
    DISTANCE_ORIENTATION_REGISTRY,
    OBSERVABLE_RENAME,
    renameObservables,
    bishopFrame,
    mutualVelocityGradient,
    INTERNAL_PHASE_CANDIDATES,
    CONFIRMATORY_CHECKLIST,
    ROSETTA_DEFAULTS,
    analyzeCarrierPair,
    version: '1.0.0'
  };
})(typeof window !== 'undefined' ? window : globalThis);
