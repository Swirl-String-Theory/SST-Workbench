/**
 * VortexLab catalog browser — render-only grid of knot thumbnails.
 * Uses one shared WebGL renderer; each card keeps a static 2D snapshot
 * so scrolling never tears down visible thumbs (no MAX_LIVE flicker).
 */
(function () {
  'use strict';

  const G = window.VortexLabCatalogGeometry;
  if (!G) {
    console.error('[catalog] VortexLabCatalogGeometry ontbreekt');
    return;
  }
  if (typeof THREE === 'undefined') {
    console.error('[catalog] THREE ontbreekt');
    return;
  }

  const THUMB_N = 128;
  const TUBE_RADIAL = 5;
  const THUMB_W = 480;
  const THUMB_H = 360;
  const COLORS = [0x5eb0ff, 0xe08ad8, 0x6bcb8a, 0xe0b35a, 0xff8a6b, 0x9ad0ff];

  const SOURCE_LABEL = {
    ideal: 'Ideal',
    fseries: 'Fseries',
    knotplot: 'KnotPlot',
    twist: 'Twist',
  };

  function collectCatalog() {
    const rows = [];
    const specs = [
      { source: 'ideal', ids: window.IDEAL_KNOT_IDS, db: window.IDEAL_KNOT_DB },
      { source: 'fseries', ids: window.FSERIES_KNOT_IDS, db: window.FSERIES_KNOT_DB },
      { source: 'knotplot', ids: window.KNOTPLOT_KNOT_IDS, db: window.KNOTPLOT_KNOT_DB },
      { source: 'twist', ids: window.TWIST_KNOT_IDS, db: window.TWIST_KNOT_DB },
    ];
    for (const s of specs) {
      if (!Array.isArray(s.ids) || !s.db || typeof s.db !== 'object') continue;
      for (const id of s.ids) {
        const entry = s.db[id];
        if (!entry) continue;
        const comps = G.knotEntryComponents(entry);
        rows.push({
          key: s.source + '|' + id,
          source: s.source,
          id,
          entry,
          label: entry.label || entry.knotId || id,
          topology: entry.topology || entry.conway || '',
          profile: entry.profile || '',
          resolutionN: entry.resolutionN || null,
          family: entry.family || '',
          componentCount: comps.length || Number(entry.componentCount) || 0,
          status: entry.status || (entry.ideal ? 'ideal' : 'candidate'),
        });
      }
    }
    return rows;
  }

  const ALL = collectCatalog();
  let filterSource = 'all';
  let filterQuery = '';

  const grid = document.getElementById('catalogGrid');
  const statsEl = document.getElementById('catStats');
  const searchEl = document.getElementById('catSearch');
  const tabs = document.querySelectorAll('.cat-tabs button');

  // Shared offscreen WebGL context (one only).
  const glCanvas = document.createElement('canvas');
  glCanvas.width = THUMB_W;
  glCanvas.height = THUMB_H;
  const renderer = new THREE.WebGLRenderer({
    canvas: glCanvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
    failIfMajorPerformanceCaveat: false,
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(1);
  renderer.setSize(THUMB_W, THUMB_H, false);
  renderer.setClearColor(0x080c16, 1);

  const scene = new THREE.Scene();
  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const keyLight = new THREE.DirectionalLight(0xffffff, 0.85);
  keyLight.position.set(1.2, -0.8, 1.6);
  scene.add(keyLight);
  const camera = new THREE.PerspectiveCamera(40, THUMB_W / THUMB_H, 0.05, 20);
  const group = new THREE.Group();
  scene.add(group);

  const snapshots = new Map(); // key -> dataURL or ImageBitmap-ready canvas clone not needed; we draw to card canvas
  const rendered = new Set();
  const queue = [];
  let busy = false;

  function matches(row) {
    if (filterSource !== 'all' && row.source !== filterSource) return false;
    const q = filterQuery.trim().toLowerCase();
    if (!q) return true;
    const hay = [row.id, row.label, row.topology, row.profile, row.family, row.source]
      .join(' ')
      .toLowerCase();
    return hay.includes(q);
  }

  function filtered() {
    return ALL.filter(matches);
  }

  function metaLine(row) {
    const bits = [];
    if (row.componentCount) bits.push(row.componentCount + ' comp');
    if (row.resolutionN) bits.push('N' + row.resolutionN);
    if (row.profile) bits.push(row.profile);
    if (row.family) bits.push(row.family);
    if (row.status) bits.push(row.status);
    return bits.join(' · ');
  }

  function clearGroup() {
    while (group.children.length) {
      const m = group.children[0];
      group.remove(m);
      if (m.geometry) m.geometry.dispose();
      if (m.material) m.material.dispose();
    }
  }

  function paintCard(card, dataUrl) {
    let canvas = card.querySelector('canvas.cat-thumb');
    if (!canvas) {
      const ph = card.querySelector('.cat-placeholder');
      canvas = document.createElement('canvas');
      canvas.className = 'cat-thumb';
      canvas.width = THUMB_W;
      canvas.height = THUMB_H;
      if (ph) ph.replaceWith(canvas);
      else card.insertBefore(canvas, card.firstChild);
    }
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
    };
    img.src = dataUrl;
  }

  function renderSnapshot(row) {
    clearGroup();
    let thumb;
    try {
      thumb = G.sampleEntryThumb(row.entry, row.source, THUMB_N);
    } catch (err) {
      console.warn('[catalog] sample failed', row.key, err);
      return null;
    }

    thumb.points.forEach((raw, ci) => {
      const n = Math.floor(raw.length / 3);
      if (n < 4) return;
      const pts = [];
      for (let k = 0; k < n; k++) {
        pts.push(new THREE.Vector3(raw[3 * k], raw[3 * k + 1], raw[3 * k + 2]));
      }
      const curve = new THREE.CatmullRomCurve3(pts, true, 'catmullrom', 0.0);
      const geo = new THREE.TubeGeometry(
        curve,
        Math.max(40, Math.min(n, 128)),
        0.045,
        TUBE_RADIAL,
        true
      );
      const mat = new THREE.MeshPhongMaterial({
        color: COLORS[ci % COLORS.length],
        shininess: 40,
        specular: 0x334455,
      });
      group.add(new THREE.Mesh(geo, mat));
    });

    const camTh = 0.55;
    const camPh = 1.05;
    const camD = 3.2;
    camera.position.set(
      camD * Math.sin(camPh) * Math.cos(camTh),
      camD * Math.sin(camPh) * Math.sin(camTh),
      camD * Math.cos(camPh)
    );
    camera.up.set(0, 0, 1);
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
    clearGroup();
    return glCanvas.toDataURL('image/png');
  }

  function pumpQueue() {
    if (busy) return;
    const next = queue.shift();
    if (!next) return;
    busy = true;
    const { row, card } = next;
    requestAnimationFrame(() => {
      try {
        if (!rendered.has(row.key)) {
          const url = renderSnapshot(row);
          if (url) {
            snapshots.set(row.key, url);
            rendered.add(row.key);
          }
        }
        const url = snapshots.get(row.key);
        if (url && card.isConnected) paintCard(card, url);
      } catch (err) {
        console.warn('[catalog] render failed', row.key, err);
        const ph = card.querySelector('.cat-placeholder');
        if (ph) ph.textContent = 'renderfout';
      } finally {
        busy = false;
        pumpQueue();
      }
    });
  }

  function enqueue(card, row) {
    if (snapshots.has(row.key)) {
      paintCard(card, snapshots.get(row.key));
      return;
    }
    if (queue.some((q) => q.row.key === row.key)) return;
    queue.push({ card, row });
    pumpQueue();
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const ent of entries) {
        if (!ent.isIntersecting) continue;
        const key = ent.target.getAttribute('data-key');
        const row = ALL.find((r) => r.key === key);
        if (row) enqueue(ent.target, row);
      }
    },
    { root: null, rootMargin: '400px 0px', threshold: 0.01 }
  );

  function renderGrid() {
    observer.disconnect();
    queue.length = 0;
    busy = false;
    const rows = filtered();
    if (statsEl) {
      statsEl.textContent =
        rows.length + ' / ' + ALL.length + ' knopen · render-only (geen Biot–Savart)';
    }
    grid.innerHTML = '';
    if (!rows.length) {
      const empty = document.createElement('div');
      empty.className = 'cat-empty';
      empty.textContent =
        ALL.length === 0
          ? 'Geen catalogusdata geladen. Controleer data/*.js.'
          : 'Geen treffers voor deze filter.';
      grid.appendChild(empty);
      return;
    }
    for (const row of rows) {
      const card = document.createElement('article');
      card.className = 'cat-card';
      card.setAttribute('data-key', row.key);

      if (snapshots.has(row.key)) {
        const canvas = document.createElement('canvas');
        canvas.className = 'cat-thumb';
        canvas.width = THUMB_W;
        canvas.height = THUMB_H;
        card.appendChild(canvas);
        // paint async after append
        requestAnimationFrame(() => paintCard(card, snapshots.get(row.key)));
      } else {
        const ph = document.createElement('div');
        ph.className = 'cat-placeholder';
        ph.textContent = 'laden…';
        card.appendChild(ph);
      }

      const body = document.createElement('div');
      body.className = 'cat-card-body';
      const badge = document.createElement('span');
      badge.className = 'cat-badge ' + row.source;
      badge.textContent = SOURCE_LABEL[row.source] || row.source;
      const idEl = document.createElement('div');
      idEl.className = 'cat-card-id';
      idEl.textContent = row.id;
      const meta = document.createElement('div');
      meta.className = 'cat-card-meta';
      meta.textContent = (row.label !== row.id ? row.label + ' · ' : '') + metaLine(row);
      const selectBtn = document.createElement('button');
      selectBtn.type = 'button';
      selectBtn.className = 'cat-select';
      selectBtn.textContent = 'Selecteer in lab';
      selectBtn.title = 'Open VortexLab met deze knoop geselecteerd';
      selectBtn.addEventListener('click', () => {
        const url = new URL('./index.html', location.href);
        url.searchParams.set('knotSource', row.source);
        url.searchParams.set('knotId', row.id);
        location.href = url.href;
      });
      body.appendChild(badge);
      body.appendChild(idEl);
      body.appendChild(meta);
      body.appendChild(selectBtn);
      card.appendChild(body);
      grid.appendChild(card);
      observer.observe(card);
    }
  }

  tabs.forEach((btn) => {
    btn.addEventListener('click', () => {
      tabs.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      filterSource = btn.getAttribute('data-source') || 'all';
      renderGrid();
    });
  });

  if (searchEl) {
    let t = 0;
    searchEl.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(() => {
        filterQuery = searchEl.value || '';
        renderGrid();
      }, 120);
    });
  }

  renderGrid();
  console.info('[VortexLab catalog]', ALL.length, 'entries · shared WebGL snapshots');
})();
