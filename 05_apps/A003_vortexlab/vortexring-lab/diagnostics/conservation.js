/** @module diagnostics/conservation — lengte, hashes, Kelvin-validatie */

export function arcLength(Y, fil) {
  let L = 0;
  const N = fil.N;
  const o = fil.off;
  for (let k = 0; k < N; k++) {
    const k2 = (k + 1) % N;
    L += Math.hypot(
      Y[o + 3 * k2] - Y[o + 3 * k],
      Y[o + 3 * k2 + 1] - Y[o + 3 * k + 1],
      Y[o + 3 * k2 + 2] - Y[o + 3 * k + 2],
    );
  }
  return L;
}

export function totalArcLength(Y, fils) {
  let L = 0;
  for (const f of fils) L += arcLength(Y, f);
  return L;
}

export function kelvinSpeed(R, gamma, a, deltaCore) {
  return (
    (Math.abs(gamma) / (4 * Math.PI * Math.max(R, 1e-6))) *
    (Math.log((8 * R) / a) - deltaCore)
  );
}

export function ringMeanRadius(Y, fil) {
  const N = fil.N;
  const o = fil.off;
  let cx = 0;
  let cy = 0;
  for (let k = 0; k < N; k++) {
    cx += Y[o + 3 * k];
    cy += Y[o + 3 * k + 1];
  }
  cx /= N;
  cy /= N;
  let R = 0;
  for (let k = 0; k < N; k++) {
    R += Math.hypot(Y[o + 3 * k] - cx, Y[o + 3 * k + 1] - cy);
  }
  return R / N;
}

/** FNV-1a over Float64Array bytes — deterministische state fingerprint. */
export function hashFloat64Array(arr) {
  let h = 0x811c9dc5;
  const view = new Uint8Array(arr.buffer, arr.byteOffset, arr.byteLength);
  for (let i = 0; i < view.length; i++) {
    h ^= view[i];
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, '0');
}

export function hashString(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, '0');
}

export function hashParams(P) {
  return hashString(JSON.stringify(P));
}

export function stateFingerprint(Y, P) {
  return `${hashFloat64Array(Y)}:${hashParams(P)}`;
}
