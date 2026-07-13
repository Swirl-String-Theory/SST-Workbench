/** @module physics/sst-similarity — Rankine display-similarity ansatz (niet canonieke kernfysica) */

export const KAPPA_HE = 9.9693e-8;
export const GAMMA0_SST = 9.68361920349e-9;
export const RCORE_SST = 1.40897017e-15;
export const VSWIRL_SST = 1.09384563e6;
export const OMEGA_CORE_SST = GAMMA0_SST / (2 * Math.PI * RCORE_SST * RCORE_SST);

export function gammaFromMedium(med, nQ, gaDemo) {
  if (med === 'he') return nQ * KAPPA_HE;
  if (med === 'sst') return nQ * GAMMA0_SST;
  const g = gaDemo;
  const s = g < 0 ? -1 : 1;
  return s * Math.max(Math.abs(g), 0.2) * 1e-3;
}

/** Rankine: Γ = 2π a² Ω */
export function rankineGamma(a, omega) {
  return 2 * Math.PI * a * a * Math.abs(omega);
}

export function rankineCoreSpeed(a, omega) {
  return a * Math.abs(omega);
}

export function similarityRadiusFromGamma(gamma, omega) {
  const om = Math.max(1e-12, Math.abs(omega));
  return Math.sqrt(Math.abs(gamma) / (2 * Math.PI * om));
}

export function displaySimilarityRatio(a, omega) {
  const uSim = rankineCoreSpeed(a, omega);
  return uSim / VSWIRL_SST;
}
