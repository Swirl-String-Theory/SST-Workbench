/**
 * Bridge: koppelt geëxtraheerde modules aan de legacy inline API.
 * Import in vortexring-lab-app.js vóór gebruik van Y/fils globals.
 */
import * as Vec from '../physics/vec3.js';
import * as Topology from '../physics/topology.js';
import * as Contact from '../physics/contact.js';
import * as Timestep from '../physics/timestep.js';
import * as SST from '../physics/sst-similarity.js';
import * as Body from '../physics/body-frame.js';
import * as Stability from '../diagnostics/stability.js';
import * as Conservation from '../diagnostics/conservation.js';

export const VortexModules = {
  Vec,
  Topology,
  Contact,
  Timestep,
  SST,
  Body,
  Stability,
  Conservation,
};

/** Installeert module-backed wrappers op window voor geleidelijke migratie. */
export function installModuleBridge() {
  window.VortexModules = VortexModules;
  return VortexModules;
}

export function gaussFromY(Y, o1, N1, o2, N2, same, absMode) {
  return Topology.gaussIntegral(Y, o1, N1, o2, N2, same, absMode);
}

export function pointAtY(Y, o, idx) {
  return Vec.pointAt(Y, o, idx);
}

export function segmentGap(Y, f1, f2) {
  return Contact.minGapBetweenFilaments(Y, f1, f2);
}

export function selfGap(Y, f) {
  return Contact.dminSelf(Y, f);
}

export function chiHat(Y, f, isRing) {
  return Body.chiHatFromFilament(Y, f, { isRing });
}

export function bodyState(Y, f, V, isRing) {
  return Body.bodyFrameState(Y, f, V, { isRing });
}

export { Vec, Topology, Contact, Timestep, SST, Body, Stability, Conservation };
