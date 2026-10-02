

"use strict";

const P = {
  Om: 1.0,
  Ga: 2.0e-3,
  a: 1.5e-3,
  off: 0.0,
  acc: 8,
  R0: 0.07,
  zA: 0.08, zB: 0.92,
  Rcyl: 0.25, Hcyl: 1.0,
  topology: "ring",
  knotId: "3:1:1",
  compA: 1,
  compB: 1,
  quality: "medium",
  qualityN: { low: 64, medium: 128, high: 256 },
  vzA: 0.0,
  vzB: 0.0,
  lockVz: true
};

const SUB_RING = "Twee coaxiale ringen, Γ instelbaar, frontaal · gedesingulariseerde Biot–Savart op kernlijnen";
const SUB_IDEAL = "Ideal-knoop uit Brian Gilbert Fourier · Γ instelbaar, frontaal · gedesingulariseerde Biot–Savart";

let knotN = 48;
let paused = false, tPhys = 0, flagged = "";
let VA, VB, KA, KB, TA, TB;

function vFromOmega(om) { return om * P.R0; }
function vFromGamma(ga) { return ga / (2 * Math.PI * P.R0); }
function fmtSpeed(v) {
  const c = Math.abs(v) * 100;
  return (c >= 10 ? c.toFixed(1) : c.toFixed(2)) + " cm/s";
}
function fmtGammaSlider(x) {
  const ga = x * 1e-3;
  return x.toFixed(1) + "·10⁻³ m²/s · v≈" + fmtSpeed(vFromGamma(ga));
}
function fmtOmegaSlider(x) {
  return x.toFixed(2) + " rad/s · v≈" + fmtSpeed(vFromOmega(x));
}
function updateHeaderOm() {
  document.getElementById("hOm").textContent =
    P.Om.toFixed(2) + " rad·s⁻¹ · " + fmtSpeed(vFromOmega(P.Om));
}

function currentKnotN() {
  return P.topology === "ring" ? 48 : P.qualityN[P.quality];
}

function allocBuffers() {
  const n3 = 3 * knotN;
  VA = new Float64Array(n3);
  VB = new Float64Array(n3);
  KA = new Float64Array(n3);
  KB = new Float64Array(n3);
  TA = new Float64Array(n3);
  TB = new Float64Array(n3);
}

function activeKnot() {
  return IDEAL_KNOT_DB[P.knotId] || IDEAL_KNOT_DB["3:1:1"];
}

function sampleFourierKnot(coeffs, n) {
  const x = new Float64Array(3 * n);
  for (let k = 0; k < n; k++) {
    const t = 2 * Math.PI * k / n;
    let px = 0, py = 0, pz = 0;
    for (const c of coeffs) {
      const ct = Math.cos(c.I * t), st = Math.sin(c.I * t);
      px += ct * c.A[0] + st * c.B[0];
      py += ct * c.A[1] + st * c.B[1];
      pz += ct * c.A[2] + st * c.B[2];
    }
    x[3 * k] = px;
    x[3 * k + 1] = py;
    x[3 * k + 2] = pz;
  }
  return x;
}

function makeIdealKnot(coeffs, z0, cx, ccw) {
  const raw = sampleFourierKnot(coeffs, knotN);
  let cx0 = 0, cy0 = 0, cz0 = 0;
  for (let k = 0; k < knotN; k++) {
    cx0 += raw[3 * k];
    cy0 += raw[3 * k + 1];
    cz0 += raw[3 * k + 2];
  }
  cx0 /= knotN; cy0 /= knotN; cz0 /= knotN;
  let rMax = 0;
  for (let k = 0; k < knotN; k++) {
    const dx = raw[3 * k] - cx0, dy = raw[3 * k + 1] - cy0;
    const r = Math.hypot(dx, dy);
    if (r > rMax) rMax = r;
  }
  const scale = P.R0 / Math.max(rMax, 1e-12);
  const x = new Float64Array(3 * knotN);
  for (let k = 0; k < knotN; k++) {
    const sk = ccw ? k : knotN - 1 - k;
    x[3 * k] = cx + (raw[3 * sk] - cx0) * scale;
    x[3 * k + 1] = (raw[3 * sk + 1] - cy0) * scale;
    x[3 * k + 2] = z0 + (raw[3 * sk + 2] - cz0) * scale;
  }
  return x;
}

