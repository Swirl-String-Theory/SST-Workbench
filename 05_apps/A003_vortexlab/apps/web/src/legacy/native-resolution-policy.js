/* A003 native-XYZ/converted-XYZ resolution and visual tracer budget (non-physics policy). */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.VortexLabResolutionPolicy = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const XYZ_DERIVED_SOURCES = new Set(['xyz', 'twist', 'knotplot', 'ruben']);
  function positiveVertexCount(value) {
    const x = Number(value);
    return Number.isSafeInteger(x) && x >= 4 ? x : null;
  }
  function nativeComponentPoints(entry, component, index, source) {
    if (!XYZ_DERIVED_SOURCES.has(source) || !component) return null;
    // For session XYZ, the actual coordinate-buffer length takes precedence over metadata.
    if (source === 'xyz') {
      const p = component.points;
      if (!p || !Number.isSafeInteger(p.length / 3)) return null;
      return positiveVertexCount(p.length / 3);
    }
    // Converted XYZ catalogs (A006/KnotPlot): metadata records the original XYZ vertex count.
    // No claim is made about geometric fidelity beyond that of the Fourier reconstruction.
    return positiveVertexCount(component.pointCount) ??
      positiveVertexCount(entry?.pointsPerComponent?.[index]);
  }
  function requestedTracerCount(value) {
    return Math.max(0, Math.min(20000, Math.round(Number(value) || 0)));
  }
  function effectiveTracerCount(requested, nodes, options={}) {
    const n = requestedTracerCount(requested);
    const count = Math.max(0, Math.round(Number(nodes) || 0));
    const baselineNodes = options.baselineNodes || 288;
    const referenceTracers = options.referenceTracers || 5000;
    if (count <= baselineNodes) return n; // no regression for normal/legacy previews
    const budget = Math.max(64, Math.floor(referenceTracers * baselineNodes / count));
    return Math.min(n, budget);
  }
  return {nativeComponentPoints, requestedTracerCount, effectiveTracerCount};
});
