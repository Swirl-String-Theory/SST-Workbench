/**
 * Session XYZ centerline import for VortexLab.
 * Format matches build_knotplot_knots_data.parse_xyz_components:
 * finite x y z vertices; blank lines separate closed components;
 * non-numeric lines (e.g. "Component 0:") are skipped.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.VortexLabXyzImport = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function parseXyzText(text, fileName) {
    const name = String(fileName || 'import.xyz').trim() || 'import.xyz';
    if (typeof text !== 'string') {
      return { ok: false, error: `${name}: tekstinvoer ontbreekt` };
    }

    const components = [];
    let current = [];
    const lines = text.split(/\r?\n/);

    for (let lineNumber = 0; lineNumber < lines.length; lineNumber++) {
      const stripped = lines[lineNumber].trim();
      if (!stripped) {
        if (current.length) {
          components.push(current);
          current = [];
        }
        continue;
      }

      const fields = stripped.replace(/,/g, ' ').split(/\s+/).filter(Boolean);
      if (fields.length < 3) continue;

      const x = Number(fields[0]);
      const y = Number(fields[1]);
      const z = Number(fields[2]);
      // Non-numeric → skip (Python ValueError continue). Inf/NaN after numeric parse → reject.
      if (Number.isNaN(x) || Number.isNaN(y) || Number.isNaN(z)) continue;
      if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) {
        return { ok: false, error: `${name}:${lineNumber + 1}: niet-eindige coördinaat` };
      }
      current.push(x, y, z);
    }
    if (current.length) components.push(current);

    if (!components.length) {
      return { ok: false, error: `${name}: geen XYZ-componenten gevonden` };
    }
    for (let i = 0; i < components.length; i++) {
      const n = components[i].length / 3;
      if (n < 4) {
        return { ok: false, error: `${name}: component ${i + 1} heeft minder dan vier vertices` };
      }
    }

    const entryComponents = components.map((flat, i) => {
      const points = new Float64Array(flat);
      return {
        I: i + 1,
        pointCount: points.length / 3,
        points
      };
    });

    return {
      ok: true,
      entry: {
        knotId: name.replace(/\.xyz$/i, '') || name,
        sourceFile: name,
        sourceFormat: 'XYZ vertices; blank lines separate closed components',
        sourceRole: 'session-xyz-import',
        status: 'session-import',
        componentCount: entryComponents.length,
        components: entryComponents,
        pointsPerComponent: entryComponents.map((c) => c.pointCount),
        warning: 'Session XYZ-import: polygonal centerline, niet gecatalogiseerd en niet ideal/tight-gecertificeerd'
      }
    };
  }

  /**
   * Resample a closed polygonal component to n vertices.
   * @param {{points: Float64Array|number[], pointCount?: number}} component
   * @param {number} n
   * @param {(raw: Float64Array, n: number) => Float64Array} resampleClosedCurve
   */
  function sampleXyzComponent(component, n, resampleClosedCurve) {
    const raw = component?.points;
    if (!raw || !(raw.length >= 12)) {
      return new Float64Array(Math.max(0, 3 * (Number(n) || 0)));
    }
    const points = raw instanceof Float64Array ? raw : new Float64Array(raw);
    const nativeN = Math.floor(points.length / 3);
    const target = Math.max(4, Math.round(Number(n) || nativeN));
    if (target === nativeN) return points.slice ? points.slice() : new Float64Array(points);
    if (typeof resampleClosedCurve !== 'function') {
      throw new TypeError('sampleXyzComponent requires resampleClosedCurve');
    }
    return resampleClosedCurve(points, target);
  }

  return { parseXyzText, sampleXyzComponent };
});
