export const ENGINE_PROTOCOL_VERSION = 'vortexlab-engine/0.1';

export const BenchmarkKind = Object.freeze({
  SPEC_CLOCK: 'spec-clock',
  DECOMPOSITION: 'decomposition',
  HOLDOUT: 'holdout',
  CONTINUUM: 'continuum',
  REACH: 'reach'
});

export function assertEngineResponse(value) {
  if (!value || typeof value !== 'object') throw new TypeError('Engine response must be an object.');
  if (typeof value.engineVersion !== 'string') throw new TypeError('engineVersion is required.');
  if (!Array.isArray(value.gates)) throw new TypeError('gates must be an array.');
  return value;
}
