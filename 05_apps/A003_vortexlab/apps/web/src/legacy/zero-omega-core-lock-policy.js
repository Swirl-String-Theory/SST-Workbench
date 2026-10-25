/* Zero-Ω Rankine core-flow lock policy (UI/coupling invariant; non-physics kernel). */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.VortexLabZeroOmegaCoreLockPolicy = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';

  const ZERO_OMEGA_EPS = 1e-12;
  const ZERO_OMEGA_UNLOCK_NOTICE =
    'koppeling automatisch ontgrendeld: Ω_wall=0 is niet verenigbaar met Γ≠0 bij eindige a_sim';

  /**
   * Legacy buggy behavior (pre-patch): silently force |Ω|=1 under core lock.
   * Kept only so regression tests can document the defect that was removed.
   */
  function legacyForceUnitOmega(P) {
    if (Math.abs(P.Om) >= ZERO_OMEGA_EPS) return false;
    P.Om = P.revOm ? -1 : 1;
    return true;
  }

  /**
   * Correct policy: Ω=0 is a valid user choice. Rankine lock |Γ|=2π a²|Ω|
   * cannot hold with Γ≠0 and finite a_sim, so unlock instead of rewriting Ω.
   *
   * @param {object} P mutable params with Om, revOm, coreFlowLock
   * @param {{lockCheckbox?: {checked:boolean}, setNotice?: (s:string)=>void}|undefined} ui
   * @returns {{handled:boolean, unlocked:boolean, notice:string|null}}
   */
  function applyZeroOmegaUnderCoreLock(P, ui) {
    if (!P || !P.coreFlowLock) {
      return { handled: false, unlocked: false, notice: null };
    }
    if (Math.abs(P.Om) >= ZERO_OMEGA_EPS) {
      return { handled: false, unlocked: false, notice: null };
    }
    P.coreFlowLock = false;
    if (typeof ui?.setNotice === 'function') ui.setNotice(ZERO_OMEGA_UNLOCK_NOTICE);
    if (ui?.lockCheckbox) ui.lockCheckbox.checked = false;
    return { handled: true, unlocked: true, notice: ZERO_OMEGA_UNLOCK_NOTICE };
  }

  return {
    ZERO_OMEGA_EPS,
    ZERO_OMEGA_UNLOCK_NOTICE,
    legacyForceUnitOmega,
    applyZeroOmegaUnderCoreLock,
  };
});
