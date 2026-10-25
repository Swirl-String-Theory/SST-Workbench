export const ENGINE_PROTOCOL_VERSION = 'vortexlab-engine/0.1';
export const PHYSICS_PROTOCOL_VERSION = 'vortexlab-physics/0.1';

export const BenchmarkKind = Object.freeze({
  SPEC_CLOCK: 'spec-clock',
  DECOMPOSITION: 'decomposition',
  HOLDOUT: 'holdout',
  CONTINUUM: 'continuum',
  REACH: 'reach'
});

export const PhysicsMethod = Object.freeze({
  HEALTH: 'health',
  FILAMENT_VELOCITY: 'filament.velocity',
  FILAMENT_RK4: 'filament.rk4'
});

export function assertEngineResponse(value) {
  if (!value || typeof value !== 'object') throw new TypeError('Engine response must be an object.');
  if (typeof value.engineVersion !== 'string') throw new TypeError('engineVersion is required.');
  if (!Array.isArray(value.gates)) throw new TypeError('gates must be an array.');
  return value;
}

/** @param {unknown} value */
export function assertPhysicsRequest(value) {
  if (!value || typeof value !== 'object') throw new TypeError('Physics request must be an object.');
  if (value.protocolVersion !== PHYSICS_PROTOCOL_VERSION) {
    throw new TypeError(`protocolVersion must be ${PHYSICS_PROTOCOL_VERSION}`);
  }
  if (!Object.values(PhysicsMethod).includes(value.method)) {
    throw new TypeError(`unknown physics method: ${value.method}`);
  }
  return value;
}

/** @param {unknown} value */
export function assertPhysicsResponse(value) {
  if (!value || typeof value !== 'object') throw new TypeError('Physics response must be an object.');
  if (value.protocolVersion !== PHYSICS_PROTOCOL_VERSION) {
    throw new TypeError(`protocolVersion must be ${PHYSICS_PROTOCOL_VERSION}`);
  }
  if (typeof value.ok !== 'boolean') throw new TypeError('ok must be boolean.');
  if (typeof value.engine !== 'string') throw new TypeError('engine is required.');
  return value;
}

/**
 * @param {object} partial
 * @returns {object}
 */
export function makePhysicsRequest(partial) {
  return {
    protocolVersion: PHYSICS_PROTOCOL_VERSION,
    requestId: partial.requestId || `req-${Date.now()}`,
    method: partial.method,
    filaments: partial.filaments || [],
    dt: partial.dt,
    options: partial.options || {}
  };
}
