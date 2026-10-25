/**
 * Browser EngineClient for the companion sst-core physics-server.
 * Uses synchronous XHR so the existing RK4 animation loop stays sync.
 * On failure/timeout the runtime falls back to the JS velocityCore path.
 */
(function (global) {
  'use strict';

  const PROTOCOL = 'vortexlab-physics/0.1';
  const DEFAULT_URL = 'http://127.0.0.1:4174';
  const STORAGE_KEY = 'vortexlab.nativeSstcore';

  function resolveUrl() {
    try {
      if (global.SSTCORE_PHYSICS_URL) return String(global.SSTCORE_PHYSICS_URL).replace(/\/+$/, '');
    } catch (_) { /* ignore */ }
    return DEFAULT_URL;
  }

  function readStoredEnabled() {
    try {
      const v = global.localStorage && global.localStorage.getItem(STORAGE_KEY);
      return v === '1' || v === 'true';
    } catch (_) {
      return false;
    }
  }

  function writeStoredEnabled(on) {
    try {
      if (global.localStorage) global.localStorage.setItem(STORAGE_KEY, on ? '1' : '0');
    } catch (_) { /* ignore */ }
  }

  const Engine = {
    protocolVersion: PROTOCOL,
    url: resolveUrl(),
    enabled: readStoredEnabled(),
    online: false,
    lastError: null,
    lastHealth: null,
    engineVersion: null,
    isNative: false,
    timeoutMs: 250,
    stats: {
      nativeSteps: 0,
      fallbackSteps: 0,
      healthFails: 0,
      lastElapsedMs: null
    },

    wantNative() {
      return !!(this.enabled && this.online);
    },

    setEnabled(on) {
      this.enabled = !!on;
      writeStoredEnabled(this.enabled);
      if (this.enabled) this.probeHealth();
      this._emitStatus();
      if (global.ModelLog && global.ModelLog.logEvent) {
        global.ModelLog.logEvent('sstcore-native-toggle', {
          enabled: this.enabled,
          online: this.online,
          url: this.url,
          engineVersion: this.engineVersion,
          isNative: this.isNative
        });
      }
    },

    _emitStatus() {
      const el = global.document && global.document.getElementById('nativeSstcoreStatus');
      if (!el) return;
      if (!this.enabled) {
        el.textContent = 'uit · JS Biot–Savart';
        return;
      }
      if (!this.online) {
        el.textContent = `aan · server offline (${this.url}) · JS-fallback`;
        return;
      }
      const eng = this.isNative ? 'native C++' : 'sst-core';
      el.textContent = `aan · ${eng} ${this.engineVersion || ''} · steps ${this.stats.nativeSteps}`;
    },

    _syncRequest(method, path, body, timeoutMs) {
      const xhr = new XMLHttpRequest();
      const url = `${this.url}${path}`;
      xhr.open(method, url, false);
      xhr.setRequestHeader('Content-Type', 'application/json');
      const ms = timeoutMs != null ? timeoutMs : this.timeoutMs;
      try {
        xhr.timeout = ms;
      } catch (_) { /* sync XHR may ignore timeout in some browsers */ }
      const payload = body == null ? null : JSON.stringify(body);
      try {
        xhr.send(payload);
      } catch (err) {
        this.lastError = String(err && err.message ? err.message : err);
        return null;
      }
      if (xhr.status < 200 || xhr.status >= 300) {
        this.lastError = `HTTP ${xhr.status}: ${xhr.responseText.slice(0, 200)}`;
        return null;
      }
      try {
        return JSON.parse(xhr.responseText);
      } catch (err) {
        this.lastError = `invalid JSON: ${err.message}`;
        return null;
      }
    },

    probeHealth() {
      this.url = resolveUrl();
      const res = this._syncRequest('GET', '/health', null, 400);
      if (!res || !res.ok) {
        this.online = false;
        this.stats.healthFails += 1;
        this.lastHealth = res;
        this._emitStatus();
        return false;
      }
      this.online = true;
      this.lastHealth = res;
      this.engineVersion = res.engineVersion || null;
      this.isNative = !!res.isNative;
      this.lastError = null;
      this._emitStatus();
      return true;
    },

    rk4StepSync(filaments, dt, options) {
      if (!this.wantNative()) return null;
      const body = {
        protocolVersion: PROTOCOL,
        requestId: `rk4-${Date.now()}`,
        method: 'filament.rk4',
        filaments,
        dt,
        options: options || {}
      };
      const res = this._syncRequest('POST', '/filament/rk4', body);
      if (!res || !res.ok || !Array.isArray(res.filaments)) {
        this.stats.fallbackSteps += 1;
        if (this.stats.fallbackSteps <= 3 || this.stats.fallbackSteps % 60 === 0) {
          if (global.ModelLog && global.ModelLog.logEvent) {
            global.ModelLog.logEvent('sstcore-native-fallback', {
              error: this.lastError,
              fallbackSteps: this.stats.fallbackSteps
            });
          }
        }
        return null;
      }
      this.stats.nativeSteps += 1;
      this.stats.lastElapsedMs = res.elapsedMs;
      this.lastError = null;
      if (this.stats.nativeSteps === 1 || this.stats.nativeSteps % 120 === 0) this._emitStatus();
      return res;
    },

    velocitySync(filaments, options) {
      if (!this.wantNative()) return null;
      const body = {
        protocolVersion: PROTOCOL,
        requestId: `vel-${Date.now()}`,
        method: 'filament.velocity',
        filaments,
        options: options || {}
      };
      const res = this._syncRequest('POST', '/filament/velocity', body);
      if (!res || !res.ok) {
        this.stats.fallbackSteps += 1;
        return null;
      }
      this.stats.lastElapsedMs = res.elapsedMs;
      return res;
    },

    bindUi() {
      const cb = global.document && global.document.getElementById('cNativeSstcore');
      if (cb) {
        cb.checked = !!this.enabled;
        cb.addEventListener('change', () => this.setEnabled(cb.checked));
      }
      this._emitStatus();
      if (this.enabled) {
        // Deferred probe so first paint is not blocked; animation loop will re-probe.
        setTimeout(() => this.probeHealth(), 50);
      }
    }
  };

  global.VortexLabEngine = Engine;
  if (global.document && global.document.readyState === 'loading') {
    global.document.addEventListener('DOMContentLoaded', () => Engine.bindUi());
  } else {
    setTimeout(() => Engine.bindUi(), 0);
  }
})(typeof window !== 'undefined' ? window : globalThis);
