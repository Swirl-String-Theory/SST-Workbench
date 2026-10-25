/**
 * Render-only Fourier sampling for the VortexLab catalog page.
 * Copied/adapted from vortexlab-runtime.js (no Biot–Savart / solver state).
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  }
  root.VortexLabCatalogGeometry = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function finiteMetaNumber(v) {
    const n = Number(v);
    return Number.isFinite(n) ? n : NaN;
  }

  function sampleFourierParametric(coeffs, n) {
    const x = new Float64Array(3 * n);
    const list = coeffs || [];
    for (let k = 0; k < n; k++) {
      const t = (2 * Math.PI * k) / n;
      let px = 0;
      let py = 0;
      let pz = 0;
      for (const c of list) {
        const I = Number(c.I) || 0;
        const ct = Math.cos(I * t);
        const st = Math.sin(I * t);
        const A = c.A || [0, 0, 0];
        const B = c.B || [0, 0, 0];
        px += ct * A[0] + st * B[0];
        py += ct * A[1] + st * B[1];
        pz += ct * A[2] + st * B[2];
      }
      x[3 * k] = px;
      x[3 * k + 1] = py;
      x[3 * k + 2] = pz;
    }
    return x;
  }

  function resampleClosedCurve(raw, n) {
    const m = Math.floor(raw.length / 3);
    const cum = new Float64Array(m + 1);
    for (let i = 0; i < m; i++) {
      const j = (i + 1) % m;
      cum[i + 1] =
        cum[i] +
        Math.hypot(
          raw[3 * j] - raw[3 * i],
          raw[3 * j + 1] - raw[3 * i + 1],
          raw[3 * j + 2] - raw[3 * i + 2]
        );
    }
    const L = cum[m];
    const out = new Float64Array(3 * n);
    if (!(L > 0)) return out;
    let seg = 0;
    for (let k = 0; k < n; k++) {
      const target = (L * k) / n;
      while (seg < m - 1 && cum[seg + 1] < target) seg++;
      const j = (seg + 1) % m;
      const den = Math.max(1e-30, cum[seg + 1] - cum[seg]);
      const u = (target - cum[seg]) / den;
      out[3 * k] = raw[3 * seg] + u * (raw[3 * j] - raw[3 * seg]);
      out[3 * k + 1] = raw[3 * seg + 1] + u * (raw[3 * j + 1] - raw[3 * seg + 1]);
      out[3 * k + 2] = raw[3 * seg + 2] + u * (raw[3 * j + 2] - raw[3 * seg + 2]);
    }
    return out;
  }

  function sampleFourierKnot(coeffs, n, arcLengthUniform) {
    if (!arcLengthUniform) return sampleFourierParametric(coeffs, n);
    const imax = (coeffs || []).reduce(
      (m, c) => Math.max(m, Math.abs(Number(c.I) || 0)),
      1
    );
    const nRef = Math.max(4096, 16 * imax);
    return resampleClosedCurve(sampleFourierParametric(coeffs, nRef), n);
  }

  function sampleIdealComponent(component, n) {
    return sampleFourierKnot(component.coeffs || component, n, true);
  }

  function sampleKnotPlotComponent(entry, component, n) {
    const nativeN = Math.max(
      4,
      Math.round(
        finiteMetaNumber(component && component.pointCount) ||
          finiteMetaNumber(
            entry &&
              entry.pointsPerComponent &&
              entry.pointsPerComponent[Math.max(0, (Number(component && component.I) || 1) - 1)]
          ) ||
          300
      )
    );
    const native = sampleFourierParametric(component.coeffs || component, nativeN);
    return n === nativeN ? native : resampleClosedCurve(native, n);
  }

  function sampleCatalogComponent(entry, component, n, source) {
    if (source === 'knotplot') {
      const role = entry && entry.sourceRole;
      const label = entry && entry.normalization && entry.normalization.label;
      if (role === 'vortexlab-uniform-N300' || label === 'uniform-N300') {
        return sampleKnotPlotComponent(entry, component, n);
      }
      // Native polygonal Fourier (A006 seeds / borromean / other knotplot):
      // evaluate on native grid then resample to thumb-N.
      const nativeN = Math.max(
        4,
        Math.round(
          finiteMetaNumber(component && component.pointCount) ||
            finiteMetaNumber(entry && entry.resolutionN) ||
            256
        )
      );
      const native = sampleFourierParametric(component.coeffs || component, nativeN);
      return n === nativeN ? native : resampleClosedCurve(native, n);
    }
    if (source === 'twist') {
      const nativeN = Math.max(
        4,
        Math.round(
          finiteMetaNumber(component && component.pointCount) ||
            finiteMetaNumber(entry && entry.resolutionN) ||
            256
        )
      );
      const native = sampleFourierParametric(component.coeffs || component, nativeN);
      return n === nativeN ? native : resampleClosedCurve(native, n);
    }
    return sampleIdealComponent(component, n);
  }

  function knotEntryComponents(entry) {
    if (!entry) return [];
    if (Array.isArray(entry.components) && entry.components.length) return entry.components;
    if (entry.coeffs) return [entry];
    return [];
  }

  /** Center and scale so RMS radius ≈ 1 (or max |r| ≈ 1). Returns {points[] Float64Array, radius}. */
  function normalizeComponents(rawList) {
    let cx = 0;
    let cy = 0;
    let cz = 0;
    let count = 0;
    for (const raw of rawList) {
      const n = Math.floor(raw.length / 3);
      for (let k = 0; k < n; k++) {
        cx += raw[3 * k];
        cy += raw[3 * k + 1];
        cz += raw[3 * k + 2];
        count++;
      }
    }
    if (count > 0) {
      cx /= count;
      cy /= count;
      cz /= count;
    }
    let rMax = 0;
    const points = rawList.map((raw) => {
      const n = Math.floor(raw.length / 3);
      const out = new Float64Array(3 * n);
      for (let k = 0; k < n; k++) {
        const x = raw[3 * k] - cx;
        const y = raw[3 * k + 1] - cy;
        const z = raw[3 * k + 2] - cz;
        out[3 * k] = x;
        out[3 * k + 1] = y;
        out[3 * k + 2] = z;
        rMax = Math.max(rMax, Math.hypot(x, y, z));
      }
      return out;
    });
    const scale = rMax > 1e-12 ? 1 / rMax : 1;
    for (const out of points) {
      for (let i = 0; i < out.length; i++) out[i] *= scale;
    }
    return { points, radius: 1, center: [cx, cy, cz], scale };
  }

  function sampleEntryThumb(entry, source, thumbN) {
    const n = Math.max(32, Math.round(thumbN) || 160);
    const comps = knotEntryComponents(entry);
    if (!comps.length) return { points: [], radius: 1 };
    const raws = comps.map((c) => sampleCatalogComponent(entry, c, n, source));
    return normalizeComponents(raws);
  }

  /** Unit circle in XY for tests: x=cos t, y=sin t. */
  function unitCircleCoeffs() {
    return [
      { I: 0, A: [0, 0, 0], B: [0, 0, 0] },
      { I: 1, A: [1, 0, 0], B: [0, 1, 0] },
    ];
  }

  return {
    sampleFourierParametric,
    resampleClosedCurve,
    sampleFourierKnot,
    sampleIdealComponent,
    sampleKnotPlotComponent,
    sampleCatalogComponent,
    knotEntryComponents,
    normalizeComponents,
    sampleEntryThumb,
    unitCircleCoeffs,
    finiteMetaNumber,
  };
});