function makeRing(z0, cx, ccw) {
  const x = new Float64Array(3 * knotN);
  for (let k = 0; k < knotN; k++) {
    const th = (ccw ? 1 : -1) * 2 * Math.PI * k / knotN;
    x[3 * k] = cx + P.R0 * Math.cos(th);
    x[3 * k + 1] = P.R0 * Math.sin(th);
    x[3 * k + 2] = z0;
  }
  return x;
}

function makeCarrierA() {
  if (P.topology === "ring") return makeRing(P.zA, 0, true);
  const knot = activeKnot();
  const ci = Math.max(1, Math.min(P.compA, knot.components.length)) - 1;
  return makeIdealKnot(knot.components[ci].coeffs, P.zA, 0, true);
}

function makeCarrierB() {
  if (P.topology === "ring") return makeRing(P.zB, P.off, false);
  const knot = activeKnot();
  const ci = Math.max(1, Math.min(P.compB, knot.components.length)) - 1;
  return makeIdealKnot(knot.components[ci].coeffs, P.zB, P.off, false);
}

let XA, XB;

function updateSubtitle() {
  if (P.topology === "ring") {
    document.getElementById("hSub").textContent = SUB_RING;
    document.getElementById("hRLbl").textContent = "R";
    document.getElementById("hRLblB").textContent = "R";
    return;
  }
  const k = activeKnot();
  document.getElementById("hSub").textContent =
    SUB_IDEAL + " · " + k.knotId + (k.conway ? " (" + k.conway + ")" : "");
  document.getElementById("hRLbl").textContent = "gem. ρ";
  document.getElementById("hRLblB").textContent = "gem. ρ";
}

function resetState() {
  XA = makeCarrierA();
  XB = makeCarrierB();
  tPhys = 0;
  flagged = "";
  hist.length = 0;
  document.getElementById("flag").style.display = "none";
  updateSubtitle();
  document.getElementById("hVz").textContent =
    (P.vzA * 1000).toFixed(1) + " / " + ((P.lockVz ? P.vzA : P.vzB) * 1000).toFixed(1) + " mm/s";
}

function applyZDrift(Va, Vb) {
  const vzB = P.lockVz ? P.vzA : P.vzB;
  for (let k = 0; k < knotN; k++) {
    Va[3 * k + 2] += P.vzA;
    Vb[3 * k + 2] += vzB;
  }
}

function computeVel(Xa, Xb, Va, Vb) {
  const N = knotN, a2 = P.a * P.a, pref = P.Ga / (4 * Math.PI);
  const rings = [Xa, Xb];
  const mid = [new Float64Array(3 * N), new Float64Array(3 * N)];
  const dl = [new Float64Array(3 * N), new Float64Array(3 * N)];
  for (let r = 0; r < 2; r++) {
    const X = rings[r];
    for (let k = 0; k < N; k++) {
      const k2 = (k + 1) % N;
      for (let d = 0; d < 3; d++) {
        mid[r][3 * k + d] = 0.5 * (X[3 * k + d] + X[3 * k2 + d]);
        dl[r][3 * k + d] = X[3 * k2 + d] - X[3 * k + d];
      }
    }
  }
  const V = [Va, Vb];
  let umax = 0;
  for (let rt = 0; rt < 2; rt++) {
    const Xt = rings[rt], Vt = V[rt];
    for (let i = 0; i < N; i++) {
      let ux = 0, uy = 0, uz = 0;
      const px = Xt[3 * i], py = Xt[3 * i + 1], pz = Xt[3 * i + 2];
      for (let rs = 0; rs < 2; rs++) {
        for (let j = 0; j < N; j++) {
          const rx = px - mid[rs][3 * j], ry = py - mid[rs][3 * j + 1], rz = pz - mid[rs][3 * j + 2];
          const r2 = rx * rx + ry * ry + rz * rz + a2;
          const inv = 1 / (r2 * Math.sqrt(r2));
          const dx = dl[rs][3 * j], dy = dl[rs][3 * j + 1], dz = dl[rs][3 * j + 2];
          ux += pref * (dy * rz - dz * ry) * inv;
          uy += pref * (dz * rx - dx * rz) * inv;
          uz += pref * (dx * ry - dy * rx) * inv;
        }
      }
      ux += -P.Om * py;
      uy += P.Om * px;
      Vt[3 * i] = ux;
      Vt[3 * i + 1] = uy;
      Vt[3 * i + 2] = uz;
      const um = Math.sqrt(ux * ux + uy * uy + uz * uz);
      if (um > umax) umax = um;
    }
  }
  applyZDrift(Va, Vb);
  return umax;
}

