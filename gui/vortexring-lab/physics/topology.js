/** @module physics/topology — polygonale Gauss writhe / linking integralen */

import { pointAt, vSub, vDot, vCross, vNorm } from './vec3.js';

export function gaussSegmentTerm(p1, p2, p3, p4) {
  const a = vSub(p2, p1);
  const b = vSub(p4, p3);
  const c = vSub(p3, p1);
  const d = vSub(p4, p2);
  const e = vSub(p3, p2);
  const f = vCross(a, b);
  const num = vDot(f, c);
  const den = vNorm(c) * vNorm(d) * vNorm(e) + vDot(c, d) * vDot(a, e);
  if (!isFinite(num) || !isFinite(den) || Math.abs(den) < 1e-24) return 0;
  return (2 * Math.atan2(num, den)) / (4 * Math.PI);
}

export function segmentsAdjacent(N, i, j) {
  if (i === j) return true;
  const d = Math.abs(i - j);
  const wrap = N - d;
  return d === 1 || wrap === 1;
}

/** Discrete Gauss integral between two closed polygonal curves in Y. */
export function gaussIntegral(Y, o1, N1, o2, N2, same, absMode = false) {
  let S = 0;
  for (let i = 0; i < N1; i++) {
    const p1 = pointAt(Y, o1, i);
    const p2 = pointAt(Y, o1, (i + 1) % N1);
    for (let j = 0; j < N2; j++) {
      if (same && segmentsAdjacent(N1, i, j)) continue;
      const p3 = pointAt(Y, o2, j);
      const p4 = pointAt(Y, o2, (j + 1) % N2);
      const term = gaussSegmentTerm(p1, p2, p3, p4);
      S += absMode ? Math.abs(term) : term;
    }
  }
  return S;
}

export function writheOfFilament(Y, fil) {
  return gaussIntegral(Y, fil.off, fil.N, fil.off, fil.N, true, false);
}

export function linkingFilaments(Y, fa, fb) {
  return gaussIntegral(Y, fa.off, fa.N, fb.off, fb.N, false, false);
}

export function acnOfFilament(Y, fil) {
  return gaussIntegral(Y, fil.off, fil.N, fil.off, fil.N, true, true);
}
