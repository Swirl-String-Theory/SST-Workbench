/** @module physics/contact — segment–segment afstanden en contactdetectie */

import { clamp, pointAt, vAdd, vDot, vNorm, vScale, vSub } from './vec3.js';
import { segmentsAdjacent } from './topology.js';

export function segmentSegmentDistance(p1, p2, p3, p4) {
  const u = vSub(p2, p1);
  const v = vSub(p4, p3);
  const w = vSub(p1, p3);
  const a = vDot(u, u);
  const b = vDot(u, v);
  const c = vDot(v, v);
  const d = vDot(u, w);
  const e = vDot(v, w);
  const D = a * c - b * b;
  let sc;
  let tc;
  if (D < 1e-24) {
    sc = 0;
    tc = c > 1e-24 ? clamp(e / c, 0, 1) : 0;
  } else {
    sc = clamp((b * e - c * d) / D, 0, 1);
    tc = clamp((a * e - b * d) / D, 0, 1);
  }
  const pq = vSub(vAdd(p1, vScale(u, sc)), vAdd(p3, vScale(v, tc)));
  return vNorm(pq);
}

export function minGapBetweenFilaments(Y, f1, f2) {
  let m = 1e9;
  for (let i = 0; i < f1.N; i++) {
    const p1 = pointAt(Y, f1.off, i);
    const p2 = pointAt(Y, f1.off, (i + 1) % f1.N);
    for (let j = 0; j < f2.N; j++) {
      const p3 = pointAt(Y, f2.off, j);
      const p4 = pointAt(Y, f2.off, (j + 1) % f2.N);
      m = Math.min(m, segmentSegmentDistance(p1, p2, p3, p4));
    }
  }
  return m;
}

export function dminSelf(Y, fil) {
  let m = 1e9;
  for (let i = 0; i < fil.N; i++) {
    const p1 = pointAt(Y, fil.off, i);
    const p2 = pointAt(Y, fil.off, (i + 1) % fil.N);
    for (let j = i + 1; j < fil.N; j++) {
      if (segmentsAdjacent(fil.N, i, j)) continue;
      const p3 = pointAt(Y, fil.off, j);
      const p4 = pointAt(Y, fil.off, (j + 1) % fil.N);
      m = Math.min(m, segmentSegmentDistance(p1, p2, p3, p4));
    }
  }
  return m;
}

/** Node-only gap (legacy detector for test D). */
export function minGapNodes(Y, f1, f2) {
  let m = 1e9;
  for (let i = 0; i < f1.N; i++) {
    for (let j = 0; j < f2.N; j++) {
      const dx = Y[f1.off + 3 * i] - Y[f2.off + 3 * j];
      const dy = Y[f1.off + 3 * i + 1] - Y[f2.off + 3 * j + 1];
      const dz = Y[f1.off + 3 * i + 2] - Y[f2.off + 3 * j + 2];
      m = Math.min(m, Math.hypot(dx, dy, dz));
    }
  }
  return m;
}

/**
 * Pure contact check (no DOM / flags). Returns { hit, msg, warnOnly }.
 * @param {object} ctx
 */
export function checkContactRegime(ctx) {
  const {
    Y,
    fils,
    mode,
    inter,
    a,
    Rcyl,
    zMin,
    zMax,
    topo,
    knotKey,
    knotIdx,
    tracerWrapZ,
    ringN = 48,
  } = ctx;
  const lia = inter === 'lia';
  const thresh = 3 * a;

  if (mode === 'botsing' && !lia) {
    const fa = fils.filter((f) => (f.carrier || 'A') === 'A');
    const fb = fils.filter((f) => (f.carrier || 'A') === 'B');
    if (fa.length && fb.length) {
      let cross = 1e9;
      for (const f1 of fa) for (const f2 of fb) {
        cross = Math.min(cross, minGapBetweenFilaments(Y, f1, f2));
      }
      if (cross < thresh) {
        return {
          hit: true,
          msg: '⚠ dragers binnen 3a — reconnectieregime; filamentmodel niet langer geldig. Reset om opnieuw te draaien.',
          warnOnly: false,
        };
      }
    }
  }

  const knotLike = topo === 'trefoil' || knotKey || knotIdx >= 0;
  for (const f of fils) {
    if (f.N > ringN || knotLike) {
      const ds = dminSelf(Y, f);
      if (ds < thresh) {
        return {
          hit: true,
          msg: lia
            ? '⚠ strengen < 3a: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'
            : '⚠ strengen binnen 3a — zelfreconnectieregime: hier zou de knoop ontknopen (Kleckner–Irvine); niet gemodelleerd.',
          warnOnly: lia,
        };
      }
    }
    for (let ii = 0; ii < fils.length; ii++) {
      for (let jj = ii + 1; jj < fils.length; jj++) {
        if ((fils[ii].carrier || 'A') !== (fils[jj].carrier || 'A')) continue;
        if (minGapBetweenFilaments(Y, fils[ii], fils[jj]) < thresh) {
          return {
            hit: true,
            msg: lia
              ? '⚠ componenten < 3a: LIA negeert deze interactie — resultaat vanaf hier kwalitatief.'
              : '⚠ componenten binnen 3a — reconnectieregime binnen de drager; niet gemodelleerd.',
            warnOnly: lia,
          };
        }
      }
    }
    const st = filamentCentroidStats(Y, f);
    if (st.rWall > 0.9 * Rcyl) {
      return { hit: true, msg: 'filament buiten volume-kader', warnOnly: true };
    }
    if (!tracerWrapZ && (st.z < zMin + 0.02 || st.z > zMax - 0.02)) {
      return { hit: true, msg: 'filament buiten z-domein', warnOnly: true };
    }
  }
  return { hit: false };
}

export function filamentCentroidStats(Y, f) {
  const N = f.N;
  const o = f.off;
  let cx = 0;
  let cy = 0;
  let cz = 0;
  for (let k = 0; k < N; k++) {
    cx += Y[o + 3 * k];
    cy += Y[o + 3 * k + 1];
    cz += Y[o + 3 * k + 2];
  }
  cx /= N;
  cy /= N;
  cz /= N;
  let R = 0;
  let rWall = 0;
  for (let k = 0; k < N; k++) {
    R += Math.hypot(Y[o + 3 * k] - cx, Y[o + 3 * k + 1] - cy);
    rWall = Math.max(rWall, Math.hypot(Y[o + 3 * k], Y[o + 3 * k + 1]));
  }
  return { R: R / N, z: cz, rWall, cx, cy, cz };
}