function stepRK2(dt) {
  const um1 = computeVel(XA, XB, VA, VB);
  const n3 = 3 * knotN;
  for (let i = 0; i < n3; i++) {
    TA[i] = XA[i] + dt * VA[i];
    TB[i] = XB[i] + dt * VB[i];
  }
  computeVel(TA, TB, KA, KB);
  for (let i = 0; i < n3; i++) {
    XA[i] += 0.5 * dt * (VA[i] + KA[i]);
    XB[i] += 0.5 * dt * (VB[i] + KB[i]);
  }
  return um1;
}

function ringStats(X) {
  let cx = 0, cy = 0, cz = 0;
  for (let k = 0; k < knotN; k++) {
    cx += X[3 * k]; cy += X[3 * k + 1]; cz += X[3 * k + 2];
  }
  cx /= knotN; cy /= knotN; cz /= knotN;
  let R = 0;
  for (let k = 0; k < knotN; k++) {
    const dx = X[3 * k] - cx, dy = X[3 * k + 1] - cy;
    R += Math.hypot(dx, dy);
  }
  return { R: R / knotN, z: cz };
}

function gauss(X1, X2, same) {
  const N = knotN;
  let S = 0;
  for (let i = 0; i < N; i++) {
    const i2 = (i + 1) % N;
    const ax = X1[3 * i], ay = X1[3 * i + 1], az = X1[3 * i + 2];
    const t1x = X1[3 * i2] - ax, t1y = X1[3 * i2 + 1] - ay, t1z = X1[3 * i2 + 2] - az;
    const m1x = ax + 0.5 * t1x, m1y = ay + 0.5 * t1y, m1z = az + 0.5 * t1z;
    for (let j = 0; j < N; j++) {
      if (same) {
        const dd = Math.abs(i - j);
        if (dd < 2 || dd > N - 2) continue;
      }
      const j2 = (j + 1) % N;
      const bx = X2[3 * j], by = X2[3 * j + 1], bz = X2[3 * j + 2];
      const t2x = X2[3 * j2] - bx, t2y = X2[3 * j2 + 1] - by, t2z = X2[3 * j2 + 2] - bz;
      const m2x = bx + 0.5 * t2x, m2y = by + 0.5 * t2y, m2z = bz + 0.5 * t2z;
      const rx = m1x - m2x, ry = m1y - m2y, rz = m1z - m2z;
      const r2 = rx * rx + ry * ry + rz * rz;
      if (r2 < 1e-12) continue;
      const cxx = t1y * t2z - t1z * t2y, cyy = t1z * t2x - t1x * t2z, czz = t1x * t2y - t1y * t2x;
      S += (cxx * rx + cyy * ry + czz * rz) / (r2 * Math.sqrt(r2));
    }
  }
  return S / (4 * Math.PI);
}

function minGap() {
  let m = 1e9;
  for (let i = 0; i < knotN; i++) {
    for (let j = 0; j < knotN; j++) {
      const dx = XA[3 * i] - XB[3 * j], dy = XA[3 * i + 1] - XB[3 * j + 1], dz = XA[3 * i + 2] - XB[3 * j + 2];
      const d = dx * dx + dy * dy + dz * dz;
      if (d < m) m = d;
    }
  }
  return Math.sqrt(m);
}

const canvas = document.getElementById("c3d");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0B1020);
const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 20);
let camTh = 0.9, camPh = 1.15, camD = 1.6, camTarget = new THREE.Vector3(0, 0, 0.5);

function updCam() {
  camera.position.set(
    camTarget.x + camD * Math.sin(camPh) * Math.cos(camTh),
    camTarget.y + camD * Math.sin(camPh) * Math.sin(camTh),
    camTarget.z + camD * Math.cos(camPh));
  camera.up.set(0, 0, 1);
  camera.lookAt(camTarget);
}

