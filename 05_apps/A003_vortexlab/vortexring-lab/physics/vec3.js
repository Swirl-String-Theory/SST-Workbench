/** @module physics/vec3 — pure 3-vector helpers (browser + Node) */

export function clamp(x, lo, hi) {
  return Math.max(lo, Math.min(hi, x));
}

export function vec3(ax, ay, az) {
  return [ax, ay, az];
}

export function vSub(a, b) {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

export function vDot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

export function vCross(a, b) {
  return [
    a[1] * b[2] - a[2] * b[1],
    a[2] * b[0] - a[0] * b[2],
    a[0] * b[1] - a[1] * b[0],
  ];
}

export function vNorm(a) {
  return Math.hypot(a[0], a[1], a[2]);
}

export function vAdd(a, b) {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

export function vScale(a, s) {
  return [a[0] * s, a[1] * s, a[2] * s];
}

export function pointAt(Y, o, idx) {
  return vec3(Y[o + 3 * idx], Y[o + 3 * idx + 1], Y[o + 3 * idx + 2]);
}
