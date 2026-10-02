/** @module physics/timestep — CFL en RK4 snelheidslimieten */

export const C0 = 0.1395;
export const DELTA = { hol: 0.5, vast: 0.25, gp: 0.615 };

export function lminFromY(Y, fils) {
  let m = 1e9;
  for (const f of fils) {
    const N = f.N;
    const o = f.off;
    for (let k = 0; k < N; k++) {
      const k2 = (k + 1) % N;
      const d = Math.hypot(
        Y[o + 3 * k2] - Y[o + 3 * k],
        Y[o + 3 * k2 + 1] - Y[o + 3 * k + 1],
        Y[o + 3 * k2 + 2] - Y[o + 3 * k + 2],
      );
      if (d < m) m = d;
    }
  }
  return m;
}

export function gammaMaxAll(gammas) {
  let g = 0;
  for (const x of gammas) g = Math.max(g, Math.abs(x));
  return Math.max(g, 1e-30);
}

/**
 * Kelvin-wave CFL + advective cap.
 * @param {object} p
 * @param {number} p.lm — min segment length
 * @param {number} p.gammaMax
 * @param {number} p.lastUmax
 * @param {number} p.a
 * @param {string} p.core — hol | vast | gp
 * @param {number} [p.Om]
 * @param {boolean} [p.bgOmegaCoupling]
 */
export function dtCFL(p) {
  const eD = Math.exp(DELTA[p.core] ?? DELTA.gp);
  const nu = (p.gammaMax / (4 * Math.PI)) * (Math.log((2 * p.lm) / (eD * p.a)) + C0);
  const om = Math.max(1e-12, Math.abs(nu) * (Math.PI / p.lm) ** 2);
  let dt = 0.5 / om;
  dt = Math.min(dt, 0.25 * p.lm / Math.max(1e-12, p.lastUmax));
  if (p.bgOmegaCoupling && Math.abs(p.Om) > 1e-9) {
    dt = Math.min(dt, 0.2 / Math.abs(p.Om));
  }
  return dt;
}

export function maxRKStageSpeed(speeds) {
  let u = 1e-12;
  for (const s of speeds) u = Math.max(u, s);
  return u;
}