const cylGeo = new THREE.CylinderGeometry(P.Rcyl, P.Rcyl, P.Hcyl, 48, 1, true);
cylGeo.rotateX(Math.PI / 2);
cylGeo.translate(0, 0, 0.5);
scene.add(new THREE.Mesh(cylGeo, new THREE.MeshBasicMaterial({
  color: 0x1E2C4A, wireframe: true, transparent: true, opacity: 0.35
})));

const latticeGrp = new THREE.Group();
scene.add(latticeGrp);
(function () {
  const mat = new THREE.LineBasicMaterial({ color: 0x2A4A7A, transparent: true, opacity: 0.5 });
  for (let n = 0; n < 26; n++) {
    const r = P.Rcyl * Math.sqrt(Math.random()) * 0.95, th = Math.random() * 2 * Math.PI;
    latticeGrp.add(new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(r * Math.cos(th), r * Math.sin(th), 0),
        new THREE.Vector3(r * Math.cos(th), r * Math.sin(th), 1)
      ]), mat));
  }
})();

function gun(z, flip, color) {
  const g = new THREE.ConeGeometry(0.02, 0.05, 16);
  g.rotateX(flip ? Math.PI / 2 : -Math.PI / 2);
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color }));
  m.position.set(0, 0, z);
  scene.add(m);
}
gun(0.01, false, 0xFFAE45);
gun(0.99, true, 0x55D6FF);

let lineA, lineB;

function ringLine(color) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(3 * (knotN + 1)), 3));
  return new THREE.Line(geo, new THREE.LineBasicMaterial({ color, linewidth: 2 }));
}

function rebuildLines() {
  if (lineA) { scene.remove(lineA); lineA.geometry.dispose(); lineA.material.dispose(); }
  if (lineB) { scene.remove(lineB); lineB.geometry.dispose(); lineB.material.dispose(); }
  lineA = ringLine(0xFFAE45);
  lineB = ringLine(0x55D6FF);
  scene.add(lineA);
  scene.add(lineB);
}

function pushRing(line, X) {
  const p = line.geometry.attributes.position.array;
  for (let k = 0; k <= knotN; k++) {
    const s = (k % knotN) * 3;
    p[3 * k] = X[s]; p[3 * k + 1] = X[s + 1]; p[3 * k + 2] = X[s + 2];
  }
  line.geometry.attributes.position.needsUpdate = true;
}

