/* SST 3D Collider — Biot–Savart physics engine */
"use strict";

window.SSTPhysics = (function () {
    const SUB_RING = "Ringen (0₁) · Biot–Savart op kernlijnen";
    const SUB_TREFOIL = "Ideal-trefoils (3₁), Fourier parameters · Biot–Savart";
    const SUB_IDEAL = "Ideal-knoop uit Brian Gilbert Fourier · Biot–Savart";

    const P = {
        Om: 1.0,
        GaMag: 2.0e-3,
        a: 1.5e-3,
        off: 0.0,
        mirrorB: false,
        acc: 8,
        R0: 0.07,
        zA: 0.08,
        zB: 0.92,
        Rcyl: 1.0,
        Hcyl: 1.0,
        topology: "ring",
        knotId: "3:1:1",
        compA: 1,
        compB: 1,
        quality: "medium",
        count: 2,
        qualityN: { low: 64, medium: 128, high: 256 },
        ccwA: true,
        ccwB: false,
        vzA: 0.0,
        vzB: 0.0,
        lockVz: true,
        coreModel: "solid"
    };

    const Flags = { alpha: false, beta: false, sep: false, gamma: false };

    let knotN = 48;
    let paused = false;
    let tPhys = 0;
    let flagged = "";
    let refFrame = "lab";

    let VA, VB, KA, KB, TA, TB, XA, XB;
    const hist = [];

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
        if (typeof IDEAL_KNOT_DB === "undefined") return null;
        return IDEAL_KNOT_DB[P.knotId] || IDEAL_KNOT_DB["3:1:1"];
    }

    function trefoilCoeffs() {
        if (typeof IDEAL_KNOT_DB !== "undefined" && IDEAL_KNOT_DB["3:1:1"]) {
            return IDEAL_KNOT_DB["3:1:1"].components[0].coeffs;
        }
        const k = activeKnot();
        if (k && k.components && k.components[0]) return k.components[0].coeffs;
        return [];
    }

    function sampleFourierKnot(coeffs, n) {
        const x = new Float64Array(3 * n);
        for (let k = 0; k < n; k++) {
            const t = (2 * Math.PI * k) / n;
            let px = 0, py = 0, pz = 0;
            for (const c of coeffs) {
                const ct = Math.cos(c.I * t);
                const st = Math.sin(c.I * t);
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

    function scaleFourierKnot(raw, z0, cx, ccw) {
        let cx0 = 0, cy0 = 0, cz0 = 0;
        for (let k = 0; k < knotN; k++) {
            cx0 += raw[3 * k];
            cy0 += raw[3 * k + 1];
            cz0 += raw[3 * k + 2];
        }
        cx0 /= knotN;
        cy0 /= knotN;
        cz0 /= knotN;
        let rMax = 0;
        for (let k = 0; k < knotN; k++) {
            const dx = raw[3 * k] - cx0;
            const dy = raw[3 * k + 1] - cy0;
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

    function makeIdealKnot(coeffs, z0, cx, ccw) {
        return scaleFourierKnot(sampleFourierKnot(coeffs, knotN), z0, cx, ccw);
    }

    function makeTrefoil(z0, cx, ccw) {
        return makeIdealKnot(trefoilCoeffs(), z0, cx, ccw);
    }

    function makeRing(z0, cx, ccw) {
        const x = new Float64Array(3 * knotN);
        for (let k = 0; k < knotN; k++) {
            const th = (ccw ? 1 : -1) * (2 * Math.PI * k) / knotN;
            x[3 * k] = cx + P.R0 * Math.cos(th);
            x[3 * k + 1] = P.R0 * Math.sin(th);
            x[3 * k + 2] = z0;
        }
        return x;
    }

    function makeCarrier(z0, cx, ccw, which) {
        if (P.topology === "ring") return makeRing(z0, cx, ccw);
        if (P.topology === "trefoil") return makeTrefoil(z0, cx, ccw);
        const knot = activeKnot();
        if (!knot) return makeRing(z0, cx, ccw);
        const comp = which === "A" ? P.compA : P.compB;
        const ci = Math.max(1, Math.min(comp, knot.components.length)) - 1;
        return makeIdealKnot(knot.components[ci].coeffs, z0, cx, ccw);
    }

    function offsetB() {
        return P.mirrorB ? -P.off : P.off;
    }

    function ringSign(index) {
        return (index === 0 ? P.ccwA : P.ccwB) ? 1 : -1;
    }

    function applyZDrift(Va, Vb) {
        const vzB = P.lockVz ? P.vzA : P.vzB;
        for (let k = 0; k < knotN; k++) {
            if (isFinite(P.vzA)) Va[3 * k + 2] += P.vzA;
            if (P.count === 2 && isFinite(vzB)) Vb[3 * k + 2] += vzB;
        }
    }

    function computeVel(Xa, Xb, Va, Vb) {
        const N = knotN;
        const a2 = P.a * P.a;
        const base = P.GaMag / (4 * Math.PI);
        const ringCount = P.count;
        const rings = ringCount === 1 ? [Xa] : [Xa, Xb];
        const mid = ringCount === 1
            ? [new Float64Array(3 * N)]
            : [new Float64Array(3 * N), new Float64Array(3 * N)];
        const dl = ringCount === 1
            ? [new Float64Array(3 * N)]
            : [new Float64Array(3 * N), new Float64Array(3 * N)];

        for (let r = 0; r < ringCount; r++) {
            const X = rings[r];
            for (let k = 0; k < N; k++) {
                const k2 = (k + 1) % N;
                for (let d = 0; d < 3; d++) {
                    mid[r][3 * k + d] = 0.5 * (X[3 * k + d] + X[3 * k2 + d]);
                    dl[r][3 * k + d] = X[3 * k2 + d] - X[3 * k + d];
                }
            }
        }

        const V = ringCount === 1 ? [Va] : [Va, Vb];
        let umax = 0;

        for (let rt = 0; rt < ringCount; rt++) {
            const Xt = rings[rt];
            const Vt = V[rt];
            for (let i = 0; i < N; i++) {
                let ux = 0, uy = 0, uz = 0;
                const px = Xt[3 * i];
                const py = Xt[3 * i + 1];
                const pz = Xt[3 * i + 2];
                for (let rs = 0; rs < ringCount; rs++) {
                    const pref = base * ringSign(rs);
                    for (let j = 0; j < N; j++) {
                        const rx = px - mid[rs][3 * j];
                        const ry = py - mid[rs][3 * j + 1];
                        const rz = pz - mid[rs][3 * j + 2];
                        const r2 = rx * rx + ry * ry + rz * rz + a2;
                        const inv = 1 / (r2 * Math.sqrt(r2));
                        const dx = dl[rs][3 * j];
                        const dy = dl[rs][3 * j + 1];
                        const dz = dl[rs][3 * j + 2];
                        ux += pref * (dy * rz - dz * ry) * inv;
                        uy += pref * (dz * rx - dx * rz) * inv;
                        uz += pref * (dx * ry - dy * rx) * inv;
                    }
                }
                ux += -P.Om * py;
                uy += P.Om * px;
                if (isFinite(ux)) Vt[3 * i] = ux; else Vt[3 * i] = 0;
                if (isFinite(uy)) Vt[3 * i + 1] = uy; else Vt[3 * i + 1] = 0;
                if (isFinite(uz)) Vt[3 * i + 2] = uz; else Vt[3 * i + 2] = 0;
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
            if (P.count === 2) TB[i] = XB[i] + dt * VB[i];
        }
        computeVel(TA, TB, KA, KB);
        for (let i = 0; i < n3; i++) {
            XA[i] += 0.5 * dt * (VA[i] + KA[i]);
            if (P.count === 2) XB[i] += 0.5 * dt * (VB[i] + KB[i]);
            if (!isFinite(XA[i])) {
                flagged = "NaN in drager A";
                return Infinity;
            }
            if (P.count === 2 && !isFinite(XB[i])) {
                flagged = "NaN in drager B";
                return Infinity;
            }
        }
        return um1;
    }

    function ringStats(X) {
        let cx = 0, cy = 0, cz = 0;
        for (let k = 0; k < knotN; k++) {
            cx += X[3 * k];
            cy += X[3 * k + 1];
            cz += X[3 * k + 2];
        }
        cx /= knotN;
        cy /= knotN;
        cz /= knotN;
        let R = 0;
        for (let k = 0; k < knotN; k++) {
            R += Math.hypot(X[3 * k] - cx, X[3 * k + 1] - cy);
        }
        return { R: R / knotN, z: cz, cx, cy, cz };
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
                const cxx = t1y * t2z - t1z * t2y;
                const cyy = t1z * t2x - t1x * t2z;
                const czz = t1x * t2y - t1y * t2x;
                S += (cxx * rx + cyy * ry + czz * rz) / (r2 * Math.sqrt(r2));
            }
        }
        return S / (4 * Math.PI);
    }

    function minGap() {
        if (P.count === 1) return 1e9;
        let m = 1e9;
        for (let i = 0; i < knotN; i++) {
            for (let j = 0; j < knotN; j++) {
                const dx = XA[3 * i] - XB[3 * j];
                const dy = XA[3 * i + 1] - XB[3 * j + 1];
                const dz = XA[3 * i + 2] - XB[3 * j + 2];
                const d = dx * dx + dy * dy + dz * dz;
                if (d < m) m = d;
            }
        }
        return Math.sqrt(m);
    }

    function subtitle() {
        if (P.count === 1) {
            if (P.topology === "ideal") {
                const k = activeKnot();
                return "Eén centrale ideal-knoop · " + (k ? k.knotId : P.knotId) + " · Biot–Savart";
            }
            if (P.topology === "trefoil") {
                return "Eén centrale ideal-trefoil (3₁) · Biot–Savart geprojecteerd op z-as";
            }
            return "Eén centrale ring (0₁) · Biot–Savart geprojecteerd op z-as";
        }
        if (P.topology === "ideal") {
            const k = activeKnot();
            return SUB_IDEAL + " · " + (k ? k.knotId : P.knotId) +
                (k && k.conway ? " (" + k.conway + ")" : "");
        }
        if (P.topology === "trefoil") return SUB_TREFOIL;
        return SUB_RING;
    }

    function resetState() {
        if (P.count === 1) {
            XA = makeCarrier(0.5, 0, P.ccwA, "A");
            XB = new Float64Array(3 * knotN);
        } else {
            XA = makeCarrier(P.zA, 0, P.ccwA, "A");
            XB = makeCarrier(P.zB, offsetB(), P.ccwB, "B");
        }
        tPhys = 0;
        flagged = "";
        hist.length = 0;
    }

    function reinitSimulation() {
        knotN = currentKnotN();
        allocBuffers();
        resetState();
    }

    function signedGammaB() {
        return (P.ccwB ? 1 : -1) * P.GaMag;
    }

    function clamp(x, lo, hi) {
        return Math.max(lo, Math.min(hi, x));
    }

    function taylorColumnState(s, vz) {
        const rBase = s.R * 1.5 + P.a * 3;
        const zetaAbs = 2 * P.Om + P.GaMag / (Math.PI * Math.max(s.R * s.R, P.a * P.a));
        const Lchar = Math.max(0.05, 2 * rBase);
        const zetaRel = zetaAbs - 2 * P.Om - vz / Lchar;
        const ratio = Math.abs(zetaAbs) / Math.max(1e-6, Math.abs(zetaRel));
        const rCap = rBase * Math.sqrt(clamp(ratio, 0.16, 6.25));
        const zTop = Math.min(1.5, s.cz + rCap);
        const zBot = Math.max(-0.5, s.cz - rCap);
        return { rCap, zTop, zBot, zetaAbs, zetaRel, rBase };
    }

    function getMetrics() {
        const sA = ringStats(XA);
        const sB = P.count === 2 ? ringStats(XB) : sA;
        const Wr = gauss(XA, XA, true) + (P.count === 2 ? gauss(XB, XB, true) : 0);
        const Lk = P.count === 2 ? gauss(XA, XB, false) : 0;
        const H = Wr + 2 * Lk;
        let approachV = null;
        if (P.count === 2 && hist.length > 5) {
            const p = hist[hist.length - 5];
            const q = hist[hist.length - 1];
            approachV = (p.dz - q.dz) / Math.max(1e-9, q.t - p.t);
        }
        const vzB = P.lockVz ? P.vzA : P.vzB;
        const taylorA = taylorColumnState(sA, P.vzA);
        const taylorB = P.count === 2 ? taylorColumnState(sB, vzB) : taylorA;
        const wrel = Flags.sep ? taylorA.zetaRel : 2 * P.Om;
        return {
            H, Wr, Lk,
            wrel,
            wrelBackground: 2 * P.Om,
            taylorA,
            taylorB,
            sA, sB,
            dz: P.count === 2 ? Math.abs(sB.z - sA.z) : null,
            approachV,
            tPhys,
            vzA: P.vzA,
            vzB,
            subtitle: subtitle(),
            flagged,
            count: P.count,
            topology: P.topology
        };
    }

    function pushHistory() {
        const m = getMetrics();
        hist.push({
            t: tPhys,
            RA: m.sA.R,
            RB: m.sB.R,
            dz: m.dz || 0
        });
        if (hist.length > 400) hist.shift();
    }

    function physicsStep(dtReal, lastUmaxRef) {
        if (paused || flagged) return { lastUmax: lastUmaxRef.value, flagged };

        let budget = P.acc * dtReal;
        let guard = 0;
        let lastUmax = lastUmaxRef.value;

        try {
            while (budget > 1e-6 && guard < 40 && !flagged) {
                const umax = Math.max(1e-6, lastUmax);
                const dt = Math.min(0.03, (0.3 * P.a) / umax, budget);
                lastUmax = stepRK2(dt);
                if (flagged) break;
                tPhys += dt;
                budget -= dt;
                guard++;
            }

            if (!flagged) {
                const gap = minGap();
                const sA = ringStats(XA);
                const sB = P.count === 2 ? ringStats(XB) : sA;
                if (P.count === 2 && gap < 3 * P.a) {
                    flagged = "⚠ kernen binnen 3a — reconnectieregime bereikt; filamentmodel niet langer geldig.";
                } else if (Math.max(sA.R, sB.R) > 0.9 * P.Rcyl) {
                    flagged = "⚠ filament nadert cilinderwand — wandbeelden niet gemodelleerd.";
                }
            }
        } catch (e) {
            flagged = "Physics error: " + e.message;
        }

        lastUmaxRef.value = lastUmax;
        return { lastUmax, flagged };
    }

    function vFromOmega(om) { return om * P.R0; }
    function vFromGamma(ga) { return ga / (2 * Math.PI * P.R0); }

    function signedGammaA() {
        return (P.ccwA ? 1 : -1) * P.GaMag;
    }
    function signedGammaB() {
        return (P.ccwB ? 1 : -1) * P.GaMag;
    }

    return {
        P,
        Flags,
        get knotN() { return knotN; },
        get XA() { return XA; },
        get XB() { return XB; },
        get paused() { return paused; },
        set paused(v) { paused = v; },
        get tPhys() { return tPhys; },
        get flagged() { return flagged; },
        get refFrame() { return refFrame; },
        set refFrame(v) { refFrame = v; },
        get hist() { return hist; },
        activeKnot,
        currentKnotN,
        reinitSimulation,
        resetState,
        physicsStep,
        getMetrics,
        pushHistory,
        ringStats,
        makeCarrier,
        offsetB,
        vFromOmega,
        vFromGamma,
        signedGammaA,
        signedGammaB,
        taylorColumnState,
        clearFlag() { flagged = ""; }
    };
})();
