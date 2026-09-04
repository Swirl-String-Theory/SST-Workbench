/* SST 3D Collider — Three.js scene */
"use strict";

window.SSTScene = (function () {
    class DynamicArrayCurve extends THREE.Curve {
        constructor(array, n) {
            super();
            this.array = array;
            this.n = n;
        }
        getPoint(t, optionalTarget = new THREE.Vector3()) {
            let idx = t * this.n;
            let i = Math.floor(idx);
            let f = idx - i;
            if (i >= this.n) { i = this.n - 1; f = 1; }
            const i2 = (i + 1) % this.n;
            const x = this.array[i * 3] + f * (this.array[i2 * 3] - this.array[i * 3]);
            const y = this.array[i * 3 + 1] + f * (this.array[i2 * 3 + 1] - this.array[i * 3 + 1]);
            const z = this.array[i * 3 + 2] + f * (this.array[i2 * 3 + 2] - this.array[i * 3 + 2]);
            return optionalTarget.set(x, y, z);
        }
    }

    let renderer, scene, camera, controls;
    let rootGroup, latticeGrp;
    let meshA, meshB, flowA, flowB;
    let wireA, wireB;
    let betaMeshA, betaMeshB;
    let sepA, sepB;
    let topCircA, botCircA, topRingA, botRingA;
    let topCircB, botCircB, topRingB, botRingB;
    let colSilA, colSilB;
    let alphaA, alphaB;
    let matSolidA, matSolidB, matHollowA, matHollowB;
    let flowMatA, flowMatB;
    let betaMat;
    let physics;
    let meshFrame = 0;
    let betaFrame = 0;
    let showCenterline = false;

    function createCapDisc(color) {
        return new THREE.Mesh(
            new THREE.CircleGeometry(1, 48),
            new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.35, side: THREE.DoubleSide })
        );
    }

    function createCapRing(color) {
        return new THREE.Mesh(
            new THREE.RingGeometry(0.92, 1.0, 48),
            new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.75, side: THREE.DoubleSide })
        );
    }

    function createColumnSilhouette(color) {
        const geo = new THREE.CylinderGeometry(1, 1, 1, 32, 1, true);
        geo.rotateX(Math.PI / 2);
        return new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
            color, wireframe: true, transparent: true, opacity: 0.15
        }));
    }

    function createSeparatrixSphere() {
        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(1, 32, 32),
            new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.12, depthWrite: false })
        );
        const edges = new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.SphereGeometry(1, 16, 16)),
            new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.6 })
        );
        mesh.add(edges);
        return mesh;
    }

    function init(canvas, physicsRef) {
        physics = physicsRef;
        const P = physics.P;

        renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setClearColor(0x0B1020, 1);

        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0B1020);
        scene.fog = new THREE.FogExp2(0x0B1020, 0.02);

        camera = new THREE.PerspectiveCamera(45, 1, 0.01, 50);
        camera.up.set(0, 0, 1);
        camera.position.set(1.5, -1.5, 1.8);

        if (typeof THREE.OrbitControls !== "undefined") {
            controls = new THREE.OrbitControls(camera, canvas);
            controls.enableDamping = true;
            controls.dampingFactor = 0.06;
            controls.target.set(0, 0, 0.5);
            controls.update();
        }

        scene.add(new THREE.AmbientLight(0xffffff, 0.7));
        const light1 = new THREE.PointLight(0x55D6FF, 2, 50);
        light1.position.set(2, 2, 2);
        scene.add(light1);
        const light2 = new THREE.PointLight(0xFFAE45, 2, 50);
        light2.position.set(-2, -2, -2);
        scene.add(light2);

        rootGroup = new THREE.Group();
        scene.add(rootGroup);

        const cylGeo = new THREE.CylinderGeometry(P.Rcyl, P.Rcyl, P.Hcyl, 48, 1, true);
        cylGeo.rotateX(Math.PI / 2);
        cylGeo.translate(0, 0, 0.5);
        rootGroup.add(new THREE.Mesh(cylGeo, new THREE.MeshBasicMaterial({
            color: 0x1E2C4A, wireframe: true, transparent: true, opacity: 0.25
        })));

        latticeGrp = new THREE.Group();
        rootGroup.add(latticeGrp);
        const vPos = new Float32Array(200 * 2 * 3);
        for (let i = 0; i < 200; i++) {
            const r = P.Rcyl * Math.sqrt(Math.random()) * 0.95 + 0.02;
            const th = Math.random() * 2 * Math.PI;
            const x = r * Math.cos(th);
            const y = r * Math.sin(th);
            vPos[i * 6] = x;
            vPos[i * 6 + 1] = y;
            vPos[i * 6 + 2] = -0.5;
            vPos[i * 6 + 3] = x;
            vPos[i * 6 + 4] = y;
            vPos[i * 6 + 5] = 1.5;
        }
        const vortexGeo = new THREE.BufferGeometry();
        vortexGeo.setAttribute("position", new THREE.BufferAttribute(vPos, 3));
        latticeGrp.add(new THREE.LineSegments(vortexGeo, new THREE.LineBasicMaterial({
            color: 0x6F82A0, transparent: true, opacity: 0.04
        })));

        const zGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, -0.5),
            new THREE.Vector3(0, 0, 1.5)
        ]);
        const zAxis = new THREE.Line(zGeo, new THREE.LineDashedMaterial({
            color: 0x55D6FF, dashSize: 0.05, gapSize: 0.05, transparent: true, opacity: 0.5
        }));
        zAxis.computeLineDistances();
        rootGroup.add(zAxis);

        matSolidA = new THREE.MeshPhysicalMaterial({ color: 0xFFAE45, metalness: 0.3, roughness: 0.2 });
        matSolidB = new THREE.MeshPhysicalMaterial({ color: 0x55D6FF, metalness: 0.3, roughness: 0.2 });
        matHollowA = new THREE.MeshPhysicalMaterial({
            color: 0xFFAE45, metalness: 0.1, roughness: 0.1, transmission: 0.95,
            thickness: 0.01, transparent: true, opacity: 0.6
        });
        matHollowB = new THREE.MeshPhysicalMaterial({
            color: 0x55D6FF, metalness: 0.1, roughness: 0.1, transmission: 0.95,
            thickness: 0.01, transparent: true, opacity: 0.6
        });
        flowMatA = new THREE.MeshBasicMaterial({ color: 0xA855F7, wireframe: true, transparent: true, opacity: 0.3 });
        flowMatB = new THREE.MeshBasicMaterial({ color: 0xA855F7, wireframe: true, transparent: true, opacity: 0.3 });
        betaMat = new THREE.MeshBasicMaterial({ color: 0xfacc15, wireframe: true, transparent: true, opacity: 0.55 });

        sepA = createSeparatrixSphere();
        sepB = createSeparatrixSphere();
        rootGroup.add(sepA);
        rootGroup.add(sepB);

        topCircA = createCapDisc(0xFFAE45);
        botCircA = createCapDisc(0xFFAE45);
        topRingA = createCapRing(0xFFAE45);
        botRingA = createCapRing(0xFFAE45);
        topCircB = createCapDisc(0x55D6FF);
        botCircB = createCapDisc(0x55D6FF);
        topRingB = createCapRing(0x55D6FF);
        botRingB = createCapRing(0x55D6FF);
        colSilA = createColumnSilhouette(0xFFAE45);
        colSilB = createColumnSilhouette(0x55D6FF);
        rootGroup.add(topCircA, botCircA, topRingA, botRingA, colSilA);
        rootGroup.add(topCircB, botCircB, topRingB, botRingB, colSilB);

        const alphaMat = new THREE.MeshBasicMaterial({ color: 0xFF6E6E, transparent: true, opacity: 0.8 });
        alphaA = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 16), alphaMat);
        alphaB = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 16), alphaMat.clone());
        rootGroup.add(alphaA);
        rootGroup.add(alphaB);

        wireA = makeWireLoop(0xFFAE45);
        wireB = makeWireLoop(0x55D6FF);
        wireA.visible = false;
        wireB.visible = false;
        rootGroup.add(wireA);
        rootGroup.add(wireB);

        updateBeautifulMeshes(true);
        updateWireLines();
    }

    function makeWireLoop(color) {
        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(3 * 512), 3));
        return new THREE.LineLoop(geo, new THREE.LineBasicMaterial({ color, linewidth: 2 }));
    }

    function updateWireLines() {
        if (!physics || !physics.XA) return;
        const knotN = physics.knotN;
        const XA = physics.XA;
        const XB = physics.XB;
        pushWire(wireA, XA, knotN);
        wireA.visible = showCenterline;
        if (physics.P.count === 2) {
            pushWire(wireB, XB, knotN);
            wireB.visible = showCenterline;
        } else {
            wireB.visible = false;
        }
    }

    function pushWire(line, X, knotN) {
        const p = line.geometry.attributes.position.array;
        const need = (knotN + 1) * 3;
        if (p.length < need) {
            line.geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(need), 3));
        }
        const arr = line.geometry.attributes.position.array;
        for (let k = 0; k <= knotN; k++) {
            const s = (k % knotN) * 3;
            arr[k * 3] = X[s];
            arr[k * 3 + 1] = X[s + 1];
            arr[k * 3 + 2] = X[s + 2];
        }
        line.geometry.attributes.position.needsUpdate = true;
    }

    function disposeMesh(m) {
        if (!m) return;
        rootGroup.remove(m);
        m.geometry.dispose();
    }

    function updateBeautifulMeshes(force) {
        meshFrame++;
        if (!force && meshFrame % 2 !== 0) return;

        const P = physics.P;
        const knotN = physics.knotN;
        const XA = physics.XA;
        const XB = physics.XB;
        const solid = P.coreModel === "solid";

        disposeMesh(meshA);
        disposeMesh(meshB);
        disposeMesh(flowA);
        disposeMesh(flowB);
        meshA = meshB = flowA = flowB = null;

        const tubeRadius = P.a * 2.5;
        try {
            const curveA = new DynamicArrayCurve(XA, knotN);
            meshA = new THREE.Mesh(
                new THREE.TubeGeometry(curveA, knotN, tubeRadius, 8, true),
                solid ? matSolidA : matHollowA
            );
            rootGroup.add(meshA);

            if (physics.Flags.gamma) {
                flowA = new THREE.Mesh(
                    new THREE.TubeGeometry(curveA, knotN, tubeRadius * 1.6, 12, true),
                    flowMatA
                );
                rootGroup.add(flowA);
            }

            if (P.count === 2) {
                const curveB = new DynamicArrayCurve(XB, knotN);
                meshB = new THREE.Mesh(
                    new THREE.TubeGeometry(curveB, knotN, tubeRadius, 8, true),
                    solid ? matSolidB : matHollowB
                );
                rootGroup.add(meshB);
                if (physics.Flags.gamma) {
                    flowB = new THREE.Mesh(
                        new THREE.TubeGeometry(curveB, knotN, tubeRadius * 1.6, 12, true),
                        flowMatB
                    );
                    rootGroup.add(flowB);
                }
            }
        } catch (e) {
            console.warn("TubeGeometry rebuild skipped:", e.message);
        }
    }

    function updateBetaMeshes(force) {
        const F = physics.Flags;
        if (!F.beta) {
            disposeMesh(betaMeshA);
            disposeMesh(betaMeshB);
            betaMeshA = betaMeshB = null;
            return;
        }

        betaFrame++;
        if (!force && betaFrame % 2 !== 0) return;

        const P = physics.P;
        const knotN = physics.knotN;
        const XA = physics.XA;
        const XB = physics.XB;
        const tubeRadius = P.a * 2.5 * 1.03;

        disposeMesh(betaMeshA);
        disposeMesh(betaMeshB);
        betaMeshA = betaMeshB = null;

        try {
            const curveA = new DynamicArrayCurve(XA, knotN);
            betaMeshA = new THREE.Mesh(
                new THREE.TubeGeometry(curveA, knotN, tubeRadius, 10, true),
                betaMat
            );
            rootGroup.add(betaMeshA);

            if (P.count === 2) {
                const curveB = new DynamicArrayCurve(XB, knotN);
                betaMeshB = new THREE.Mesh(
                    new THREE.TubeGeometry(curveB, knotN, tubeRadius, 10, true),
                    betaMat
                );
                rootGroup.add(betaMeshB);
            }
        } catch (e) {
            console.warn("Beta tube rebuild skipped:", e.message);
        }
    }

    function setCapPair(topDisc, botDisc, topRing, botRing, colSil, cx, cy, zTop, zBot, rCap, color) {
        const h = Math.max(0.01, zTop - zBot);
        const zMid = (zTop + zBot) * 0.5;

        topDisc.visible = botDisc.visible = true;
        topRing.visible = botRing.visible = true;
        colSil.visible = true;

        topDisc.position.set(cx, cy, zTop);
        botDisc.position.set(cx, cy, zBot);
        topRing.position.set(cx, cy, zTop);
        botRing.position.set(cx, cy, zBot);
        colSil.position.set(cx, cy, zMid);

        topDisc.scale.set(rCap, rCap, 1);
        botDisc.scale.set(rCap, rCap, 1);
        topRing.scale.set(rCap, rCap, 1);
        botRing.scale.set(rCap, rCap, 1);
        colSil.scale.set(rCap, rCap, h);
    }

    function hideCapPair(topDisc, botDisc, topRing, botRing, colSil) {
        topDisc.visible = botDisc.visible = false;
        topRing.visible = botRing.visible = false;
        colSil.visible = false;
    }

    function updateSeparatrix(m, count, P) {
        const F = physics.Flags;
        if (!F.sep) {
            sepA.visible = sepB.visible = false;
            hideCapPair(topCircA, botCircA, topRingA, botRingA, colSilA);
            hideCapPair(topCircB, botCircB, topRingB, botRingB, colSilB);
            return;
        }

        const tA = m.taylorA;
        sepA.visible = true;
        sepA.position.set(m.sA.cx, m.sA.cy, m.sA.cz);
        sepA.scale.set(tA.rCap, tA.rCap, tA.rCap);
        setCapPair(topCircA, botCircA, topRingA, botRingA, colSilA,
            m.sA.cx, m.sA.cy, tA.zTop, tA.zBot, tA.rCap);

        if (count === 2) {
            const tB = m.taylorB;
            sepB.visible = true;
            sepB.position.set(m.sB.cx, m.sB.cy, m.sB.cz);
            sepB.scale.set(tB.rCap, tB.rCap, tB.rCap);
            setCapPair(topCircB, botCircB, topRingB, botRingB, colSilB,
                m.sB.cx, m.sB.cy, tB.zTop, tB.zBot, tB.rCap);
        } else {
            sepB.visible = false;
            hideCapPair(topCircB, botCircB, topRingB, botRingB, colSilB);
        }
    }

    function updateAlpha(sA, sB, count, P, tPhys) {
        const F = physics.Flags;
        if (!F.alpha) {
            alphaA.visible = alphaB.visible = false;
            return;
        }
        alphaA.visible = true;
        alphaA.position.set(sA.cx, sA.cy, sA.cz);
        const pScale = P.a * 6 * (1 + 0.2 * Math.sin(tPhys * 20));
        alphaA.scale.set(pScale, pScale, pScale);
        if (count === 2) {
            alphaB.visible = true;
            alphaB.position.set(sB.cx, sB.cy, sB.cz);
            alphaB.scale.set(pScale, pScale, pScale);
        } else {
            alphaB.visible = false;
        }
    }

    function frameUpdate(tPhys) {
        const P = physics.P;
        const m = physics.getMetrics();
        updateWireLines();
        updateBeautifulMeshes(false);
        updateBetaMeshes(false);
        updateSeparatrix(m, P.count, P);
        updateAlpha(m.sA, m.sB, P.count, P, tPhys);

        if (physics.Flags.gamma) {
            if (flowA) flowMatA.opacity = 0.2 + 0.15 * Math.sin(tPhys * 15);
            if (flowB) flowMatB.opacity = 0.2 + 0.15 * Math.sin(tPhys * 15 + Math.PI);
        }

        if (physics.refFrame === "lab") {
            latticeGrp.rotation.z = P.Om * tPhys;
            rootGroup.rotation.z = 0;
        } else {
            latticeGrp.rotation.z = P.Om * tPhys;
            rootGroup.rotation.z = -P.Om * tPhys;
        }
    }

    function resize(w, h) {
        if (!renderer || !camera) return;
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
    }

    function render() {
        if (controls) controls.update();
        renderer.render(scene, camera);
    }

    function onCoreModelChange() {
        updateBeautifulMeshes(true);
    }

    function onIndicatorChange() {
        updateBetaMeshes(true);
        updateBeautifulMeshes(true);
    }

    function setShowCenterline(v) {
        showCenterline = !!v;
        updateWireLines();
    }

    function onReinit() {
        meshFrame = 0;
        betaFrame = 0;
        updateBeautifulMeshes(true);
        updateBetaMeshes(true);
        updateWireLines();
    }

    return {
        init,
        frameUpdate,
        resize,
        render,
        onCoreModelChange,
        onIndicatorChange,
        setShowCenterline,
        onReinit,
        get canvas() { return renderer && renderer.domElement; }
    };
})();