let drag = false, lx = 0, ly = 0;
canvas.addEventListener("pointerdown", e => { drag = true; lx = e.clientX; ly = e.clientY; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener("pointermove", e => {
  if (!drag) return;
  camTh -= (e.clientX - lx) * 0.008;
  camPh = Math.min(2.9, Math.max(0.2, camPh - (e.clientY - ly) * 0.008));
  lx = e.clientX; ly = e.clientY;
});
canvas.addEventListener("pointerup", () => drag = false);
canvas.addEventListener("wheel", e => { e.preventDefault(); camD = Math.min(4, Math.max(0.4, camD * (1 + 0.001 * e.deltaY))); }, { passive: false });

const hist = [];
const sctx = document.getElementById("cspark").getContext("2d");

function drawSpark() {
  const w = 220, h = 72;
  sctx.clearRect(0, 0, w, h);
  sctx.fillStyle = "#6F82A0";
  sctx.font = "9px monospace";
  sctx.fillText("R_A, R_B (—)  Δz (··)", 4, 10);
  if (hist.length < 2) return;
  const t0 = hist[0].t, t1 = hist[hist.length - 1].t || 1;
  const Rmax = Math.max(0.1, ...hist.map(p => Math.max(p.RA, p.RB)));
  const Zmax = Math.max(0.1, ...hist.map(p => p.dz));
  function line(key, color, dash, vmax) {
    sctx.strokeStyle = color; sctx.setLineDash(dash); sctx.beginPath();
    hist.forEach((p, i) => {
      const x = 4 + (w - 8) * (p.t - t0) / Math.max(1e-9, t1 - t0);
      const y = h - 4 - (h - 18) * (p[key] / vmax);
      i ? sctx.lineTo(x, y) : sctx.moveTo(x, y);
    });
    sctx.stroke(); sctx.setLineDash([]);
  }
  line("RA", "#FFAE45", [], Rmax);
  line("RB", "#55D6FF", [], Rmax);
  line("dz", "#C9D6E3", [3, 3], Zmax);
}

function fillKnotSelect() {
  const sel = document.getElementById("knotSelect");
  sel.innerHTML = "";
  for (const id of IDEAL_KNOT_IDS) {
    const k = IDEAL_KNOT_DB[id];
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = id + (k.conway ? " · " + k.conway : "") +
      (k.components.length > 1 ? " [" + k.components.length + " comp]" : "");
    if (id === P.knotId) opt.selected = true;
    sel.appendChild(opt);
  }
}

function fillCompSelect(selId, compVal) {
  const sel = document.getElementById(selId);
  const knot = activeKnot();
  const n = knot.components.length;
  sel.innerHTML = "";
  for (let i = 1; i <= n; i++) {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = "comp " + i;
    if (i === compVal) opt.selected = true;
    sel.appendChild(opt);
  }
}

function syncCompUi() {
  const knot = activeKnot();
  const multi = knot.components.length > 1;
  document.getElementById("compRow").classList.toggle("hidden", !multi);
  if (multi) {
    fillCompSelect("compA", P.compA);
    fillCompSelect("compB", P.compB);
  } else {
    P.compA = 1; P.compB = 1;
  }
}

function syncTopoUi() {
  document.querySelectorAll("#topoSeg .seg-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.topo === P.topology);
  });
  const ideal = P.topology === "ideal";
  document.getElementById("knotRow").classList.toggle("hidden", !ideal);
  document.getElementById("qualSeg").classList.toggle("disabled", !ideal);
  document.querySelectorAll("#qualSeg .seg-btn").forEach(btn => { btn.disabled = !ideal; });
  if (ideal) syncCompUi();
  else document.getElementById("compRow").classList.add("hidden");
}

function syncQualityUi() {
  document.querySelectorAll("#qualSeg .seg-btn").forEach(btn => {
    btn.classList.toggle("active", P.topology === "ideal" && btn.dataset.qual === P.quality);
  });
}

function syncVzUi() {
  const lock = P.lockVz;
  document.getElementById("lockVz").checked = lock;
  document.getElementById("sVzB").disabled = lock;
  document.getElementById("vzBWrap").style.opacity = lock ? "0.45" : "1";
  if (lock) P.vzB = P.vzA;
}

function reinitSimulation() {
  knotN = currentKnotN();
  allocBuffers();
  rebuildLines();
  syncTopoUi();
  syncQualityUi();
  syncVzUi();
  resetState();
}

function bind(id, fmt, set) {
  const s = document.getElementById("s" + id), v = document.getElementById("v" + id);
  s.addEventListener("input", () => {
    const x = parseFloat(s.value);
    set(x);
    v.textContent = fmt(x);
  });
}

bind("Om", fmtOmegaSlider, x => { P.Om = x; updateHeaderOm(); });
bind("Ga", fmtGammaSlider, x => P.Ga = x * 1e-3);
bind("A", x => x.toFixed(1) + " mm", x => P.a = x * 1e-3);
bind("Off", x => x.toFixed(0) + " mm", x => { P.off = x * 1e-3; resetState(); });
bind("Acc", x => x.toFixed(0) + "×", x => P.acc = x);
bind("VzA", x => (x).toFixed(0) + " mm/s", x => {
  P.vzA = x * 1e-3;
  if (P.lockVz) { P.vzB = P.vzA; document.getElementById("sVzB").value = x; document.getElementById("vVzB").textContent = (x).toFixed(0) + " mm/s"; }
});
bind("VzB", x => (x).toFixed(0) + " mm/s", x => { if (!P.lockVz) P.vzB = x * 1e-3; });

document.getElementById("topoSeg").addEventListener("click", e => {
  const btn = e.target.closest("[data-topo]");
  if (!btn || btn.dataset.topo === P.topology) return;
  P.topology = btn.dataset.topo;
  reinitSimulation();
});
document.getElementById("qualSeg").addEventListener("click", e => {
  const btn = e.target.closest("[data-qual]");
  if (!btn || btn.disabled || btn.dataset.qual === P.quality) return;
  P.quality = btn.dataset.qual;
  reinitSimulation();
});
document.getElementById("knotSelect").addEventListener("change", e => {
  P.knotId = e.target.value;
  P.compA = 1; P.compB = Math.min(2, activeKnot().components.length);
  syncCompUi();
  resetState();
});
document.getElementById("compA").addEventListener("change", e => { P.compA = parseInt(e.target.value, 10); resetState(); });
document.getElementById("compB").addEventListener("change", e => { P.compB = parseInt(e.target.value, 10); resetState(); });
document.getElementById("lockVz").addEventListener("change", e => {
  P.lockVz = e.target.checked;
  syncVzUi();
  if (P.lockVz) { P.vzB = P.vzA; document.getElementById("sVzB").value = P.vzA * 1000; document.getElementById("vVzB").textContent = (P.vzA * 1000).toFixed(0) + " mm/s"; }
});
document.getElementById("bPause").addEventListener("click", e => { paused = !paused; e.target.textContent = paused ? "Hervat" : "Pauzeer"; });
document.getElementById("bReset").addEventListener("click", resetState);

function setFlag(msg) {
  flagged = msg;
  const f = document.getElementById("flag");
  f.textContent = msg;
  f.style.display = "block";
}

fillKnotSelect();
updateHeaderOm();
document.getElementById("vOm").textContent = fmtOmegaSlider(P.Om);
document.getElementById("vGa").textContent = fmtGammaSlider(P.Ga * 1000);
reinitSimulation();
updCam();
let lastT = performance.now(), frame = 0, lastUmax = 0.02;

function loop(now) {
  requestAnimationFrame(loop);
  const dtReal = Math.min(0.05, (now - lastT) / 1000);
  lastT = now;
  if (!paused && !flagged) {
    let budget = P.acc * dtReal, guard = 0;
    while (budget > 1e-6 && guard < 40) {
      const umax = Math.max(1e-6, lastUmax);
      const dt = Math.min(0.03, 0.3 * P.a / umax, budget);
      lastUmax = stepRK2(dt);
      tPhys += dt;
      budget -= dt;
      guard++;
    }
    const gap = minGap();
    const sA = ringStats(XA), sB = ringStats(XB);
    if (gap < 3 * P.a) {
      setFlag("⚠ kernen binnen 3a — reconnectieregime bereikt; filamentmodel niet langer geldig. Reset om opnieuw te draaien.");
    } else if (Math.max(sA.R, sB.R) > 0.9 * P.Rcyl) {
      setFlag("⚠ filament nadert cilinderwand — wandbeelden niet gemodelleerd.");
    }
  }
  latticeGrp.rotation.z = P.Om * tPhys;
  pushRing(lineA, XA);
  pushRing(lineB, XB);
  if (frame % 3 === 0) {
    const sA = ringStats(XA), sB = ringStats(XB);
    const Wr = gauss(XA, XA, true) + gauss(XB, XB, true);
    const Lk = gauss(XA, XB, false);
    const H = Wr + 2 * Lk;
    document.getElementById("hHel").textContent = H.toFixed(3);
    document.getElementById("hHel").style.color = Math.abs(H) < 0.02 ? "#7BE8A8" : "#FFAE45";
    document.getElementById("hWr").textContent = Wr.toFixed(3);
    document.getElementById("hLk").textContent = Lk.toFixed(3);
    document.getElementById("hWrel").textContent = (2 * P.Om).toFixed(2) + " s⁻¹ ẑ";
    document.getElementById("hR").textContent = (sA.R * 100).toFixed(1) + " / " + (sB.R * 100).toFixed(1) + " cm";
    document.getElementById("hDz").textContent = (Math.abs(sB.z - sA.z) * 100).toFixed(1) + " cm";
    document.getElementById("hVz").textContent =
      (P.vzA * 1000).toFixed(1) + " / " + ((P.lockVz ? P.vzA : P.vzB) * 1000).toFixed(1) + " mm/s";
    document.getElementById("hT").textContent = tPhys.toFixed(1) + " s";
    hist.push({ t: tPhys, RA: sA.R, RB: sB.R, dz: Math.abs(sB.z - sA.z) });
    if (hist.length > 400) hist.shift();
    if (hist.length > 5) {
      const p = hist[hist.length - 5], q = hist[hist.length - 1];
      const v = (p.dz - q.dz) / Math.max(1e-9, q.t - p.t);
      document.getElementById("hV").textContent = (v * 1000).toFixed(1) + " mm/s";
    }
    drawSpark();
  }
  frame++;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w || canvas.height !== h) {
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  updCam();
  renderer.render(scene, camera);
}

requestAnimationFrame(loop);

