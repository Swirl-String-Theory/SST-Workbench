/** @module physics/body-frame — χ-as (PCA) en Ω_body na centroidaftrek */

import { filamentCentroidStats } from './contact.js';

/**
 * Objectieve chiraliteitsas: eerste hoofdcomponent van xy-projectie (PCA).
 * @returns {{x:number,y:number,phi:number}|null}
 */
export function chiHatFromFilament(Y, fil, { isRing = false } = {}) {
  if (isRing) return null;
  const st = filamentCentroidStats(Y, fil);
  const N = fil.N;
  const o = fil.off;
  let sxx = 0;
  let sxy = 0;
  let syy = 0;
  for (let k = 0; k < N; k++) {
    const dx = Y[o + 3 * k] - st.cx;
    const dy = Y[o + 3 * k + 1] - st.cy;
    sxx += dx * dx;
    sxy += dx * dy;
    syy += dy * dy;
  }
  const inv = 1 / Math.max(1, N);
  sxx *= inv;
  sxy *= inv;
  syy *= inv;
  const tr = sxx + syy;
  const det = sxx * syy - sxy * sxy;
  const disc = Math.max(0, (tr * tr) * 0.25 - det);
  const lambda1 = tr * 0.5 + Math.sqrt(disc);
  let vx = sxy;
  let vy = lambda1 - sxx;
  const n = Math.hypot(vx, vy);
  if (n < 1e-12) {
    vx = 1;
    vy = 0;
  } else {
    vx /= n;
    vy /= n;
  }
  return { x: vx, y: vy, phi: (Math.atan2(vy, vx) * 180) / Math.PI };
}

/**
 * Body-frame Ω_z uit punt-snelheden na aftrek centroidtranslatie.
 */
export function bodyFrameOmega(Y, fil, V) {
  const st = filamentCentroidStats(Y, fil);
  const N = fil.N;
  const o = fil.off;
  let vcx = 0;
  let vcy = 0;
  let vcz = 0;
  for (let k = 0; k < N; k++) {
    vcx += V[o + 3 * k];
    vcy += V[o + 3 * k + 1];
    vcz += V[o + 3 * k + 2];
  }
  vcx /= N;
  vcy /= N;
  vcz /= N;
  let num = 0;
  let den = 0;
  for (let k = 0; k < N; k++) {
    const rx = Y[o + 3 * k] - st.cx;
    const ry = Y[o + 3 * k + 1] - st.cy;
    const vx = V[o + 3 * k] - vcx;
    const vy = V[o + 3 * k + 1] - vcy;
    num += rx * vy - ry * vx;
    den += rx * rx + ry * ry;
  }
  return den > 1e-12 ? num / den : 0;
}

export function bodyFrameState(Y, fil, V, opts = {}) {
  const st = filamentCentroidStats(Y, fil);
  const omegaZ = bodyFrameOmega(Y, fil, V);
  const chi = chiHatFromFilament(Y, fil, opts);
  return { omegaZ, chi, cx: st.cx, cy: st.cy, cz: st.cz, R: st.R };
}
