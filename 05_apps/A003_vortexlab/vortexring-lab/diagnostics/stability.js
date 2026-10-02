/** @module diagnostics/stability — passieve stabiliteitsmetingen (geen mutatie) */

import { clamp } from '../physics/vec3.js';
import { filamentCentroidStats } from '../physics/contact.js';

export function scoreDescending(x, good, bad) {
  if (x <= good) return 100;
  if (x >= bad) return 0;
  return (100 * (bad - x)) / (bad - good);
}

export function scoreAscending(x, bad, good) {
  if (x >= good) return 100;
  if (x <= bad) return 0;
  return (100 * (x - bad)) / (good - bad);
}

/** Wandmarge in eenheden van tube-radius a (passief). */
export function minBoundaryRatio(Y, fils, { Rcyl, zMin, zMax, a }) {
  let boundary = Infinity;
  for (const f of fils) {
    const o = f.off;
    for (let k = 0; k < f.N; k++) {
      const x = Y[o + 3 * k];
      const y = Y[o + 3 * k + 1];
      const z = Y[o + 3 * k + 2];
      boundary = Math.min(
        boundary,
        Rcyl - Math.hypot(x, y) - a,
        z - zMin - a,
        zMax - z - a,
      );
    }
  }
  return boundary / Math.max(a, 1e-12);
}

export function filamentResolutionMetrics(Y, fil, { a, core, deltaTable, c0 }) {
  const N = fil.N;
  const o = fil.off;
  const eD = Math.exp(deltaTable[core] ?? 0.615);
  let lmin = Infinity;
  let lmax = 0;
  let lsum = 0;
  let maxAk = 0;
  let minLogArg = Infinity;
  for (let i = 0; i < N; i++) {
    const im = (i - 1 + N) % N;
    const ip = (i + 1) % N;
    const ax = Y[o + 3 * i] - Y[o + 3 * im];
    const ay = Y[o + 3 * i + 1] - Y[o + 3 * im + 1];
    const az = Y[o + 3 * i + 2] - Y[o + 3 * im + 2];
    const bx = Y[o + 3 * ip] - Y[o + 3 * i];
    const by = Y[o + 3 * ip + 1] - Y[o + 3 * i + 1];
    const bz = Y[o + 3 * ip + 2] - Y[o + 3 * i + 2];
    const la = Math.hypot(ax, ay, az);
    const lb = Math.hypot(bx, by, bz);
    lmin = Math.min(lmin, lb);
    lmax = Math.max(lmax, lb);
    lsum += lb;
    if (la > 1e-12 && lb > 1e-12) {
      const dot = clamp((ax * bx + ay * by + az * bz) / (la * lb), -1, 1);
      const ang = Math.acos(dot);
      const kappa = (2 * Math.sin(0.5 * ang)) / Math.max(1e-12, 0.5 * (la + lb));
      maxAk = Math.max(maxAk, a * kappa);
      minLogArg = Math.min(minLogArg, (2 * Math.sqrt(la * lb)) / (eD * Math.max(a, 1e-12)));
    }
  }
  return { lmin, lmax, lmean: lsum / N, q: lmax / Math.max(lmin, 1e-12), maxAk, minLogArg };
}

/** Passieve kernlimiet — meet alleen, muteert P.a niet. */
export function intrinsicCoreRadiusLimitMeasure(reachCandidates) {
  let reach = Infinity;
  for (const r of reachCandidates) reach = Math.min(reach, r);
  if (!Number.isFinite(reach) || reach <= 0) reach = 1e-6;
  return Math.max(1e-6, 0.995 * reach);
}
